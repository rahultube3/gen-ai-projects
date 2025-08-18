#!/bin/bash

# HR Assistant Docker Management Script
# This script helps manage the HR Assistant Docker deployment

set -e  # Exit on any error

PROJECT_NAME="hr-assistant"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
DOCKER_COMPOSE_CMD=""  # Will be set by check_docker function

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        warning ".env file not found!"
        log "Copying .env.docker template to .env..."
        if [ -f ".env.docker" ]; then
            cp .env.docker .env
            warning "Please edit .env file and add your OpenAI API key and other configuration"
            echo "Required changes:"
            echo "  - OPENAI_API_KEY=your_actual_api_key"
            echo "  - MONGO_PASSWORD=your_secure_password"
            echo ""
            read -p "Press Enter after updating .env file..."
        else
            error ".env.docker template not found!"
            exit 1
        fi
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop or Docker daemon."
        exit 1
    fi
    success "Docker is running"
    
    # Check if docker compose is available
    if docker compose version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif docker-compose --version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        error "Neither 'docker compose' nor 'docker-compose' is available."
        error "Please install Docker Desktop or docker-compose plugin."
        exit 1
    fi
    log "Using Docker Compose command: $DOCKER_COMPOSE_CMD"
}

# Function to build all images
build_images() {
    log "Building Docker images..."
    $DOCKER_COMPOSE_CMD build --no-cache
    success "All images built successfully"
}

# Function to start services
start_services() {
    log "Starting HR Assistant services..."
    $DOCKER_COMPOSE_CMD up -d
    
    # Wait for services to be healthy
    log "Waiting for services to become healthy..."
    sleep 10
    
    # Check service status
    check_services
}

# Function to stop services
stop_services() {
    log "Stopping HR Assistant services..."
    $DOCKER_COMPOSE_CMD down
    success "All services stopped"
}

# Function to restart services
restart_services() {
    log "Restarting HR Assistant services..."
    $DOCKER_COMPOSE_CMD down
    $DOCKER_COMPOSE_CMD up -d
    sleep 10
    check_services
}

# Function to check service health
check_services() {
    log "Checking service health..."
    
    services=("mongodb" "rag-api" "comprehensive-api" "streamlit-chat")
    all_healthy=true
    
    for service in "${services[@]}"; do
        if $DOCKER_COMPOSE_CMD ps "$service" | grep -q "healthy\|running"; then
            success "$service is running"
        else
            error "$service is not healthy"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        success "All services are healthy!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Streamlit Chat: http://localhost:8501"
        echo "   RAG API: http://localhost:8001"
        echo "   Comprehensive API: http://localhost:8002"
        echo "   MongoDB: mongodb://localhost:27017"
    else
        warning "Some services are not healthy. Check logs with: $0 logs"
    fi
}

# Function to show logs
show_logs() {
    if [ -n "$1" ]; then
        log "Showing logs for $1..."
        $DOCKER_COMPOSE_CMD logs -f "$1"
    else
        log "Showing logs for all services..."
        $DOCKER_COMPOSE_CMD logs -f
    fi
}

# Function to clean up
cleanup() {
    log "Cleaning up Docker resources..."
    $DOCKER_COMPOSE_CMD down -v --remove-orphans
    docker system prune -f
    success "Cleanup completed"
}

# Function to setup data
setup_data() {
    log "Setting up initial data..."
    
    # Wait for services to be ready
    sleep 15
    
    # Check if rag-api is responding
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        log "Initializing document store..."
        # You can add data initialization commands here
        success "Data setup completed"
    else
        error "RAG API is not responding. Please check service health."
    fi
}

# Function to backup data
backup_data() {
    log "Creating data backup..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_dir="backups/docker_backup_$timestamp"
    mkdir -p "$backup_dir"
    
    # Export MongoDB data
    $DOCKER_COMPOSE_CMD exec -T mongodb mongodump --uri="mongodb://admin:secure_password_change_this@localhost:27017/hr_assistant?authSource=admin" --out="/tmp/backup"
    docker cp $($DOCKER_COMPOSE_CMD ps -q mongodb):/tmp/backup "$backup_dir/mongodb"
    
    success "Backup created in $backup_dir"
}

# Function to show usage
show_usage() {
    echo "HR Assistant Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  build       Build all Docker images"
    echo "  status      Check service health"
    echo "  logs [svc]  Show logs (optionally for specific service)"
    echo "  setup       Setup initial data"
    echo "  backup      Backup MongoDB data"
    echo "  cleanup     Clean up Docker resources"
    echo "  shell [svc] Open shell in service container"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start all services"
    echo "  $0 logs streamlit     # Show Streamlit logs"
    echo "  $0 shell mongodb      # Open MongoDB shell"
}

# Function to open shell in container
open_shell() {
    if [ -n "$1" ]; then
        log "Opening shell in $1..."
        $DOCKER_COMPOSE_CMD exec "$1" /bin/bash
    else
        error "Please specify a service name"
        echo "Available services: mongodb, rag-api, comprehensive-api, streamlit-chat"
    fi
}

# Main script logic
case "$1" in
    "start")
        check_docker
        check_env_file
        start_services
        ;;
    "stop")
        check_docker
        stop_services
        ;;
    "restart")
        check_docker
        restart_services
        ;;
    "build")
        check_docker
        build_images
        ;;
    "status")
        check_docker
        check_services
        ;;
    "logs")
        check_docker
        show_logs "$2"
        ;;
    "setup")
        check_docker
        setup_data
        ;;
    "backup")
        check_docker
        backup_data
        ;;
    "cleanup")
        check_docker
        cleanup
        ;;
    "shell")
        check_docker
        open_shell "$2"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
