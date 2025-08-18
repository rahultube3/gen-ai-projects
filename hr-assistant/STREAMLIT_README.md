# HR Assistant Web Chat Interface

A modern, interactive web interface for the HR Assistant RAG system, built with Streamlit. This provides a user-friendly chat interface for querying HR documents, policies, and procedures.

## 🌟 Features

### Web Chat Interface
- **Real-time Chat**: Interactive chat interface with immediate responses
- **Source Attribution**: View source documents for each answer with relevance scores
- **Example Questions**: Pre-built example queries to get started quickly
- **Chat History**: Persistent conversation history during the session
- **Performance Metrics**: Response time tracking and system statistics

### System Integration
- **RAG Integration**: Connects to the RAG API (port 8001) for document retrieval
- **API Health Monitoring**: Real-time status of backend services
- **Error Handling**: Graceful error handling with user-friendly messages
- **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have the HR Assistant backend running:
```bash
# Start the RAG API server
python rag_system.py
```

### 2. Start the Web Interface

**Option A: Using the startup script (Recommended)**
```bash
# Make the script executable (first time only)
chmod +x start_streamlit.sh

# Start the web interface
./start_streamlit.sh
```

**Option B: Manual start**
```bash
# Start the simple chat interface
streamlit run simple_chat.py --server.port 8501

# OR start the advanced interface
streamlit run streamlit_chat.py --server.port 8502
```

### 3. Access the Interface
- Open your browser to: http://localhost:8501
- The interface will automatically check API connectivity
- Start asking HR-related questions!

## 📱 Available Interfaces

### 1. Simple Chat (`simple_chat.py`)
- **Port**: 8501
- **Features**: Basic chat interface, perfect for testing
- **Use Case**: Quick queries and testing the RAG system
- **Layout**: Centered layout with sidebar for examples

### 2. Advanced Chat (`streamlit_chat.py`)
- **Port**: 8502 (if running both)
- **Features**: Full-featured interface with metrics and monitoring
- **Use Case**: Production-ready interface with comprehensive features
- **Layout**: Multi-column layout with performance tracking

## 💡 Example Questions

Try these sample questions to explore the system:

### Benefits & Insurance
- "What are the health insurance benefits?"
- "How does the dental coverage work?"
- "What is covered under disability insurance?"
- "Tell me about vision benefits"

### Retirement & Financial
- "How does the retirement plan work?"
- "What is the 401(k) matching policy?"
- "When am I eligible for retirement benefits?"

### Policies & Procedures
- "What is the vacation policy?"
- "How do I request time off?"
- "What are the eligibility requirements?"
- "Tell me about dependent care benefits"

## 🔧 Configuration

### Environment Variables
The web interface automatically uses the same environment configuration as the backend:
- `MONGODB_URI`: Database connection
- `OPENAI_API_KEY`: LLM service
- `OPENAI_MODEL`: Model selection (default: gpt-3.5-turbo)

### API Endpoints
- **RAG API**: http://localhost:8001
- **Comprehensive API**: http://localhost:8002 (for advanced features)

### Customization
You can modify the following in the Streamlit files:

```python
# API Configuration
RAG_API_URL = "http://localhost:8001"
COMPREHENSIVE_API_URL = "http://localhost:8002"

# Default settings
max_sources = 5  # Number of source documents to retrieve
context_window = 3000  # Context size for RAG queries
```

## 🎨 Interface Features

### Chat Experience
- **Message History**: All messages persist during the session
- **Source Display**: Expandable source documents with relevance scores
- **Response Time**: Real-time performance metrics
- **Error Handling**: Clear error messages with troubleshooting tips

### Sidebar Features
- **System Status**: Real-time API health monitoring
- **Example Questions**: Quick-start buttons for common queries
- **Performance Metrics**: Response time statistics and trends
- **Settings**: Configurable query parameters
- **Clear Chat**: Reset conversation history

### Visual Elements
- **Color-coded Messages**: Different styling for user/assistant messages
- **Source Cards**: Highlighted source document previews
- **Status Indicators**: Green/red status indicators for system health
- **Responsive Layout**: Adapts to different screen sizes

## 🔍 Troubleshooting

### Common Issues

#### "HR Assistant API is not available"
```bash
# Check if the RAG API is running
curl http://localhost:8001/health

# If not running, start it:
python rag_system.py
```

