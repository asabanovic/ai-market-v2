#!/usr/bin/env python3
"""
Monthly re-engagement email job for users without tracked products.
Sends emails to users who haven't set up product tracking, showing
popular products others are tracking and current best deals.

Schedule: 1st of each month at 8 AM UTC
Command: python jobs/monthly_reengagement.py
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserTrackedProduct, Product, Business, JobRun, EmailNotification
from sendgrid_utils import send_reengagement_email
from sqlalchemy import func, desc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
EMAIL_BATCH_SIZE = 10  # Log progress every N emails
DELAY_BETWEEN_EMAILS = 0.5  # Seconds between emails


def get_popular_tracked_terms(limit: int = 10) -> list:
    """Get most popular search terms that users are tracking."""
    results = db.session.query(
        UserTrackedProduct.search_term,
        func.count(func.distinct(UserTrackedProduct.user_id)).label('users_count')
    ).filter(
        UserTrackedProduct.is_active == True
    ).group_by(
        UserTrackedProduct.search_term
    ).order_by(
        desc('users_count')
    ).limit(limit).all()

    return [{'term': r.search_term, 'users_count': r.users_count} for r in results]


def get_best_current_deals(limit: int = 10) -> list:
    """Get current best discounted products."""
    # Get products with discount that haven't expired
    results = Product.query.join(Business).filter(
        Product.discount_price.isnot(None),
        Product.discount_price < Product.base_price,
        db.or_(Product.expires.is_(None), Product.expires >= datetime.now().date())
    ).order_by(
        # Order by discount percentage
        ((Product.base_price - Product.discount_price) / Product.base_price).desc()
    ).limit(limit * 2).all()

    deals = []
    seen_titles = set()
    for p in results:
        # Dedupe by similar title prefix
        title_prefix = p.title[:20].lower() if p.title else ''
        if title_prefix in seen_titles:
            continue
        seen_titles.add(title_prefix)

        discount_pct = round(((p.base_price - p.discount_price) / p.base_price) * 100)
        deals.append({
            'title': p.title,
            'store': p.business.name if p.business else '',
            'discount_price': p.discount_price,
            'discount_percent': discount_pct
        })

        if len(deals) >= limit:
            break

    return deals


def get_users_without_tracking() -> list:
    """Get users who have no tracked products and have email enabled."""
    # Subquery to get user IDs that have tracked products
    users_with_tracking = db.session.query(
        UserTrackedProduct.user_id
    ).filter(
        UserTrackedProduct.is_active == True
    ).distinct().subquery()

    # Get users who are NOT in that list
    users = User.query.filter(
        User.email.isnot(None),
        User.email != '',
        ~User.id.in_(db.session.query(users_with_tracking.c.user_id))
    ).all()

    # Filter out users who have email notifications disabled
    eligible_users = []
    for user in users:
        prefs = user.preferences or {}
        if prefs.get('email_notifications', True):
            eligible_users.append(user)

    return eligible_users


def get_total_users_tracking() -> int:
    """Get count of users who have tracked products."""
    return db.session.query(
        func.count(func.distinct(UserTrackedProduct.user_id))
    ).filter(
        UserTrackedProduct.is_active == True
    ).scalar() or 0


def run_reengagement_emails():
    """Send monthly re-engagement emails."""
    with app.app_context():
        # Check if it's the 1st of the month
        now = datetime.utcnow()
        if now.day != 1:
            logger.info("Skipping reengagement emails - not the 1st of month")
            return

        # Start tracking this job run
        job_run = JobRun.start('monthly_reengagement')

        try:
            # Get users without tracking
            users = get_users_without_tracking()
            logger.info(f"Found {len(users)} users without product tracking")

            if not users:
                job_run.complete(records_processed=0, records_success=0, records_failed=0)
                return

            # Get popular terms and best deals (shared across all emails)
            popular_terms = get_popular_tracked_terms(limit=10)
            best_deals = get_best_current_deals(limit=10)
            total_users_tracking = get_total_users_tracking()

            logger.info(f"Popular terms: {len(popular_terms)}, Best deals: {len(best_deals)}")
            logger.info(f"Total users tracking: {total_users_tracking}")

            if not popular_terms and not best_deals:
                logger.info("No popular terms or deals to show, skipping emails")
                job_run.complete(records_processed=0, records_success=0, records_failed=0)
                return

            email_data = {
                'popular_terms': popular_terms,
                'best_deals': best_deals,
                'total_users_tracking': total_users_tracking
            }

            sent_count = 0
            failed_count = 0
            processed_count = 0

            for user in users:
                processed_count += 1

                try:
                    user_name = user.first_name or user.email.split('@')[0]

                    if send_reengagement_email(user.email, user_name, email_data):
                        sent_count += 1

                        # Log the email
                        EmailNotification.log_email(
                            email=user.email,
                            email_type='monthly_reengagement',
                            subject=f"{total_users_tracking} korisnika vec stedi - pridruzite se!",
                            user_id=user.id,
                            status='sent',
                            extra_data={
                                'popular_terms_count': len(popular_terms),
                                'deals_count': len(best_deals)
                            }
                        )

                        # Rate limit
                        time.sleep(DELAY_BETWEEN_EMAILS)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error sending email to user {user.id}: {e}")
                    failed_count += 1

                    EmailNotification.log_email(
                        email=user.email if user.email else 'unknown',
                        email_type='monthly_reengagement',
                        user_id=user.id,
                        status='failed',
                        error_message=str(e)
                    )

                # Log progress
                if processed_count % EMAIL_BATCH_SIZE == 0:
                    logger.info(f"Progress: {processed_count}/{len(users)} processed, {sent_count} sent")

            logger.info(f"Reengagement job complete: {sent_count} sent, {failed_count} failed")

            job_run.complete(
                records_processed=len(users),
                records_success=sent_count,
                records_failed=failed_count
            )

        except Exception as e:
            logger.error(f"Reengagement job failed: {e}")
            job_run.fail(str(e))


if __name__ == '__main__':
    logger.info("Starting monthly reengagement email job")
    run_reengagement_emails()
    logger.info("Monthly reengagement job finished")
