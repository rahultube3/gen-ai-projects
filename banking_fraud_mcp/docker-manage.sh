#!/bin/bash

# Docker Management Script for Banking Fraud Detection MCP Server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="banking-fraud-mcp"
CONTAINER_NAME="banking-fraud-detection"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build the Docker image
build_image() {
    print_header "Building Banking Fraud Detection Docker Image"
    cd "$SCRIPT_DIR"
    
    print_status "Building image: $IMAGE_NAME"
    if docker build -t "$IMAGE_NAME" .; then
        print_status "✅ Image built successfully"
    else
        print_error "❌ Failed to build image"
        exit 1
    fi
}

# Function to start the container
start_container() {
    print_header "Starting Banking Fraud Detection Container"
    
    # Check if .env file exists
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_warning "No .env file found. Creating from template..."
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        print_warning "Please edit .env file with your configuration before starting"
        return 1
    fi
    
    # Create data directory if it doesn't exist
    mkdir -p "$SCRIPT_DIR/data"
    mkdir -p "$SCRIPT_DIR/logs"
    
    print_status "Starting container with docker-compose..."
    if docker-compose -f "$COMPOSE_FILE" up -d banking-fraud-mcp; then
        print_status "✅ Container started successfully"
        print_status "Container name: $CONTAINER_NAME"
        sleep 3
        show_status
    else
        print_error "❌ Failed to start container"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    print_header "Stopping Banking Fraud Detection Container"
    
    print_status "Stopping container..."
    if docker-compose -f "$COMPOSE_FILE" down; then
        print_status "✅ Container stopped successfully"
    else
        print_error "❌ Failed to stop container"
        exit 1
    fi
}

# Function to restart the container
restart_container() {
    print_header "Restarting Banking Fraud Detection Container"
    stop_container
    sleep 2
    start_container
}

# Function to show container status
show_status() {
    print_header "Banking Fraud Detection Container Status"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "$CONTAINER_NAME"; then
        print_status "✅ Container is running"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "$CONTAINER_NAME"
        
        # Show health status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null)
        if [ "$health_status" = "healthy" ]; then
            print_status "✅ Health check: HEALTHY"
        elif [ "$health_status" = "unhealthy" ]; then
            print_error "❌ Health check: UNHEALTHY"
        else
            print_warning "⏳ Health check: STARTING"
        fi
    else
        print_warning "❌ Container is not running"
    fi
}

# Function to show container logs
show_logs() {
    print_header "Banking Fraud Detection Container Logs"
    
    if docker ps -q -f name="$CONTAINER_NAME" > /dev/null; then
        docker logs -f "$CONTAINER_NAME"
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Function to access container shell
shell_access() {
    print_header "Accessing Banking Fraud Detection Container Shell"
    
    if docker ps -q -f name="$CONTAINER_NAME" > /dev/null; then
        print_status "Entering container shell..."
        docker exec -it "$CONTAINER_NAME" /bin/bash
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Function to run MCP client tests
test_mcp() {
    print_header "Testing MCP Fraud Detection"
    
    if docker ps -q -f name="$CONTAINER_NAME" > /dev/null; then
        print_status "Running MCP client tests..."
        docker exec "$CONTAINER_NAME" uv run python mcp_fraud_client.py demo
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Function to check database status
check_database() {
    print_header "Database Status Check"
    
    if docker ps -q -f name="$CONTAINER_NAME" > /dev/null; then
        print_status "Checking database status..."
        docker exec "$CONTAINER_NAME" uv run python -c "
import duckdb
import os

db_path = '/app/data/bank.db'
try:
    conn = duckdb.connect(db_path)
    customers = conn.execute('SELECT COUNT(*) FROM customer_profiles').fetchone()[0]
    transactions = conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
    print(f'✅ Database operational: {customers} customers, {transactions} transactions')
    conn.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"
    else
        print_error "Container is not running"
        exit 1
    fi
}

# Function to backup data
backup_data() {
    print_header "Backing Up Fraud Detection Data"
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="fraud_backup_$timestamp.tar.gz"
    
    print_status "Creating backup: $backup_file"
    if tar -czf "$backup_file" -C "$SCRIPT_DIR" data logs; then
        print_status "✅ Backup created successfully: $backup_file"
    else
        print_error "❌ Failed to create backup"
        exit 1
    fi
}

# Function to restore data
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup file to restore"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_header "Restoring Fraud Detection Data"
    print_warning "This will overwrite existing data. Continue? (y/N)"
    read -r confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        print_status "Restoring from: $backup_file"
        if tar -xzf "$backup_file" -C "$SCRIPT_DIR"; then
            print_status "✅ Data restored successfully"
            print_status "Restart the container to apply changes"
        else
            print_error "❌ Failed to restore data"
            exit 1
        fi
    else
        print_status "Restore cancelled"
    fi
}

# Function to clean up Docker resources
cleanup() {
    print_header "Cleaning Up Docker Resources"
    
    print_status "Stopping and removing containers..."
    docker-compose -f "$COMPOSE_FILE" down -v
    
    print_status "Removing unused images..."
    docker image prune -f
    
    print_status "✅ Cleanup completed"
}

# Main script logic
case "$1" in
    build)
        check_docker
        build_image
        ;;
    start)
        check_docker
        start_container
        ;;
    stop)
        check_docker
        stop_container
        ;;
    restart)
        check_docker
        restart_container
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        check_docker
        show_logs
        ;;
    shell)
        check_docker
        shell_access
        ;;
    test)
        check_docker
        test_mcp
        ;;
    db-status)
        check_docker
        check_database
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    cleanup)
        check_docker
        cleanup
        ;;
    *)
        echo "Docker Management Script for Banking Fraud Detection MCP Server"
        echo ""
        echo "Usage: $0 {build|start|stop|restart|status|logs|shell|test|db-status|backup|restore|cleanup}"
        echo ""
        echo "Container Management:"
        echo "  build       - Build the Docker image"
        echo "  start       - Start the container"
        echo "  stop        - Stop the container"
        echo "  restart     - Restart the container"
        echo "  status      - Show container status"
        echo "  logs        - Show container logs (follow mode)"
        echo "  shell       - Access container shell"
        echo ""
        echo "Application Commands:"
        echo "  test        - Run MCP client tests"
        echo "  db-status   - Check database status"
        echo ""
        echo "Data Management:"
        echo "  backup      - Backup application data"
        echo "  restore     - Restore from backup file"
        echo "  cleanup     - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 build                    # Build the image"
        echo "  $0 start                    # Start the container"
        echo "  $0 test                     # Run fraud detection tests"
        echo "  $0 restore backup.tar.gz    # Restore from backup"
        exit 1
        ;;
esac
