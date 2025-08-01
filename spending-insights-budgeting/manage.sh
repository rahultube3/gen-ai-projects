#!/bin/bash

# =============================================================================
# Advanced Spending Insights & Budgeting - Project Management Script
# =============================================================================
# 
# This script provides comprehensive management capabilities for the
# Advanced Spending Insights & Budgeting application.
#
# Usage: ./manage.sh [command] [options]
#
# Commands:
#   setup       - Initial project setup
#   install     - Install dependencies
#   dev         - Start development server
#   test        - Run tests
#   build       - Build the application
#   deploy      - Deploy using Docker
#   clean       - Clean up temporary files
#   backup      - Backup database and data
#   restore     - Restore from backup
#   logs        - View application logs
#   status      - Check application status
#   help        - Show this help message
#
# =============================================================================

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
PROJECT_NAME="Advanced Spending Insights & Budgeting"
VERSION="1.0.0"
PYTHON_VERSION="3.11"
STREAMLIT_PORT="8501"
API_PORT="8000"
DB_FILE="spending_insights.db"
BACKUP_DIR="backups"
LOG_DIR="logs"
DATA_DIR="data"
VECTORSTORE_DIR="vectorstore_cache"

# Utility functions
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

log_header() {
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}========================================${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11 or later."
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$python_version < 3.11" | bc -l) -eq 1 ]]; then
        log_warning "Python version $python_version detected. Python 3.11+ recommended."
    else
        log_info "Python version $python_version detected."
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed. Docker deployment features will be unavailable."
        return 1
    fi
    log_info "Docker is available."
    return 0
}

create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p "$BACKUP_DIR" "$LOG_DIR" "$DATA_DIR" "$VECTORSTORE_DIR"
    log_success "Directories created successfully."
}

# Command functions
cmd_setup() {
    log_header "Setting up $PROJECT_NAME"
    
    check_python
    create_directories
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created."
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success ".env file created from template."
            log_warning "Please edit .env file with your configuration."
        else
            log_warning ".env.example not found. Creating basic .env file."
            cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
STREAMLIT_PORT=8501
DEBUG=false
LOG_LEVEL=INFO

# Database Settings
DATABASE_URL=sqlite:///spending_insights.db

# Privacy Settings
REDACTION_LEVEL=medium
EOF
            log_success "Basic .env file created. Please update with your settings."
        fi
    fi
    
    log_success "Setup completed! Run './manage.sh install' to install dependencies."
}

cmd_install() {
    echo "========================================"
    echo "Installing Dependencies"
    echo "========================================"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "[INFO] Virtual environment activated."
    else
        echo "[ERROR] Virtual environment not found. Run './manage.sh setup' first."
        exit 1
    fi
    
    # Upgrade pip
    echo "[INFO] Installing Python dependencies..."
    python -m pip install --upgrade pip
    
    # Install from clean requirements file first
    if [ -f "requirements_clean.txt" ]; then
        echo "[INFO] Using requirements_clean.txt..."
        pip install -r requirements_clean.txt
    elif [ -f "requirements_docker.txt" ]; then
        echo "[INFO] Using requirements_docker.txt (without editable installs)..."
        pip install -r requirements_docker.txt
    elif [ -f "requirements.txt" ]; then
        echo "[INFO] Using requirements.txt (may have issues with editable installs)..."
        pip install -r requirements.txt
    else
        echo "[INFO] No requirements file found. Installing core dependencies..."
        pip install streamlit openai langchain langchain-openai langchain-community duckdb faiss-cpu python-dotenv pandas numpy requests plotly
    fi
    
    echo "[SUCCESS] Dependencies installed successfully."
    
    # Setup database
    echo "[INFO] Setting up database..."
    if [ -f "db_setup.py" ]; then
        python db_setup.py
    else
        echo "[WARNING] db_setup.py not found. Database setup skipped."
    fi
    
    echo "[SUCCESS] Database setup completed."
}

