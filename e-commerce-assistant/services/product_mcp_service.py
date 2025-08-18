#!/usr/bin/env python3
"""
Product MCP Service
Handles all product-related operations in the e-commerce system.
"""

import asyncio
import os
from typing import Dict, List
from pymongo import MongoClient
from dotenv import load_dotenv

from base_mcp_service import BaseMCPService

# Load environment variables
load_dotenv()

class ProductMCPService(BaseMCPService):
    """MCP Service for product operations."""
    
    def __init__(self):
        super().__init__("product-service", "1.0.0")
        self.mongo_client = None
        self.db = None
    
    def setup_service(self):
        """Setup service-specific configuration."""
        self.logger.info("Setting up Product Service...")
    
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
        """Register product-specific tools."""
        self.tools.update({
            "search_products": {
                "name": "search_products",
                "description": "Search for products using various criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (product name, brand, category)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by product category"
                        },
                        "min_price": {
                            "type": "number",
                            "description": "Minimum price filter"
                        },
                        "max_price": {
                            "type": "number", 
                            "description": "Maximum price filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_product_details": {
                "name": "get_product_details",
                "description": "Get detailed information about a specific product",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID or name to get details for"
                        }
                    },
                    "required": ["product_id"]
                }
            },
            "list_categories": {
                "name": "list_categories",
                "description": "Get all available product categories",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "filter_products": {
                "name": "filter_products", 
                "description": "Filter products by specific criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "brand": {
                            "type": "string",
                            "description": "Filter by brand"
                        },
                        "rating_min": {
                            "type": "number",
                            "description": "Minimum rating filter"
                        },
                        "in_stock": {
                            "type": "boolean",
                            "description": "Filter by stock availability"
                        },
                        "featured": {
                            "type": "boolean", 
                            "description": "Filter featured products"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 20
                        }
                    },
                    "required": []
                }
            }
        })
    
    def register_resources(self):
        """Register product-specific resources."""
        self.resources.update({
            "ecommerce://products/catalog": {
                "uri": "ecommerce://products/catalog",
                "name": "Product Catalog",
                "description": "Complete product catalog with all available products",
                "mimeType": "application/json"
            },
            "ecommerce://products/categories": {
                "uri": "ecommerce://products/categories",
                "name": "Product Categories",
                "description": "All product categories and subcategories",
                "mimeType": "application/json"
            },
            "ecommerce://products/featured": {
                "uri": "ecommerce://products/featured",
                "name": "Featured Products", 
                "description": "Currently featured products",
                "mimeType": "application/json"
            }
        })
    
    async def execute_tool(self, name: str, arguments: Dict) -> str:
        """Execute product-specific tools."""
        if name == "search_products":
            return await self.search_products(arguments)
        elif name == "get_product_details":
            return await self.get_product_details(arguments)
        elif name == "list_categories":
            return await self.list_categories(arguments)
        elif name == "filter_products":
            return await self.filter_products(arguments)
        else:
            return await super().execute_tool(name, arguments)
    
    async def search_products(self, args: Dict) -> str:
        """Search for products."""
        try:
            query = args.get("query", "").lower().strip()
            category = args.get("category")
            min_price = args.get("min_price")
            max_price = args.get("max_price")
            limit = args.get("limit", 10)
            
            # Build MongoDB query
            mongo_query = {"is_active": True}
            
            # Text search
            if query:
                mongo_query["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"brand": {"$regex": query, "$options": "i"}}
                ]
            
            # Category filter
            if category:
                # Find category ID
                category_doc = self.db.categories.find_one(
                    {"name": {"$regex": category, "$options": "i"}}
                )
                if category_doc:
                    mongo_query["category_id"] = category_doc["_id"]
            
            # Price filters
            if min_price is not None or max_price is not None:
                price_filter = {}
                if min_price is not None:
                    price_filter["$gte"] = min_price
                if max_price is not None:
                    price_filter["$lte"] = max_price
                mongo_query["price"] = price_filter
            
            # Execute query
            products = list(self.db.products.find(mongo_query).limit(limit))
            
            if not products:
                return f"❌ No products found for query: '{query}'"
            
            # Format results
            results = []
            for product in products:
                results.append({
                    "name": product["name"],
                    "brand": product.get("brand", "N/A"),
                    "price": product["price"],
                    "rating": product.get("rating", "N/A"),
                    "stock": product.get("stock_quantity", 0),
                    "description": product["description"][:100] + "..."
                })
            
            formatted_results = []
            for r in results:
                formatted_results.append(
                    f"• **{r['brand']} {r['name']}** - ${r['price']}\n"
                    f"  ⭐ {r['rating']}/5.0 | 📦 Stock: {r['stock']}\n"
                    f"  📝 {r['description']}"
                )
            
            return f"🔍 Found {len(results)} products:\n\n" + "\n\n".join(formatted_results)
            
        except Exception as e:
            self.logger.error(f"Product search error: {e}")
            return f"❌ Error searching products: {str(e)}"
    
    async def get_product_details(self, args: Dict) -> str:
        """Get detailed product information."""
        try:
            product_id = args.get("product_id", "").strip()
            
            # Try to find by name first, then by ID
            product = self.db.products.find_one({
                "$or": [
                    {"name": {"$regex": product_id, "$options": "i"}},
                    {"_id": product_id} if len(product_id) == 24 else {"name": ""}
                ]
            })
            
            if not product:
                return f"❌ Product not found: '{product_id}'"
            
            # Get category name
            category_name = "N/A"
            if product.get("category_id"):
                category = self.db.categories.find_one({"_id": product["category_id"]})
                if category:
                    category_name = category["name"]
            
            # Format detailed information
            details = f"""
📦 **Product Details**

**{product.get('brand', 'N/A')} {product['name']}**

💰 **Price**: ${product['price']}
📂 **Category**: {category_name}
⭐ **Rating**: {product.get('rating', 'N/A')}/5.0 ({product.get('review_count', 0)} reviews)
📦 **Stock**: {product.get('stock_quantity', 0)} units
🏷️ **SKU**: {product.get('sku', 'N/A')}

📝 **Description**:
{product['description']}

🔧 **Specifications**:
"""
            
            # Add specifications if available
            specs = []
            if product.get('color'):
                specs.append(f"• Color: {product['color']}")
            if product.get('size'):
                specs.append(f"• Size: {product['size']}")
            if product.get('weight'):
                specs.append(f"• Weight: {product['weight']} kg")
            if product.get('material'):
                specs.append(f"• Material: {product['material']}")
            
            if specs:
                details += "\n".join(specs)
            else:
                details += "No detailed specifications available"
            
            # Add availability status
            stock = product.get('stock_quantity', 0)
            if stock > 0:
                details += f"\n\n✅ **In Stock** ({stock} available)"
            else:
                details += "\n\n❌ **Out of Stock**"
            
            return details.strip()
            
        except Exception as e:
            self.logger.error(f"Product details error: {e}")
            return f"❌ Error getting product details: {str(e)}"
    
    async def list_categories(self, args: Dict) -> str:
        """List all product categories."""
        try:
            categories = list(self.db.categories.find())
            
            if not categories:
                return "❌ No categories found"
            
            # Organize categories by parent
            main_categories = []
            sub_categories = {}
            
            for category in categories:
                if category.get("parent_id") is None:
                    main_categories.append(category)
                else:
                    parent_id = category["parent_id"]
                    if parent_id not in sub_categories:
                        sub_categories[parent_id] = []
                    sub_categories[parent_id].append(category)
            
            # Format output
            result = "📂 **Product Categories**\n\n"
            
            for main_cat in main_categories:
                result += f"**{main_cat['name']}**\n"
                result += f"   {main_cat['description']}\n"
                
                # Add subcategories if they exist
                if main_cat["_id"] in sub_categories:
                    for sub_cat in sub_categories[main_cat["_id"]]:
                        result += f"   └─ {sub_cat['name']}\n"
                
                result += "\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"List categories error: {e}")
            return f"❌ Error listing categories: {str(e)}"
    
    async def filter_products(self, args: Dict) -> str:
        """Filter products by criteria."""
        try:
            brand = args.get("brand")
            rating_min = args.get("rating_min")
            in_stock = args.get("in_stock")
            featured = args.get("featured")
            limit = args.get("limit", 20)
            
            # Build query
            query = {"is_active": True}
            
            if brand:
                query["brand"] = {"$regex": brand, "$options": "i"}
            
            if rating_min is not None:
                query["rating"] = {"$gte": rating_min}
            
            if in_stock is True:
                query["stock_quantity"] = {"$gt": 0}
            elif in_stock is False:
                query["stock_quantity"] = {"$lte": 0}
            
            if featured is not None:
                query["featured"] = featured
            
            # Execute query
            products = list(self.db.products.find(query).limit(limit))
            
            if not products:
                return "❌ No products match the specified filters"
            
            # Format results
            result = f"🔍 **Filtered Products** ({len(products)} found)\n\n"
            
            for product in products:
                result += f"• **{product.get('brand', 'N/A')} {product['name']}**\n"
                result += f"  💰 ${product['price']} | ⭐ {product.get('rating', 'N/A')}/5.0\n"
                result += f"  📦 Stock: {product.get('stock_quantity', 0)}"
                
                if product.get('featured'):
                    result += " | ⭐ Featured"
                
                result += "\n\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Filter products error: {e}")
            return f"❌ Error filtering products: {str(e)}"
    
    async def read_service_resource(self, uri: str) -> str:
        """Read product-specific resources."""
        try:
            if uri == "ecommerce://products/catalog":
                products = list(self.db.products.find({"is_active": True}).limit(50))
                return f"📦 Product Catalog ({len(products)} products)\n\n" + str(products)
            
            elif uri == "ecommerce://products/categories":
                categories = list(self.db.categories.find())
                return f"📂 Product Categories ({len(categories)} categories)\n\n" + str(categories)
            
            elif uri == "ecommerce://products/featured":
                featured = list(self.db.products.find({"featured": True, "is_active": True}))
                return f"⭐ Featured Products ({len(featured)} products)\n\n" + str(featured)
            
            else:
                return await super().read_service_resource(uri)
                
        except Exception as e:
            self.logger.error(f"Resource read error: {e}")
            return f"❌ Error reading resource: {str(e)}"

async def main():
    """Main function to run the Product MCP Service."""
    service = ProductMCPService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
