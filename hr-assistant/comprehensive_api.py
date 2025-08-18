# Comprehensive HR Assistant API with RAG, MCP, LLM Integration, and Guardrails
# All-in-one API server combining vector search, RAG, MCP capabilities, and content protection

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dotenv import load_dotenv

# FastAPI components
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our components
from rag_system import HRAssistantRAG, RAGConfig, RAGQuery, RAGResponse
from ingest_mongodb import MongoVectorStore, MockEmbedder

# Guardrails integration
from guardrails import validate_query, validate_response, get_violations_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Pydantic models for comprehensive API
class ChatMessage(BaseModel):
    """Chat message model for conversational interface."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    """Chat conversation request."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    use_rag: bool = Field(True, description="Whether to use RAG for answer generation")
    max_sources: int = Field(5, description="Maximum source documents to retrieve")

class ChatResponse(BaseModel):
    """Chat conversation response."""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source documents if RAG was used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    model_used: str = Field(..., description="LLM model used for response")

class DocumentUploadStatus(BaseModel):
    """Document upload and processing status."""
    filename: str
    status: str  # "processing", "completed", "failed"
    chunks_created: Optional[int] = None
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None

class SystemStatus(BaseModel):
    """Complete system status."""
    service: str
    version: str
    status: str
    components: Dict[str, Any]
    database_stats: Dict[str, Any]
    uptime_seconds: float

