#!/usr/bin/env python3
"""
Weekly summary email job for users with tracked products.
Sends comprehensive overview of all tracked products, prices, and deals.

Features:
- Total products being tracked with match counts
- Best deals from the week (highest discounts)
- Price drops detected this week
- New products matching tracked terms
- Top 2 prices per tracked term

Schedule: Sundays at 8 AM UTC (9 AM Bosnia time)
Command: python jobs/weekly_summary.py
"""

import os
import sys
import time
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserProductScan, UserScanResult, UserTrackedProduct, JobRun, EmailNotification
from sendgrid_utils import send_weekly_summary_email
from sqlalchemy import func, distinct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
EMAIL_BATCH_SIZE = 10  # Log progress every N emails
DELAY_BETWEEN_EMAILS = 0.5  # Seconds between emails


def get_users_with_tracking() -> list:
    """Get users who have active tracked products and weekly emails enabled."""
    # Get user IDs that have tracked products
    users_with_tracking = db.session.query(
        distinct(UserTrackedProduct.user_id)
    ).filter(
        UserTrackedProduct.is_active == True
    ).all()

    user_ids = [u[0] for u in users_with_tracking]

    if not user_ids:
        return []

    users = User.query.filter(
        User.id.in_(user_ids),
        User.email.isnot(None),
        User.email != ''
    ).all()

    # Filter out users who have weekly emails disabled
    eligible_users = []
    for user in users:
        prefs = user.preferences or {}

        # Check legacy email_notifications setting
        if not prefs.get('email_notifications', True):
            continue

        # Check weekly_summary preference (default: True)
        email_prefs = prefs.get('email_preferences', {})
        if not email_prefs.get('weekly_summary', True):
            continue

        eligible_users.append(user)

    return eligible_users


def get_weekly_summary_for_user(user_id: int) -> dict:
    """
    Get comprehensive weekly summary for a user's tracked products.

    Returns dict with:
    - total_products: Number of tracked terms
    - total_matches: Total products found
    - total_savings: Potential savings (sum of best discount per term)
    - best_deals: Top 3 deals by discount percentage
    - tracked_items: Top 2 products per tracked term
    - price_drops: Products that dropped in price this week
    - new_products: New products discovered this week
    - terms_count: Number of terms with matches
    """
    # Get user's tracked products
    tracked_products = UserTrackedProduct.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()

    if not tracked_products:
        return None

    # Get scans from the past 7 days
    week_ago = datetime.now().date() - timedelta(days=7)

    scans = UserProductScan.query.filter(
        UserProductScan.user_id == user_id,
        UserProductScan.scan_date >= week_ago,
        UserProductScan.status == 'completed'
    ).all()

    if not scans:
        # Try to get the most recent scan
        latest_scan = UserProductScan.query.filter(
            UserProductScan.user_id == user_id,
            UserProductScan.status == 'completed'
        ).order_by(UserProductScan.scan_date.desc()).first()

        if latest_scan:
            scans = [latest_scan]
        else:
            return None

    scan_ids = [s.id for s in scans]

    # Get all results from these scans
    results = UserScanResult.query.filter(
        UserScanResult.scan_id.in_(scan_ids)
    ).all()

    if not results:
        return None

    # Group results by tracked product for deduplication
    # Use the most recent result for each product_id per tracked_product_id
    product_map = {}  # (tracked_product_id, product_id) -> result
    for result in results:
        key = (result.tracked_product_id, result.product_id)
        if key not in product_map or result.created_at > product_map[key].created_at:
            product_map[key] = result

    unique_results = list(product_map.values())

    # Calculate statistics
    best_deals = []
    tracked_items = []
    price_drops = []
    new_products = []
    total_savings = 0
    terms_with_matches = set()

    # Group by tracked term
    term_results = {}
    for result in unique_results:
        tracked = UserTrackedProduct.query.get(result.tracked_product_id)
        if not tracked:
            continue

        term = tracked.search_term
        terms_with_matches.add(term)

        if term not in term_results:
            term_results[term] = []
        term_results[term].append(result)

    # Process each term
    for term, results in term_results.items():
        # Filter out low-relevance results (similarity < 0.5) to avoid irrelevant matches
        relevant_results = [r for r in results if (r.similarity_score or 0) >= 0.5]
        if relevant_results:
            results = relevant_results

        # Sort by effective price (discount_price if available, else base_price)
        def get_effective_price(r):
            return float(r.discount_price or r.base_price or 999999)

        results.sort(key=get_effective_price)

        # Top 2 per term for tracked_items
        for i, result in enumerate(results[:2]):
            effective_price = result.discount_price or result.base_price
            if effective_price:
                tracked_items.append({
                    'product': f"[{term}] {result.product_title[:40]}..." if len(result.product_title or '') > 40 else f"[{term}] {result.product_title or ''}",
                    'store': result.business_name or '',
                    'current_price': float(effective_price),
                    'price_change': 0  # Would need historical data to calculate
                })

        # Best deal per term (for best_deals and savings)
        for result in results:
            if result.discount_price and result.base_price and result.discount_price < result.base_price:
                savings = float(result.base_price - result.discount_price)
                savings_pct = (savings / float(result.base_price)) * 100

                best_deals.append({
                    'product': result.product_title or '',
                    'store': result.business_name or '',
                    'original_price': float(result.base_price),
                    'discount_price': float(result.discount_price),
                    'savings_percent': savings_pct,
                    'savings_amount': savings
                })

                # Add best saving per term to total
                if result == results[0]:  # First (lowest price) with discount
                    total_savings += savings
                break

        # Collect price drops and new products
        for result in results:
            if result.price_dropped_today:
                price_drops.append({
                    'product': result.product_title or '',
                    'store': result.business_name or '',
                    'drop_amount': float(result.base_price - (result.discount_price or result.base_price)) if result.base_price else 0
                })

            if result.is_new_today:
                effective_price = result.discount_price or result.base_price
                new_products.append({
                    'product': result.product_title or '',
                    'store': result.business_name or '',
                    'price': float(effective_price) if effective_price else 0
                })

    # Sort best deals by savings percentage
    best_deals.sort(key=lambda x: x['savings_percent'], reverse=True)

    return {
        'total_products': len(tracked_products),
        'total_matches': len(unique_results),
        'total_savings': total_savings,
        'best_deals': best_deals[:3],
        'tracked_items': tracked_items[:10],
        'price_drops': price_drops[:5],
        'new_products': new_products[:5],
        'terms_count': len(terms_with_matches)
    }


