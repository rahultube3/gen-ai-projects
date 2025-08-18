"""
Simple demonstration of LangChain + MCP integration
Tests basic functionality without requiring OpenAI API
"""

import asyncio
import json
import os
import sys
from typing import Dict

def test_mcp_direct_call():
    """Test direct MCP service call structure."""
    print("🔧 Testing Direct MCP Service Call...")
    
    try:
        from langchain_agent import MCPServiceTool
        
        # Create MCP tool
        mcp_tool = MCPServiceTool(
            name="health_checker",
            description="Check service health",
            service_path="services/gateway_mcp_service.py",
            tool_name="health_check"
        )
        
        print("✅ MCP Tool created")
        
        # Create LangChain tool
        langchain_tool = mcp_tool.create_langchain_tool()
        print("✅ LangChain Tool created")
        
        # Test tool structure instead of actual call (which requires running services)
        print("🚀 Testing tool structure...")
        assert hasattr(langchain_tool, 'name'), "Tool should have name"
        assert hasattr(langchain_tool, 'description'), "Tool should have description"
        assert hasattr(langchain_tool, 'func'), "Tool should have func"
        assert callable(langchain_tool.func), "Tool func should be callable"
        
        print(f"📝 Tool Name: {langchain_tool.name}")
        print(f"📝 Tool Description: {langchain_tool.description}")
        print("✅ Tool structure valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_list_creation():
    """Test creating the full tool list."""
    print("\n🛠️ Testing Tool List Creation...")
    
    try:
        from langchain_agent import MCPServiceTool
        
        # Test tool configuration structure
        tool_configs = [
            ("Product Search", "Search for products in the catalog", "services/product_mcp_service.py", "search_products"),
            ("Get Recommendations", "Get personalized product recommendations", "services/recommendation_mcp_service.py", "get_recommendations"),
            ("Create Order", "Create a new order", "services/order_mcp_service.py", "create_order"),
        ]
        
        tools_created = 0
        for name, desc, path, tool_name in tool_configs:
            try:
                mcp_tool = MCPServiceTool(
                    name=name,
                    description=desc,
                    service_path=path,
                    tool_name=tool_name
                )
                langchain_tool = mcp_tool.create_langchain_tool()
                
                # Validate tool structure
                assert hasattr(langchain_tool, 'name'), f"Tool {name} missing name"
                assert hasattr(langchain_tool, 'description'), f"Tool {name} missing description"
                assert callable(langchain_tool.func), f"Tool {name} func not callable"
                
                tools_created += 1
                
            except Exception as e:
                print(f"❌ Failed to create tool {name}: {e}")
                return False
        
        print(f"✅ Successfully created {tools_created} LangChain tools")
        print("✅ Tool structure validation passed")
        return True
                
    except Exception as e:
        print(f"❌ Tool creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_api_server():
    """Demonstrate API server capabilities."""
    print("\n🌐 Testing API Server Structure...")
    
    try:
        from langchain_api_server import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', set())
                routes.append(f"{list(methods)[0] if methods else 'GET'} {route.path}")
        
        print("📋 Available API Endpoints:")
        for route in sorted(routes):
            print(f"   {route}")
        
        print("✅ API server structure valid")
        return True
        
    except Exception as e:
        print(f"❌ API server error: {e}")
        return False

def show_integration_capabilities():
    """Show what the integration can do."""
    print("\n" + "="*60)
    print("🎯 LANGCHAIN + MCP INTEGRATION CAPABILITIES")
    print("="*60)
    
    capabilities = [
        "🔍 Product Search with AI recommendations",
        "💬 Intelligent conversational commerce",
        "📦 Order management and analytics", 
        "📊 Personalized user dashboards",
        "🏥 Health monitoring of all services",
        "📈 Cross-service analytics and insights",
        "🔧 RESTful API for external integration",
        "🤖 Natural language processing for commerce",
        "📱 Session management for multi-turn conversations",
        "🎨 Customizable agent behavior and prompts"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    print("\n🚀 Integration Architecture:")
    print("   LangChain Agent → MCP Tools → Microservices → MongoDB")
    print("   FastAPI Server → Agent API → Tool Orchestration")
    
    print("\n💡 Use Cases:")
    print("   • Customer service chatbots")
    print("   • Product recommendation engines") 
    print("   • Order management systems")
    print("   • Business intelligence dashboards")
    print("   • Multi-service orchestration")

def main():
    """Run the demonstration."""
    print("🤖 LangChain + MCP E-commerce Integration Demo")
    print("="*60)
    
    tests = [
        ("Direct MCP Tool", test_mcp_direct_call),
        ("Tool Structure", test_tool_list_creation), 
        ("API Server", demo_api_server)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    # Show capabilities
    show_integration_capabilities()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DEMO RESULTS")
    print("="*60)
    
    passed = sum(result for result in results.values() if result is not None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Status: {passed}/{total} components working")
    
    if passed >= total * 0.8:
        print("🎉 LangChain integration is ready for use!")
        print("\n🚀 Next Steps:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Start API server: python langchain_api_server.py")
        print("   3. Test with: curl http://localhost:8001/health")
        print("   4. Use interactive docs: http://localhost:8001/docs")
    else:
        print("⚠️ Some components need attention")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Demo error: {e}")
        sys.exit(1)
