#!/usr/bin/env python3
"""
Order MCP Service
Handles order management and analytics in the e-commerce system.
"""

import asyncio
import os
from typing import Dict, List
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

from base_mcp_service import BaseMCPService

# Load environment variables
load_dotenv()

class OrderMCPService(BaseMCPService):
    """MCP Service for order operations."""
    
    def __init__(self):
        super().__init__("order-service", "1.0.0")
        self.mongo_client = None
        self.db = None
    
    def setup_service(self):
        """Setup service-specific configuration."""
        self.logger.info("Setting up Order Service...")
    
    async def initialize_service(self):
        """Initialize database connection."""
        try:
            mongo_uri = os.getenv('MONGO_DB_URI', 'mongodb://localhost:27017')
            db_name = os.getenv('MONGODB_DATABASE', 'ecommerce_assistant')
            
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[db_name]
            
            self.logger.info(f"Connected to MongoDB: {db_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def register_tools(self):
        """Register order-specific tools."""
        self.tools.update({
            "get_order_stats": {
                "name": "get_order_stats",
                "description": "Get comprehensive order statistics and metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Type of statistics to retrieve",
                            "enum": ["overview", "recent", "trends", "revenue", "status"],
                            "default": "overview"
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Time period for analysis",
                            "enum": ["last_week", "last_month", "last_quarter", "all_time"],
                            "default": "last_month"
                        }
                    },
                    "required": []
                }
            },
            "recent_orders": {
                "name": "recent_orders",
                "description": "Get recent orders with details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent orders to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by order status",
                            "enum": ["pending", "processing", "shipped", "delivered", "cancelled"]
                        }
                    },
                    "required": []
                }
            },
            "order_analytics": {
                "name": "order_analytics",
                "description": "Get detailed order analytics and insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of analysis to perform",
                            "enum": ["sales_trends", "customer_behavior", "product_performance", "payment_methods"],
                            "default": "sales_trends"
                        },
                        "time_period": {
                            "type": "string",
                            "enum": ["last_week", "last_month", "last_quarter", "all_time"],
                            "default": "last_month"
                        }
                    },
                    "required": ["analysis_type"]
                }
            },
            "customer_orders": {
                "name": "customer_orders",
                "description": "Get order history for a specific customer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email address"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of orders to return",
                            "default": 20
                        }
                    },
                    "required": ["customer_email"]
                }
            }
        })
    
    def register_resources(self):
        """Register order-specific resources."""
        self.resources.update({
            "ecommerce://orders/data": {
                "uri": "ecommerce://orders/data",
                "name": "Order Data",
                "description": "Complete order database with transactions and details",
                "mimeType": "application/json"
            },
            "ecommerce://orders/analytics": {
                "uri": "ecommerce://orders/analytics",
                "name": "Order Analytics",
                "description": "Order analytics dashboard with KPIs and metrics",
                "mimeType": "application/json"
            },
            "ecommerce://orders/reports": {
                "uri": "ecommerce://orders/reports",
                "name": "Order Reports",
                "description": "Generated order reports and summaries",
                "mimeType": "text/plain"
            }
        })
    
    async def execute_tool(self, name: str, arguments: Dict) -> str:
        """Execute order-specific tools."""
        if name == "get_order_stats":
            return await self.get_order_stats(arguments)
        elif name == "recent_orders":
            return await self.recent_orders(arguments)
        elif name == "order_analytics":
            return await self.order_analytics(arguments)
        elif name == "customer_orders":
            return await self.customer_orders(arguments)
        else:
            return await super().execute_tool(name, arguments)
    
    def _get_time_filter(self, time_period: str) -> Dict:
        """Get MongoDB time filter based on period."""
        now = datetime.now()
        
        if time_period == "last_week":
            start_date = now - timedelta(weeks=1)
        elif time_period == "last_month":
            start_date = now - timedelta(days=30)
        elif time_period == "last_quarter":
            start_date = now - timedelta(days=90)
        else:  # all_time
            return {}
        
        return {"created_at": {"$gte": start_date}}
    
    async def get_order_stats(self, args: Dict) -> str:
        """Get order statistics."""
        try:
            stat_type = args.get("type", "overview")
            time_period = args.get("time_period", "last_month")
            
            time_filter = self._get_time_filter(time_period)
            
            if stat_type == "overview":
                return await self._get_overview_stats(time_filter, time_period)
            elif stat_type == "recent":
                return await self._get_recent_stats(time_filter)
            elif stat_type == "trends":
                return await self._get_trend_stats(time_filter, time_period)
            elif stat_type == "revenue":
                return await self._get_revenue_stats(time_filter, time_period)
            elif stat_type == "status":
                return await self._get_status_stats(time_filter)
            else:
                return f"❌ Unknown statistics type: {stat_type}"
                
        except Exception as e:
            self.logger.error(f"Order stats error: {e}")
            return f"❌ Error getting order statistics: {str(e)}"
    
    async def _get_overview_stats(self, time_filter: Dict, period: str) -> str:
        """Get overview statistics."""
        # Total orders
        total_orders = self.db.orders.count_documents(time_filter)
        
        # Revenue calculation
        revenue_pipeline = [
            {"$match": {**time_filter, "status": {"$ne": "cancelled"}}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        revenue_result = list(self.db.orders.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]["total"] if revenue_result else 0
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Order status breakdown
        status_pipeline = [
            {"$match": time_filter},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_breakdown = {item["_id"]: item["count"] for item in self.db.orders.aggregate(status_pipeline)}
        
        # Payment method breakdown
        payment_pipeline = [
            {"$match": time_filter},
            {"$group": {"_id": "$payment_method", "count": {"$sum": 1}}}
        ]
        payment_breakdown = {item["_id"]: item["count"] for item in self.db.orders.aggregate(payment_pipeline)}
        
        # Format results
        result = f"📊 **Order Statistics Overview** ({period.replace('_', ' ').title()})\n\n"
        
        result += f"📈 **Key Metrics**\n"
        result += f"• Total Orders: {total_orders:,}\n"
        result += f"• Total Revenue: ${total_revenue:,.2f}\n"
        result += f"• Average Order Value: ${avg_order_value:.2f}\n\n"
        
        result += f"📋 **Order Status Breakdown**\n"
        for status, count in status_breakdown.items():
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            result += f"• {status.title()}: {count} ({percentage:.1f}%)\n"
        
        result += f"\n💳 **Payment Methods**\n"
        for method, count in payment_breakdown.items():
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            result += f"• {method.replace('_', ' ').title()}: {count} ({percentage:.1f}%)\n"
        
        return result
    
    async def _get_recent_stats(self, time_filter: Dict) -> str:
        """Get recent order statistics."""
        recent_orders = list(self.db.orders.find(time_filter).sort("created_at", -1).limit(10))
        
        if not recent_orders:
            return "❌ No recent orders found"
        
        result = f"📋 **Recent Orders** ({len(recent_orders)} orders)\n\n"
        
        for order in recent_orders:
            result += f"• **Order #{order['order_number']}**\n"
            result += f"  Status: {order['status'].title()}\n"
            result += f"  Amount: ${order['total_amount']:.2f}\n"
            result += f"  Date: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            result += f"  Payment: {order.get('payment_method', 'N/A').replace('_', ' ').title()}\n\n"
        
        return result
    
    async def _get_trend_stats(self, time_filter: Dict, period: str) -> str:
        """Get trend statistics."""
        # Daily order trends
        daily_pipeline = [
            {"$match": time_filter},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "orders": {"$sum": 1},
                    "revenue": {"$sum": "$total_amount"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_trends = list(self.db.orders.aggregate(daily_pipeline))
        
        result = f"📈 **Order Trends** ({period.replace('_', ' ').title()})\n\n"
        
        if daily_trends:
            result += f"📅 **Daily Performance**\n"
            for day in daily_trends[-7:]:  # Last 7 days
                result += f"• {day['_id']}: {day['orders']} orders, ${day['revenue']:.2f}\n"
            
            # Calculate growth
            if len(daily_trends) >= 2:
                latest_revenue = daily_trends[-1]['revenue']
                previous_revenue = daily_trends[-2]['revenue']
                growth = ((latest_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
                result += f"\n📊 **Day-over-day Growth**: {growth:+.1f}%\n"
        
        return result
    
    async def _get_revenue_stats(self, time_filter: Dict, period: str) -> str:
        """Get revenue statistics."""
        # Revenue by status
        revenue_pipeline = [
            {"$match": time_filter},
            {
                "$group": {
                    "_id": "$status",
                    "revenue": {"$sum": "$total_amount"},
                    "orders": {"$sum": 1}
                }
            }
        ]
        
        revenue_by_status = list(self.db.orders.aggregate(revenue_pipeline))
        
        # Revenue breakdown
        breakdown_pipeline = [
            {"$match": {**time_filter, "status": {"$ne": "cancelled"}}},
            {
                "$group": {
                    "_id": None,
                    "subtotal": {"$sum": "$subtotal"},
                    "tax": {"$sum": "$tax_amount"},
                    "shipping": {"$sum": "$shipping_amount"},
                    "discounts": {"$sum": "$discount_amount"}
                }
            }
        ]
        
        breakdown_result = list(self.db.orders.aggregate(breakdown_pipeline))
        breakdown = breakdown_result[0] if breakdown_result else {}
        
        result = f"💰 **Revenue Analysis** ({period.replace('_', ' ').title()})\n\n"
        
        # Revenue by status
        result += f"📊 **Revenue by Order Status**\n"
        total_revenue = 0
        for item in revenue_by_status:
            status = item["_id"]
            revenue = item["revenue"]
            orders = item["orders"]
            avg_value = revenue / orders if orders > 0 else 0
            
            result += f"• {status.title()}: ${revenue:,.2f} ({orders} orders, avg ${avg_value:.2f})\n"
            if status != "cancelled":
                total_revenue += revenue
        
        result += f"\n💵 **Total Net Revenue**: ${total_revenue:,.2f}\n\n"
        
        # Revenue breakdown
        if breakdown:
            result += f"🧾 **Revenue Breakdown**\n"
            result += f"• Subtotal: ${breakdown.get('subtotal', 0):,.2f}\n"
            result += f"• Tax: ${breakdown.get('tax', 0):,.2f}\n"
            result += f"• Shipping: ${breakdown.get('shipping', 0):,.2f}\n"
            result += f"• Discounts: -${breakdown.get('discounts', 0):,.2f}\n"
        
        return result
    
    async def _get_status_stats(self, time_filter: Dict) -> str:
        """Get order status statistics."""
        status_pipeline = [
            {"$match": time_filter},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "revenue": {"$sum": "$total_amount"},
                    "avg_value": {"$avg": "$total_amount"}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        status_stats = list(self.db.orders.aggregate(status_pipeline))
        total_orders = sum(item["count"] for item in status_stats)
        
        result = f"📋 **Order Status Analysis**\n\n"
        
        for item in status_stats:
            status = item["_id"]
            count = item["count"]
            revenue = item["revenue"]
            avg_value = item["avg_value"]
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            
            result += f"**{status.upper()}**\n"
            result += f"• Orders: {count} ({percentage:.1f}%)\n"
            result += f"• Revenue: ${revenue:,.2f}\n"
            result += f"• Avg Value: ${avg_value:.2f}\n\n"
        
        return result
    
    async def recent_orders(self, args: Dict) -> str:
        """Get recent orders."""
        try:
            limit = args.get("limit", 10)
            status_filter = args.get("status")
            
            query = {}
            if status_filter:
                query["status"] = status_filter
            
            orders = list(self.db.orders.find(query).sort("created_at", -1).limit(limit))
            
            if not orders:
                return "❌ No recent orders found"
            
            result = f"📋 **Recent Orders** ({len(orders)} orders"
            if status_filter:
                result += f" with status '{status_filter}'"
            result += ")\n\n"
            
            for order in orders:
                result += f"🛍️ **{order['order_number']}**\n"
                result += f"   📅 {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                result += f"   💰 ${order['total_amount']:.2f}\n"
                result += f"   📦 Status: {order['status'].title()}\n"
                result += f"   💳 Payment: {order.get('payment_method', 'N/A').replace('_', ' ').title()}\n"
                
                if order.get('shipped_at'):
                    result += f"   🚚 Shipped: {order['shipped_at'].strftime('%Y-%m-%d')}\n"
                if order.get('delivered_at'):
                    result += f"   ✅ Delivered: {order['delivered_at'].strftime('%Y-%m-%d')}\n"
                
                result += "\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Recent orders error: {e}")
            return f"❌ Error getting recent orders: {str(e)}"
    
    async def order_analytics(self, args: Dict) -> str:
        """Get detailed order analytics."""
        try:
            analysis_type = args.get("analysis_type", "sales_trends")
            time_period = args.get("time_period", "last_month")
            
            time_filter = self._get_time_filter(time_period)
            
            if analysis_type == "sales_trends":
                return await self._analyze_sales_trends(time_filter, time_period)
            elif analysis_type == "customer_behavior":
                return await self._analyze_customer_behavior(time_filter, time_period)
            elif analysis_type == "product_performance":
                return await self._analyze_product_performance(time_filter, time_period)
            elif analysis_type == "payment_methods":
                return await self._analyze_payment_methods(time_filter, time_period)
            else:
                return f"❌ Unknown analysis type: {analysis_type}"
                
        except Exception as e:
            self.logger.error(f"Order analytics error: {e}")
            return f"❌ Error running analytics: {str(e)}"
    
    async def _analyze_sales_trends(self, time_filter: Dict, period: str) -> str:
        """Analyze sales trends."""
        # Implementation would include trend analysis
        return f"📈 **Sales Trends Analysis** ({period})\n\nDetailed sales trend analysis would be implemented here."
    
    async def _analyze_customer_behavior(self, time_filter: Dict, period: str) -> str:
        """Analyze customer behavior."""
        # Implementation would include customer behavior analysis
        return f"👥 **Customer Behavior Analysis** ({period})\n\nCustomer behavior insights would be implemented here."
    
    async def _analyze_product_performance(self, time_filter: Dict, period: str) -> str:
        """Analyze product performance."""
        # Implementation would include product performance analysis
        return f"📦 **Product Performance Analysis** ({period})\n\nProduct performance metrics would be implemented here."
    
    async def _analyze_payment_methods(self, time_filter: Dict, period: str) -> str:
        """Analyze payment methods."""
        pipeline = [
            {"$match": time_filter},
            {
                "$group": {
                    "_id": "$payment_method",
                    "count": {"$sum": 1},
                    "revenue": {"$sum": "$total_amount"},
                    "avg_value": {"$avg": "$total_amount"}
                }
            },
            {"$sort": {"revenue": -1}}
        ]
        
        payment_stats = list(self.db.orders.aggregate(pipeline))
        total_orders = sum(item["count"] for item in payment_stats)
        total_revenue = sum(item["revenue"] for item in payment_stats)
        
        result = f"💳 **Payment Methods Analysis** ({period})\n\n"
        
        for item in payment_stats:
            method = item["_id"]
            count = item["count"]
            revenue = item["revenue"]
            avg_value = item["avg_value"]
            
            order_pct = (count / total_orders * 100) if total_orders > 0 else 0
            revenue_pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            result += f"**{method.replace('_', ' ').title()}**\n"
            result += f"• Orders: {count} ({order_pct:.1f}%)\n"
            result += f"• Revenue: ${revenue:,.2f} ({revenue_pct:.1f}%)\n"
            result += f"• Avg Value: ${avg_value:.2f}\n\n"
        
        return result
    
    async def customer_orders(self, args: Dict) -> str:
        """Get customer order history."""
        try:
            customer_email = args.get("customer_email", "").strip()
            limit = args.get("limit", 20)
            
            # Find customer
            customer = self.db.customers.find_one({"email": customer_email})
            if not customer:
                return f"❌ Customer not found: {customer_email}"
            
            # Get customer orders
            orders = list(self.db.orders.find(
                {"customer_id": customer["_id"]}
            ).sort("created_at", -1).limit(limit))
            
            if not orders:
                return f"❌ No orders found for customer: {customer_email}"
            
            # Calculate customer stats
            total_spent = sum(order["total_amount"] for order in orders if order["status"] != "cancelled")
            avg_order_value = total_spent / len(orders) if orders else 0
            
            result = f"👤 **Customer Order History**\n"
            result += f"Customer: {customer['first_name']} {customer['last_name']} ({customer_email})\n\n"
            
            result += f"📊 **Customer Summary**\n"
            result += f"• Total Orders: {len(orders)}\n"
            result += f"• Total Spent: ${total_spent:.2f}\n"
            result += f"• Average Order Value: ${avg_order_value:.2f}\n\n"
            
            result += f"📋 **Order History**\n\n"
            
            for order in orders:
                result += f"🛍️ **{order['order_number']}**\n"
                result += f"   📅 {order['created_at'].strftime('%Y-%m-%d')}\n"
                result += f"   💰 ${order['total_amount']:.2f}\n"
                result += f"   📦 {order['status'].title()}\n\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Customer orders error: {e}")
            return f"❌ Error getting customer orders: {str(e)}"
    
    async def read_service_resource(self, uri: str) -> str:
        """Read order-specific resources."""
        try:
            if uri == "ecommerce://orders/data":
                recent_count = self.db.orders.count_documents({})
                return f"📊 **Order Database**\n\nTotal Orders: {recent_count:,}\nLast Updated: {datetime.now().isoformat()}"
            
            elif uri == "ecommerce://orders/analytics":
                return await self._get_overview_stats({}, "all_time")
            
            elif uri == "ecommerce://orders/reports":
                return "📈 **Order Reports**\n\nVarious order reports and summaries are available through the analytics tools."
            
            else:
                return await super().read_service_resource(uri)
                
        except Exception as e:
            self.logger.error(f"Resource read error: {e}")
            return f"❌ Error reading resource: {str(e)}"

async def main():
    """Main function to run the Order MCP Service."""
    service = OrderMCPService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
