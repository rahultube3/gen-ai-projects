#!/bin/bash

# Legal Chatbot Startup Script
# This script starts both the backend RAG API and the Angular frontend

echo "🚀 Starting Legal Document Chatbot..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to start
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=60
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service_name to start on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            echo -e "${GREEN}✅ $service_name is running on port $port${NC}"
            return 0
        fi
        
        # Show different messages for frontend vs backend
        if [[ "$service_name" == "Frontend Server" ]] && (( attempt % 5 == 0 )); then
            echo -e "${YELLOW}⏳ Attempt $attempt/$max_attempts - Angular is building, please wait...${NC}"
        elif [[ "$service_name" != "Frontend Server" ]]; then
            echo -e "${YELLOW}Attempt $attempt/$max_attempts - waiting for $service_name...${NC}"
        fi
        
        sleep 3
        ((attempt++))
    done
    
    echo -e "${RED}❌ Failed to start $service_name on port $port${NC}"
    return 1
}

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Backend API stopped${NC}"
    fi
    
    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${GREEN}✅ Frontend server stopped${NC}"
    fi
    
    # Kill any remaining processes on our ports
    pkill -f "uvicorn.*api_server:app" 2>/dev/null
    pkill -f "ng serve" 2>/dev/null
    
    echo -e "${GREEN}🎉 All services stopped successfully${NC}"
    exit 0
}

# Trap cleanup function on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if required directories exist
if [ ! -d "../legal-document-review" ]; then
    echo -e "${RED}❌ Backend directory 'legal-document-review' not found${NC}"
    exit 1
fi

if [ ! -d "." ]; then
    echo -e "${RED}❌ Frontend directory 'legal-chatbot' not found${NC}"
    exit 1
fi

# Start Backend API
echo -e "${BLUE}🔧 Starting Backend API...${NC}"
cd ../legal-document-review

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt

# Start the backend API in the background
echo -e "${BLUE}🚀 Launching FastAPI server...${NC}"
python api_server.py &
BACKEND_PID=$!

# Wait for backend to start
if ! wait_for_service 8000 "Backend API"; then
    echo -e "${RED}❌ Failed to start backend API${NC}"
    exit 1
fi

# Go back to root directory and then to frontend
cd ..

# Start Frontend
echo -e "${BLUE}🔧 Starting Frontend...${NC}"
cd legal-chatbot

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
fi

# Start the Angular development server in the background
echo -e "${BLUE}🚀 Launching Angular development server...${NC}"
echo -e "${BLUE}⏳ First build may take 30-60 seconds, please be patient${NC}"
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
if ! wait_for_service 4200 "Frontend Server"; then
    echo -e "${RED}❌ Failed to start frontend server${NC}"
    exit 1
fi

# Success message
echo -e "\n${GREEN}🎉 Legal Document Chatbot is now running!${NC}"
echo -e "${GREEN}=================================${NC}"
echo -e "${BLUE}📱 Frontend (Angular):${NC} http://localhost:4200"
echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep the script running
while true; do
    sleep 1
done
