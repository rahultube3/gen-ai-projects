#!/usr/bin/env python3
"""
Test script for the MCP weather server.
This script tests the weather functions, resources, and prompts.
"""

import asyncio
import sys
sys.path.append('/Users/rahultomar/rahul-dev/gen-ai-projects/mcp-weather-server')

from weather import get_alerts, get_forecast, get_weather_report, get_alert_summary, prompt_weather_alerts, prompt_weather_safety

async def test_weather_functionality():
    """Test all weather functionality: tools, resources, and prompts."""
    print("Testing Complete MCP Weather Server")
    print("=" * 70)
    
    # Test Tools (async functions)
    print("\n🛠️  TESTING TOOLS (Live Data)")
    print("-" * 40)
    
    print("\n1. Testing get_alerts function with 'CA':")
    try:
        alerts_result = await get_alerts("CA")
        print(f"✅ Result: {alerts_result[:150]}...")
    except Exception as e:
        print(f"❌ Error in get_alerts: {e}")
    
    print("\n2. Testing get_forecast function with SF coordinates:")
    try:
        forecast_result = await get_forecast(37.7749, -122.4194)
        print(f"✅ Result: {forecast_result[:150]}...")
    except Exception as e:
        print(f"❌ Error in get_forecast: {e}")
    
    # Test Resources (sync functions)
    print("\n\n📚 TESTING RESOURCES (Cached Data)")
    print("-" * 40)
    
    print("\n3. Testing weather report resource for San Francisco:")
    try:
        report_result = get_weather_report("san-francisco")
        print(f"✅ Result: {report_result[:150]}...")
    except Exception as e:
        print(f"❌ Error in get_weather_report: {e}")
    
    print("\n4. Testing alert summary resource for California:")
    try:
        summary_result = get_alert_summary("ca")
        print(f"✅ Result: {summary_result[:150]}...")
    except Exception as e:
        print(f"❌ Error in get_alert_summary: {e}")
    
    # Test Prompts (sync functions)
    print("\n\n💭 TESTING PROMPTS (AI Assistant Instructions)")
    print("-" * 40)
    
    print("\n5. Testing weather alert analysis prompt:")
    try:
        alert_prompt = prompt_weather_alerts()
        print(f"✅ Result: {alert_prompt[:150]}...")
    except Exception as e:
        print(f"❌ Error in prompt_weather_alerts: {e}")
    
    print("\n6. Testing weather safety guide prompt:")
    try:
        safety_prompt = prompt_weather_safety()
        print(f"✅ Result: {safety_prompt[:150]}...")
    except Exception as e:
        print(f"❌ Error in prompt_weather_safety: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 ALL TESTS COMPLETED!")
    print("\n📋 MCP Feature Summary:")
    print("✅ Tools: 2 (get_alerts, get_forecast)")
    print("✅ Resources: 2 (weather reports, alert summaries)")  
    print("✅ Prompts: 2 (analysis, safety)")
    
    print("\n🔗 Available MCP Resources:")
    print("• weather://reports/san-francisco")
    print("• weather://reports/new-york")
    print("• weather://reports/chicago")
    print("• weather://alerts/ca, ny, fl, tx, il")
    
    print("\n🤖 Available MCP Prompts:")
    print("• weather-alert-analysis")
    print("• weather-safety-guide")

if __name__ == "__main__":
    asyncio.run(test_weather_functionality())
