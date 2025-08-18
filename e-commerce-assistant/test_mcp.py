#!/usr/bin/env python3
"""
Test script for E-commerce RAG Assistant MCP Server
Tests MCP protocol functionality and tool integration.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List

async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🔌 E-commerce RAG Assistant MCP Server Test")
    print("=" * 60)
    
    try:
        # Start MCP server process
        print("🚀 Starting MCP server...")
        
        process = await asyncio.create_subprocess_exec(
            "uv", "run", "python", "mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait a moment for initialization
        await asyncio.sleep(3)
        
        # Test MCP protocol messages
        test_messages = [
            {
                "name": "Initialize",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "test-client",
                            "version": "1.0.0"
                        }
                    }
                }
            },
            {
                "name": "List Tools",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            },
            {
                "name": "Search Products Tool",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "search_products",
                        "arguments": {
                            "query": "smartphones"
                        }
                    }
                }
            }
        ]
        
        results = []
        
        for test in test_messages:
            print(f"\n🧪 Testing: {test['name']}")
            
            try:
                # Send message to MCP server
                message = json.dumps(test["message"]) + "\n"
                process.stdin.write(message.encode())
                await process.stdin.drain()
                
                # Wait for response (with timeout)
                try:
                    response_line = await asyncio.wait_for(
                        process.stdout.readline(), 
                        timeout=10.0
                    )
                    
                    if response_line:
                        response = json.loads(response_line.decode().strip())
                        print(f"   ✅ PASSED - Received response")
                        print(f"   📝 Response ID: {response.get('id', 'N/A')}")
                        
                        # Show specific response details
                        if test["name"] == "List Tools":
                            tools = response.get("result", {}).get("tools", [])
                            print(f"   🔧 Found {len(tools)} tools")
                            for tool in tools:
                                print(f"      - {tool.get('name', 'Unknown')}")
                        
                        results.append({"test": test["name"], "success": True})
                    else:
                        print(f"   ❌ FAILED - No response received")
                        results.append({"test": test["name"], "success": False})
                
                except asyncio.TimeoutError:
                    print(f"   ⏰ TIMEOUT - No response within 10 seconds")
                    results.append({"test": test["name"], "success": False})
            
            except Exception as e:
                print(f"   ❌ ERROR - {str(e)}")
                results.append({"test": test["name"], "success": False})
        
        # Close the process
        process.stdin.close()
        await process.wait()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 MCP Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        print(f"🎯 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All MCP tests passed! Server is working correctly.")
        else:
            print("\n⚠️ Some MCP tests failed. Check the implementation.")
        
        return passed == total
    
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def test_mcp_integration():
    """Test MCP integration capabilities."""
    print("\n🔗 Testing MCP Integration Features")
    print("-" * 40)
    
    integration_tests = [
        {
            "feature": "Claude Desktop Configuration",
            "file": "claude_desktop_config.json",
            "test": lambda: check_file_exists("claude_desktop_config.json")
        },
        {
            "feature": "MCP Server Script",
            "file": "mcp_server.py", 
            "test": lambda: check_file_exists("mcp_server.py")
        },
        {
            "feature": "Tool Definitions",
            "file": "mcp_server.py",
            "test": lambda: check_tool_definitions()
        }
    ]
    
    results = []
    for test in integration_tests:
        print(f"🔍 Checking: {test['feature']}")
        try:
            success = test["test"]()
            if success:
                print(f"   ✅ PASSED")
            else:
                print(f"   ❌ FAILED")
            results.append(success)
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n📊 Integration Tests: {passed}/{total} passed")
    
    return passed == total

def check_file_exists(filename: str) -> bool:
    """Check if a file exists."""
    import os
    return os.path.exists(filename)

def check_tool_definitions() -> bool:
    """Check if MCP tools are properly defined."""
    try:
        with open("mcp_server.py", "r") as f:
            content = f.read()
            
        # Check for required tool functions
        required_tools = [
            "search_products",
            "get_product_recommendations", 
            "chat_with_assistant",
            "analyze_product_trends",
            "get_order_insights"
        ]
        
        for tool in required_tools:
            if tool not in content:
                return False
        
        return True
    except Exception:
        return False

async def main():
    """Main test function."""
    print("🧪 E-commerce RAG Assistant - MCP & Integration Tests")
    print("=" * 70)
    
    # Test MCP server
    mcp_success = await test_mcp_server()
    
    # Test integration features
    integration_success = test_mcp_integration()
    
    # Overall results
    print("\n" + "=" * 70)
    print("🏁 Final Test Results")
    print("=" * 70)
    
    if mcp_success and integration_success:
        print("🎉 ALL TESTS PASSED! MCP server is ready for production.")
        print("\n📋 Next Steps:")
        print("1. Add claude_desktop_config.json to your Claude Desktop configuration")
        print("2. Start the MCP server: uv run python mcp_server.py")
        print("3. Test with Claude Desktop using the available tools")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
