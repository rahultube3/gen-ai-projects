#!/bin/bash

# HR Assistant RAG System Launcher
# Starts the RAG API server with the local virtual environment

echo "🚀 HR Assistant RAG System Launcher"
echo "==================================="

# Check if we're in the right directory
if [ ! -f "rag_system.py" ]; then
    echo "❌ Error: rag_system.py not found"
    echo "Please run this script from the hr-assistant directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements_basic.txt"
    exit 1
fi

# Set paths
PYTHON_PATH="./venv/bin/python"

echo "📦 Using Python environment: $PYTHON_PATH"
echo "📊 Starting RAG API server on port 8001..."
echo ""

# Check if port is already in use
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8001 is already in use!"
    echo "   Run './stop_all.sh' to stop existing services"
    exit 1
fi

echo "💡 API will be available at: http://localhost:8001"
echo "📖 API docs at: http://localhost:8001/docs"
echo ""
echo "🔄 Starting server..."
echo "To stop the server, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping RAG API..."
    # Kill the background process if it exists
    if [ ! -z "$RAG_PID" ] && kill -0 $RAG_PID 2>/dev/null; then
        kill -TERM $RAG_PID 2>/dev/null
        wait $RAG_PID 2>/dev/null
    fi
    # Clean up port
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    echo "✅ RAG API stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Start RAG system in background and get PID
$PYTHON_PATH rag_system.py &
RAG_PID=$!

# Wait for the process
wait $RAG_PID
