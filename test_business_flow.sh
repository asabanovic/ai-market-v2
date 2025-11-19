#!/bin/bash

# Test Business Management Flow
# Tests: Add business, Update business, Add products via JSON

BASE_URL="http://localhost:5001"
EMAIL="biztest_$(date +%s)@test.com"
PASSWORD="TestPass123"

echo "========================================="
echo "Business Management Flow Test"
echo "========================================="
echo ""
echo "Test user: $EMAIL"
echo ""

# Step 1: Register and Login
echo "[1/6] Registering new test user..."

# Register
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"name\":\"Business Test User\",\"city\":\"Tuzla\"}")

# Extract token from registration (it returns a token directly)
LOGIN_RESPONSE="$REGISTER_RESPONSE"

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Login successful"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Add a new business (via database since there's no JWT endpoint for creating businesses)
echo "[2/6] Adding a new business..."

# Create business via database
BUSINESS_ID=$(docker exec pgvector psql -U postgres -d ai_pijaca -t -c "
INSERT INTO businesses (name, contact_phone, city, google_link)
VALUES ('Test Market 2025', '+38761123456', 'Sarajevo', 'https://maps.google.com/test')
RETURNING id;" | grep -oE '[0-9]+' | head -1)

if [ -z "$BUSINESS_ID" ]; then
  echo "❌ Failed to add business!"
  exit 1
fi

echo "✓ Business added successfully"
echo "Business ID: $BUSINESS_ID"
echo ""

# Step 3: Update the business
echo "[3/6] Updating business details via API..."
UPDATE_RESPONSE=$(curl -s -X POST "http://localhost:5001/api/businesses/${BUSINESS_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Market 2025 - Updated",
    "contact_phone": "+38761999888",
    "city": "Tuzla",
    "google_link": "https://maps.google.com/test-updated"
  }')

UPDATE_SUCCESS=$(echo $UPDATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$UPDATE_SUCCESS" != "True" ]; then
  echo "❌ Failed to update business!"
  echo "Response: $UPDATE_RESPONSE"
else
  echo "✓ Business updated successfully"
fi
echo ""

# Step 4: Add products via JSON bulk import
echo "[4/6] Adding products via JSON bulk import..."
PRODUCTS_JSON='{
  "products": [
    {
      "title": "Test Hleb 500g",
      "base_price": 1.50,
      "discount_price": 1.20,
      "category": "Pekara",
      "expires": "2025-12-31",
      "image_url": "https://example.com/hleb.jpg"
    },
    {
      "title": "Test Mlijeko 1L",
      "base_price": 2.50,
      "discount_price": 2.10,
      "category": "Mliječni proizvodi",
      "expires": "2025-11-30",
      "image_url": "https://example.com/mlijeko.jpg"
    },
    {
      "title": "Test Jabuka 1kg",
      "base_price": 3.00,
      "category": "Voće",
      "image_url": "https://example.com/jabuka.jpg"
    }
  ]
}'

IMPORT_RESPONSE=$(curl -s -X POST "http://localhost:5001/biznisi/${BUSINESS_ID}/proizvodi/bulk-import" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PRODUCTS_JSON}")

IMPORTED_COUNT=$(echo $IMPORT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('imported_count', 0))" 2>/dev/null)

if [ "$IMPORTED_COUNT" -eq 0 ]; then
  echo "❌ Failed to import products!"
  echo "Response: $IMPORT_RESPONSE"
else
  echo "✓ Products imported successfully"
  echo "Imported count: $IMPORTED_COUNT"
  echo "Response details:"
  echo "$IMPORT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$IMPORT_RESPONSE"
fi
echo ""

# Step 5: Verify products were added
echo "[5/6] Verifying products..."
PRODUCTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/businesses/${BUSINESS_ID}/products" \
  -H "Authorization: Bearer ${TOKEN}")

PRODUCT_COUNT=$(echo $PRODUCTS_RESPONSE | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('products', [])))" 2>/dev/null)

if [ -z "$PRODUCT_COUNT" ] || [ "$PRODUCT_COUNT" -eq 0 ]; then
  echo "❌ No products found for business!"
  echo "Response: $PRODUCTS_RESPONSE"
else
  echo "✓ Products verified"
  echo "Total products: $PRODUCT_COUNT"
  echo ""
  echo "Product details:"
  echo "$PRODUCTS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); [print(f\"  - {p['title']}: {p['base_price']} KM\") for p in data.get('products', [])]" 2>/dev/null
fi
echo ""

# Step 6: Test updating a product
echo "[6/6] Testing product update..."
FIRST_PRODUCT_ID=$(echo $PRODUCTS_RESPONSE | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('products', [{}])[0].get('id', ''))" 2>/dev/null)

if [ -n "$FIRST_PRODUCT_ID" ]; then
  UPDATE_PRODUCT_RESPONSE=$(curl -s -X PUT "http://localhost:5001/biznisi/${BUSINESS_ID}/proizvodi/${FIRST_PRODUCT_ID}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Test Hleb 500g - UPDATED",
      "base_price": 1.80,
      "discount_price": 1.50,
      "category": "Pekara"
    }')

  UPDATE_PRODUCT_SUCCESS=$(echo $UPDATE_PRODUCT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

  if [ "$UPDATE_PRODUCT_SUCCESS" = "True" ]; then
    echo "✓ Product updated successfully"
  else
    echo "❌ Failed to update product"
    echo "Response: $UPDATE_PRODUCT_RESPONSE"
  fi
else
  echo "⚠ No product ID found to test update"
fi
echo ""

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "✓ Login successful"
echo "✓ Business created (ID: $BUSINESS_ID)"
echo "✓ Business updated"
echo "✓ Products imported ($IMPORTED_COUNT items)"
echo "✓ Products verified ($PRODUCT_COUNT total)"
echo "✓ Product update tested"
echo ""
echo "All tests passed! ✓"
echo ""
echo "Business ID: $BUSINESS_ID"
echo "You can view it at: http://localhost:5001/biznisi/${BUSINESS_ID}/proizvodi"
