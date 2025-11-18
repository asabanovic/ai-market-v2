#!/usr/bin/env python3
"""
Test script to create a shopping list for admin user
"""
import sys
from datetime import datetime, timedelta
from app import app, db
from models import User, Product, Business, ShoppingList, ShoppingListItem
from credits_service import CreditsService

def test_shopping_list():
    with app.app_context():
        print("=" * 60)
        print("TESTING SHOPPING LIST FEATURE")
        print("=" * 60)

        # 1. Get admin user
        print("\n1. Getting admin user...")
        user = User.query.filter_by(email='adnanxteam@gmail.com').first()

        if not user:
            print("❌ ERROR: Admin user not found!")
            return False

        print(f"✅ Found user: {user.email} (ID: {user.id})")

        # 2. Initialize credits
        print("\n2. Initializing user credits...")
        try:
            current_balance = CreditsService.get_balance(user.id)
            print(f"   Current balance: {current_balance} credits")

            if current_balance < 20:
                # Add credits if needed
                result = CreditsService.add_credits(
                    user_id=user.id,
                    amount=50,
                    action='TEST_TOP_UP',
                    metadata={'test': True}
                )
                print(f"✅ Added 50 credits. New balance: {result['balance']}")
            else:
                print(f"✅ User has sufficient credits: {current_balance}")
        except Exception as e:
            print(f"❌ ERROR initializing credits: {e}")
            return False

        # 3. Get some products
        print("\n3. Finding products...")
        products = Product.query.join(Business).limit(5).all()

        if len(products) < 3:
            print(f"❌ ERROR: Not enough products in database (found {len(products)})")
            return False

        print(f"✅ Found {len(products)} products:")
        for p in products:
            price = p.discount_price if p.has_discount else p.base_price
            print(f"   - {p.title[:50]} | {price:.2f} KM | Business: {p.business.name}")

        # 4. Create shopping list
        print("\n4. Creating shopping list...")
        try:
            # Check if user has active list
            existing_list = ShoppingList.query.filter_by(
                user_id=user.id,
                status='ACTIVE'
            ).filter(
                ShoppingList.expires_at > datetime.now()
            ).first()

            if existing_list:
                print(f"   User already has active list (ID: {existing_list.id})")
                shopping_list = existing_list
            else:
                shopping_list = ShoppingList(
                    user_id=user.id,
                    status='ACTIVE',
                    expires_at=datetime.now() + timedelta(hours=24)
                )
                db.session.add(shopping_list)
                db.session.commit()
                print(f"✅ Created new shopping list (ID: {shopping_list.id})")
                print(f"   Expires at: {shopping_list.expires_at}")
                print(f"   TTL: {shopping_list.ttl_seconds} seconds")
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR creating shopping list: {e}")
            return False

        # 5. Add items to list
        print("\n5. Adding items to shopping list...")
        items_added = 0

        for i, product in enumerate(products[:3]):  # Add 3 items
            try:
                # Check if item already exists
                existing_item = ShoppingListItem.query.filter_by(
                    list_id=shopping_list.id,
                    product_id=product.id,
                    business_id=product.business_id
                ).first()

                if existing_item:
                    print(f"   Item {i+1}: Already exists, incrementing qty")
                    existing_item.qty += 1
                    existing_item.updated_at = datetime.now()
                else:
                    # Deduct credit for new item
                    try:
                        CreditsService.deduct_credits(
                            user_id=user.id,
                            amount=1,
                            action='TEST_ADD_TO_CART',
                            metadata={'product_id': product.id, 'list_id': shopping_list.id}
                        )
                    except Exception as credit_error:
                        print(f"   ⚠️  Credit deduction failed: {credit_error}")
                        continue

                    # Snapshot prices
                    price = product.discount_price if product.has_discount else product.base_price
                    old_price = product.base_price if product.has_discount else None
                    discount_pct = product.discount_percentage if product.has_discount else None

                    new_item = ShoppingListItem(
                        list_id=shopping_list.id,
                        product_id=product.id,
                        business_id=product.business_id,
                        qty=i + 1,  # Different quantities
                        price_snapshot=price,
                        old_price_snapshot=old_price,
                        discount_percent_snapshot=discount_pct
                    )

                    db.session.add(new_item)
                    items_added += 1
                    print(f"   ✅ Item {i+1}: {product.title[:40]} | Qty: {i+1} | {price:.2f} KM")

                db.session.commit()

            except Exception as e:
                db.session.rollback()
                print(f"   ❌ ERROR adding item {i+1}: {e}")
                continue

        if items_added == 0:
            print("   ℹ️  No new items added (all existed)")
        else:
            print(f"\n✅ Added {items_added} new items to shopping list")

        # 6. Verify list
        print("\n6. Verifying shopping list...")
        try:
            items = ShoppingListItem.query.filter_by(list_id=shopping_list.id).all()
            total_items = sum(item.qty for item in items)
            total_price = sum(item.subtotal for item in items)
            total_saving = sum(item.estimated_saving for item in items)

            print(f"   List ID: {shopping_list.id}")
            print(f"   Status: {shopping_list.status}")
            print(f"   Distinct items: {len(items)}")
            print(f"   Total quantity: {total_items}")
            print(f"   Total price: {total_price:.2f} KM")
            print(f"   Total saving: {total_saving:.2f} KM")
            print(f"   TTL: {shopping_list.ttl_seconds // 60} minutes")

            print("\n   Items breakdown:")
            for item in items:
                product = item.product
                print(f"   - {product.title[:40]}")
                print(f"     Qty: {item.qty} x {item.price_snapshot:.2f} KM = {item.subtotal:.2f} KM")
                if item.estimated_saving > 0:
                    print(f"     Saving: {item.estimated_saving:.2f} KM")
        except Exception as e:
            print(f"❌ ERROR verifying list: {e}")
            return False

        # 7. Check final credits
        print("\n7. Final credit balance...")
        try:
            final_balance = CreditsService.get_balance(user.id)
            print(f"✅ Final balance: {final_balance} credits")
        except Exception as e:
            print(f"❌ ERROR checking balance: {e}")
            return False

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print(f"\nShopping list created successfully!")
        print(f"List ID: {shopping_list.id}")
        print(f"User: {user.email}")
        print(f"Items: {len(items)} distinct, {total_items} total")
        print(f"Total: {total_price:.2f} KM (saving: {total_saving:.2f} KM)")
        print("\nYou can now test the API endpoints!")

        return True

if __name__ == '__main__':
    success = test_shopping_list()
    sys.exit(0 if success else 1)
