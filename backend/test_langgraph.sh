#!/bin/bash

echo "===== TESTING LANGGRAPH AI AGENTS SYSTEM ====="

# Get authentication token
echo "1. Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"adnanxteam@gmail.com","password":"demo123"}')

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    exit 1
fi

echo "✓ Token obtained"

# Test 1: Agent info endpoint (no auth required)
echo ""
echo "2. Getting agents info..."
curl -s http://localhost:5001/api/agents/info | python3 -m json.tool | head -50
echo ""

# Test 2: Semantic search via unified endpoint
echo "3. Testing unified search - Semantic Search (piletina)..."
curl -s -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"piletina"}' | python3 -m json.tool | head -60
echo ""

# Test 3: Price filter search
echo "4. Testing unified search - Price Filter (meso ispod 10 KM)..."
curl -s -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"meso ispod 10 KM"}' | python3 -m json.tool | head -60
echo ""

# Test 4: Meal planning
echo "5. Testing unified search - Meal Planning (šta da napravim za ručak)..."
curl -s -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"šta da napravim za ručak"}' | python3 -m json.tool | head -80
echo ""

# Test 5: General assistant
echo "6. Testing unified search - General (koje trgovine su dostupne)..."
curl -s -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"koje trgovine su dostupne"}' | python3 -m json.tool | head -40
echo ""

echo "===== ALL LANGGRAPH TESTS COMPLETE ====="
