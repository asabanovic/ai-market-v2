#!/bin/bash

# Get token
TOKEN=$(cat /tmp/tok.txt)

echo "===== TESTING ALL ENDPOINTS WITH CORS ====="
echo ""

echo "1. Favorites:"
curl -s "http://localhost:5001/api/favorites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool | head -30

echo ""
echo "2. Shopping List Header/TTL:"
curl -s "http://localhost:5001/api/shopping-list/header/ttl" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool

echo ""
echo "3. Shopping List Sidebar:"
curl -s "http://localhost:5001/api/shopping-list/sidebar" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool | head -60

echo ""
echo "4. Auth Verify:"
curl -s "http://localhost:5001/auth/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool

echo ""
echo "5. Products (No auth required):"
curl -s "http://localhost:5001/api/products?page=1&per_page=3" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool | head -35

echo ""
echo "6. Businesses (No auth required):"
curl -s "http://localhost:5001/api/businesses" \
  -H "Origin: http://localhost:3000" | python3 -m json.tool

echo ""
echo "===== ALL TESTS COMPLETE ====="
