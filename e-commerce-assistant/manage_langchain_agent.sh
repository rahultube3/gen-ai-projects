#!/bin/bash

# 🤖 LangChain Agent + MCP Services Management Script
# Manages the complete AI e-commerce system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/rahultomar/rahul-dev/gen-ai-projects/e-commerce-assistant"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"
MCP_SERVICES_SCRIPT="$PROJECT_DIR/orchestration/manage_services.sh"
LANGCHAIN_API_SERVER="$PROJECT_DIR/langchain_api_server.py"
LANGCHAIN_AGENT_CLI="$PROJECT_DIR/langchain_agent.py"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if a process is running
is_process_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to check environment variables
check_environment() {
    print_header "Checking Environment"
    
    local missing_vars=()
    
    if [ -z "$OPENAI_API_KEY" ]; then
        missing_vars+=("OPENAI_API_KEY")
    else
        print_info "✅ OPENAI_API_KEY is set"
    fi
    
    if [ -z "$MONGODB_URI" ]; then
        print_warning "⚠️  MONGODB_URI not set, using default: mongodb://localhost:27017/ecommerce_assistant"
        export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant"
    else
        print_info "✅ MONGODB_URI is set"
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        print_info "Please set them and try again:"
        print_info "  export OPENAI_API_KEY='your-api-key-here'"
        print_info "  export MONGODB_URI='your-mongodb-uri-here'"
        return 1
    fi
    
    return 0
}

# Function to check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install it first."
        return 1
    fi
    print_info "✅ uv is available"
    
    # Check if Python dependencies are installed
    if ! uv run python -c "import langchain, fastapi, pymongo" 2>/dev/null; then
        print_warning "Some Python dependencies are missing. Installing..."
        cd "$PROJECT_DIR"
        uv sync
        print_info "✅ Dependencies installed"
    else
        print_info "✅ Python dependencies are available"
    fi
    
    # Check if MCP services management script exists
    if [ ! -f "$MCP_SERVICES_SCRIPT" ]; then
        print_error "MCP services management script not found: $MCP_SERVICES_SCRIPT"
        return 1
    fi
    print_info "✅ MCP services script is available"
    
    return 0
}

# Function to start MCP services
start_mcp_services() {
    print_header "Starting MCP Services"
    
    print_info "🚀 Starting all MCP microservices..."
    if "$MCP_SERVICES_SCRIPT" start; then
        print_status "✅ MCP services started successfully"
        
        # Wait for services to be ready
        print_info "⏳ Waiting for services to be ready..."
        sleep 5
        
        # Validate services
        if "$MCP_SERVICES_SCRIPT" validate; then
            print_status "✅ All MCP services are healthy"
            return 0
        else
            print_error "❌ Some MCP services failed validation"
            return 1
        fi
    else
        print_error "❌ Failed to start MCP services"
        return 1
    fi
}

# Function to stop MCP services
stop_mcp_services() {
    print_header "Stopping MCP Services"
    
    print_info "🛑 Stopping all MCP microservices..."
    if "$MCP_SERVICES_SCRIPT" stop; then
        print_status "✅ MCP services stopped successfully"
        return 0
    else
        print_error "❌ Failed to stop MCP services"
        return 1
    fi
}

# Function to start LangChain API server
start_langchain_api() {
    print_header "Starting LangChain API Server"
    
    local pid_file="$PID_DIR/langchain_api_server.pid"
    local log_file="$LOG_DIR/langchain_api_server.log"
    
    if is_process_running "$pid_file"; then
        print_warning "LangChain API server is already running (PID: $(cat $pid_file))"
        return 0
    fi
    
    print_info "🚀 Starting LangChain API server..."
    cd "$PROJECT_DIR"
    
    # Start the server in background
    nohup uv run python "$LANGCHAIN_API_SERVER" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait for server to start
    print_info "⏳ Waiting for API server to start..."
    local retries=10
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            print_status "✅ LangChain API server started successfully (PID: $pid)"
            print_info "📚 API Documentation: http://localhost:8001/docs"
            print_info "🔄 Interactive Docs: http://localhost:8001/redoc"
            return 0
        fi
        sleep 2
        retries=$((retries - 1))
    done
    
    print_error "❌ Failed to start LangChain API server"
    kill $pid 2>/dev/null || true
    rm -f "$pid_file"
    return 1
}

