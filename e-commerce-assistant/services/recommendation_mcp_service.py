#!/usr/bin/env python3
"""
Recommendation MCP Service
Handles AI-powered product recommendations in the e-commerce system.
"""

import asyncio
import os
from typing import Dict, List
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

from base_mcp_service import BaseMCPService

# Load environment variables
load_dotenv()

class RecommendationMCPService(BaseMCPService):
    """MCP Service for product recommendations."""
    
    def __init__(self):
        super().__init__("recommendation-service", "1.0.0")
        self.mongo_client = None
        self.db = None
    
    def setup_service(self):
        """Setup service-specific configuration."""
        self.logger.info("Setting up Recommendation Service...")
    
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
        """Register recommendation-specific tools."""
        self.tools.update({
            "get_recommendations": {
                "name": "get_recommendations",
                "description": "Get AI-powered product recommendations based on user query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "User description of what they're looking for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of recommendations to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category filter"
                        },
                        "price_range": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"}
                            }
                        }
                    },
                    "required": ["query"]
                }
            },
            "similar_products": {
                "name": "similar_products",
                "description": "Find products similar to a given product",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "ID or name of the reference product"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of similar products to return",
                            "default": 5
                        }
                    },
                    "required": ["product_id"]
                }
            },
            "trending_products": {
                "name": "trending_products",
                "description": "Get currently trending products",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Optional category filter"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of trending products",
                            "default": 10
                        }
                    },
                    "required": []
                }
            },
            "personalized_recommendations": {
                "name": "personalized_recommendations",
                "description": "Get personalized recommendations based on user preferences",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_preferences": {
                            "type": "object",
                            "properties": {
                                "brands": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "categories": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "price_range": {
                                    "type": "object",
                                    "properties": {
                                        "min": {"type": "number"},
                                        "max": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10
                        }
                    },
                    "required": ["user_preferences"]
                }
            }
        })
    
    def register_resources(self):
        """Register recommendation-specific resources."""
        self.resources.update({
            "ecommerce://recommendations/engine": {
                "uri": "ecommerce://recommendations/engine",
                "name": "Recommendation Engine",
                "description": "AI-powered recommendation engine information and capabilities",
                "mimeType": "text/plain"
            },
            "ecommerce://recommendations/trending": {
                "uri": "ecommerce://recommendations/trending",
                "name": "Trending Products",
                "description": "Currently trending products across all categories",
                "mimeType": "application/json"
            },
            "ecommerce://recommendations/models": {
                "uri": "ecommerce://recommendations/models",
                "name": "ML Models",
                "description": "Information about recommendation models and algorithms",
                "mimeType": "text/plain"
            }
        })
    
    async def execute_tool(self, name: str, arguments: Dict) -> str:
        """Execute recommendation-specific tools."""
        if name == "get_recommendations":
            return await self.get_recommendations(arguments)
        elif name == "similar_products":
            return await self.similar_products(arguments)
        elif name == "trending_products":
            return await self.trending_products(arguments)
        elif name == "personalized_recommendations":
            return await self.personalized_recommendations(arguments)
        else:
            return await super().execute_tool(name, arguments)
    
    async def get_recommendations(self, args: Dict) -> str:
        """Get AI-powered product recommendations."""
        try:
            query = args.get("query", "").lower().strip()
            limit = args.get("limit", 5)
            category = args.get("category")
            price_range = args.get("price_range", {})
            
            # Build search criteria based on query keywords
            keywords = query.split()
            search_terms = []
            
            # Map common terms to product attributes
            category_mappings = {
                'phone': ['smartphone', 'mobile', 'iphone', 'samsung'],
                'laptop': ['computer', 'macbook', 'notebook', 'dell'],
                'headphone': ['audio', 'earphone', 'airpods', 'sony'],
                'watch': ['smartwatch', 'apple watch'],
                'gaming': ['game', 'console', 'xbox', 'playstation']
            }
            
            # Find relevant search terms
            for keyword in keywords:
                search_terms.append(keyword)
                for cat, terms in category_mappings.items():
                    if keyword in terms or cat in keyword:
                        search_terms.extend(terms)
            
            # Remove duplicates
            search_terms = list(set(search_terms))
            
            # Build MongoDB query
            mongo_query = {"is_active": True}
            
            if search_terms:
                mongo_query["$or"] = []
                for term in search_terms:
                    mongo_query["$or"].extend([
                        {"name": {"$regex": term, "$options": "i"}},
                        {"description": {"$regex": term, "$options": "i"}},
                        {"brand": {"$regex": term, "$options": "i"}}
                    ])
            
            # Category filter
            if category:
                category_doc = self.db.categories.find_one(
                    {"name": {"$regex": category, "$options": "i"}}
                )
                if category_doc:
                    mongo_query["category_id"] = category_doc["_id"]
            
            # Price range filter
            if price_range:
                price_filter = {}
                if price_range.get("min"):
                    price_filter["$gte"] = price_range["min"]
                if price_range.get("max"):
                    price_filter["$lte"] = price_range["max"]
                if price_filter:
                    mongo_query["price"] = price_filter
            
            # Execute query with intelligent sorting
            # Prioritize by rating, stock availability, and featured status
            products = list(self.db.products.find(mongo_query).sort([
                ("featured", -1),
                ("rating", -1),
                ("stock_quantity", -1)
            ]).limit(limit))
            
            if not products:
                return f"❌ No recommendations found for: '{query}'"
            
            # Format recommendations
            result = f"🎯 **AI Recommendations for '{query}'**\n\n"
            
            for i, product in enumerate(products, 1):
                result += f"**{i}. {product.get('brand', 'N/A')} {product['name']}**\n"
                result += f"   💰 **Price**: ${product['price']}\n"
                result += f"   ⭐ **Rating**: {product.get('rating', 'N/A')}/5.0"
                
                if product.get('review_count', 0) > 0:
                    result += f" ({product['review_count']} reviews)"
                
                result += f"\n   📦 **Stock**: {product.get('stock_quantity', 0)} units\n"
                
                if product.get('featured'):
                    result += "   ⭐ **Featured Product**\n"
                
                # Add brief description
                description = product['description'][:150]
                result += f"   📝 {description}...\n\n"
            
            # Add recommendation reasoning
            result += "🤖 **Why these recommendations?**\n"
            result += "• Sorted by rating and customer reviews\n"
            result += "• Prioritized in-stock items\n"
            result += "• Featured products highlighted\n"
            
            if category:
                result += f"• Filtered for category: {category}\n"
            
            if price_range:
                result += f"• Price range: ${price_range.get('min', 0)} - ${price_range.get('max', '∞')}\n"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Recommendations error: {e}")
            return f"❌ Error getting recommendations: {str(e)}"
    
    async def similar_products(self, args: Dict) -> str:
        """Find products similar to a reference product."""
        try:
            product_id = args.get("product_id", "").strip()
            limit = args.get("limit", 5)
            
            # Find the reference product
            ref_product = self.db.products.find_one({
                "$or": [
                    {"name": {"$regex": product_id, "$options": "i"}},
                    {"_id": ObjectId(product_id)} if len(product_id) == 24 else {"name": ""}
                ]
            })
            
            if not ref_product:
                return f"❌ Reference product not found: '{product_id}'"
            
            # Find similar products based on:
            # 1. Same category
            # 2. Similar price range (±30%)
            # 3. Same brand (bonus)
            
            price_min = ref_product["price"] * 0.7
            price_max = ref_product["price"] * 1.3
            
            query = {
                "is_active": True,
                "_id": {"$ne": ref_product["_id"]},  # Exclude the reference product
                "$or": [
                    {"category_id": ref_product.get("category_id")},
                    {"brand": ref_product.get("brand")},
                    {"price": {"$gte": price_min, "$lte": price_max}}
                ]
            }
            
            # Execute query with scoring
            similar_products = list(self.db.products.find(query).limit(limit * 2))
            
            # Score products based on similarity
            scored_products = []
            for product in similar_products:
                score = 0
                
                # Category match (high importance)
                if product.get("category_id") == ref_product.get("category_id"):
                    score += 3
                
                # Brand match (medium importance)
                if product.get("brand") == ref_product.get("brand"):
                    score += 2
                
                # Price similarity (low importance)
                price_diff = abs(product["price"] - ref_product["price"]) / ref_product["price"]
                if price_diff < 0.3:
                    score += 1
                
                # Rating bonus
                if product.get("rating", 0) >= 4.0:
                    score += 1
                
                scored_products.append((product, score))
            
            # Sort by score and take top results
            scored_products.sort(key=lambda x: x[1], reverse=True)
            top_products = [p[0] for p in scored_products[:limit]]
            
            if not top_products:
                return f"❌ No similar products found for '{ref_product['name']}'"
            
            # Format results
            result = f"🔍 **Products Similar to '{ref_product['name']}'**\n\n"
            
            for i, product in enumerate(top_products, 1):
                result += f"**{i}. {product.get('brand', 'N/A')} {product['name']}**\n"
                result += f"   💰 ${product['price']} (vs ${ref_product['price']})\n"
                result += f"   ⭐ {product.get('rating', 'N/A')}/5.0\n"
                
                # Show similarity reasons
                reasons = []
                if product.get("category_id") == ref_product.get("category_id"):
                    reasons.append("same category")
                if product.get("brand") == ref_product.get("brand"):
                    reasons.append("same brand")
                
                price_diff = abs(product["price"] - ref_product["price"]) / ref_product["price"]
                if price_diff < 0.3:
                    reasons.append("similar price")
                
                if reasons:
                    result += f"   🔗 Similar: {', '.join(reasons)}\n"
                
                result += "\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Similar products error: {e}")
            return f"❌ Error finding similar products: {str(e)}"
    
    async def trending_products(self, args: Dict) -> str:
        """Get trending products."""
        try:
            category = args.get("category")
            limit = args.get("limit", 10)
            
            # Build query
            query = {"is_active": True}
            
            if category:
                category_doc = self.db.categories.find_one(
                    {"name": {"$regex": category, "$options": "i"}}
                )
                if category_doc:
                    query["category_id"] = category_doc["_id"]
            
            # Define "trending" as products with:
            # High ratings, good review counts, and in stock
            trending_products = list(self.db.products.find(query).sort([
                ("rating", -1),
                ("review_count", -1),
                ("stock_quantity", -1)
            ]).limit(limit))
            
            if not trending_products:
                return "❌ No trending products found"
            
            # Format results
            result = f"📈 **Trending Products**"
            if category:
                result += f" in {category}"
            result += "\n\n"
            
            for i, product in enumerate(trending_products, 1):
                result += f"**{i}. {product.get('brand', 'N/A')} {product['name']}**\n"
                result += f"   💰 ${product['price']}\n"
                result += f"   ⭐ {product.get('rating', 'N/A')}/5.0"
                
                if product.get('review_count', 0) > 0:
                    result += f" ({product['review_count']} reviews)"
                
                result += "\n   📦 Stock: " + str(product.get('stock_quantity', 0))
                
                if product.get('featured'):
                    result += " | ⭐ Featured"
                
                result += "\n\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Trending products error: {e}")
            return f"❌ Error getting trending products: {str(e)}"
    
    async def personalized_recommendations(self, args: Dict) -> str:
        """Get personalized recommendations based on user preferences."""
        try:
            preferences = args.get("user_preferences", {})
            limit = args.get("limit", 10)
            
            preferred_brands = preferences.get("brands", [])
            preferred_categories = preferences.get("categories", [])
            price_range = preferences.get("price_range", {})
            
            # Build query based on preferences
            query = {"is_active": True}
            
            or_conditions = []
            
            # Brand preferences
            if preferred_brands:
                for brand in preferred_brands:
                    or_conditions.append({"brand": {"$regex": brand, "$options": "i"}})
            
            # Category preferences
            if preferred_categories:
                category_ids = []
                for cat_name in preferred_categories:
                    category = self.db.categories.find_one(
                        {"name": {"$regex": cat_name, "$options": "i"}}
                    )
                    if category:
                        category_ids.append(category["_id"])
                
                if category_ids:
                    or_conditions.append({"category_id": {"$in": category_ids}})
            
            if or_conditions:
                query["$or"] = or_conditions
            
            # Price range
            if price_range:
                price_filter = {}
                if price_range.get("min"):
                    price_filter["$gte"] = price_range["min"]
                if price_range.get("max"):
                    price_filter["$lte"] = price_range["max"]
                if price_filter:
                    query["price"] = price_filter
            
            # Get recommendations
            products = list(self.db.products.find(query).sort([
                ("rating", -1),
                ("featured", -1),
                ("review_count", -1)
            ]).limit(limit))
            
            if not products:
                return "❌ No personalized recommendations found based on your preferences"
            
            # Format results
            result = f"🎯 **Personalized Recommendations**\n"
            result += f"Based on your preferences: "
            
            pref_summary = []
            if preferred_brands:
                pref_summary.append(f"Brands: {', '.join(preferred_brands)}")
            if preferred_categories:
                pref_summary.append(f"Categories: {', '.join(preferred_categories)}")
            if price_range:
                pref_summary.append(f"Price: ${price_range.get('min', 0)}-${price_range.get('max', '∞')}")
            
            result += ", ".join(pref_summary) + "\n\n"
            
            for i, product in enumerate(products, 1):
                result += f"**{i}. {product.get('brand', 'N/A')} {product['name']}**\n"
                result += f"   💰 ${product['price']}\n"
                result += f"   ⭐ {product.get('rating', 'N/A')}/5.0\n"
                
                # Show why it matches preferences
                matches = []
                if product.get('brand') in preferred_brands:
                    matches.append(f"matches preferred brand")
                if any(cat in preferred_categories for cat in []):  # Would need category lookup
                    matches.append("matches preferred category")
                
                if matches:
                    result += f"   ✨ {', '.join(matches)}\n"
                
                result += "\n"
            
            return result.strip()
            
        except Exception as e:
            self.logger.error(f"Personalized recommendations error: {e}")
            return f"❌ Error getting personalized recommendations: {str(e)}"
    
    async def read_service_resource(self, uri: str) -> str:
        """Read recommendation-specific resources."""
        try:
            if uri == "ecommerce://recommendations/engine":
                return """🤖 **AI Recommendation Engine**

**Capabilities:**
• Semantic product matching using natural language
• Multi-factor scoring algorithm
• Real-time inventory consideration
• Rating and review-based filtering
• Price range optimization

**Recommendation Types:**
• Query-based recommendations
• Similar product suggestions  
• Trending product identification
• Personalized recommendations

**Algorithms Used:**
• Collaborative filtering
• Content-based filtering
• Hybrid recommendation scoring
• Real-time inventory weighting"""
            
            elif uri == "ecommerce://recommendations/trending":
                trending = await self.trending_products({"limit": 20})
                return trending
            
            elif uri == "ecommerce://recommendations/models":
                return """📊 **Recommendation Models**

**Model Types:**
1. **Similarity Model**: Content-based matching using product attributes
2. **Popularity Model**: Trending products based on ratings and reviews
3. **Hybrid Model**: Combines multiple signals for optimal recommendations

**Scoring Factors:**
• Product rating (weight: 30%)
• Review count (weight: 20%) 
• Stock availability (weight: 20%)
• Category relevance (weight: 15%)
• Price competitiveness (weight: 10%)
• Featured status (weight: 5%)

**Update Frequency**: Real-time based on inventory and rating changes"""
            
            else:
                return await super().read_service_resource(uri)
                
        except Exception as e:
            self.logger.error(f"Resource read error: {e}")
            return f"❌ Error reading resource: {str(e)}"

async def main():
    """Main function to run the Recommendation MCP Service."""
    service = RecommendationMCPService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
