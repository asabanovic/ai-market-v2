#!/usr/bin/env python3
"""
Daily product scan job for user tracking.
Runs vector searches for all users with tracked products and stores results.

Features:
- Round-robin processing: scans users incrementally (BATCH_SIZE per run)
- Filters by user's preferred_stores
- Detects changes in user preferences and auto-extracts new search terms
- Runs vector searches for each tracked term
- Compares with previous day to find new products and discounts
- Rate limited with delays between users to prevent system overload

Schedule: Daily at 6 AM UTC (0 6 * * *)
Command: python jobs/scan_user_products.py
"""

import os
import sys
import json
import time
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserTrackedProduct, UserProductScan, UserScanResult, JobRun
from sendgrid_utils import plural_bs
from preference_config import PREFERENCE_MATCH_THRESHOLD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 10  # Number of users to process per run (round-robin)
DELAY_BETWEEN_USERS = 2  # Seconds to wait between users
DELAY_BETWEEN_SEARCHES = 0.5  # Seconds to wait between search terms


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

For each item:
1. FIX TYPOS: Correct misspellings (e.g., "toletni" → "toaletni", missing letters)
2. ADD DIACRITICS: Add proper Bosnian diacritics (č, ć, š, ž, đ)
3. EXTRACT core product name suitable for semantic search

Examples:
- "toletni papir" → "toaletni papir" (fix missing 'a')
- "osvjezvac" → "osvježivač" (fix missing 'i', add diacritics)
- "Ariel deterdžent za veš" → "ariel deterdžent"
- "svježe mlijeko" → "mlijeko"
- "coca cola zero" → "coca cola zero"
- "voće i povrće" → split into "voće", "povrće"
- "jeftina hrana" → skip (too generic)
- "cokolada" → "čokolada" (add diacritics)

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


def get_users_to_scan_round_robin():
    """
    Get the next batch of users to scan using round-robin.
    Prioritizes users who haven't been scanned today, ordered by last scan date.

    Includes users who have:
    - preferences with grocery_interests or typical_products
    - OR tracked products from any source (including camera_scan)
    """
    today = date.today()

    # Get user IDs who have active tracked products (from any source including camera_scan)
    users_with_tracked = set(
        row[0] for row in db.session.query(UserTrackedProduct.user_id).filter(
            UserTrackedProduct.is_active == True
        ).distinct().all()
    )

    # Get all users with preferences
    all_users_with_prefs = User.query.filter(
        User.preferences.isnot(None)
    ).all()

    # Filter to users who have actual grocery data OR tracked products
    eligible_users = []
    checked_user_ids = set()

    for user in all_users_with_prefs:
        prefs = user.preferences or {}
        if prefs.get('grocery_interests') or prefs.get('typical_products'):
            # Check if already scanned today
            today_scan = UserProductScan.query.filter_by(
                user_id=user.id,
                scan_date=today,
                status='completed'
            ).first()
            if not today_scan:
                eligible_users.append(user)
                checked_user_ids.add(user.id)

    # Also include users with tracked products who weren't already added
    for user_id in users_with_tracked:
        if user_id not in checked_user_ids:
            user = User.query.get(user_id)
            if user:
                today_scan = UserProductScan.query.filter_by(
                    user_id=user.id,
                    scan_date=today,
                    status='completed'
                ).first()
                if not today_scan:
                    eligible_users.append(user)

    # Sort by last scan date (oldest first for fair round-robin)
    def get_last_scan_date(user):
        last_scan = UserProductScan.query.filter_by(
            user_id=user.id
        ).order_by(UserProductScan.scan_date.desc()).first()
        return last_scan.scan_date if last_scan else date(2000, 1, 1)

    eligible_users.sort(key=get_last_scan_date)

    # Return up to BATCH_SIZE users
    return eligible_users[:BATCH_SIZE]


