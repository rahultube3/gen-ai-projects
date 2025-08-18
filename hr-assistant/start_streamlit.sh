#!/bin/bash

# HR Assistant Streamlit Chat Launcher
# This script starts the Streamlit web interface for the HR Assistant

echo "🏢 HR Assistant Streamlit Chat Launcher"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "simple_chat.py" ]; then
    echo "❌ Error: simple_chat.py not found"
    echo "Please run this script from the hr-assistant directory"
    exit 1
fi

# Check if the RAG API is running
echo "📡 Checking RAG API status..."
if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ RAG API is running on port 8001"
else
    echo "⚠️  RAG API is not running. The web interface will still start,"
    echo "   but you may need to start the RAG API for full functionality:"
    echo "   Run: ./start_rag.sh"
    echo ""
fi

# Check if Streamlit is installed
PYTHON_PATH="./venv/bin/python"
STREAMLIT_PATH="./venv/bin/streamlit"

if ! command -v $STREAMLIT_PATH &> /dev/null; then
    echo "❌ Streamlit is not installed in virtual environment"
    echo "Installing Streamlit..."
    $PYTHON_PATH -m pip install streamlit streamlit-chat
fi

# Check if port is already in use
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8501 is already in use!"
    echo "   Run './stop_all.sh' to stop existing services"
    exit 1
fi

echo ""
echo "🚀 Starting Streamlit HR Assistant Chat..."
echo "📱 The web interface will open automatically"
echo "🌐 URL: http://localhost:8501"
echo ""
echo "💡 Example questions to try:"
echo "   • What are the health insurance benefits?"
echo "   • How does the retirement plan work?"
echo "   • What is covered under disability insurance?"
echo ""
echo "To stop the application, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Streamlit..."
    # Kill the background process if it exists
    if [ ! -z "$STREAMLIT_PID" ] && kill -0 $STREAMLIT_PID 2>/dev/null; then
        kill -TERM $STREAMLIT_PID 2>/dev/null
        wait $STREAMLIT_PID 2>/dev/null
    fi
    # Clean up port
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    echo "✅ Streamlit stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Start Streamlit in background and get PID
$STREAMLIT_PATH run simple_chat.py --server.port 8501 --server.address localhost &
STREAMLIT_PID=$!

# Wait for the process
wait $STREAMLIT_PID
