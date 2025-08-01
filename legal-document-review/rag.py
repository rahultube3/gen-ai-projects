#!/usr/bin/env python3
"""
Legal Document RAG with Retrieval + Generation
Enhanced RAG system with compliance guardrails for legal document Q&A.
"""

from openai import OpenAI
import numpy as np
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

from main import LegalDocumentRAG
from compliance_guardrails import LegalComplianceGuardrails, ComplianceLevel

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalRAGGenerator:
    """
    Legal Document RAG system with Retrieval + Generation capabilities.
    Integrates document search with OpenAI GPT for comprehensive legal Q&A.
    """
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.STANDARD):
        self.openai_client = None
        self.rag_system = None
        self.compliance = None
        self.generation_history = []
        self._initialize(compliance_level)
    
    def _initialize(self, compliance_level: ComplianceLevel):
        """Initialize the RAG generator with compliance."""
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found. Generation will not be available.")
                self.openai_client = None
            else:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            
            # Initialize RAG system with compliance
            self.rag_system = LegalDocumentRAG(compliance_level)
            self.compliance = LegalComplianceGuardrails(compliance_level)
            
            logger.info("Legal RAG Generator initialized with compliance guardrails")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG generator: {str(e)}")
            raise
    
    def search_similar_docs(self, query: str, top_k: int = 3, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for similar documents using the compliance-aware RAG system.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            user_context: User context for compliance checking
            
        Returns:
            Search results with compliance information
        """
        try:
            if not self.rag_system:
                raise ValueError("RAG system not initialized")
            
            # Use the compliance-aware search from our main system
            search_result = self.rag_system.search_documents(
                query=query,
                top_k=top_k,
                user_context=user_context
            )
            
            # Log the search for audit purposes
            logger.info(f"Document search: '{query[:50]}...' | Results: {search_result.get('total_results', 0)}")
            
            return search_result
            
        except Exception as e:
            logger.error(f"Error in document search: {str(e)}")
            return {
                'results': [],
                'compliance_report': None,
                'search_allowed': False,
                'message': f'Search failed: {str(e)}'
            }
    
    def generate_answer(self, query: str, user_context: Optional[Dict[str, Any]] = None, 
                       model: str = "gpt-4", temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate a legal answer using RAG (Retrieval + Generation).
        
        Args:
            query: Legal question
            user_context: User context for compliance
            model: OpenAI model to use
            temperature: Generation temperature
            
        Returns:
            Generated answer with compliance information
        """
        generation_start = datetime.now()
        
        try:
            # Step 1: Retrieve relevant documents
            search_result = self.search_similar_docs(query, top_k=3, user_context=user_context)
            
            if not search_result['search_allowed']:
                return {
                    'success': False,
                    'answer': None,
                    'compliance_report': search_result.get('compliance_report'),
                    'message': 'Query blocked by compliance validation',
                    'search_results': [],
                    'generation_allowed': False
                }
            
            retrieved_docs = search_result['results']
            
            if not retrieved_docs:
                return {
                    'success': False,
                    'answer': "I couldn't find any relevant legal documents to answer your question.",
                    'compliance_report': search_result.get('compliance_report'),
                    'message': 'No relevant documents found',
                    'search_results': [],
                    'generation_allowed': False
                }
            
            # Step 2: Prepare context from retrieved documents
            context = self._prepare_context(retrieved_docs)
            
            # Step 3: Generate answer using OpenAI
            if not self.openai_client:
                # Fallback to retrieval-only response
                answer = self._create_retrieval_only_response(retrieved_docs)
                generation_method = "retrieval_only"
            else:
                # Full RAG with generation
                answer = self._generate_with_openai(query, context, model, temperature)
                generation_method = "rag_generation"
            
            # Step 4: Validate the generated response for compliance
            response_compliance = self.compliance.validate_response(answer, user_context)
            
            # Step 5: Add legal disclaimers
            final_answer = self._add_legal_disclaimers(answer)
            
            # Step 6: Log the generation for audit
            self._log_generation(query, len(retrieved_docs), response_compliance, user_context)
            
            generation_duration = (datetime.now() - generation_start).total_seconds()
            
            return {
                'success': True,
                'answer': final_answer,
                'compliance_report': response_compliance,
                'search_results': retrieved_docs,
                'generation_allowed': True,
                'generation_method': generation_method,
                'generation_duration_seconds': generation_duration,
                'sources_count': len(retrieved_docs),
                'message': 'Answer generated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error in answer generation: {str(e)}")
            return {
                'success': False,
                'answer': None,
                'compliance_report': None,
                'message': f'Generation failed: {str(e)}',
                'search_results': [],
                'generation_allowed': False
            }
    
    def _prepare_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            doc_context = f"""
Document {i}: {doc.get('title', 'Untitled')}
Category: {doc.get('category', 'unknown')}
Jurisdiction: {doc.get('jurisdiction', 'unknown')}
Content: {doc.get('text', '')[:500]}...
"""
            context_parts.append(doc_context.strip())
        
        return "\n\n".join(context_parts)
    
    def _generate_with_openai(self, query: str, context: str, model: str, temperature: float) -> str:
        """Generate answer using OpenAI GPT."""
        prompt = f"""You are a legal research assistant. Based on the legal documents provided below, answer the legal question clearly and accurately.

IMPORTANT GUIDELINES:
1. Base your answer ONLY on the provided legal documents
2. If the documents don't contain enough information, say so explicitly
3. Use appropriate legal terminology but explain complex concepts
4. Include relevant citations from the provided documents
5. Always add appropriate disclaimers about seeking professional legal advice
6. Do not make definitive legal conclusions without sufficient basis

LEGAL DOCUMENTS:
{context}

QUESTION: {query}

ANSWER:"""

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional legal research assistant. Provide accurate, well-sourced answers based on the provided legal documents."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            return f"I found relevant legal documents but couldn't generate a comprehensive answer due to a technical issue. Please review the source documents directly."
    
    def _create_retrieval_only_response(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Create a response using only retrieved documents (no OpenAI generation)."""
        if not retrieved_docs:
            return "No relevant legal documents were found for your query."
        
        response_parts = [
            "Based on the legal documents in our database, here are the most relevant excerpts:",
            ""
        ]
        
        for i, doc in enumerate(retrieved_docs, 1):
            doc_summary = f"""
{i}. **{doc.get('title', 'Untitled')}** ({doc.get('category', 'unknown')} - {doc.get('jurisdiction', 'unknown')})
   
   {doc.get('text', '')[:300]}...
   
   Relevance Score: {doc.get('similarity', 0):.3f}
"""
            response_parts.append(doc_summary.strip())
        
        response_parts.append("\nPlease review these documents for detailed information relevant to your query.")
        
        return "\n\n".join(response_parts)
    
    def _add_legal_disclaimers(self, answer: str) -> str:
        """Add appropriate legal disclaimers to the answer."""
        disclaimer = """

⚖️ **LEGAL DISCLAIMER**: This information is provided for general informational purposes only and does not constitute legal advice. The information may not reflect the most current legal developments and may not be applicable to your specific situation. For legal advice specific to your circumstances, please consult with a qualified attorney licensed in your jurisdiction."""
        
        return answer + disclaimer
    
    def _log_generation(self, query: str, sources_count: int, compliance_report, user_context: Optional[Dict[str, Any]]):
        """Log the generation for audit purposes."""
        generation_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query[:100] + "..." if len(query) > 100 else query,
            'user_role': user_context.get('role', 'unknown') if user_context else 'unknown',
            'sources_used': sources_count,
            'compliance_score': compliance_report.compliance_score if compliance_report else 0.0,
            'generation_compliant': compliance_report.is_compliant if compliance_report else False
        }
        
        self.generation_history.append(generation_entry)
        logger.info(f"Answer generated: {query[:50]}... | Sources: {sources_count} | Compliant: {generation_entry['generation_compliant']}")
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of generation activities."""
        if not self.generation_history:
            return {
                'total_generations': 0,
                'average_compliance_score': 0.0,
                'openai_available': self.openai_client is not None,
                'rag_system_available': self.rag_system is not None
            }
        
        return {
            'total_generations': len(self.generation_history),
            'recent_generations': self.generation_history[-5:],
            'average_compliance_score': np.mean([entry['compliance_score'] for entry in self.generation_history]),
            'non_compliant_generations': len([entry for entry in self.generation_history if not entry['generation_compliant']]),
            'average_sources_per_query': np.mean([entry['sources_used'] for entry in self.generation_history]),
            'openai_available': self.openai_client is not None,
            'rag_system_available': self.rag_system is not None
        }
    
    def close(self):
        """Clean up resources."""
        if self.rag_system:
            self.rag_system.close()
            logger.info("RAG Generator closed successfully")

def main():
    """Demo the Legal RAG Generator with compliance."""
    print("🏛️  Legal Document RAG Generator Demo")
    print("=" * 50)
    
    try:
        # Initialize the RAG generator
        rag_gen = LegalRAGGenerator(ComplianceLevel.STANDARD)
        
        # Test queries with different user contexts
        test_scenarios = [
            {
                'query': "What are the legal requirements for evicting a tenant?",
                'user_context': {'role': 'attorney', 'access_level': 'confidential'},
                'description': "Attorney Legal Research"
            },
            {
                'query': "How do I form a valid contract?",
                'user_context': {'role': 'client', 'access_level': 'public'},
                'description': "Client Legal Question"
            },
            {
                'query': "What constitutes negligence in tort law?",
                'user_context': {'role': 'paralegal', 'access_level': 'internal'},
                'description': "Paralegal Research"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔍 {scenario['description']}")
            print(f"Query: '{scenario['query']}'")
            print(f"User: {scenario['user_context']['role']} ({scenario['user_context']['access_level']})")
            print("-" * 60)
            
            result = rag_gen.generate_answer(
                scenario['query'],
                user_context=scenario['user_context']
            )
            
            if result['success']:
                print(f"✅ Generation Successful")
                print(f"📊 Sources Used: {result['sources_count']}")
                print(f"⚡ Generation Time: {result.get('generation_duration_seconds', 0):.3f}s")
                print(f"🛡️ Compliance Score: {result['compliance_report'].compliance_score:.3f}")
                print(f"🔧 Method: {result.get('generation_method', 'unknown')}")
                print(f"\n📝 **Answer:**")
                print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
                
                if result['search_results']:
                    print(f"\n📚 **Sources:**")
                    for i, doc in enumerate(result['search_results'], 1):
                        print(f"  {i}. {doc.get('title', 'Untitled')} (Score: {doc.get('similarity', 0):.3f})")
                
            else:
                print(f"❌ Generation Failed: {result['message']}")
                if result['compliance_report']:
                    for violation in result['compliance_report'].violations:
                        print(f"   - {violation.severity}: {violation.message}")
            
            print("\n" + "="*60)
        
        # Show generation summary
        print(f"\n📊 Generation Summary:")
        summary = rag_gen.get_generation_summary()
        for key, value in summary.items():
            if key != 'recent_generations':
                print(f"  {key}: {value}")
        
        # Close the system
        rag_gen.close()
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"❌ Demo failed: {str(e)}")

if __name__ == "__main__":
    main()
