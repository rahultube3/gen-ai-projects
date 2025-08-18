#!/bin/bash

# HR Assistant Complete System Launcher
# Starts all components of the HR Assistant system

echo "🏢 HR Assistant Complete System Launcher"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "rag_system.py" ] || [ ! -f "comprehensive_api.py" ] || [ ! -f "simple_chat.py" ]; then
    echo "❌ Error: Required files not found"
    echo "Please run this script from the hr-assistant directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please create virtual environment first:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements_basic.txt"
    exit 1
fi

# Set paths
PYTHON_PATH="./venv/bin/python"
STREAMLIT_PATH="./venv/bin/streamlit"

echo "📦 Using Python environment: $PYTHON_PATH"
echo ""

# Data Ingestion Steps
echo "📚 Checking and Ingesting HR Data..."
echo ""

# Check if MongoDB connection is available and get data count
echo "0️⃣ Verifying MongoDB connection and checking data..."
DATA_COUNT=$($PYTHON_PATH check_data.py 2>/dev/null)
CHECK_STATUS=$?

if [ $CHECK_STATUS -eq 2 ]; then
    echo "   ❌ MongoDB connection failed. Please check MONGODB_URI in .env file"
    exit 1
elif [ $CHECK_STATUS -eq 0 ]; then
    echo "   ✅ MongoDB connection verified"
    echo "   � Current document count in database: $DATA_COUNT"
    echo "   ✅ Sufficient data already exists (count: $DATA_COUNT)"
