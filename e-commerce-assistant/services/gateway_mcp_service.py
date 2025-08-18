#!/usr/bin/env python3
"""
Gateway MCP Service
Acts as the main entry point and orchestrator for all other MCP services.
Provides unified API access and coordinates multi-service requests.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base_mcp_service import BaseMCPService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway-service")

class GatewayMCPService(BaseMCPService):
    """Gateway service that orchestrates all other MCP services."""
    
    def __init__(self):
        super().__init__("gateway-service", "1.0.0")
        
        # Service registry
        self.registered_services = {
            "product-service": {
                "name": "Product Service",
                "description": "Product search, details, and catalog management",
                "status": "unknown",
                "tools": ["search_products", "get_product_details", "list_categories", "filter_products"]
            },
            "recommendation-service": {
                "name": "Recommendation Service", 
                "description": "AI-powered product recommendations",
                "status": "unknown",
                "tools": ["get_recommendations", "similar_products", "trending_products", "personalized_recommendations"]
            },
            "order-service": {
                "name": "Order Service",
                "description": "Order management and analytics",
                "status": "unknown", 
                "tools": ["get_order_stats", "recent_orders", "order_analytics", "customer_orders"]
            },
            "chat-service": {
                "name": "Chat Service",
                "description": "Conversational AI and natural language processing",
                "status": "unknown",
                "tools": ["start_conversation", "continue_conversation", "analyze_intent", "generate_response"]
            }
        }
        
        # Request routing and orchestration
        self.active_sessions: Dict[str, Dict] = {}
        self.request_cache: Dict[str, Dict] = {}
        self.service_health: Dict[str, Dict] = {}
    
    def setup_service(self):
        """Service-specific setup for gateway service."""
        self.logger.info("Setting up Gateway Service...")
    
    def register_tools(self):
        """Register gateway service tools."""
        for tool in self.get_available_tools():
            self.tools[tool["name"]] = tool
    
    def register_resources(self):
        """Register gateway service resources."""
        for resource in self.get_service_resources():
            self.resources[resource["uri"]] = resource
    
    def get_available_tools(self) -> List[Dict]:
        """Define gateway service tools."""
        return [
            {
                "name": "unified_search",
                "description": "Unified search across products with intelligent recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "user_id": {"type": "string", "description": "User identifier for personalization"},
                        "include_recommendations": {"type": "boolean", "description": "Include AI recommendations", "default": True},
                        "limit": {"type": "integer", "description": "Maximum results to return", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "smart_chat",
                "description": "Intelligent conversational interface with service integration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "User message"},
                        "user_id": {"type": "string", "description": "User identifier"},
                        "session_id": {"type": "string", "description": "Chat session ID (optional)"},
                        "context": {"type": "object", "description": "Additional context information"}
                    },
                    "required": ["message", "user_id"]
                }
            },
            {
                "name": "complete_order_flow",
                "description": "Complete order management with recommendations and analytics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "action": {
                            "type": "string",
                            "enum": ["view_orders", "order_analytics", "reorder_suggestions"],
                            "description": "Order action to perform"
                        },
                        "order_id": {"type": "string", "description": "Specific order ID (optional)"}
                    },
                    "required": ["user_id", "action"]
                }
            },
            {
                "name": "personalized_dashboard",
                "description": "Generate personalized user dashboard with cross-service data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "sections": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["recommendations", "recent_orders", "trending", "categories"]
                            },
                            "description": "Dashboard sections to include"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "service_health_check",
                "description": "Check health status of all registered services",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "detailed": {"type": "boolean", "description": "Include detailed service information", "default": False}
                    }
                }
            },
            {
                "name": "cross_service_analytics",
                "description": "Generate analytics across multiple services",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "metric_type": {
                            "type": "string",
                            "enum": ["user_journey", "product_performance", "service_usage", "conversion_funnel"],
                            "description": "Type of analytics to generate"
                        },
                        "time_range": {"type": "string", "description": "Time range for analytics (e.g., '7d', '30d')", "default": "7d"},
                        "filters": {"type": "object", "description": "Additional filters for analytics"}
                    },
                    "required": ["metric_type"]
                }
            }
        ]
    
    def get_service_resources(self) -> List[Dict]:
        """Define gateway service resources."""
        return [
            {
                "uri": "gateway://services",
                "name": "Service Registry",
                "description": "Information about all registered MCP services",
                "mimeType": "application/json"
            },
            {
                "uri": "gateway://sessions",
                "name": "Active Sessions",
                "description": "Currently active user sessions",
                "mimeType": "application/json"
            },
            {
                "uri": "gateway://analytics",
                "name": "Cross-Service Analytics",
                "description": "Aggregated analytics from all services",
                "mimeType": "application/json"
            },
            {
                "uri": "gateway://health",
                "name": "System Health",
                "description": "Health status of all services and system components",
                "mimeType": "application/json"
            }
        ]
    
    async def unified_search(self, query: str, user_id: Optional[str] = None, include_recommendations: bool = True, limit: int = 10) -> Dict:
        """Unified search with intelligent recommendations."""
        try:
            request_id = str(uuid.uuid4())
            logger.info(f"Unified search request {request_id}: '{query}' for user {user_id}")
            
            # Start parallel service calls
            tasks = []
            
            # Product search
            tasks.append(self._search_products(query, limit))
            
            # Recommendations if user provided and requested
            if user_id and include_recommendations:
                tasks.append(self._get_user_recommendations(user_id, query, limit // 2))
            
            # Execute parallel calls
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            search_results = results[0] if not isinstance(results[0], Exception) else {"products": []}
            recommendations = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {"recommendations": []}
            
            # Combine and rank results
            combined_results = self._combine_search_results(search_results, recommendations, query)
            
            # Cache results
            self.request_cache[request_id] = {
                "query": query,
                "user_id": user_id,
                "results": combined_results,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Unified search {request_id} completed: {len(combined_results.get('products', []))} results")
            
            return {
                "request_id": request_id,
                "query": query,
                "total_results": len(combined_results.get("products", [])),
                "products": combined_results.get("products", [])[:limit],
                "recommendations": combined_results.get("recommendations", []),
                "search_metadata": {
                    "has_recommendations": len(combined_results.get("recommendations", [])) > 0,
                    "search_time": datetime.now().isoformat(),
                    "personalized": user_id is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in unified search: {e}")
            raise
    
    async def smart_chat(self, message: str, user_id: str, session_id: Optional[str] = None, context: Optional[Dict] = None) -> Dict:
        """Intelligent conversational interface with service integration."""
        try:
            # Get or create session
            if not session_id:
                session_id = str(uuid.uuid4())
                
                # Start new conversation
                chat_result = await self.call_other_service(
                    "chat-service",
                    "start_conversation",
                    {
                        "user_id": user_id,
                        "conversation_type": "general",
                        "initial_message": message
                    }
                )
                
                if chat_result:
                    session_id = chat_result.get("conversation_id", session_id)
            
            # Continue conversation
            chat_response = await self.call_other_service(
                "chat-service",
                "continue_conversation",
                {
                    "conversation_id": session_id,
                    "user_message": message,
                    "context": context
                }
            )
            
            if not chat_response:
                return {"error": "Chat service unavailable"}
            
            # Process actions from chat response
            enhanced_response = await self._process_chat_actions(
                chat_response, user_id, message, context
            )
            
            # Store session
            self.active_sessions[session_id] = {
                "user_id": user_id,
                "last_message": message,
                "last_response": enhanced_response["response"],
                "updated_at": datetime.now().isoformat(),
                "message_count": self.active_sessions.get(session_id, {}).get("message_count", 0) + 1
            }
            
            return {
                "session_id": session_id,
                "response": enhanced_response["response"],
                "intent": chat_response.get("intent"),
                "confidence": chat_response.get("confidence"),
                "actions_performed": enhanced_response.get("actions_performed", []),
                "suggested_actions": enhanced_response.get("suggested_actions", []),
                "context_data": enhanced_response.get("context_data", {})
            }
            
        except Exception as e:
            logger.error(f"Error in smart chat: {e}")
            raise
    
    async def complete_order_flow(self, user_id: str, action: str, order_id: Optional[str] = None) -> Dict:
        """Complete order management with recommendations and analytics."""
        try:
            logger.info(f"Complete order flow: {action} for user {user_id}")
            
            if action == "view_orders":
                # Get recent orders
                orders_result = await self.call_other_service(
                    "order-service",
                    "recent_orders",
                    {"user_id": user_id, "limit": 10}
                )
                
                # Get order statistics
                stats_result = await self.call_other_service(
                    "order-service",
                    "get_order_stats",
                    {"user_id": user_id}
                )
                
                return {
                    "action": "view_orders",
                    "orders": orders_result.get("orders", []) if orders_result else [],
                    "statistics": stats_result if stats_result else {},
                    "user_id": user_id
                }
            
            elif action == "order_analytics":
                # Get detailed analytics
                analytics_result = await self.call_other_service(
                    "order-service",
                    "order_analytics",
                    {"user_id": user_id, "analysis_type": "comprehensive"}
                )
                
                return {
                    "action": "order_analytics",
                    "analytics": analytics_result if analytics_result else {},
                    "user_id": user_id
                }
            
            elif action == "reorder_suggestions":
                # Get order history for recommendations
                orders_result = await self.call_other_service(
                    "order-service",
                    "customer_orders",
                    {"customer_id": user_id, "limit": 5}
                )
                
                if orders_result and orders_result.get("orders"):
                    # Extract product preferences from order history
                    order_preferences = self._extract_order_preferences(orders_result["orders"])
                    
                    # Get personalized recommendations
                    rec_result = await self.call_other_service(
                        "recommendation-service",
                        "personalized_recommendations",
                        {
                            "user_id": user_id,
                            "preferences": order_preferences,
                            "limit": 8
                        }
                    )
                    
                    return {
                        "action": "reorder_suggestions",
                        "recommendations": rec_result.get("recommendations", []) if rec_result else [],
                        "based_on_orders": len(orders_result.get("orders", [])),
                        "user_id": user_id
                    }
                else:
                    return {
                        "action": "reorder_suggestions",
                        "recommendations": [],
                        "message": "No order history found for recommendations",
                        "user_id": user_id
                    }
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Error in complete order flow: {e}")
            raise
    
    async def personalized_dashboard(self, user_id: str, sections: Optional[List[str]] = None) -> Dict:
        """Generate personalized user dashboard with cross-service data."""
        try:
            if not sections:
                sections = ["recommendations", "recent_orders", "trending", "categories"]
            
            logger.info(f"Generating personalized dashboard for user {user_id}: {sections}")
            
            dashboard_data = {"user_id": user_id, "sections": {}}
            tasks = []
            
            # Prepare parallel service calls based on requested sections
            if "recommendations" in sections:
                tasks.append(("recommendations", self.call_other_service(
                    "recommendation-service",
                    "personalized_recommendations",
                    {"user_id": user_id, "limit": 6}
                )))
            
            if "recent_orders" in sections:
                tasks.append(("recent_orders", self.call_other_service(
                    "order-service",
                    "recent_orders",
                    {"user_id": user_id, "limit": 5}
                )))
            
            if "trending" in sections:
                tasks.append(("trending", self.call_other_service(
                    "recommendation-service",
                    "trending_products",
                    {"limit": 8}
                )))
            
            if "categories" in sections:
                tasks.append(("categories", self.call_other_service(
                    "product-service",
                    "list_categories",
                    {}
                )))
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            # Process results
            for i, (section_name, _) in enumerate(tasks):
                result = results[i]
                if not isinstance(result, Exception) and result:
                    dashboard_data["sections"][section_name] = result
                else:
                    dashboard_data["sections"][section_name] = {"error": f"Failed to load {section_name}"}
            
            # Add metadata
            dashboard_data["generated_at"] = datetime.now().isoformat()
            dashboard_data["sections_loaded"] = len([s for s in dashboard_data["sections"].values() if "error" not in s])
            dashboard_data["total_sections"] = len(sections)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating personalized dashboard: {e}")
            raise
    
    async def service_health_check(self, detailed: bool = False) -> Dict:
        """Check health status of all registered services."""
        try:
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "services": {},
                "overall_status": "healthy"
            }
            
            # Check each registered service
            for service_name, service_info in self.registered_services.items():
                try:
                    # Simple health check by calling a basic method
                    if service_name == "product-service":
                        result = await self.call_other_service(service_name, "list_categories", {})
                    elif service_name == "recommendation-service":
                        result = await self.call_other_service(service_name, "trending_products", {"limit": 1})
                    elif service_name == "order-service":
                        result = await self.call_other_service(service_name, "get_order_stats", {"user_id": "health_check"})
                    elif service_name == "chat-service":
                        result = await self.call_other_service(service_name, "analyze_intent", {"message": "health check"})
                    else:
                        result = None
                    
                    if result is not None:
                        status = "healthy"
                        self.registered_services[service_name]["status"] = "healthy"
                    else:
                        status = "unhealthy"
                        self.registered_services[service_name]["status"] = "unhealthy"
                        health_data["overall_status"] = "degraded"
                    
                    health_data["services"][service_name] = {
                        "status": status,
                        "name": service_info["name"],
                        "description": service_info["description"]
                    }
                    
                    if detailed:
                        health_data["services"][service_name]["tools"] = service_info["tools"]
                        health_data["services"][service_name]["last_check"] = datetime.now().isoformat()
                
                except Exception as e:
                    health_data["services"][service_name] = {
                        "status": "error",
                        "error": str(e),
                        "name": service_info["name"]
                    }
                    health_data["overall_status"] = "degraded"
            
            # Update service health cache
            self.service_health = health_data
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error in service health check: {e}")
            raise
    
    async def cross_service_analytics(self, metric_type: str, time_range: str = "7d", filters: Optional[Dict] = None) -> Dict:
        """Generate analytics across multiple services."""
        try:
            logger.info(f"Generating cross-service analytics: {metric_type} for {time_range}")
            
            analytics_data = {
                "metric_type": metric_type,
                "time_range": time_range,
                "filters": filters or {},
                "generated_at": datetime.now().isoformat(),
                "data": {}
            }
            
            if metric_type == "user_journey":
                # Analyze user interactions across services
                analytics_data["data"] = await self._analyze_user_journey(time_range, filters)
            
            elif metric_type == "product_performance":
                # Product performance across search and recommendations
                analytics_data["data"] = await self._analyze_product_performance(time_range, filters)
            
            elif metric_type == "service_usage":
                # Service utilization and performance metrics
                analytics_data["data"] = await self._analyze_service_usage(time_range, filters)
            
            elif metric_type == "conversion_funnel":
                # Conversion funnel from search to order
                analytics_data["data"] = await self._analyze_conversion_funnel(time_range, filters)
            
            else:
                raise ValueError(f"Unknown metric type: {metric_type}")
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error in cross-service analytics: {e}")
            raise
    
    # Helper methods
    
    async def _search_products(self, query: str, limit: int) -> Dict:
        """Search products using product service."""
        return await self.call_other_service(
            "product-service",
            "search_products",
            {"query": query, "limit": limit}
        ) or {"products": []}
    
    async def _get_user_recommendations(self, user_id: str, query: str, limit: int) -> Dict:
        """Get user recommendations based on query context."""
        return await self.call_other_service(
            "recommendation-service",
            "personalized_recommendations",
            {"user_id": user_id, "context": {"search_query": query}, "limit": limit}
        ) or {"recommendations": []}
    
    def _combine_search_results(self, search_results: Dict, recommendations: Dict, query: str) -> Dict:
        """Combine search results and recommendations intelligently."""
        products = search_results.get("products", [])
        recs = recommendations.get("recommendations", [])
        
        # Mark products with their source
        for product in products:
            product["source"] = "search"
            product["relevance_score"] = product.get("relevance_score", 0.8)
        
        for rec in recs:
            rec["source"] = "recommendation"
            rec["relevance_score"] = rec.get("match_score", 0.7)
        
        # Combine and deduplicate
        all_products = products + recs
        seen_ids = set()
        unique_products = []
        
        for product in all_products:
            product_id = product.get("id") or product.get("product_id")
            if product_id and product_id not in seen_ids:
                seen_ids.add(product_id)
                unique_products.append(product)
        
        # Sort by relevance score
        unique_products.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return {
            "products": unique_products,
            "recommendations": recs,
            "search_results": products
        }
    
    async def _process_chat_actions(self, chat_response: Dict, user_id: str, message: str, context: Optional[Dict]) -> Dict:
        """Process actions from chat response and enhance with service calls."""
        actions = chat_response.get("actions", [])
        enhanced_response = {
            "response": chat_response.get("response", ""),
            "actions_performed": [],
            "suggested_actions": [],
            "context_data": {}
        }
        
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "product_search_completed":
                # Add suggested refinements
                enhanced_response["suggested_actions"].append({
                    "type": "refine_search",
                    "description": "Would you like to filter by price, category, or brand?"
                })
            
            elif action_type == "recommendations_provided":
                # Get similar products for recommended items
                products = action.get("products", [])
                if products and len(products) > 0:
                    first_product = products[0]
                    similar_result = await self.call_other_service(
                        "recommendation-service",
                        "similar_products",
                        {"product_id": first_product.get("id"), "limit": 3}
                    )
                    
                    if similar_result:
                        enhanced_response["context_data"]["similar_products"] = similar_result.get("similar_products", [])
            
            elif action_type == "order_info_provided":
                # Suggest reorder options
                enhanced_response["suggested_actions"].append({
                    "type": "reorder_suggestions",
                    "description": "Would you like recommendations based on your order history?"
                })
            
            enhanced_response["actions_performed"].append(action_type)
        
        return enhanced_response
    
    def _extract_order_preferences(self, orders: List[Dict]) -> Dict:
        """Extract user preferences from order history."""
        preferences = {
            "categories": {},
            "price_range": {"min": float("inf"), "max": 0},
            "brands": {},
            "recent_items": []
        }
        
        for order in orders:
            # This would be more sophisticated in a real implementation
            order_total = order.get("total_amount", 0)
            if order_total > 0:
                if order_total < preferences["price_range"]["min"]:
                    preferences["price_range"]["min"] = order_total
                if order_total > preferences["price_range"]["max"]:
                    preferences["price_range"]["max"] = order_total
        
        return preferences
    
    async def _analyze_user_journey(self, time_range: str, filters: Optional[Dict]) -> Dict:
        """Analyze user journey across services."""
        # Placeholder implementation
        return {
            "total_users": 150,
            "avg_session_duration": "8.5 minutes",
            "top_entry_points": ["product_search", "recommendations", "chat"],
            "conversion_rate": 0.23,
            "common_paths": [
                "search → recommendations → order",
                "chat → search → order",
                "recommendations → details → order"
            ]
        }
    
    async def _analyze_product_performance(self, time_range: str, filters: Optional[Dict]) -> Dict:
        """Analyze product performance across services."""
        # Placeholder implementation
        return {
            "top_searched_products": [],
            "top_recommended_products": [],
            "conversion_by_category": {},
            "search_to_order_rate": 0.18,
            "recommendation_click_rate": 0.34
        }
    
    async def _analyze_service_usage(self, time_range: str, filters: Optional[Dict]) -> Dict:
        """Analyze service utilization and performance."""
        # Placeholder implementation
        return {
            "service_calls": {
                "product-service": 1250,
                "recommendation-service": 890,
                "order-service": 340,
                "chat-service": 670,
                "gateway-service": 2100
            },
            "avg_response_times": {
                "product-service": "145ms",
                "recommendation-service": "230ms",
                "order-service": "89ms",
                "chat-service": "180ms"
            },
            "error_rates": {
                "product-service": 0.02,
                "recommendation-service": 0.01,
                "order-service": 0.03,
                "chat-service": 0.01
            }
        }
    
    async def _analyze_conversion_funnel(self, time_range: str, filters: Optional[Dict]) -> Dict:
        """Analyze conversion funnel from search to order."""
        # Placeholder implementation
        return {
            "funnel_stages": {
                "search": 1000,
                "view_details": 450,
                "add_to_cart": 180,
                "checkout": 120,
                "complete_order": 95
            },
            "conversion_rates": {
                "search_to_view": 0.45,
                "view_to_cart": 0.40,
                "cart_to_checkout": 0.67,
                "checkout_to_order": 0.79
            },
            "drop_off_points": [
                {"stage": "view_to_cart", "rate": 0.60, "reason": "price_sensitivity"},
                {"stage": "cart_to_checkout", "rate": 0.33, "reason": "checkout_complexity"}
            ]
        }

async def main():
    """Main function to run the gateway service."""
    service = GatewayMCPService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
