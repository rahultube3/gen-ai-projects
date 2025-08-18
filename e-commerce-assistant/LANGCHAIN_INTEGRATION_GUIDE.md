# 🤖 LangChain + MCP E-commerce Integration

## 🎯 Overview

This integration combines **LangChain AI agents** with **MCP (Model Context Protocol) microservices** to create an intelligent e-commerce assistant. The system provides natural language interaction with your microservices architecture.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangChain     │    │   MCP Tools     │    │  Microservices  │
│     Agent       │───▶│   Integration   │───▶│   (Gateway,     │
│                 │    │                 │    │  Product, etc.) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Claude        │    │    MongoDB      │
│   REST API      │    │   Desktop       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Key Features

### 🤖 **AI Agent Capabilities**
- **Natural Language Processing**: Understand complex e-commerce queries
- **Tool Orchestration**: Coordinate multiple microservices intelligently
- **Context Management**: Maintain conversation history and user preferences
- **Error Handling**: Graceful fallbacks and retry mechanisms

### 🛠️ **MCP Tool Integration**
- **Product Search**: AI-powered product discovery with recommendations
- **Order Management**: Complete order lifecycle with analytics
- **Dashboard Generation**: Personalized user insights
- **Health Monitoring**: Real-time service status checking
- **Cross-Service Analytics**: Business intelligence across all services

### 🌐 **API Interface**
- **RESTful Endpoints**: Standard HTTP API for external integration  
- **Session Management**: Multi-turn conversations with state
- **OpenAPI Documentation**: Interactive API docs and testing
- **CORS Support**: Cross-origin requests for web applications

## 📋 Prerequisites

1. **Python Environment**: Python 3.13+ with `uv` package manager
2. **Dependencies Installed**: LangChain, FastAPI, and MCP packages
3. **MongoDB**: Running MongoDB instance for data storage
4. **OpenAI API Key**: For LangChain agent functionality
5. **MCP Services**: E-commerce microservices running

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
cd e-commerce-assistant
uv sync
```

### 2. Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant" 
```

### 3. Start MCP Services
```bash
./orchestration/manage_services.sh start
```

### 4. Test Integration
```bash
uv run python demo_langchain_integration.py
```

## 🎮 Usage Examples

### 💻 **Command Line Interface**
```bash
# Start interactive agent
uv run python langchain_agent.py

# Example conversation:
# User: "Search for wireless headphones under $100"
# Agent: Uses unified_search tool to find products with recommendations
```

### 🌐 **REST API Server**
```bash
# Start API server
uv run python langchain_api_server.py

# Server runs on http://localhost:8001
# Documentation: http://localhost:8001/docs
```

### 📡 **API Endpoints**

#### **Chat with Agent**
```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find me gaming laptops under $1500",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

#### **Product Search**
```bash
curl -X POST "http://localhost:8001/products/search?query=bluetooth%20speakers&user_id=user123"
```

#### **Generate Dashboard** 
```bash
curl -X POST "http://localhost:8001/dashboard/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "sections": ["recommendations", "recent_orders", "trending"]
  }'
```

#### **Health Check**
```bash
curl http://localhost:8001/health
```

## 🛠️ Available Tools

### 🎯 **Gateway Service Tools** (Primary)
1. **`search_products`** - Unified product search with AI recommendations
2. **`chat_assistant`** - Intelligent conversational interface  
3. **`manage_orders`** - Order management with analytics
4. **`create_dashboard`** - Personalized user dashboards
5. **`check_service_health`** - Monitor all microservices
6. **`generate_analytics`** - Cross-service business analytics

### 🔧 **Direct Service Tools** (Specialized)
7. **`product_details`** - Detailed product information
8. **`product_recommendations`** - AI-powered recommendations
9. **`order_analytics`** - Order statistics and insights

## 🎨 Agent Customization

### **System Prompt**
The agent uses a comprehensive system prompt that defines:
- Role as an e-commerce assistant
- Available tools and their purposes
- Response style and formatting guidelines
- Error handling approaches

### **Memory Management**
- **Window Memory**: Keeps last 10 conversation turns
- **Session Isolation**: Each user/session has independent memory
- **Context Preservation**: Maintains user preferences across interactions

### **Tool Selection Strategy**
The agent intelligently selects tools based on:
- User intent analysis
- Query complexity
- Required data sources
- Performance considerations

## 📊 Example Conversations

### **Product Discovery**
```
User: "I need a laptop for video editing, budget around $2000"

Agent: I'll help you find the perfect video editing laptop within your budget. 
Let me search for high-performance laptops with the features you need.

[Uses search_products tool with query="video editing laptop $2000" and user preferences]

Based on your requirements, I found several excellent options:
1. MacBook Pro 16" M2 - $1,999 (Recommended for video editing)
2. Dell XPS 15 - $1,899 (Great performance, Windows-based)
3. ASUS ROG Strix - $1,799 (Gaming laptop, excellent for video work)

Would you like detailed specifications for any of these?
```

### **Order Management**
```
User: "What's my order history and when is my next delivery?"

