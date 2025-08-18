#!/usr/bin/env python3
"""
Simplified MCP Server for E-commerce RAG Assistant
Uses direct JSON-RPC over stdio for Claude Desktop integration.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional

from rag_assistant import EcommerceRAGAssistant

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ecommerce-mcp")

class SimpleMCPServer:
    """Simplified MCP server using direct JSON-RPC."""
    
    def __init__(self):
        self.rag_assistant = None
        self.initialized = False
    
    async def initialize_assistant(self):
        """Initialize the RAG assistant."""
        if self.initialized:
            return True
        
        logger.info("🚀 Initializing E-commerce RAG Assistant...")
        try:
            self.rag_assistant = EcommerceRAGAssistant()
            self.initialized = True
            logger.info("✅ RAG Assistant initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Assistant: {e}")
            return False
    
    def get_tools(self) -> List[Dict]:
        """Get list of available tools."""
        return [
            {
                "name": "search_products",
                "description": "Search for products using natural language queries",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query for products"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional product category filter"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_recommendations",
                "description": "Get AI-powered product recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What the user is looking for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of recommendations",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "chat",
                "description": "Chat with the e-commerce assistant",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to send to the assistant"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "get_order_stats",
                "description": "Get order statistics and insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Type of statistics",
                            "enum": ["recent", "stats", "trends"],
                            "default": "stats"
                        }
                    }
                }
            }
        ]
    
    def get_resources(self) -> List[Dict]:
        """Get list of available resources."""
        return [
            {
                "uri": "ecommerce://products",
                "name": "Product Catalog",
                "description": "Complete product catalog",
                "mimeType": "text/plain"
            },
            {
                "uri": "ecommerce://orders",
                "name": "Order Data",
                "description": "Order insights and statistics",
                "mimeType": "text/plain"
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict) -> str:
        """Execute a tool and return the result."""
        if not self.initialized:
            return "❌ Assistant not initialized"
        
        try:
            if name == "search_products":
                query = arguments.get("query", "")
                category = arguments.get("category")
                
                search_query = query
                if category:
                    search_query += f" category:{category}"
                
                response = self.rag_assistant.chat(f"Search for products: {search_query}")
                return f"🔍 Product Search Results:\n\n{response}"
            
            elif name == "get_recommendations":
                query = arguments.get("query", "")
                limit = arguments.get("limit", 5)
                
                recommendations = self.rag_assistant.get_product_recommendations(query, limit=limit)
                
                if recommendations:
                    result = f"🎯 Recommendations for '{query}':\n\n"
                    for i, rec in enumerate(recommendations, 1):
                        result += f"{i}. **{rec['brand']} {rec['name']}** - ${rec['price']}\n"
                        result += f"   ⭐ Rating: {rec['rating']}/5.0 | 📦 Stock: {rec['stock']}\n"
                        result += f"   📝 {rec['description']}\n\n"
                    return result
                else:
                    return f"❌ No recommendations found for '{query}'"
            
            elif name == "chat":
                message = arguments.get("message", "")
                response = self.rag_assistant.chat(message)
                return f"🤖 Assistant: {response}"
            
            elif name == "get_order_stats":
                stat_type = arguments.get("type", "stats")
                
                if stat_type == "recent":
                    query = "Show me recent orders"
                elif stat_type == "trends":
                    query = "Analyze order trends and patterns"
                else:
                    query = "Show me order statistics"
                
                response = self.rag_assistant.chat(query)
                return f"📊 Order {stat_type.title()}: {response}"
            
            else:
                return f"❌ Unknown tool: {name}"
        
        except Exception as e:
            logger.error(f"Tool error: {e}")
            return f"❌ Error: {str(e)}"
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource."""
        if not self.initialized:
            return "❌ Assistant not initialized"
        
        try:
            if uri == "ecommerce://products":
                response = self.rag_assistant.chat("Show me all available products")
                return f"📦 Product Catalog:\n\n{response}"
            
            elif uri == "ecommerce://orders":
                response = self.rag_assistant.chat("Provide order insights and statistics")
                return f"📊 Order Data:\n\n{response}"
            
            else:
                return f"❌ Unknown resource: {uri}"
        
        except Exception as e:
            logger.error(f"Resource error: {e}")
            return f"❌ Error: {str(e)}"
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle an MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                success = await self.initialize_assistant()
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
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": self.get_tools()
                    }
                }
            
            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                result = await self.call_tool(name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }
            
            elif method == "resources/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "resources": self.get_resources()
                    }
                }
            
            elif method == "resources/read":
                uri = params.get("uri", "")
                content = await self.read_resource(uri)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "text/plain",
                                "text": content
                            }
                        ]
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
            logger.error(f"Request handling error: {e}")
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
    logger.info("🔌 Starting Simplified E-commerce RAG MCP Server...")
    
    server = SimpleMCPServer()
    
    try:
        while True:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            
            if not line:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                request = json.loads(line)
                response = await server.handle_request(request)
                
                # Write response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
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
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
