#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for E-commerce RAG Assistant
Uses mcp[cli] for simplified Claude Desktop integration.
"""

import asyncio
import json
import logging
from typing import Any, Sequence, Dict, List, Optional
import sys

# MCP CLI imports - simplified approach
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client  
# from mcp.shared.exceptions import McpError

from rag_assistant import EcommerceRAGAssistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce-rag-mcp")

# Initialize the RAG assistant
rag_assistant = None

class EcommerceRAGMCPServer:
    """MCP Server for E-commerce RAG Assistant using mcp[cli]."""
    
    def __init__(self):
        self.rag_assistant = None
        self.tools = {}
        self.resources = {}
        self._initialize_tools()
        self._initialize_resources()
    
    async def initialize(self):
        """Initialize the RAG assistant."""
        logger.info("🚀 Initializing E-commerce RAG Assistant...")
        try:
            self.rag_assistant = EcommerceRAGAssistant()
            logger.info("✅ RAG Assistant initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Assistant: {e}")
            return False
    
    def _initialize_tools(self):
        """Initialize MCP tools."""
        self.tools = {
            "search_products": {
                "name": "search_products",
                "description": "Search for products in the e-commerce database using natural language queries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query for products"
                        },
                        "category": {
                            "type": "string", 
                            "description": "Optional product category filter",
                            "default": None
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_product_recommendations": {
                "name": "get_product_recommendations",
                "description": "Get personalized product recommendations based on user preferences",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "Description of what the user is looking for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of recommendations",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["user_query"]
                }
            },
            "chat_with_assistant": {
                "name": "chat_with_assistant", 
                "description": "Have a natural conversation with the e-commerce RAG assistant",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Natural language message to send to the assistant"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context or conversation history",
                            "default": None
                        }
                    },
                    "required": ["message"]
                }
            },
            "analyze_product_trends": {
                "name": "analyze_product_trends",
                "description": "Analyze product trends, popular categories, and sales patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of analysis to perform",
                            "enum": ["sales_trends", "popular_products", "category_analysis", "price_analysis"],
                            "default": "popular_products"
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Time period for analysis",
                            "enum": ["last_week", "last_month", "last_quarter", "all_time"],
                            "default": "last_month"
                        }
                    },
                    "required": ["analysis_type"]
                }
            },
            "get_order_insights": {
                "name": "get_order_insights",
                "description": "Get insights about customer orders and statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "insight_type": {
                            "type": "string",
                            "description": "Type of order insight to retrieve",
                            "enum": ["recent_orders", "order_statistics", "customer_behavior", "revenue_analysis"],
                            "default": "order_statistics"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["insight_type"]
                }
            }
        }
    
    def _initialize_resources(self):
        """Initialize MCP resources."""
        self.resources = {
            "ecommerce://products/catalog": {
                "uri": "ecommerce://products/catalog",
                "name": "Product Catalog",
                "description": "Complete e-commerce product catalog with search capabilities",
                "mimeType": "application/json"
            },
            "ecommerce://orders/insights": {
                "uri": "ecommerce://orders/insights", 
                "name": "Order Insights",
                "description": "Customer order data and analytics",
                "mimeType": "application/json"
            },
            "ecommerce://recommendations/engine": {
                "uri": "ecommerce://recommendations/engine",
                "name": "Recommendation Engine", 
                "description": "AI-powered product recommendation system",
                "mimeType": "application/json"
            }
        }
    
    async def list_tools(self) -> List[Dict]:
        """List available tools."""
        return list(self.tools.values())
    
    async def call_tool(self, name: str, arguments: Dict) -> str:
        """Handle tool calls."""
        if not self.rag_assistant:
            return "❌ RAG Assistant not initialized"
        
        try:
            if name == "search_products":
                query = arguments.get("query", "")
                category = arguments.get("category")
                
                search_query = query
                if category:
                    search_query += f" category:{category}"
                
                response = self.rag_assistant.chat(f"Search for products: {search_query}")
                return f"🔍 Product Search Results for '{query}':\n\n{response}"
            
            elif name == "get_product_recommendations":
                user_query = arguments.get("user_query", "")
                limit = arguments.get("limit", 5)
                
                recommendations = self.rag_assistant.get_product_recommendations(user_query, limit=limit)
                
                if recommendations:
                    result = f"🎯 Product Recommendations for '{user_query}':\n\n"
                    for i, rec in enumerate(recommendations, 1):
                        result += f"{i}. **{rec['brand']} {rec['name']}**\n"
                        result += f"   💰 Price: ${rec['price']}\n"
                        result += f"   ⭐ Rating: {rec['rating']}/5.0\n"
                        result += f"   📦 Stock: {rec['stock']} units\n"
                        result += f"   📝 Description: {rec['description']}\n\n"
                else:
                    result = f"❌ No recommendations found for '{user_query}'"
                
                return result
            
            elif name == "chat_with_assistant":
                message = arguments.get("message", "")
                context = arguments.get("context")
                
                if context:
                    full_message = f"Context: {context}\n\nUser: {message}"
                else:
                    full_message = message
                
                response = self.rag_assistant.chat(full_message)
                return f"🤖 Assistant Response:\n\n{response}"
            
            elif name == "analyze_product_trends":
                analysis_type = arguments.get("analysis_type", "popular_products")
                time_period = arguments.get("time_period", "last_month")
                
                query = f"Analyze {analysis_type} for {time_period}"
                response = self.rag_assistant.chat(f"Provide analysis: {query}")
                return f"📊 Product Trends Analysis ({analysis_type} - {time_period}):\n\n{response}"
            
            elif name == "get_order_insights":
                insight_type = arguments.get("insight_type", "order_statistics")
                limit = arguments.get("limit", 10)
                
                if insight_type == "recent_orders":
                    query = f"Show me the {limit} most recent orders"
                elif insight_type == "order_statistics":
                    query = "Show me order statistics and metrics"
                elif insight_type == "customer_behavior":
                    query = "Analyze customer ordering behavior patterns"
                elif insight_type == "revenue_analysis":
                    query = "Provide revenue analysis and insights"
                else:
                    query = f"Provide insights about {insight_type}"
                
                response = self.rag_assistant.chat(query)
                return f"📈 Order Insights ({insight_type}):\n\n{response}"
            
            else:
                return f"❌ Unknown tool: {name}"
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"❌ Error executing {name}: {str(e)}"
    
    async def list_resources(self) -> List[Dict]:
        """List available resources."""
        return list(self.resources.values())
    
    async def read_resource(self, uri: str) -> str:
        """Read resource content."""
        if not self.rag_assistant:
            return "❌ RAG Assistant not initialized"
        
        try:
            if uri == "ecommerce://products/catalog":
                response = self.rag_assistant.chat("Show me all available products with their details")
                return f"📦 E-commerce Product Catalog:\n\n{response}"
            
            elif uri == "ecommerce://orders/insights":
                response = self.rag_assistant.chat("Provide comprehensive order insights and statistics")
                return f"📊 Order Insights Dashboard:\n\n{response}"
            
            elif uri == "ecommerce://recommendations/engine":
                return """🎯 AI-Powered Recommendation Engine

