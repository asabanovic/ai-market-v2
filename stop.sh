#!/bin/bash

# AI Pijaca - Stop All Services Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            AI Pijaca - Stopping All Services              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop Frontend
echo -e "${YELLOW}[1/3]${NC} Stopping frontend..."
if [ -f "$PROJECT_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_DIR/.frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "   ${GREEN}✓${NC} Frontend stopped (PID: $FRONTEND_PID)"
    else
        echo -e "   ${YELLOW}→${NC} Frontend was not running"
    fi
    rm "$PROJECT_DIR/.frontend.pid"
else
    # Fallback: kill by port
    if lsof -ti:3000 > /dev/null 2>&1; then
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        echo -e "   ${GREEN}✓${NC} Frontend stopped (by port 3000)"
    else
        echo -e "   ${YELLOW}→${NC} Frontend was not running"
    fi
fi

# Stop Backend
echo -e "${YELLOW}[2/3]${NC} Stopping backend..."
if [ -f "$PROJECT_DIR/.backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_DIR/.backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "   ${GREEN}✓${NC} Backend stopped (PID: $BACKEND_PID)"
    else
        echo -e "   ${YELLOW}→${NC} Backend was not running"
    fi
    rm "$PROJECT_DIR/.backend.pid"
else
    # Fallback: kill by port
    if lsof -ti:5001 > /dev/null 2>&1; then
        lsof -ti:5001 | xargs kill -9 2>/dev/null || true
        echo -e "   ${GREEN}✓${NC} Backend stopped (by port 5001)"
    else
        echo -e "   ${YELLOW}→${NC} Backend was not running"
    fi
fi

# Stop Database (optional)
echo -e "${YELLOW}[3/3]${NC} Database status..."
if docker ps --format '{{.Names}}' | grep -q "^pgvector$"; then
    echo -e "   ${BLUE}→${NC} Database (pgvector) is still running"
    echo -e "   ${BLUE}→${NC} To stop: ${GREEN}docker stop pgvector${NC}"
    echo -e "   ${BLUE}→${NC} To remove: ${GREEN}docker rm pgvector${NC}"
else
    echo -e "   ${YELLOW}→${NC} Database is not running"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Services stopped successfully!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}To start again:${NC} ./start.sh"
echo ""
