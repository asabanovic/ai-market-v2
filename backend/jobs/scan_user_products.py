#!/usr/bin/env python3
"""
Daily product scan job for user tracking.
Runs vector searches for all users with tracked products and stores results.

Features:
- Detects changes in user preferences and auto-extracts new search terms
- Runs vector searches for each tracked term
- Compares with previous day to find new products and discounts

Schedule: Daily at 6 AM UTC (0 6 * * *)
Command: python jobs/scan_user_products.py
"""

import os
import sys
import json
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserTrackedProduct, UserProductScan, UserScanResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_tracked_products_for_user(user):
    """
    Use AI to extract product search terms from user preferences.
    Called when preferences change or user has no tracked products yet.
    """
    from openai_utils import openai_client

    prefs = user.preferences or {}
    grocery_interests = prefs.get('grocery_interests', [])
    typical_products = prefs.get('typical_products', [])

    if not grocery_interests and not typical_products:
        return []

    # Build prompt for AI
    all_items = []
    for item in grocery_interests:
        all_items.append(f"- {item} (from grocery_interests)")
    for item in typical_products:
        all_items.append(f"- {item} (from typical_products)")

    items_text = "\n".join(all_items)

    system_prompt = """You extract normalized product search terms from user preferences.

For each item, extract the core product name suitable for semantic search.
Examples:
- "Ariel deterdžent za veš" → "ariel deterdžent"
- "svježe mlijeko" → "mlijeko"
- "coca cola zero" → "coca cola zero"
- "voće i povrće" → split into "voće", "povrće"
- "jeftina hrana" → skip (too generic)

Return JSON array of objects with: search_term, original_text, source
Only include specific, searchable product terms. Skip generic terms like "hrana", "namirnice", "jeftino"."""

    user_prompt = f"""Extract product search terms from these user preferences:

{items_text}

Return JSON like: {{"items": [{{"search_term": "mlijeko", "original_text": "svježe mlijeko", "source": "grocery_interests"}}]}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        if isinstance(result, dict):
            extracted = result.get('items', result.get('products', result.get('terms', [])))
        else:
            extracted = result

        return extracted

    except Exception as e:
        logger.error(f"Error extracting tracked products: {e}")
        return []


def sync_tracked_products(user, extracted_items):
    """
    Sync extracted items with database - add new ones, keep existing.
    Returns count of new items added.
    """
    added = 0
    for item in extracted_items:
        search_term = item.get('search_term', '').strip().lower()
        if not search_term or len(search_term) < 2:
            continue

        existing = UserTrackedProduct.query.filter_by(
            user_id=user.id,
            search_term=search_term
        ).first()

        if not existing:
            tracked = UserTrackedProduct(
                user_id=user.id,
                search_term=search_term,
                original_text=item.get('original_text'),
                source=item.get('source', 'auto_extracted'),
                is_active=True
            )
            db.session.add(tracked)
            added += 1

    if added > 0:
        db.session.commit()
        logger.info(f"Added {added} new tracked products for user {user.id}")

    return added


def run_daily_scan():
    """Run daily product scan for all users with preferences or tracked products"""
    with app.app_context():
        try:
            from agents.common.db_utils import search_by_vector
            from agents.common.embeddings import get_embedding

            today = date.today()
            yesterday = today - timedelta(days=1)

            # Get all users with preferences (grocery_interests or typical_products)
            # This is broader than just users with tracked products - we want to auto-extract
            all_users_with_prefs = User.query.filter(
                User.preferences.isnot(None)
            ).all()

            # Filter to users who have actual grocery data
            users_to_scan = []
            for user in all_users_with_prefs:
                prefs = user.preferences or {}
                if prefs.get('grocery_interests') or prefs.get('typical_products'):
                    users_to_scan.append(user)

            logger.info(f"Found {len(users_to_scan)} users with preferences to scan")

            total_users_processed = 0
            total_products_found = 0
            total_extractions = 0

            for user in users_to_scan:
                try:
                    # Calculate current preferences hash
                    current_hash = UserTrackedProduct.get_preferences_hash(user)

                    # Get last scan to check if preferences changed
                    last_scan = UserProductScan.query.filter_by(
                        user_id=user.id
                    ).order_by(UserProductScan.scan_date.desc()).first()

                    # Check if we need to extract new terms:
                    # 1. User has no tracked products yet
                    # 2. Preferences changed since last scan
                    tracked_products = UserTrackedProduct.query.filter_by(
                        user_id=user.id,
                        is_active=True
                    ).all()

                    needs_extraction = (
                        len(tracked_products) == 0 or
                        (last_scan and last_scan.preferences_hash != current_hash)
                    )

                    if needs_extraction:
                        logger.info(f"Extracting tracked products for user {user.id} (preferences changed or new user)")
                        extracted = extract_tracked_products_for_user(user)
                        if extracted:
                            sync_tracked_products(user, extracted)
                            total_extractions += 1
                            # Refresh tracked products
                            tracked_products = UserTrackedProduct.query.filter_by(
                                user_id=user.id,
                                is_active=True
                            ).all()

                    if not tracked_products:
                        logger.debug(f"Skipping user {user.id} - no tracked products after extraction")
                        continue

                    # Check if scan already exists for today
                    existing_scan = UserProductScan.query.filter_by(
                        user_id=user.id,
                        scan_date=today
                    ).first()

                    if existing_scan:
                        # Skip if already completed today with same preferences
                        if existing_scan.status == 'completed' and existing_scan.preferences_hash == current_hash:
                            logger.info(f"Skipping user {user.id} - already scanned today with same preferences")
                            continue
                        # Delete incomplete results or re-scan due to preference change
                        UserScanResult.query.filter_by(scan_id=existing_scan.id).delete()
                        scan = existing_scan
                    else:
                        scan = UserProductScan(
                            user_id=user.id,
                            scan_date=today,
                            status='running'
                        )
                        db.session.add(scan)

                    scan.status = 'running'
                    scan.preferences_hash = current_hash  # Save current preferences hash
                    db.session.commit()

                    # Get yesterday's results for comparison
                    yesterday_scan = UserProductScan.query.filter_by(
                        user_id=user.id,
                        scan_date=yesterday
                    ).first()

                    yesterday_products = set()
                    yesterday_prices = {}
                    if yesterday_scan:
                        yesterday_results = UserScanResult.query.filter_by(
                            scan_id=yesterday_scan.id
                        ).all()
                        for r in yesterday_results:
                            if r.product_id:
                                yesterday_products.add(r.product_id)
                                yesterday_prices[r.product_id] = {
                                    'base': r.base_price,
                                    'discount': r.discount_price
                                }

                    # Run searches
                    user_total = 0
                    new_count = 0
                    discount_count = 0

                    for tracked in tracked_products:
                        try:
                            embedding = get_embedding(tracked.search_term)
                            results = search_by_vector(
                                query_embedding=embedding,
                                k=50,
                                similarity_threshold=0.3,
                                max_per_store=10
                            )

                            for product_data in results:
                                product_id = product_data.get('id')
                                is_new = product_id not in yesterday_products

                                price_dropped = False
                                was_discounted = False
                                if product_id in yesterday_prices:
                                    yp = yesterday_prices[product_id]
                                    current_price = product_data.get('discount_price') or product_data.get('base_price')
                                    old_price = yp.get('discount') or yp.get('base')
                                    if current_price and old_price and current_price < old_price:
                                        price_dropped = True
                                    if not yp.get('discount') and product_data.get('discount_price'):
                                        discount_count += 1

                                result = UserScanResult(
                                    scan_id=scan.id,
                                    tracked_product_id=tracked.id,
                                    product_id=product_id,
                                    product_title=product_data.get('title'),
                                    business_name=product_data.get('business', {}).get('name'),
                                    similarity_score=product_data.get('similarity'),
                                    base_price=product_data.get('base_price'),
                                    discount_price=product_data.get('discount_price'),
                                    is_new_today=is_new,
                                    was_discounted_yesterday=was_discounted,
                                    price_dropped_today=price_dropped
                                )
                                db.session.add(result)
                                user_total += 1
                                if is_new:
                                    new_count += 1

                        except Exception as search_err:
                            logger.error(f"Error searching for '{tracked.search_term}': {search_err}")
                            continue

                    # Update scan summary
                    scan.status = 'completed'
                    scan.total_products_found = user_total
                    scan.new_products_count = new_count
                    scan.new_discounts_count = discount_count

                    summary_parts = []
                    if new_count > 0:
                        summary_parts.append(f"{new_count} novih proizvoda")
                    if discount_count > 0:
                        summary_parts.append(f"{discount_count} novih popusta")
                    if not summary_parts:
                        summary_parts.append("Bez promjena od jučer")
                    scan.summary_text = ", ".join(summary_parts)

                    db.session.commit()
                    total_users_processed += 1
                    total_products_found += user_total

                    logger.info(f"Completed scan for user {user.id}: {user_total} products, {new_count} new")

                except Exception as user_err:
                    logger.error(f"Error processing user {user.id}: {user_err}")
                    db.session.rollback()
                    continue

            logger.info(f"Daily scan complete: {total_users_processed} users, {total_products_found} total products, {total_extractions} new extractions")

        except Exception as e:
            logger.error(f"Fatal error in daily scan: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    logger.info("Starting daily user product scan job")
    run_daily_scan()
    logger.info("Daily scan job finished")
