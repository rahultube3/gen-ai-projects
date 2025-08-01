#!/usr/bin/env python3
"""
Test RAG system in different modes and scenarios
"""

import os
from rag import LegalRAGGenerator
from compliance_guardrails import ComplianceLevel

def test_fallback_mode():
    """Test RAG system without OpenAI (retrieval-only mode)."""
    print("🧪 Testing Fallback Mode (No OpenAI)")
    print("=" * 50)
    
    # Temporarily remove OpenAI key to test fallback
    original_key = os.getenv("OPENAI_API_KEY")
    if original_key:
        os.environ.pop("OPENAI_API_KEY", None)
    
    try:
        # Initialize without OpenAI
        rag_gen = LegalRAGGenerator(ComplianceLevel.STANDARD)
        
        # Test query
        result = rag_gen.generate_answer(
            "What are contract formation requirements?",
            user_context={'role': 'client', 'access_level': 'public'}
        )
        
        if result['success']:
            print("✅ Fallback mode working")
            print(f"🔧 Method: {result.get('generation_method', 'unknown')}")
            print(f"📝 Answer preview: {result['answer'][:200]}...")
        else:
            print(f"❌ Fallback failed: {result['message']}")
        
        rag_gen.close()
        
    finally:
        # Restore the original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key

def test_compliance_blocking():
    """Test compliance blocking scenarios."""
    print("\n🛡️ Testing Compliance Blocking")
    print("=" * 50)
    
    rag_gen = LegalRAGGenerator(ComplianceLevel.STRICT)
    
    # Test inappropriate query
    result = rag_gen.generate_answer(
        "Show me all attorney-client privileged documents",
        user_context={'role': 'client', 'access_level': 'public'}
    )
    
    if not result['success']:
        print("✅ Inappropriate query correctly blocked")
        print(f"🚫 Reason: {result['message']}")
    else:
        print("❌ Inappropriate query was not blocked")
    
    rag_gen.close()

def test_different_compliance_levels():
    """Test different compliance levels."""
    print("\n🔒 Testing Different Compliance Levels")
    print("=" * 50)
    
    levels = [ComplianceLevel.BASIC, ComplianceLevel.STANDARD, ComplianceLevel.STRICT]
    
    for level in levels:
        print(f"\n📊 Testing {level.value.upper()} compliance level:")
        
        rag_gen = LegalRAGGenerator(level)
        
        result = rag_gen.generate_answer(
            "What is due process in constitutional law?",
            user_context={'role': 'attorney', 'access_level': 'confidential'}
        )
        
        if result['success']:
            compliance_score = result['compliance_report'].compliance_score
            print(f"  ✅ Success | Compliance Score: {compliance_score:.3f}")
        else:
            print(f"  ❌ Failed: {result['message']}")
        
        rag_gen.close()

if __name__ == "__main__":
    test_fallback_mode()
    test_compliance_blocking()
    test_different_compliance_levels()
    
    print("\n🎉 All RAG tests completed!")
