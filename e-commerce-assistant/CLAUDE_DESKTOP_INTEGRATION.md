# Claude Desktop Integration Guide

## 🎯 Overview

This guide shows how to integrate the MCP microservices with Claude Desktop, enabling AI-powered conversations with your e-commerce system.

## 📋 Prerequisites

1. **Claude Desktop installed**: Download from [claude.ai/download](https://claude.ai/download)
2. **MongoDB running**: Ensure your MongoDB instance is accessible
3. **Services validated**: Run `./orchestration/manage_services.sh validate` to ensure all services work
4. **Python environment**: Ensure `uv` and dependencies are installed

## 🔧 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
./setup_claude_integration.sh
```

This script will:
- Detect your Claude Desktop configuration location
- Backup any existing configuration
- Copy the appropriate MCP configuration
- Test the connection
- Provide next steps

### Option 2: Manual Setup

1. **Find your Claude Desktop config location:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

2. **Choose a configuration approach:**

#### Approach A: Gateway Only (Recommended)
Use the gateway service as the single entry point:

```json
{
  "mcpServers": {
    "ecommerce-gateway": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/Users/rahultomar/rahul-dev/gen-ai-projects/e-commerce-assistant/services/gateway_mcp_service.py"
      ],
      "env": {
        "MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant",
        "PYTHONPATH": "/Users/rahultomar/rahul-dev/gen-ai-projects/e-commerce-assistant"
      }
    }
  }
}
```

#### Approach B: All Services
Access each microservice individually:

```json
{
  "mcpServers": {
    "ecommerce-product": {
      "command": "uv",
      "args": ["run", "python", "/path/to/services/product_mcp_service.py"],
      "env": {"MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant"}
    },
    "ecommerce-recommendations": {
      "command": "uv", 
      "args": ["run", "python", "/path/to/services/recommendation_mcp_service.py"],
      "env": {"MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant"}
    },
    "ecommerce-orders": {
      "command": "uv",
      "args": ["run", "python", "/path/to/services/order_mcp_service.py"], 
      "env": {"MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant"}
    },
    "ecommerce-chat": {
      "command": "uv",
      "args": ["run", "python", "/path/to/services/chat_mcp_service.py"],
      "env": {"MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant"}
    },
    "ecommerce-gateway": {
      "command": "uv",
      "args": ["run", "python", "/path/to/services/gateway_mcp_service.py"],
      "env": {"MONGODB_URI": "mongodb://localhost:27017/ecommerce_assistant"}
    }
  }
}
```

3. **Update paths**: Replace `/Users/rahultomar/rahul-dev/gen-ai-projects/e-commerce-assistant/` with your actual project path

4. **Restart Claude Desktop**

## 🚀 Available Tools & Capabilities

### Gateway Service Tools (Recommended Approach)

When using the gateway service, you get access to these unified tools:

#### 1. **Unified Search** (`unified_search`)
```
Parameters:
- query (required): Search terms
- user_id (optional): User identifier for personalization  
- include_recommendations (optional): Include AI recommendations (default: true)
- limit (optional): Max results (default: 10)

Example: "Search for wireless headphones for user123"
```

#### 2. **Smart Chat** (`smart_chat`)
```
Parameters:
- message (required): User message
- user_id (required): User identifier
- session_id (optional): Chat session ID
- context (optional): Additional context

Example: "Start a conversation about product recommendations"
```

#### 3. **Complete Order Flow** (`complete_order_flow`)
```
Parameters:
- user_id (required): User identifier
- action (required): "view_orders" | "order_analytics" | "reorder_suggestions"
- order_id (optional): Specific order ID

Example: "Show order analytics for user123"
```

#### 4. **Personalized Dashboard** (`personalized_dashboard`)
```
Parameters:
- user_id (required): User identifier
- sections (optional): ["recommendations", "recent_orders", "trending", "categories"]

Example: "Generate a dashboard for user123 with recommendations and orders"
```

#### 5. **Service Health Check** (`service_health_check`)
```
Parameters:
- detailed (optional): Include detailed info (default: false)

Example: "Check the health of all services"
```

#### 6. **Cross-Service Analytics** (`cross_service_analytics`)
```
Parameters:
- metric_type (required): "user_journey" | "product_performance" | "service_usage" | "conversion_funnel"
- time_range (optional): Time range like "7d", "30d" (default: "7d")
- filters (optional): Additional filters

