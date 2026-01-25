#!/usr/bin/env python3
"""
Coupon reminder job.
Sends email reminders for:
1. Coupons at 50% of validity period
2. Coupons expiring tomorrow
3. Updates expired coupons status

Runs daily at 8:00 AM Bosnia time (7:00 AM UTC).
"""

import os
import sys
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_coupon_reminders():
    """
    Process coupon reminders:
    1. Find coupons at 50% validity and send reminder
    2. Find coupons expiring tomorrow and send urgent reminder
    3. Mark expired coupons as expired
    """
    from app import db
    from models import UserCoupon, Coupon
    from sendgrid_utils import (
        send_coupon_halfway_reminder_email,
        send_coupon_expiry_reminder_email
    )

    logger.info("Starting coupon reminder job...")
    now = datetime.utcnow()

    # Track sent reminders to avoid duplicates
    halfway_sent = 0
    expiry_sent = 0
    expired_count = 0

    # Get all active coupons
    active_coupons = UserCoupon.query.filter(
        UserCoupon.status == 'active'
    ).all()

    logger.info(f"Found {len(active_coupons)} active coupons to process")

    for uc in active_coupons:
        try:
            coupon = uc.coupon
            user = uc.user
            business = coupon.business

            # Skip deactivated users
            if user.deleted_at is not None:
                logger.debug(f"User {user.id} is deactivated, skipping coupon reminder")
                continue

            # Check if coupon has expired
            if uc.expires_at and uc.expires_at < now:
                uc.status = 'expired'
                expired_count += 1
                db.session.commit()
                logger.info(f"Marked coupon {uc.id} as expired")
                continue

            # Calculate validity timeline
            if not uc.purchased_at or not uc.expires_at:
                continue

            total_validity = (uc.expires_at - uc.purchased_at).total_seconds()
            elapsed = (now - uc.purchased_at).total_seconds()
            remaining_days = (uc.expires_at - now).days

            # Check for 50% reminder (only if not already sent)
            halfway_mark = uc.purchased_at + timedelta(seconds=total_validity / 2)
            within_halfway_window = abs((now - halfway_mark).total_seconds()) < 86400  # Within 24 hours

            if within_halfway_window and not uc.reminder_50_sent:
                # Send 50% reminder
                coupon_data = {
                    'redemption_code': uc.redemption_code,
                    'article_name': coupon.article_name,
                    'business_name': business.name,
                    'business_address': business.address or '',
                    'final_price': coupon.final_price,
                    'expires_at': uc.expires_at.strftime('%d.%m.%Y'),
                    'days_remaining': remaining_days
                }

                success = send_coupon_halfway_reminder_email(
                    user.email,
                    user.first_name or '',
                    coupon_data
                )

                if success:
                    uc.reminder_50_sent = True
                    db.session.commit()
                    halfway_sent += 1
                    logger.info(f"Sent halfway reminder for coupon {uc.id} to {user.email}")

            # Check for expiry reminder (expires tomorrow)
            expires_tomorrow = (uc.expires_at.date() - now.date()).days == 1

            if expires_tomorrow and not uc.reminder_final_sent:
                # Send expiry reminder
                coupon_data = {
                    'redemption_code': uc.redemption_code,
                    'article_name': coupon.article_name,
                    'business_name': business.name,
                    'business_address': business.address or '',
                    'final_price': coupon.final_price,
                    'expires_at': uc.expires_at.strftime('%d.%m.%Y')
                }

                success = send_coupon_expiry_reminder_email(
                    user.email,
                    user.first_name or '',
                    coupon_data
                )

                if success:
                    uc.reminder_final_sent = True
                    db.session.commit()
                    expiry_sent += 1
                    logger.info(f"Sent expiry reminder for coupon {uc.id} to {user.email}")

        except Exception as e:
            logger.error(f"Error processing coupon {uc.id}: {e}")
            continue

    logger.info(f"Coupon reminder job completed:")
    logger.info(f"  - Halfway reminders sent: {halfway_sent}")
    logger.info(f"  - Expiry reminders sent: {expiry_sent}")
    logger.info(f"  - Coupons marked as expired: {expired_count}")


if __name__ == "__main__":
    from app import app
    with app.app_context():
        run_coupon_reminders()
