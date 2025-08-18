# 🛠️ LangChain Agent Management Script Usage Guide

## 📋 Overview

The `manage_langchain_agent.sh` script is your **complete management tool** for the LangChain + MCP e-commerce system. It handles everything from environment checks to service orchestration.

## 🚀 Quick Start

### **1. Basic Setup & Start**
```bash
# Quick start everything (recommended for first-time users)
./quickstart_langchain.sh

# Or step by step:
export OPENAI_API_KEY="your-api-key-here"
./manage_langchain_agent.sh start
```

### **2. Check System Status**
```bash
./manage_langchain_agent.sh status
```

### **3. Test Everything**
```bash
./manage_langchain_agent.sh test
```

## 📖 Complete Command Reference

### **🎯 Core Commands**

#### `start` - Start All Services
```bash
./manage_langchain_agent.sh start
```
**What it does:**
- ✅ Checks environment variables (OPENAI_API_KEY, MONGODB_URI)
- ✅ Validates dependencies (uv, Python packages)
- ✅ Starts all 5 MCP microservices
- ✅ Starts LangChain API server on port 8001
- ✅ Runs health checks and validation

**Output:**
```
================================
 Checking Environment
================================
[INFO] ✅ OPENAI_API_KEY is set
[INFO] ✅ MONGODB_URI is set

================================
 Starting MCP Services
================================
[INFO] 🚀 Starting all MCP microservices...
[✓] ✅ MCP services started successfully

================================
 Starting LangChain API Server
================================
[INFO] 🚀 Starting LangChain API server...
[✓] ✅ LangChain API server started successfully (PID: 12345)
[INFO] 📚 API Documentation: http://localhost:8001/docs
```

#### `stop` - Stop All Services
```bash
./manage_langchain_agent.sh stop
```

#### `restart` - Restart Everything
```bash
./manage_langchain_agent.sh restart
```

#### `status` - Show System Status
```bash
./manage_langchain_agent.sh status
```
**Sample Output:**
```
MCP Services:
  ✅ product-service: Running (PID: 12346)
  ✅ recommendation-service: Running (PID: 12347)
  ✅ order-service: Running (PID: 12348)
  ✅ chat-service: Running (PID: 12349)
  ✅ gateway-service: Running (PID: 12350)

LangChain API Server:
  ✅ Running (PID: 12345)
  URL: http://localhost:8001
  Docs: http://localhost:8001/docs

Health Check:
  ✅ API server is responding
```

### **🔍 Monitoring Commands**

#### `logs` - View System Logs
```bash
# View all logs
./manage_langchain_agent.sh logs

# View specific service logs
./manage_langchain_agent.sh logs api      # LangChain API server
./manage_langchain_agent.sh logs mcp      # MCP services
./manage_langchain_agent.sh logs all      # Everything
```

#### `health` - Quick Health Check
```bash
./manage_langchain_agent.sh health
```
**Returns:** Exit code 0 if healthy, 1 if not

#### `test` - Run System Tests
```bash
./manage_langchain_agent.sh test
```
**What it tests:**
- ✅ MCP services functionality
- ✅ LangChain integration
- ✅ API endpoints (health, chat)
- ✅ Database connectivity

### **🎛️ Individual Service Management**

#### Start/Stop MCP Services Only
```bash
./manage_langchain_agent.sh start-mcp    # Start MCP services
./manage_langchain_agent.sh stop-mcp     # Stop MCP services
```

#### Start/Stop API Server Only
```bash
./manage_langchain_agent.sh start-api    # Start LangChain API
./manage_langchain_agent.sh stop-api     # Stop LangChain API
```

### **💬 Interactive Mode**

#### `cli` - Start Interactive CLI Agent
```bash
./manage_langchain_agent.sh cli
```
**Features:**
- Direct conversation with AI agent
- Full access to all MCP tools
- Memory management across conversation
- Type `quit` to exit, `reset` to clear memory

**Example session:**
```
🤖 E-commerce LangChain Agent Ready!
Type 'quit' to exit, 'reset' to clear memory
--------------------------------------------------

👤 You: Find gaming laptops under $1500

🤖 Assistant: I'll search for gaming laptops in your price range with intelligent recommendations.

[Uses unified_search tool]

Here are the best gaming laptops under $1500:

1. **ASUS ROG Strix G15** - $1,299 ⭐⭐⭐⭐⭐
   • AMD Ryzen 7, RTX 3060
   • 16GB RAM, 512GB SSD
   • 144Hz display

2. **Acer Predator Helios 300** - $1,399 ⭐⭐⭐⭐
   • Intel i7, RTX 3060
   • 16GB RAM, 1TB SSD
   • RGB keyboard

Would you like detailed specifications or customer reviews for any of these?

👤 You: Tell me more about the ASUS
```

