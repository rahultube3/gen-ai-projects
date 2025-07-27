#!/usr/bin/env python3
"""
Enhanced Banking Fraud Detection MCP Client
Showcases all advanced features of the comprehensive fraud detection server.
"""

import asyncio
import json
import logging
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logging.basicConfig(level=logging.INFO)

class EnhancedFraudDetectionClient:
    """Enhanced MCP client for comprehensive fraud detection operations."""
    
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python3", "fraud_server.py"],
            cwd="/Users/rahultomar/rahul-dev/gen-ai-projects/banking_fraud_mcp"
        )
    
    async def run_comprehensive_demo(self):
        """Run a comprehensive demo showcasing all server features."""
        print("🏦 COMPREHENSIVE BANKING FRAUD DETECTION DEMO")
        print("=" * 55)
        
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 1. Show available capabilities
                await self._show_server_capabilities(session)
                
                # 2. Demonstrate enhanced fraud detection
                await self._demo_enhanced_fraud_detection(session)
                
                # 3. Show system statistics
                await self._demo_system_statistics(session)
                
                # 4. Demonstrate customer risk analysis
                await self._demo_customer_risk_analysis(session)
                
                # 5. Showcase resources
                await self._demo_resources(session)
                
                # 6. Show prompts
                await self._demo_prompts(session)
                
                print("\n🎉 COMPREHENSIVE DEMO COMPLETED!")
    
    async def _show_server_capabilities(self, session):
        """Display all server capabilities."""
        print("\n📋 SERVER CAPABILITIES")
        print("-" * 30)
        
        # List tools
        tools_result = await session.list_tools()
        print("🛠️  Available Tools:")
        for tool in tools_result.tools:
            print(f"   • {tool.name}")
        
        # List resources
        resources_result = await session.list_resources()
        print("\n📚 Available Resources:")
        for resource in resources_result.resources:
            print(f"   • {resource.uri}")
        
        # List prompts
        prompts_result = await session.list_prompts()
        print("\n💭 Available Prompts:")
        for prompt in prompts_result.prompts:
            print(f"   • {prompt.name}")
    
    async def _demo_enhanced_fraud_detection(self, session):
        """Demonstrate enhanced fraud detection with multiple scenarios."""
        print("\n🔍 ENHANCED FRAUD DETECTION")
        print("-" * 35)
        
        test_transactions = [
            ("txn001", "High Risk: Alice, $4000, New York"),
            ("txn002", "Low Risk: Bob, $150, HomeCity"),
            ("txn003", "Very High Risk: Carol, $5000, Las Vegas")
        ]
        
        for txn_id, description in test_transactions:
            print(f"\n📊 Analyzing {txn_id}: {description}")
            
            result = await session.call_tool("check_fraud", {"txn_id": txn_id})
            fraud_data = json.loads(result.content[0].text)
            
            print(f"   🎯 Fraud Score: {fraud_data.get('fraud_score')}")
            print(f"   ⚠️  Risk Level: {fraud_data.get('risk_level')}")
            print(f"   🔍 Risk Factors:")
            for factor in fraud_data.get('risk_factors', []):
                print(f"      • {factor}")
            print(f"   💡 Top Recommendation: {fraud_data.get('recommendations', ['None'])[0]}")
    
    async def _demo_system_statistics(self, session):
        """Show comprehensive system statistics."""
        print("\n📊 SYSTEM STATISTICS & HEALTH")
        print("-" * 35)
        
        result = await session.call_tool("get_fraud_statistics", {})
        stats = json.loads(result.content[0].text)
        
        print(f"   🟢 System Status: {stats.get('system_status', 'Unknown').upper()}")
        print(f"   📈 Total Transactions: {stats.get('total_transactions', 0)}")
        print(f"   👥 Total Customers: {stats.get('total_customers', 0)}")
        
        metrics = stats.get('fraud_detection_metrics', {})
        print(f"   🎯 Detection Accuracy: {metrics.get('detection_accuracy', 'N/A')}")
        print(f"   ⚡ Avg Processing Time: {metrics.get('processing_time_avg_ms', 'N/A')}ms")
        print(f"   ❌ False Positive Rate: {metrics.get('false_positive_rate', 'N/A')}")
        
        patterns = stats.get('recent_patterns', {})
        print(f"   🌍 Suspicious Locations: {', '.join(patterns.get('suspicious_locations', []))}")
        print(f"   💰 High Risk Amounts: {patterns.get('high_risk_amounts', 'N/A')}")
    
    async def _demo_customer_risk_analysis(self, session):
        """Demonstrate comprehensive customer risk analysis."""
        print("\n👤 CUSTOMER RISK ANALYSIS")
        print("-" * 30)
        
        test_customers = [
            ("cust123", "Alice - Medium activity customer"),
            ("cust456", "Bob - Low risk customer"),
            ("cust789", "Carol - High risk customer")
        ]
        
        for customer_id, description in test_customers:
            print(f"\n📋 Analyzing {description}")
            
            result = await session.call_tool("analyze_customer_risk", {"customer_id": customer_id})
            customer_data = json.loads(result.content[0].text)
            
            if "error" not in customer_data:
                print(f"   👤 Name: {customer_data.get('name')}")
                print(f"   🎯 Base Risk Score: {customer_data.get('base_risk_score')}")
                
                history = customer_data.get('transaction_history', {})
                print(f"   📊 Transaction Count: {history.get('total_transactions', 0)}")
                print(f"   💰 Average Amount: ${history.get('average_amount', 0):.2f}")
                print(f"   🌍 Unique Locations: {history.get('unique_locations', 0)}")
                
                assessment = customer_data.get('risk_assessment', {})
                print(f"   ⚠️  Overall Risk: {assessment.get('overall_risk_level', 'Unknown')}")
            else:
                print(f"   ❌ {customer_data.get('error')}")
    
    async def _demo_resources(self, session):
        """Showcase available resources."""
        print("\n📚 FRAUD DETECTION RESOURCES")
        print("-" * 35)
        
        resources = [
            ("fraud://reports/system-status", "System Status Report"),
            ("fraud://reports/risk-patterns", "Risk Patterns Analysis"),
            ("fraud://data/sample-transactions", "Sample Transaction Data")
        ]
        
        for uri, name in resources:
            print(f"\n📄 {name}")
            try:
                result = await session.read_resource(uri)
                content = result.contents[0].text
                # Show first few lines
                lines = content.split('\\n')[:3]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                print(f"   ... (resource contains {len(content.split())} words)")
            except Exception as e:
                print(f"   ❌ Error loading resource: {e}")
    
    async def _demo_prompts(self, session):
        """Demonstrate available prompts."""
        print("\n💭 FRAUD ANALYSIS PROMPTS")
        print("-" * 30)
        
        prompts = [
            ("fraud_analysis_prompt", {"transaction_data": "txn001: $4000 transaction in New York"}),
            ("security_advisory_prompt", {"risk_level": "high"})
        ]
        
        for prompt_name, args in prompts:
            print(f"\n🎯 {prompt_name.replace('_', ' ').title()}")
            try:
                result = await session.get_prompt(prompt_name, args)
                content = result.content[0].text
                # Show first few lines
                lines = content.split('\\n')[:4]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                print(f"   ... (prompt contains {len(content.split())} words)")
            except Exception as e:
                print(f"   ❌ Error with prompt: {e}")