#### "Connection Error"
1. Verify the RAG API is running on port 8001
2. Check firewall settings
3. Ensure MongoDB is accessible
4. Verify OpenAI API key is set

#### "No sources found"
1. Check if documents are ingested: `python ingest_mongodb.py`
2. Verify MongoDB connection
3. Check vector store data

### API Health Check
```bash
# Test RAG API
curl http://localhost:8001/health

# Test comprehensive API (if running)
curl http://localhost:8002/health

# Test a sample query
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "health benefits", "max_sources": 3}'
```

## 📊 Performance

### Response Times
- **Typical Response**: 2-5 seconds
- **Vector Search**: ~500ms
- **LLM Generation**: 1-3 seconds
- **Document Retrieval**: ~200ms

### System Requirements
- **RAM**: 4GB+ recommended
- **CPU**: 2 cores minimum
- **Network**: Stable internet for OpenAI API calls
- **Browser**: Modern browser with JavaScript enabled

## 🔒 Security

### Data Privacy
- **Local Processing**: Documents stored locally in MongoDB
- **API Keys**: Securely stored in environment variables
- **No Data Persistence**: Chat history not saved between sessions
- **Encrypted Connections**: HTTPS support available

### Access Control
- **Local Access**: Default configuration allows localhost only
- **Network Configuration**: Modify server.address for network access
- **Authentication**: Can be added via Streamlit's authentication features

## 🔄 Integration

### Backend APIs
The web interface integrates with:
1. **RAG System** (`rag_system.py`) - Document retrieval and Q&A
2. **Comprehensive API** (`comprehensive_api.py`) - Advanced chat features
3. **MCP Server** (`mcp_server.py`) - Tool-based interactions

### Database
- **MongoDB Atlas**: Vector storage and document management
- **Collections**: hr_assistant collection with 95+ document chunks
- **Indexing**: Vector similarity search with 384-dimensional embeddings

## 📈 Analytics

### Built-in Metrics
- **Response Time Tracking**: Per-query performance measurement
- **Source Relevance**: Document similarity scores
- **Query Success Rate**: Error rate monitoring
- **System Health**: API availability monitoring

### Performance Charts
The advanced interface includes:
- Response time trends
- Query volume statistics
- Source utilization metrics
- System resource usage

## 🚀 Deployment

### Local Development
```bash
# Clone and setup
git clone <repository>
cd hr-assistant

# Install dependencies
pip install -r requirements_basic.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start services
python rag_system.py &
streamlit run simple_chat.py
```

### Production Deployment
For production deployment, consider:
1. **Reverse Proxy**: Use nginx or Apache
2. **SSL/TLS**: Enable HTTPS
3. **Authentication**: Add user authentication
4. **Monitoring**: Set up logging and monitoring
5. **Scaling**: Use container orchestration

## 📝 Development

### File Structure
```
hr-assistant/
├── simple_chat.py          # Basic Streamlit interface
├── streamlit_chat.py       # Advanced Streamlit interface
├── start_streamlit.sh      # Startup script
├── rag_system.py          # RAG API backend
├── comprehensive_api.py    # Advanced API backend
└── requirements_basic.txt  # Dependencies
```

### Adding Features
To extend the web interface:
1. Modify the Streamlit files
2. Add new API endpoints in the backend
3. Update the configuration as needed
4. Test with the development setup

## 📞 Support

### Getting Help
- **Documentation**: Check the main README files
- **API Reference**: See rag_system.py for API endpoints
- **Troubleshooting**: Use the health check endpoints
- **Performance**: Monitor response times and system metrics

### Common Solutions
- **Slow Responses**: Check OpenAI API rate limits
- **Missing Sources**: Verify document ingestion
- **Connection Issues**: Restart backend services
- **Memory Issues**: Monitor MongoDB resource usage

---

## 🎯 Summary

The HR Assistant Web Chat Interface provides:
- ✅ **User-Friendly**: Intuitive chat interface for HR queries
- ✅ **Real-Time**: Immediate responses with source attribution
- ✅ **Integrated**: Seamless connection to RAG backend
- ✅ **Performant**: Sub-5-second response times
- ✅ **Extensible**: Easy to customize and extend
- ✅ **Production-Ready**: Suitable for enterprise deployment

Start with the simple interface for testing, then move to the advanced interface for production use!