## 🔧 Environment Setup

### **Required Environment Variables**

```bash
# OpenAI API Key (Required)
export OPENAI_API_KEY="sk-your-openai-api-key-here"

# MongoDB URI (Optional - defaults to localhost)
export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant"

# Or for MongoDB Atlas:
export MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/ecommerce_assistant"
```

### **Persistent Environment Setup**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# LangChain + MCP Environment
export OPENAI_API_KEY="your-api-key-here"
export MONGODB_URI="your-mongodb-uri-here"
export PYTHONPATH="/path/to/e-commerce-assistant:$PYTHONPATH"
```

## 📊 Usage Scenarios

### **🎯 Development Workflow**
```bash
# Morning startup
./manage_langchain_agent.sh start

# Check everything is working
./manage_langchain_agent.sh status

# Run tests after changes
./manage_langchain_agent.sh test

# View logs during development
./manage_langchain_agent.sh logs api

# End of day cleanup
./manage_langchain_agent.sh stop
```

### **🚀 Production Deployment**
```bash
# Start services
./manage_langchain_agent.sh start

# Monitor health
watch -n 30 "./manage_langchain_agent.sh health"

# Check logs
./manage_langchain_agent.sh logs | tee system.log

# Restart if needed
./manage_langchain_agent.sh restart
```

### **🐛 Debugging Issues**
```bash
# Check current status
./manage_langchain_agent.sh status

# View recent logs
./manage_langchain_agent.sh logs

# Test individual components
./manage_langchain_agent.sh start-mcp    # Test MCP services
./manage_langchain_agent.sh start-api    # Test API server

# Run comprehensive tests
./manage_langchain_agent.sh test
```

### **⚡ Quick Tasks**
```bash
# Quick health check
./manage_langchain_agent.sh health

# Interactive chat session
./manage_langchain_agent.sh cli

# Restart just the API server
./manage_langchain_agent.sh stop-api && ./manage_langchain_agent.sh start-api
```

## 🌐 API Usage Examples

Once services are running with `./manage_langchain_agent.sh start`:

### **Health Check**
```bash
curl http://localhost:8001/health
```

### **Chat with Agent**
```bash
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find me wireless headphones under $100",
    "user_id": "user123",
    "session_id": "session456"
  }'
```

### **Product Search**
```bash
curl -X POST "http://localhost:8001/products/search?query=gaming%20mouse&user_id=user123"
```

### **Generate Dashboard**
```bash
curl -X POST "http://localhost:8001/dashboard/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "sections": ["recommendations", "recent_orders"]
  }'
```

## 🔧 Troubleshooting

### **Common Issues**

#### **1. "OPENAI_API_KEY not set"**
```bash
# Set the environment variable
export OPENAI_API_KEY="your-api-key-here"

# Or add to your shell profile for persistence
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### **2. "Failed to start MCP services"**
```bash
# Check individual service logs
./manage_langchain_agent.sh logs mcp

# Try starting MCP services alone
./manage_langchain_agent.sh start-mcp

# Check MongoDB connection
mongosh $MONGODB_URI
```

#### **3. "API server not responding"**
```bash
# Check if port 8001 is in use
lsof -i :8001

# Try starting API server alone
./manage_langchain_agent.sh start-api

# Check API server logs
./manage_langchain_agent.sh logs api
```

#### **4. "Dependencies missing"**
```bash
# Reinstall dependencies
uv sync --reload

# Check Python environment
uv run python --version
uv run python -c "import langchain, fastapi; print('OK')"
```

### **Log Locations**
- **API Server**: `logs/langchain_api_server.log`
- **MCP Services**: `logs/*_service.log`
- **Service Manager**: `logs/service_manager.log`
- **Process IDs**: `pids/*.pid`

## 🎉 Success Indicators

### **✅ Everything Working**
```bash
$ ./manage_langchain_agent.sh status
MCP Services:
  ✅ All 5 services running
LangChain API Server:
  ✅ Running (PID: 12345)
  ✅ Responding at http://localhost:8001
Health Check:
  ✅ System is healthy
```

### **🌐 API Accessible**
- **API Server**: http://localhost:8001
- **Health Check**: http://localhost:8001/health returns `{"status": "healthy"}`
- **Documentation**: http://localhost:8001/docs loads successfully

### **🤖 Agent Responsive**
```bash
$ curl -s http://localhost:8001/health | grep healthy
"status": "healthy"
```

---

## 🚀 You're Ready!

Your **LangChain + MCP e-commerce system** is now fully manageable with this script. The system provides:

- **🤖 AI-powered customer interactions**
- **🔧 Complete service orchestration** 
- **📊 Real-time monitoring and health checks**
- **🛠️ Easy development and debugging workflow**

**Start building amazing AI-powered e-commerce experiences!** 🎉
