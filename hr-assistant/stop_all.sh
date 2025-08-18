#!/bin/bash

# HR Assistant System Shutdown Script
# Safely stops all HR Assistant components

echo "🛑 HR Assistant System Shutdown"
echo "==============================="

# Function to stop service on a specific port
stop_service_on_port() {
    local port=$1
    local service_name=$2
    
    echo "🔍 Checking for processes on port $port ($service_name)..."
    
    # Find processes using the port
    pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo "   ✅ No processes found on port $port"
        return 0
    fi
    
    echo "   📋 Found processes: $pids"
    
    # Try graceful shutdown first
    echo "   🚦 Attempting graceful shutdown..."
    for pid in $pids; do
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid 2>/dev/null
        fi
    done
    
    # Wait for graceful shutdown
    sleep 3
    
    # Check if processes are still running
    remaining_pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -z "$remaining_pids" ]; then
        echo "   ✅ $service_name stopped gracefully"
        return 0
    fi
    
    # Force kill if necessary
    echo "   ⚡ Force stopping remaining processes..."
    for pid in $remaining_pids; do
        if kill -0 $pid 2>/dev/null; then
            kill -KILL $pid 2>/dev/null
        fi
    done
    
    # Final check
    final_pids=$(lsof -ti:$port 2>/dev/null)
    if [ -z "$final_pids" ]; then
        echo "   ✅ $service_name stopped successfully"
    else
        echo "   ❌ Failed to stop some processes on port $port"
        return 1
    fi
}

# Function to stop Streamlit processes specifically
stop_streamlit_processes() {
    echo "🔍 Looking for Streamlit processes running HR Assistant files..."
    
    # Find Streamlit processes that are running hr-assistant files
    streamlit_pids=$(ps aux | grep -E "streamlit.*run.*(simple_chat|streamlit_chat)" | grep -v grep | awk '{print $2}')
    
    if [ -z "$streamlit_pids" ]; then
        echo "   ✅ No HR Assistant Streamlit processes found"
        return 0
    fi
    
    echo "   📋 Found Streamlit processes: $streamlit_pids"
    
    for pid in $streamlit_pids; do
        if kill -0 $pid 2>/dev/null; then
            echo "   🚦 Gracefully stopping Streamlit process $pid..."
            kill -TERM $pid 2>/dev/null
            sleep 2
            
            if kill -0 $pid 2>/dev/null; then
                echo "   ⚡ Force stopping Streamlit process $pid..."
                kill -KILL $pid 2>/dev/null
            else
                echo "   ✅ Streamlit process $pid stopped gracefully"
            fi
        fi
    done
}

# Stop Streamlit processes first (they can be tricky)
stop_streamlit_processes

# Stop each service by port
stop_service_on_port 8501 "Streamlit Web Interface"
stop_service_on_port 8502 "Streamlit Advanced Interface"
stop_service_on_port 8002 "Comprehensive API"
stop_service_on_port 8001 "RAG API"

echo ""
echo "🧹 Cleaning up any remaining Python processes..."

# Find any remaining HR Assistant Python processes (including streamlit)
hr_processes=$(ps aux | grep -E "(rag_system|comprehensive_api|simple_chat|streamlit.*hr-assistant)" | grep -v grep | awk '{print $2}')

if [ ! -z "$hr_processes" ]; then
    echo "   📋 Found remaining HR processes: $hr_processes"
    for pid in $hr_processes; do
        if kill -0 $pid 2>/dev/null; then
            echo "   🛑 Stopping process $pid..."
            kill -TERM $pid 2>/dev/null
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid 2>/dev/null
            fi
        fi
    done
else
    echo "   ✅ No remaining processes found"
fi

echo ""
echo "🎉 HR Assistant system shutdown complete!"
echo ""
echo "To restart the system, run:"
echo "   ./start_all.sh"
