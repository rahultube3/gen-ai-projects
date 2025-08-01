#!/bin/bash

# Docker Management Script for Spending Insights Project
# Usage: ./docker-manage.sh [command] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="spending-insights"
IMAGE_NAME="spending-insights"
CONTAINER_NAME="spending-insights-app"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_warning "docker-compose not found. Trying docker compose..."
        if ! docker compose version &> /dev/null; then
            log_error "Neither docker-compose nor 'docker compose' is available."
            exit 1
        fi
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
}

# Create necessary directories
setup_directories() {
    log_info "Creating necessary directories..."
    mkdir -p data backups logs vectorstore_cache
    log_success "Directories created successfully"
}

# Check environment file
check_env() {
    if [ ! -f .env ]; then
        log_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            log_warning "Please edit .env file and add your OpenAI API key"
        else
            log_error ".env.example not found. Please create .env file manually"
            exit 1
        fi
    fi
    
    # Check if OpenAI API key is set
    if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        log_warning "OpenAI API key not found in .env file"
        log_warning "Please add: OPENAI_API_KEY=your_key_here"
    fi
}

# Build Docker images
build() {
    log_info "Building Docker images..."
    setup_directories
    
    # Determine which Dockerfile to use
    DOCKERFILE_TO_USE="Dockerfile"
    if [ "$1" = "--simple" ]; then
        DOCKERFILE_TO_USE="Dockerfile.simple"
        log_info "Using simple Dockerfile (pip-based)"
        shift
    elif [ ! -f "uv.lock" ] && [ -f "requirements.txt" ]; then
        log_warning "uv.lock not found, checking if requirements.txt build works..."
        # Try to build with main Dockerfile first, fallback to simple if needed
    fi
    
    # Build main application
    log_info "Building main application with $DOCKERFILE_TO_USE..."
    if ! docker build -f "$DOCKERFILE_TO_USE" -t ${IMAGE_NAME}:latest .; then
        if [ "$DOCKERFILE_TO_USE" = "Dockerfile" ] && [ -f "Dockerfile.simple" ]; then
            log_warning "Main Dockerfile failed, trying simple Dockerfile..."
            docker build -f "Dockerfile.simple" -t ${IMAGE_NAME}:latest .
        else
            log_error "Docker build failed"
            exit 1
        fi
    fi
    
    # Build API if Dockerfile.api exists
    if [ -f "Dockerfile.api" ]; then
        log_info "Building API service..."
        docker build -f Dockerfile.api -t ${IMAGE_NAME}-api:latest .
    fi
    
    log_success "Docker images built successfully"
}

# Start services
start() {
    log_info "Starting services..."
    check_env
    setup_directories
    
    # Default profile
    PROFILE=""
    
    # Check for additional arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-api)
                PROFILE="--profile api"
                shift
                ;;
            --production)
                PROFILE="--profile production"
                shift
                ;;
            --with-backup)
                PROFILE="--profile backup"
                shift
                ;;
            --all)
                PROFILE="--profile api --profile production --profile backup"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    $DOCKER_COMPOSE_CMD up -d $PROFILE
    log_success "Services started successfully"
    
    # Show access information
    echo ""
    log_info "Access your application at:"
    echo "  🌐 Main App: http://localhost:8501"
    if [[ $PROFILE == *"api"* ]]; then
        echo "  🔗 API: http://localhost:8000"
    fi
    if [[ $PROFILE == *"production"* ]]; then
        echo "  🔧 Traefik Dashboard: http://localhost:8080"
    fi
}

# Stop services
stop() {
    log_info "Stopping services..."
    $DOCKER_COMPOSE_CMD down
    log_success "Services stopped successfully"
}

# Restart services
restart() {
    log_info "Restarting services..."
    stop
    start "$@"
}

# View logs
logs() {
    SERVICE=${1:-spending-insights}
    log_info "Showing logs for $SERVICE..."
    $DOCKER_COMPOSE_CMD logs -f $SERVICE
}

