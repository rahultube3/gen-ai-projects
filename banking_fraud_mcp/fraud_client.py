#!/usr/bin/env python3
"""
MCP Fraud Detection Client
A client to interact with the fraud detection MCP server.
"""

import asyncio
import subprocess
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def run_fraud_client():
    """Run the fraud detection client."""
    
    # Define the server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python3", "banking_fraud_mcp/fraud_server.py"],
        cwd="/Users/rahultomar/rahul-dev/gen-ai-projects"
    )
    
    print("🏦 Starting Fraud Detection MCP Client...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✅ Connected to Fraud Detection Server")
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"📊 Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Test the check_fraud tool with different transaction IDs
            test_transactions = ["txn001", "nonexistent_txn"]
            
            for txn_id in test_transactions:
                print(f"\n🔍 Checking transaction: {txn_id}")
                
                try:
                    # Call the check_fraud tool
                    result = await session.call_tool("check_fraud", {"txn_id": txn_id})
                    
                    if result.content:
                        fraud_data = json.loads(result.content[0].text)
                        
                        if "error" in fraud_data:
                            print(f"❌ Error: {fraud_data['error']}")
                        else:
                            print(f"📋 Transaction ID: {fraud_data.get('txn_id')}")
                            print(f"👤 Customer ID: {fraud_data.get('customer_id')}")
                            print(f"⚠️  Fraud Score: {fraud_data.get('fraud_score')}")
                            print(f"🚨 Risk Level: {fraud_data.get('risk_level')}")
                            print(f"💡 Reasoning: {fraud_data.get('reasoning')}")
                    
                except Exception as e:
                    print(f"❌ Error calling tool: {e}")
            
            print("\n✅ Fraud detection testing completed!")


async def test_direct_tool():
    """Test the fraud tool directly without MCP for comparison."""
    print("\n🔧 Testing fraud tool directly...")
    
    try:
        # Import and test the fraud tool directly
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from fraud_tool import check_transaction
        
        result = check_transaction("txn001")
        print("📋 Direct tool result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"❌ Error testing direct tool: {e}")


if __name__ == "__main__":
    print("🚀 Fraud Detection MCP Client")
    print("=" * 40)
    
    # Test direct tool first
    asyncio.run(test_direct_tool())
    
    # Then test via MCP
    asyncio.run(run_fraud_client())