elif [ $CHECK_STATUS -eq 1 ]; then
    echo "   ✅ MongoDB connection verified"
    echo "   📊 Current document count in database: $DATA_COUNT"
    echo "   🔄 Insufficient data detected. Running data ingestion..."
    
    # Ingest basic sample data
    if [ -f "ingest_sample_data.py" ] && [ -d "sample_data" ]; then
        echo "   📚 Ingesting basic HR sample data..."
        $PYTHON_PATH ingest_sample_data.py
        if [ $? -eq 0 ]; then
            echo "   ✅ Basic sample data ingested successfully"
        else
            echo "   ⚠️  Warning: Basic sample data ingestion had issues (continuing anyway)"
        fi
    fi
    
    # Ingest table comparison data
    if [ -f "ingest_table_data.py" ]; then
        echo "   📊 Ingesting table comparison data..."
        $PYTHON_PATH ingest_table_data.py
        if [ $? -eq 0 ]; then
            echo "   ✅ Table comparison data ingested successfully"
        else
            echo "   ⚠️  Warning: Table data ingestion had issues (continuing anyway)"
        fi
    fi
    
    # Verify final data count using the check script
    FINAL_COUNT=$($PYTHON_PATH check_data.py 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   📊 Final document count: $FINAL_COUNT"
        echo "   ✅ Data ingestion completed successfully"
    else
        echo "   📊 Data ingestion completed (count verification skipped)"
    fi
else
    echo "   ❌ Unexpected error checking data status"
    exit 1
fi

echo ""

# Start services in order
echo "🚀 Starting HR Assistant System Components..."
echo ""

# 1. Start RAG API
echo "1️⃣ Starting RAG API (Port 8001)..."
$PYTHON_PATH rag_system.py &
RAG_PID=$!
echo "   ✅ RAG API started with PID: $RAG_PID"

# Wait for RAG API to be ready
echo "   🔄 Waiting for RAG API to be ready..."
for i in {1..30}; do
    if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
        echo "   ✅ RAG API is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ RAG API failed to start within 30 seconds"
        cleanup
        exit 1
    fi
done

# 2. Start Comprehensive API
echo "2️⃣ Starting Comprehensive API (Port 8002)..."
$PYTHON_PATH comprehensive_api.py &
COMP_PID=$!
echo "   ✅ Comprehensive API started with PID: $COMP_PID"

# Wait for Comprehensive API to be ready
echo "   🔄 Waiting for Comprehensive API to be ready..."
for i in {1..30}; do
    if curl -s -f http://localhost:8002/health > /dev/null 2>&1; then
        echo "   ✅ Comprehensive API is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ❌ Comprehensive API failed to start within 30 seconds"
        cleanup
        exit 1
    fi
done

# 3. Start Streamlit Simple Interface
echo "3️⃣ Starting Streamlit Simple Interface (Port 8501)..."
$STREAMLIT_PATH run simple_chat.py --server.port 8501 --server.address localhost &
STREAMLIT_PID=$!
echo "   ✅ Streamlit simple interface started with PID: $STREAMLIT_PID"

# Wait for Simple Streamlit to be ready
echo "   🔄 Waiting for simple Streamlit to be ready..."
for i in {1..30}; do
    if curl -s -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "   ✅ Simple Streamlit interface is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ⚠️  Simple Streamlit may still be starting (continuing anyway)"
        break
    fi
done

# 4. Start Streamlit Advanced Interface
echo "4️⃣ Starting Streamlit Advanced Interface (Port 8502)..."
$STREAMLIT_PATH run streamlit_chat.py --server.port 8502 --server.address localhost &
STREAMLIT_ADV_PID=$!
echo "   ✅ Streamlit advanced interface started with PID: $STREAMLIT_ADV_PID"

# Wait for Advanced Streamlit to be ready
echo "   🔄 Waiting for advanced Streamlit to be ready..."
for i in {1..30}; do
    if curl -s -f http://localhost:8502/_stcore/health > /dev/null 2>&1; then
        echo "   ✅ Advanced Streamlit interface is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "   ⚠️  Advanced Streamlit may still be starting (continuing anyway)"
        break
    fi
done

echo ""
echo "🎉 All systems started successfully!"
echo ""
echo "🌐 Access Points:"
echo "   • Simple Web Interface: http://localhost:8501"
echo "   • Advanced Web Interface: http://localhost:8502"
echo "   • RAG API: http://localhost:8001"
echo "   • Comprehensive API: http://localhost:8002"
echo ""
echo "📖 API Documentation:"
echo "   • RAG API docs: http://localhost:8001/docs"
echo "   • Comprehensive API docs: http://localhost:8002/docs"
echo ""
echo "💡 Example questions to try (on both web interfaces):"
echo "   • What are the health insurance benefits?"
echo "   • How does the retirement plan work?"
echo "   • What is covered under disability insurance?"
echo "   • Compare PPO vs HMO health insurance plans"
echo "   • Show me premium costs for health insurance"
echo "   • What are the PTO policies and accrual rates?"
echo ""
echo "🌟 Features:"
echo "   • Simple Interface (8501): Basic chat functionality"
echo "   • Advanced Interface (8502): Enhanced UI with performance metrics"
echo "   • Table Comparisons: Structured health insurance plan comparisons"
echo "   • Sample Data: Comprehensive HR policies and procedures"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down HR Assistant system..."
    
    # Stop each service gracefully with timeout
    if [ ! -z "$STREAMLIT_PID" ] && kill -0 $STREAMLIT_PID 2>/dev/null; then
        echo "   Stopping Simple Streamlit (PID: $STREAMLIT_PID)..."
        kill -TERM $STREAMLIT_PID 2>/dev/null
        sleep 2
        if kill -0 $STREAMLIT_PID 2>/dev/null; then
            echo "   Force stopping Simple Streamlit..."
            kill -KILL $STREAMLIT_PID 2>/dev/null
        fi
    fi
    
    if [ ! -z "$STREAMLIT_ADV_PID" ] && kill -0 $STREAMLIT_ADV_PID 2>/dev/null; then
        echo "   Stopping Advanced Streamlit (PID: $STREAMLIT_ADV_PID)..."
        kill -TERM $STREAMLIT_ADV_PID 2>/dev/null
        sleep 2
        if kill -0 $STREAMLIT_ADV_PID 2>/dev/null; then
            echo "   Force stopping Advanced Streamlit..."
            kill -KILL $STREAMLIT_ADV_PID 2>/dev/null
        fi
    fi
    
    if [ ! -z "$COMP_PID" ] && kill -0 $COMP_PID 2>/dev/null; then
        echo "   Stopping Comprehensive API (PID: $COMP_PID)..."
        kill -TERM $COMP_PID 2>/dev/null
        sleep 2
        if kill -0 $COMP_PID 2>/dev/null; then
            echo "   Force stopping Comprehensive API..."
            kill -KILL $COMP_PID 2>/dev/null
        fi
    fi
    
    if [ ! -z "$RAG_PID" ] && kill -0 $RAG_PID 2>/dev/null; then
        echo "   Stopping RAG API (PID: $RAG_PID)..."
        kill -TERM $RAG_PID 2>/dev/null
        sleep 2
        if kill -0 $RAG_PID 2>/dev/null; then
            echo "   Force stopping RAG API..."
            kill -KILL $RAG_PID 2>/dev/null
        fi
    fi
    
    # Clean up any remaining processes on our ports
    echo "   Cleaning up any remaining processes..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    lsof -ti:8502 | xargs kill -9 2>/dev/null || true
    
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

echo "Press Ctrl+C to stop all services"
echo ""

# Wait for any process to exit
wait
