# HR Assistant Document Ingestion System with MongoDB Vector Storage
# Import required libraries for PDF processing, text chunking, and MongoDB integration
import pathlib, uuid, json, os
from pypdf import PdfReader  # For reading PDF files
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For intelligent text chunking
import numpy as np  # For basic vector operations
from pymongo import MongoClient  # For MongoDB database operations
from dotenv import load_dotenv  # For loading environment variables from .env file
from datetime import datetime
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

class MockEmbedder:
    """Mock embedding model that generates consistent random vectors for demo purposes."""
    
    def __init__(self, dimension=384):
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
                stored_vector = np.array(doc["vector"])
                # Cosine similarity = dot product of normalized vectors
                similarity = np.dot(query_vector, stored_vector)
                similarities.append(similarity)
                
                # Prepare metadata for results
                metadata = {
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "text": doc["text"],
                    "chunk_index": doc["chunk_index"],
                    "char_count": doc["char_count"],
                    "source": doc["source"],
                    "collection": doc["collection"],
                    "file_type": doc["file_type"],
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

# Initialize components
print("🚀 Initializing HR Assistant with MongoDB Vector Storage")
print("="*60)

# Initialize the mock embedding model
embedder = MockEmbedder(dimension=384)
INDEX_DIM = 384

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_DB_URI')
if not MONGO_URI:
    raise ValueError("❌ MONGO_DB_URI not found in environment variables. Please check your .env file.")

# Initialize MongoDB vector store
vector_store = MongoVectorStore(MONGO_URI, database_name="hr_assistant", collection_name="document_vectors")

# Text splitter configuration for optimal chunk sizes
splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,           # Target size for each text chunk (in characters)
    chunk_overlap=120,        # Overlap between chunks to preserve context
    separators=["\n\n", "\n", ". ", " "]  # Split on paragraphs, then lines, then sentences, then words
)

def extract_pdf_text(path: str) -> str:
    """
    Extract text from PDF using pypdf library.
    
    Args:
        path (str): File path to the PDF document
        
    Returns:
        str: Combined text from all pages in the PDF
    """
    try:
        reader = PdfReader(path)
        text_pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_pages.append(page_text)
        return "\n\n".join(text_pages)
    except Exception as e:
        print(f"❌ Error extracting text from {path}: {e}")
        return ""

def ingest_pdf(path: str, doc_meta: dict):
    """
    Complete PDF ingestion pipeline with MongoDB storage:
    1. Extract text from PDF file
    2. Split text into manageable, overlapping chunks
    3. Generate vector embeddings for semantic search capability
    4. Store vectors and metadata in MongoDB for persistent storage
    
    Args:
        path (str): File path to the PDF document
        doc_meta (dict): Additional metadata to store with each chunk
    """
    print(f"📖 Starting ingestion of: {path}")
    
    # Step 1: Extract all text content from the PDF
    text = extract_pdf_text(path)
    
    if not text.strip():
        print(f"⚠️  No text extracted from {path}")
        return
    
    print(f"📝 Extracted {len(text)} characters of text")
    
    # Step 2: Split text into overlapping chunks
    chunks = splitter.split_text(text)
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
    vector_store.add(vectors, chunk_metadata)
    
    print(f"✅ Successfully ingested {len(chunks)} chunks from {pathlib.Path(path).name}")
    
    # Display current storage statistics
    stats = vector_store.get_stats()
    print(f"📊 MongoDB Vector Store Stats:")
    print(f"   📄 Total vectors: {stats['total_vectors']}")
    print(f"   📐 Vector dimension: {stats['dimension']}")
    print(f"   💾 Storage size: {stats['storage_size_mb']:.2f} MB")
    print(f"   📚 Unique documents: {stats['unique_documents']}")
    print(f"   🗄️  Database: {stats['database']}")
    print(f"   📋 Collection: {stats['collection']}")

