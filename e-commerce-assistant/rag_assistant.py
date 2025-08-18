#!/usr/bin/env python3
"""
E-commerce RAG Assistant with LangChain, Vector Search, and MongoDB
Provides intelligent product search, recommendations, and customer support using RAG.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# LangChain imports
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun

# Database imports
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EcommerceVectorStore:
    """Manages vector storage and embeddings for e-commerce products."""
    
    def __init__(self, persist_directory: str = "./vector_store"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def create_vector_store(self, documents: List[Document]):
        """Create vector store from documents."""
        try:
            # Split documents into chunks
            splits = self.text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Persist the store
            self.vector_store.persist()
            logger.info(f"Created vector store with {len(splits)} document chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            return False
    
    def load_vector_store(self):
        """Load existing vector store."""
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info("Loaded existing vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False
    
    def search_similar(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return []
        
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return docs
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

def create_mongodb_product_tool(mongo_client, db_name: str):
    """Create a tool for querying MongoDB products."""
    db = mongo_client[db_name]
    
    def search_products(query: str) -> str:
        """Search for products in MongoDB database."""
        try:
            # Parse query for different types of searches
            results = []
            search_term = query.lower().strip()
            
            # Handle category-specific searches
            category_mappings = {
                'smartphone': ['phone', 'iphone', 'samsung', 'mobile'],
                'laptop': ['macbook', 'computer', 'notebook'],
                'headphone': ['airpods', 'audio', 'earphone'],
                'watch': ['apple watch', 'smartwatch'],
                'tablet': ['ipad', 'tablet']
            }
            
            # Find relevant category
            search_terms = [search_term]
            for category, keywords in category_mappings.items():
                if any(keyword in search_term for keyword in keywords) or category in search_term:
                    search_terms.extend(keywords)
                    search_terms.append(category)
            
            # Remove duplicates
            search_terms = list(set(search_terms))
            
            # Try text search first
            for term in search_terms:
                products = list(db.products.find({
                    "$or": [
                        {"name": {"$regex": term, "$options": "i"}},
                        {"description": {"$regex": term, "$options": "i"}},
                        {"brand": {"$regex": term, "$options": "i"}},
                        {"category": {"$regex": term, "$options": "i"}}
                    ]
                }).limit(10))
                
                if products:
                    break
            
            # If no specific products found, get all products
            if not products:
                products = list(db.products.find().limit(5))
            
            for product in products:
                results.append({
                    "name": product["name"],
                    "price": product["price"],
                    "brand": product.get("brand", "N/A"),
                    "description": product["description"][:150] + "...",
                    "stock": product.get("stock_quantity", 0),
                    "rating": product.get("rating", "N/A")
                })
            
            if results:
                formatted_results = []
                for r in results:
                    formatted_results.append(f"• {r['brand']} {r['name']} - ${r['price']} (Stock: {r['stock']}, Rating: {r['rating']})")
                return f"Found {len(results)} products:\n" + "\n".join(formatted_results)
            else:
                return "No products found matching your query."
                
        except Exception as e:
            return f"Error searching products: {e}"
    
    return Tool(
        name="mongodb_product_search",
        description="Search for products in MongoDB database by name, category, brand, or price range",
        func=search_products
    )

def create_mongodb_order_tool(mongo_client, db_name: str):
    """Create a tool for querying MongoDB orders."""
    db = mongo_client[db_name]
    
    def search_orders(query: str) -> str:
        """Search for order information."""
        try:
            results = []
            
            # Get recent orders
            if 'recent' in query.lower() or 'latest' in query.lower():
                orders = list(db.orders.find({}).sort("created_at", -1).limit(10))
                
                for order in orders:
                    results.append({
                        "order_number": order["order_number"],
                        "status": order["status"],
                        "total": order["total_amount"],
                        "date": order["created_at"].strftime("%Y-%m-%d")
                    })
            
            # Get order statistics
            elif 'stats' in query.lower() or 'statistics' in query.lower():
                total_orders = db.orders.count_documents({})
                total_revenue = list(db.orders.aggregate([
                    {"$match": {"status": {"$ne": "cancelled"}}},
                    {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
                ]))
                
                results = {
                    "total_orders": total_orders,
                    "total_revenue": total_revenue[0]["total"] if total_revenue else 0,
                    "avg_order_value": total_revenue[0]["total"] / total_orders if total_revenue and total_orders > 0 else 0
                }
            
            return str(results) if results else "No order information found."
            
        except Exception as e:
            return f"Error searching orders: {e}"
    
    return Tool(
        name="mongodb_order_search",
        description="Search for order information, order status, and customer order history",
        func=search_orders
    )

class EcommerceRAGAssistant:
    """Main RAG Assistant for E-commerce with LangChain and MongoDB."""
    
    def __init__(self):
        self.mongo_client = None
        self.db = None
        self.vector_store_manager = None
        self.llm = None
        self.memory = None
        self.agent = None
        self.setup_complete = False
        
        # Initialize components
        self._setup_database()
        self._setup_llm()
        self._setup_vector_store()
        self._setup_agent()
    
    def _setup_database(self):
        """Setup MongoDB connection."""
        try:
            mongo_uri = os.getenv('MONGO_DB_URI', 'mongodb://localhost:27017')
            db_name = os.getenv('MONGODB_DATABASE', 'ecommerce_assistant')
            
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[db_name]
            
            logger.info(f"Connected to MongoDB: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _setup_llm(self):
        """Setup LangChain LLM."""
        try:
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000
            )
            
            # Setup conversation memory
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=10,
                return_messages=True
            )
            
            logger.info("LLM and memory initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup LLM: {e}")
            raise
    
    def _setup_vector_store(self):
        """Setup vector store with product data."""
        try:
            self.vector_store_manager = EcommerceVectorStore()
            
            # Try to load existing vector store
            if not self.vector_store_manager.load_vector_store():
                # Create new vector store from MongoDB data
                logger.info("Creating new vector store from product data...")
                self._populate_vector_store()
            
            logger.info("Vector store ready")
            
        except Exception as e:
            logger.error(f"Failed to setup vector store: {e}")
            raise
    
    def _populate_vector_store(self):
        """Populate vector store with product data from MongoDB."""
        try:
            # Get all products from MongoDB
            products = list(self.db.products.find({"is_active": True}))
            
            documents = []
            for product in products:
                # Create document content
                content = f"""
                Product: {product['name']}
                Brand: {product.get('brand', 'N/A')}
                Price: ${product['price']}
                Description: {product['description']}
                Category: {product.get('category_id', 'N/A')}
                Stock: {product.get('stock_quantity', 0)}
                Rating: {product.get('rating', 'N/A')}/5.0
                Reviews: {product.get('review_count', 0)} reviews
                """
                
                # Create metadata
                metadata = {
                    "product_id": str(product['_id']),
                    "name": product['name'],
                    "brand": product.get('brand', ''),
                    "price": product['price'],
                    "category": str(product.get('category_id', '')),
                    "type": "product"
                }
                
                documents.append(Document(page_content=content, metadata=metadata))
            
            # Add category information
            categories = list(self.db.categories.find())
            for category in categories:
                content = f"""
                Category: {category['name']}
                Description: {category['description']}
                Type: Product Category
                """
                
                metadata = {
                    "category_id": str(category['_id']),
                    "name": category['name'],
                    "type": "category"
                }
                
                documents.append(Document(page_content=content, metadata=metadata))
            
            # Create vector store
            self.vector_store_manager.create_vector_store(documents)
            logger.info(f"Created vector store with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to populate vector store: {e}")
            raise
    
    def _vector_search_tool(self, query: str) -> str:
        """Vector search tool function for agent"""
        try:
            # Check if vector manager is properly initialized
            if not hasattr(self, 'vector_manager') or self.vector_manager is None:
                logger.error("Vector manager not initialized")
                return "Vector search is currently unavailable. Please try the product search instead."
            
            if not hasattr(self.vector_manager, 'vector_store') or self.vector_manager.vector_store is None:
                logger.error("Vector store not properly initialized")
                return "Vector search is currently unavailable. Please try the product search instead."
            
            # Perform similarity search
            docs = self.vector_manager.vector_store.similarity_search(query, k=5)
            if not docs:
                return "No similar products found for your query. Try searching with product search instead."
            
            results = []
            for doc in docs:
                # Extract product info from metadata
                if doc.metadata.get('type') == 'product':
                    name = doc.metadata.get('name', 'Unknown Product')
                    brand = doc.metadata.get('brand', '')
                    price = doc.metadata.get('price', 'N/A')
                    
                    if brand:
                        results.append(f"• {brand} {name} - ${price}")
                    else:
                        results.append(f"• {name} - ${price}")
                else:
                    # For category or general content
                    content = doc.page_content.strip()[:100]
                    results.append(f"• {content}")
            
            if results:
                return "Similar products found:\n" + "\n".join(results[:5])
            else:
                return "No relevant products found for your query. Try the product search instead."
                
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return f"Vector search unavailable. Try product search instead. Error: {str(e)}"
    
    def _setup_agent(self):
        """Setup LangChain agent with tools."""
        try:
            # Create tools
            tools = [
                create_mongodb_product_tool(self.mongo_client, self.db.name),
                create_mongodb_order_tool(self.mongo_client, self.db.name),
                Tool(
                    name="vector_search",
                    description="Search for products using semantic similarity",
                    func=self._vector_search_tool
                )
            ]
            
            # Initialize agent
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate",
                handle_parsing_errors=True
            )
            
            logger.info("Agent initialized with tools")
            self.setup_complete = True
            
        except Exception as e:
            logger.error(f"Failed to setup agent: {e}")
            raise
    
    def _vector_search_tool(self, query: str) -> str:
        """Vector search tool function."""
        try:
            # Search similar documents
            docs = self.vector_store_manager.search_similar(query, k=3)
            
            if not docs:
                return "No similar products found."
            
            results = []
            for doc in docs:
                metadata = doc.metadata
                results.append({
                    "name": metadata.get("name", "Unknown"),
                    "price": metadata.get("price", "N/A"),
                    "brand": metadata.get("brand", "N/A"),
                    "type": metadata.get("type", "product"),
                    "content": doc.page_content[:300] + "..."
                })
            
            return f"Found {len(results)} similar items: " + str(results)
            
        except Exception as e:
            return f"Vector search failed: {e}"
    
    def chat(self, message: str) -> str:
        """Main chat interface."""
        if not self.setup_complete:
            return "❌ Assistant not properly initialized. Please check the logs."
        
        try:
            # Use agent to process the message
            response = self.agent.run(message)
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Sorry, I encountered an error: {e}"
    
    def get_product_recommendations(self, user_query: str, limit: int = 5) -> List[Dict]:
        """Get product recommendations based on user query."""
        try:
            # Use vector search for semantic similarity
            docs = self.vector_store_manager.search_similar(user_query, k=limit)
            
            recommendations = []
            for doc in docs:
                if doc.metadata.get("type") == "product":
                    # Get full product details from MongoDB
                    product_id = ObjectId(doc.metadata["product_id"])
                    product = self.db.products.find_one({"_id": product_id})
                    
                    if product:
                        recommendations.append({
                            "name": product["name"],
                            "price": product["price"],
                            "brand": product.get("brand", "N/A"),
                            "description": product["description"][:200] + "...",
                            "rating": product.get("rating", "N/A"),
                            "stock": product.get("stock_quantity", 0)
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return []
    
    def close(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Database connections closed")

def main():
    """Demo the RAG assistant."""
    try:
        # Initialize assistant
        print("🚀 Initializing E-commerce RAG Assistant...")
        assistant = EcommerceRAGAssistant()
        
        print("\n✅ Assistant ready! Type 'quit' to exit.\n")
        
        # Interactive chat loop
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if not user_input:
                continue
            
            print("Assistant: ", end="")
            response = assistant.chat(user_input)
            print(response)
            print()
    
    except Exception as e:
        print(f"❌ Error initializing assistant: {e}")
    
    finally:
        if 'assistant' in locals():
            assistant.close()

if __name__ == "__main__":
    main()
