#!/usr/bin/env python3
"""
Simple MCP Fraud Detection Client
A simplified client for quick fraud detection testing.
"""

import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def check_fraud_simple(txn_id: str):
    """Simple function to check fraud for a transaction."""
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python3", "banking_fraud_mcp/fraud_server.py"],
        cwd="/Users/rahultomar/rahul-dev/gen-ai-projects"
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Call the fraud detection tool
            result = await session.call_tool("check_fraud", {"txn_id": txn_id})
            
            if result.content:
                return json.loads(result.content[0].text)
            return {"error": "No result returned"}


async def main():
    """Main function for simple testing."""
    print("🏦 Simple Fraud Detection Test")
    print("-" * 30)
    
    # Test with the known transaction
    txn_id = "txn001"
    print(f"Checking transaction: {txn_id}")
    
    result = await check_fraud_simple(txn_id)
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ Fraud Score: {result.get('fraud_score')} ({result.get('risk_level')} Risk)")
        print(f"💡 {result.get('reasoning')}")


if __name__ == "__main__":
    asyncio.run(main())
