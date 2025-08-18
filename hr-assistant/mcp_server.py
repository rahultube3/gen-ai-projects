# HR Assistant MCP Server
# Model Context Protocol server for HR document queries and management

import json
import logging
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

# MCP imports
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Our RAG system
from rag_system import HRAssistantRAG, RAGConfig, RAGQuery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRAssistantMCPServer:
    """
    MCP Server for HR Assistant
    Provides tools for document search, RAG queries, and system management
    """
    
    def __init__(self):
        self.server = Server("hr-assistant")
        self.rag_system = None
        self._setup_tools()
        self._setup_handlers()
        
    def _setup_tools(self):
        """Define MCP tools for HR Assistant."""
        
        # Tool 1: Document Search
        @self.server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return [
                types.Tool(
                    name="search_hr_documents",
                    description="Search HR documents using vector similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for HR documents"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of documents to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="ask_hr_question",
                    description="Ask a question using RAG (Retrieval-Augmented Generation) with LLM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to ask the HR Assistant"
                            },
                            "max_sources": {
                                "type": "integer",
                                "description": "Maximum number of source documents to use (default: 5)",
                                "default": 5
                            },
                            "include_sources": {
                                "type": "boolean",
                                "description": "Whether to include source documents in response (default: true)",
                                "default": True
                            }
                        },
                        "required": ["question"]
                    }
                ),
                types.Tool(
                    name="get_hr_system_stats",
                    description="Get statistics about the HR document system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                types.Tool(
                    name="list_hr_documents",
                    description="List all available HR documents in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
    
    def _setup_handlers(self):
        """Set up tool execution handlers."""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool execution."""
            
            # Initialize RAG system if not done
            if self.rag_system is None:
                try:
                    config = RAGConfig()
                    self.rag_system = HRAssistantRAG(config)
                    logger.info("✅ RAG system initialized in MCP server")
                except Exception as e:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Failed to initialize RAG system: {str(e)}"
                    )]
            
            try:
                if name == "search_hr_documents":
                    return await self._handle_search_documents(arguments)
                elif name == "ask_hr_question":
                    return await self._handle_ask_question(arguments)
                elif name == "get_hr_system_stats":
                    return await self._handle_get_stats(arguments)
                elif name == "list_hr_documents":
                    return await self._handle_list_documents(arguments)
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"❌ Error executing tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )]
    
    async def _handle_search_documents(self, arguments: dict) -> list[types.TextContent]:
        """Handle document search requests."""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        
        if not query:
            return [types.TextContent(
                type="text",
                text="❌ Query parameter is required for document search"
            )]
        
        logger.info(f"🔍 MCP: Searching documents for '{query}'")
        
        # Retrieve documents
        documents = self.rag_system.retrieve_relevant_documents(query, top_k)
        
        # Format results
        result_text = f"📋 Found {len(documents)} relevant documents for '{query}':\n\n"
        
        for doc in documents:
            result_text += f"📄 **{doc['title']}** (Chunk {doc['chunk_index']})\n"
            result_text += f"   🎯 Relevance: {doc['similarity_score']:.3f}\n"
            result_text += f"   📝 Content: {doc['text'][:200]}...\n"
            result_text += f"   🆔 Doc ID: {doc['doc_id']}\n\n"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_ask_question(self, arguments: dict) -> list[types.TextContent]:
        """Handle RAG-based question answering."""
        question = arguments.get("question", "")
        max_sources = arguments.get("max_sources", 5)
        include_sources = arguments.get("include_sources", True)
        
        if not question:
            return [types.TextContent(
                type="text",
                text="❌ Question parameter is required"
            )]
        
        logger.info(f"🤖 MCP: Processing RAG question '{question}'")
        
        # Get RAG response
        rag_response = self.rag_system.answer_query(
            query=question,
            max_sources=max_sources,
            include_sources=include_sources
        )
        
        # Format response
        result_text = f"🎯 **Question:** {question}\n\n"
        result_text += f"🤖 **Answer:**\n{rag_response.answer}\n\n"
        
        if include_sources and rag_response.sources:
            result_text += f"📚 **Sources ({len(rag_response.sources)} documents):**\n"
            for source in rag_response.sources:
                result_text += f"   📄 {source['title']} (Relevance: {source['similarity_score']:.3f})\n"
        
        result_text += f"\n⚡ Processed in {rag_response.processing_time_ms:.0f}ms using {rag_response.model_used}"
        
        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_get_stats(self, arguments: dict) -> list[types.TextContent]:
        """Handle system statistics requests."""
        logger.info("📊 MCP: Getting system statistics")
        
        # Get vector store stats
        stats = self.rag_system.vector_store.get_stats()
        
        result_text = f"""📊 **HR Assistant System Statistics**

🗄️  **Database:** {stats['database']}
📋 **Collection:** {stats['collection']}
📄 **Total Documents:** {stats['total_vectors']} chunks
📐 **Vector Dimension:** {stats['dimension']}
💾 **Storage Size:** {stats['storage_size_mb']:.2f} MB
📚 **Unique Documents:** {stats['unique_documents']}

🤖 **LLM Model:** {self.rag_system.config.llm_model}
🔧 **RAG Configuration:**
   - Top-K Retrieval: {self.rag_system.config.retrieval_top_k}
   - Max Tokens: {self.rag_system.config.max_tokens}
   - Temperature: {self.rag_system.config.temperature}

⏰ **Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"""

        return [types.TextContent(type="text", text=result_text)]
    
    async def _handle_list_documents(self, arguments: dict) -> list[types.TextContent]:
        """Handle document listing requests."""
        logger.info("📋 MCP: Listing available documents")
        
        try:
            # Get unique document titles from MongoDB
            pipeline = [
                {"$group": {"_id": "$title", "count": {"$sum": 1}, "latest": {"$max": "$created_at"}}},
                {"$sort": {"latest": -1}}
            ]
            
            cursor = self.rag_system.vector_store.collection.aggregate(pipeline)
            documents = list(cursor)
            
            result_text = f"📚 **Available HR Documents ({len(documents)} total):**\n\n"
            
            for doc in documents:
                result_text += f"📄 **{doc['_id']}**\n"
                result_text += f"   📊 Chunks: {doc['count']}\n"
                result_text += f"   📅 Last Updated: {doc['latest'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if not documents:
                result_text = "📭 No documents found in the system. Upload documents using the ingestion system."
            
        except Exception as e:
            result_text = f"❌ Error retrieving document list: {str(e)}"
        
        return [types.TextContent(type="text", text=result_text)]

async def main():
    """Run the HR Assistant MCP server."""
    logger.info("🚀 Starting HR Assistant MCP Server")
    
    # Create and configure server
    hr_server = HRAssistantMCPServer()
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await hr_server.server.run(
            read_stream,
            write_stream,
            hr_server.server.create_initialization_options()
        )

if __name__ == "__main__":
    print("🎯 HR Assistant MCP Server")
    print("📡 Model Context Protocol server for HR document queries")
    print("🔧 Available tools:")
    print("   - search_hr_documents: Vector search in HR documents")
    print("   - ask_hr_question: RAG-based question answering")
    print("   - get_hr_system_stats: System statistics and health")
    print("   - list_hr_documents: List available documents")
    print("\n🚀 Starting server...")
    
    asyncio.run(main())
