#!/bin/bash

# Wikipedia RAG Chatbot Startup Script
# Starts both the FastAPI backend and the AngularJS frontend

echo "🚀 Starting Wikipedia RAG Chatbot System"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "chatbot_api_server.py" ]; then
    echo "❌ Please run this script from the web-scraping directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one with your OpenAI API key:"
    echo "   OPENAI_API_KEY=your_key_here"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Kill any existing servers on these ports
echo "🧹 Cleaning up existing servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $API_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo "🔧 Starting FastAPI backend server on port 8000..."
uv run python chatbot_api_server.py &
API_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend failed to start. Please check the logs above."
    kill $API_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Backend server started successfully"

# Start frontend server  
echo "🌐 Starting AngularJS frontend server on port 3000..."
python3 frontend_server.py 3000 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 2

echo ""
echo "🎉 Wikipedia RAG Chatbot System Started!"
echo "========================================"
echo "📡 API Server:      http://localhost:8000"
echo "📱 Frontend:        http://localhost:3000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo "🔍 Health Check:    http://localhost:8000/health"
echo ""
echo "💡 Quick Start:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Add a Wikipedia page (e.g., https://en.wikipedia.org/wiki/Health_data)"
echo "   3. Start asking questions about the content!"
echo ""
echo "Press Ctrl+C to stop all servers"

# Keep script running
wait