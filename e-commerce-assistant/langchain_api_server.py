"""
FastAPI Server for LangChain E-commerce Agent
Provides REST API endpoints for the intelligent agent.
"""

import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from langchain_agent import EcommerceAgentAPI

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: str = Field(default="default_user", description="User identifier")
    session_id: str = Field(default="default", description="Session identifier")

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    user_id: str
    session_id: str
    timestamp: str
    conversation_length: Optional[int] = None

class SessionResponse(BaseModel):
    success: bool
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    active_sessions: int
    services_available: List[str]

# Initialize FastAPI app
app = FastAPI(
    title="E-commerce LangChain Agent API",
    description="Intelligent AI agent for e-commerce operations using MCP microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent API instance
agent_api: Optional[EcommerceAgentAPI] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent_api
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    agent_api = EcommerceAgentAPI(openai_api_key)
    print("🤖 LangChain E-commerce Agent API started successfully!")

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "E-commerce LangChain Agent API",
        "version": "1.0.0",
        "description": "Intelligent AI agent for e-commerce operations",
        "endpoints": {
            "chat": "/chat - Send messages to the AI agent",
            "health": "/health - Check API health and status",
            "sessions": "/sessions - Manage conversation sessions",
            "docs": "/docs - Interactive API documentation"
        },
        "powered_by": "LangChain + MCP Microservices"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global agent_api
    
    if not agent_api:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        active_sessions=len(agent_api.get_active_sessions()),
        services_available=[
            "product-search", "recommendations", "order-management", 
            "chat-assistant", "analytics", "dashboard-generation"
        ]
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Send a message to the AI agent."""
    global agent_api
    
    if not agent_api:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_api.process_message(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/sessions/{session_id}/reset", response_model=SessionResponse)
async def reset_session(session_id: str):
    """Reset a conversation session."""
    global agent_api
    
    if not agent_api:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = agent_api.reset_session(session_id)
    return SessionResponse(**result)

@app.get("/sessions", response_model=List[str])
async def get_active_sessions():
    """Get list of active session IDs."""
    global agent_api
    
    if not agent_api:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return agent_api.get_active_sessions()

@app.get("/sessions/{session_id}/history", response_model=List[Dict])
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    global agent_api
    
    if not agent_api:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        agent = agent_api.get_agent(session_id)
        return agent.get_conversation_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

# Example endpoints for specific e-commerce operations
@app.post("/products/search")
async def search_products(
    query: str,
    user_id: str = "default_user",
    session_id: str = "default"
):
    """Search for products using the AI agent."""
    request = ChatRequest(
        message=f"Search for products: {query}",
        user_id=user_id,
        session_id=session_id
    )
    return await chat_with_agent(request)

@app.post("/orders/analyze")
async def analyze_orders(
    user_id: str,
    session_id: str = "default"
):
    """Analyze orders for a user."""
    request = ChatRequest(
        message=f"Analyze orders and provide insights for user {user_id}",
        user_id=user_id,
        session_id=session_id
    )
    return await chat_with_agent(request)

@app.post("/dashboard/generate")
async def generate_dashboard(
    user_id: str,
    sections: List[str] = ["recommendations", "recent_orders"],
    session_id: str = "default"
):
    """Generate a personalized dashboard."""
    sections_str = ", ".join(sections)
    request = ChatRequest(
        message=f"Generate a personalized dashboard for user {user_id} with sections: {sections_str}",
        user_id=user_id,
        session_id=session_id
    )
    return await chat_with_agent(request)

@app.post("/recommendations/get")
async def get_recommendations(
    user_id: str,
    category: Optional[str] = None,
    session_id: str = "default"
):
    """Get product recommendations for a user."""
    message = f"Get product recommendations for user {user_id}"
    if category:
        message += f" in category {category}"
    
    request = ChatRequest(
        message=message,
        user_id=user_id,
        session_id=session_id
    )
    return await chat_with_agent(request)

# Development server runner
def run_server(host: str = "0.0.0.0", port: int = 8001, reload: bool = True):
    """Run the FastAPI server."""
    uvicorn.run(
        "langchain_api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        print("   Example: export OPENAI_API_KEY='your-api-key-here'")
        exit(1)
    
    print("🚀 Starting LangChain E-commerce Agent API Server...")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🔄 Interactive Docs: http://localhost:8001/redoc")
    
    run_server()