# Initialize comprehensive API
class ComprehensiveHRAPI:
    """
    Comprehensive HR Assistant API
    Combines RAG, vector search, chat interface, and system management
    """
    
    def __init__(self):
        self.config = RAGConfig()
        self.rag_system = HRAssistantRAG(self.config)
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.start_time = datetime.utcnow()
        
        # Active WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        logger.info("✅ Comprehensive HR API initialized")
    
    async def add_connection(self, websocket: WebSocket):
        """Add WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔗 WebSocket connected. Total: {len(self.active_connections)}")
    
    def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_message(self, message: str):
        """Broadcast message to all connected WebSockets."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.remove_connection(connection)
    
    def get_conversation(self, conversation_id: str) -> List[ChatMessage]:
        """Get conversation history."""
        return self.conversations.get(conversation_id, [])
    
    def add_message_to_conversation(self, conversation_id: str, message: ChatMessage):
        """Add message to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(message)
        
        # Keep only last 20 messages per conversation
        if len(self.conversations[conversation_id]) > 20:
            self.conversations[conversation_id] = self.conversations[conversation_id][-20:]
    
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """Process chat message with optional RAG."""
        import time
        import uuid
        
        start_time = time.time()
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Add user message to conversation
        user_message = ChatMessage(role="user", content=request.message)
        self.add_message_to_conversation(conversation_id, user_message)
        
        if request.use_rag:
            # Use RAG for response
            logger.info(f"💬 Processing chat with RAG: '{request.message}'")
            
            rag_response = self.rag_system.answer_query(
                query=request.message,
                max_sources=request.max_sources,
                include_sources=True
            )
            
            response_text = rag_response.answer
            sources = rag_response.sources
            model_used = rag_response.model_used
            
        else:
            # Direct LLM response without RAG
            logger.info(f"💬 Processing chat without RAG: '{request.message}'")
            
            # Get conversation context
            conversation_history = self.get_conversation(conversation_id)
            context_messages = []
            
            for msg in conversation_history[-10:]:  # Last 10 messages
                context_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current message
            context_messages.append({
                "role": "user", 
                "content": request.message
            })
            
            # Generate response
            try:
                response = self.rag_system.openai_client.chat.completions.create(
                    model=self.config.llm_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful HR Assistant. Provide concise, helpful responses."}
                    ] + context_messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
                response_text = response.choices[0].message.content.strip()
                sources = None
                model_used = self.config.llm_model
            except Exception as e:
                response_text = f"I apologize, but I encountered an error: {str(e)}"
                sources = None
                model_used = "error"
        
        # Add assistant response to conversation
        assistant_message = ChatMessage(role="assistant", content=response_text)
        self.add_message_to_conversation(conversation_id, assistant_message)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            sources=sources,
            processing_time_ms=round(processing_time, 2),
            model_used=model_used
        )

# Initialize API system
api_system = ComprehensiveHRAPI()

# Create FastAPI app
app = FastAPI(
    title="HR Assistant Comprehensive API",
    description="Complete HR Assistant with RAG, Chat, Vector Search, and MCP integration",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", summary="API Overview")
async def root():
    """Comprehensive API overview and status."""
    try:
        stats = api_system.rag_system.vector_store.get_stats()
        uptime = (datetime.utcnow() - api_system.start_time).total_seconds()
        
        return {
            "service": "HR Assistant Comprehensive API",
            "version": "4.0.0",
            "status": "operational",
            "uptime_seconds": round(uptime, 2),
            "capabilities": {
                "rag_queries": "POST /rag/ask",
                "chat_interface": "POST /chat",
                "vector_search": "POST /search",
                "websocket_chat": "WS /ws/chat",
                "document_management": "GET /documents",
                "system_health": "GET /health"
            },
            "llm_model": api_system.config.llm_model,
            "database": {
                "total_documents": stats["total_vectors"],
                "database": stats["database"],
                "collection": stats["collection"],
                "storage_mb": stats["storage_size_mb"]
            },
            "active_connections": len(api_system.active_connections)
        }
    except Exception as e:
        return {
            "service": "HR Assistant Comprehensive API",
            "status": "error",
            "error": str(e)
        }

# RAG Endpoints with Guardrails
@app.post("/rag/ask", response_model=RAGResponse, summary="RAG Question Answering with Guardrails")
async def rag_ask(query: RAGQuery):
    """Ask questions using Retrieval-Augmented Generation with content protection."""
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
                    "message": "Your query contains content that violates our usage policy."
                }
            )
        
        # Process query through RAG system
        response = api_system.rag_system.answer_query(
            query=query.query,
            max_sources=query.max_sources,
            include_sources=query.include_sources,
            context_window=query.context_window
        )
        
        # Apply guardrails to response
        filtered_answer, response_violations = validate_response(
            response.answer, query.query, user_id=None
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
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@app.get("/rag/query", summary="Simple RAG Query with Guardrails")
async def rag_simple_query(q: str, sources: int = 5):
    """Simple GET endpoint for RAG queries with content protection."""
    query_obj = RAGQuery(query=q, max_sources=sources)
    return await rag_ask(query_obj)

# Chat Endpoints with Guardrails
@app.post("/chat", response_model=ChatResponse, summary="Chat with HR Assistant (Protected)")
async def chat(request: ChatRequest):
    """Conversational interface with the HR Assistant with content protection."""
    try:
        # Apply guardrails to message
        is_allowed, violations = validate_query(request.message, user_id=request.user_id)
        
        if not is_allowed:
            violation_messages = [v.message for v in violations]
            return ChatResponse(
                message="I'm sorry, but I can't process your message as it violates our usage policy. Please rephrase your question appropriately.",
                conversation_id=request.conversation_id or "error",
                sources=[],
                metadata={
                    "error": "Content policy violation",
                    "violations": violation_messages,
                    "guardrails": {
                        "query_violations": len(violations),
                        "blocked": True
                    }
                }
            )
        
        # Process chat message
        response = await api_system.process_chat_message(request)
        
        # Apply guardrails to response
        filtered_message, response_violations = validate_response(
            response.message, request.message, user_id=request.user_id
        )
        
        response.message = filtered_message
        response.metadata["guardrails"] = {
            "query_violations": len(violations),
            "response_violations": len(response_violations),
            "content_filtered": len(response_violations) > 0
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/chat/conversations/{conversation_id}", summary="Get Conversation History")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history."""
    conversation = api_system.get_conversation(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": conversation,
        "message_count": len(conversation)
    }