# Show status
status() {
    log_info "Service status:"
    $DOCKER_COMPOSE_CMD ps
    
    echo ""
    log_info "Docker images:"
    docker images | grep $IMAGE_NAME
    
    echo ""
    log_info "Volume usage:"
    docker system df
}

# Clean up
clean() {
    log_info "Cleaning up Docker resources..."
    
    # Stop and remove containers
    $DOCKER_COMPOSE_CMD down --volumes --remove-orphans
    
    # Remove images
    docker rmi ${IMAGE_NAME}:latest 2>/dev/null || true
    docker rmi ${IMAGE_NAME}-api:latest 2>/dev/null || true
    
    # Clean up unused resources
    docker system prune -f
    
    log_success "Cleanup completed"
}

# Backup database
backup() {
    log_info "Creating database backup..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
    
    if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        docker exec $CONTAINER_NAME cp /app/data/spending_insights.db /app/backups/$BACKUP_FILE
        log_success "Backup created: $BACKUP_FILE"
    else
        log_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Restore database
restore() {
    BACKUP_FILE=$1
    if [ -z "$BACKUP_FILE" ]; then
        log_error "Please specify backup file to restore"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    log_info "Restoring database from $BACKUP_FILE..."
    
    if docker ps --format "table {{.Names}}" | grep -q $CONTAINER_NAME; then
        docker exec $CONTAINER_NAME cp /app/backups/$BACKUP_FILE /app/data/spending_insights.db
        log_success "Database restored from $BACKUP_FILE"
        log_info "Restarting container to apply changes..."
        docker restart $CONTAINER_NAME
    else
        log_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Update application
update() {
    log_info "Updating application..."
    
    # Pull latest code (if in git repo)
    if [ -d ".git" ]; then
        git pull
    fi
    
    # Rebuild and restart
    build
    restart "$@"
    
    log_success "Application updated successfully"
}

# Development mode
dev() {
    log_info "Starting in development mode..."
    
    # Build with development target if exists
    if grep -q "as development" Dockerfile; then
        docker build --target development -t ${IMAGE_NAME}:dev .
    else
        build
    fi
    
    # Mount source code for live reloading
    docker run -it --rm \
        -p 8501:8501 \
        -v $(pwd):/app \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/vectorstore_cache:/app/vectorstore_cache \
        --env-file .env \
        ${IMAGE_NAME}:latest \
        streamlit run streamlit_app.py --server.address=0.0.0.0 --server.fileWatcherType=poll
}

# Show help
help() {
    echo "Docker Management Script for Spending Insights Project"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build [--simple]       Build Docker images (--simple for pip-based build)"
    echo "  start              Start all services"
    echo "    --with-api       Include FastAPI backend"
    echo "    --production     Include reverse proxy"
    echo "    --with-backup    Include backup service"
    echo "    --all            Include all optional services"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  logs [service]     Show logs (default: spending-insights)"
    echo "  status             Show service status"
    echo "  clean              Clean up Docker resources"
    echo "  backup             Create database backup"
    echo "  restore <file>     Restore database from backup"
    echo "  update             Update and restart application"
    echo "  dev                Start in development mode"
    echo "  help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start basic application"
    echo "  $0 start --with-api         # Start with FastAPI backend"
    echo "  $0 start --all              # Start all services"
    echo "  $0 logs spending-insights   # Show app logs"
    echo "  $0 backup                   # Create backup"
    echo "  $0 restore backup.db        # Restore from backup"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            shift
            build "$@"
            ;;
        start)
            shift
            start "$@"
            ;;
        stop)
            stop
            ;;
        restart)
            shift
            restart "$@"
            ;;
        logs)
            shift
            logs "$@"
            ;;
        status)
            status
            ;;
        clean)
            clean
            ;;
        backup)
            backup
            ;;
        restore)
            shift
            restore "$@"
            ;;
        update)
            shift
            update "$@"
            ;;
        dev)
            dev
            ;;
        help|--help|-h)
            help
            ;;
        *)
            log_error "Unknown command: $1"
            help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
