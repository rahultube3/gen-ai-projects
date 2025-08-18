#!/usr/bin/env python3
"""
Simple script to check if HR data exists in MongoDB
Returns 0 if sufficient data exists, 1 if ingestion is needed
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGO_DB_URI')  # Changed from MONGODB_URI to MONGO_DB_URI
        if not mongo_uri:
            print("ERROR: MONGO_DB_URI not found in environment", file=sys.stderr)
            sys.exit(2)
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        
        # Check document count
        db = client['hr_assistant']
        collection = db['document_vectors']  # Changed from 'documents' to 'document_vectors'
        count = collection.count_documents({})
        
        print(f"{count}")
        
        # Return exit code based on data availability
        if count >= 10:
            sys.exit(0)  # Sufficient data exists
        else:
            sys.exit(1)  # Need to ingest data
            
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(2)  # Connection or other error

if __name__ == "__main__":
    main()
