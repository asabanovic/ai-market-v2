#!/usr/bin/env python3
"""
Email summary job for user product scans.
Sends email summaries to users who had scans completed today.

Features:
- Groups results by tracked search term
- Shows lowest/highest prices per term with store names
- Highlights new products and new discounts
- Links to /moji-proizvodi page for full details

Schedule: Daily at 7 AM UTC (after scan job completes at 6 AM)
Command: python jobs/send_scan_email_summaries.py
"""

import os
import sys
import time
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserProductScan, UserScanResult, UserTrackedProduct, JobRun, EmailNotification
from sendgrid_utils import send_scan_summary_email as sendgrid_scan_summary, plural_bs
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.environ.get("BASE_URL", "https://popust.ba")
EMAIL_BATCH_SIZE = 10  # Log progress every N emails
DELAY_BETWEEN_EMAILS = 0.5  # Seconds to wait between emails (avoid rate limits)


def get_scan_summary_for_user(user_id: int, scan_date: date) -> dict:
    """
    Get detailed scan summary grouped by tracked product term.

    Returns dict with:
    - total_products: int
    - new_products: int
    - new_discounts: int
    - terms: list of term summaries
    """
    scan = UserProductScan.query.filter_by(
        user_id=user_id,
        scan_date=scan_date,
        status='completed'
    ).first()

    if not scan:
        return None

    # Get all results grouped by tracked product
    results = UserScanResult.query.filter_by(scan_id=scan.id).all()

    # Group by tracked product
    term_groups = {}
    for result in results:
        tracked = UserTrackedProduct.query.get(result.tracked_product_id)
        if not tracked:
            continue

        term = tracked.search_term
        if term not in term_groups:
            term_groups[term] = {
                'search_term': term,
                'original_text': tracked.original_text,
                'products': [],
                'new_count': 0,
                'discount_count': 0
            }

        term_groups[term]['products'].append({
            'title': result.product_title,
            'business': result.business_name,
            'base_price': result.base_price,
            'discount_price': result.discount_price,
            'is_new': result.is_new_today,
            'price_dropped': result.price_dropped_today
        })

        if result.is_new_today:
            term_groups[term]['new_count'] += 1
        if result.price_dropped_today:
            term_groups[term]['discount_count'] += 1

    # Calculate stats per term
    terms = []
    for term, data in term_groups.items():
        products = data['products']
        if not products:
            continue

        # Get effective prices (discount or base) and calculate actual savings
        prices_with_store = []
        for p in products:
            effective_price = p['discount_price'] if p['discount_price'] else p['base_price']
            if effective_price:
                # Calculate actual discount savings (base_price - discount_price)
                actual_saving = 0.0
                if p['discount_price'] and p['base_price']:
                    actual_saving = float(p['base_price']) - float(p['discount_price'])
                    if actual_saving < 0:
                        actual_saving = 0.0

                prices_with_store.append({
                    'price': float(effective_price),
                    'store': p['business'],
                    'title': p['title'],
                    'is_discounted': p['discount_price'] is not None,
                    'base_price': float(p['base_price']) if p['base_price'] else None,
                    'discount_price': float(p['discount_price']) if p['discount_price'] else None,
                    'actual_saving': actual_saving
                })

        if not prices_with_store:
            continue

        # Sort by price
        prices_with_store.sort(key=lambda x: x['price'])

        lowest = prices_with_store[0]
        highest = prices_with_store[-1]

        # Find the best saving among all discounted products for this term
        best_saving = max((p['actual_saving'] for p in prices_with_store if p['actual_saving'] > 0), default=0.0)

        terms.append({
            'search_term': term,
            'original_text': data['original_text'],
            'total_products': len(products),
            'new_count': data['new_count'],
            'discount_count': data['discount_count'],
            'lowest_price': lowest['price'],
            'lowest_store': lowest['store'],
            'lowest_product': lowest['title'],
            'lowest_is_discounted': lowest['is_discounted'],
            'lowest_base_price': lowest.get('base_price'),
            'lowest_actual_saving': lowest.get('actual_saving', 0),
            'best_saving': best_saving,  # Best savings for this term
            'highest_price': highest['price'],
            'highest_store': highest['store']
        })

    # Sort terms by those with new products/discounts first
    terms.sort(key=lambda x: (-x['new_count'], -x['discount_count'], x['search_term']))

    return {
        'total_products': scan.total_products_found or 0,
        'new_products': scan.new_products_count or 0,
        'new_discounts': scan.new_discounts_count or 0,
        'terms': terms
    }


