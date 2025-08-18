#!/bin/bash

# HR Assistant Comprehensive API Launcher
# Starts the comprehensive API server with the local virtual environment

echo "🚀 HR Assistant Comprehensive API Launcher"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "comprehensive_api.py" ]; then
    echo "❌ Error: comprehensive_api.py not found"
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
echo "📊 Starting Comprehensive API server on port 8002..."
echo ""

# Check if port is already in use
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8002 is already in use!"
    echo "   Run './stop_all.sh' to stop existing services"
    exit 1
fi

echo "💡 API will be available at: http://localhost:8002"
echo "📖 API docs at: http://localhost:8002/docs"
echo ""
echo "🔄 Starting server..."
echo "To stop the server, press Ctrl+C"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Comprehensive API..."
    # Kill the background process if it exists
    if [ ! -z "$COMP_PID" ] && kill -0 $COMP_PID 2>/dev/null; then
        kill -TERM $COMP_PID 2>/dev/null
        wait $COMP_PID 2>/dev/null
    fi
    # Clean up port
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    echo "✅ Comprehensive API stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Start Comprehensive API in background and get PID
$PYTHON_PATH comprehensive_api.py &
COMP_PID=$!

# Wait for the process
wait $COMP_PID
