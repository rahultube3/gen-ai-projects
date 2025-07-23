#!/usr/bin/env python3
"""
Get Florida weather alerts directly using our MCP server.
"""

import asyncio
import json
import sys

async def get_florida_alerts():
    """Get current weather alerts for Florida."""
    
    print("🌴 Getting Weather Alerts for Florida")
    print("=" * 40)
    
    # Start the server process
    process = await asyncio.create_subprocess_exec(
        "uv", "run", "python", "main.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd="/Users/rahultomar/rahul-dev/gen-ai-projects/mcp-weather-server"
    )
    
    try:
        # Initialize
        init_req = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "florida-alerts", "version": "1.0"}
            }
        }
        
        process.stdin.write((json.dumps(init_req) + "\n").encode())
        await process.stdin.drain()
        
        # Wait for init response
        init_resp = await process.stdout.readline()
        
        # Send initialized notification
        init_notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        process.stdin.write((json.dumps(init_notif) + "\n").encode())
        await process.stdin.drain()
        
        print("✅ Connected to MCP weather server")
        
        # Get Florida alerts
        alert_req = {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "get_alerts", "arguments": {"state": "FL"}}
        }
        process.stdin.write((json.dumps(alert_req) + "\n").encode())
        await process.stdin.drain()
        
        alert_resp = await process.stdout.readline()
        alert_data = json.loads(alert_resp.decode().strip())
        
        if "result" in alert_data and "content" in alert_data["result"]:
            alert_text = alert_data["result"]["content"][0]["text"]
            
            if alert_text.strip():
                print("\n🚨 CURRENT WEATHER ALERTS FOR FLORIDA:")
                print("=" * 50)
                
                # Split alerts by separator
                alerts = alert_text.split("---")
                
                for i, alert in enumerate(alerts, 1):
                    alert = alert.strip()
                    if alert:
                        print(f"\n📢 ALERT #{i}")
                        print("-" * 20)
                        
                        # Parse alert sections
                        lines = alert.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line.startswith("Event:"):
                                print(f"🌪️  {line}")
                            elif line.startswith("Area:"):
                                print(f"📍 {line}")
                            elif line.startswith("Severity:"):
                                severity = line.replace("Severity: ", "")
                                if severity.lower() == "severe":
                                    print(f"⚠️  Severity: {severity} ⚠️")
                                else:
                                    print(f"ℹ️  {line}")
                            elif line.startswith("Description:"):
                                print(f"📝 {line}")
                                break
                
                print(f"\n✅ Retrieved {len([a for a in alerts if a.strip()])} active alerts")
                print("📡 Data source: National Weather Service API")
                
            else:
                print("✅ No active weather alerts for Florida at this time")
        else:
            print("❌ Failed to retrieve alert data")
            if "error" in alert_data:
                print(f"Error: {alert_data['error']}")
        
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")
    finally:
        try:
            process.stdin.close()
            await process.wait()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(get_florida_alerts())
