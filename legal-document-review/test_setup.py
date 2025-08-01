#!/usr/bin/env python3
"""
Test script for Legal Document Review RAG System
"""

import sys
import os
from dotenv import load_dotenv

def test_imports():
    """Test if all required packages can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import sentence_transformers
        print("✅ sentence-transformers")
    except ImportError:
        print("❌ sentence-transformers not found")
        return False
    
    try:
        import pymongo
        print("✅ pymongo")
    except ImportError:
        print("❌ pymongo not found")
        return False
    
    try:
        import numpy
        print("✅ numpy")
    except ImportError:
        print("❌ numpy not found")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv not found")
        return False
    
    return True

def test_environment():
    """Test environment configuration."""
    print("\n🔍 Testing environment...")
    
    load_dotenv()
    
    mongo_uri = os.getenv("MONGO_DB_URI")
    if mongo_uri:
        print(f"✅ MONGO_DB_URI configured: {mongo_uri[:20]}...")
        return True
    else:
        print("❌ MONGO_DB_URI not configured")
        return False

def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n🔍 Testing MongoDB connection...")
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        load_dotenv()
        mongo_uri = os.getenv("MONGO_DB_URI")
        
        if not mongo_uri:
            print("❌ MONGO_DB_URI not configured")
            return False
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        client.close()
        print("✅ MongoDB connection successful")
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_embedding_model():
    """Test if the embedding model can be loaded."""
    print("\n🔍 Testing embedding model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test encoding
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        
        print(f"✅ Model loaded successfully")
        print(f"   Embedding dimension: {len(embedding)}")
        return True
        
    except Exception as e:
        print(f"❌ Model loading failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🧪 Legal Document Review RAG System - Test Suite")
    print("=" * 55)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment),
        ("MongoDB Test", test_mongodb_connection),
        ("Embedding Model Test", test_embedding_model)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary:")
    print("-" * 30)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The system is ready to use.")
        print("   Run: python db_setup.py")
        print("   Then: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the requirements and configuration.")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Configure .env file with MONGO_DB_URI")
        print("   3. Ensure MongoDB is running")

if __name__ == "__main__":
    main()
