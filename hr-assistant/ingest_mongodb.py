# HR Assistant Document Ingestion System with MongoDB Vector Storage
# Import required libraries for text processing and MongoDB integration
import pathlib, uuid, json, os
import numpy as np  # For basic vector operations
from pymongo import MongoClient  # For MongoDB database operations
from dotenv import load_dotenv  # For loading environment variables from .env file
from datetime import datetime
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

class OpenAIEmbedder:
    """OpenAI embedding model for generating high-quality document embeddings."""
    
    def __init__(self, model="text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model
        self.dimension = 1536  # text-embedding-3-small dimension
    
    def encode(self, texts):
        """Generate embeddings using OpenAI's embedding API."""
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
        except Exception as e:
            print(f"⚠️  OpenAI embedding failed: {e}")
            print("Falling back to MockEmbedder...")
            # Fallback to mock embedder if OpenAI fails
            mock_embedder = MockEmbedder(dimension=self.dimension)
            return mock_embedder.encode(texts)

class MockEmbedder:
    """Mock embedding model that generates consistent random vectors for demo purposes."""
    
    def __init__(self, dimension=1536):  # Updated to match OpenAI dimension
        self.dimension = dimension
        # Use a fixed seed for consistent results
        np.random.seed(42)
    
    def encode(self, texts):
        """Generate mock embeddings for text inputs."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Generate consistent random vectors based on text hash
        embeddings = []
        for text in texts:
            # Use text hash as seed for consistent vectors for same text
            text_hash = hash(text) % 1000000
            np.random.seed(text_hash)
            embedding = np.random.normal(0, 1, self.dimension)
            # Normalize for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)
        
        return np.array(embeddings)

class MongoVectorStore:
    """MongoDB-based vector store for HR document embeddings and metadata."""
    
    def __init__(self, mongo_uri: str, database_name: str = "hr_assistant", collection_name: str = "document_vectors"):
        """
        Initialize MongoDB vector store connection.
        
        Args:
            mongo_uri (str): MongoDB connection URI from environment variables
            database_name (str): Name of the MongoDB database
            collection_name (str): Name of the collection to store vectors
        """
        try:
            self.client = MongoClient(mongo_uri)
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            
            # Test the connection
            self.client.admin.command('ping')
            print(f"✅ Successfully connected to MongoDB database: {database_name}")
            
            # Create index for efficient searching (optional but recommended)
            self.collection.create_index("doc_id")
            self.collection.create_index("title")
            self.collection.create_index("created_at")
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    def add(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]):
        """
        Add vectors and their metadata to MongoDB.
        
        Args:
            vectors (np.ndarray): Array of embedding vectors
            metadata (List[Dict]): List of metadata dictionaries for each vector
        """
        if len(vectors.shape) == 1:
            vectors = vectors.reshape(1, -1)
        
        # Prepare documents for MongoDB insertion
        documents = []
        for i, vector in enumerate(vectors):
            meta = metadata[i] if isinstance(metadata, list) else metadata
            
            document = {
                "doc_id": meta.get("doc_id", str(uuid.uuid4())),
                "vector": vector.tolist(),  # Convert numpy array to list for MongoDB storage
                "title": meta.get("title", "Unknown"),
                "text": meta.get("text", ""),
                "chunk_index": meta.get("chunk_index", i),
                "char_count": meta.get("char_count", 0),
                "source": meta.get("source", "unknown"),
                "collection": meta.get("collection", "hr_documents"),
                "file_type": meta.get("file_type", "unknown"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            documents.append(document)
        
        # Insert documents into MongoDB
        try:
            result = self.collection.insert_many(documents)
            print(f"✅ Successfully stored {len(result.inserted_ids)} document chunks in MongoDB")
            return result.inserted_ids
        except Exception as e:
            print(f"❌ Error storing documents in MongoDB: {e}")
            raise
    
    def search(self, query_vector: np.ndarray, top_k: int = 5, title_filter: str = None):
        """
        Search for similar vectors using cosine similarity.
        
        Args:
            query_vector (np.ndarray): Query vector to search for
            top_k (int): Number of top results to return
            title_filter (str): Optional filter by document title
            
        Returns:
            tuple: (similarities, metadata) lists
        """
        try:
            # Build MongoDB query filter
            query_filter = {}
            if title_filter:
                query_filter["title"] = {"$regex": title_filter, "$options": "i"}
            
            # Retrieve all vectors from MongoDB
            cursor = self.collection.find(query_filter)
            documents = list(cursor)
            
            if not documents:
                print("⚠️  No documents found in vector store")
                return [], []
            
            # Calculate cosine similarities
            similarities = []
            metadata_results = []
            
            for doc in documents:
                # Handle both old and new document formats
                if "vector" in doc:
                    stored_vector = np.array(doc["vector"])
                    content = doc.get("text", "")
                    doc_id = doc.get("doc_id", str(doc.get("_id", "")))
                    chunk_index = doc.get("chunk_index", 0)
                    char_count = doc.get("char_count", len(content))
                    source = doc.get("source", "unknown")
                    collection = doc.get("collection", "unknown")
                    file_type = doc.get("file_type", "unknown")
                elif "embedding" in doc:
                    stored_vector = np.array(doc["embedding"])
                    content = doc.get("content", "")
                    doc_id = str(doc.get("_id", ""))
                    chunk_index = doc.get("chunk_index", 0)
                    char_count = len(content)
                    source = doc.get("source", "unknown")
                    collection = "document_vectors"
                    file_type = doc.get("type", "markdown")
                else:
                    continue  # Skip documents without embeddings
                
                # Cosine similarity = dot product of normalized vectors
                similarity = np.dot(query_vector, stored_vector)
                similarities.append(similarity)
                
                # Prepare metadata for results
                metadata = {
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "text": content,
                    "chunk_index": chunk_index,
                    "char_count": char_count,
                    "source": source,
                    "collection": collection,
                    "file_type": file_type,
                    "created_at": doc["created_at"]
                }
                metadata_results.append(metadata)
            
            # Get top-k most similar documents
            if similarities:
                top_indices = np.argsort(similarities)[-top_k:][::-1]
                top_similarities = [similarities[i] for i in top_indices]
                top_metadata = [metadata_results[i] for i in top_indices]
                return top_similarities, top_metadata
            else:
                return [], []
                
        except Exception as e:
            print(f"❌ Error searching MongoDB: {e}")
            return [], []
    
    def get_stats(self):
        """Get statistics about the vector store."""
        try:
            total_docs = self.collection.count_documents({})
            
            # Get sample document to determine vector dimension
            sample_doc = self.collection.find_one()
            dimension = len(sample_doc["vector"]) if sample_doc and "vector" in sample_doc else 0
            
            # Estimate storage size (rough calculation)
            storage_size_mb = total_docs * dimension * 8 / (1024 * 1024)  # 8 bytes per float64
            
            # Get unique titles count
            unique_titles = len(self.collection.distinct("title"))
            
            return {
                "total_vectors": total_docs,
                "dimension": dimension,
                "storage_size_mb": storage_size_mb,
                "unique_documents": unique_titles,
                "database": self.db.name,
                "collection": self.collection.name
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear all documents from the collection (useful for testing)."""
        try:
            result = self.collection.delete_many({})
            print(f"🗑️  Cleared {result.deleted_count} documents from MongoDB collection")
            return result.deleted_count
        except Exception as e:
            print(f"❌ Error clearing collection: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()
            print("🔒 MongoDB connection closed")

def get_embedder():
    """Initialize and return the appropriate embedder."""
    print("🤖 Initializing embedding model...")
    try:
        embedder = OpenAIEmbedder()
        print(f"✅ Using OpenAI embeddings (dimension: {embedder.dimension})")
        return embedder
    except Exception as e:
        print(f"⚠️  OpenAI embedder failed: {e}")
        print("📝 Falling back to MockEmbedder...")
        embedder = MockEmbedder(dimension=1536)
        print(f"✅ Using MockEmbedder (dimension: {embedder.dimension})")
        return embedder

# Initialize components
if __name__ == "__main__":
    print("🚀 Initializing HR Assistant Document Ingestion")
    print("=" * 60)
    
    # Get embedder
    embedder = get_embedder()
    INDEX_DIM = embedder.dimension

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_DB_URI')
if not MONGO_URI:
    raise ValueError("❌ MONGO_DB_URI not found in environment variables. Please check your .env file.")

# Initialize MongoDB vector store (lazy initialization)
vector_store = None

def get_vector_store():
    """Get vector store instance with lazy initialization"""
    global vector_store
    if vector_store is None:
        vector_store = MongoVectorStore(MONGO_URI, database_name="hr_assistant", collection_name="document_vectors")
    return vector_store

def chunk_text(text: str, chunk_size: int = 900, chunk_overlap: int = 120) -> List[str]:
    """Simple text chunking function"""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunks.append(text[start:])
            break
        
        # Try to break at sentence endings
        chunk = text[start:end]
        last_period = chunk.rfind('. ')
        last_newline = chunk.rfind('\n')
        
        if last_period > chunk_size - 200:  # If period is reasonably close to end
            end = start + last_period + 2
        elif last_newline > chunk_size - 200:  # If newline is reasonably close to end
            end = start + last_newline + 1
        
        chunks.append(text[start:end])
        start = end - chunk_overlap if chunk_overlap < end else end
    
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def extract_text_from_file(path: str) -> str:
    """
    Extract text from files (simplified - only handles text files).
    
    Args:
        path (str): File path to the document
        
    Returns:
        str: Text content from the file
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error extracting text from {path}: {e}")
        return ""

def ingest_pdf(path: str, doc_meta: dict, embedder=None):
    """
    Complete PDF ingestion pipeline with MongoDB storage:
    1. Extract text from PDF file
    2. Split text into manageable, overlapping chunks
    3. Generate vector embeddings for semantic search capability
    4. Store vectors and metadata in MongoDB for persistent storage
    
    Args:
        path (str): File path to the PDF document
        doc_meta (dict): Additional metadata to store with each chunk
        embedder: Embedding model to use
    """
    if embedder is None:
        embedder = get_embedder()
        
    print(f"📖 Starting ingestion of: {path}")
    
    # Step 1: Extract all text content from the file
    text = extract_text_from_file(path)
    
    if not text.strip():
        print(f"⚠️  No text extracted from {path}")
        return
    
    print(f"📝 Extracted {len(text)} characters of text")
    
    # Step 2: Split text into overlapping chunks
    chunks = chunk_text(text)
    print(f"✂️  Split into {len(chunks)} chunks")
    
    # Step 3: Generate embeddings for each chunk
    vectors = embedder.encode(chunks)
    print(f"🔢 Generated {vectors.shape[0]} embeddings of dimension {vectors.shape[1]}")
    
    # Step 4: Prepare metadata for MongoDB storage
    chunk_metadata = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {
            "doc_id": str(uuid.uuid4()),
            "chunk_index": i,
            "title": pathlib.Path(path).name,
            "text": chunk,
            "char_count": len(chunk),
            **doc_meta
        }
        chunk_metadata.append(chunk_meta)
    
    # Step 5: Store in MongoDB
    get_vector_store().add(vectors, chunk_metadata)
    
    print(f"✅ Successfully ingested {len(chunks)} chunks from {pathlib.Path(path).name}")
    
    # Display current storage statistics
    stats = get_vector_store().get_stats()
    print(f"📊 MongoDB Vector Store Stats:")
    print(f"   📄 Total vectors: {stats['total_vectors']}")
    print(f"   📐 Vector dimension: {stats['dimension']}")
    print(f"   💾 Storage size: {stats['storage_size_mb']:.2f} MB")
    print(f"   📚 Unique documents: {stats['unique_documents']}")
    print(f"   🗄️  Database: {stats['database']}")
    print(f"   📋 Collection: {stats['collection']}")

def search_documents(query: str, top_k: int = 5, title_filter: str = None, embedder=None):
    """
    Search through ingested documents using semantic similarity with MongoDB backend.
    
    Args:
        query (str): Search query text
        top_k (int): Number of top results to return
        title_filter (str): Optional filter by document title
        embedder: Embedding model to use
        
    Returns:
        list: List of matching document chunks with similarity scores
    """
    if embedder is None:
        embedder = get_embedder()
        
    print(f"🔍 Searching MongoDB for: '{query}'")
    if title_filter:
        print(f"📁 Filtering by title: '{title_filter}'")
    
    # Generate embedding for the search query
    query_vector = embedder.encode([query])[0]
    
    # Search in MongoDB vector store
    similarities, metadata_results = get_vector_store().search(query_vector, top_k, title_filter)
    
    # Format results for easy reading
    results = []
    for i, (similarity, metadata) in enumerate(zip(similarities, metadata_results)):
        result = {
            "rank": i + 1,
            "similarity_score": float(similarity),
            "title": metadata["title"],
            "text_preview": metadata["text"][:200] + "..." if len(metadata["text"]) > 200 else metadata["text"],
            "full_text": metadata["text"],
            "doc_id": metadata["doc_id"],
            "chunk_index": metadata["chunk_index"],
            "created_at": metadata["created_at"],
            "source": metadata["source"]
        }
        results.append(result)
    
    print(f"📋 Found {len(results)} relevant results from MongoDB")
    return results

def demo_search():
    """Demonstrate the search functionality with sample queries against MongoDB."""
    print("\n" + "="*60)
    print("🔍 MONGODB SEARCH DEMONSTRATION")
    print("="*60)
    
    # Sample search queries
    queries = [
        "vacation policy",
        "work from home",
        "health insurance benefits", 
        "employee conduct rules",
        "retirement plan"
    ]
    
    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 40)
        
        results = search_documents(query, top_k=3)
        
        for result in results:
            print(f"📄 {result['title']} (Score: {result['similarity_score']:.3f})")
            print(f"   📅 Created: {result['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📝 {result['text_preview']}")
            print()

def create_sample_document():
    """Create a sample text file for testing if no PDFs are available."""
    sample_content = """
    Employee Handbook - Company Policies
    
    Welcome to our company! This handbook contains important information about company policies and procedures.
    
    Vacation Policy:
    All employees are entitled to 15 days of paid vacation per year. Vacation requests must be submitted at least 2 weeks in advance.
    
    Work from Home Policy:
    Employees may work from home up to 2 days per week with manager approval. A dedicated workspace and reliable internet connection are required.
    
    Benefits:
    We offer comprehensive health insurance, dental coverage, and a 401k retirement plan with company matching up to 4%.
    
    Code of Conduct:
    All employees must maintain professional behavior and treat colleagues with respect. Harassment or discrimination will not be tolerated.
    
    Employee Development:
    We provide annual training budgets and encourage continuous learning. Professional development opportunities include conferences, workshops, and online courses.
    
    Performance Reviews:
    Annual performance reviews are conducted each December. Goals are set collaboratively between employees and managers.
    """
    
    docs_dir = pathlib.Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    sample_file = docs_dir / "employee_handbook.txt"
    with open(sample_file, "w") as f:
        f.write(sample_content)
    
    print(f"📝 Created sample document: {sample_file}")
    return str(sample_file)

def ingest_text_file(path: str, doc_meta: dict, embedder=None):
    """Ingest a text file into MongoDB vector store."""
    if embedder is None:
        embedder = get_embedder()
        
    print(f"📖 Starting ingestion of text file: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"❌ Error reading file {path}: {e}")
        return
    
    if not text.strip():
        print(f"⚠️  No text found in {path}")
        return
    
    print(f"📝 Read {len(text)} characters of text")
    
    # Split text into chunks
    chunks = chunk_text(text)
    print(f"✂️  Split into {len(chunks)} chunks")
    
    # Generate embeddings
    vectors = embedder.encode(chunks)
    print(f"🔢 Generated {vectors.shape[0]} embeddings of dimension {vectors.shape[1]}")
    
    # Prepare metadata
    chunk_metadata = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {
            "doc_id": str(uuid.uuid4()),
            "chunk_index": i,
            "title": pathlib.Path(path).name,
            "text": chunk,
            "char_count": len(chunk),
            **doc_meta
        }
        chunk_metadata.append(chunk_meta)
    
    # Store in MongoDB
    get_vector_store().add(vectors, chunk_metadata)
    print(f"✅ Successfully ingested {len(chunks)} chunks from {pathlib.Path(path).name}")

# Main execution block
if __name__ == "__main__":
    try:
        print("🚀 HR Assistant Document Ingestion System with MongoDB")
        print("="*60)
        
        # Check if docs directory exists
        docs_path = pathlib.Path("docs")
        if not docs_path.exists():
            print("📁 Creating docs directory...")
            docs_path.mkdir()
        
        # Option to clear existing data (uncomment for fresh start)
        # print("🗑️  Clearing existing MongoDB data...")
        # vector_store.clear_collection()
        
        # Look for PDF files to ingest
        pdf_files = list(docs_path.glob("*.pdf"))
        text_files = list(docs_path.glob("*.txt"))
        
        total_files = len(pdf_files) + len(text_files)
        
        if total_files > 0:
            print(f"📚 Found {total_files} file(s) to ingest:")
            
            # Process PDF files
            for pdf_file in pdf_files:
                print(f"   📄 {pdf_file.name}")
                ingest_pdf(
                    str(pdf_file), 
                    {
                        "source": "file_upload", 
                        "collection": "hr_documents",
                        "file_type": "pdf"
                    },
                    embedder
                )
                print()
            
            # Process text files
            for text_file in text_files:
                print(f"   📝 {text_file.name}")
                ingest_text_file(
                    str(text_file),
                    {
                        "source": "file_upload",
                        "collection": "hr_documents", 
                        "file_type": "text"
                    },
                    embedder
                )
                print()
        
        else:
            print("📝 No files found. Creating sample document for demonstration...")
            sample_file = create_sample_document()
            ingest_text_file(
                sample_file,
                {
                    "source": "sample_document",
                    "collection": "hr_documents",
                    "file_type": "text"
                },
                embedder
            )
        
        # Display final statistics
        print("\n" + "="*60)
        print("📊 FINAL MONGODB STATISTICS")
        print("="*60)
        
        stats = get_vector_store().get_stats()
        print(f"📄 Total vectors stored: {stats['total_vectors']}")
        print(f"📐 Vector dimension: {stats['dimension']}")
        print(f"💾 Estimated storage size: {stats['storage_size_mb']:.2f} MB")
        print(f"📚 Unique documents: {stats['unique_documents']}")
        print(f"🗄️  MongoDB Database: {stats['database']}")
        print(f"📋 MongoDB Collection: {stats['collection']}")
        
        # Run search demonstration if we have data
        if stats['total_vectors'] > 0:
            demo_search()
        
        print(f"\n✨ MongoDB ingestion complete! HR Assistant vector store is ready for queries.")
        print(f"🔗 Connected to: {MONGO_URI.split('@')[1].split('/')[0] if '@' in MONGO_URI else 'MongoDB'}")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        
    finally:
        # Always close the MongoDB connection
        if vector_store is not None:
            vector_store.close()