Example: "Show user journey analytics for the last 30 days"
```

### Individual Service Tools

If using the all-services approach, each service provides specialized tools:

#### Product Service
- `search_products` - Search product catalog
- `get_product_details` - Get detailed product information
- `list_categories` - List all product categories
- `filter_products` - Filter products by criteria

#### Recommendation Service  
- `get_recommendations` - Get AI recommendations
- `similar_products` - Find similar products
- `trending_products` - Get trending products
- `personalized_recommendations` - Get personalized recommendations

#### Order Service
- `get_order_stats` - Get order statistics
- `recent_orders` - Get recent orders
- `order_analytics` - Get detailed order analytics
- `customer_orders` - Get customer order history

#### Chat Service
- `start_conversation` - Start a new conversation
- `continue_conversation` - Continue existing conversation
- `get_conversation_history` - Get conversation history
- `analyze_intent` - Analyze user intent
- `generate_response` - Generate AI response
- `end_conversation` - End conversation session

## 💬 Example Conversations

### Getting Started
```
User: "Can you check if all the e-commerce services are healthy?"
Claude: I'll check the health of all services for you.
[Calls service_health_check tool]
```

### Product Search
```
User: "I'm looking for gaming laptops under $1500 for user john_doe"
Claude: I'll search for gaming laptops in your price range with personalized recommendations.
[Calls unified_search with query="gaming laptops under $1500", user_id="john_doe"]
```

### Order Management
```
User: "Show me the order analytics for user mary_smith"
Claude: I'll get the comprehensive order analytics for mary_smith.
[Calls complete_order_flow with user_id="mary_smith", action="order_analytics"]
```

### Conversational AI
```
User: "Start a shopping conversation for user alex_jones asking about workout equipment"
Claude: I'll start an intelligent conversation about workout equipment.
[Calls smart_chat with message="I'm looking for workout equipment", user_id="alex_jones"]
```

### Dashboard Creation
```
User: "Create a personalized dashboard for user sarah_wilson showing recommendations and recent orders"
Claude: I'll generate a personalized dashboard with recommendations and order history.
[Calls personalized_dashboard with user_id="sarah_wilson", sections=["recommendations", "recent_orders"]]
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Not Found
```
Error: Service not found in Claude Desktop
Solution: 
- Restart Claude Desktop
- Check configuration file path
- Verify absolute paths in config
```

#### 2. MongoDB Connection Error
```
Error: Failed to connect to MongoDB
Solution:
- Ensure MongoDB is running: brew services start mongodb-community
- Check MONGODB_URI in configuration
- Verify database exists
```

#### 3. Python Import Errors
```
Error: ImportError or ModuleNotFoundError
Solution:
- Add PYTHONPATH to environment variables
- Ensure uv environment has all dependencies
- Run: uv install
```

#### 4. Permission Errors
```
Error: Permission denied
Solution:
- Make scripts executable: chmod +x setup_claude_integration.sh
- Check file permissions
- Ensure paths are accessible
```

### Debug Steps

1. **Test service manually:**
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | uv run python services/gateway_mcp_service.py
```

2. **Check service validation:**
```bash
./orchestration/manage_services.sh validate
```

3. **Test MongoDB connection:**
```bash
mongosh mongodb://localhost:27017/ecommerce_assistant
```

4. **View Claude Desktop logs:**
   - **macOS**: `~/Library/Logs/Claude/`
   - **Linux**: `~/.local/share/Claude/logs/`

## 🎯 Best Practices

### 1. **Use Gateway Service** (Recommended)
- Single entry point reduces complexity
- Cross-service coordination built-in  
- Unified API with intelligent routing
- Better error handling and recovery

### 2. **Service Management**
```bash
# Start services before using Claude Desktop
./orchestration/manage_services.sh start

# Check service status
./orchestration/manage_services.sh status

# Stop services when done
./orchestration/manage_services.sh stop
```

### 3. **Database Preparation**
```bash
# Ensure MongoDB is running and has sample data
# Run database setup if needed
uv run python db_setup.py
```

### 4. **Environment Variables**
```bash
# Set environment variables for consistency
export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant"
export PYTHONPATH="/path/to/your/project"
```

## 🚀 Advanced Usage

### Custom Tool Creation
You can extend the services by adding new tools. Example:

```python
# In gateway_mcp_service.py
async def custom_recommendation_tool(self, user_preferences: Dict) -> Dict:
    """Custom recommendation logic."""
    # Your implementation here
    pass
```

### Service Extension
Add new microservices by:
1. Creating a new service class extending `BaseMCPService`
2. Adding it to `services_config.json`  
3. Registering in Claude Desktop configuration

### Monitoring Integration
Monitor service performance:
```bash
# View service logs
tail -f logs/gateway_service.log

# Check metrics
./orchestration/manage_services.sh metrics
```

## 📚 Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Desktop Documentation](https://claude.ai/docs)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Project Architecture Guide](./MICROSERVICES_ARCHITECTURE.md)
- [Implementation Summary](./MICROSERVICES_IMPLEMENTATION.md)

## 🔄 Updates & Maintenance

### Updating Services
```bash
# Pull latest changes
git pull origin main

# Update dependencies  
uv install

# Restart services
./orchestration/manage_services.sh restart

# Update Claude Desktop (restart application)
```

### Configuration Updates
When updating service configurations:
1. Stop Claude Desktop
2. Update configuration files
3. Restart Claude Desktop
4. Test functionality

---

**Ready to start?** Run `./setup_claude_integration.sh` and begin your AI-powered e-commerce conversations! 🎉
