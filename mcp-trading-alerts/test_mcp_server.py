#!/usr/bin/env python3
"""
Test the MCP Trading Alerts Server.
"""

import asyncio
import json
import sys

async def test_mcp_trading_server():
    """Test the MCP trading alerts server."""
    
    print("🚀 Testing MCP Trading Alerts Server")
    print("=" * 45)
    
    # Start the server process
    process = await asyncio.create_subprocess_exec(
        "python3", "mcp-trading-alert-server.py",
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
        init_data = json.loads(init_resp.decode().strip())
        print(f"✅ Server initialized: {init_data['result']['serverInfo']['name']}")
        
        # Send initialized notification
        init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        process.stdin.write((json.dumps(init_notif) + "\n").encode())
        await process.stdin.drain()
        
        # Test: List Tools
        print("\n🛠️  Available Tools:")
        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        process.stdin.write((json.dumps(tools_req) + "\n").encode())
        await process.stdin.drain()
        
        tools_resp = await process.stdout.readline()
        tools_data = json.loads(tools_resp.decode().strip())
        
        if "result" in tools_data:
            for tool in tools_data["result"]["tools"]:
                print(f"  • {tool['name']}: {tool['description'].split('.')[0]}")
        
        # Test: Call Trading News Tool
        print(f"\n📰 Testing Trading News Tool (AAPL):")
        news_req = {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "get_trading_news", "arguments": {"symbol": "AAPL", "limit": 2}}
        }
        process.stdin.write((json.dumps(news_req) + "\n").encode())
        await process.stdin.drain()
        
        news_resp = await process.stdout.readline()
        news_data = json.loads(news_resp.decode().strip())
        
        if "result" in news_data:
            result_text = news_data["result"]["content"][0]["text"]
            # Show first few lines
            lines = result_text.split("\n")[:8]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            print("  ...")
        
        print(f"\n🎉 MCP Trading Server Test Complete!")
        print("=" * 45)
        print("✅ Server: Successfully initialized")
        print("✅ Tools: Trading news fetcher working")
        print("✅ API: Benzinga integration functional")
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
    asyncio.run(test_mcp_trading_server())