def generate_scan_email_html(user_name: str, summary: dict) -> str:
    """Generate HTML email for scan summary."""
    logo_url = get_logo_url()
    moji_proizvodi_url = f"{BASE_URL}/moji-proizvodi"

    # Build terms HTML
    terms_html = ""
    for term in summary['terms']:
        # Badge for new products/discounts
        badges = ""
        if term['new_count'] > 0:
            badges += f'<span style="background-color: #10B981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px;">{term["new_count"]} novo</span>'
        if term['discount_count'] > 0:
            badges += f'<span style="background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{term["discount_count"]} sniženo</span>'

        # Discount indicator
        discount_badge = ""
        if term['lowest_is_discounted']:
            discount_badge = '<span style="color: #EF4444; font-weight: bold;">AKCIJA</span> '

        terms_html += f"""
        <div style="background-color: #F9FAFB; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #10B981;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 16px; color: #1F2937;">🔍 {term['search_term']}</h3>
                <span style="color: #6B7280; font-size: 13px;">{term['total_products']} proizvoda</span>
            </div>
            {f'<div style="margin-bottom: 8px;">{badges}</div>' if badges else ''}
            <div style="margin-top: 8px;">
                <div style="font-size: 14px; color: #374151;">
                    {discount_badge}<strong>Najniža cijena:</strong> {term['lowest_price']:.2f} KM
                    <span style="color: #6B7280;">({term['lowest_store']})</span>
                </div>
                <div style="font-size: 12px; color: #6B7280; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {term['lowest_product'][:50]}{'...' if len(term['lowest_product']) > 50 else ''}
                </div>
            </div>
        </div>
        """

    # Summary badges
    summary_items = []
    if summary['new_products'] > 0:
        product_text = plural_bs(summary['new_products'], "novi proizvod", "nova proizvoda", "novih proizvoda")
        summary_items.append(f"<strong>{summary['new_products']}</strong> {product_text}")
    if summary['new_discounts'] > 0:
        discount_text = plural_bs(summary['new_discounts'], "novi popust", "nova popusta", "novih popusta")
        summary_items.append(f"<strong>{summary['new_discounts']}</strong> {discount_text}")

    summary_text = " i ".join(summary_items) if summary_items else "Nema novih promjena"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Dnevni pregled proizvoda - Popust.ba</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #10B981; }}
            .content {{ padding: 24px 0; }}
            .summary-box {{ background-color: #ECFDF5; border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center; }}
            .button {{ display: inline-block; background-color: #10B981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 13px; color: #6B7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{logo_url}" alt="Popust.ba" style="height: 40px; width: auto;">
            </div>

            <div class="content">
                <h2 style="color: #1F2937; margin-bottom: 8px;">Dobro jutro, {user_name}!</h2>
                <p style="color: #6B7280; margin-top: 0;">Evo pregleda vaših praćenih proizvoda za danas:</p>

                <div class="summary-box">
                    <div style="font-size: 32px; font-weight: bold; color: #10B981;">{summary['total_products']}</div>
                    <div style="color: #374151; font-size: 14px;">ukupno proizvoda pronađeno</div>
                    <div style="margin-top: 8px; font-size: 14px; color: #059669;">{summary_text}</div>
                </div>

                <h3 style="color: #1F2937; margin-bottom: 16px;">Po kategorijama:</h3>

                {terms_html}

                <div style="text-align: center; margin-top: 24px;">
                    <a href="{moji_proizvodi_url}" class="button">Pogledaj sve proizvode</a>
                </div>

                <p style="text-align: center; color: #6B7280; font-size: 13px; margin-top: 16px;">
                    Klikni gore da vidiš sve pronađene proizvode, uporediš cijene i pronađeš najbolje ponude.
                </p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Popust.ba. Sva prava zadržana.</p>
                <p style="font-size: 12px; color: #9CA3AF;">
                    Primaš ovaj email jer imaš aktivno praćenje proizvoda na Popust.ba.
                    <br>Za upravljanje obavještenjima posjetite <a href="{BASE_URL}/profil" style="color:#10B981;">Vaš profil</a>.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def send_scan_summary_email(user: User, summary: dict) -> bool:
    """Send scan summary email to a user."""
    if not user.email:
        logger.warning(f"User {user.id} has no email address")
        return False

    # Check if user has email notifications enabled (default: True)
    prefs = user.preferences or {}

    # Check legacy email_notifications setting
    if not prefs.get('email_notifications', True):
        logger.info(f"User {user.id} has email notifications disabled")
        return False

    # Check new daily_emails preference (default: True)
    email_prefs = prefs.get('email_preferences', {})
    if not email_prefs.get('daily_emails', True):
        logger.info(f"User {user.id} has daily emails disabled")
        return False

    # Only send if there are new products or price drops
    if summary.get('new_products', 0) == 0 and summary.get('new_discounts', 0) == 0:
        logger.info(f"User {user.id}: no new products or discounts, skipping email")
        return False

    user_name = user.first_name or user.email.split('@')[0]

    # Use SendGrid template
    return sendgrid_scan_summary(user.email, user_name, summary)


def run_email_summaries():
    """Send email summaries for all users who had scans today."""
    with app.app_context():
        # Start tracking this job run
        job_run = JobRun.start('email_summary')

        try:
            today = date.today()

            # Get all completed scans for today
            completed_scans = UserProductScan.query.filter_by(
                scan_date=today,
                status='completed'
            ).all()

            if not completed_scans:
                logger.info("No completed scans found for today")
                job_run.complete(records_processed=0, records_success=0, records_failed=0)
                return

            logger.info(f"Found {len(completed_scans)} completed scans for today")

            # Get users who already received a daily or weekly email today to prevent duplicates
            # Skip daily email if user already got weekly email today
            from datetime import datetime
            today_start = datetime.combine(today, datetime.min.time())
            already_emailed_today = set(
                row[0] for row in db.session.query(EmailNotification.user_id).filter(
                    EmailNotification.email_type.in_(['daily_scan', 'weekly_scan']),
                    EmailNotification.status == 'sent',
                    EmailNotification.sent_at >= today_start
                ).all() if row[0] is not None
            )
            # Also track by email address to prevent duplicates when same email has multiple user_ids
            # or when race conditions between job instances occur
            already_emailed_addresses = set(
                row[0].lower() for row in db.session.query(EmailNotification.email).filter(
                    EmailNotification.email_type.in_(['daily_scan', 'weekly_scan']),
                    EmailNotification.status == 'sent',
                    EmailNotification.sent_at >= today_start
                ).all() if row[0] is not None
            )
            logger.info(f"Found {len(already_emailed_today)} users/{len(already_emailed_addresses)} emails already emailed today")

            sent_count = 0
            skipped_count = 0
            failed_count = 0
            emailed_user_ids = set()  # Track users emailed in this run
            emailed_addresses = set()  # Track email addresses emailed in this run

            processed_count = 0
            for scan in completed_scans:
                processed_count += 1
                user = User.query.get(scan.user_id)
                if not user or not user.email:
                    continue

                user_email_lower = user.email.lower()

                # Skip if user already received email today (daily or weekly)
                if user.id in already_emailed_today:
                    logger.debug(f"User {user.id} already received daily/weekly email today, skipping")
                    skipped_count += 1
                    continue

                # Skip if email address already received email today (handles race conditions)
                if user_email_lower in already_emailed_addresses:
                    logger.debug(f"Email {user.email} already received email today, skipping user {user.id}")
                    skipped_count += 1
                    continue

                # Skip if we already emailed this user in this job run
                if user.id in emailed_user_ids:
                    logger.debug(f"User {user.id} already processed in this run, skipping")
                    skipped_count += 1
                    continue

                # Skip if we already emailed this email address in this job run
                if user_email_lower in emailed_addresses:
                    logger.debug(f"Email {user.email} already processed in this run, skipping user {user.id}")
                    skipped_count += 1
                    continue

                # Get summary
                summary = get_scan_summary_for_user(user.id, today)
                if not summary or summary['total_products'] == 0:
                    skipped_count += 1
                    continue

                # Send email
                try:
                    if send_scan_summary_email(user, summary):
                        emailed_user_ids.add(user.id)  # Mark as emailed
                        emailed_addresses.add(user_email_lower)  # Track email address too
                        sent_count += 1

                        # Log the email notification
                        EmailNotification.log_email(
                            email=user.email,
                            email_type='daily_scan',
                            subject=f"Dnevni pregled - {summary['total_products']} proizvoda pronađeno",
                            user_id=user.id,
                            status='sent',
                            extra_data={
                                'total_products': summary['total_products'],
                                'new_products': summary['new_products'],
                                'new_discounts': summary['new_discounts'],
                                'terms_count': len(summary['terms'])
                            }
                        )

                        # Rate limit between emails
                        time.sleep(DELAY_BETWEEN_EMAILS)
                    else:
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Error sending email to user {user.id}: {e}")
                    failed_count += 1

                    # Log failed email
                    EmailNotification.log_email(
                        email=user.email if user else 'unknown',
                        email_type='daily_scan',
                        user_id=user.id if user else None,
                        status='failed',
                        error_message=str(e)
                    )

                # Log progress every N emails
                if processed_count % EMAIL_BATCH_SIZE == 0:
                    logger.info(f"Progress: {processed_count}/{len(completed_scans)} processed, {sent_count} sent")

            logger.info(f"Email summary job complete: {sent_count} sent, {skipped_count} skipped, {failed_count} failed")

            # Complete job tracking
            job_run.complete(
                records_processed=len(completed_scans),
                records_success=sent_count,
                records_failed=failed_count
            )

        except Exception as e:
            logger.error(f"Email summary job failed: {e}")
            job_run.fail(str(e))


if __name__ == '__main__':
    logger.info("Starting email summary job")
    run_email_summaries()
    logger.info("Email summary job finished")
