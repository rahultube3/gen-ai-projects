#!/usr/bin/env python3
"""
Base MCP Service Class
Provides common functionality for all MCP microservices.
"""

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BaseMCPService(ABC):
    """Base class for all MCP microservices."""
    
    def __init__(self, service_name: str, version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.logger = logging.getLogger(f"mcp.{service_name}")
        self.tools = {}
        self.resources = {}
        self.initialized = False
        
        # Register default tools
        self.register_default_tools()
        
        # Service-specific setup
        self.setup_service()
    
    def register_default_tools(self):
        """Register default tools available to all services."""
        self.tools["health_check"] = {
            "name": "health_check",
            "description": f"Check the health status of {self.service_name}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        self.tools["service_info"] = {
            "name": "service_info", 
            "description": f"Get information about {self.service_name}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    
    @abstractmethod
    def setup_service(self):
        """Setup service-specific configuration and resources."""
        pass
    
    @abstractmethod
    def register_tools(self):
        """Register service-specific tools."""
        pass
    
    @abstractmethod
    def register_resources(self):  
        """Register service-specific resources."""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the service."""
        if self.initialized:
            return True
        
        self.logger.info(f"🚀 Initializing {self.service_name} service...")
        
        try:
            # Register tools and resources
            self.register_tools()
            self.register_resources()
            
            # Service-specific initialization
            await self.initialize_service()
            
            self.initialized = True
            self.logger.info(f"✅ {self.service_name} service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize {self.service_name}: {e}")
            return False
    
    async def initialize_service(self):
        """Service-specific initialization logic."""
        pass
    
    def get_tools(self) -> List[Dict]:
        """Get list of available tools."""
        return list(self.tools.values())
    
    def get_resources(self) -> List[Dict]:
        """Get list of available resources."""
        return list(self.resources.values())
    
    async def call_tool(self, name: str, arguments: Dict) -> str:
        """Execute a tool and return the result."""
        if not self.initialized:
            return f"❌ {self.service_name} service not initialized"
        
        try:
            # Handle default tools
            if name == "health_check":
                return await self.health_check()
            elif name == "service_info":
                return await self.service_info()
            
            # Handle service-specific tools
            return await self.execute_tool(name, arguments)
            
        except Exception as e:
            self.logger.error(f"Tool execution error for {name}: {e}")
            return f"❌ Error executing {name}: {str(e)}"
    
    async def execute_tool(self, name: str, arguments: Dict) -> str:
        """Execute service-specific tool."""
        # Check if tool exists in registered tools
        if name in self.tools:
            # Get the method from the class
            if hasattr(self, name):
                method = getattr(self, name)
                return await method(**arguments)
        
        return f"❌ Unknown tool: {name}"
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource."""
        if not self.initialized:
            return f"❌ {self.service_name} service not initialized"
        
        try:
            return await self.read_service_resource(uri)
        except Exception as e:
            self.logger.error(f"Resource read error for {uri}: {e}")
            return f"❌ Error reading resource {uri}: {str(e)}"
    
    async def read_service_resource(self, uri: str) -> str:
        """Read service-specific resource."""
        return f"❌ Unknown resource: {uri}"
    
    async def health_check(self) -> str:
        """Perform health check."""
        return f"✅ {self.service_name} service is healthy (v{self.version})"
    
    async def service_info(self) -> str:
        """Get service information."""
        info = {
            "service": self.service_name,
            "version": self.version,
            "status": "healthy" if self.initialized else "initializing",
            "tools": len(self.tools),
            "resources": len(self.resources),
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(info, indent=2)
    
    async def call_other_service(self, service_command: List[str], tool: str, arguments: Dict) -> Dict:
        """Call another MCP service."""
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *service_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Prepare MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": arguments
                }
            }
            
            # Send request
            input_data = json.dumps(request) + "\n"
            stdout, stderr = await process.communicate(input_data.encode())
            
            if process.returncode == 0 and stdout:
                response = json.loads(stdout.decode().strip())
                return response
            else:
                self.logger.error(f"Service call failed: {stderr.decode() if stderr else 'No output'}")
                return {"error": "Service call failed"}
                
        except Exception as e:
            self.logger.error(f"Error calling other service: {e}")
            return {"error": str(e)}
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle an MCP request."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                success = await self.initialize()
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
                            "name": self.service_name,
                            "version": self.version
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
            self.logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def run(self):
        """Main run loop for the MCP service."""
        self.logger.info(f"� Initializing {self.service_name} service...")
        
        try:
            # Initialize the service
            await self.initialize()
            self.logger.info(f"✅ {self.service_name} service initialized successfully")
            
            # Process MCP messages from stdin
            while True:
                try:
                    # Read line from stdin
                    line = await asyncio.get_event_loop().run_in_executor(
                        None, sys.stdin.readline
                    )
                    
                    if not line:
                        # If no more input, keep running for daemon mode
                        # instead of breaking immediately
                        self.logger.info(f"📨 {self.service_name} waiting for requests...")
                        await asyncio.sleep(5)  # Wait 5 seconds before checking again
                        continue
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse and handle the request
                    try:
                        request = json.loads(line)
                        response = await self.handle_request(request)
                        
                        if response:
                            print(json.dumps(response), flush=True)
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON received: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32700,
                                "message": "Parse error",
                                "data": str(e)
                            }
                        }
                        print(json.dumps(error_response), flush=True)
                        
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info(f"🛑 {self.service_name} service shutting down...")
        except Exception as e:
            self.logger.error(f"Fatal error in {self.service_name}: {e}")
        finally:
            # Cleanup
            if hasattr(self, 'db') and self.db is not None:
                self.db.close()
            self.logger.info(f"👋 {self.service_name} service stopped")
