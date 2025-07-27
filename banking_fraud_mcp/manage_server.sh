#!/bin/bash

# MCP Banking Fraud Detection Server Management Script

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
    echo "Starting MCP Banking Fraud Detection Server..."
    cd "$PROJECT_DIR"
    uv run python3 banking_fraud_mcp/fraud_server.py
}

# Function to start the server in background
start_server_background() {
    echo "Starting MCP Banking Fraud Detection Server in background..."
    cd "$PROJECT_DIR"
    nohup uv run python3 banking_fraud_mcp/fraud_server.py > /dev/null 2>&1 &
    local server_pid=$!
    echo "Server started with PID: $server_pid"
    sleep 2
}

# Function to start the server with inspector
start_inspector() {
    echo "Starting MCP Banking Fraud Detection Server with Inspector..."
    echo "This will start both the MCP server and the web inspector interface."
    echo "The inspector will be available at: http://localhost:6274"
    echo "A session token will be displayed - use this to authenticate or set DANGEROUSLY_OMIT_AUTH=true"
    echo ""
    cd "$PROJECT_DIR"
    npx @modelcontextprotocol/inspector uv run python3 banking_fraud_mcp/fraud_server.py
}

# Function to stop the server
stop_server() {
    echo "Stopping MCP Banking Fraud Detection Server..."
    pkill -f "banking_fraud_mcp/fraud_server.py"
    cleanup_port 6277
}

# Function to test the fraud detection functions
test_functions() {
    echo "Testing MCP fraud detection functions..."
    cd "$PROJECT_DIR"
    echo "Running native MCP client demo..."
    python3 banking_fraud_mcp/mcp_fraud_client.py demo
}

# Function to run enhanced demo
demo_enhanced() {
    echo "Running enhanced fraud detection demo..."
    cd "$PROJECT_DIR"
    python3 banking_fraud_mcp/enhanced_client.py demo
}

# Function to run interactive client
interactive() {
    echo "Starting interactive fraud detection client..."
    cd "$PROJECT_DIR"
    python3 banking_fraud_mcp/mcp_fraud_client.py
}

# Function to run enhanced interactive client
interactive_enhanced() {
    echo "Starting enhanced interactive fraud detection client..."
    cd "$PROJECT_DIR"
    python3 banking_fraud_mcp/enhanced_client.py
}

# Function to setup database
setup_db() {
    echo "Setting up banking fraud detection database..."
    cd "$PROJECT_DIR"
    python3 banking_fraud_mcp/db_setup.py
    echo "Database setup complete!"
}

# Function to show database status
db_status() {
    echo "Banking Fraud Detection Database Status:"
    cd "$PROJECT_DIR"
    python3 -c "
import duckdb
import os

current_dir = os.path.dirname(os.path.abspath('banking_fraud_mcp/fraud_server.py'))
db_path = os.path.join(current_dir, 'bank.db')

try:
    conn = duckdb.connect(db_path)
    
    # Get table info
    customers = conn.execute('SELECT COUNT(*) FROM customer_profiles').fetchone()[0]
    transactions = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
    
    print(f'  📊 Total Customers: {customers}')
    print(f'  📊 Total Transactions: {transactions}')
    
    # Show sample data
    print('\n  👥 Sample Customers:')
    for row in conn.execute('SELECT customer_id, name, risk_score FROM customer_profiles LIMIT 3').fetchall():
        print(f'    • {row[1]} ({row[0]}): Risk {row[2]}')
    
    print('\n  💳 Sample Transactions:')
    for row in conn.execute('SELECT txn_id, customer_id, amount, location FROM transactions LIMIT 3').fetchall():
        print(f'    • {row[0]}: \${row[2]} in {row[3]} ({row[1]})')
    
    conn.close()
    print('\n  ✅ Database is operational!')
    
except Exception as e:
    print(f'  ❌ Database error: {e}')
"
}

# Function to run langchain client (requires GROQ_API_KEY)
run_langchain() {
    echo "Running LangChain-based fraud client..."
    cd "$PROJECT_DIR"
    
    # Load environment variables from .env file if it exists
    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
    elif [ -f "$PROJECT_DIR/.env" ]; then
        export $(cat "$PROJECT_DIR/.env" | grep -v '^#' | xargs)
    fi
    
    # Check if GROQ_API_KEY is set
    if [ -z "$GROQ_API_KEY" ]; then
        echo "❌ GROQ_API_KEY not set. Please set it in your .env file or environment."
        return 1
    fi
    
    echo "Using GROQ_API_KEY: ${GROQ_API_KEY:0:20}..."
    echo "Note: LangChain MCP client will automatically start the server as needed."
    
    cd "$SCRIPT_DIR" && uv run python client.py $1
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
            echo "MCP Banking Fraud Detection Server appears to be running (port 6277 in use)"
        else
            echo "MCP Banking Fraud Detection Server appears to be stopped (port 6277 free)"
        fi
        ;;
    cleanup)
        cleanup_port 6277
        ;;
    test)
        test_functions
        ;;
    demo)
        demo_enhanced
        ;;
    interactive)
        interactive
        ;;
    enhanced)
        interactive_enhanced
        ;;
    setup-db)
        setup_db
        ;;
    db-status)
        db_status
        ;;
    langchain)
        run_langchain "$@"
        ;;
    docker-build)
        echo "Building Docker image..."
        ./docker-manage.sh build
        ;;
    docker-start)
        echo "Starting Docker container..."
        ./docker-manage.sh start
        ;;
    docker-stop)
        echo "Stopping Docker container..."
        ./docker-manage.sh stop
        ;;
    docker-status)
        echo "Checking Docker container status..."
        ./docker-manage.sh status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|cleanup|inspector|test|demo|interactive|enhanced|setup-db|db-status|langchain|docker-build|docker-start|docker-stop|docker-status}"
        echo ""
        echo "Server Commands:"
        echo "  start       - Start the MCP fraud detection server"
        echo "  inspector   - Start the MCP server with web inspector"
        echo "  stop        - Stop the MCP fraud detection server"
        echo "  restart     - Restart the MCP fraud detection server"
        echo "  status      - Check if the server is running"
        echo "  cleanup     - Clean up any stuck processes using port 6277"
        echo ""
        echo "Client Commands:"
        echo "  test        - Test fraud detection with native MCP client"
        echo "  demo        - Run comprehensive fraud detection demo"
        echo "  interactive - Start interactive fraud analysis client"
        echo "  enhanced    - Start enhanced interactive client with all features"
        echo "  langchain   - Run LangChain-based client (requires GROQ_API_KEY)"
        echo ""
        echo "Database Commands:"
        echo "  setup-db    - Initialize the fraud detection database"
        echo "  db-status   - Show database status and sample data"
        echo ""
        echo "Docker Commands:"
        echo "  docker-build  - Build Docker image"
        echo "  docker-start  - Start Docker container"
        echo "  docker-stop   - Stop Docker container"
        echo "  docker-status - Show Docker container status"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start the server"
        echo "  $0 demo                     # Run comprehensive demo"
        echo "  $0 interactive              # Start interactive fraud analysis"
        echo "  $0 langchain demo           # Run LangChain demo mode"
        echo "  $0 inspector                # Start with web inspector"
        echo "  $0 docker-build             # Build Docker image"
        exit 1
        ;;
esac
