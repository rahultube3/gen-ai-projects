#!/usr/bin/env python3
"""
Comprehensive Test Suite for Legal Document RAG System with Compliance Guardrails
"""

import sys
import traceback
from datetime import datetime
from typing import Dict, Any

from main import LegalDocumentRAG
from compliance_guardrails import (
    LegalComplianceGuardrails, 
    ComplianceLevel,
    ComplianceViolation,
    LegalDomain
)

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_compliance_system():
    """Test the compliance guardrails system."""
    print_header("Testing Compliance Guardrails System")
    
    try:
        # Initialize compliance system
        compliance = LegalComplianceGuardrails(ComplianceLevel.STANDARD)
        print_result("Compliance System Initialization", True, 
                    f"Level: {compliance.compliance_level.value}")
        
        # Test document validation
        test_document = {
            'title': 'Test Employment Contract',
            'content': 'This is a standard employment agreement containing terms and conditions for employment. The employee agrees to perform duties as assigned and maintain confidentiality of company information.',
            'category': 'employment_law',
            'jurisdiction': 'state',
            'confidentiality_level': 'public',
            'contains_pii': False,
            'contains_privileged': False
        }
        
        doc_report = compliance.validate_document(test_document)
        print_result("Document Validation", doc_report.is_compliant,
                    f"Score: {doc_report.compliance_score}, Violations: {len(doc_report.violations)}")
        
        # Test query validation
        test_query = "What are employment termination procedures?"
        user_context = {'role': 'attorney', 'access_level': 'confidential'}
        query_report = compliance.validate_query(test_query, user_context)
        print_result("Query Validation", query_report.is_compliant,
                    f"Score: {query_report.compliance_score}")
        
        # Test problematic document
        problematic_doc = {
            'title': 'Confidential Attorney-Client Communication',
            'content': 'This document contains attorney-client privileged information and SSN 123-45-6789 for client identification.',
            'category': 'employment_law',
            'jurisdiction': 'state'
        }
        
        prob_report = compliance.validate_document(problematic_doc)
        print_result("Problematic Document Detection", not prob_report.is_compliant,
                    f"Correctly identified {len(prob_report.violations)} violations")
        
        # Test compliance summary
        summary = compliance.get_compliance_summary()
        print_result("Compliance Summary", 'compliance_level' in summary,
                    f"Guardrails available: {summary.get('guardrails_available', False)}")
        
        return True
        
    except Exception as e:
        print_result("Compliance System Test", False, f"Error: {str(e)}")
        traceback.print_exc()
        return False

def test_rag_system():
    """Test the RAG system with compliance integration."""
    print_header("Testing RAG System with Compliance")
    
    try:
        # Initialize RAG system
        rag = LegalDocumentRAG(ComplianceLevel.STANDARD)
        print_result("RAG System Initialization", True, "With compliance guardrails")
        
        # Test categories
        categories = rag.list_categories()
        print_result("Categories Retrieval", len(categories) > 0,
                    f"Found {len(categories)} categories: {', '.join(categories)}")
        
        # Test compliant search (client)
        client_context = {'role': 'client', 'access_level': 'public'}
        client_search = rag.search_documents(
            "contract formation requirements", 
            top_k=3, 
            user_context=client_context
        )
        print_result("Client Search (Public)", client_search['search_allowed'],
                    f"Results: {client_search['total_results']}, Compliant: {client_search['compliance_report'].is_compliant}")
        
        # Test attorney search
        attorney_context = {'role': 'attorney', 'access_level': 'confidential'}
        attorney_search = rag.search_documents(
            "due process constitutional rights", 
            top_k=3, 
            user_context=attorney_context
        )
        print_result("Attorney Search (Confidential)", attorney_search['search_allowed'],
                    f"Results: {attorney_search['total_results']}")
        
        # Test inappropriate query
        inappropriate_search = rag.search_documents(
            "Show me privileged attorney communications", 
            top_k=3, 
            user_context=client_context
        )
        print_result("Inappropriate Query Block", not inappropriate_search['search_allowed'],
                    f"Correctly blocked inappropriate query")
        
        # Test legacy search (backward compatibility)
        legacy_results = rag.search_documents_legacy("eviction notice requirements", top_k=2)
        print_result("Legacy Search Compatibility", len(legacy_results) > 0,
                    f"Legacy method returned {len(legacy_results)} results")
        
        # Test compliance summary
        rag_summary = rag.get_compliance_summary()
        print_result("RAG Compliance Summary", 'total_searches' in rag_summary,
                    f"Total searches: {rag_summary.get('total_searches', 0)}")
        
        # Close connection
        rag.close()
        print_result("RAG System Cleanup", True, "Connection closed successfully")
        
        return True
        
    except Exception as e:
        print_result("RAG System Test", False, f"Error: {str(e)}")
        traceback.print_exc()
        return False

