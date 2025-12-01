#!/bin/bash
# Test production build locally before deploying to Railway
# This replicates the EXACT Railway deployment process

set -e

echo "========================================"
echo "  Production Build Test"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Stopping any running containers...${NC}"
docker compose down 2>/dev/null || true

echo -e "${YELLOW}Step 2: Building production containers (this replicates Railway build)...${NC}"
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

echo -e "${YELLOW}Step 3: Starting production containers...${NC}"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo -e "${YELLOW}Step 4: Waiting for services to start...${NC}"
sleep 10

echo -e "${YELLOW}Step 5: Running health checks...${NC}"
echo ""

# Check backend
echo -n "Backend health: "
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health 2>/dev/null || echo "000")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}OK (200)${NC}"
else
    echo -e "${RED}FAILED (HTTP $BACKEND_STATUS)${NC}"
fi

# Check frontend homepage
echo -n "Frontend homepage: "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}OK (200)${NC}"
else
    echo -e "${RED}FAILED (HTTP $FRONTEND_STATUS)${NC}"
fi

# Check frontend static files (the main issue we've been debugging)
echo -n "Frontend static files (_nuxt): "
# Get any _nuxt file from the HTML
NUXT_FILE=$(curl -s http://localhost:3000 2>/dev/null | grep -o '/_nuxt/[^"]*\.js' | head -1)
if [ -n "$NUXT_FILE" ]; then
    STATIC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000${NUXT_FILE}" 2>/dev/null || echo "000")
    if [ "$STATIC_STATUS" = "200" ]; then
        echo -e "${GREEN}OK (200) - $NUXT_FILE${NC}"
    else
        echo -e "${RED}FAILED (HTTP $STATIC_STATUS) - $NUXT_FILE${NC}"
    fi
else
    echo -e "${YELLOW}WARNING: No _nuxt files found in HTML${NC}"
fi

# Check API endpoint
echo -n "API products endpoint: "
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/products 2>/dev/null || echo "000")
if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}OK (200)${NC}"
else
    echo -e "${YELLOW}CHECK ($API_STATUS) - may need auth or be empty${NC}"
fi

echo ""
echo "========================================"
echo "  Container Logs (last 10 lines each)"
echo "========================================"
echo ""
echo -e "${YELLOW}Frontend logs:${NC}"
docker compose logs frontend --tail 10 2>/dev/null || echo "No logs available"
echo ""
echo -e "${YELLOW}Backend logs:${NC}"
docker compose logs backend --tail 10 2>/dev/null || echo "No logs available"

echo ""
echo "========================================"
echo "  Test URLs"
echo "========================================"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:5001"
echo "API:      http://localhost:5001/api/products"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
echo ""

# Summary
echo "========================================"
if [ "$FRONTEND_STATUS" = "200" ] && [ "$STATIC_STATUS" = "200" ] && [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}All critical checks PASSED - safe to deploy!${NC}"
else
    echo -e "${RED}Some checks FAILED - review before deploying!${NC}"
fi
echo "========================================"
