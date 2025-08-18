#!/bin/bash
#
# Service Management Script
# Provides convenient commands for managing MCP microservices.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICES_DIR="services"
ORCHESTRATION_DIR="orchestration"
PYTHON_CMD="uv run python"

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

# Check if required directories exist
check_setup() {
    if [ ! -d "$SERVICES_DIR" ]; then
        print_error "Services directory not found: $SERVICES_DIR"
        exit 1
    fi
    
    if [ ! -d "$ORCHESTRATION_DIR" ]; then
        print_error "Orchestration directory not found: $ORCHESTRATION_DIR"
        exit 1
    fi
    
    if [ ! -f "$ORCHESTRATION_DIR/service_manager.py" ]; then
        print_error "Service manager not found: $ORCHESTRATION_DIR/service_manager.py"
        exit 1
    fi
}

# Function to list available services
list_services() {
    print_status "Available MCP Services:"
    echo
    
    for service_file in "$SERVICES_DIR"/*_mcp_service.py; do
        if [ -f "$service_file" ]; then
            service_name=$(basename "$service_file" .py | sed 's/_mcp_service//')
            service_display=$(echo "$service_name" | tr '_' '-')
            echo "  • $service_display"
        fi
    done
    
    echo
}

# Function to start all services using service manager
start_all() {
    print_status "Starting all MCP services..."
    
    cd "$(dirname "$0")"
    $PYTHON_CMD "service_manager.py" start
    
    if [ $? -eq 0 ]; then
        print_success "All services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Function to stop all services
stop_all() {
    print_status "Stopping all MCP services..."
    
    cd "$(dirname "$0")"
    $PYTHON_CMD "service_manager.py" stop
    
    if [ $? -eq 0 ]; then
        print_success "All services stopped successfully"
    else
        print_error "Failed to stop services"
        exit 1
    fi
}

# Function to restart all services
restart_all() {
    print_status "Restarting all MCP services..."
    stop_all
    sleep 2
    start_all
}

# Function to restart a specific service
restart_service() {
    local service_name="$1"
    print_status "Restarting service: $service_name"
    
    cd "$(dirname "$0")"
    $PYTHON_CMD "service_manager.py" restart "$service_name"
    
    if [ $? -eq 0 ]; then
        print_success "Service $service_name restarted successfully"
    else
        print_error "Failed to restart service $service_name"
        exit 1
    fi
}

# Function to check service status
check_status() {
    print_status "Checking service status..."
    
    cd "$(dirname "$0")"
    $PYTHON_CMD "service_manager.py" status
}

# Function to run service manager in daemon mode
run_daemon() {
    print_status "Starting service manager in daemon mode..."
    print_warning "Press Ctrl+C to stop all services"
    
    cd "$(dirname "$0")"
    $PYTHON_CMD "service_manager.py"
}

# Function to test a specific service
test_service() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        print_error "Service name required for testing"
        echo "Usage: $0 test <service-name>"
        list_services
        exit 1
    fi
    
    service_file="$SERVICES_DIR/${service_name}_mcp_service.py"
    
    if [ ! -f "$service_file" ]; then
        print_error "Service file not found: $service_file"
        list_services
        exit 1
    fi
    
    print_status "Testing service: $service_name"
    
    # Run the service in test mode (just start and stop)
    cd "$(dirname "$0")"
    timeout 10s $PYTHON_CMD "$service_file" &
    sleep 5
    
    if pgrep -f "$service_file" > /dev/null; then
        pkill -f "$service_file"
        print_success "Service $service_name test passed"
    else
        print_error "Service $service_name test failed"
        exit 1
    fi
}

# Function to validate all services
validate_all() {
    print_status "Validating all services..."
    
    error_count=0
    
    for service_file in "$SERVICES_DIR"/*_mcp_service.py; do
        if [ -f "$service_file" ]; then
            service_name=$(basename "$service_file" .py | sed 's/_mcp_service//')
            
            # Skip base service since it's abstract
            if [ "$service_name" = "base" ]; then
                continue
            fi
            
            print_status "Validating $service_name..."
            
            # Check if service can be imported
            cd "$(dirname "$0")/.."  # Go to project root
            if $PYTHON_CMD -c "import sys; sys.path.append('$SERVICES_DIR'); import $(basename "$service_file" .py)" 2>/dev/null; then
                print_success "$service_name syntax is valid"
            else
                print_error "$service_name has syntax errors"
                ((error_count++))
            fi
        fi
    done
    
    if [ $error_count -eq 0 ]; then
        print_success "All services validated successfully"
    else
        print_error "$error_count services have errors"
        exit 1
    fi
}

# Function to show logs (placeholder - would integrate with proper logging)
show_logs() {
    local service_name="$1"
    
    if [ -z "$service_name" ]; then
        print_status "Showing all service logs..."
        # In a real implementation, this would show aggregated logs
        echo "Log viewing not implemented yet. Check individual service outputs."
    else
        print_status "Showing logs for service: $service_name"
        # In a real implementation, this would show specific service logs
        echo "Individual service log viewing not implemented yet."
    fi
}

# Function to display help
show_help() {
    echo "MCP Microservices Management Script"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  start                 Start all services using service manager"
    echo "  stop                  Stop all services"
    echo "  restart [service]     Restart all services or specific service"
    echo "  status               Check status of all services"
    echo "  daemon               Run service manager in daemon mode"
    echo "  test <service>       Test a specific service"
    echo "  validate             Validate all service syntax"
    echo "  list                 List available services"
    echo "  logs [service]       Show logs (all or specific service)"
    echo "  help                 Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 restart product-service  # Restart product service"
    echo "  $0 test chat-service        # Test chat service"
    echo "  $0 logs gateway-service     # Show gateway service logs"
    echo
}

# Main script logic
main() {
    check_setup
    
    case "${1:-help}" in
        "start")
            start_all
            ;;
        "stop")
            stop_all
            ;;
        "restart")
            if [ -n "$2" ]; then
                restart_service "$2"
            else
                restart_all
            fi
            ;;
        "status")
            check_status
            ;;
        "daemon")
            run_daemon
            ;;
        "test")
            test_service "$2"
            ;;
        "validate")
            validate_all
            ;;
        "list")
            list_services
            ;;
        "logs")
            show_logs "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
