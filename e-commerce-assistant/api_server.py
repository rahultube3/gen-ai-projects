#!/usr/bin/env python3
"""
FastAPI Server for E-commerce RAG Assistant
Provides REST API endpoints for the RAG assistant functionality.
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from rag_assistant import EcommerceRAGAssistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global assistant instance
assistant_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global assistant_instance
    
    # Startup
    logger.info("🚀 Starting E-commerce RAG Assistant API...")
    try:
        assistant_instance = EcommerceRAGAssistant()
        logger.info("✅ RAG Assistant initialized successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG Assistant: {e}")
        raise
    
    # Shutdown
    logger.info("🔄 Shutting down E-commerce RAG Assistant API...")
    if assistant_instance:
        assistant_instance.close()
    logger.info("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="E-commerce RAG Assistant API",
    description="REST API for intelligent e-commerce product search and recommendations using RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to send to the assistant")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation tracking")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant's response")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now)

class ProductRecommendationRequest(BaseModel):
    query: str = Field(..., description="Search query for product recommendations")
    limit: int = Field(default=5, ge=1, le=20, description="Number of recommendations to return")

class ProductRecommendation(BaseModel):
    name: str
    price: float
    brand: str
    description: str
    rating: Optional[float]
    stock: int

class ProductRecommendationResponse(BaseModel):
    recommendations: List[ProductRecommendation]
    query: str
    count: int

class ProductSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for products")
    category: Optional[str] = Field(None, description="Product category filter")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    limit: int = Field(default=10, ge=1, le=50, description="Number of results to return")

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    assistant_ready: bool

def get_assistant():
    """Dependency to get the assistant instance."""
    global assistant_instance
    if not assistant_instance:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    return assistant_instance

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "E-commerce RAG Assistant API",
        "version": "1.0.0",
        "description": "REST API for intelligent e-commerce product search and recommendations",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "products/search": "/products/search",
            "products/recommendations": "/products/recommendations",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    global assistant_instance
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
        assistant_ready=assistant_instance is not None
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    assistant: EcommerceRAGAssistant = Depends(get_assistant)
):
    """Chat with the RAG assistant."""
    try:
        logger.info(f"Chat request: {request.message}")
        
        # Get response from assistant
        response = assistant.chat(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/products/recommendations", response_model=ProductRecommendationResponse)
async def get_recommendations(
    request: ProductRecommendationRequest,
    assistant: EcommerceRAGAssistant = Depends(get_assistant)
):
    """Get product recommendations based on query."""
    try:
        logger.info(f"Recommendation request: {request.query}")
        
        # Get recommendations from assistant
        recommendations = assistant.get_product_recommendations(
            request.query, 
            limit=request.limit
        )
        
        # Convert to response format
        recommendation_list = [
            ProductRecommendation(
                name=rec["name"],
                price=rec["price"],
                brand=rec["brand"],
                description=rec["description"],
                rating=rec.get("rating"),
                stock=rec["stock"]
            )
            for rec in recommendations
        ]
        
        return ProductRecommendationResponse(
            recommendations=recommendation_list,
            query=request.query,
            count=len(recommendation_list)
        )
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/products/search")
async def search_products(
    request: ProductSearchRequest,
    assistant: EcommerceRAGAssistant = Depends(get_assistant)
):
    """Search for products using various filters."""
    try:
        logger.info(f"Product search request: {request.query}")
        
        # Build search query
        search_query = request.query
        if request.category:
            search_query += f" category:{request.category}"
        if request.min_price:
            search_query += f" min_price:{request.min_price}"
        if request.max_price:
            search_query += f" max_price:{request.max_price}"
        
        # Use chat interface for product search
        response = assistant.chat(f"Search for products: {search_query}")
        
        return {
            "query": request.query,
            "filters": {
                "category": request.category,
                "min_price": request.min_price,
                "max_price": request.max_price,
                "limit": request.limit
            },
            "results": response,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Product search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/products/categories")
async def get_categories(assistant: EcommerceRAGAssistant = Depends(get_assistant)):
    """Get available product categories."""
    try:
        # Use assistant to get category information
        response = assistant.chat("What product categories are available?")
        
        return {
            "categories": response,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/stats")
async def get_stats(assistant: EcommerceRAGAssistant = Depends(get_assistant)):
    """Get system and database statistics."""
    try:
        # Get order statistics
        order_stats = assistant.chat("Show me order statistics")
        
        return {
            "order_statistics": order_stats,
            "api_version": "1.0.0",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
