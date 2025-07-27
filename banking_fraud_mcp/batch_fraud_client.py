#!/usr/bin/env python3
"""
Batch MCP Fraud Detection Client
Process multiple transactions for fraud detection.
"""

import asyncio
import json
from typing import List, Dict
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class FraudDetectionClient:
    """A client class for fraud detection operations."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python3", "banking_fraud_mcp/fraud_server.py"],
            cwd="/Users/rahultomar/rahul-dev/gen-ai-projects"
        )
    
    async def check_single_transaction(self, txn_id: str) -> Dict:
        """Check a single transaction for fraud."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("check_fraud", {"txn_id": txn_id})
                
                if result.content:
                    return json.loads(result.content[0].text)
                return {"error": "No result returned", "txn_id": txn_id}
    
    async def check_multiple_transactions(self, txn_ids: List[str]) -> List[Dict]:
        """Check multiple transactions for fraud."""
        results = []
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                for txn_id in txn_ids:
                    try:
                        result = await session.call_tool("check_fraud", {"txn_id": txn_id})
                        
                        if result.content:
                            fraud_result = json.loads(result.content[0].text)
                        else:
                            fraud_result = {"error": "No result returned", "txn_id": txn_id}
                            
                        results.append(fraud_result)
                        
                    except Exception as e:
                        results.append({"error": str(e), "txn_id": txn_id})
        
        return results
    
    def print_fraud_report(self, results: List[Dict]):
        """Print a formatted fraud detection report."""
        print("\n🏦 FRAUD DETECTION REPORT")
        print("=" * 50)
        
        high_risk_count = 0
        low_risk_count = 0
        error_count = 0
        
        for result in results:
            if "error" in result:
                print(f"❌ {result.get('txn_id', 'Unknown')}: {result['error']}")
                error_count += 1
            else:
                risk_icon = "🚨" if result.get('risk_level') == 'High' else "✅"
                print(f"{risk_icon} {result.get('txn_id')}: Score {result.get('fraud_score')} "
                      f"({result.get('risk_level')} Risk)")
                
                if result.get('risk_level') == 'High':
                    high_risk_count += 1
                else:
                    low_risk_count += 1
        
        print("\n📊 SUMMARY:")
        print(f"  🚨 High Risk: {high_risk_count}")
        print(f"  ✅ Low Risk: {low_risk_count}")
        print(f"  ❌ Errors: {error_count}")
        print(f"  📋 Total: {len(results)}")


async def main():
    """Main function for batch fraud detection."""
    client = FraudDetectionClient()
    
    # Test with multiple transaction IDs
    test_transactions = [
        "txn001",           # Known transaction - high risk
        "nonexistent_txn",  # Non-existent transaction
        "txn002",           # Another non-existent transaction
    ]
    
    print("🔍 Batch Fraud Detection Testing")
    print(f"Processing {len(test_transactions)} transactions...")
    
    # Check multiple transactions
    results = await client.check_multiple_transactions(test_transactions)
    
    # Print the report
    client.print_fraud_report(results)


if __name__ == "__main__":
    asyncio.run(main())
