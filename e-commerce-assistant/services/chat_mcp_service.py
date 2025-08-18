#!/usr/bin/env python3
"""
Chat MCP Service
Handles conversational AI interactions, context management, and natural language processing.
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
logger = logging.getLogger("chat-service")

class ChatMCPService(BaseMCPService):
    """Chat service for conversational AI interactions."""
    
    def __init__(self):
        super().__init__("chat-service", "1.0.0")
        
        # Chat-specific state
        self.conversations: Dict[str, Dict] = {}
        self.context_memory: Dict[str, List[Dict]] = {}
        self.max_context_length = 50  # Maximum messages to keep in context
        
        # AI response templates and prompts
        self.system_prompts = {
            "general": "You are a helpful e-commerce assistant. Help users find products, get recommendations, and manage their orders.",
            "product_search": "Help the user find products based on their requirements. Ask clarifying questions if needed.",
            "recommendations": "Provide personalized product recommendations based on user preferences and history.",
            "order_help": "Assist with order-related questions, tracking, and support."
        }
    
    def setup_service(self):
        """Service-specific setup for chat service."""
        self.logger.info("Setting up Chat Service...")
    
    def register_tools(self):
        """Register chat service tools."""
        for tool in self.get_available_tools():
            self.tools[tool["name"]] = tool
    
    def register_resources(self):
        """Register chat service resources."""
        for resource in self.get_service_resources():
            self.resources[resource["uri"]] = resource
    
    def get_available_tools(self) -> List[Dict]:
        """Define chat service tools."""
        return [
            {
                "name": "start_conversation",
                "description": "Start a new conversation session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "conversation_type": {
                            "type": "string", 
                            "enum": ["general", "product_search", "recommendations", "order_help"],
                            "description": "Type of conversation"
                        },
                        "initial_message": {"type": "string", "description": "Initial user message"}
                    },
                    "required": ["user_id", "conversation_type"]
                }
            },
            {
                "name": "continue_conversation",
                "description": "Continue an existing conversation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "Conversation identifier"},
                        "user_message": {"type": "string", "description": "User's message"},
                        "context": {"type": "object", "description": "Additional context information"}
                    },
                    "required": ["conversation_id", "user_message"]
                }
            },
            {
                "name": "get_conversation_history",
                "description": "Get conversation history for a session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "Conversation identifier"},
                        "limit": {"type": "integer", "description": "Maximum number of messages to return", "default": 20}
                    },
                    "required": ["conversation_id"]
                }
            },
            {
                "name": "analyze_intent",
                "description": "Analyze user intent from a message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "User message to analyze"},
                        "context": {"type": "object", "description": "Conversation context"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "generate_response",
                "description": "Generate AI response based on conversation context",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "Conversation identifier"},
                        "user_message": {"type": "string", "description": "User's message"},
                        "intent": {"type": "string", "description": "Detected intent"},
                        "context_data": {"type": "object", "description": "Additional context from other services"}
                    },
                    "required": ["conversation_id", "user_message", "intent"]
                }
            },
            {
                "name": "end_conversation",
                "description": "End a conversation session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "Conversation identifier"},
                        "reason": {"type": "string", "description": "Reason for ending conversation"}
                    },
                    "required": ["conversation_id"]
                }
            }
        ]
    
    def get_service_resources(self) -> List[Dict]:
        """Define chat service resources."""
        return [
            {
                "uri": "chat://conversations",
                "name": "Active Conversations",
                "description": "List of active conversation sessions",
                "mimeType": "application/json"
            },
            {
                "uri": "chat://intents",
                "name": "Intent Classification",
                "description": "Available intent categories and classification rules",
                "mimeType": "application/json"
            },
            {
                "uri": "chat://templates",
                "name": "Response Templates",
                "description": "AI response templates and prompts",
                "mimeType": "application/json"
            }
        ]
    
    async def start_conversation(self, user_id: str, conversation_type: str, initial_message: Optional[str] = None) -> Dict:
        """Start a new conversation session."""
        try:
            conversation_id = str(uuid.uuid4())
            
            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "type": conversation_type,
                "started_at": datetime.now().isoformat(),
                "status": "active",
                "messages": [],
                "context": {
                    "system_prompt": self.system_prompts.get(conversation_type, self.system_prompts["general"]),
                    "user_preferences": {},
                    "session_data": {}
                }
            }
            
            # Add initial message if provided
            if initial_message:
                conversation["messages"].append({
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": initial_message,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Store conversation
            self.conversations[conversation_id] = conversation
            
            # Initialize context memory
            self.context_memory[conversation_id] = []
            
            logger.info(f"Started conversation {conversation_id} for user {user_id}")
            
            return {
                "conversation_id": conversation_id,
                "status": "started",
                "conversation_type": conversation_type,
                "system_prompt": conversation["context"]["system_prompt"]
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise
    
    async def continue_conversation(self, conversation_id: str, user_message: str, context: Optional[Dict] = None) -> Dict:
        """Continue an existing conversation."""
        try:
            if conversation_id not in self.conversations:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            
            if conversation["status"] != "active":
                raise ValueError(f"Conversation {conversation_id} is not active")
            
            # Add user message
            user_msg = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            
            conversation["messages"].append(user_msg)
            
            # Analyze intent
            intent_result = await self.analyze_intent(user_message, conversation["context"])
            
            # Generate response
            response_result = await self.generate_response(
                conversation_id, user_message, intent_result["intent"], context
            )
            
            # Add assistant message
            assistant_msg = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": response_result["response"],
                "timestamp": datetime.now().isoformat(),
                "intent": intent_result["intent"],
                "confidence": intent_result.get("confidence", 0.8),
                "actions": response_result.get("actions", [])
            }
            
            conversation["messages"].append(assistant_msg)
            
            # Update context memory
            self._update_context_memory(conversation_id, user_msg, assistant_msg)
            
            # Trim conversation if too long
            if len(conversation["messages"]) > self.max_context_length:
                conversation["messages"] = conversation["messages"][-self.max_context_length:]
            
            logger.info(f"Continued conversation {conversation_id} - Intent: {intent_result['intent']}")
            
            return {
                "message_id": assistant_msg["id"],
                "response": response_result["response"],
                "intent": intent_result["intent"],
                "confidence": intent_result.get("confidence", 0.8),
                "actions": response_result.get("actions", []),
                "conversation_status": "active"
            }
            
        except Exception as e:
            logger.error(f"Error continuing conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 20) -> Dict:
        """Get conversation history."""
        try:
            if conversation_id not in self.conversations:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            messages = conversation["messages"][-limit:] if limit else conversation["messages"]
            
            return {
                "conversation_id": conversation_id,
                "user_id": conversation["user_id"],
                "type": conversation["type"],
                "started_at": conversation["started_at"],
                "status": conversation["status"],
                "message_count": len(conversation["messages"]),
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history {conversation_id}: {e}")
            raise
    
    async def analyze_intent(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Analyze user intent from message."""
        try:
            message_lower = message.lower()
            
            # Simple intent classification based on keywords
            intent_patterns = {
                "product_search": ["find", "search", "looking for", "need", "want", "show me", "product"],
                "recommendations": ["recommend", "suggest", "advice", "similar", "like", "best"],
                "order_inquiry": ["order", "purchase", "buy", "cart", "checkout", "payment"],
                "order_status": ["status", "track", "where is", "delivery", "shipping", "when"],
                "support": ["help", "support", "problem", "issue", "complaint", "refund", "return"],
                "greeting": ["hello", "hi", "hey", "good morning", "good afternoon"],
                "goodbye": ["bye", "goodbye", "see you", "thanks", "thank you"]
            }
            
            # Calculate intent scores
            intent_scores = {}
            for intent, keywords in intent_patterns.items():
                score = sum(1 for keyword in keywords if keyword in message_lower)
                if score > 0:
                    intent_scores[intent] = score / len(keywords)
            
            # Determine primary intent
            if intent_scores:
                primary_intent = max(intent_scores, key=intent_scores.get)
                confidence = intent_scores[primary_intent]
            else:
                primary_intent = "general"
                confidence = 0.5
            
            # Extract entities (simple extraction)
            entities = self._extract_entities(message)
            
            return {
                "intent": primary_intent,
                "confidence": confidence,
                "all_intents": intent_scores,
                "entities": entities,
                "message_sentiment": self._analyze_sentiment(message)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"intent": "general", "confidence": 0.5, "entities": {}}
    
    def _extract_entities(self, message: str) -> Dict:
        """Extract entities from message (simplified)."""
        entities = {}
        
        # Price ranges
        import re
        price_pattern = r'\$?(\d+(?:\.\d{2})?)'
        prices = re.findall(price_pattern, message)
        if prices:
            entities["price_mentions"] = [float(p) for p in prices]
        
        # Common product categories
        categories = ["laptop", "phone", "book", "clothing", "shoes", "electronics", "home", "kitchen"]
        mentioned_categories = [cat for cat in categories if cat in message.lower()]
        if mentioned_categories:
            entities["categories"] = mentioned_categories
        
        # Colors
        colors = ["red", "blue", "green", "black", "white", "yellow", "purple", "orange", "pink"]
        mentioned_colors = [color for color in colors if color in message.lower()]
        if mentioned_colors:
            entities["colors"] = mentioned_colors
        
        return entities
    
    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ["good", "great", "excellent", "amazing", "love", "like", "perfect", "awesome"]
        negative_words = ["bad", "terrible", "awful", "hate", "dislike", "problem", "issue", "wrong"]
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    async def generate_response(self, conversation_id: str, user_message: str, intent: str, context_data: Optional[Dict] = None) -> Dict:
        """Generate AI response based on context."""
        try:
            conversation = self.conversations[conversation_id]
            actions = []
            
            # Generate response based on intent
            if intent == "product_search":
                response, search_actions = await self._handle_product_search(user_message, context_data)
                actions.extend(search_actions)
            
            elif intent == "recommendations":
                response, rec_actions = await self._handle_recommendations(user_message, conversation, context_data)
                actions.extend(rec_actions)
            
            elif intent == "order_inquiry" or intent == "order_status":
                response, order_actions = await self._handle_order_inquiry(user_message, conversation, context_data)
                actions.extend(order_actions)
            
            elif intent == "greeting":
                response = self._generate_greeting_response(conversation)
            
            elif intent == "goodbye":
                response = self._generate_goodbye_response()
                actions.append({"type": "end_conversation", "reason": "user_goodbye"})
            
            else:
                response = self._generate_general_response(user_message, conversation, context_data)
            
            return {
                "response": response,
                "actions": actions,
                "intent_handled": intent
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Could you please try rephrasing?",
                "actions": [],
                "intent_handled": "error"
            }
    
    async def _handle_product_search(self, message: str, context_data: Optional[Dict] = None) -> tuple:
        """Handle product search requests."""
        try:
            # Call product service for search
            search_result = await self.call_other_service(
                "product-service",
                "search_products",
                {"query": message, "limit": 5}
            )
            
            if search_result and "products" in search_result:
                products = search_result["products"]
                if products:
                    response = f"I found {len(products)} products for you:\n\n"
                    for i, product in enumerate(products[:3], 1):
                        response += f"{i}. **{product['name']}** - ${product['price']}\n"
                        response += f"   {product.get('description', 'No description available')[:100]}...\n\n"
                    
                    if len(products) > 3:
                        response += f"And {len(products) - 3} more products. Would you like to see more details or refine your search?"
                    
                    actions = [{"type": "product_search_completed", "products": products}]
                else:
                    response = "I couldn't find any products matching your search. Could you try different keywords or be more specific about what you're looking for?"
                    actions = [{"type": "search_refinement_needed"}]
            else:
                response = "I'm having trouble searching for products right now. Please try again in a moment."
                actions = []
            
            return response, actions
            
        except Exception as e:
            logger.error(f"Error handling product search: {e}")
            return "I encountered an error while searching for products. Please try again later.", []
    
    async def _handle_recommendations(self, message: str, conversation: Dict, context_data: Optional[Dict] = None) -> tuple:
        """Handle recommendation requests."""
        try:
            # Call recommendation service
            rec_result = await self.call_other_service(
                "recommendation-service",
                "get_recommendations",
                {"user_preferences": context_data or {}, "limit": 3}
            )
            
            if rec_result and "recommendations" in rec_result:
                products = rec_result["recommendations"]
                if products:
                    response = "Based on your preferences, I recommend these products:\n\n"
                    for i, product in enumerate(products, 1):
                        response += f"{i}. **{product['name']}** - ${product['price']}\n"
                        response += f"   Match Score: {product.get('match_score', 0):.1f}/10\n"
                        response += f"   {product.get('description', 'No description available')[:100]}...\n\n"
                    
                    actions = [{"type": "recommendations_provided", "products": products}]
                else:
                    response = "I'd be happy to make recommendations! Could you tell me more about what you're looking for or your preferences?"
                    actions = [{"type": "preference_collection_needed"}]
            else:
                response = "I'm having trouble generating recommendations right now. Could you tell me more about what you're interested in?"
                actions = []
            
            return response, actions
            
        except Exception as e:
            logger.error(f"Error handling recommendations: {e}")
            return "I encountered an error while generating recommendations. Please try again later.", []
    
    async def _handle_order_inquiry(self, message: str, conversation: Dict, context_data: Optional[Dict] = None) -> tuple:
        """Handle order-related inquiries."""
        try:
            user_id = conversation["user_id"]
            
            # Call order service for recent orders
            order_result = await self.call_other_service(
                "order-service",
                "recent_orders",
                {"user_id": user_id, "limit": 3}
            )
            
            if order_result and "orders" in order_result:
                orders = order_result["orders"]
                if orders:
                    response = f"Here are your recent orders:\n\n"
                    for i, order in enumerate(orders, 1):
                        response += f"{i}. Order #{order['order_id']} - ${order['total_amount']}\n"
                        response += f"   Status: {order['status'].title()}\n"
                        response += f"   Date: {order['order_date']}\n\n"
                    
                    response += "Is there a specific order you'd like to know more about?"
                    actions = [{"type": "order_info_provided", "orders": orders}]
                else:
                    response = "I don't see any recent orders for your account. Would you like to browse products or get recommendations?"
                    actions = [{"type": "no_orders_found"}]
            else:
                response = "I'm having trouble accessing your order information right now. Please try again in a moment."
                actions = []
            
            return response, actions
            
        except Exception as e:
            logger.error(f"Error handling order inquiry: {e}")
            return "I encountered an error while checking your orders. Please try again later.", []
    
    def _generate_greeting_response(self, conversation: Dict) -> str:
        """Generate a greeting response."""
        user_id = conversation["user_id"]
        responses = [
            f"Hello! I'm your e-commerce assistant. How can I help you today?",
            f"Hi there! I'm here to help you find products, get recommendations, or answer questions about your orders. What can I do for you?",
            f"Welcome! I can help you search for products, provide personalized recommendations, or assist with your orders. What would you like to do?"
        ]
        
        # Simple selection based on user ID hash
        return responses[hash(user_id) % len(responses)]
    
    def _generate_goodbye_response(self) -> str:
        """Generate a goodbye response."""
        responses = [
            "Thank you for using our service! Have a great day!",
            "Goodbye! Feel free to come back anytime if you need help.",
            "Thanks for chatting with me. See you next time!"
        ]
        
        import random
        return random.choice(responses)
    
    def _generate_general_response(self, message: str, conversation: Dict, context_data: Optional[Dict] = None) -> str:
        """Generate a general response."""
        return ("I understand you're looking for help. I can assist you with:\n"
                "• Searching for products\n"
                "• Getting personalized recommendations\n"
                "• Checking your orders\n"
                "• General shopping questions\n\n"
                "What would you like to do?")
    
    def _update_context_memory(self, conversation_id: str, user_msg: Dict, assistant_msg: Dict):
        """Update context memory for conversation."""
        if conversation_id not in self.context_memory:
            self.context_memory[conversation_id] = []
        
        memory = self.context_memory[conversation_id]
        
        # Add interaction to memory
        memory.append({
            "user_message": user_msg["content"],
            "assistant_response": assistant_msg["content"],
            "intent": assistant_msg.get("intent"),
            "timestamp": user_msg["timestamp"],
            "entities": user_msg.get("context", {})
        })
        
        # Keep only recent interactions
        if len(memory) > self.max_context_length // 2:
            memory[:] = memory[-(self.max_context_length // 2):]
    
    async def end_conversation(self, conversation_id: str, reason: Optional[str] = None) -> Dict:
        """End a conversation session."""
        try:
            if conversation_id not in self.conversations:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            conversation["status"] = "ended"
            conversation["ended_at"] = datetime.now().isoformat()
            conversation["end_reason"] = reason or "manual"
            
            # Clean up context memory
            if conversation_id in self.context_memory:
                del self.context_memory[conversation_id]
            
            logger.info(f"Ended conversation {conversation_id} - Reason: {reason}")
            
            return {
                "conversation_id": conversation_id,
                "status": "ended",
                "duration_messages": len(conversation["messages"]),
                "end_reason": reason or "manual"
            }
            
        except Exception as e:
            logger.error(f"Error ending conversation {conversation_id}: {e}")
            raise

async def main():
    """Main function to run the chat service."""
    service = ChatMCPService()
    await service.run()

if __name__ == "__main__":
    asyncio.run(main())
