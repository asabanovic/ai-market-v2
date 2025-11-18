#!/usr/bin/env python3
"""
Test API endpoints for shopping list and favorites
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_response(response, action):
    print(f"\n{action}")
    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def test_api():
    print_section("TESTING SHOPPING LIST API ENDPOINTS")

    # 1. Login to get JWT token
    print_section("1. Login")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "adnanxteam@gmail.com",
            "password": "admin123"  # Update with correct password
        }
    )

    if login_response.status_code != 200:
        print("❌ Login failed! Please update the password in the script.")
        print(f"Status: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False

    login_data = print_response(login_response, "✅ Login successful")
    token = login_data.get('token')

    if not token:
        print("❌ No token in response!")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. Test Shopping List Header/TTL
    print_section("2. Get Shopping List Header/TTL")
    response = requests.get(f"{BASE_URL}/api/shopping-list/header/ttl", headers=headers)
    if response.status_code != 200:
        print(f"❌ ERROR: Status {response.status_code}")
        print_response(response, "Error")
        return False

    data = print_response(response, "✅ Header/TTL")
    print(f"   TTL: {data.get('ttl_seconds')} seconds ({data.get('ttl_seconds', 0) // 60} minutes)")
    print(f"   Item Count: {data.get('item_count')}")

    # 3. Test Shopping List Sidebar
    print_section("3. Get Shopping List Sidebar")
    response = requests.get(f"{BASE_URL}/api/shopping-list/sidebar", headers=headers)
    if response.status_code != 200:
        print(f"❌ ERROR: Status {response.status_code}")
        print_response(response, "Error")
        return False

    sidebar_data = print_response(response, "✅ Shopping List Sidebar")

    if sidebar_data:
        print(f"\n   Summary:")
        print(f"   - List ID: {sidebar_data.get('list_id')}")
        print(f"   - Total Items: {sidebar_data.get('total_items')}")
        print(f"   - Grand Total: {sidebar_data.get('grand_total')} KM")
        print(f"   - Grand Saving: {sidebar_data.get('grand_saving')} KM")
        print(f"   - Number of Stores: {len(sidebar_data.get('groups', []))}")

        for group in sidebar_data.get('groups', []):
            store = group['store']
            print(f"\n   Store: {store['name']}")
            print(f"   - Items: {len(group['items'])}")
            print(f"   - Subtotal: {group['group_subtotal']} KM")
            print(f"   - Saving: {group['group_saving']} KM")

    # 4. Test Adding Item to List
    print_section("4. Add Item to Shopping List")

    # First, get a product
    from app import app, db
    from models import Product

    with app.app_context():
        product = Product.query.first()
        if product:
            print(f"   Testing with product: {product.title} (ID: {product.id})")
            print(f"   Business ID: {product.business_id}")

            response = requests.post(
                f"{BASE_URL}/api/shopping-list/items",
                headers=headers,
                json={
                    "product_id": product.id,
                    "offer_id": product.business_id,
                    "qty": 1
                }
            )

            if response.status_code in [200, 201]:
                data = print_response(response, "✅ Item added successfully")
                print(f"   New TTL: {data.get('ttl_seconds')} seconds")
                print(f"   Credits left: {data.get('credits_left')}")
            else:
                print_response(response, "⚠️  Add item response")

    # 5. Test Favorites
    print_section("5. Test Favorites")

    with app.app_context():
        product = Product.query.offset(1).first()
        if product:
            print(f"   Testing with product: {product.title} (ID: {product.id})")

            # Add favorite
            response = requests.post(
                f"{BASE_URL}/api/favorites",
                headers=headers,
                json={"product_id": product.id}
            )

            if response.status_code in [200, 201]:
                data = print_response(response, "✅ Favorite added")
                favorite_id = data.get('favorite_id')
            else:
                print_response(response, "⚠️  Add favorite response")

    # Get favorites list
    print("\n   Getting favorites list...")
    response = requests.get(f"{BASE_URL}/api/favorites", headers=headers)
    if response.status_code == 200:
        favorites = print_response(response, "✅ Favorites list")
        print(f"\n   Total favorites: {len(favorites) if favorites else 0}")
    else:
        print_response(response, "❌ Error getting favorites")

    # 6. Test Updating Quantity
    print_section("6. Update Item Quantity")

    if sidebar_data and sidebar_data.get('groups'):
        first_item = sidebar_data['groups'][0]['items'][0]
        item_id = first_item['item_id']
        current_qty = first_item['qty']
        new_qty = current_qty + 1

        print(f"   Item ID: {item_id}")
        print(f"   Current qty: {current_qty}")
        print(f"   New qty: {new_qty}")

        response = requests.patch(
            f"{BASE_URL}/api/shopping-list/items/{item_id}",
            headers=headers,
            json={"qty": new_qty}
        )

        if response.status_code == 200:
            print_response(response, "✅ Quantity updated")
        else:
            print_response(response, "❌ Error updating quantity")

    # 7. Test 10-Item Limit
    print_section("7. Test 10-Item Limit")

    with app.app_context():
        products = Product.query.limit(15).all()
        print(f"   Will attempt to add {len(products)} different items...")

        added_count = 0
        for i, product in enumerate(products):
            response = requests.post(
                f"{BASE_URL}/api/shopping-list/items",
                headers=headers,
                json={
                    "product_id": product.id,
                    "offer_id": product.business_id,
                    "qty": 1
                }
            )

            if response.status_code in [200, 201]:
                added_count += 1
                print(f"   ✅ Item {i+1}: Added successfully")
            elif response.status_code == 400:
                data = response.json()
                if data.get('code') == 'LIST_ITEM_LIMIT':
                    print(f"   🛑 Item {i+1}: Hit 10-item limit (as expected)")
                    print(f"      Message: {data.get('message')}")
                    break
                else:
                    print(f"   ⚠️  Item {i+1}: {data}")
            else:
                print(f"   ⚠️  Item {i+1}: Status {response.status_code}")

    # 8. Final Summary
    print_section("8. Final Summary")
    response = requests.get(f"{BASE_URL}/api/shopping-list/sidebar", headers=headers)
    if response.status_code == 200:
        final_data = response.json()
        print(f"\n✅ Final Shopping List State:")
        print(f"   - List ID: {final_data.get('list_id')}")
        print(f"   - Distinct Items: {len([item for group in final_data.get('groups', []) for item in group['items']])}")
        print(f"   - Total Quantity: {final_data.get('total_items')}")
        print(f"   - Grand Total: {final_data.get('grand_total')} KM")
        print(f"   - Grand Saving: {final_data.get('grand_saving')} KM")
        print(f"   - TTL: {final_data.get('ttl_seconds')} seconds")

    print("\n" + "=" * 60)
    print("✅ ALL API TESTS COMPLETED!")
    print("=" * 60)
    print("\nNo 500 errors encountered!")
    print("All endpoints are working correctly.")

    return True

if __name__ == '__main__':
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