# Function to stop LangChain API server
stop_langchain_api() {
    print_header "Stopping LangChain API Server"
    
    local pid_file="$PID_DIR/langchain_api_server.pid"
    
    if is_process_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        print_info "🛑 Stopping LangChain API server (PID: $pid)..."
        kill $pid
        rm -f "$pid_file"
        print_status "✅ LangChain API server stopped"
    else
        print_warning "LangChain API server is not running"
    fi
}

# Function to start LangChain CLI agent
start_langchain_cli() {
    print_header "Starting LangChain CLI Agent"
    
    print_info "🤖 Starting interactive LangChain agent..."
    print_info "Type 'quit' to exit, 'reset' to clear memory"
    print_info "==============================================="
    
    cd "$PROJECT_DIR"
    uv run python "$LANGCHAIN_AGENT_CLI"
}

# Function to show status of all services
show_status() {
    print_header "System Status"
    
    # MCP Services Status
    echo -e "${CYAN}MCP Services:${NC}"
    "$MCP_SERVICES_SCRIPT" status
    echo
    
    # LangChain API Server Status
    echo -e "${CYAN}LangChain API Server:${NC}"
    local api_pid_file="$PID_DIR/langchain_api_server.pid"
    if is_process_running "$api_pid_file"; then
        local pid=$(cat "$api_pid_file")
        print_status "✅ Running (PID: $pid)"
        print_info "   URL: http://localhost:8001"
        print_info "   Docs: http://localhost:8001/docs"
    else
        print_warning "❌ Not running"
    fi
    echo
    
    # Health Check
    echo -e "${CYAN}Health Check:${NC}"
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        print_status "✅ API server is responding"
    else
        print_warning "❌ API server is not responding"
    fi
}

# Function to show logs
show_logs() {
    local service="$1"
    
    case "$service" in
        "api"|"langchain")
            print_header "LangChain API Server Logs"
            if [ -f "$LOG_DIR/langchain_api_server.log" ]; then
                tail -f "$LOG_DIR/langchain_api_server.log"
            else
                print_warning "No log file found"
            fi
            ;;
        "mcp"|"services")
            print_header "MCP Services Logs"
            "$MCP_SERVICES_SCRIPT" logs
            ;;
        "all"|*)
            print_header "All System Logs"
            print_info "LangChain API Server Logs:"
            if [ -f "$LOG_DIR/langchain_api_server.log" ]; then
                tail -n 20 "$LOG_DIR/langchain_api_server.log"
            else
                print_warning "No LangChain API log file found"
            fi
            echo
            print_info "MCP Services Logs:"
            "$MCP_SERVICES_SCRIPT" logs
            ;;
    esac
}

# Function to run tests
run_tests() {
    print_header "Running System Tests"
    
    cd "$PROJECT_DIR"
    
    # Test MCP services
    print_info "🧪 Testing MCP services..."
    if "$MCP_SERVICES_SCRIPT" validate; then
        print_status "✅ MCP services tests passed"
    else
        print_error "❌ MCP services tests failed"
        return 1
    fi
    
    # Test LangChain integration
    print_info "🧪 Testing LangChain integration..."
    if uv run python demo_langchain_integration.py; then
        print_status "✅ LangChain integration tests passed"
    else
        print_error "❌ LangChain integration tests failed"
        return 1
    fi
    
    # Test API endpoints
    if is_process_running "$PID_DIR/langchain_api_server.pid"; then
        print_info "🧪 Testing API endpoints..."
        
        # Test health endpoint
        if curl -s http://localhost:8001/health | grep -q "healthy"; then
            print_status "✅ Health endpoint working"
        else
            print_error "❌ Health endpoint failed"
            return 1
        fi
        
        # Test chat endpoint
        local test_response=$(curl -s -X POST "http://localhost:8001/chat" \
            -H "Content-Type: application/json" \
            -d '{"message": "test", "user_id": "test_user"}')
        
        if echo "$test_response" | grep -q "success"; then
            print_status "✅ Chat endpoint working"
        else
            print_error "❌ Chat endpoint failed"
            return 1
        fi
    else
        print_warning "⚠️ API server not running, skipping API tests"
    fi
    
    print_status "🎉 All tests passed!"
}

