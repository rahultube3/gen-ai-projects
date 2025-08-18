#!/usr/bin/env python3
"""
Test script for E-commerce RAG Assistant API
Tests both FastAPI endpoints and basic functionality.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# API base URL
API_BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Test an API endpoint."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "response_time": response.elapsed.total_seconds()
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "response_time": 0
        }

def run_api_tests():
    """Run comprehensive API tests."""
    print("🚀 E-commerce RAG Assistant API Test Suite")
    print("=" * 60)
    
    # Wait for server to be ready
    print("⏳ Waiting for API server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ API server is ready!")
                break
        except:
            pass
        
        if i == max_retries - 1:
            print("❌ API server failed to start within 60 seconds")
            return
        
        time.sleep(2)
        print(f"   Retry {i+1}/{max_retries}...")
    
    # Test cases
    test_cases = [
        {
            "name": "Root Endpoint",
            "endpoint": "/",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Health Check",
            "endpoint": "/health",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Chat - Product Search",
            "endpoint": "/chat",
            "method": "POST",
            "data": {
                "message": "What smartphones do you have?",
                "session_id": "test-session-1"
            },
            "expected_status": 200
        },
        {
            "name": "Chat - Product Recommendation",
            "endpoint": "/chat",
            "method": "POST",
            "data": {
                "message": "I need a laptop for programming work under $1500",
                "session_id": "test-session-1"
            },
            "expected_status": 200
        },
        {
            "name": "Product Recommendations",
            "endpoint": "/products/recommendations",
            "method": "POST",
            "data": {
                "query": "smartphone with good camera",
                "limit": 3
            },
            "expected_status": 200
        },
        {
            "name": "Product Search",
            "endpoint": "/products/search",
            "method": "POST",
            "data": {
                "query": "Apple products",
                "category": "electronics",
                "max_price": 2000,
                "limit": 5
            },
            "expected_status": 200
        },
        {
            "name": "Product Categories",
            "endpoint": "/products/categories",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "System Statistics",
            "endpoint": "/stats",
            "method": "GET",
            "expected_status": 200
        }
    ]
    
    # Run tests
    results = []
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        result = test_api_endpoint(
            test_case["endpoint"],
            test_case.get("method", "GET"),
            test_case.get("data")
        )
        
        # Check result
        success = result["success"] and result["status_code"] == test_case.get("expected_status", 200)
        
        if success:
            print(f"   ✅ PASSED - Status: {result['status_code']}, Time: {result['response_time']:.2f}s")
        else:
            print(f"   ❌ FAILED - Status: {result['status_code']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        # Show sample response for chat endpoints
        if test_case["endpoint"] == "/chat" and success:
            response_text = result["data"].get("response", "No response")[:150]
            print(f"   📝 Response: {response_text}...")
        
        results.append({
            "test": test_case["name"],
            "success": success,
            "result": result
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"🎯 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_api_tests()
    exit(0 if success else 1)