def search_documents(query: str, top_k: int = 5, title_filter: str = None):
    """
    Search through ingested documents using semantic similarity with MongoDB backend.
    
    Args:
        query (str): Search query text
        top_k (int): Number of top results to return
        title_filter (str): Optional filter by document title
        
    Returns:
        list: List of matching document chunks with similarity scores
    """
    print(f"🔍 Searching MongoDB for: '{query}'")
    if title_filter:
        print(f"📁 Filtering by title: '{title_filter}'")
    
    # Generate embedding for the search query
    query_vector = embedder.encode([query])[0]
    
    # Search in MongoDB vector store
    similarities, metadata_results = vector_store.search(query_vector, top_k, title_filter)
    
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

def ingest_text_file(path: str, doc_meta: dict):
    """Ingest a text file into MongoDB vector store."""
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
    chunks = splitter.split_text(text)
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
    vector_store.add(vectors, chunk_metadata)
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
                    }
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
                    }
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
                }
            )
        
        # Display final statistics
        print("\n" + "="*60)
        print("📊 FINAL MONGODB STATISTICS")
        print("="*60)
        
        stats = vector_store.get_stats()
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
        vector_store.close()

def extract_pdf_text(path: str) -> str:
    """
    Extract text from PDF using pypdf library.
    This function reads PDF files and extracts all text content from each page.
    
    Args:
        path (str): File path to the PDF document
        
    Returns:
        str: Combined text from all pages in the PDF
    """
    try:
        # Use pypdf to read the PDF file
        reader = PdfReader(path)
        
        # Extract text from each page and combine into single string
        # Filter out None values and empty strings that might occur
        text_pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():  # Only add non-empty pages
                text_pages.append(page_text)
        
        # Join all pages with double newlines to separate page content
        return "\n\n".join(text_pages)
        
    except Exception as e:
        print(f"❌ Error extracting text from {path}: {e}")
        return ""

def ingest_pdf(path: str, doc_meta: dict):
    """
    Complete PDF ingestion pipeline with detailed comments:
    1. Extract text from PDF file
    2. Split text into manageable, overlapping chunks
    3. Generate vector embeddings for semantic search capability
    4. Add vectors to our simple vector store for fast retrieval
    5. Store metadata for each chunk to enable content retrieval
    
    Args:
        path (str): File path to the PDF document
        doc_meta (dict): Additional metadata to store with each chunk
    """
    
    print(f"📖 Starting ingestion of: {path}")
    
    # Step 1: Extract all text content from the PDF
    text = extract_pdf_text(path)
    
    if not text.strip():
        print(f"⚠️  No text extracted from {path}")
        return
    
    print(f"📝 Extracted {len(text)} characters of text")
    
    # Step 2: Split text into overlapping chunks for better context retention
    # The splitter intelligently breaks text at natural boundaries (paragraphs, sentences)
    chunks = splitter.split_text(text)
    
    print(f"✂️  Split into {len(chunks)} chunks")
    
    # Step 3: Generate embeddings (vector representations) for each chunk
    # These vectors enable semantic similarity search across content
    vectors = embedder.encode(chunks)
    
    print(f"🔢 Generated {vectors.shape[0]} embeddings of dimension {vectors.shape[1]}")
    
    # Step 4: Add vectors to our vector store for fast similarity search
    # We store each chunk as a separate vector for granular search
    chunk_metadata = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {
            "doc_id": str(uuid.uuid4()),        # Unique identifier for this chunk
            "chunk_index": i,                   # Position within the original document
            "title": pathlib.Path(path).name,   # Original filename for reference
            "text": chunk,                      # The actual text content
            "char_count": len(chunk),           # Length of this chunk
            **doc_meta                          # Additional metadata passed in
        }
        chunk_metadata.append(chunk_meta)
        meta_store.append(chunk_meta)
    
    # Add all vectors to the store at once
    vector_store.add(vectors, chunk_metadata)
    
    print(f"✅ Successfully ingested {len(chunks)} chunks from {pathlib.Path(path).name}")
    
    # Display current storage statistics
    stats = vector_store.get_stats()
    print(f"📊 Vector store stats: {stats['total_vectors']} vectors, {stats['storage_size_mb']:.2f} MB")

