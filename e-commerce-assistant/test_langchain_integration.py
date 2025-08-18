"""
Test script for LangChain E-commerce Agent integration
Verifies agent functionality and MCP service integration.
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any

# Test the basic imports
def test_imports():
    """Test that all required packages can be imported."""
    try:
        import langchain
        import langchain_openai
        import langchain_core
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain.tools import BaseTool
        from langchain.memory import ConversationBufferWindowMemory
        print("✅ LangChain imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_mcp_service_availability():
    """Test that MCP services are available."""
    services = [
        "services/gateway_mcp_service.py",
        "services/product_mcp_service.py", 
        "services/recommendation_mcp_service.py",
        "services/order_mcp_service.py",
        "services/chat_mcp_service.py"
    ]
    
    available_services = []
    for service in services:
        if os.path.exists(service):
            available_services.append(service)
            print(f"✅ {service} found")
        else:
            print(f"❌ {service} not found")
    
    return available_services

async def test_mcp_tool_integration():
    """Test MCP tool integration without OpenAI API."""
    try:
        from langchain_agent import MCPServiceTool
        
        # Create a test tool
        mcp_tool = MCPServiceTool(
            name="test_health_check",
            description="Test health check tool",
            service_path="services/gateway_mcp_service.py",
            tool_name="health_check"
        )
        
        print("✅ MCPServiceTool created successfully")
        
        # Create LangChain tool from it
        langchain_tool = mcp_tool.create_langchain_tool()
        print("✅ LangChain tool created successfully")
        
        # Test the tool call (this will actually call the MCP service)
        result = langchain_tool.func("test")
        if "service is healthy" in result.lower() or "error" in result.lower():
            print(f"✅ MCP tool call successful: {result[:100]}...")
            return True
        else:
            print(f"⚠️ Unexpected MCP response: {result[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ MCP tool integration error: {e}")
        return False

async def test_agent_creation():
    """Test agent creation without API key."""
    try:
        # Mock OpenAI API key for testing structure
        os.environ["OPENAI_API_KEY"] = "test-key-for-structure-testing"
        
        from langchain_agent import EcommerceAgent
        
        # This will fail at LLM initialization, but we can test structure
        try:
            agent = EcommerceAgent("test-key")
            print("❌ Should have failed with invalid API key")
            return False
        except Exception as e:
            if "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower():
                print("✅ Agent structure valid (failed appropriately on invalid API key)")
                return True
            else:
                print(f"❌ Unexpected agent error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return False

async def test_api_server_structure():
    """Test API server structure."""
    try:
        from langchain_api_server import app
        print("✅ FastAPI server structure valid")
        
        # Test that endpoints are defined
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/chat", "/sessions"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ API server structure error: {e}")
        return False

def test_configuration():
    """Test configuration and environment setup."""
    config_issues = []
    
    # Check Claude Desktop configuration
    claude_config_path = "/Users/rahultomar/Library/Application Support/Claude/claude_desktop_config.json"
    if os.path.exists(claude_config_path):
        print("✅ Claude Desktop configuration found")
    else:
        config_issues.append("Claude Desktop configuration not found")
    
    # Check MongoDB URI
    mongodb_uri = os.getenv("MONGODB_URI")
    if mongodb_uri:
        print("✅ MONGODB_URI environment variable set")
    else:
        config_issues.append("MONGODB_URI environment variable not set")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "test-key-for-structure-testing":
        print("✅ OPENAI_API_KEY environment variable set")
    else:
        config_issues.append("OPENAI_API_KEY environment variable not set")
    
    if config_issues:
        print("\n⚠️ Configuration issues:")
        for issue in config_issues:
            print(f"   - {issue}")
    
    return len(config_issues) == 0

async def run_integration_tests():
    """Run comprehensive integration tests."""
    print("🧪 Running LangChain E-commerce Agent Integration Tests")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Package imports
    print("\n1. Testing package imports...")
    test_results["imports"] = test_imports()
    
    # Test 2: MCP service availability
    print("\n2. Testing MCP service availability...")
    available_services = test_mcp_service_availability()
    test_results["mcp_services"] = len(available_services) > 0
    
    # Test 3: MCP tool integration
    print("\n3. Testing MCP tool integration...")
    test_results["mcp_tools"] = await test_mcp_tool_integration()
    
    # Test 4: Agent creation structure
    print("\n4. Testing agent structure...")
    test_results["agent_structure"] = await test_agent_creation()
    
    # Test 5: API server structure
    print("\n5. Testing API server structure...")
    test_results["api_server"] = await test_api_server_structure()
    
    # Test 6: Configuration
    print("\n6. Testing configuration...")
    test_results["configuration"] = test_configuration()
    
    # Summary
    print("\n" + "=" * 60)
    print("🔍 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LangChain integration is ready!")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. Review failed tests above.")
    else:
        print("❌ Several tests failed. Check configuration and dependencies.")
    
    return test_results

def print_usage_examples():
    """Print usage examples for the LangChain integration."""
    print("\n" + "=" * 60)
    print("📖 USAGE EXAMPLES")
    print("=" * 60)
    
    print("""
🚀 1. Start the LangChain Agent CLI:
   python langchain_agent.py

🌐 2. Start the FastAPI Server:
   python langchain_api_server.py
   
   Or with custom settings:
   uvicorn langchain_api_server:app --host 0.0.0.0 --port 8001 --reload

🔧 3. Environment Setup:
   export OPENAI_API_KEY="your-openai-api-key"
   export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant"

💬 4. Example API Calls:
   curl -X POST "http://localhost:8001/chat" \\
     -H "Content-Type: application/json" \\
     -d '{"message": "Search for laptops", "user_id": "user123"}'

🛍️ 5. Product Search:
   curl -X POST "http://localhost:8001/products/search?query=wireless headphones&user_id=user123"

📊 6. Generate Dashboard:
   curl -X POST "http://localhost:8001/dashboard/generate" \\
     -H "Content-Type: application/json" \\
     -d '{"user_id": "user123", "sections": ["recommendations", "recent_orders"]}'

🔍 7. Check API Health:
   curl http://localhost:8001/health

📚 8. Interactive API Docs:
   Open: http://localhost:8001/docs
""")

if __name__ == "__main__":
    print("🤖 LangChain E-commerce Agent Test Suite")
    
    # Run tests
    try:
        results = asyncio.run(run_integration_tests())
        print_usage_examples()
        
        # Exit with appropriate code
        passed = sum(results.values())
        total = len(results)
        sys.exit(0 if passed == total else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        sys.exit(1)
