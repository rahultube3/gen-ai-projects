# HR Assistant API Server with MongoDB Vector Storage
# FastAPI web server for the HR document search system

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import numpy as np
from datetime import datetime

# Import our MongoDB components
from ingest_mongodb import MongoVectorStore, MockEmbedder

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="HR Assistant API",
    description="MongoDB-powered HR document search and management system",
    version="2.0.0"
)

# Add CORS middleware for web interface compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
MONGO_URI = os.getenv('MONGO_DB_URI')
if not MONGO_URI:
    raise ValueError("❌ MONGO_DB_URI not found in environment variables")

vector_store = MongoVectorStore(MONGO_URI, database_name="hr_assistant", collection_name="document_vectors")
embedder = MockEmbedder(dimension=384)

# Pydantic models for API requests/responses
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    title_filter: Optional[str] = None

class SearchResult(BaseModel):
    rank: int
    similarity_score: float
    title: str
    text_preview: str
    full_text: str
    doc_id: str
    chunk_index: int
    created_at: datetime
    source: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float

class StatsResponse(BaseModel):
    total_vectors: int
    dimension: int
    storage_size_mb: float
    unique_documents: int
    database: str
    collection: str
    status: str

# API Endpoints

@app.get("/", summary="API Status")
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": "HR Assistant API with MongoDB Vector Storage",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "search": "/search",
            "stats": "/stats", 
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.post("/search", response_model=SearchResponse, summary="Search HR Documents")
async def search_documents(request: SearchRequest):
    """
    Search through HR documents using semantic similarity.
    
    - **query**: Natural language search query
    - **top_k**: Number of results to return (default: 5)
    - **title_filter**: Optional filter by document title
    """
    try:
        import time
        start_time = time.time()
        
        # Generate embedding for the search query
        query_vector = embedder.encode([request.query])[0]
        
        # Search in MongoDB vector store
        similarities, metadata_results = vector_store.search(
            query_vector, 
            request.top_k, 
            request.title_filter
        )
        
        # Format results
        results = []
        for i, (similarity, metadata) in enumerate(zip(similarities, metadata_results)):
            result = SearchResult(
                rank=i + 1,
                similarity_score=float(similarity),
                title=metadata["title"],
                text_preview=metadata["text"][:200] + "..." if len(metadata["text"]) > 200 else metadata["text"],
                full_text=metadata["text"],
                doc_id=metadata["doc_id"],
                chunk_index=metadata["chunk_index"],
                created_at=metadata["created_at"],
                source=metadata["source"]
            )
            results.append(result)
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search", summary="Simple Search (GET)")
async def search_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results"),
    title_filter: Optional[str] = Query(None, description="Filter by title")
):
    """
    Simple GET endpoint for searching documents.
    Useful for quick testing and browser-based queries.
    """
    request = SearchRequest(query=q, top_k=top_k, title_filter=title_filter)
    return await search_documents(request)

@app.get("/stats", response_model=StatsResponse, summary="Database Statistics")
async def get_stats():
    """Get current MongoDB vector store statistics."""
    try:
        stats = vector_store.get_stats()
        
        return StatsResponse(
            total_vectors=stats["total_vectors"],
            dimension=stats["dimension"],
            storage_size_mb=stats["storage_size_mb"],
            unique_documents=stats["unique_documents"],
            database=stats["database"],
            collection=stats["collection"],
            status="healthy"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@app.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test MongoDB connection
        stats = vector_store.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "mongodb": "connected",
            "total_documents": stats["total_vectors"],
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "2.0.0"
        }

@app.get("/documents", summary="List Document Titles")
async def list_documents():
    """Get a list of all unique document titles in the system."""
    try:
        # Get unique document titles from MongoDB
        pipeline = [
            {"$group": {"_id": "$title", "count": {"$sum": 1}, "latest": {"$max": "$created_at"}}},
            {"$sort": {"latest": -1}}
        ]
        
        cursor = vector_store.collection.aggregate(pipeline)
        documents = list(cursor)
        
        return {
            "documents": [
                {
                    "title": doc["_id"],
                    "chunk_count": doc["count"],
                    "latest_update": doc["latest"]
                }
                for doc in documents
            ],
            "total_documents": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document listing failed: {str(e)}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("🚀 HR Assistant API starting up...")
    print(f"📊 MongoDB connection: {MONGO_URI.split('@')[1].split('/')[0] if '@' in MONGO_URI else 'MongoDB'}")
    
    # Test the connection
    try:
        stats = vector_store.get_stats()
        print(f"✅ Connected to MongoDB: {stats['total_vectors']} vectors available")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    print("🔒 HR Assistant API shutting down...")
    vector_store.close()
    print("✅ MongoDB connection closed")

# Development server runner
if __name__ == "__main__":
    import uvicorn
    
    print("🌐 Starting HR Assistant API Server")
    print("📚 MongoDB-powered document search system")
    print("🔗 API documentation will be available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server_mongodb:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