async def run_interactive_enhanced_mode():
    """Run enhanced interactive mode with all features."""
    client = EnhancedFraudDetectionClient()
    
    print("🏦 ENHANCED FRAUD DETECTION INTERACTIVE MODE")
    print("=" * 50)
    print("Available commands:")
    print("• 'demo' - Run comprehensive demo")
    print("• 'fraud [txn_id]' - Analyze transaction fraud")
    print("• 'customer [customer_id]' - Analyze customer risk")
    print("• 'stats' - Show system statistics")
    print("• 'resources' - List available resources")
    print("• 'help' - Show this help")
    print("• 'exit' - Exit the program")
    print("=" * 50)
    
    async with stdio_client(client.server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            while True:
                user_input = input("\n🏦 Command: ").strip().lower()
                
                if user_input in ["exit", "quit"]:
                    print("👋 Goodbye!")
                    break
                
                elif user_input == "demo":
                    await client.run_comprehensive_demo()
                
                elif user_input.startswith("fraud "):
                    txn_id = user_input[6:].strip()
                    await client._analyze_single_transaction(session, txn_id)
                
                elif user_input.startswith("customer "):
                    customer_id = user_input[9:].strip()
                    await client._analyze_single_customer(session, customer_id)
                
                elif user_input == "stats":
                    await client._demo_system_statistics(session)
                
                elif user_input == "resources":
                    await client._demo_resources(session)
                
                elif user_input == "help":
                    print("Available commands:")
                    print("• demo, fraud [id], customer [id], stats, resources, help, exit")
                
                else:
                    print("❓ Unknown command. Type 'help' for available commands.")
    
    async def _analyze_single_transaction(self, session, txn_id):
        """Analyze a single transaction."""
        result = await session.call_tool("check_fraud", {"txn_id": txn_id})
        fraud_data = json.loads(result.content[0].text)
        
        if "error" not in fraud_data:
            print(f"🎯 Fraud Score: {fraud_data.get('fraud_score')}")
            print(f"⚠️  Risk Level: {fraud_data.get('risk_level')}")
            print("💡 Recommendations:")
            for rec in fraud_data.get('recommendations', [])[:3]:
                print(f"   • {rec}")
        else:
            print(f"❌ {fraud_data.get('error')}")
    
    async def _analyze_single_customer(self, session, customer_id):
        """Analyze a single customer."""
        result = await session.call_tool("analyze_customer_risk", {"customer_id": customer_id})
        customer_data = json.loads(result.content[0].text)
        
        if "error" not in customer_data:
            print(f"👤 {customer_data.get('name')} (Risk: {customer_data.get('base_risk_score')})")
            history = customer_data.get('transaction_history', {})
            print(f"📊 {history.get('total_transactions', 0)} transactions, avg ${history.get('average_amount', 0):.2f}")
        else:
            print(f"❌ {customer_data.get('error')}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        client = EnhancedFraudDetectionClient()
        asyncio.run(client.run_comprehensive_demo())
    else:
        asyncio.run(run_interactive_enhanced_mode())
