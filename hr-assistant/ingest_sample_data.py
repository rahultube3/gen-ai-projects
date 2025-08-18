#!/usr/bin/env python3
"""
Sample Data Ingestion Script for HR Assistant
Processes curated sample markdown files and creates high-quality vector embeddings
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from ingest_mongodb import MongoVectorStore, get_embedder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ingest_markdown_file(file_path: str, vector_store: MongoVectorStore, embedder=None):
    """Ingest a single markdown file into MongoDB."""
    try:
        # Read the markdown file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"⚠️  Empty file: {file_path}")
            return False
        
        # Extract title from filename
        title = Path(file_path).stem.replace('_', ' ').title()
        
        # Document metadata
        doc_meta = {
            "title": title,
            "source": file_path,
            "type": "markdown",
            "created_at": datetime.now()
        }
        
        logger.info(f"📄 Processing: {title}")
        
        # Initialize embedder if not provided
        if embedder is None:
            embedder = get_embedder()
        
        # Chunk the document
        chunk_size = 800
        chunk_overlap = 100
        
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            
            if current_size + line_size > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk)
                if chunk_text.strip():
                    chunks.append(chunk_text.strip())
                
                # Start new chunk with overlap
                overlap_lines = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
                current_chunk = overlap_lines + [line]
                current_size = sum(len(l) for l in current_chunk)
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        
        logger.info(f"   Created {len(chunks)} chunks")
        
        # Generate embeddings and store
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = embedder.encode(chunk)
                
                # Handle single text input (returns array, we need the first element)
                if hasattr(embedding, 'shape') and len(embedding.shape) > 1:
                    embedding = embedding[0].tolist()
                elif hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                
                # Create document entry
                doc = {
                    "title": doc_meta["title"],
                    "content": chunk,
                    "chunk_index": i,
                    "source": doc_meta["source"],
                    "type": doc_meta["type"],
                    "created_at": doc_meta["created_at"],
                    "embedding": embedding
                }
                
                # Insert into MongoDB
                vector_store.collection.insert_one(doc)
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {i}: {str(e)}")
                return False
        
        logger.info(f"✅ Successfully ingested: {title}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ingesting {file_path}: {str(e)}")
        return False

def main():
    """Ingest sample HR documents into MongoDB with proper embeddings."""
    
    # Define sample data directory
    sample_data_dir = project_root / "sample_data"
    
    if not sample_data_dir.exists():
        logger.error(f"❌ Sample data directory not found: {sample_data_dir}")
        return False
    
    # Get all markdown files
    md_files = list(sample_data_dir.glob("*.md"))
    
    if not md_files:
        logger.error(f"❌ No markdown files found in {sample_data_dir}")
        return False
    
    logger.info(f"🚀 Starting sample data ingestion...")
    logger.info(f"📂 Source directory: {sample_data_dir}")
    logger.info(f"📄 Found {len(md_files)} markdown files")
    
    # List files to be processed
    for file_path in md_files:
        logger.info(f"   • {file_path.name}")
    
    try:
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGO_DB_URI')
        if not mongo_uri:
            logger.error("❌ MONGO_DB_URI environment variable not set")
            return False
        
        # Clear existing data first (optional - comment out to keep existing data)
        logger.info("🗑️  Clearing existing documents...")
        vector_store = MongoVectorStore(mongo_uri)
        vector_store.clear_collection()
        logger.info("✅ Existing documents cleared")
        
        # Initialize embedder once
        embedder = get_embedder()
        logger.info(f"🤖 Using embedder: {type(embedder).__name__}")
        
        # Ingest each markdown file
        success_count = 0
        for file_path in md_files:
            if ingest_markdown_file(str(file_path), vector_store, embedder):
                success_count += 1
        
        if success_count == len(md_files):
            # Get final statistics
            stats = vector_store.get_stats()
            logger.info("🎉 Sample data ingestion completed successfully!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   • Total documents: {stats['total_vectors']}")
            logger.info(f"   • Database: {stats['database']}")
            logger.info(f"   • Collection: {stats['collection']}")
            logger.info(f"   • Storage size: {stats['storage_size_mb']:.2f} MB")
            logger.info(f"   • Embedding dimension: {stats['dimension']}")
            
            return True
        else:
            logger.error(f"❌ Only {success_count}/{len(md_files)} files processed successfully")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {str(e)}")
        return False
    
    finally:
        # Close connections
        try:
            vector_store.close()
        except:
            pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