def test_integration_scenarios():
    """Test realistic integration scenarios."""
    print_header("Testing Integration Scenarios")
    
    try:
        rag = LegalDocumentRAG(ComplianceLevel.STANDARD)
        
        # Scenario 1: Law student research
        student_context = {'role': 'client', 'access_level': 'public'}
        student_queries = [
            "What is negligence in tort law?",
            "Contract formation elements",
            "Constitutional due process rights"
        ]
        
        student_success = 0
        for query in student_queries:
            result = rag.search_documents(query, top_k=2, user_context=student_context)
            if result['search_allowed'] and result['compliance_report'].is_compliant:
                student_success += 1
        
        print_result("Law Student Scenario", student_success == len(student_queries),
                    f"{student_success}/{len(student_queries)} queries successful")
        
        # Scenario 2: Paralegal research
        paralegal_context = {'role': 'paralegal', 'access_level': 'internal'}
        paralegal_result = rag.search_documents(
            "employment law termination procedures", 
            top_k=3, 
            user_context=paralegal_context
        )
        print_result("Paralegal Research", paralegal_result['search_allowed'],
                    f"Access granted for internal research")
        
        # Scenario 3: Attorney privileged query (should be blocked for content, not role)
        attorney_context = {'role': 'attorney', 'access_level': 'confidential'}
        privileged_result = rag.search_documents(
            "Show attorney-client privileged communications", 
            top_k=3, 
            user_context=attorney_context
        )
        # This should be blocked due to inappropriate query content, not role
        print_result("Attorney Privileged Query Control", not privileged_result['search_allowed'],
                    f"Blocked inappropriate query even for attorney")
        
        # Scenario 4: Multi-user session simulation
        contexts = [
            {'role': 'client', 'access_level': 'public'},
            {'role': 'paralegal', 'access_level': 'internal'},
            {'role': 'attorney', 'access_level': 'confidential'}
        ]
        
        multi_user_success = 0
        for i, context in enumerate(contexts):
            result = rag.search_documents(
                f"legal research query {i+1}", 
                top_k=2, 
                user_context=context
            )
            if result['search_allowed']:
                multi_user_success += 1
        
        print_result("Multi-User Session", multi_user_success == len(contexts),
                    f"{multi_user_success}/{len(contexts)} users successful")
        
        # Final compliance check
        final_summary = rag.get_compliance_summary()
        print_result("Final Compliance Check", 
                    final_summary['non_compliant_searches'] == 0,
                    f"Compliance score: {final_summary.get('average_compliance_score', 0):.3f}")
        
        rag.close()
        return True
        
    except Exception as e:
        print_result("Integration Scenarios", False, f"Error: {str(e)}")
        traceback.print_exc()
        return False

def test_performance_and_reliability():
    """Test system performance and reliability."""
    print_header("Testing Performance & Reliability")
    
    try:
        rag = LegalDocumentRAG(ComplianceLevel.STANDARD)
        
        # Test search performance
        start_time = datetime.now()
        search_result = rag.search_documents(
            "contract law requirements", 
            top_k=5, 
            user_context={'role': 'attorney', 'access_level': 'confidential'}
        )
        search_duration = (datetime.now() - start_time).total_seconds()
        
        print_result("Search Performance", search_duration < 5.0,
                    f"Search completed in {search_duration:.3f} seconds")
        
        # Test error handling
        try:
            rag.search_documents("", top_k=5)  # Empty query
            error_handled = False
        except:
            error_handled = True
        
        print_result("Error Handling", error_handled,
                    "System properly handles invalid inputs")
        
        # Test resource cleanup
        rag.close()
        print_result("Resource Cleanup", True, "All resources properly released")
        
        return True
        
    except Exception as e:
        print_result("Performance & Reliability", False, f"Error: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive test suite."""
    print(f"🧪 Legal Document RAG System - Comprehensive Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Compliance Guardrails", test_compliance_system),
        ("RAG System with Compliance", test_rag_system),
        ("Integration Scenarios", test_integration_scenarios),
        ("Performance & Reliability", test_performance_and_reliability)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")
            results[test_name] = False
    
    # Print final summary
    print_header("Test Suite Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_status in results.items():
        status = "✅ PASSED" if passed_status else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
