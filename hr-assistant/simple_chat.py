# Simple HR Assistant Streamlit Chat with Guardrails
# Basic web interface for testing the HR RAG system with content protection

import streamlit as st
import requests
import json
from datetime import datetime

# Import guardrails for client-side validation
try:
    from guardrails import validate_query, validate_response
    GUARDRAILS_AVAILABLE = True
except ImportError:
    GUARDRAILS_AVAILABLE = False
    st.warning("⚠️ Guardrails module not available - content filtering disabled")

# Page configuration
st.set_page_config(
    page_title="HR Assistant - Simple Chat",
    page_icon="🏢",
    layout="centered"
)

# Configuration
RAG_API_URL = "http://localhost:8001"

def check_api_health():
    """Check if the RAG API is available."""
    try:
        response = requests.get(f"{RAG_API_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def send_query(query, max_sources=3):
    """Send query to the RAG system."""
    try:
        payload = {
            "query": query,
            "max_sources": max_sources,
            "include_sources": True,
            "context_window": 2000
        }
        
        response = requests.post(f"{RAG_API_URL}/ask", json=payload, timeout=20)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Main interface
st.title("🏢 HR Assistant Chat")
st.markdown("Ask questions about HR policies, benefits, and procedures.")

# Check API status
if check_api_health():
    st.success("✅ HR Assistant is online and ready!")
else:
    st.error("❌ HR Assistant API is not available. Please start the server first.")
    st.info("Run: `./venv/bin/python rag_system.py` or use `./start_rag.sh` to start the RAG API server")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources for assistant messages
        if message["role"] == "assistant" and "sources" in message:
            sources = message["sources"]
            if sources:
                with st.expander(f"📚 Sources ({len(sources)} documents)"):
                    for i, source in enumerate(sources):
                        st.markdown(f"""
                        **📄 {source.get('title', 'Document')}** (Score: {source.get('similarity_score', 0):.3f})
                        
                        {source.get('text_preview', source.get('text', ''))[:300]}...
                        """)

# Chat input with guardrails
if prompt := st.chat_input("Ask about HR policies, benefits, or procedures..."):
    # Client-side guardrails validation
    if GUARDRAILS_AVAILABLE:
        is_allowed, violations = validate_query(prompt)
        if not is_allowed:
            st.error("⚠️ Your message contains content that violates our usage policy. Please rephrase your question appropriately.")
            violation_messages = [v.message for v in violations]
            with st.expander("ℹ️ Policy Violation Details"):
                for msg in violation_messages:
                    st.warning(f"• {msg}")
            st.stop()
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Searching HR documents..."):
            result = send_query(prompt)
            
            if result:
                answer = result.get("answer", "I couldn't find a relevant answer.")
                sources = result.get("sources", [])
                processing_time = result.get("processing_time_ms", 0)
                metadata = result.get("metadata", {})
                guardrails_info = metadata.get("guardrails", {})
                
                # Display answer
                st.markdown(answer)
                
                # Show processing time and guardrails info
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"⚡ Response time: {processing_time:.0f}ms")
                with col2:
                    if guardrails_info.get("content_filtered", False):
                        st.caption("🛡️ Content filtered for safety")
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources,
                    "guardrails": guardrails_info
                })
                
                # Show sources
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} documents)"):
                        for i, source in enumerate(sources):
                            st.markdown(f"""
                            **📄 {source.get('title', 'Document')}** (Score: {source.get('similarity_score', 0):.3f})
                            
                            {source.get('text_preview', source.get('text', ''))[:300]}...
                            """)
            else:
                error_msg = "Sorry, I encountered an error processing your request."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar with example questions
with st.sidebar:
    st.markdown("## 💡 Example Questions")
    
    example_questions = [
        "What are the health insurance benefits?",
        "How does the retirement plan work?",
        "What is covered under disability insurance?",
        "Tell me about dependent care benefits",
        "What are the eligibility requirements for benefits?"
    ]
    
    for question in example_questions:
        if st.button(question, key=f"example_{hash(question)}"):
            # Add the example question as user input
            st.session_state.messages.append({"role": "user", "content": question})
            
            # Get response
            result = send_query(question)
            if result:
                answer = result.get("answer", "I couldn't find a relevant answer.")
                sources = result.get("sources", [])
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
            
            st.rerun()
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔧 System Info")
    st.info("RAG API: http://localhost:8001")
    
    # Try to get system stats
    try:
        stats_response = requests.get(f"{RAG_API_URL}/stats", timeout=3)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            if 'database' in stats:
                db_stats = stats['database']
                st.metric("Documents", db_stats.get('total_vectors', 0))
    except:
        pass
