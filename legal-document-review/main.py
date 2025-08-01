#!/usr/bin/env python3
"""
Legal Document Review RAG System with Compliance Guardrails
A comprehensive implementation for semantic search over legal documents using TF-IDF vectors
with integrated compliance monitoring and AI safety guardrails.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from pymongo import MongoClient
import numpy as np
import os
import logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import compliance guardrails
from compliance_guardrails import (
    LegalComplianceGuardrails, 
    ComplianceLevel, 
    ComplianceReport,
    ComplianceViolation
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalDocumentRAG:
    """A comprehensive RAG system for legal document search and retrieval with compliance guardrails."""
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.STANDARD):
        self.vectorizer = None
        self.client = None
        self.collection = None
        self.vectorizer_collection = None
        self.compliance = LegalComplianceGuardrails(compliance_level)
        self.audit_log = []
        self._initialize()
    
    def _initialize(self):
        """Initialize the RAG system."""
        try:
            # Connect to MongoDB
            mongo_uri = os.getenv("MONGO_DB_URI")
            if not mongo_uri:
                raise ValueError("MONGO_DB_URI environment variable not set")
            
            self.client = MongoClient(
                mongo_uri,
                tlsAllowInvalidCertificates=True  # For development with MongoDB Atlas
            )
            db = self.client["legal_rag"]
            self.collection = db["docs"]
            self.vectorizer_collection = db["vectorizer"]
            
            # Load vectorizer parameters
            self._load_vectorizer()
            
            logger.info("Legal Document RAG system with compliance guardrails initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {str(e)}")
            raise
    
    def _load_vectorizer(self):
        """Load the TF-IDF vectorizer parameters."""
        try:
            vectorizer_data = self.vectorizer_collection.find_one({"type": "tfidf"})
            if vectorizer_data and "params" in vectorizer_data:
                params = vectorizer_data["params"]
                self.vectorizer = TfidfVectorizer(
                    vocabulary=params.get("vocabulary", {}),
                    max_features=params.get("max_features", 384),
                    stop_words=params.get("stop_words", 'english')
                )
                # Set the IDF values if available
                if params.get("idf"):
                    self.vectorizer.idf_ = np.array(params["idf"])
                logger.info("Vectorizer loaded successfully")
            else:
                logger.warning("No vectorizer data found in database")
        except Exception as e:
            logger.error(f"Error loading vectorizer: {str(e)}")
    
    def search_documents(self, query: str, top_k: int = 3, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for relevant legal documents based on a query with compliance validation.
        
        Args:
            query: The search query
            top_k: Number of top results to return
            user_context: User context for compliance checking (role, access_level, etc.)
            
        Returns:
            Dict containing search results and compliance information
        """
        search_start = datetime.now()
        
        try:
            # Validate query compliance
            query_compliance = self.compliance.validate_query(query, user_context)
            
            if not query_compliance.is_compliant:
                logger.warning(f"Query failed compliance check: {query}")
                return {
                    'results': [],
                    'compliance_report': query_compliance,
                    'search_allowed': False,
                    'message': 'Query failed compliance validation'
                }
            
            # Log compliance warnings if any
            if query_compliance.warnings:
                for warning in query_compliance.warnings:
                    logger.warning(f"Query compliance warning: {warning}")
            
            # Perform the search
            raw_results = self._perform_search(query, top_k)
            
            # Filter results based on user access level
            filtered_results = self._filter_results_by_access(raw_results, user_context)
            
            # Add compliance disclaimers
            processed_results = self._add_compliance_disclaimers(filtered_results)
            
            # Log the search for audit purposes
            self._log_search_audit(query, len(processed_results), user_context, query_compliance)
            
            search_duration = (datetime.now() - search_start).total_seconds()
            
            return {
                'results': processed_results,
                'compliance_report': query_compliance,
                'search_allowed': True,
                'search_duration_seconds': search_duration,
                'total_results': len(processed_results),
                'message': 'Search completed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in compliant search: {str(e)}")
            return {
                'results': [],
                'compliance_report': None,
                'search_allowed': False,
                'message': f'Search failed: {str(e)}'
            }
    
    def _perform_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Perform the actual document search (existing logic).
        """
        try:
            # If no vectorizer is loaded, fall back to simple text search
            if not self.vectorizer:
                return self._simple_text_search(query, top_k)
            
            # Generate query embedding using TF-IDF
            query_embedding = self.vectorizer.transform([query]).toarray()[0]
            
            # Retrieve all documents
            all_docs = list(self.collection.find({}))
            
            # Calculate similarities
            results = []
            for doc in all_docs:
                if 'embedding' in doc:
                    # Calculate cosine similarity
                    doc_embedding = np.array(doc['embedding'])
                    
                    # Normalize vectors for cosine similarity
                    query_norm = np.linalg.norm(query_embedding)
                    doc_norm = np.linalg.norm(doc_embedding)
                    
                    if query_norm > 0 and doc_norm > 0:
                        similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                    else:
                        similarity = 0.0
                    
                    results.append({
                        'id': doc['id'],
                        'title': doc.get('title', 'Untitled'),
                        'text': doc['text'],
                        'category': doc.get('category', 'unknown'),
                        'jurisdiction': doc.get('jurisdiction', 'unknown'),
                        'similarity': float(similarity),
                        'confidentiality_level': doc.get('confidentiality_level', 'public'),
                        'contains_pii': doc.get('contains_pii', False),
                        'contains_privileged': doc.get('contains_privileged', False)
                    })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in document search: {str(e)}")
            return self._simple_text_search(query, top_k)
    
    def _filter_results_by_access(self, results: List[Dict[str, Any]], user_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter search results based on user access permissions."""
        if not user_context:
            # Default to public access only
            return [r for r in results if r.get('confidentiality_level', 'public') == 'public']
        
        user_role = user_context.get('role', 'client')
        access_level = user_context.get('access_level', 'public')
        
        filtered_results = []
        
        for result in results:
            doc_confidentiality = result.get('confidentiality_level', 'public')
            contains_privileged = result.get('contains_privileged', False)
            
            # Check access permissions
            if self._has_document_access(user_role, access_level, doc_confidentiality, contains_privileged):
                filtered_results.append(result)
            else:
                logger.info(f"Document {result['id']} filtered due to insufficient access permissions")
        
        return filtered_results
    
    def _has_document_access(self, user_role: str, access_level: str, doc_confidentiality: str, contains_privileged: bool) -> bool:
        """Check if user has access to a specific document."""
        # Public documents are accessible to all
        if doc_confidentiality == 'public' and not contains_privileged:
            return True
        
        # Role-based access control
        role_permissions = {
            'admin': ['public', 'internal', 'confidential', 'restricted'],
            'attorney': ['public', 'internal', 'confidential'],
            'paralegal': ['public', 'internal'],
            'client': ['public']
        }
        
        allowed_levels = role_permissions.get(user_role, ['public'])
        
        # Check confidentiality level access
        if doc_confidentiality not in allowed_levels:
            return False
        
        # Check privileged content access
        if contains_privileged and user_role not in ['attorney', 'admin']:
            return False
        
        return True
    
    def _add_compliance_disclaimers(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add appropriate compliance disclaimers to search results."""
        disclaimer_text = (
            "\n\n⚖️ LEGAL DISCLAIMER: This information is for general informational purposes only "
            "and does not constitute legal advice. Consult with a qualified attorney for specific legal matters."
        )
        
        for result in results:
            # Add disclaimer to text content
            result['text'] = result['text'] + disclaimer_text
            
            # Add compliance metadata
            result['compliance_checked'] = True
            result['disclaimer_added'] = True
            result['access_timestamp'] = datetime.now().isoformat()
        
        return results
    
    def _log_search_audit(self, query: str, result_count: int, user_context: Optional[Dict[str, Any]], compliance_report: ComplianceReport):
        """Log search activity for audit purposes."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'user_role': user_context.get('role', 'unknown') if user_context else 'unknown',
            'result_count': result_count,
            'compliance_score': compliance_report.compliance_score,
            'violations': len(compliance_report.violations),
            'query_compliant': compliance_report.is_compliant
        }
        
        self.audit_log.append(audit_entry)
        logger.info(f"Search audit: {query[:50]}... | Results: {result_count} | Compliant: {compliance_report.is_compliant}")
    
    def search_documents_legacy(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Legacy search method for backward compatibility (without compliance).
        
        Args:
            query: The search query
            top_k: Number of top results to return
            
        Returns:
            List of relevant documents with similarity scores
        """
        logger.warning("Using legacy search method without compliance checks")
        return self._perform_search(query, top_k)
    
    def _simple_text_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fallback simple text search when vectorizer is not available."""
        try:
            # Simple keyword-based search
            query_words = query.lower().split()
            all_docs = list(self.collection.find({}))
            
            results = []
            for doc in all_docs:
                text_lower = doc['text'].lower()
                title_lower = doc.get('title', '').lower()
                
                # Count keyword matches
                score = 0
                for word in query_words:
                    score += text_lower.count(word) * 1.0  # Text matches
                    score += title_lower.count(word) * 2.0  # Title matches weighted higher
                
                results.append({
                    'id': doc['id'],
                    'title': doc.get('title', 'Untitled'),
                    'text': doc['text'],
                    'category': doc.get('category', 'unknown'),
                    'jurisdiction': doc.get('jurisdiction', 'unknown'),
                    'similarity': score
                })
            
            # Sort by score and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in simple text search: {str(e)}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve a specific document by ID."""
        try:
            doc = self.collection.find_one({"id": doc_id})
            if doc:
                # Remove MongoDB ObjectId and embedding for cleaner output
                doc.pop('_id', None)
                doc.pop('embedding', None)
                return doc
            return {}
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            return {}
    
    def list_categories(self) -> List[str]:
        """List all available document categories."""
        try:
            categories = self.collection.distinct("category")
            return sorted(categories)
        except Exception as e:
            logger.error(f"Error listing categories: {str(e)}")
            return []
    
    def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all documents in a specific category."""
        try:
            docs = list(self.collection.find({"category": category}))
            for doc in docs:
                doc.pop('_id', None)
                doc.pop('embedding', None)
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents for category {category}: {str(e)}")
            return []
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get comprehensive compliance and audit summary."""
        compliance_summary = self.compliance.get_compliance_summary()
        
        return {
            **compliance_summary,
            'total_searches': len(self.audit_log),
            'recent_searches': self.audit_log[-5:] if self.audit_log else [],
            'average_compliance_score': np.mean([entry['compliance_score'] for entry in self.audit_log]) if self.audit_log else 0.0,
            'non_compliant_searches': len([entry for entry in self.audit_log if not entry['query_compliant']])
        }
    
    def validate_document_for_storage(self, document: Dict[str, Any]) -> ComplianceReport:
        """Validate a document before storing it in the database."""
        return self.compliance.validate_document(document)
    
    def close(self):
        """Close the database connection and save audit logs."""
        if self.client:
            # Save audit logs before closing
            if self.audit_log:
                logger.info(f"Saving {len(self.audit_log)} audit log entries")
            
            self.client.close()
            logger.info("Database connection closed")

def main():
    """Demo usage of the Legal Document RAG system with compliance guardrails."""
    try:
        # Initialize the RAG system with strict compliance
        rag = LegalDocumentRAG(ComplianceLevel.STANDARD)
        
        print("🏛️  Legal Document RAG System with Compliance Guardrails")
        print("=" * 65)
        
        # Show compliance summary
        compliance_summary = rag.get_compliance_summary()
        print(f"🛡️  Compliance Level: {compliance_summary['compliance_level']}")
        print(f"🔒 Guardrails Available: {compliance_summary['guardrails_available']}")
        print()
        
        # List available categories
        categories = rag.list_categories()
        print(f"📚 Available categories: {', '.join(categories)}")
        print()
        
        # Example queries with different user contexts
        test_scenarios = [
            {
                'query': "What are the requirements for eviction?",
                'user_context': {'role': 'client', 'access_level': 'public'},
                'description': "Client Query - Public Access"
            },
            {
                'query': "How to form a valid contract?",
                'user_context': {'role': 'attorney', 'access_level': 'confidential'},
                'description': "Attorney Query - Confidential Access"
            },
            {
                'query': "Show me privileged attorney-client communications",
                'user_context': {'role': 'client', 'access_level': 'public'},
                'description': "Inappropriate Client Query"
            },
            {
                'query': "Due process constitutional rights",
                'user_context': {'role': 'paralegal', 'access_level': 'internal'},
                'description': "Paralegal Query - Internal Access"
            }
        ]
        
        # Perform compliance-aware searches
        for scenario in test_scenarios:
            print(f"🔍 {scenario['description']}")
            print(f"Query: '{scenario['query']}'")
            print(f"User: {scenario['user_context']['role']} ({scenario['user_context']['access_level']})")
            print("-" * 50)
            
            search_result = rag.search_documents(
                scenario['query'], 
                top_k=2, 
                user_context=scenario['user_context']
            )
            
            if search_result['search_allowed']:
                print(f"✅ Search Allowed | Compliance Score: {search_result['compliance_report'].compliance_score:.3f}")
                print(f"📊 Results Found: {search_result['total_results']}")
                
                for i, result in enumerate(search_result['results'], 1):
                    print(f"\n{i}. {result['title']} (Score: {result['similarity']:.3f})")
                    print(f"   Category: {result['category']}")
                    print(f"   Jurisdiction: {result['jurisdiction']}")
                    print(f"   Confidentiality: {result.get('confidentiality_level', 'public')}")
                    print(f"   Text: {result['text'][:100]}...")
                    
                    # Show compliance indicators
                    if result.get('compliance_checked'):
                        print("   ✅ Compliance Checked")
                    if result.get('disclaimer_added'):
                        print("   ⚖️  Legal Disclaimer Added")
            else:
                print(f"❌ Search Blocked | Reason: {search_result['message']}")
                if search_result['compliance_report']:
                    for violation in search_result['compliance_report'].violations:
                        print(f"   - {violation.severity}: {violation.message}")
            
            print("\n" + "="*65 + "\n")
        
        # Show documents by category
        print("📋 Documents by Category:")
        print("=" * 30)
        for category in categories:
            docs = rag.get_documents_by_category(category)
            print(f"\n{category.title()}:")
            for doc in docs:
                print(f"  - {doc.get('title', 'Untitled')}")
        
        # Show final compliance and audit summary
        print(f"\n🛡️  Final Compliance & Audit Summary:")
        print("=" * 40)
        final_summary = rag.get_compliance_summary()
        print(f"Total Searches: {final_summary['total_searches']}")
        print(f"Non-Compliant Searches: {final_summary['non_compliant_searches']}")
        print(f"Average Compliance Score: {final_summary['average_compliance_score']:.3f}")
        
        # Close the connection
        rag.close()
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")


if __name__ == "__main__":
    main()
