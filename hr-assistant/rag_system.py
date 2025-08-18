# HR Assistant RAG System with LLM Integration and Guardrails
# Retrieval-Augmented Generation using MongoDB Vector Store + OpenAI/Anthropic

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# FastAPI and web components
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LLM integrations
import openai
from openai import OpenAI

# MongoDB and vector components
from ingest_mongodb import get_vector_store, OpenAIEmbedder, MockEmbedder

# Guardrails integration
from guardrails import validate_query, validate_response, get_violations_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RAGConfig:
    """Configuration for RAG system from environment variables."""
    
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_DB_URI')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.mongo_uri:
            raise ValueError("❌ MONGO_DB_URI not found in environment variables")
        if not self.openai_api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in environment variables")
        
        # RAG-specific settings
        self.retrieval_top_k = int(os.getenv('RAG_TOP_K', '5'))
        self.chunk_overlap_threshold = float(os.getenv('RAG_OVERLAP_THRESHOLD', '0.1'))
        self.llm_model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))

class RAGResponse(BaseModel):
    """Response model for RAG queries."""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_count: int
    processing_time_ms: float
    model_used: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RAGQuery(BaseModel):
    """Request model for RAG queries."""
    query: str = Field(..., description="User's question or query")
    max_sources: int = Field(5, description="Maximum number of source documents to retrieve")
    include_sources: bool = Field(True, description="Whether to include source documents in response")
    context_window: int = Field(3000, description="Maximum context length for LLM")

class HRAssistantRAG:
    """
    HR Assistant RAG System
    Combines MongoDB vector search with LLM for intelligent question answering
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        
        # Initialize components
        logger.info("🚀 Initializing HR Assistant RAG System")
        
        # MongoDB Vector Store
        self.vector_store = get_vector_store()
        
        # Embedding model (same as ingestion for consistency)
        try:
            self.embedder = OpenAIEmbedder()
            logger.info(f"✅ Using OpenAI embeddings (dimension: {self.embedder.dimension})")
        except Exception as e:
            logger.warning(f"⚠️  OpenAI embedder failed: {e}, falling back to MockEmbedder")
            self.embedder = MockEmbedder(dimension=1536)
            logger.info(f"✅ Using MockEmbedder (dimension: {self.embedder.dimension})")
        
        # OpenAI client
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        
        logger.info(f"✅ RAG System initialized with model: {config.llm_model}")
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from MongoDB vector store.
        
        Args:
            query (str): User query
            top_k (int): Number of documents to retrieve
            
        Returns:
            List[Dict]: Retrieved documents with metadata
        """
        logger.info(f"🔍 Retrieving documents for: '{query}'")
        
        # Generate query embedding
        query_vector = self.embedder.encode([query])[0]
        
        # Search MongoDB vector store
        similarities, metadata_results = self.vector_store.search(
            query_vector, 
            top_k=top_k
        )
        
        # Format results
        documents = []
        for i, (similarity, metadata) in enumerate(zip(similarities, metadata_results)):
            doc = {
                "rank": i + 1,
                "similarity_score": float(similarity),
                "title": metadata["title"],
                "text": metadata["text"],
                "chunk_index": metadata["chunk_index"],
                "doc_id": metadata["doc_id"],
                "source": metadata["source"],
                "created_at": metadata["created_at"]
            }
            documents.append(doc)
        
        logger.info(f"📋 Retrieved {len(documents)} relevant documents")
        return documents
    
    def create_context_prompt(self, query: str, documents: List[Dict[str, Any]], context_window: int = 3000) -> str:
        """
        Create a context-aware prompt for the LLM.
        
        Args:
            query (str): User query
            documents (List[Dict]): Retrieved documents
            context_window (int): Maximum context length
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Build context from retrieved documents
        context_parts = []
        current_length = 0
        
        for doc in documents:
            text_snippet = doc["text"]
            snippet_length = len(text_snippet)
            
            if current_length + snippet_length < context_window:
                context_parts.append(f"""
Document: {doc['title']} (Chunk {doc['chunk_index']})
Relevance Score: {doc['similarity_score']:.3f}
Content: {text_snippet}
---""")
                current_length += snippet_length
            else:
                break
        
        context = "\n".join(context_parts)
        
        # Create the prompt
        prompt = f"""You are an HR Assistant AI helping employees find information from company documents. 
