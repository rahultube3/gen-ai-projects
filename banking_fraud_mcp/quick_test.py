#!/usr/bin/env python3
"""
Quick Model Test
Test the retrained model with a few key transactions
"""

import asyncio
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def quick_test():
    """Quick test of key transactions"""
    
    print("🧪 QUICK MODEL TEST")
    print("=" * 30)
    
    # Key test transactions
    test_txns = [
        ("txn001", "MINIMAL - Coffee at HomeCity"),
        ("txn020", "MEDIUM - Late night restaurant"),  
        ("txn040", "HIGH - Casino transaction"),
        ("txn070", "CRITICAL - Offshore transaction"),
    ]
    
    @asynccontextmanager
    async def create_server_session():
        server_params = StdioServerParameters(
            command="uv", 
            args=["run", "python", "fraud_server.py"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async with create_server_session() as session:
        for txn_id, description in test_txns:
            try:
                print(f"\n🔍 Testing {txn_id}: {description}")
                
                result = await session.call_tool("check_fraud", arguments={"txn_id": txn_id})
                
                # Print raw result for debugging
                if result.content:
                    content = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    
                    # Try to extract key info
                    lines = content.split('\n')
                    for line in lines:
                        if any(keyword in line for keyword in ['fraud_score', 'risk_level', 'ml_fraud_probability']):
                            print(f"   {line.strip()}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
