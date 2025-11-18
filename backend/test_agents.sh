#!/bin/bash

echo "===== TESTING AI AGENTS ====="

# Get authentication token
echo "1. Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"adnanxteam@gmail.com","password":"demo123"}')

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✓ Token obtained"

# Test 1: List agents
echo ""
echo "2. Listing available agents..."
curl -s http://localhost:5001/api/agents/list | python3 -m json.tool
echo ""

# Test 2: Semantic search
echo "3. Testing semantic search agent..."
SEARCH_RESULT=$(curl -s -X POST http://localhost:5001/api/agents/semantic_search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"piletina", "k": 3, "enable_explanation": false}')

echo "$SEARCH_RESULT" | python3 -m json.tool
echo ""

# Test 3: Semantic search with price filter
echo "4. Testing semantic search with price filter..."
curl -s -X POST http://localhost:5001/api/agents/semantic_search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"meso ispod 10 KM", "k": 5, "enable_explanation": false}' | python3 -m json.tool
echo ""

# Test 4: Meal planner
echo "5. Testing meal planner agent..."
curl -s -X POST http://localhost:5001/api/agents/meal_planner \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"meal_type":"ručak", "preferences":["brzo"], "max_budget":20.0}' | python3 -m json.tool
echo ""

echo "===== ALL AGENT TESTS COMPLETE ====="
