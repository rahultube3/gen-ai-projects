#!/usr/bin/env python3
"""
Quick test of the Wikipedia RAG Chatbot API
"""
import requests
import json
import time
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_api():
    """Test the chatbot API"""
    api_base = "http://localhost:8000"
    
    print("🧪 Testing Wikipedia RAG Chatbot API")
    print("="*45)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{api_base}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health: {health_data['status']}")
            print(f"📊 RAG Active: {health_data['rag_system_active']}")
            print(f"🔑 OpenAI Configured: {health_data['openai_configured']}")
            print(f"⏱️  Uptime: {health_data['uptime']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API not reachable: {e}")
        print("💡 Make sure to start the API server first:")
        print("   cd web-scraping")
        print("   uv run uvicorn chatbot_api_server:app --reload")
        return False
    
    # Test adding a Wikipedia page
    print("\n2. Testing add Wikipedia page...")
    test_url = "https://en.wikipedia.org/wiki/Health_data"
    
    try:
        response = requests.post(f"{api_base}/add-page", json={"url": test_url}, timeout=30)
        add_result = response.json()
        
        if add_result['success']:
            print(f"✅ Added page: {add_result['page_title']}")
        else:
            print(f"⚠️  Add page result: {add_result['message']}")
    except Exception as e:
        print(f"❌ Error adding page: {e}")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Test chat
    print("\n3. Testing chat functionality...")
    test_questions = [
        "What is health data?",
        "How is health data collected?",
        "What are the privacy concerns with health data?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n3.{i} Question: {question}")
        
        try:
            response = requests.post(f"{api_base}/chat", 
                                   json={"message": question}, 
                                   timeout=30)
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"✅ Response received")
                print(f"📝 Answer: {chat_data['response'][:200]}...")
                print(f"🎯 Confidence: {chat_data['confidence']:.3f}")
                print(f"📚 Sources: {len(chat_data['sources'])}")
                
                if chat_data['sources']:
                    for j, source in enumerate(chat_data['sources'][:2], 1):
                        print(f"   {j}. {source['title']} - {source['section']} ({source['similarity']:.3f})")
            else:
                print(f"❌ Chat failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in chat: {e}")
        
        time.sleep(1)  # Brief pause between questions
    
    # Test collections
    print("\n4. Testing collections...")
    try:
        response = requests.get(f"{api_base}/collections", timeout=5)
        collections = response.json()
        
        for collection in collections:
            print(f"📂 Collection: {collection['name']}")
            print(f"   Documents: {collection['document_count']}")
            if collection['sample_pages']:
                print(f"   Sample pages: {', '.join(collection['sample_pages'][:3])}")
                
    except Exception as e:
        print(f"❌ Error getting collections: {e}")
    
    print("\n🎉 API Test Complete!")
    return True

if __name__ == "__main__":
    test_api()