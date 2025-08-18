#!/usr/bin/env python3
"""
Table-Formatted Data Ingestion for HR Assistant
Specialized ingestion for structured comparison tables and formatted data
"""

import os
import sys
import logging
import re
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

def extract_tables_from_markdown(content: str):
    """Extract table data from markdown content and create structured chunks."""
    
    # Find all markdown tables
    table_pattern = r'\|.*\|.*\n\|[-\s:]+\|.*\n(?:\|.*\|.*\n)+'
    tables = re.findall(table_pattern, content, re.MULTILINE)
    
    structured_chunks = []
    
    for i, table in enumerate(tables):
        lines = table.strip().split('\n')
        
        # Extract header and data rows
        if len(lines) >= 3:  # Header, separator, at least one data row
            headers = [cell.strip() for cell in lines[0].split('|')[1:-1]]
            data_rows = []
            
            for line in lines[2:]:  # Skip header and separator
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) == len(headers):
                    data_rows.append(cells)
            
            # Create a structured representation
            table_data = {
                'type': 'table',
                'headers': headers,
                'rows': data_rows,
                'row_count': len(data_rows),
                'column_count': len(headers)
            }
            
            # Create searchable text representation
            table_text = f"Table {i+1}:\n"
            table_text += " | ".join(headers) + "\n"
            table_text += "-" * 50 + "\n"
            
            for row in data_rows:
                table_text += " | ".join(row) + "\n"
            
            # Add comparison context for each row
            for row in data_rows:
                row_text = f"Comparison data: {row[0]} - "
                for j, cell in enumerate(row[1:], 1):
                    if j < len(headers):
                        row_text += f"{headers[j]}: {cell}, "
                table_text += row_text.rstrip(', ') + "\n"
            
            structured_chunks.append({
                'content': table_text,
                'metadata': table_data,
                'chunk_type': 'table'
            })
    
    return structured_chunks

def extract_key_value_pairs(content: str):
    """Extract key-value pairs and structured information."""
    
    # Patterns for structured data
    patterns = {
        'benefits': r'(\w+(?:\s+\w+)*?):\s*([^\n]+)',
        'amounts': r'\$([0-9,]+)(?:/(\w+))?',
        'percentages': r'(\d+)%',
        'comparisons': r'(vs\.?|compared to|versus)\s+([^\n]+)'
    }
    
    structured_data = {}
    
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            structured_data[pattern_name] = matches
    
    return structured_data

def create_comparison_chunks(content: str, title: str):
    """Create specialized chunks for comparison data."""
    
    chunks = []
    
    # Extract tables
    table_chunks = extract_tables_from_markdown(content)
    chunks.extend(table_chunks)
    
    # Extract sections
    sections = re.split(r'\n## ', content)
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
            
        # Add section header if missing
        if not section.startswith('#'):
            section = '## ' + section
        
        # Extract section title
        section_lines = section.split('\n')
        section_title = section_lines[0].replace('#', '').strip()
        
        # Create enhanced chunk with comparison context
        chunk_content = section.strip()
        
        # Add comparison context
        comparison_context = f"Document: {title}\nSection: {section_title}\n\n"
        comparison_context += chunk_content
        
        # Extract structured data
        structured_data = extract_key_value_pairs(chunk_content)
        
        chunks.append({
            'content': comparison_context,
            'metadata': {
                'section_title': section_title,
                'structured_data': structured_data,
                'has_tables': 'table' in chunk_content.lower(),
                'has_amounts': bool(structured_data.get('amounts')),
                'has_percentages': bool(structured_data.get('percentages'))
            },
            'chunk_type': 'section'
        })
    
    return chunks

def ingest_comparison_document(file_path: str, vector_store: MongoVectorStore, embedder=None):
    """Ingest a document with table formatting and comparison data."""
    
    try:
        # Read the document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.warning(f"⚠️  Empty file: {file_path}")
            return False
        
        # Extract title from filename
        title = Path(file_path).stem.replace('_', ' ').title()
        
        logger.info(f"📄 Processing comparison document: {title}")
        
        # Initialize embedder if not provided
        if embedder is None:
            embedder = get_embedder()
        
        # Create specialized chunks for comparisons
        chunks = create_comparison_chunks(content, title)
        
        logger.info(f"   Created {len(chunks)} specialized chunks")
        
        # Generate embeddings and store
        for i, chunk_info in enumerate(chunks):
            try:
                chunk_content = chunk_info['content']
                chunk_metadata = chunk_info['metadata']
                chunk_type = chunk_info['chunk_type']
                
                # Generate embedding
                embedding = embedder.encode(chunk_content)
                
                # Handle single text input
                if hasattr(embedding, 'shape') and len(embedding.shape) > 1:
                    embedding = embedding[0].tolist()
                elif hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                
                # Create document entry with enhanced metadata
                doc = {
                    "title": title,
                    "content": chunk_content,
                    "chunk_index": i,
                    "chunk_type": chunk_type,
                    "source": file_path,
                    "type": "comparison_table",
                    "created_at": datetime.now(),
                    "embedding": embedding,
                    "structured_metadata": chunk_metadata
                }
                
                # Insert into MongoDB
                vector_store.collection.insert_one(doc)
                
            except Exception as e:
                logger.error(f"❌ Error processing chunk {i}: {str(e)}")
                return False
        
        logger.info(f"✅ Successfully ingested comparison document: {title}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ingesting {file_path}: {str(e)}")
        return False

def main():
    """Ingest table-formatted comparison documents."""
    
    # Define sample data directory
    sample_data_dir = project_root / "sample_data"
    
    if not sample_data_dir.exists():
        logger.error(f"❌ Sample data directory not found: {sample_data_dir}")
        return False
    
    # Get comparison documents (look for files with 'comparison' in name)
    comparison_files = list(sample_data_dir.glob("*comparison*.md"))
    
    if not comparison_files:
        logger.error(f"❌ No comparison files found in {sample_data_dir}")
        return False
    
    logger.info(f"🚀 Starting table-formatted data ingestion...")
    logger.info(f"📂 Source directory: {sample_data_dir}")
    logger.info(f"📄 Found {len(comparison_files)} comparison files")
    
    # List files to be processed
    for file_path in comparison_files:
        logger.info(f"   • {file_path.name}")
    
    try:
        # Get MongoDB URI
        mongo_uri = os.getenv('MONGO_DB_URI')
        if not mongo_uri:
            logger.error("❌ MONGO_DB_URI environment variable not set")
            return False
        
        # Initialize vector store and embedder
        vector_store = MongoVectorStore(mongo_uri)
        embedder = get_embedder()
        logger.info(f"🤖 Using embedder: {type(embedder).__name__}")
        
        # Ingest each comparison file
        success_count = 0
        for file_path in comparison_files:
            if ingest_comparison_document(str(file_path), vector_store, embedder):
                success_count += 1
        
        if success_count == len(comparison_files):
            # Get final statistics
            stats = vector_store.get_stats()
            logger.info("🎉 Table-formatted data ingestion completed successfully!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   • Total documents: {stats['total_vectors']}")
            logger.info(f"   • Database: {stats['database']}")
            logger.info(f"   • Collection: {stats['collection']}")
            logger.info(f"   • Storage size: {stats['storage_size_mb']:.2f} MB")
            logger.info(f"   • Embedding dimension: {stats['dimension']}")
            
            return True
        else:
            logger.error(f"❌ Only {success_count}/{len(comparison_files)} files processed successfully")
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
