#!/usr/bin/env python3
"""
Simple test script to validate MCP services can start and respond to basic requests.
"""

import asyncio
import json
import subprocess
import sys
import os
import time

async def test_service(service_path, service_name):
    """Test if a service can start and respond to basic MCP requests."""
    print(f"\n🧪 Testing {service_name}...")
    
    try:
        # Start the service
        process = subprocess.Popen(
            ["uv", "run", "python", service_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(service_path)
        )
        
        # Wait a moment for the service to initialize
        await asyncio.sleep(1)
        
        # Check if process is still running
        if process.poll() is not None:
            stderr_output = process.stderr.read() if process.stderr else "No error output"
            print(f"❌ {service_name} failed to start")
            print(f"Error: {stderr_output}")
            return False
        
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0.0"}
            }
        }
        
        # Send the request
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Wait for response
        await asyncio.sleep(2)
        
        # Try to read response
        try:
            # Set a timeout for reading
            import select
            if select.select([process.stdout], [], [], 1)[0]:
                response = process.stdout.readline()
                if response:
                    response_data = json.loads(response.strip())
                    if "result" in response_data:
                        print(f"✅ {service_name} is working correctly")
                        success = True
                    else:
                        print(f"⚠️  {service_name} responded but with unexpected format")
                        success = False
                else:
                    print(f"⚠️  {service_name} didn't respond to initialization")
                    success = False
            else:
                print(f"⚠️  {service_name} timed out on response")
                success = False
        except Exception as e:
            print(f"⚠️  {service_name} error reading response: {e}")
            success = False
        
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing {service_name}: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 MCP Services Validation Test")
    print("=" * 40)
    
    # Define services to test
    services = [
        ("services/base_mcp_service.py", "Base MCP Service"),
        ("services/product_mcp_service.py", "Product Service"),
        ("services/recommendation_mcp_service.py", "Recommendation Service"),
        ("services/order_mcp_service.py", "Order Service"),
        ("services/chat_mcp_service.py", "Chat Service"),
        ("services/gateway_mcp_service.py", "Gateway Service")
    ]
    
    results = {}
    
    for service_path, service_name in services:
        if os.path.exists(service_path):
            results[service_name] = await test_service(service_path, service_name)
        else:
            print(f"❌ {service_name} file not found: {service_path}")
            results[service_name] = False
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 40)
    
    working_services = []
    failed_services = []
    
    for service_name, success in results.items():
        if success:
            working_services.append(service_name)
            print(f"✅ {service_name}")
        else:
            failed_services.append(service_name)
            print(f"❌ {service_name}")
    
    print(f"\n📈 {len(working_services)}/{len(results)} services are working")
    
    if failed_services:
        print(f"\n🔧 Services needing attention:")
        for service in failed_services:
            print(f"   • {service}")
    
    return len(failed_services) == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
