#!/bin/bash

# MCP Weather Server Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to check if port is in use
check_port() {
    local port=${1:-6277}
    if lsof -ti:$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes using the MCP port
cleanup_port() {
    local port=${1:-6277}
    echo "Checking for processes using port $port..."
    
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "Found processes using port $port: $pids"
        echo "Killing processes..."
        kill -9 $pids 2>/dev/null
        sleep 1
        
        # Check if processes are still running
        if check_port $port; then
            echo "Warning: Some processes may still be using port $port"
        else
            echo "Port $port is now free"
        fi
    else
        echo "Port $port is already free"
    fi
}

# Function to start the server
start_server() {
    echo "Starting MCP Weather Server..."
    cd "$PROJECT_DIR"
    uv run python3 mcp-weather-server/main.py
}

# Function to start the server with inspector
start_inspector() {
    echo "Starting MCP Weather Server with Inspector..."
    echo "This will start both the MCP server and the web inspector interface."
    echo "The inspector will be available at: http://localhost:6274"
    echo "A session token will be displayed - use this to authenticate or set DANGEROUSLY_OMIT_AUTH=true"
    echo ""
    cd "$PROJECT_DIR"
    npx @modelcontextprotocol/inspector uv run python3 mcp-weather-server/main.py
}

# Function to stop the server
stop_server() {
    echo "Stopping MCP Weather Server..."
    pkill -f "mcp-weather-server/main.py"
    cleanup_port 6277
}

# Function to test the weather functions
test_functions() {
    echo "Testing MCP weather functions..."
    cd "$PROJECT_DIR"
    uv run python3 test_weather.py
}

# Main script logic
case "$1" in
    start)
        cleanup_port 6277
        start_server
        ;;
    inspector)
        cleanup_port 6277
        start_inspector
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 2
        cleanup_port 6277
        start_server
        ;;
    status)
        if check_port 6277; then
            echo "MCP Weather Server appears to be running (port 6277 in use)"
        else
            echo "MCP Weather Server appears to be stopped (port 6277 free)"
        fi
        ;;
    cleanup)
        cleanup_port 6277
        ;;
    test)
        test_functions
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|cleanup|inspector|test}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the MCP weather server"
        echo "  inspector - Start the MCP weather server with inspector"
        echo "  stop      - Stop the MCP weather server"
        echo "  restart   - Restart the MCP weather server"
        echo "  status    - Check if the server is running"
        echo "  cleanup   - Clean up any stuck processes using port 6277"
        echo "  test      - Test the weather functions independently"
        exit 1
        ;;
esac
