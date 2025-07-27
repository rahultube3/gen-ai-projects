#!/usr/bin/env python3
"""
Simple test for the get_fraud_statistics MCP tool.
"""

import asyncio
import json
import logging
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logging.basicConfig(level=logging.INFO)

async def test_fraud_statistics():
    """Test the get_fraud_statistics MCP tool."""
    print("🧪 TESTING GET_FRAUD_STATISTICS MCP TOOL")
    print("=" * 50)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python3", "fraud_server.py"],
        cwd="/app"
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("✅ MCP session initialized")
                
                # List available tools
                tools = await session.list_tools()
                print(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
                
                # Test get_fraud_statistics tool
                print("\n🔍 Testing get_fraud_statistics...")
                result = await session.call_tool("get_fraud_statistics", arguments={})
                
                if result.isError:
                    print(f"❌ Error calling tool")
                else:
                    print("✅ SUCCESS: get_fraud_statistics worked!")
                    print(f"📊 Result: {json.dumps(result.content[0].text, indent=2)}")
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fraud_statistics())