# Function to show help
show_help() {
    echo -e "${PURPLE}🤖 LangChain Agent + MCP Services Manager${NC}"
    echo
    echo -e "${CYAN}Usage:${NC}"
    echo "  $0 <command> [options]"
    echo
    echo -e "${CYAN}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}           Start all services (MCP + LangChain API)"
    echo -e "  ${GREEN}stop${NC}            Stop all services"
    echo -e "  ${GREEN}restart${NC}         Restart all services"
    echo -e "  ${GREEN}status${NC}          Show status of all services"
    echo -e "  ${GREEN}logs${NC} [service]  Show logs (api, mcp, all)"
    echo -e "  ${GREEN}test${NC}            Run system tests"
    echo -e "  ${GREEN}cli${NC}             Start interactive LangChain CLI agent"
    echo -e "  ${GREEN}health${NC}          Quick health check"
    echo
    echo -e "${CYAN}Service Management:${NC}"
    echo -e "  ${GREEN}start-mcp${NC}       Start only MCP services"
    echo -e "  ${GREEN}stop-mcp${NC}        Stop only MCP services"
    echo -e "  ${GREEN}start-api${NC}       Start only LangChain API server"
    echo -e "  ${GREEN}stop-api${NC}        Stop only LangChain API server"
    echo
    echo -e "${CYAN}Examples:${NC}"
    echo "  $0 start              # Start everything"
    echo "  $0 logs api           # Show API server logs"
    echo "  $0 test               # Run all tests"
    echo "  $0 cli                # Start interactive agent"
    echo
    echo -e "${CYAN}Environment Variables:${NC}"
    echo "  OPENAI_API_KEY        Required for LangChain agent"
    echo "  MONGODB_URI           MongoDB connection string"
    echo
    echo -e "${CYAN}URLs:${NC}"
    echo "  API Server:           http://localhost:8001"
    echo "  API Documentation:    http://localhost:8001/docs"
    echo "  Interactive Docs:     http://localhost:8001/redoc"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "start")
            if ! check_environment; then exit 1; fi
            if ! check_dependencies; then exit 1; fi
            if ! start_mcp_services; then exit 1; fi
            if ! start_langchain_api; then exit 1; fi
            print_status "🎉 All services started successfully!"
            show_status
            ;;
        "stop")
            stop_langchain_api
            stop_mcp_services
            print_status "🛑 All services stopped"
            ;;
        "restart")
            stop_langchain_api
            stop_mcp_services
            sleep 2
            if ! check_environment; then exit 1; fi
            if ! start_mcp_services; then exit 1; fi
            if ! start_langchain_api; then exit 1; fi
            print_status "🔄 All services restarted successfully!"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-all}"
            ;;
        "test")
            if ! check_environment; then exit 1; fi
            if ! check_dependencies; then exit 1; fi
            run_tests
            ;;
        "cli")
            if ! check_environment; then exit 1; fi
            if ! check_dependencies; then exit 1; fi
            start_langchain_cli
            ;;
        "health")
            if curl -s http://localhost:8001/health | grep -q "healthy"; then
                print_status "✅ System is healthy"
                exit 0
            else
                print_error "❌ System health check failed"
                exit 1
            fi
            ;;
        "start-mcp")
            if ! check_dependencies; then exit 1; fi
            start_mcp_services
            ;;
        "stop-mcp")
            stop_mcp_services
            ;;
        "start-api")
            if ! check_environment; then exit 1; fi
            if ! check_dependencies; then exit 1; fi
            start_langchain_api
            ;;
        "stop-api")
            stop_langchain_api
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle script interruption
cleanup() {
    print_info "🛑 Received interrupt signal, stopping services..."
    stop_langchain_api
    stop_mcp_services
    exit 130
}

trap cleanup INT TERM

# Run main function with all arguments
main "$@"
