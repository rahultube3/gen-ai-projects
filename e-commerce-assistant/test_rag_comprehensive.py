#!/usr/bin/env python3
"""
Comprehensive test of the E-commerce RAG Assistant
"""
import sys
from rag_assistant import EcommerceRAGAssistant

def test_ecommerce_rag():
    """Test the complete RAG system functionality"""
    
    print("🚀 E-commerce RAG Assistant - Comprehensive Test")
    print("=" * 60)
    
    try:
        # Initialize the assistant
        print("🔄 Initializing RAG Assistant...")
        assistant = EcommerceRAGAssistant()
        print("✅ Assistant initialized successfully!\n")
        
        # Test scenarios
        test_queries = [
            {
                "category": "Product Search",
                "queries": [
                    "What smartphones do you have?",
                    "Show me laptops",
                    "Find me headphones",
                    "What Apple products are available?"
                ]
            },
            {
                "category": "Product Recommendations",
                "queries": [
                    "I need a phone under $1200",
                    "Recommend a laptop for work",
                    "What's the best rated product?",
                    "Show me products with high ratings"
                ]
            },
            {
                "category": "Conversational AI",
                "queries": [
                    "Hi, I'm looking for a new phone",
                    "Tell me about the iPhone 15 Pro Max",
                    "Is the Samsung Galaxy good?",
                    "Thank you for your help!"
                ]
            }
        ]
        
        # Run tests
        for test_category in test_queries:
            print(f"📋 Testing: {test_category['category']}")
            print("-" * 40)
            
            for query in test_category['queries']:
                print(f"\n💬 User: {query}")
                try:
                    response = assistant.chat(query)
                    print(f"🤖 Assistant: {response}\n")
                except Exception as e:
                    print(f"❌ Error: {e}\n")
        
        # Test recommendations separately
        print("🎯 Testing Direct Recommendations")
        print("-" * 40)
        try:
            recommendations = assistant.get_product_recommendations("smartphone", limit=3)
            print(f"📱 Smartphone recommendations: {recommendations}")
            
            recommendations = assistant.get_product_recommendations("laptop", limit=2)
            print(f"💻 Laptop recommendations: {recommendations}")
        except Exception as e:
            print(f"❌ Recommendation error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Comprehensive test completed!")
        
        # Close the assistant
        assistant.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_ecommerce_rag()
    sys.exit(0 if success else 1)