def scan_single_user(user):
    """
    Run product scan for a single user.
    Returns (total_found, new_count, discount_count) or None on error.
    """
    from semantic_search import semantic_search_with_context

    today = date.today()
    yesterday = today - timedelta(days=1)

    try:
        # Calculate current preferences hash
        current_hash = UserTrackedProduct.get_preferences_hash(user)

        # Get last scan to check if preferences changed
        last_scan = UserProductScan.query.filter_by(
            user_id=user.id
        ).order_by(UserProductScan.scan_date.desc()).first()

        # Get tracked products
        tracked_products = UserTrackedProduct.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()

        # Check if we need to extract new terms
        needs_extraction = (
            len(tracked_products) == 0 or
            (last_scan and last_scan.preferences_hash != current_hash)
        )

        if needs_extraction:
            logger.info(f"Extracting tracked products for user {user.id}")
            extracted = extract_tracked_products_for_user(user)
            if extracted:
                sync_tracked_products(user, extracted)
                # Refresh tracked products
                tracked_products = UserTrackedProduct.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()

        if not tracked_products:
            logger.debug(f"Skipping user {user.id} - no tracked products")
            return None

        # Get user's preferred stores (filter by these)
        prefs = user.preferences or {}
        business_ids = prefs.get('preferred_stores', None)
        if business_ids and len(business_ids) == 0:
            business_ids = None  # Empty list means no filter

        # Create or update scan record
        existing_scan = UserProductScan.query.filter_by(
            user_id=user.id,
            scan_date=today
        ).first()

        if existing_scan:
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
        scan.preferences_hash = current_hash
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

        # Run searches with delays
        user_total = 0
        new_count = 0
        discount_count = 0

        # Minimum combined score from centralized config
        # See preference_config.py for details on score components
        MIN_COMBINED_SCORE = PREFERENCE_MATCH_THRESHOLD

        for tracked in tracked_products:
            try:
                # Run semantic search with user context (favorites-based boosting)
                # Products similar to user's favorites get higher scores
                # Limit to 10 results per tracked term (free tier)
                results = semantic_search_with_context(
                    query=tracked.search_term,
                    user_id=user.id,
                    k=10,  # Max 10 products per tracked term
                    min_similarity=0.25,  # Low raw threshold, combined score filters
                    business_ids=business_ids,  # Filter by user's stores
                    context_weight=0.2  # Context bonus weight (0.2 = up to +20% for favorites match)
                )

                for product_data in results:
                    # Filter by combined score (includes text bonus + context bonus)
                    combined_score = product_data.get('similarity_score', 0)
                    if combined_score < MIN_COMBINED_SCORE:
                        continue  # Skip low-relevance products
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
                        similarity_score=product_data.get('similarity_score'),
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

                # Rate limit between search terms
                time.sleep(DELAY_BETWEEN_SEARCHES)

            except Exception as search_err:
                logger.error(f"Error searching for '{tracked.search_term}': {search_err}")
                db.session.rollback()
                continue

        # Update scan summary
        scan.status = 'completed'
        scan.total_products_found = user_total
        scan.new_products_count = new_count
        scan.new_discounts_count = discount_count

        summary_parts = []
        if new_count > 0:
            product_text = plural_bs(new_count, "novi proizvod", "nova proizvoda", "novih proizvoda")
            summary_parts.append(f"{new_count} {product_text}")
        if discount_count > 0:
            discount_text = plural_bs(discount_count, "novi popust", "nova popusta", "novih popusta")
            summary_parts.append(f"{discount_count} {discount_text}")
        if not summary_parts:
            summary_parts.append("Bez promjena od jučer")
        scan.summary_text = ", ".join(summary_parts)

        db.session.commit()
        logger.info(f"Completed scan for user {user.id}: {user_total} products, {new_count} new")

        return (user_total, new_count, discount_count)

    except Exception as e:
        logger.error(f"Error processing user {user.id}: {e}")
        db.session.rollback()
        return None


def run_daily_scan():
    """
    Run daily product scan for ALL users.
    Processes users in batches of BATCH_SIZE until everyone is scanned.
    """
    with app.app_context():
        # Start tracking this job run
        job_run = JobRun.start('product_scan')

        try:
            total_users_processed = 0
            total_products_found = 0
            failed_count = 0
            batch_number = 0

            # Keep looping until all users are scanned
            while True:
                batch_number += 1
                users_to_scan = get_users_to_scan_round_robin()

                if not users_to_scan:
                    logger.info(f"All users scanned after {batch_number - 1} batches")
                    break

                logger.info(f"Processing batch {batch_number}: {len(users_to_scan)} users")

                for user in users_to_scan:
                    try:
                        result = scan_single_user(user)

                        if result:
                            user_total, new_count, discount_count = result
                            total_users_processed += 1
                            total_products_found += user_total
                    except Exception as e:
                        logger.error(f"Error scanning user {user.id}: {e}")
                        failed_count += 1

                    # Rate limit between users
                    time.sleep(DELAY_BETWEEN_USERS)

                logger.info(f"Batch {batch_number} complete. Total so far: {total_users_processed} users, {total_products_found} products")

                # Small delay between batches
                time.sleep(5)

            logger.info(f"Daily scan complete: {total_users_processed} users processed, {total_products_found} total products, {failed_count} failed")

            # Complete job tracking
            job_run.complete(
                records_processed=total_users_processed + failed_count,
                records_success=total_users_processed,
                records_failed=failed_count
            )

        except Exception as e:
            logger.error(f"Fatal error in daily scan: {e}")
            import traceback
            traceback.print_exc()
            job_run.fail(str(e))


if __name__ == '__main__':
    logger.info("Starting daily user product scan job (round-robin)")
    run_daily_scan()
    logger.info("Daily scan job finished")
