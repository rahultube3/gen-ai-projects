# 🏗️ MCP Protocol Microservices Architecture

## Overview
Transform the E-commerce RAG Assistant into a **microservices architecture** using the **Model Context Protocol (MCP)** as the communication layer between services.

## 🎯 Architecture Goals
- **Service Isolation**: Each service handles specific business logic
- **MCP Communication**: Services communicate via MCP protocol (JSON-RPC over stdio)
- **Scalability**: Independent scaling of each service
- **Modularity**: Easy to add/remove services
- **Claude Integration**: Each service can be used directly by Claude Desktop

## 🏗️ Microservices Design

### Core Services

#### 1. **Product Service** (`product_mcp_service.py`)
**Purpose**: Handle all product-related operations
```json
{
  "tools": [
    "search_products",
    "get_product_details", 
    "list_categories",
    "filter_products"
  ],
  "resources": [
    "ecommerce://products/catalog",
    "ecommerce://products/categories"
  ]
}
```

#### 2. **Recommendation Service** (`recommendation_mcp_service.py`)
**Purpose**: AI-powered product recommendations
```json
{
  "tools": [
    "get_recommendations",
    "similar_products",
    "trending_products",
    "personalized_recommendations"
  ],
  "resources": [
    "ecommerce://recommendations/engine",
    "ecommerce://recommendations/models"
  ]
}
```

#### 3. **Order Service** (`order_mcp_service.py`)
**Purpose**: Order management and analytics
```json
{
  "tools": [
    "get_order_stats",
    "recent_orders",
    "order_analytics",
    "customer_orders"
  ],
  "resources": [
    "ecommerce://orders/data",
    "ecommerce://orders/analytics"
  ]
}
```

#### 4. **Chat Service** (`chat_mcp_service.py`)
**Purpose**: Conversational AI and natural language processing
```json
{
  "tools": [
    "chat_assistant",
    "natural_language_query",
    "conversation_context"
  ],
  "resources": [
    "ecommerce://chat/history",
    "ecommerce://chat/context"
  ]
}
```

#### 5. **Gateway Service** (`gateway_mcp_service.py`)
**Purpose**: API Gateway and service orchestration
```json
{
  "tools": [
    "route_request",
    "health_check",
    "service_discovery"
  ],
  "resources": [
    "ecommerce://gateway/services",
    "ecommerce://gateway/health"
  ]
}
```

## 🔄 Service Communication

### MCP Service-to-Service Communication
```python
# Service A calls Service B via MCP
async def call_service(service_name: str, tool: str, args: dict):
    process = await create_subprocess_exec(
        f"{service_name}_mcp_service.py",
        stdin=PIPE, stdout=PIPE
    )
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    }
    
    process.stdin.write(json.dumps(request).encode())
    response = await process.stdout.readline()
    return json.loads(response)
```

## 📂 Directory Structure
```
e-commerce-assistant/
├── services/
│   ├── product_mcp_service.py          # Product management
│   ├── recommendation_mcp_service.py   # AI recommendations
│   ├── order_mcp_service.py           # Order processing
│   ├── chat_mcp_service.py            # Conversational AI
│   ├── gateway_mcp_service.py         # API Gateway
│   └── base_mcp_service.py            # Base service class
├── config/
│   ├── services_config.json           # Service configuration
│   └── claude_desktop_services.json   # Claude Desktop config
├── orchestration/
│   ├── service_manager.py             # Service lifecycle
│   ├── health_monitor.py              # Health checking
│   └── load_balancer.py               # Load balancing
├── shared/
│   ├── mcp_client.py                  # MCP client library
│   ├── service_registry.py            # Service discovery
│   └── database.py                    # Shared database access
└── tests/
    ├── test_services.py               # Individual service tests
    └── test_integration.py            # End-to-end tests
```

## 🚀 Benefits

### 1. **Scalability**
- Scale services independently based on load
- Distribute services across multiple machines
- Add service instances dynamically

### 2. **Maintainability**
- Clear separation of concerns
- Independent deployment of services
- Easier debugging and monitoring

### 3. **Claude Integration**
- Each service can be used directly by Claude Desktop
- Fine-grained tool access control
- Service-specific configurations

### 4. **Resilience**
- Service isolation prevents cascading failures
- Independent health monitoring
- Graceful degradation

## 📋 Implementation Plan

### Phase 1: Service Extraction
1. Extract product logic → `product_mcp_service.py`
2. Extract recommendation logic → `recommendation_mcp_service.py`
3. Extract order logic → `order_mcp_service.py`
4. Extract chat logic → `chat_mcp_service.py`

### Phase 2: Service Communication
1. Implement base MCP service class
2. Create MCP client for service-to-service calls
3. Implement service registry/discovery

### Phase 3: Orchestration
1. Service manager for lifecycle management
2. Health monitoring system
3. Load balancing and routing

### Phase 4: Integration
1. Gateway service for external API
2. Claude Desktop configurations
3. End-to-end testing

## 💻 Example Service Implementation

```python
# base_mcp_service.py
class BaseMCPService:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tools = {}
        self.resources = {}
    
    async def handle_request(self, request: dict) -> dict:
        # Standard MCP request handling
        pass
    
    async def call_other_service(self, service: str, tool: str, args: dict):
        # Inter-service communication
        pass

# product_mcp_service.py
class ProductMCPService(BaseMCPService):
    def __init__(self):
        super().__init__("product-service")
        self.register_tools()
    
    def register_tools(self):
        self.tools["search_products"] = self.search_products
        self.tools["get_product_details"] = self.get_product_details
    
    async def search_products(self, query: str) -> str:
        # Product search logic
        pass
```

## 🔧 Configuration Management

### Service Configuration
```json
{
  "services": {
    "product": {
      "port": 8001,
      "instances": 2,
      "resources": ["database", "vector_store"]
    },
    "recommendation": {
      "port": 8002, 
      "instances": 1,
      "resources": ["ml_models", "vector_store"]
    }
  }
}
```

### Claude Desktop Integration
```json
{
  "mcpServers": {
    "ecommerce-products": {
      "command": "uv",
      "args": ["run", "python", "services/product_mcp_service.py"]
    },
    "ecommerce-recommendations": {
      "command": "uv",
      "args": ["run", "python", "services/recommendation_mcp_service.py"]  
    }
  }
}
```

## 📊 Monitoring & Observability

### Health Checks
- Service-level health endpoints
- Dependency health monitoring  
- Circuit breaker patterns

### Metrics
- Request/response times per service
- Error rates and success rates
- Resource utilization

### Logging
- Structured logging per service
- Distributed tracing
- Error aggregation

## 🔄 Next Steps

1. **Choose Services to Implement**: Start with 2-3 core services
2. **Implement Base Classes**: Create reusable MCP service framework
3. **Build Service Registry**: Enable service discovery
4. **Test Integration**: Ensure services work together
5. **Add Orchestration**: Service management and monitoring

This microservices architecture provides a scalable, maintainable foundation while leveraging the MCP protocol for seamless integration with Claude Desktop and inter-service communication.
