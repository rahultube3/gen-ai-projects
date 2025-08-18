#!/bin/bash
"""
Claude Desktop Integration Setup Script
Helps configure Claude Desktop to work with MCP microservices.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Detect operating system
get_claude_config_path() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "$HOME/.config/claude/claude_desktop_config.json"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Check if Claude Desktop is installed
check_claude_desktop() {
    local config_path=$(get_claude_config_path)
    local config_dir=$(dirname "$config_path")
    
    if [ ! -d "$config_dir" ]; then
        print_error "Claude Desktop configuration directory not found: $config_dir"
        print_warning "Please install Claude Desktop first from: https://claude.ai/download"
        return 1
    fi
    
    print_success "Claude Desktop configuration directory found"
    return 0
}

# Show available configuration options
show_config_options() {
    print_status "Available Claude Desktop configurations:"
    echo
    echo "1. Gateway Only (Recommended) - Single entry point through gateway service"
    echo "2. All Services - All 5 microservices individually accessible"
    echo "3. Custom - Manual configuration"
    echo
}

# Copy configuration to Claude Desktop
copy_config() {
    local config_choice=$1
    local claude_config_path=$(get_claude_config_path)
    local source_config=""
    
    case $config_choice in
        1)
            source_config="claude_desktop_gateway_only.json"
            print_status "Using Gateway-only configuration..."
            ;;
        2)
            source_config="claude_desktop_config.json"
            print_status "Using all services configuration..."
            ;;
        *)
            print_error "Invalid configuration choice"
            return 1
            ;;
    esac
    
    if [ ! -f "$source_config" ]; then
        print_error "Configuration file not found: $source_config"
        return 1
    fi
    
    # Backup existing config if it exists
    if [ -f "$claude_config_path" ]; then
        local backup_path="${claude_config_path}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$claude_config_path" "$backup_path"
        print_warning "Existing configuration backed up to: $backup_path"
    fi
    
    # Copy new configuration
    cp "$source_config" "$claude_config_path"
    print_success "Configuration copied to: $claude_config_path"
}

# Test MCP connection
test_mcp_connection() {
    print_status "Testing MCP service connection..."
    
    # Test gateway service
    echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | \
    uv run python services/gateway_mcp_service.py > /dev/null 2>&1 &
    
    local pid=$!
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        kill $pid
        print_success "Gateway service is responding to MCP requests"
    else
        print_error "Gateway service failed to respond"
        return 1
    fi
}

# Show setup instructions
show_instructions() {
    print_status "Claude Desktop Integration Setup Complete!"
    echo
    print_success "Next Steps:"
    echo "1. Restart Claude Desktop application"
    echo "2. The MCP services should appear in Claude Desktop"
    echo "3. You can now use the following tools:"
    echo
    if [ -f "claude_desktop_gateway_only.json" ]; then
        echo "   Gateway Service Tools:"
        echo "   • unified_search - Search products with AI recommendations"
        echo "   • smart_chat - Intelligent conversational interface"  
        echo "   • complete_order_flow - Order management with analytics"
        echo "   • personalized_dashboard - Generate user dashboards"
        echo "   • service_health_check - Check all services status"
        echo "   • cross_service_analytics - Generate cross-service analytics"
    fi
    echo
    print_warning "Make sure MongoDB is running before using the services!"
    echo
    print_status "Test the integration by asking Claude:"
    echo '   "Can you search for laptops using the unified search?"'
    echo '   "Show me a personalized dashboard for user user123"'
    echo '   "Check the health of all services"'
}

# Main function
main() {
    echo "🚀 Claude Desktop MCP Integration Setup"
    echo "======================================"
    
    # Check if we're in the right directory
    if [ ! -f "services/gateway_mcp_service.py" ]; then
        print_error "Please run this script from the e-commerce-assistant directory"
        exit 1
    fi
    
    # Check Claude Desktop installation
    if ! check_claude_desktop; then
        exit 1
    fi
    
    # Show configuration options
    show_config_options
    
    # Get user choice
    read -p "Choose configuration (1-3): " choice
    
    case $choice in
        1|2)
            copy_config $choice
            test_mcp_connection
            show_instructions
            ;;
        3)
            print_status "For custom configuration, edit the files:"
            echo "  • claude_desktop_config.json (all services)"
            echo "  • claude_desktop_gateway_only.json (gateway only)"
            echo
            print_status "Then copy to: $(get_claude_config_path)"
            ;;
        *)
            print_error "Invalid choice. Please run the script again."
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
