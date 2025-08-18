#!/bin/bash
"""
Startup script for E-commerce RAG Assistant
Manages both FastAPI and MCP servers
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to stop servers
stop_servers() {
    print_status "Stopping E-commerce RAG Assistant servers..."
    
    # Stop FastAPI server
    if check_port 8000; then
        print_status "Stopping FastAPI server on port 8000..."
        pkill -f "uvicorn.*api_server:app" || true
        sleep 2
    fi
    
    # Stop MCP server
    pkill -f "mcp_server.py" || true
    
    print_success "Servers stopped"
}

# Function to start FastAPI server
start_api_server() {
    print_status "Starting FastAPI server..."
    
    if check_port 8000; then
        print_warning "Port 8000 is already in use. Stopping existing server..."
        pkill -f "uvicorn.*api_server:app" || true
        sleep 2
    fi
    
    # Start API server in background
    uv run uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload > logs/api_server.log 2>&1 &
    API_PID=$!
    
    # Wait for server to start
    print_status "Waiting for API server to start..."
    for i in {1..30}; do
        if check_port 8000; then
            print_success "FastAPI server started on http://localhost:8000"
            print_status "API Documentation: http://localhost:8000/docs"
            return 0
        fi
        sleep 1
    done
    
    print_error "FastAPI server failed to start"
    return 1
}

# Function to start MCP server
start_mcp_server() {
    print_status "Starting MCP server..."
    
    # Check if MCP server process exists
    if pgrep -f "mcp_server.py" > /dev/null; then
        print_warning "MCP server is already running. Stopping existing server..."
        pkill -f "mcp_server.py" || true
        sleep 2
    fi
    
    # Start MCP server in background
    uv run python mcp_server.py > logs/mcp_server.log 2>&1 &
    MCP_PID=$!
    
    print_success "MCP server started (PID: $MCP_PID)"
    print_status "MCP server logs: logs/mcp_server.log"
}

# Function to test servers
test_servers() {
    print_status "Testing servers..."
    
    # Test API server
    if command -v python3 >/dev/null 2>&1; then
        print_status "Testing FastAPI server..."
        uv run python test_api.py
    else
        print_warning "Python3 not found, skipping API tests"
    fi
    
    # Test MCP server
    print_status "Testing MCP server..."
    uv run python test_mcp.py
}

# Function to show server status
show_status() {
    print_status "Server Status:"
    echo ""
    
    # FastAPI server
    if check_port 8000; then
        print_success "✅ FastAPI Server: Running on http://localhost:8000"
    else
        print_error "❌ FastAPI Server: Not running"
    fi
    
    # MCP server
    if pgrep -f "mcp_server.py" > /dev/null; then
        print_success "✅ MCP Server: Running"
    else
        print_error "❌ MCP Server: Not running"
    fi
    
    echo ""
    print_status "Useful URLs:"
    echo "  - API Documentation: http://localhost:8000/docs"
    echo "  - API Health Check: http://localhost:8000/health"
    echo "  - Interactive API: http://localhost:8000/docs#/"
}

# Function to show logs
show_logs() {
    local service=$1
    
    if [ "$service" = "api" ]; then
        if [ -f "logs/api_server.log" ]; then
            print_status "FastAPI Server Logs (last 50 lines):"
            tail -n 50 logs/api_server.log
        else
            print_warning "No API server logs found"
        fi
    elif [ "$service" = "mcp" ]; then
        if [ -f "logs/mcp_server.log" ]; then
            print_status "MCP Server Logs (last 50 lines):"
            tail -n 50 logs/mcp_server.log
        else
            print_warning "No MCP server logs found"
        fi
    else
        show_logs "api"
        echo ""
        show_logs "mcp"
    fi
}

# Create logs directory
mkdir -p logs

# Main script logic
case "${1:-start}" in
    "start")
        print_status "🚀 Starting E-commerce RAG Assistant Servers"
        echo ""
        
        # Check environment
        if [ ! -f ".env" ]; then
            print_warning "No .env file found. Make sure to set MONGODB_URI and OPENAI_API_KEY"
        fi
        
        start_api_server
        start_mcp_server
        
        echo ""
        show_status
        echo ""
        print_success "🎉 All servers started successfully!"
        print_status "Use './manage_servers.sh status' to check server status"
        print_status "Use './manage_servers.sh stop' to stop all servers"
        print_status "Check logs with './manage_servers.sh logs [api|mcp]'"
        ;;
    
    "stop")
        stop_servers
        ;;
    
    "restart")
        stop_servers
        sleep 2
        $0 start
        ;;
    
    "status")
        show_status
        ;;
    
    "test")
        test_servers
        ;;
    
    "logs")
        show_logs "${2:-all}"
        ;;
    
    "api")
        start_api_server
        ;;
    
    "mcp")
        start_mcp_server
        ;;
    
    *)
        echo "E-commerce RAG Assistant Server Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|test|logs|api|mcp}"
        echo ""
        echo "Commands:"
        echo "  start    - Start both FastAPI and MCP servers"
        echo "  stop     - Stop all servers"
        echo "  restart  - Restart all servers"
        echo "  status   - Show server status"
        echo "  test     - Run server tests"
        echo "  logs     - Show server logs (optional: api|mcp)"
        echo "  api      - Start only FastAPI server"
        echo "  mcp      - Start only MCP server"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start all servers"
        echo "  $0 logs api       # Show API server logs"
        echo "  $0 test           # Run comprehensive tests"
        exit 1
        ;;
esac