cmd_dev() {
    echo "========================================"
    echo "Starting Development Server"
    echo "========================================"
    
    # Check if virtual environment exists and create if needed
    if [ ! -d "venv" ]; then
        echo "[INFO] Virtual environment not found. Creating..."
        cmd_setup
    fi
    
    # Use virtual environment Python directly
    VENV_PYTHON="venv/bin/python"
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "[ERROR] Virtual environment Python not found. Try './manage.sh setup' first."
        exit 1
    fi
    
    # Check if streamlit is available in venv
    if ! $VENV_PYTHON -c "import streamlit" &> /dev/null; then
        echo "[INFO] Streamlit not found in virtual environment. Installing dependencies..."
        cmd_install
    fi
    
    echo "[INFO] Starting Streamlit development server..."
    echo "[INFO] Access the application at: http://localhost:8501"
    echo "[INFO] Press Ctrl+C to stop the server"
    echo ""
    
    # Run using virtual environment Python directly
    $VENV_PYTHON -m streamlit run streamlit_app.py --server.port 8501
}

cmd_test() {
    log_header "Running Tests"
    
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
    fi
    
    # Run Python tests if they exist
    if [ -d "tests" ]; then
        log_info "Running Python tests..."
        python -m pytest tests/ -v
    else
        log_info "Running basic application validation..."
        python -c "
import streamlit_app
import db_setup
import vectorstore
print('✅ All imports successful')
print('✅ Application structure validated')
"
    fi
    
    log_success "Tests completed successfully."
}

cmd_build() {
    log_header "Building Application"
    
    if check_docker; then
        log_info "Building Docker image..."
        if [ -f "docker-manage.sh" ]; then
            chmod +x docker-manage.sh
            ./docker-manage.sh build
        else
            docker build -t spending-insights:latest .
        fi
        log_success "Docker image built successfully."
    else
        log_info "Building Python package..."
        if [[ "$VIRTUAL_ENV" == "" ]]; then
            if [ -f "venv/bin/activate" ]; then
                source venv/bin/activate
            fi
        fi
        
        # Create requirements_docker.txt if it doesn't exist
        if [ ! -f "requirements_docker.txt" ]; then
            grep -v "^-e" requirements.txt > requirements_docker.txt
            log_info "Created requirements_docker.txt"
        fi
        
        log_success "Application prepared for deployment."
    fi
}

cmd_deploy() {
    log_header "Deploying Application"
    
    if check_docker; then
        if [ -f "docker-manage.sh" ]; then
            chmod +x docker-manage.sh
            log_info "Using Docker deployment..."
            ./docker-manage.sh start
        else
            log_info "Starting Docker container..."
            docker run -d \
                --name spending-insights \
                -p $STREAMLIT_PORT:8501 \
                -v "$(pwd)/data:/app/data" \
                -v "$(pwd)/logs:/app/logs" \
                spending-insights:latest
        fi
        log_success "Application deployed successfully."
        log_info "Access the application at: http://localhost:$STREAMLIT_PORT"
    else
        log_error "Docker not available. Use './manage.sh dev' for local development."
        exit 1
    fi
}

cmd_clean() {
    log_header "Cleaning Up"
    
    log_info "Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    log_info "Cleaning up temporary files..."
    rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
    
    if check_docker; then
        log_info "Cleaning up Docker resources..."
        docker system prune -f >/dev/null 2>&1 || true
    fi
    
    log_success "Cleanup completed."
}

cmd_backup() {
    log_header "Creating Backup"
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
    
    log_info "Creating backup: $backup_file"
    
    tar -czf "$backup_file" \
        --exclude="venv" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".git" \
        --exclude="$BACKUP_DIR" \
        .
    
    log_success "Backup created: $backup_file"
    
    # Keep only last 10 backups
    ls -t "$BACKUP_DIR"/backup_*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true
}

