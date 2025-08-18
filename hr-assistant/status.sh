#!/bin/bash

# HR Assistant System Status Checker
# Checks the status of all HR Assistant components

echo "📊 HR Assistant System Status"
echo "============================="

# Function to check service status
check_service() {
    local port=$1
    local service_name=$2
    local health_endpoint=$3
    
    echo -n "🔍 $service_name (Port $port): "
    
    # Check if port is in use
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Not running"
        return 1
    fi
    
    # Check health endpoint if provided
    if [ ! -z "$health_endpoint" ]; then
        if curl -s -f "$health_endpoint" > /dev/null 2>&1; then
            echo "✅ Running and healthy"
            return 0
        else
            echo "⚠️  Running but not responding"
            return 1
        fi
    else
        echo "✅ Running"
        return 0
    fi
}

# Check each service
echo ""
check_service 8001 "RAG API" "http://localhost:8001/health"
check_service 8002 "Comprehensive API" "http://localhost:8002/health" 
check_service 8501 "Streamlit Web Interface" "http://localhost:8501/_stcore/health"
check_service 8502 "Streamlit Advanced Interface" "http://localhost:8502/_stcore/health"

echo ""
echo "🌐 Access Points:"
echo "   • Web Interface: http://localhost:8501"
echo "   • RAG API: http://localhost:8001"
echo "   • Comprehensive API: http://localhost:8002"
echo ""
echo "📖 API Documentation:"
echo "   • RAG API docs: http://localhost:8001/docs"
echo "   • Comprehensive API docs: http://localhost:8002/docs"
echo ""

# Show running Python processes related to HR Assistant
echo "🐍 Related Python Processes:"
hr_processes=$(ps aux | grep -E "(rag_system|comprehensive_api|simple_chat|streamlit)" | grep -v grep)
if [ ! -z "$hr_processes" ]; then
    echo "$hr_processes" | while IFS= read -r line; do
        echo "   📋 $line"
    done
else
    echo "   ✅ No HR Assistant processes found"
fi

echo ""
echo "💡 Management Commands:"
echo "   • Start all: ./start_all.sh"
echo "   • Stop all: ./stop_all.sh"
echo "   • Check status: ./status.sh"
echo "   • Individual: ./start_rag.sh, ./start_comprehensive.sh, ./start_streamlit.sh"
