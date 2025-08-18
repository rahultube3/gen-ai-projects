#!/usr/bin/env python3
"""
Test script for Simplified E-commerce RAG MCP Server
"""

import asyncio
import json
import subprocess
import sys
import time

async def test_mcp_server():
    """Test the simplified MCP server."""
    print("🔌 Testing Simplified E-commerce RAG MCP Server")
    print("=" * 60)
    
    test_commands = [
        {
            "name": "Initialize Server",
            "command": '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
        },
        {
            "name": "List Tools",
            "command": '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
        },
        {
            "name": "Search Products",
            "command": '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_products","arguments":{"query":"smartphones"}}}'
        },
        {
            "name": "Get Recommendations",
            "command": '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_recommendations","arguments":{"query":"laptop for programming","limit":3}}}'
        },
        {
            "name": "Chat",
            "command": '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"chat","arguments":{"message":"What are your most popular products?"}}}'
        },
        {
            "name": "List Resources",
            "command": '{"jsonrpc":"2.0","id":6,"method":"resources/list","params":{}}'
        }
    ]
    
    results = []
    
    for test in test_commands:
        print(f"\n🧪 Testing: {test['name']}")
        
        try:
            # Run the MCP server with the test command
            process = subprocess.Popen(
                ["uv", "run", "python", "mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send the command and get response
            stdout, stderr = process.communicate(input=test['command'], timeout=30)
            
            if process.returncode == 0 and stdout:
                try:
                    response = json.loads(stdout.strip().split('\n')[-1])  # Get last line (JSON response)
                    
                    if "result" in response:
                        print(f"   ✅ PASSED - Got valid response")
                        
                        # Show specific details for certain tests
                        if test['name'] == "List Tools":
                            tools = response["result"].get("tools", [])
                            print(f"   🔧 Found {len(tools)} tools: {[t['name'] for t in tools]}")
                        elif test['name'] == "Search Products":
                            content = response["result"]["content"][0]['text']
                            print(f"   📝 Response: {content[:100]}...")
                        
                        results.append({"test": test['name'], "success": True})
                    else:
                        print(f"   ❌ FAILED - No result in response")
                        results.append({"test": test['name'], "success": False})
                
                except json.JSONDecodeError:
                    print(f"   ❌ FAILED - Invalid JSON response")
                    results.append({"test": test['name'], "success": False})
            else:
                print(f"   ❌ FAILED - Process error or no output")
                if stderr:
                    print(f"   Error: {stderr[:200]}...")
                results.append({"test": test['name'], "success": False})
        
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT - Test took too long")
            results.append({"test": test['name'], "success": False})
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            results.append({"test": test['name'], "success": False})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"🎯 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Simplified MCP server is working correctly.")
        print("\n📋 Next Steps:")
        print("1. Copy claude_desktop_config.json to your Claude Desktop configuration")
        print("2. Restart Claude Desktop")
        print("3. Test with Claude using the available tools:")
        print("   - Search for products: 'Search for smartphones'")
        print("   - Get recommendations: 'Recommend laptops for programming'")
        print("   - Chat: 'What are your most popular products?'")
        print("   - Order stats: 'Show me order statistics'")
    else:
        print("\n⚠️ Some tests failed. Check the server implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)
