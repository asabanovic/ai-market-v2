#!/bin/bash

echo "Testing /search endpoint..."
echo ""

curl -X POST "http://localhost:5001/search" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"query": "Zelim meso"}' 2>&1 | python3 -m json.tool

echo ""
echo "Done"
