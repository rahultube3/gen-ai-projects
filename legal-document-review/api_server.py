#!/usr/bin/env python3
"""
Legal Document Review API with Compliance Guardrails
FastAPI-based REST API for the legal document RAG system with integrated compliance.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from main import LegalDocumentRAG
from compliance_guardrails import ComplianceLevel, ComplianceReport

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Legal Document Review API",
    description="AI-powered legal document search with compliance guardrails",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG system instance
rag_system: Optional[LegalDocumentRAG] = None

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")
    user_role: str = Field(default="client", description="User role (client, paralegal, attorney, admin)")
    access_level: str = Field(default="public", description="User access level")

class DocumentValidationRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    category: str = Field(..., description="Legal category")
    jurisdiction: str = Field(..., description="Jurisdiction")
    confidentiality_level: str = Field(default="public", description="Confidentiality level")
    contains_pii: bool = Field(default=False, description="Contains PII")
    contains_privileged: bool = Field(default=False, description="Contains privileged information")

class SearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    compliance_report: Dict[str, Any]
    search_allowed: bool
    total_results: int
    search_duration_seconds: float
    message: str

class ComplianceResponse(BaseModel):
    is_compliant: bool
    violations: List[Dict[str, Any]]
    warnings: List[str]
    recommendations: List[str]
    compliance_score: float
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    compliance_level: str
    guardrails_available: bool
    database_connected: bool

# Dependency to get current user context
def get_user_context(
    user_role: str = Query("client", description="User role"),
    access_level: str = Query("public", description="Access level")
) -> Dict[str, str]:
    """Extract user context from request parameters."""
    return {
        "role": user_role,
        "access_level": access_level
    }

# Initialize RAG system
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup."""
    global rag_system
    try:
        compliance_level = ComplianceLevel(os.getenv("COMPLIANCE_LEVEL", "standard"))
        rag_system = LegalDocumentRAG(compliance_level)
        logger.info("Legal Document RAG API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    global rag_system
    if rag_system:
        rag_system.close()
        logger.info("RAG system shut down successfully")

# API Routes

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with compliance status."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        summary = rag_system.get_compliance_summary()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            compliance_level=summary["compliance_level"],
            guardrails_available=summary["guardrails_available"],
            database_connected=True  # Would check actual DB connection in production
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user_context: Dict[str, str] = Depends(get_user_context)
):
    """Search legal documents with compliance validation."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        # Override user context with request data if provided
        search_context = {
            "role": request.user_role,
            "access_level": request.access_level
        }
        
        # Perform search with compliance checks
        search_result = rag_system.search_documents(
            query=request.query,
            top_k=request.max_results,
            user_context=search_context
        )
        
        # Convert compliance report to dict for JSON serialization
        compliance_dict = {}
        if search_result.get('compliance_report'):
            report = search_result['compliance_report']
            compliance_dict = {
                'is_compliant': report.is_compliant,
                'compliance_score': report.compliance_score,
                'violations': [
                    {
                        'type': v.violation_type,
                        'severity': v.severity,
                        'message': v.message,
                        'field': v.field,
                        'suggested_fix': v.suggested_fix
                    } for v in report.violations
                ],
                'warnings': report.warnings,
                'recommendations': report.recommendations,
                'timestamp': report.timestamp.isoformat()
            }
        
        return SearchResponse(
            success=True,
            results=search_result.get('results', []),
            compliance_report=compliance_dict,
            search_allowed=search_result.get('search_allowed', False),
            total_results=search_result.get('total_results', 0),
            search_duration_seconds=search_result.get('search_duration_seconds', 0.0),
            message=search_result.get('message', 'Search completed')
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/validate-document", response_model=ComplianceResponse)
async def validate_document(request: DocumentValidationRequest):
    """Validate a document for compliance before storage."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        document_dict = request.dict()
        
        # Validate document compliance
        compliance_report = rag_system.validate_document_for_storage(document_dict)
        
        return ComplianceResponse(
            is_compliant=compliance_report.is_compliant,
            violations=[
                {
                    'type': v.violation_type,
                    'severity': v.severity,
                    'message': v.message,
                    'field': v.field,
                    'suggested_fix': v.suggested_fix
                } for v in compliance_report.violations
            ],
            warnings=compliance_report.warnings,
            recommendations=compliance_report.recommendations,
            compliance_score=compliance_report.compliance_score,
            timestamp=compliance_report.timestamp.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Document validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@app.get("/categories")
async def get_categories():
    """Get all available legal document categories."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        categories = rag_system.list_categories()
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/documents/category/{category}")
async def get_documents_by_category(category: str):
    """Get all documents in a specific category."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        documents = rag_system.get_documents_by_category(category)
        return {
            "category": category,
            "documents": documents,
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Failed to get documents for category {category}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@app.get("/compliance/summary")
async def get_compliance_summary():
    """Get comprehensive compliance and audit summary."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        summary = rag_system.get_compliance_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get compliance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance summary: {str(e)}")

@app.get("/compliance/audit-log")
async def get_audit_log(limit: int = Query(50, ge=1, le=1000)):
    """Get recent audit log entries."""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG system not initialized")
        
        # In a production system, this would come from a persistent audit log
        audit_entries = rag_system.audit_log[-limit:] if hasattr(rag_system, 'audit_log') else []
        
        return {
            "audit_entries": audit_entries,
            "total_shown": len(audit_entries),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit log: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting Legal Document Review API on {host}:{port}")
    
    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