This resource provides access to our advanced recommendation system that uses:

1. **Vector Similarity Search**: Semantic understanding of product features
2. **Customer Behavior Analysis**: Purchase history and preferences  
3. **Real-time Inventory**: Live stock and availability data
4. **Rating-based Filtering**: Quality-assured recommendations

Available recommendation types:
- Similar products based on user query
- Category-specific recommendations
- Price-range filtered suggestions
- Highly-rated product suggestions

Use the 'get_product_recommendations' tool to access personalized recommendations.
"""
            
            else:
                return f"❌ Unknown resource: {uri}"
        
        except Exception as e:
            logger.error(f"Resource read error: {e}")
            return f"❌ Error reading resource {uri}: {str(e)}"

# Create server instance
server = EcommerceRAGMCPServer()

async def handle_mcp_request(request: Dict) -> Dict:
    """Handle MCP protocol requests."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")
    
    try:
        if method == "initialize":
            success = await server.initialize()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "ecommerce-rag-assistant",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = await server.list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await server.call_tool(name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result}]
                }
            }
        
        elif method == "resources/list":
            resources = await server.list_resources()
            return {
                "jsonrpc": "2.0", 
                "id": request_id,
                "result": {"resources": resources}
            }
        
        elif method == "resources/read":
            uri = params.get("uri", "")
            content = await server.read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [{"uri": uri, "mimeType": "text/plain", "text": content}]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

async def main():
    """Main function to run the MCP server."""
    logger.info("🔌 Starting E-commerce RAG MCP Server with mcp[cli]...")
    
    try:
        while True:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await handle_mcp_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON request: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
    
    except KeyboardInterrupt:
        logger.info("🛑 MCP Server shutting down...")
    except Exception as e:
        logger.error(f"❌ MCP Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
