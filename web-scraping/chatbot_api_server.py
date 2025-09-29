#!/usr/bin/env python3
"""
Wikipedia RAG API Server
FastAPI server exposing Wikipedia RAG functionality for the AngularJS chatbot
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
import asyncio
import time
import logging

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from wikipedia_rag_scraper import WikipediaRAGIntegrator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG integrator
rag_integrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG system on startup"""
    global rag_integrator
    try:
        logger.info("🚀 Initializing Wikipedia RAG system...")
        rag_integrator = WikipediaRAGIntegrator("chatbot_knowledge")
        logger.info("✅ RAG system initialized successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG system: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down RAG system...")

# Create FastAPI app
app = FastAPI(
    title="Wikipedia RAG Chatbot API",
    description="API for AngularJS chatbot with Wikipedia RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[Dict] = []
    confidence: float = 0.0
    timestamp: str

class WikipediaPage(BaseModel):
    url: HttpUrl
    
class AddPageRequest(BaseModel):
    url: str

class AddPageResponse(BaseModel):
    success: bool
    message: str
    page_title: Optional[str] = None
    sections_added: Optional[int] = None

class CollectionInfo(BaseModel):
    name: str
    document_count: int
    sample_pages: List[str] = []

class SystemStatus(BaseModel):
    status: str
    rag_system_active: bool
    openai_configured: bool
    collections: List[CollectionInfo] = []
    uptime: str

# Global state
start_time = time.time()
processing_jobs = {}

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Wikipedia RAG Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Health check endpoint"""
    uptime_seconds = int(time.time() - start_time)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
    
    collections_info = []
    if rag_integrator:
        try:
            count = rag_integrator.collection.count()
            collections_info.append(CollectionInfo(
                name="chatbot_knowledge",
                document_count=count,
                sample_pages=[]  # Could add sample page titles here
            ))
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
    
    return SystemStatus(
        status="healthy",
        rag_system_active=rag_integrator is not None,
        openai_configured=bool(os.getenv('OPENAI_API_KEY')),
        collections=collections_info,
        uptime=uptime_str
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint - process user message and return AI response"""
    if not rag_integrator:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        logger.info(f"🤖 Processing chat message: {message.message[:100]}...")
        
        # Use the RAG system to get intelligent response
        response = rag_integrator.query_wikipedia_knowledge(message.message, n_results=3)
        
        # If response is just a string (error case), wrap it
        if isinstance(response, str):
            return ChatResponse(
                response=response,
                sources=[],
                confidence=0.0,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
        
        # For successful responses, response is the actual answer string
        # We need to get the search results separately for sources
        search_results = rag_integrator.collection.query(
            query_texts=[message.message],
            n_results=3
        )
        
        sources = []
        confidence = 0.0
        
        if search_results.get('documents') and search_results['documents'][0]:
            documents = search_results['documents'][0]
            distances = search_results.get('distances', [[]])[0]
            metadatas = search_results.get('metadatas', [[]])[0]
            
            for doc, dist, meta in zip(documents, distances, metadatas):
                similarity = 1.0 - (dist / 2.0) if dist else 0.0
                sources.append({
                    "title": meta.get('page_title', 'Unknown') if meta else 'Unknown',
                    "section": meta.get('section_title', 'Unknown') if meta else 'Unknown',
                    "similarity": round(similarity, 3),
                    "preview": doc[:150] + "..." if len(doc) > 150 else doc
                })
            
            # Calculate average confidence
            if distances:
                confidence = sum(1.0 - (d / 2.0) for d in distances) / len(distances)
        
        return ChatResponse(
            response=response,
            sources=sources,
            confidence=round(confidence, 3),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/add-page", response_model=AddPageResponse)
async def add_wikipedia_page(request: AddPageRequest, background_tasks: BackgroundTasks):
    """Add a Wikipedia page to the knowledge base"""
    if not rag_integrator:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    # Validate URL
    if not request.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    if 'wikipedia.org/wiki/' not in request.url:
        raise HTTPException(status_code=400, detail="Only Wikipedia URLs are supported")
    
    try:
        logger.info(f"📚 Adding Wikipedia page: {request.url}")
        
        # Add page synchronously for immediate response
        success = rag_integrator.add_wikipedia_page(request.url)
        
        if success:
            # Extract page title from URL
            page_title = request.url.split('/')[-1].replace('_', ' ')
            
            return AddPageResponse(
                success=True,
                message=f"Successfully added Wikipedia page: {page_title}",
                page_title=page_title,
                sections_added=None  # Could count sections if needed
            )
        else:
            return AddPageResponse(
                success=False,
                message="Failed to add Wikipedia page. Please check the URL and try again."
            )
            
    except Exception as e:
        logger.error(f"❌ Add page error: {e}")
        return AddPageResponse(
            success=False,
            message=f"Error adding page: {str(e)}"
        )

@app.get("/collections", response_model=List[CollectionInfo])
async def get_collections():
    """Get information about available collections"""
    if not rag_integrator:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    try:
        count = rag_integrator.collection.count()
        
        # Get sample documents to extract page titles
        sample_pages = []
        if count > 0:
            sample_docs = rag_integrator.collection.get(limit=5)
            if sample_docs and sample_docs.get('metadatas'):
                seen_titles = set()
                for meta in sample_docs['metadatas']:
                    if meta and 'page_title' in meta:
                        title = meta['page_title']
                        if title not in seen_titles and len(seen_titles) < 3:
                            seen_titles.add(title)
                            sample_pages.append(title)
        
        return [CollectionInfo(
            name="chatbot_knowledge",
            document_count=count,
            sample_pages=sample_pages
        )]
        
    except Exception as e:
        logger.error(f"❌ Collections error: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting collections: {str(e)}")

@app.delete("/collections/reset")
async def reset_collection():
    """Reset/clear the knowledge base"""
    if not rag_integrator:
        raise HTTPException(status_code=500, detail="RAG system not initialized")
    
    try:
        # Create a new collection (this effectively clears the old one)
        rag_integrator.collection.delete()
        rag_integrator.collection = rag_integrator.chroma_client.create_collection(
            name="chatbot_knowledge",
            metadata={"description": "Wikipedia content for chatbot"}
        )
        
        return {"message": "Knowledge base cleared successfully"}
        
    except Exception as e:
        logger.error(f"❌ Reset error: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting collection: {str(e)}")

@app.get("/sample-queries", response_model=List[str])
async def get_sample_queries():
    """Get sample queries for the chatbot"""
    return [
        "What is health data and why is it important?",
        "How does digital health technology work?",
        "What are electronic health records?",
        "Explain health informatics and its benefits",
        "What are the privacy concerns with health data?",
        "How is health data used in medical research?",
        "What is the difference between structured and unstructured health data?",
        "How does telemedicine improve healthcare delivery?"
    ]

if __name__ == "__main__":
    import uvicorn
    
    # Check if OpenAI API key is configured
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("⚠️  OpenAI API key not found. Chatbot responses may be limited.")
    
    logger.info("🚀 Starting Wikipedia RAG Chatbot API server...")
    uvicorn.run(
        "chatbot_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )