#!/bin/bash

###############################################################################
# Startup Script for Code Review System (Backend + Frontend)
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Trap to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM

print_header "Starting Code Review System"

# Check if ports are available
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
    print_error "Port 5000 is already in use. Stopping existing process..."
    fuser -k 5000/tcp 2>/dev/null || true
    sleep 2
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    print_error "Port 5173 is already in use. Stopping existing process..."
    fuser -k 5173/tcp 2>/dev/null || true
    sleep 2
fi

# Start Backend
print_info "Starting Flask backend on port 5000..."
cd "$SCRIPT_DIR"
python3 main.py > /tmp/flask_backend.log 2>&1 &
BACKEND_PID=$!
print_success "Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo -n "Waiting for backend to be ready"
for i in {1..20}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo ""
        print_success "Backend is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# Start Frontend
print_info "Starting React frontend on port 5173..."
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_info "Installing frontend dependencies..."
    npm install
fi

npm run dev > /tmp/vite_frontend.log 2>&1 &
FRONTEND_PID=$!
print_success "Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to be ready
echo -n "Waiting for frontend to be ready"
for i in {1..20}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo ""
        print_success "Frontend is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

print_header "System is Running"
echo -e "${GREEN}Backend:${NC}  http://localhost:5000"
echo -e "${GREEN}Frontend:${NC} http://localhost:5173"
echo -e "${GREEN}API Docs:${NC} http://localhost:5000/api/auth/register"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  Backend:  tail -f /tmp/flask_backend.log"
echo -e "  Frontend: tail -f /tmp/vite_frontend.log"

# Keep script running
wait
