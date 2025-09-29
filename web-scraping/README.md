# Wikipedia RAG System

A specialized web scraping and RAG (Retrieval-Augmented Generation) system for Wikipedia content integration.

## 🎯 Overview

This project provides tools to scrape Wikipedia pages and integrate them into an intelligent knowledge base using ChromaDB vector storage and OpenAI for AI-powered responses.

## 🚀 Features

- **Wikipedia Scraping**: Extract structured content from any Wikipedia page
- **Health Data Specialization**: Dedicated scraper for health-related Wikipedia content
- **Interactive Interface**: Command-line tool for real-time scraping and querying
- **Batch Processing**: Handle multiple Wikipedia URLs efficiently
- **Intelligent Responses**: OpenAI GPT-powered contextual answers
- **Vector Search**: ChromaDB semantic search capabilities

## 📁 Core Components

- **`health_data_rag.py`** - Specialized health data Wikipedia scraper with comprehensive testing
- **`wikipedia_rag_scraper.py`** - General-purpose Wikipedia scraper for any page
- **`interactive_wikipedia_rag.py`** - Interactive CLI for adding pages and querying knowledge
- **`batch_wikipedia_rag.py`** - Batch processor for multiple Wikipedia URLs
- **`chromadb_cli.py`** - Command-line interface for ChromaDB operations
- **`llm_client.py`** - Multi-provider LLM client (OpenAI, Anthropic, Azure)

## ⚙️ Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment** (create `.env` file):
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🎮 Usage

### Quick Health Data Demo
```bash
uv run python health_data_rag.py
```

### Interactive Wikipedia RAG
```bash
uv run python interactive_wikipedia_rag.py
```

### Batch Processing Demo
```bash
uv run python batch_wikipedia_rag.py --health-demo
```

### Batch Process Custom URLs
```bash
# Create sample URLs file
uv run python batch_wikipedia_rag.py --create-sample my_urls.txt
# Edit my_urls.txt with your Wikipedia URLs
uv run python batch_wikipedia_rag.py my_urls.txt
```

### ChromaDB Management
```bash
# List all collections
uv run python chromadb_cli.py list

# Search within a collection
uv run python chromadb_cli.py search health_data_knowledge "digital health"
```

## 📊 Performance

- **Scraping Speed**: ~1.7 seconds per Wikipedia page
- **Query Accuracy**: 65-85% similarity scores
- **Response Quality**: GPT-3.5-turbo powered comprehensive answers
- **Batch Processing**: Handle multiple pages with error tracking

## 🗂️ Database Structure

- **`chroma_db/`** - Main ChromaDB vector database
- **`health_rag_db/`** - Specialized health data knowledge base
- **Collections**: Organized by topic and scraping session
- **Metadata**: Source URLs, section titles, timestamps, word counts

## 📈 Success Metrics

✅ **Health Data RAG**: 100% successful queries, 72.8% average confidence  
✅ **Batch Processing**: 4 Wikipedia pages, 113 documents, 38K+ words  
✅ **Response Quality**: Contextual, comprehensive AI-powered answers  
✅ **Integration**: Seamless ChromaDB + OpenAI workflow

## 🌟 Example Queries

- "What is health data and why is it important?"
- "How does health informatics improve healthcare delivery?"
- "What are the main benefits of digital health technologies?"
- "What is the difference between health data and electronic health records?"

## 📋 Quick Start

1. Clone and set up:
   ```bash
   cd web-scraping
   uv sync
   echo "OPENAI_API_KEY=your_key_here" > .env
   ```

2. Run health data demo:
   ```bash
   uv run python health_data_rag.py
   ```

3. Try interactive mode:
   ```bash
   uv run python interactive_wikipedia_rag.py
   ```

## 🔧 Customization

- **Add New Domains**: Extend scrapers for other educational websites
- **Custom Collections**: Create topic-specific knowledge bases  
- **Advanced Queries**: Implement metadata filtering and complex searches
- **Integration**: Connect with other RAG systems and data sources
