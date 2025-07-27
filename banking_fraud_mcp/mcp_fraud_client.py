#!/usr/bin/env python3
"""
Banking Fraud Detection MCP Client
A client to interact with the fraud detection MCP server using native MCP libraries.
"""

import asyncio
import sys
import json
import logging
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logging.basicConfig(level=logging.INFO)

class FraudDetectionMCPClient:
    """MCP client for fraud detection operations."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python3", "fraud_server.py"],
            cwd="/Users/rahultomar/rahul-dev/gen-ai-projects/banking_fraud_mcp"
        )
    
    async def check_fraud(self, txn_id: str) -> dict:
        """Check a transaction for fraud using the MCP server."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the fraud detection tool
                result = await session.call_tool("check_fraud", {"txn_id": txn_id})
                
                if result.content:
                    return json.loads(result.content[0].text)
                return {"error": "No result returned", "txn_id": txn_id}

async def run_demo_queries():
    """Run some demo queries to test the MCP fraud detection server."""
    logging.info("🏦 MCP Banking Fraud Detection Demo")
    logging.info("=" * 40)

    client = FraudDetectionMCPClient()

    # Demo queries with transaction IDs
    demo_transactions = [
        ("txn001", "High-risk: Alice, $4000 in New York"),
        ("txn002", "Low-risk: Bob, $150 in HomeCity"), 
        ("txn003", "Very high-risk: Carol, $5000 in Las Vegas"),
        ("txn004", "Low-risk: Alice, $25 in HomeCity"),
        ("nonexistent_txn", "Non-existent transaction test"),
    ]

    for i, (txn_id, description) in enumerate(demo_transactions, 1):
        logging.info(f"\n--- Demo Query {i} ---")
        logging.info(f"Testing: {description}")
        logging.info(f"Transaction ID: {txn_id}")
        
        try:
            result = await client.check_fraud(txn_id)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"📊 Fraud Analysis Results:")
                print(f"   Transaction ID: {result.get('txn_id')}")
                print(f"   Customer ID: {result.get('customer_id')}")
                print(f"   Fraud Score: {result.get('fraud_score')}")
                print(f"   Risk Level: {result.get('risk_level')}")
                print(f"   Reasoning: {result.get('reasoning')}")
                
                # Risk level emoji
                risk_emoji = "🚨" if result.get('risk_level') == 'High' else "✅"
                print(f"   {risk_emoji} Overall Assessment: {result.get('risk_level')} Risk")
                
        except Exception as e:
            logging.error(f"Error: {e}")
        
        # Small delay between queries
        await asyncio.sleep(1)

    logging.info("\n🎉 Demo completed successfully!")

async def run_interactive_chat():
    """Run an interactive fraud detection chat."""
    logging.info("🏦 MCP Banking Fraud Interactive Chat")
    logging.info("=" * 40)

    client = FraudDetectionMCPClient()

    logging.info("\n===== Interactive MCP Fraud Detection Chat =====")
    logging.info("Available commands:")
    logging.info("• 'exit' or 'quit' - End the conversation")
    logging.info("• 'demo' - Run demo queries")
    logging.info("• 'help' - Show fraud detection capabilities")
    logging.info("\nExample usage:")
    logging.info("• Just enter a transaction ID (e.g., 'txn001')")
    logging.info("• Ask questions like 'check txn001'")
    logging.info("=" * 49)

    # Main chat loop
    while True:
        # Get user input
        user_input = input("\n🏦 Enter transaction ID or command: ").strip()

        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            logging.info("👋 Ending fraud detection session...")
            break

        # Check for demo command
        if user_input.lower() == "demo":
            logging.info("\n🎬 Running fraud detection demo...")
            await run_demo_queries()
            continue

        # Check for help command
        if user_input.lower() == "help":
            logging.info("\n📚 MCP Banking Fraud Detection Capabilities:")
            logging.info("🛠️  Available Tool:")
            logging.info("  • check_fraud(txn_id) - Analyze transaction for fraud")
            logging.info("\n📊 Fraud Detection Features:")
            logging.info("  • Customer risk profile analysis")
            logging.info("  • Transaction amount risk scoring")
            logging.info("  • Location-based risk assessment")
            logging.info("  • Comprehensive fraud scoring (0.0 - 1.0)")
            logging.info("\n🔍 Risk Scoring Logic:")
            logging.info("  • Base customer risk score")
            logging.info("  • +0.3 for high amounts (>$3000)")
            logging.info("  • +0.2 for unfamiliar locations")
            logging.info("  • >0.5 = High Risk, ≤0.5 = Low Risk")
            logging.info("\n💡 Test Transaction IDs:")
            logging.info("  • txn001 - Alice: $4000 in New York (High Risk)")
            logging.info("  • txn002 - Bob: $150 in HomeCity (Low Risk)")
            logging.info("  • txn003 - Carol: $5000 in Las Vegas (Very High Risk)")
            logging.info("  • txn004 - Alice: $25 in HomeCity (Low Risk)")
            logging.info("  • Any other ID to test error handling")
            continue

        # Extract transaction ID from input
        txn_id = user_input
        
        # Handle common phrases
        if user_input.lower().startswith("check "):
            txn_id = user_input[6:].strip()
        elif user_input.lower().startswith("analyze "):
            txn_id = user_input[8:].strip()

        if not txn_id:
            print("❌ Please provide a transaction ID")
            continue

        print(f"🔍 Analyzing transaction: {txn_id}")

        try:
            result = await client.check_fraud(txn_id)
            
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n📊 Fraud Analysis Results:")
                print(f"┌─────────────────────────────────────┐")
                print(f"│ Transaction ID: {result.get('txn_id', 'N/A'):<19} │")
                print(f"│ Customer ID:    {result.get('customer_id', 'N/A'):<19} │")
                print(f"│ Fraud Score:    {result.get('fraud_score', 'N/A'):<19} │")
                print(f"│ Risk Level:     {result.get('risk_level', 'N/A'):<19} │")
                print(f"└─────────────────────────────────────┘")
                print(f"💡 Reasoning: {result.get('reasoning', 'N/A')}")
                
                # Risk assessment
                risk_level = result.get('risk_level', 'Unknown')
                if risk_level == 'High':
                    print(f"🚨 HIGH RISK TRANSACTION - Requires immediate review!")
                elif risk_level == 'Low':
                    print(f"✅ Low risk transaction - Appears normal")
                else:
                    print(f"❓ Unknown risk level")

        except Exception as e:
            logging.error(f"\n❌ Error analyzing transaction: {e}")

async def main():
    """Main function to choose between demo and interactive mode."""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await run_demo_queries()
    else:
        await run_interactive_chat()

if __name__ == "__main__":
    asyncio.run(main())
