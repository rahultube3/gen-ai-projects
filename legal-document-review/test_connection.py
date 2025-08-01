#!/usr/bin/env python3
"""
Test MongoDB connection
"""

import os
import ssl
from dotenv import load_dotenv
from pymongo import MongoClient

def test_connection():
    load_dotenv()
    
    mongo_uri = os.getenv("MONGO_DB_URI")
    print(f"MongoDB URI: {mongo_uri[:50]}...")
    
    try:
        # For MongoDB Atlas, we might need to handle SSL
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=10000,
            tlsAllowInvalidCertificates=True  # For development only
        )
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client["legal_rag"]
        collection = db["test"]
        
        # Insert a test document
        result = collection.insert_one({"test": "connection"})
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Remove test document
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document removed")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