cmd_restore() {
    log_header "Restoring from Backup"
    
    if [ -z "$1" ]; then
        log_info "Available backups:"
        ls -la "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null || {
            log_error "No backups found."
            exit 1
        }
        log_info "Usage: ./manage.sh restore <backup_file>"
        exit 1
    fi
    
    backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warning "This will overwrite current files. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Restoring from: $backup_file"
        tar -xzf "$backup_file"
        log_success "Restore completed."
    else
        log_info "Restore cancelled."
    fi
}

cmd_logs() {
    log_header "Application Logs"
    
    if check_docker && docker ps | grep -q spending-insights; then
        log_info "Showing Docker container logs..."
        docker logs -f spending-insights
    elif [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR)" ]; then
        log_info "Showing application logs..."
        tail -f "$LOG_DIR"/*.log 2>/dev/null || {
            log_info "No log files found. Starting fresh log monitor..."
            mkdir -p "$LOG_DIR"
            touch "$LOG_DIR/app.log"
            tail -f "$LOG_DIR/app.log"
        }
    else
        log_info "No logs available. Run the application to generate logs."
    fi
}

cmd_status() {
    log_header "Application Status"
    
    # Check Python environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        log_success "Virtual environment: Active ($VIRTUAL_ENV)"
    elif [ -d "venv" ]; then
        log_warning "Virtual environment: Available but not activated"
    else
        log_error "Virtual environment: Not found"
    fi
    
    # Check dependencies
    if [ -f "requirements.txt" ]; then
        log_success "Dependencies: requirements.txt found"
    else
        log_error "Dependencies: requirements.txt missing"
    fi
    
    # Check database
    if [ -f "$DB_FILE" ]; then
        log_success "Database: $DB_FILE exists"
    else
        log_warning "Database: $DB_FILE not found"
    fi
    
    # Check configuration
    if [ -f ".env" ]; then
        log_success "Configuration: .env file exists"
    else
        log_warning "Configuration: .env file missing"
    fi
    
    # Check Docker status
    if check_docker; then
        if docker ps | grep -q spending-insights; then
            log_success "Docker: Container running"
        else
            log_info "Docker: Available but container not running"
        fi
    fi
    
    # Check ports
    if netstat -tuln 2>/dev/null | grep -q ":$STREAMLIT_PORT "; then
        log_success "Port $STREAMLIT_PORT: In use (application may be running)"
    else
        log_info "Port $STREAMLIT_PORT: Available"
    fi
}

cmd_help() {
    echo -e "${CYAN}$PROJECT_NAME - Management Script${NC}"
    echo -e "${CYAN}Version: $VERSION${NC}"
    echo ""
    echo "Usage: ./manage.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  setup       Initial project setup and configuration"
    echo "  install     Install Python dependencies"
    echo "  dev         Start development server (Streamlit)"
    echo "  test        Run tests and validation"
    echo "  build       Build application (Docker image)"
    echo "  deploy      Deploy application using Docker"
    echo "  clean       Clean up temporary files and cache"
    echo "  backup      Create backup of project"
    echo "  restore     Restore from backup file"
    echo "  logs        View application logs"
    echo "  status      Check application and environment status"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./manage.sh setup           # Initial setup"
    echo "  ./manage.sh install         # Install dependencies"
    echo "  ./manage.sh dev             # Start development server"
    echo "  ./manage.sh deploy          # Deploy with Docker"
    echo "  ./manage.sh backup          # Create backup"
    echo "  ./manage.sh logs            # View logs"
    echo ""
    echo "For more information, see README.md"
}

# Main script logic
main() {
    case "${1:-help}" in
        setup)
            cmd_setup
            ;;
        install)
            cmd_install
            ;;
        dev|start)
            cmd_dev
            ;;
        test)
            cmd_test
            ;;
        build)
            cmd_build
            ;;
        deploy)
            cmd_deploy
            ;;
        clean)
            cmd_clean
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$2"
            ;;
        logs)
            cmd_logs
            ;;
        status)
            cmd_status
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Unknown command: $1"
            cmd_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
