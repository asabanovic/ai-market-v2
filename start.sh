#!/bin/bash

# AI Pijaca - Full Stack Startup Script
# Starts database, backend, and frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Log file
LOG_FILE="$PROJECT_DIR/startup.log"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           AI Pijaca - Full Stack Startup                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
    return $?
}

# Function to wait for a service
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=0

    echo -n "   Waiting for $service to be ready"
    while ! check_port $port; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e " ${RED}✗${NC}"
            echo -e "${RED}   Error: $service failed to start after $max_attempts seconds${NC}"
            return 1
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${GREEN}✓${NC}"
    return 0
}

# Step 1: Check Docker
echo -e "${YELLOW}[1/6]${NC} Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "   ${YELLOW}Docker not running. Starting Docker Desktop...${NC}"
    open -a Docker
    echo -n "   Waiting for Docker to start"
    max_wait=60
    elapsed=0
    while ! docker info > /dev/null 2>&1; do
        if [ $elapsed -ge $max_wait ]; then
            echo -e " ${RED}✗${NC}"
            echo -e "${RED}   Error: Docker failed to start after $max_wait seconds${NC}"
            exit 1
        fi
        echo -n "."
        sleep 2
        ((elapsed+=2))
    done
    echo -e " ${GREEN}✓${NC}"
else
    echo -e "   ${GREEN}✓${NC} Docker is running"
fi

# Step 2: Start/Check PostgreSQL with pgvector
echo -e "${YELLOW}[2/6]${NC} Setting up PostgreSQL with pgvector..."

if docker ps -a --format '{{.Names}}' | grep -q "^pgvector$"; then
    if docker ps --format '{{.Names}}' | grep -q "^pgvector$"; then
        echo -e "   ${GREEN}✓${NC} pgvector container is already running"
    else
        echo -e "   ${YELLOW}Starting existing pgvector container...${NC}"
        docker start pgvector > /dev/null
        echo -e "   ${GREEN}✓${NC} pgvector container started"
    fi
else
    echo -e "   ${YELLOW}Creating pgvector container...${NC}"
    docker run -d \
        --name pgvector \
        -e POSTGRES_PASSWORD=devpass \
        -p 5432:5432 \
        pgvector/pgvector:pg16 > /dev/null
    echo -e "   ${GREEN}✓${NC} pgvector container created and started"
fi

# Wait for PostgreSQL to be ready
echo -n "   Waiting for PostgreSQL to be ready"
max_wait=30
elapsed=0
while ! docker exec pgvector pg_isready -U postgres > /dev/null 2>&1; do
    if [ $elapsed -ge $max_wait ]; then
        echo -e " ${RED}✗${NC}"
        echo -e "${RED}   Error: PostgreSQL failed to be ready after $max_wait seconds${NC}"
        exit 1
    fi
    echo -n "."
    sleep 1
    ((elapsed++))
done
echo -e " ${GREEN}✓${NC}"

# Ensure database and extension exist
echo -e "   ${YELLOW}Checking database setup...${NC}"
if ! docker exec pgvector psql -U postgres -lqt | cut -d \| -f 1 | grep -qw ai_pijaca; then
    echo -e "   ${YELLOW}Creating ai_pijaca database...${NC}"
    docker exec pgvector psql -U postgres -c "CREATE DATABASE ai_pijaca;" > /dev/null
fi

docker exec pgvector psql -U postgres -d ai_pijaca -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null 2>&1
echo -e "   ${GREEN}✓${NC} Database ready (ai_pijaca with pgvector extension)"

# Step 3: Check Backend Dependencies
echo -e "${YELLOW}[3/6]${NC} Checking backend dependencies..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ] && [ ! -f "requirements.txt" ]; then
    echo -e "   ${YELLOW}Note: No virtual environment found, using system Python${NC}"
fi

# Check if key dependencies are installed
if ! /usr/local/bin/python3.11 -c "import flask" 2>/dev/null; then
    echo -e "   ${YELLOW}Installing backend dependencies...${NC}"
    /usr/local/bin/python3.11 -m pip install -r requirements.txt > /dev/null 2>&1 || true