# WebSocket Chat
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await api_system.add_connection(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process chat request
            chat_request = ChatRequest(**message_data)
            response = await api_system.process_chat_message(chat_request)
            
            # Send response back to client
            await websocket.send_text(json.dumps({
                "type": "response",
                "data": response.dict()
            }))
            
    except WebSocketDisconnect:
        api_system.remove_connection(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        api_system.remove_connection(websocket)

# Vector Search Endpoints
@app.post("/search", summary="Vector Document Search")
async def vector_search(query: str, top_k: int = 5, title_filter: Optional[str] = None):
    """Search documents using vector similarity."""
    try:
        documents = api_system.rag_system.retrieve_relevant_documents(query, top_k)
        return {
            "query": query,
            "results": documents,
            "total_results": len(documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Document Management
@app.get("/documents", summary="List All Documents")
async def list_documents():
    """List all documents in the system."""
    try:
        pipeline = [
            {"$group": {"_id": "$title", "count": {"$sum": 1}, "latest": {"$max": "$created_at"}}},
            {"$sort": {"latest": -1}}
        ]
        
        cursor = api_system.rag_system.vector_store.collection.aggregate(pipeline)
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

# System Management
@app.get("/health", response_model=SystemStatus, summary="System Health Check")
async def health_check():
    """Comprehensive system health check."""
    try:
        stats = api_system.rag_system.vector_store.get_stats()
        uptime = (datetime.utcnow() - api_system.start_time).total_seconds()
        
        # Test LLM connection
        test_response = api_system.rag_system.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        
        return SystemStatus(
            service="HR Assistant Comprehensive API",
            version="4.0.0",
            status="healthy",
            components={
                "mongodb": "connected",
                "openai": "connected",
                "rag_system": "operational",
                "websocket_connections": len(api_system.active_connections),
                "conversations": len(api_system.conversations)
            },
            database_stats=stats,
            uptime_seconds=round(uptime, 2)
        )
    except Exception as e:
        uptime = (datetime.utcnow() - api_system.start_time).total_seconds()
        return SystemStatus(
            service="HR Assistant Comprehensive API",
            version="4.0.0",
            status="unhealthy",
            components={"error": str(e)},
            database_stats={},
            uptime_seconds=round(uptime, 2)
        )

@app.get("/guardrails/summary", summary="Guardrails Violations Summary")
async def guardrails_summary(hours: int = 24):
    """Get comprehensive summary of guardrails violations."""
    try:
        summary = get_violations_summary(hours)
        return {
            "status": "success",
            "data": summary,
            "message": f"Guardrails summary for last {hours} hours",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guardrails summary: {str(e)}")

@app.get("/stats", summary="Detailed System Statistics")
async def get_detailed_stats():
    """Get detailed system statistics and metrics."""
    try:
        stats = api_system.rag_system.vector_store.get_stats()
        uptime = (datetime.utcnow() - api_system.start_time).total_seconds()
        
        return {
            "system": {
                "service": "HR Assistant Comprehensive API",
                "version": "4.0.0",
                "uptime_seconds": round(uptime, 2),
                "start_time": api_system.start_time.isoformat()
            },
            "database": stats,
            "llm": {
                "model": api_system.config.llm_model,
                "max_tokens": api_system.config.max_tokens,
                "temperature": api_system.config.temperature
            },
            "connections": {
                "active_websockets": len(api_system.active_connections),
                "total_conversations": len(api_system.conversations),
                "total_messages": sum(len(conv) for conv in api_system.conversations.values())
            },
            "rag_config": {
                "top_k": api_system.config.retrieval_top_k,
                "overlap_threshold": api_system.config.chunk_overlap_threshold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("🚀 HR Assistant Comprehensive API starting up...")
    logger.info(f"🤖 LLM Model: {api_system.config.llm_model}")
    logger.info(f"📊 MongoDB: Connected")
    
    try:
        stats = api_system.rag_system.vector_store.get_stats()
        logger.info(f"✅ Ready to serve: {stats['total_vectors']} documents available")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("🔒 HR Assistant Comprehensive API shutting down...")
    
    # Close WebSocket connections
    for connection in api_system.active_connections[:]:
        try:
            await connection.close()
        except:
            pass
    
    # Close database connection
    try:
        api_system.rag_system.vector_store.close()
        logger.info("✅ All resources cleaned up")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

# Development server
if __name__ == "__main__":
    print("🚀 HR Assistant Comprehensive API")
    print("🔗 RAG + Chat + Vector Search + WebSocket + MCP Integration")
    print("📚 Full documentation: http://localhost:8002/docs")
    print("💬 WebSocket chat: ws://localhost:8002/ws/chat")
    print("🔍 Try: curl 'http://localhost:8002/rag/query?q=vacation+policy'")
    
    uvicorn.run(
        "comprehensive_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
