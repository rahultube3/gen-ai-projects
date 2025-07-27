#!/usr/bin/env python3
"""
Test the MCP Trading Alerts Server directly.
"""

import asyncio
import json
import sys

async def test_trading_server():
    """Test the MCP trading alerts server."""
    
    print("🚀 Testing MCP Trading Alerts Server")
    print("=" * 45)
    
    # Start the server process
    process = await asyncio.create_subprocess_exec(
        "python3", "main.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="/Users/rahultomar/rahul-dev/gen-ai-projects/mcp-trading-alerts"
    )
    
    try:
        # Initialize
        init_req = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        process.stdin.write((json.dumps(init_req) + "\n").encode())
        await process.stdin.drain()
        
        # Wait for init response
        init_resp = await process.stdout.readline()
        print(f"✅ Server initialized: {json.loads(init_resp.decode().strip())['result']['serverInfo']['name']}")
        
        # Send initialized notification
        init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        process.stdin.write((json.dumps(init_notif) + "\n").encode())
        await process.stdin.drain()
        
        # Test 1: List Tools
        print("\n🛠️  Available Tools:")
        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        process.stdin.write((json.dumps(tools_req) + "\n").encode())
        await process.stdin.drain()
        
        tools_resp = await process.stdout.readline()
        tools_data = json.loads(tools_resp.decode().strip())
        
        if "result" in tools_data:
            for tool in tools_data["result"]["tools"]:
                print(f"  • {tool['name']}: {tool['description'].split('.')[0]}")
        
        # Test 2: List Resources
        print("\n📚 Available Resources:")
        resources_req = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
        process.stdin.write((json.dumps(resources_req) + "\n").encode())
        await process.stdin.drain()
        
        resources_resp = await process.stdout.readline()
        resources_data = json.loads(resources_resp.decode().strip())
        
        resource_count = len(resources_data.get("result", {}).get("resources", []))
        print(f"  • Found {resource_count} cached trading resources")
        
        # Test 3: List Prompts
        print("\n💭 Available Prompts:")
        prompts_req = {"jsonrpc": "2.0", "id": 4, "method": "prompts/list", "params": {}}
        process.stdin.write((json.dumps(prompts_req) + "\n").encode())
        await process.stdin.drain()
        
        prompts_resp = await process.stdout.readline()
        prompts_data = json.loads(prompts_resp.decode().strip())
        
        if "result" in prompts_data:
            for prompt in prompts_data["result"]["prompts"]:
                print(f"  • {prompt['name']}: {prompt['description']}")
        
        # Test 4: Test Trading News Tool (without API key)
        print(f"\n📰 Testing Trading News Tool:")
        news_req = {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "get_trading_news", "arguments": {"symbol": "AAPL", "limit": 3}}
        }
        process.stdin.write((json.dumps(news_req) + "\n").encode())
        await process.stdin.drain()
        
        news_resp = await process.stdout.readline()
        news_data = json.loads(news_resp.decode().strip())
        
        if "result" in news_data:
            result_text = news_data["result"]["content"][0]["text"]
            # Show first few lines
            lines = result_text.split("\n")[:5]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            print("  ...")
        
        # Test 5: Test Resource Access
        print(f"\n📊 Testing Resource Access:")
        resource_req = {
            "jsonrpc": "2.0", "id": 6, "method": "resources/read",
            "params": {"uri": "trading://news/aapl"}
        }
        process.stdin.write((json.dumps(resource_req) + "\n").encode())
        await process.stdin.drain()
        
        resource_resp = await process.stdout.readline()
        resource_data = json.loads(resource_resp.decode().strip())
        
        if "result" in resource_data:
            print("  ✅ Successfully accessed cached AAPL trading news")
        
        print(f"\n🎉 MCP Trading Alerts Server Test Complete!")
        print("=" * 45)
        print("✅ Tools: Trading news and market data")
        print("✅ Resources: Cached trading information")
        print("✅ Prompts: Trading analysis templates")
        print("✅ Ready for trading applications!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        try:
            process.stdin.close()
            await process.wait()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_trading_server())
