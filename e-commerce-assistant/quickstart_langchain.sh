#!/bin/bash

# 🚀 LangChain + MCP E-commerce Quick Start Script
# Automatically sets up and tests the complete integration

set -e  # Exit on any error

echo "🤖 LangChain + MCP E-commerce Integration Quick Start"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_info "Checking prerequisites..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_error "uv package manager not found. Please install uv first."
    exit 1
fi
print_status "uv package manager found"

# Check if we're in the right directory
if [ ! -f "langchain_agent.py" ]; then
    print_error "Not in the correct directory. Please run from e-commerce-assistant/"
    exit 1
fi
print_status "In correct directory"

# Install dependencies
print_info "Installing/updating dependencies..."
uv sync
print_status "Dependencies installed"

# Check environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY not set. Agent will need this for full functionality."
    echo "Set it with: export OPENAI_API_KEY='your-api-key-here'"
else
    print_status "OPENAI_API_KEY is set"
fi

if [ -z "$MONGODB_URI" ]; then
    print_info "Setting default MONGODB_URI..."
    export MONGODB_URI="mongodb://localhost:27017/ecommerce_assistant"
    print_status "MONGODB_URI set to default"
else
    print_status "MONGODB_URI is set"
fi

# Run integration demo
print_info "Running LangChain integration demo..."
echo ""
uv run python demo_langchain_integration.py
demo_exit_code=$?

echo ""
echo "======================================================"

if [ $demo_exit_code -eq 0 ]; then
    print_status "Integration demo completed successfully!"
else
    print_warning "Demo completed with some issues (expected without OpenAI API key)"
fi

# Provide next steps
echo ""
print_info "🚀 QUICK START OPTIONS:"
echo ""

echo "1. 🤖 Start Interactive Agent (CLI):"
echo "   uv run python langchain_agent.py"
echo ""

echo "2. 🌐 Start API Server:"
echo "   uv run python langchain_api_server.py"
echo "   Then visit: http://localhost:8001/docs"
echo ""

echo "3. 🔧 Start MCP Services (required for full functionality):"
echo "   ./orchestration/manage_services.sh start"
echo ""

echo "4. 📊 Test API Endpoints:"
echo "   curl http://localhost:8001/health"
echo ""

echo "5. 💬 Test Chat (requires API server running):"
echo "   curl -X POST \"http://localhost:8001/chat\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"message\": \"Hello, can you help me find products?\", \"user_id\": \"test\"}'"
echo ""

# Check if services are running
print_info "Checking if MCP services are already running..."
if pgrep -f "gateway_mcp_service.py" > /dev/null; then
    print_status "Gateway service is running"
else
    print_warning "MCP services not running. Start with: ./orchestration/manage_services.sh start"
fi

echo ""
print_info "📚 Documentation:"
echo "   • Integration Guide: LANGCHAIN_INTEGRATION_GUIDE.md"
echo "   • Success Summary: LANGCHAIN_SUCCESS_SUMMARY.md"
echo "   • Claude Desktop Integration: CLAUDE_DESKTOP_INTEGRATION.md"

echo ""
print_status "LangChain + MCP integration is ready! Choose an option above to get started."

# Ask user what they want to do
echo ""
read -p "Would you like to start the API server now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting API server..."
    print_info "Press Ctrl+C to stop the server"
    print_info "API Documentation will be at: http://localhost:8001/docs"
    echo ""
    uv run python langchain_api_server.py
fi

print_status "Quick start complete! Happy building! 🎉"