def run_weekly_summaries(force: bool = False):
    """Send weekly summary emails to all users with tracked products.

    Args:
        force: If True, bypass the Sunday check and run immediately.
    """
    with app.app_context():
        # Check if it's Sunday (unless forced)
        now = datetime.utcnow()
        if not force and now.weekday() != 6:  # 6 = Sunday
            logger.info("Skipping weekly summary - not Sunday")
            return

        # Start tracking this job run
        job_run = JobRun.start('weekly_summary')

        try:
            # Get eligible users
            users = get_users_with_tracking()
            logger.info(f"Found {len(users)} users with tracked products for weekly summary")

            if not users:
                job_run.complete(records_processed=0, records_success=0, records_failed=0)
                return

            sent_count = 0
            skipped_count = 0
            failed_count = 0
            processed_count = 0

            for user in users:
                processed_count += 1

                try:
                    # Get weekly summary
                    summary = get_weekly_summary_for_user(user.id)
                    if not summary or summary['total_matches'] == 0:
                        skipped_count += 1
                        continue

                    user_name = user.first_name or user.email.split('@')[0]

                    if send_weekly_summary_email(user.email, user_name, summary):
                        sent_count += 1

                        # Log the email
                        EmailNotification.log_email(
                            email=user.email,
                            email_type='weekly_summary',
                            subject=f"Sedmični pregled: {summary['total_products']} artikala",
                            user_id=user.id,
                            status='sent',
                            extra_data={
                                'total_products': summary['total_products'],
                                'total_matches': summary['total_matches'],
                                'best_deals_count': len(summary['best_deals']),
                                'price_drops_count': len(summary['price_drops'])
                            }
                        )

                        # Rate limit
                        time.sleep(DELAY_BETWEEN_EMAILS)
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error sending weekly summary to user {user.id}: {e}")
                    failed_count += 1

                    EmailNotification.log_email(
                        email=user.email if user.email else 'unknown',
                        email_type='weekly_summary',
                        user_id=user.id,
                        status='failed',
                        error_message=str(e)
                    )

                # Log progress
                if processed_count % EMAIL_BATCH_SIZE == 0:
                    logger.info(f"Progress: {processed_count}/{len(users)} processed, {sent_count} sent")

            logger.info(f"Weekly summary job complete: {sent_count} sent, {skipped_count} skipped, {failed_count} failed")

            job_run.complete(
                records_processed=len(users),
                records_success=sent_count,
                records_failed=failed_count
            )

        except Exception as e:
            logger.error(f"Weekly summary job failed: {e}")
            job_run.fail(str(e))


if __name__ == '__main__':
    logger.info("Starting weekly summary email job")
    run_weekly_summaries()
    logger.info("Weekly summary job finished")
