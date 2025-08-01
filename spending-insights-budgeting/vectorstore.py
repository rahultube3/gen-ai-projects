"""
Optimized Vectorstore for Spending Insights
Features: Caching, Batch Processing, Advanced Search, Performance Monitoring
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional, Tuple
import os
import json
import pickle
import hashlib
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from functools import lru_cache
import numpy as np
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OptimizedVectorStore:
    """Enhanced vectorstore with caching, batch processing, and advanced features"""
    
    def __init__(
        self,
        cache_dir: str = "vectorstore_cache",
        embedding_model: str = "text-embedding-ada-002",
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        similarity_threshold: float = 0.7
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.similarity_threshold = similarity_threshold
        
        # Initialize embeddings with optimized settings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=embedding_model,
            chunk_size=100,  # Batch size for API calls
            max_retries=3,
            request_timeout=30
        )
        
        # Performance tracking
        self.build_time = 0
        self.search_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        
    def _generate_data_hash(self, spending_data: List[Dict[str, Any]]) -> str:
        """Generate hash for spending data to detect changes"""
        # Create a deterministic hash based on the data content
        data_str = json.dumps(spending_data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cache_path(self, data_hash: str) -> Path:
        """Get cache file path for given data hash"""
        return self.cache_dir / f"vectorstore_{data_hash}.pkl"
    
    def _get_metadata_path(self, data_hash: str) -> Path:
        """Get metadata file path for given data hash"""
        return self.cache_dir / f"metadata_{data_hash}.json"
    
    def _save_to_cache(self, vectorstore: FAISS, data_hash: str, metadata: Dict[str, Any]) -> None:
        """Save vectorstore and metadata to cache"""
        try:
            cache_path = self._get_cache_path(data_hash)
            metadata_path = self._get_metadata_path(data_hash)
            
            # Save vectorstore
            with open(cache_path, 'wb') as f:
                pickle.dump(vectorstore, f)
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"✅ Vectorstore cached: {cache_path}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to cache vectorstore: {e}")
    
    def _load_from_cache(self, data_hash: str) -> Optional[Tuple[FAISS, Dict[str, Any]]]:
        """Load vectorstore and metadata from cache"""
        try:
            cache_path = self._get_cache_path(data_hash)
            metadata_path = self._get_metadata_path(data_hash)
            
            if not cache_path.exists() or not metadata_path.exists():
                return None
            
            # Check cache age
            cache_age = time.time() - cache_path.stat().st_mtime
            max_cache_age = 24 * 3600  # 24 hours
            
            if cache_age > max_cache_age:
                logger.info("🕒 Cache expired, rebuilding vectorstore")
                return None
            
            # Load vectorstore
            with open(cache_path, 'rb') as f:
                vectorstore = pickle.load(f)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.cache_hits += 1
            logger.info(f"🎯 Vectorstore loaded from cache: {cache_path}")
            return vectorstore, metadata
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load from cache: {e}")
            return None
    
    def _enhance_document_content(self, item: Dict[str, Any]) -> str:
        """Create enhanced document content with better context"""
        # Base transaction info
        content_parts = [
            f"Transaction on {item['date']}",
            f"Merchant: {item['merchant']}",
            f"Category: {item['category']}",
            f"Amount: ${item['amount']:.2f}"
        ]
        
        # Add notes if available
        if item.get('notes') and item['notes'].strip():
            content_parts.append(f"Notes: {item['notes']}")
        
        # Add contextual information
        try:
            amount = float(item['amount'])
            if amount > 100:
                content_parts.append("High-value transaction")
            elif amount < 10:
                content_parts.append("Small purchase")
            
            # Add day of week context
            from datetime import datetime
            date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
            day_of_week = date_obj.strftime('%A')
            content_parts.append(f"Day: {day_of_week}")
            
            # Add month context
            month = date_obj.strftime('%B')
            content_parts.append(f"Month: {month}")
            
        except (ValueError, KeyError) as e:
            logger.debug(f"Could not add context for item: {e}")
        
        return ". ".join(content_parts)
    
    def _create_enhanced_metadata(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced metadata with additional context"""
        metadata = {
            "date": item["date"],
            "merchant": item["merchant"],
            "category": item["category"],
            "amount": float(item["amount"])
        }
        
        # Add derived fields
        try:
            date_obj = datetime.strptime(item['date'], '%Y-%m-%d')
            metadata.update({
                "year": date_obj.year,
                "month": date_obj.month,
                "day_of_week": date_obj.strftime('%A'),
                "month_name": date_obj.strftime('%B'),
                "quarter": f"Q{(date_obj.month - 1) // 3 + 1}",
                "is_weekend": date_obj.weekday() >= 5
            })
            
            # Amount categories
            amount = float(item["amount"])
            if amount < 10:
                metadata["amount_category"] = "small"
            elif amount < 50:
                metadata["amount_category"] = "medium"
            elif amount < 200:
                metadata["amount_category"] = "large"
            else:
                metadata["amount_category"] = "very_large"
                
        except (ValueError, KeyError) as e:
            logger.debug(f"Could not add enhanced metadata: {e}")
        
        return metadata
    
    def _batch_process_documents(
        self, 
        spending_data: List[Dict[str, Any]], 
        batch_size: int = 50
    ) -> List[Document]:
        """Process documents in batches for better performance"""
        documents = []
        
        logger.info(f"📄 Processing {len(spending_data)} transactions in batches of {batch_size}")
        
        for i in range(0, len(spending_data), batch_size):
            batch = spending_data[i:i + batch_size]
            batch_docs = []
            
            for item in batch:
                try:
                    content = self._enhance_document_content(item)
                    metadata = self._create_enhanced_metadata(item)
                    
                    doc = Document(
                        page_content=content,
                        metadata=metadata
                    )
                    batch_docs.append(doc)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process item: {item}, error: {e}")
                    continue
            
            documents.extend(batch_docs)
            logger.debug(f"✅ Processed batch {i//batch_size + 1}/{(len(spending_data) + batch_size - 1)//batch_size}")
        
        logger.info(f"✅ Created {len(documents)} documents from {len(spending_data)} transactions")
        return documents
    
    def _apply_text_splitting(self, documents: List[Document]) -> List[Document]:
        """Apply text splitting for better retrieval"""
        if not documents:
            return documents
        
        # Check if splitting is needed (for very long documents)
        max_length = max(len(doc.page_content) for doc in documents)
        
        if max_length <= self.chunk_size:
            return documents
        
        logger.info(f"📝 Applying text splitting (max_length: {max_length})")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[". ", ", ", "\n", " "]
        )
        
        split_documents = text_splitter.split_documents(documents)
        logger.info(f"✂️ Split into {len(split_documents)} chunks")
        
        return split_documents
    
    def build_vectorstore(
        self, 
        spending_data: List[Dict[str, Any]], 
        force_rebuild: bool = False
    ) -> FAISS:
        """Build optimized vectorstore with caching and batch processing"""
        start_time = time.time()
        
        if not spending_data:
            raise ValueError("No spending data provided")
        
        logger.info(f"🏗️ Building vectorstore for {len(spending_data)} transactions")
        
        # Generate data hash for caching
        data_hash = self._generate_data_hash(spending_data)
        
        # Try to load from cache first
        if not force_rebuild:
            cached_result = self._load_from_cache(data_hash)
            if cached_result:
                vectorstore, metadata = cached_result
                self.build_time = metadata.get('build_time', 0)
                logger.info(f"⚡ Vectorstore loaded from cache in {time.time() - start_time:.2f}s")
                return vectorstore
        
        self.cache_misses += 1
        
        try:
            # Process documents in batches
            documents = self._batch_process_documents(spending_data)
            
            if not documents:
                raise ValueError("No valid documents created from spending data")
            
            # Apply text splitting if needed
            documents = self._apply_text_splitting(documents)
            
            # Build vectorstore with batch embedding
            logger.info("🔍 Creating embeddings and building FAISS index...")
            vectorstore = FAISS.from_documents(documents, self.embeddings)
            
            build_time = time.time() - start_time
            self.build_time = build_time
            
            # Create metadata for caching
            metadata = {
                "created_at": datetime.now().isoformat(),
                "num_documents": len(documents),
                "num_transactions": len(spending_data),
                "build_time": build_time,
                "data_hash": data_hash,
                "embedding_model": self.embedding_model,
                "config": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "similarity_threshold": self.similarity_threshold
                }
            }
            
            # Cache the vectorstore
            self._save_to_cache(vectorstore, data_hash, metadata)
            
            logger.info(f"✅ Vectorstore built successfully in {build_time:.2f}s")
            logger.info(f"📊 Index contains {vectorstore.index.ntotal} vectors")
            
            return vectorstore
            
        except Exception as e:
            logger.error(f"❌ Failed to build vectorstore: {e}")
            raise
    
    def enhanced_similarity_search(
        self, 
        vectorstore: FAISS, 
        query: str, 
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[Document, float]]:
        """Enhanced similarity search with filtering and scoring"""
        start_time = time.time()
        
        try:
            # Use score threshold if provided, otherwise use instance default
            threshold = score_threshold or self.similarity_threshold
            
            # Perform similarity search with scores
            results = vectorstore.similarity_search_with_score(
                query, 
                k=k * 2  # Get more results for filtering
            )
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results 
                if score <= (1.0 - threshold)  # FAISS uses distance, lower is better
            ]
            
            # Apply metadata filtering if provided
            if filter_metadata:
                filtered_results = [
                    (doc, score) for doc, score in filtered_results
                    if all(
                        doc.metadata.get(key) == value 
                        for key, value in filter_metadata.items()
                    )
                ]
            
            # Limit to requested number of results
            final_results = filtered_results[:k]
            
            search_time = time.time() - start_time
            self.search_times.append(search_time)
            
            logger.debug(f"🔍 Search completed in {search_time:.3f}s, found {len(final_results)} results")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_search_time = np.mean(self.search_times) if self.search_times else 0
        
        return {
            "build_time_seconds": self.build_time,
            "total_searches": len(self.search_times),
            "average_search_time_ms": round(avg_search_time * 1000, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
            "embedding_model": self.embedding_model,
            "similarity_threshold": self.similarity_threshold
        }
    
    def cleanup_cache(self, max_age_days: int = 7) -> None:
        """Clean up old cache files"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            cleaned_count = 0
            for cache_file in self.cache_dir.glob("*.pkl"):
                if current_time - cache_file.stat().st_mtime > max_age_seconds:
                    cache_file.unlink()
                    # Also remove corresponding metadata file
                    metadata_file = cache_file.with_suffix('.json').with_name(
                        cache_file.name.replace('vectorstore_', 'metadata_')
                    )
                    if metadata_file.exists():
                        metadata_file.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} old cache files")
                
        except Exception as e:
            logger.warning(f"⚠️ Cache cleanup failed: {e}")

# Global instance for backward compatibility and performance
_vectorstore_instance = OptimizedVectorStore()

def build_vectorstore(spending_data: List[Dict[str, Any]], force_rebuild: bool = False) -> FAISS:
    """
    Build optimized vectorstore (backward compatible function)
    
    Args:
        spending_data: List of spending transaction dictionaries
        force_rebuild: Force rebuild even if cache exists
        
    Returns:
        FAISS vectorstore instance
    """
    return _vectorstore_instance.build_vectorstore(spending_data, force_rebuild)

def enhanced_search(
    vectorstore: FAISS, 
    query: str, 
    k: int = 5,
    category_filter: Optional[str] = None,
    amount_range: Optional[Tuple[float, float]] = None,
    date_range: Optional[Tuple[str, str]] = None
) -> List[Tuple[Document, float]]:
    """
    Enhanced search with multiple filter options
    
    Args:
        vectorstore: FAISS vectorstore instance
        query: Search query
        k: Number of results to return
        category_filter: Filter by specific category
        amount_range: Filter by amount range (min, max)
        date_range: Filter by date range (start_date, end_date)
        
    Returns:
        List of (Document, score) tuples
    """
    # Build metadata filter
    metadata_filter = {}
    if category_filter:
        metadata_filter["category"] = category_filter
    
    # Perform search
    results = _vectorstore_instance.enhanced_similarity_search(
        vectorstore, query, k, metadata_filter
    )
    
    # Apply additional filters
    if amount_range:
        min_amount, max_amount = amount_range
        results = [
            (doc, score) for doc, score in results
            if min_amount <= doc.metadata.get("amount", 0) <= max_amount
        ]
    
    if date_range:
        start_date, end_date = date_range
        results = [
            (doc, score) for doc, score in results
            if start_date <= doc.metadata.get("date", "") <= end_date
        ]
    
    return results

def get_vectorstore_stats() -> Dict[str, Any]:
    """Get vectorstore performance statistics"""
    return _vectorstore_instance.get_performance_stats()

def cleanup_vectorstore_cache(max_age_days: int = 7) -> None:
    """Clean up old vectorstore cache files"""
    _vectorstore_instance.cleanup_cache(max_age_days)

# Advanced search utilities
@lru_cache(maxsize=100)
def get_category_suggestions(query: str) -> List[str]:
    """Get category suggestions based on query (cached)"""
    # Common spending categories with keywords
    category_keywords = {
        "Dining": ["food", "restaurant", "eat", "meal", "coffee", "lunch", "dinner"],
        "Groceries": ["grocery", "supermarket", "food shopping", "produce"],
        "Shopping": ["shop", "buy", "purchase", "store", "retail"],
        "Transport": ["gas", "fuel", "uber", "taxi", "transit", "parking"],
        "Entertainment": ["movie", "streaming", "music", "games", "fun"],
        "Healthcare": ["doctor", "pharmacy", "medicine", "health"],
        "Fitness": ["gym", "exercise", "fitness", "workout"],
        "Home Improvement": ["home", "repair", "tools", "hardware"],
        "Electronics": ["tech", "computer", "phone", "gadget"]
    }
    
    query_lower = query.lower()
    suggestions = []
    
    for category, keywords in category_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            suggestions.append(category)
    
    return suggestions[:3]  # Return top 3 suggestions

if __name__ == "__main__":
    # Example usage and testing
    print("🧪 Testing Optimized Vectorstore...")
    
    # Sample spending data
    sample_data = [
        {
            "date": "2024-07-01",
            "merchant": "Starbucks",
            "category": "Dining",
            "amount": 5.75,
            "notes": "Morning coffee"
        },
        {
            "date": "2024-07-02",
            "merchant": "Whole Foods",
            "category": "Groceries",
            "amount": 72.12,
            "notes": "Weekly shopping"
        }
    ]
    
    try:
        # Build vectorstore
        vectorstore = build_vectorstore(sample_data)
        
        # Test search
        results = enhanced_search(
            vectorstore, 
            "coffee purchases", 
            k=2,
            category_filter="Dining"
        )
        
        print(f"✅ Found {len(results)} results")
        
        # Show performance stats
        stats = get_vectorstore_stats()
        print(f"📊 Performance: {stats}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