Based on the retrieved context below, provide a comprehensive and helpful answer to the user's question.

CONTEXT FROM HR DOCUMENTS:
{context}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer the question directly and comprehensively
2. Use information from the provided context documents
3. If the context doesn't contain enough information, say so clearly
4. Cite which documents you're referencing when possible
5. Be helpful and professional in your response
6. If the question is about policies, provide specific details and any relevant procedures

ANSWER:"""

        return prompt
    
    def generate_llm_response(self, prompt: str) -> str:
        """
        Generate response using OpenAI LLM.
        
        Args:
            prompt (str): Context-aware prompt
            
        Returns:
            str: LLM generated response
        """
        try:
            logger.info(f"🤖 Generating response with {self.config.llm_model}")
            
            response = self.openai_client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful HR Assistant AI that provides accurate information based on company documents."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=False
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"✅ Generated response ({len(answer)} characters)")
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}")
            return f"I apologize, but I encountered an error while generating a response. Please try again or contact support. Error: {str(e)}"
    
    def answer_query(self, query: str, max_sources: int = 5, include_sources: bool = True, context_window: int = 3000) -> RAGResponse:
        """
        Main RAG pipeline: Retrieve + Generate answer.
        
        Args:
            query (str): User question
            max_sources (int): Maximum number of source documents
            include_sources (bool): Whether to include sources in response
            context_window (int): Maximum context length
            
        Returns:
            RAGResponse: Complete RAG response with answer and sources
        """
        import time
        start_time = time.time()
        
        logger.info(f"🎯 Processing RAG query: '{query}'")
        
        # Step 1: Retrieve relevant documents
        documents = self.retrieve_relevant_documents(query, top_k=max_sources)
        
        # Step 2: Create context-aware prompt
        prompt = self.create_context_prompt(query, documents, context_window)
        
        # Step 3: Generate LLM response
        answer = self.generate_llm_response(prompt)
        
        # Step 4: Format response
        processing_time = (time.time() - start_time) * 1000
        
        sources = documents if include_sources else []
        
        response = RAGResponse(
            query=query,
            answer=answer,
            sources=sources,
            retrieval_count=len(documents),
            processing_time_ms=round(processing_time, 2),
            model_used=self.config.llm_model,
            timestamp=datetime.utcnow(),
            metadata={}
        )
        
        logger.info(f"✅ RAG query completed in {processing_time:.2f}ms")
        return response

# Initialize RAG system
config = RAGConfig()
rag_system = HRAssistantRAG(config)

# FastAPI application for RAG endpoints
app = FastAPI(
    title="HR Assistant RAG API",
    description="Retrieval-Augmented Generation system for HR document queries",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", summary="RAG System Status")
async def root():
    """RAG system information and health check."""
    try:
        stats = rag_system.vector_store.get_stats()
        return {
            "service": "HR Assistant RAG API",
            "version": "3.0.0",
            "status": "operational",
            "llm_model": config.llm_model,
            "vector_store": {
                "total_documents": stats["total_vectors"],
                "database": stats["database"],
                "collection": stats["collection"]
            },
            "endpoints": {
                "ask": "POST /ask",
                "query": "GET /query?q=...",
                "health": "/health",
                "docs": "/docs"
            }
        }
    except Exception as e:
        return {
            "service": "HR Assistant RAG API",
            "status": "error",
            "error": str(e)
        }

@app.post("/ask", response_model=RAGResponse, summary="Ask HR Question (RAG)")
async def ask_question(query: RAGQuery):
    """
    Ask a question using RAG (Retrieval-Augmented Generation) with guardrails.
    
    This endpoint:
    1. Validates query through guardrails system
    2. Searches MongoDB vector store for relevant documents
    3. Creates context-aware prompt
    4. Generates answer using LLM
    5. Validates and filters response
    6. Returns comprehensive response with sources
    """
    try:
        # Apply guardrails to query
        is_allowed, violations = validate_query(query.query, user_id=None)
        
        if not is_allowed:
            violation_messages = [v.message for v in violations]
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Query rejected by content policy",
                    "violations": violation_messages,
                    "message": "Your query contains content that violates our usage policy. Please rephrase your question appropriately."
                }
            )
        
        # Process query through RAG system
        response = rag_system.answer_query(
            query=query.query,
            max_sources=query.max_sources,
            include_sources=query.include_sources,
            context_window=query.context_window
        )
        
        # Apply guardrails to response
        filtered_answer, response_violations = validate_response(
            response.answer, query.query, user_id=None
        )
        
        # Update response with filtered content
        response.answer = filtered_answer
        
        # Add guardrails metadata
        response.metadata["guardrails"] = {
            "query_violations": len(violations),
            "response_violations": len(response_violations),
            "content_filtered": len(response_violations) > 0
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@app.get("/query", summary="Simple RAG Query (GET)")
async def simple_query(
    q: str,
    sources: int = 5,
    include_sources: bool = True
):
    """
    Simple GET endpoint for RAG queries with guardrails.
    Useful for quick testing and integration.
    """
    try:
        # Apply guardrails to query
        is_allowed, violations = validate_query(q, user_id=None)
        
        if not is_allowed:
            violation_messages = [v.message for v in violations]
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Query rejected by content policy",
                    "violations": violation_messages,
                    "message": "Your query contains content that violates our usage policy."
                }
            )
        
        query_obj = RAGQuery(
            query=q,
            max_sources=sources,
            include_sources=include_sources
        )
        
        response = rag_system.answer_query(
            query=query_obj.query,
            max_sources=query_obj.max_sources,
            include_sources=query_obj.include_sources
        )
        
        # Apply guardrails to response
        filtered_answer, response_violations = validate_response(
            response.answer, q, user_id=None
        )
        
        response.answer = filtered_answer
        response.metadata["guardrails"] = {
            "query_violations": len(violations),
            "response_violations": len(response_violations),
            "content_filtered": len(response_violations) > 0
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/guardrails/summary", summary="Guardrails Violations Summary")
async def guardrails_summary(hours: int = 24):
    """Get summary of guardrails violations in the specified time period."""
    try:
        summary = get_violations_summary(hours)
        return {
            "status": "success",
            "data": summary,
            "message": f"Guardrails summary for last {hours} hours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guardrails summary: {str(e)}")

@app.get("/health", summary="System Health Check")
async def health_check():
    """Health check for RAG system components."""
    try:
        # Test MongoDB connection
        stats = rag_system.vector_store.get_stats()
        
        # Test OpenAI connection (simple ping)
        test_response = rag_system.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "mongodb": "connected",
                "openai": "connected",
                "vector_store": f"{stats['total_vectors']} documents",
                "llm_model": config.llm_model
            },
            "version": "3.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "3.0.0"
        }

@app.get("/examples", summary="Example RAG Queries")
async def get_examples():
    """Get example queries to test the RAG system."""
    return {
        "example_queries": [
            {
                "query": "What is the vacation policy?",
                "description": "Learn about time off and vacation policies"
            },
            {
                "query": "How do I enroll in health insurance?",
                "description": "Get information about health insurance enrollment"
            },
            {
                "query": "What are the retirement benefits?",
                "description": "Learn about 401k and retirement planning"
            },
            {
                "query": "Can I work from home?",
                "description": "Find remote work and flexible work policies"
            },
            {
                "query": "What employee development programs are available?",
                "description": "Discover training and career development opportunities"
            }
        ],
        "usage": {
            "post": "POST /ask with JSON body",
            "get": "GET /query?q=your+question+here"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup."""
    logger.info("🚀 HR Assistant RAG API starting up...")
    logger.info(f"📊 MongoDB: {config.mongo_uri.split('@')[1].split('/')[0] if '@' in config.mongo_uri else 'connected'}")
    logger.info(f"🤖 LLM Model: {config.llm_model}")
    
    try:
        stats = rag_system.vector_store.get_stats()
        logger.info(f"✅ Vector store ready: {stats['total_vectors']} documents available")
    except Exception as e:
        logger.error(f"❌ Vector store error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("🔒 HR Assistant RAG API shutting down...")
    try:
        rag_system.vector_store.close()
        logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Development server
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HR Assistant RAG API")
    print("🔗 Retrieval-Augmented Generation with MongoDB + OpenAI")
    print("📚 Documentation available at: http://localhost:8001/docs")
    print("🔍 Example: http://localhost:8001/query?q=What+is+the+vacation+policy")
    
    uvicorn.run(
        "rag_system:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