def search_documents(query: str, top_k: int = 5):
    """
    Search through ingested documents using semantic similarity.
    
    Args:
        query (str): Search query text
        top_k (int): Number of top results to return
        
    Returns:
        list: List of matching document chunks with similarity scores
    """
    
    print(f"🔍 Searching for: '{query}'")
    
    # Generate embedding for the search query
    query_vector = embedder.encode([query])[0]
    
    # Search for similar vectors in our store
    similarities, metadata_results = vector_store.search(query_vector, top_k)
    
    # Format results for easy reading
    results = []
    for i, (similarity, metadata) in enumerate(zip(similarities, metadata_results)):
        result = {
            "rank": i + 1,
            "similarity_score": float(similarity),
            "title": metadata["title"],
            "text_preview": metadata["text"][:200] + "..." if len(metadata["text"]) > 200 else metadata["text"],
            "full_text": metadata["text"],
            "doc_id": metadata["doc_id"]
        }
        results.append(result)
    
    print(f"📋 Found {len(results)} relevant results")
    
    return results

# Example usage and testing functions
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
    """
    
    # Create docs directory if it doesn't exist
    docs_dir = pathlib.Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Save sample content to a text file
    sample_file = docs_dir / "employee_handbook.txt"
    with open(sample_file, "w") as f:
        f.write(sample_content)
    
    print(f"� Created sample document: {sample_file}")
    return str(sample_file)

def demo_search():
    """Demonstrate the search functionality with sample queries."""
    
    print("\n" + "="*60)
    print("🔍 SEARCH DEMONSTRATION")
    print("="*60)
    
    # Sample search queries
    queries = [
        "vacation policy",
        "work from home",
        "health insurance benefits",
        "employee conduct rules"
    ]
    
    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        print("-" * 40)
        
        results = search_documents(query, top_k=3)
        
        for result in results:
            print(f"📄 {result['title']} (Score: {result['similarity_score']:.3f})")
            print(f"   {result['text_preview']}")
            print()

# Main execution block
if __name__ == "__main__":
    print("🚀 HR Assistant Document Ingestion System")
    print("=" * 50)
    
    # Check if docs directory exists
    docs_path = pathlib.Path("docs")
    
    if not docs_path.exists():
        print("📁 Creating docs directory...")
        docs_path.mkdir()
    
    # Look for PDF files to ingest
    pdf_files = list(docs_path.glob("*.pdf"))
    
    if pdf_files:
        print(f"📚 Found {len(pdf_files)} PDF file(s) to ingest:")
        
        for pdf_file in pdf_files:
            print(f"   📄 {pdf_file.name}")
            
            # Ingest each PDF with metadata
            ingest_pdf(
                str(pdf_file), 
                {
                    "source": "file_upload", 
                    "collection": "hr_documents",
                    "file_type": "pdf"
                }
            )
            print()
    
    else:
        print("📝 No PDF files found. Creating sample document for demonstration...")
        
        # Create and ingest a sample text document for testing
        sample_file = create_sample_document()
        
        # For text files, we'll read and ingest them manually
        with open(sample_file, 'r') as f:
            text = f.read()
        
        print(f"📖 Processing sample document: {sample_file}")
        
        # Split text into chunks
        chunks = splitter.split_text(text)
        vectors = embedder.encode(chunks)
        
        # Store chunks with metadata
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                "doc_id": str(uuid.uuid4()),
                "chunk_index": i,
                "title": pathlib.Path(sample_file).name,
                "text": chunk,
                "char_count": len(chunk),
                "source": "sample_document",
                "collection": "hr_documents",
                "file_type": "text"
            }
            chunk_metadata.append(chunk_meta)
            meta_store.append(chunk_meta)
        
        vector_store.add(vectors, chunk_metadata)
        
        print(f"✅ Ingested {len(chunks)} chunks from sample document")
    
    # Display final statistics
    stats = vector_store.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total vectors: {stats['total_vectors']}")
    print(f"   Vector dimension: {stats['dimension']}")
    print(f"   Storage size: {stats['storage_size_mb']:.2f} MB")
    print(f"   Metadata entries: {len(meta_store)}")
    
    # Run search demonstration
    if meta_store:
        demo_search()
    
    print("\n✨ Ingestion complete! Vector store is ready for queries.")
