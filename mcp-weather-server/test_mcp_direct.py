#!/usr/bin/env python3
"""
Direct MCP Weather Server Test
Tests the weather server directly using MCP protocol.
"""

import asyncio
import json
import subprocess
import sys

async def test_mcp_server():
    """Test the MCP weather server directly."""
    print("🧪 Testing MCP Weather Server Directly")
    print("=" * 40)
    
    try:
        # Start the MCP server process
        print("Starting MCP server...")
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "python", "main.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/Users/rahultomar/rahul-dev/gen-ai-projects/mcp-weather-server"
        )
        
        # Initialize the server
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read response
        init_response = await process.stdout.readline()
        if init_response:
            print(f"Initialize response: {init_response.decode().strip()}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        print("Sending initialized notification...")
        process.stdin.write((json.dumps(initialized_notification) + "\n").encode())
        await process.stdin.drain()
        
        # List tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("Requesting tools list...")
        process.stdin.write((json.dumps(tools_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read tools response
        tools_response = await process.stdout.readline()
        if tools_response:
            print(f"Tools response: {tools_response.decode().strip()}")
            tools_data = json.loads(tools_response.decode().strip())
            if "result" in tools_data and "tools" in tools_data["result"]:
                print(f"✅ Found {len(tools_data['result']['tools'])} tools:")
                for tool in tools_data['result']['tools']:
                    print(f"  - {tool['name']}: {tool['description']}")
        
        # List resources
        resources_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }
        
        print("\nRequesting resources list...")
        process.stdin.write((json.dumps(resources_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read resources response
        resources_response = await process.stdout.readline()
        if resources_response:
            print(f"Resources response: {resources_response.decode().strip()}")
            resources_data = json.loads(resources_response.decode().strip())
            if "result" in resources_data and "resources" in resources_data["result"]:
                print(f"✅ Found {len(resources_data['result']['resources'])} resources:")
                for resource in resources_data['result']['resources']:
                    print(f"  - {resource['uri']}: {resource['name']}")
        
        # List prompts
        prompts_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "prompts/list",
            "params": {}
        }
        
        print("\nRequesting prompts list...")
        process.stdin.write((json.dumps(prompts_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read prompts response
        prompts_response = await process.stdout.readline()
        if prompts_response:
            print(f"Prompts response: {prompts_response.decode().strip()}")
            prompts_data = json.loads(prompts_response.decode().strip())
            if "result" in prompts_data and "prompts" in prompts_data["result"]:
                print(f"✅ Found {len(prompts_data['result']['prompts'])} prompts:")
                for prompt in prompts_data['result']['prompts']:
                    print(f"  - {prompt['name']}: {prompt['description']}")
        
        # Test a tool call
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_alerts",
                "arguments": {
                    "state": "CA"
                }
            }
        }
        
        print("\nTesting get_alerts tool for California...")
        process.stdin.write((json.dumps(tool_call_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read tool call response
        tool_response = await process.stdout.readline()
        if tool_response:
            print(f"Tool response: {tool_response.decode().strip()}")
            tool_data = json.loads(tool_response.decode().strip())
            if "result" in tool_data:
                print("✅ Tool call successful!")
                if "content" in tool_data["result"]:
                    for content in tool_data["result"]["content"]:
                        if content["type"] == "text":
                            print(f"Alert data length: {len(content['text'])} characters")
        
        # Close the process
        process.stdin.close()
        await process.wait()
        
        print("\n🎉 MCP server test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
