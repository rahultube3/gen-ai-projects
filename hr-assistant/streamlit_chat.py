# HR Assistant Streamlit Web Chat Interface with Guardrails
# Interactive web application for HR document queries with RAG system and content protection

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Import guardrails for client-side validation
try:
    from guardrails import validate_query, validate_response, get_violations_summary
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="HR Assistant Chat",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #9c27b0;
    }
    .source-card {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #ff9800;
        font-size: 0.9rem;
    }
    .metrics-card {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .sidebar-section {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
RAG_API_URL = "http://localhost:8001"
COMPREHENSIVE_API_URL = "http://localhost:8002"

class HRChatInterface:
    """HR Assistant Chat Interface for Streamlit."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'conversation_id' not in st.session_state:
            st.session_state.conversation_id = f"chat_{int(time.time())}"
        if 'system_stats' not in st.session_state:
            st.session_state.system_stats = {}
        if 'processing_times' not in st.session_state:
            st.session_state.processing_times = []
        if 'query_cache' not in st.session_state:
            st.session_state.query_cache = {}
        if 'cache_hits' not in st.session_state:
            st.session_state.cache_hits = 0
        if 'cache_misses' not in st.session_state:
            st.session_state.cache_misses = 0
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for cache key generation."""
        return query.lower().strip().replace("?", "").replace(".", "")
    
    def get_cache_key(self, query: str, max_sources: int, use_rag: bool) -> str:
        """Generate cache key for query."""
        normalized = self.normalize_query(query)
        return f"{normalized}|{max_sources}|{use_rag}"
    
    def check_cache(self, query: str, max_sources: int, use_rag: bool) -> Optional[Dict[str, Any]]:
        """Check if query result is in cache."""
        cache_key = self.get_cache_key(query, max_sources, use_rag)
        
        if cache_key in st.session_state.query_cache:
            cached_data = st.session_state.query_cache[cache_key]
            
            # Check if cache entry is still fresh (within 30 minutes)
            cache_time = cached_data.get('timestamp', 0)
            if time.time() - cache_time < 1800:  # 30 minutes
                st.session_state.cache_hits += 1
                return cached_data
            else:
                # Remove expired cache entry
                del st.session_state.query_cache[cache_key]
        
        st.session_state.cache_misses += 1
        return None
    
    def update_cache(self, query: str, max_sources: int, use_rag: bool, result: Dict[str, Any]):
        """Update cache with new query result."""
        cache_key = self.get_cache_key(query, max_sources, use_rag)
        
        # Limit cache size to 50 entries
        if len(st.session_state.query_cache) >= 50:
            # Remove oldest entry
            oldest_key = min(st.session_state.query_cache.keys(), 
                           key=lambda k: st.session_state.query_cache[k].get('timestamp', 0))
            del st.session_state.query_cache[oldest_key]
        
        # Add to cache with timestamp
        cached_result = result.copy()
        cached_result['timestamp'] = time.time()
        cached_result['from_cache'] = True
        st.session_state.query_cache[cache_key] = cached_result
    
    def check_api_health(self, api_url: str) -> Dict[str, Any]:
        """Check if the API is healthy and accessible."""
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "data": response.json()}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics from the API."""
        try:
            response = requests.get(f"{RAG_API_URL}/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except:
            return {}
    
    def send_rag_query(self, query: str, max_sources: int = 5) -> Dict[str, Any]:
        """Send query to RAG system and get response."""
        try:
            payload = {
                "query": query,
                "max_sources": max_sources,
                "include_sources": True,
                "context_window": 3000
            }
            
            response = requests.post(
                f"{RAG_API_URL}/ask",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def send_chat_message(self, message: str, use_rag: bool = True) -> Dict[str, Any]:
        """Send message to comprehensive chat API."""
        try:
            payload = {
                "message": message,
                "conversation_id": st.session_state.conversation_id,
                "use_rag": use_rag,
                "max_sources": 5
            }
            
            response = requests.post(
                f"{COMPREHENSIVE_API_URL}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def display_message(self, role: str, content: str, sources: Optional[List[Dict]] = None, 
                       processing_time: Optional[float] = None, model_used: Optional[str] = None):
        """Display a chat message with styling."""
        if role == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🤖 HR Assistant:</strong><br>
                {content}
            </div>
            """, unsafe_allow_html=True)
            
            # Display metadata if available
            if processing_time or model_used:
                metadata_info = []
                if processing_time:
                    metadata_info.append(f"⚡ {processing_time:.1f}ms")
                if model_used:
                    metadata_info.append(f"🧠 {model_used}")
                
                st.caption(" | ".join(metadata_info))
            
            # Display sources if available
            if sources:
                with st.expander(f"📚 Sources ({len(sources)} documents)", expanded=False):
                    for i, source in enumerate(sources[:3]):  # Show top 3 sources
                        st.markdown(f"""
                        <div class="source-card">
                            <strong>📄 {source.get('title', 'Unknown Document')}</strong> 
                            (Relevance: {source.get('similarity_score', 0):.3f})<br>
                            <small>{source.get('text_preview', source.get('text', ''))[:200]}...</small>
                        </div>
                        """, unsafe_allow_html=True)
    
    def display_sidebar(self):
        """Display sidebar with system information and controls."""
        with st.sidebar:
            st.markdown("## 🏢 HR Assistant")
            st.markdown("### System Status")
            
            # Check API health
            rag_health = self.check_api_health(RAG_API_URL)
            comprehensive_health = self.check_api_health(COMPREHENSIVE_API_URL)
            
            # Display health status
            if rag_health["status"] == "healthy":
                st.success("🟢 RAG API: Online")
            else:
                st.error(f"🔴 RAG API: {rag_health.get('error', 'Offline')}")
            
            if comprehensive_health["status"] == "healthy":
                st.success("🟢 Chat API: Online")
            else:
                st.warning(f"🟡 Chat API: {comprehensive_health.get('error', 'Offline')}")
            
            st.markdown("---")
            
            # System statistics
            st.markdown("### 📊 System Stats")
            stats = self.get_system_stats()
            
            if stats:
                if 'database' in stats:
                    db_stats = stats['database']
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Documents", db_stats.get('total_vectors', 0))
                    with col2:
                        st.metric("Storage", f"{db_stats.get('storage_size_mb', 0):.1f} MB")
                
                if 'llm' in stats:
                    llm_stats = stats['llm']
                    st.info(f"🧠 Model: {llm_stats.get('model', 'N/A')}")
            
            st.markdown("---")
            
            # Chat settings
            st.markdown("### ⚙️ Chat Settings")
            
            max_sources = st.slider(
                "Max Sources",
                min_value=1,
                max_value=10,
                value=5,
                help="Maximum number of source documents to retrieve"
            )
            
            use_rag = st.checkbox(
                "Use RAG",
                value=True,
                help="Enable Retrieval-Augmented Generation for better answers"
            )
            
            st.markdown("---")
            
            # Guardrails monitoring
            if GUARDRAILS_AVAILABLE:
                st.markdown("### 🛡️ Content Protection")
                try:
                    # Get violations summary
                    response = requests.get(f"{COMPREHENSIVE_API_URL}/guardrails/summary?hours=24", timeout=5)
                    if response.status_code == 200:
                        violations_data = response.json().get("data", {})
                        total_violations = violations_data.get("total_violations", 0)
                        
                        if total_violations > 0:
                            st.warning(f"⚠️ {total_violations} violations (24h)")
                            
                            # Show breakdown
                            by_type = violations_data.get("by_type", {})
                            for vtype, count in by_type.items():
                                st.caption(f"• {vtype.replace('_', ' ').title()}: {count}")
                        else:
                            st.success("✅ No violations (24h)")
                    else:
                        st.info("📊 Violations data unavailable")
                except:
                    st.caption("🛡️ Guardrails monitoring active")
            else:
                st.warning("⚠️ Guardrails unavailable")
            
            st.markdown("---")
            
            # Cache management
            st.markdown("### ⚡ Memory Cache")
            
            total_queries = st.session_state.cache_hits + st.session_state.cache_misses
            if total_queries > 0:
                cache_hit_rate = (st.session_state.cache_hits / total_queries * 100)
                st.metric("Hit Rate", f"{cache_hit_rate:.1f}%")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Cached", len(st.session_state.query_cache))
                with col2:
                    st.metric("Hits", st.session_state.cache_hits)
            else:
                st.info("No queries processed yet")
            
            # Clear cache button
            if st.button("🗑️ Clear Cache", help="Clear query cache to free memory"):
                st.session_state.query_cache = {}
                st.session_state.cache_hits = 0
                st.session_state.cache_misses = 0
                st.success("Cache cleared!")
                st.rerun()
            
            st.markdown("---")
            
            # Clear chat
            if st.button("🗑️ Clear Chat", type="secondary"):
                st.session_state.messages = []
                st.session_state.conversation_id = f"chat_{int(time.time())}"
                st.session_state.processing_times = []
                st.session_state.query_cache = {}
                st.session_state.cache_hits = 0
                st.session_state.cache_misses = 0
                st.rerun()
            
            return max_sources, use_rag
    
    def display_performance_metrics(self):
        """Display performance metrics and charts."""
        st.markdown("### 📈 Performance Metrics")
        
        # Cache statistics
        total_queries = st.session_state.cache_hits + st.session_state.cache_misses
        cache_hit_rate = (st.session_state.cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Cache Hit Rate", f"{cache_hit_rate:.1f}%", 
                     delta=f"{st.session_state.cache_hits} hits")
        
        with col2:
            st.metric("Cached Queries", len(st.session_state.query_cache),
                     delta=f"Max: 50")
        
        with col3:
            st.metric("Total Queries", total_queries)
        
        if st.session_state.processing_times:
            st.markdown("#### Response Times")
            
            col1, col2, col3 = st.columns(3)
            
            times = st.session_state.processing_times
            
            with col1:
                avg_time = sum(times) / len(times)
                st.metric("Avg Response Time", f"{avg_time:.1f}ms")
            
            with col2:
                min_time = min(times)
                st.metric("Fastest Response", f"{min_time:.1f}ms")
            
            with col3:
                max_time = max(times)
                st.metric("Slowest Response", f"{max_time:.1f}ms")
            
            # Response time chart
            if len(times) > 1:
                df = pd.DataFrame({
                    'Query': range(1, len(times) + 1),
                    'Response Time (ms)': times
                })
                
                fig = px.line(
                    df, 
                    x='Query', 
                    y='Response Time (ms)',
                    title='Response Time Trend',
                    markers=True
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    def main_chat_interface(self):
        """Main chat interface."""
        st.markdown('<h1 class="main-header">🏢 HR Assistant Chat</h1>', unsafe_allow_html=True)
        
        # Sidebar
        max_sources, use_rag = self.display_sidebar()
        
        # Main chat area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 💬 Chat with HR Assistant")
            
            # Display chat messages
            chat_container = st.container()
            
            with chat_container:
                for message in st.session_state.messages:
                    self.display_message(
                        role=message["role"],
                        content=message["content"],
                        sources=message.get("sources"),
                        processing_time=message.get("processing_time"),
                        model_used=message.get("model_used")
                    )
            
            # Chat input
            st.markdown("---")
            
            # Handle example query
            query = ""
            auto_send = False
            
            if hasattr(st.session_state, 'example_query'):
                query = st.session_state.example_query
                auto_send = True
                del st.session_state.example_query
            else:
                query = st.text_input(
                    "Ask a question about HR policies, benefits, or procedures:",
                    placeholder="e.g., What are the health insurance options?",
                    key="chat_input"
                )
            
            # Send button
            col_send, col_clear = st.columns([3, 1])
            
            with col_send:
                send_button = st.button("🚀 Send", type="primary", use_container_width=True)
            
            # Example questions below the chat input
    
            st.markdown(" 💡 Click any question below to use it:")
            
            example_queries = [
                "What are the health insurance benefits?",
                "Tell me about dependent care benefits",
                "How does the performance review process work?",
                "What is the company's acquisition strategy?",
                "Tell me about salary bands",
                "What confidential information is protected?"
            ]
            
            # Create columns for example questions (2 per row)
            cols = st.columns(2)
            for i, example_query in enumerate(example_queries):
                with cols[i % 2]:
                    if st.button(f"💬 {example_query}", key=f"main_example_{hash(example_query)}", use_container_width=True):
                        st.session_state.example_query = example_query
                        st.rerun()
            
            st.markdown("---")
            
            # Process query if send button clicked or example query selected
            if (send_button and query) or (auto_send and query):
                # Client-side guardrails validation
                if GUARDRAILS_AVAILABLE:
                    is_allowed, violations = validate_query(query)
                    if not is_allowed:
                        st.error("⚠️ Your message contains content that violates our usage policy. Please rephrase your question appropriately.")
                        violation_messages = [v.message for v in violations]
                        with st.expander("ℹ️ Policy Violation Details"):
                            for msg in violation_messages:
                                st.warning(f"• {msg}")
                        return
                
                # Add user message
                user_message = {
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now()
                }
                st.session_state.messages.append(user_message)
                
                # Show user message immediately
                self.display_message("user", query)
                
                # Check cache first
                cached_result = self.check_cache(query, max_sources, use_rag)
                
                if cached_result:
                    # Use cached result
                    st.info("⚡ Retrieved from cache for faster response")
                    data = cached_result
                    
                    # Extract response data from cache
                    if use_rag:
                        answer = data["answer"]
                        sources = data.get("sources", [])
                        processing_time = 5  # Cached responses are super fast
                        model_used = data.get("model_used", "Cached")
                    else:
                        answer = data["response"]
                        sources = data.get("sources", [])
                        processing_time = 5
                        model_used = "Cached"
                    
                else:
                    # Show loading indicator for new queries
                    with st.spinner("🤖 HR Assistant is thinking..."):
                        # Send to appropriate API based on settings
                        if use_rag:
                            result = self.send_rag_query(query, max_sources)
                        else:
                            result = self.send_chat_message(query, use_rag=False)
                        
                        if result["success"]:
                            data = result["data"]
                            
                            # Cache the result for future use
                            self.update_cache(query, max_sources, use_rag, data)
                            
                            # Extract response data based on API used
                            if use_rag:
                                answer = data["answer"]
                                sources = data.get("sources", [])
                                processing_time = data.get("processing_time_ms", 0)
                                model_used = data.get("model_used", "Unknown")
                            else:
                                answer = data["response"]
                                sources = data.get("sources", [])
                                processing_time = data.get("processing_time_ms", 0)
                                model_used = data.get("model_used", "Unknown")
                        else:
                            # Handle API error
                            error_message = f"❌ Error: {result['error']}"
                            st.error(error_message)
                            
                            # Add error message to chat
                            error_msg = {
                                "role": "assistant",
                                "content": error_message,
                                "timestamp": datetime.now()
                            }
                            st.session_state.messages.append(error_msg)
                            return
                
                # Add assistant message (works for both cached and fresh results)
                assistant_message = {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "processing_time": processing_time,
                    "model_used": model_used,
                    "timestamp": datetime.now()
                }
                st.session_state.messages.append(assistant_message)
                
                # Track performance
                st.session_state.processing_times.append(processing_time)
                
                # Display assistant response
                self.display_message(
                    "assistant", 
                    answer, 
                    sources, 
                    processing_time, 
                    model_used
                )
                
                # Clear input and rerun
                st.rerun()
        
        with col2:
            # Performance metrics
            self.display_performance_metrics()
            
            # Recent activity
            if st.session_state.messages:
                st.markdown("### 📝 Recent Activity")
                recent_messages = st.session_state.messages[-5:]  # Last 5 messages
                
                for msg in reversed(recent_messages):
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div style="background-color: #e3f2fd; padding: 0.5rem; border-radius: 5px; margin: 0.3rem 0; font-size: 0.8rem;">
                            <strong>👤 You:</strong> {msg["content"][:50]}...
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background-color: #f3e5f5; padding: 0.5rem; border-radius: 5px; margin: 0.3rem 0; font-size: 0.8rem;">
                            <strong>🤖 Assistant:</strong> {msg["content"][:50]}...
                        </div>
                        """, unsafe_allow_html=True)

def main():
    """Main application entry point."""
    try:
        chat_interface = HRChatInterface()
        chat_interface.main_chat_interface()
        
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.info("Please ensure the RAG API server is running on http://localhost:8001")

if __name__ == "__main__":
    main()