fi
echo -e "   ${GREEN}✓${NC} Backend dependencies ready"

# Step 4: Start Backend
echo -e "${YELLOW}[4/6]${NC} Starting backend (Flask)..."

# Kill any existing backend processes
if check_port 5001; then
    echo -e "   ${YELLOW}Stopping existing backend on port 5001...${NC}"
    lsof -ti:5001 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start backend in background
cd "$BACKEND_DIR"
PYTHONUNBUFFERED=1
nohup /usr/local/bin/python3.11 -u main.py > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$PROJECT_DIR/.backend.pid"

if wait_for_service 5001 "backend"; then
    echo -e "   ${GREEN}✓${NC} Backend started successfully"
    echo -e "   ${BLUE}→${NC} Backend running at http://localhost:5001"
    echo -e "   ${BLUE}→${NC} PID: $BACKEND_PID"
else
    echo -e "${RED}   Failed to start backend. Check logs: $LOG_FILE${NC}"
    exit 1
fi

# Step 5: Check Frontend Dependencies
echo -e "${YELLOW}[5/6]${NC} Checking frontend dependencies..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo -e "   ${YELLOW}Installing frontend dependencies...${NC}"
    npm install > /dev/null 2>&1
fi
echo -e "   ${GREEN}✓${NC} Frontend dependencies ready"

# Step 6: Start Frontend
echo -e "${YELLOW}[6/6]${NC} Starting frontend (Nuxt)..."

# Kill any existing frontend processes
if check_port 3000; then
    echo -e "   ${YELLOW}Stopping existing frontend on port 3000...${NC}"
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start frontend in background using Node 20 via nvm
cd "$FRONTEND_DIR"
# Source nvm and use Node 20 for Nuxt compatibility
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20 > /dev/null 2>&1 || echo -e "   ${YELLOW}Note: nvm not found, using system Node${NC}"
nohup npm run dev > "$LOG_FILE.frontend" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$PROJECT_DIR/.frontend.pid"

if wait_for_service 3000 "frontend"; then
    echo -e "   ${GREEN}✓${NC} Frontend started successfully"
    echo -e "   ${BLUE}→${NC} Frontend running at http://localhost:3000"
    echo -e "   ${BLUE}→${NC} PID: $FRONTEND_PID"
else
    echo -e "${RED}   Failed to start frontend. Check logs: $LOG_FILE.frontend${NC}"
    exit 1
fi

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              All services started successfully!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  • Database:  ${GREEN}PostgreSQL${NC} (pgvector) - localhost:5432"
echo -e "  • Backend:   ${GREEN}Flask${NC} - http://localhost:5001"
echo -e "  • Frontend:  ${GREEN}Nuxt${NC} - http://localhost:3000"
echo ""
echo -e "${BLUE}Management:${NC}"
echo -e "  • View logs:     tail -f $LOG_FILE"
echo -e "  • Stop all:      ./stop.sh"
echo -e "  • Check status:  docker ps && ps -p $BACKEND_PID && ps -p $FRONTEND_PID"
echo ""
echo -e "${BLUE}Database:${NC}"
echo -e "  • Connect: docker exec -it pgvector psql -U postgres -d ai_pijaca"
echo -e "  • Refresh embeddings: cd backend && /usr/local/bin/python3.11 refresh_embeddings.py"
echo ""
echo -e "${YELLOW}Press Ctrl+C or run ./stop.sh to stop all services${NC}"
echo ""

# Keep script running to show it's active
# Wait for Ctrl+C
trap "echo ''; echo 'Use ./stop.sh to stop all services'; exit 0" INT TERM

# Optional: Follow logs
if [ "$1" = "--logs" ] || [ "$1" = "-l" ]; then
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    echo ""
    tail -f "$LOG_FILE"
else
    echo -e "${BLUE}Tip:${NC} Run ${GREEN}./start.sh --logs${NC} to follow the logs"
    # Keep running but don't block terminal
    wait
fi