Agent: Let me check your order history and upcoming deliveries.

[Uses manage_orders tool with user_id and action="view_orders"]

Here's your order summary:
- Recent Orders: 3 orders in the last 30 days
- Next Delivery: Gaming mouse arriving tomorrow (Order #12345)
- Order Status: 2 delivered, 1 in transit

Would you like me to provide reorder suggestions based on your purchase history?
```

### **Analytics & Insights**
```
User: "Show me analytics for our top-selling products this month"

Agent: I'll generate comprehensive product performance analytics for this month.

[Uses generate_analytics tool with metric_type="product_performance"]

Here are your top product insights:
- Best Sellers: Wireless earbuds, Gaming keyboards, Laptop stands
- Revenue Growth: 23% increase vs last month
- Customer Satisfaction: 4.7/5 average rating
- Return Rate: 2.1% (industry average: 8.2%)

Would you like me to create a detailed dashboard with these metrics?
```

## 🔧 Configuration

### **Agent Settings**
```python
# In langchain_agent.py
agent = EcommerceAgent(
    openai_api_key="your-key",
    model="gpt-4",  # or "gpt-3.5-turbo"
    temperature=0.1,  # Low for consistent responses
    max_iterations=5,  # Tool use limit
    memory_window=10   # Conversation history
)
```

### **API Server Settings**  
```python
# In langchain_api_server.py
uvicorn.run(
    "langchain_api_server:app",
    host="0.0.0.0",  # External access
    port=8001,       # Custom port
    reload=True,     # Development mode
    log_level="info"
)
```

## 🛡️ Error Handling

### **Common Issues & Solutions**

**1. OpenAI API Errors**
```python
# Automatic retry with exponential backoff
# Rate limit handling
# Fallback to cached responses
```

**2. MCP Service Timeouts**  
```python
# 30-second timeout per service call
# Graceful degradation when services unavailable
# Error messages to user with suggested alternatives
```

**3. Database Connection Issues**
```python
# Connection pooling and retry logic
# Fallback to in-memory caching
# Status reporting to user
```

## 📈 Performance Optimization

### **Caching Strategy**
- **Response Caching**: Cache frequent queries for faster responses
- **Session Caching**: Keep user context in memory
- **Tool Result Caching**: Cache MCP service responses

### **Async Processing**
- **Non-blocking Operations**: All I/O operations are asynchronous
- **Concurrent Tool Calls**: Multiple services called in parallel when possible
- **Background Tasks**: Long-running analytics in background

### **Load Balancing**
- **Session Distribution**: Distribute users across multiple agent instances
- **Service Health Checks**: Route requests to healthy services only
- **Circuit Breaker Pattern**: Fail fast on unhealthy services

## 🔍 Monitoring & Debugging

### **Logging**
```bash
# Agent logs
tail -f logs/langchain_agent.log

# API server logs  
tail -f logs/api_server.log

# MCP service logs
tail -f logs/gateway_service.log
```

### **Health Endpoints**
```bash
# Agent health
curl http://localhost:8001/health

# Service health  
curl -X POST "http://localhost:8001/chat" \
  -d '{"message": "Check service health"}'
```

### **Debug Mode**
```python
# Enable verbose logging
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,  # Shows tool calls and reasoning
    debug=True     # Additional debug information
)
```

## 🚀 Deployment

### **Production Considerations**
1. **API Keys**: Use secure key management (AWS Secrets, Azure KeyVault)
2. **Rate Limiting**: Implement request rate limiting
3. **Load Balancing**: Multiple agent instances behind load balancer
4. **Monitoring**: Application performance monitoring (APM)
5. **Caching**: Redis for distributed caching
6. **Security**: HTTPS, authentication, input validation

### **Docker Deployment**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8001
CMD ["uv", "run", "python", "langchain_api_server.py"]
```

### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langchain-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: langchain-agent
  template:
    spec:
      containers:
      - name: agent
        image: langchain-agent:latest
        ports:
        - containerPort: 8001
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
```

## 🎯 Next Steps

### **Immediate Actions**
1. ✅ Set up environment variables
2. ✅ Test basic functionality with demo script  
3. ✅ Start API server and test endpoints
4. ✅ Integrate with existing frontend applications

### **Advanced Features**
- **Multi-language Support**: Extend for international markets
- **Voice Integration**: Add speech-to-text capabilities
- **Visual Search**: Image-based product search
- **Recommendation Engine**: Enhanced ML-based recommendations
- **A/B Testing**: Experiment with different agent behaviors

### **Scaling Considerations**
- **Horizontal Scaling**: Multiple agent instances
- **Database Optimization**: Query optimization and indexing
- **Caching Layer**: Redis for improved performance
- **CDN Integration**: Static asset delivery optimization

---

## 📞 Support

For questions, issues, or contributions:
- 📧 Email: support@ecommerce-agent.com
- 🐛 Issues: GitHub Issues
- 📖 Documentation: `/docs` endpoint  
- 💬 Community: Discord/Slack channel

**Happy building with LangChain + MCP! 🚀**
