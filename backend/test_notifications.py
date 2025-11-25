#!/usr/bin/env python3
"""
Test script for the notification system
Creates test notifications to verify the entire flow works
"""
import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Notification, User, Product, Favorite
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_notification():
    """Create a test notification for the admin user"""
    with app.app_context():
        try:
            # Get admin user
            admin_user = User.query.filter_by(email="adnanxteam@gmail.com").first()
            if not admin_user:
                logger.error("Admin user not found")
                return False

            # Get any product with discount
            product = Product.query.filter(
                Product.discount_price.isnot(None),
                Product.discount_price < Product.base_price
            ).first()

            if not product:
                logger.warning("No products with discounts found, creating generic notification")
                # Create a generic notification
                notification = Notification(
                    user_id=admin_user.id,
                    notification_type='discount_alert',
                    title='🎉 Test notifikacija!',
                    message='Ovo je test notifikacija za sistem popusta. Sistem radi ispravno!',
                    is_read=False
                )
            else:
                # Calculate discount percentage
                discount_percentage = round(((product.base_price - product.discount_price) / product.base_price) * 100)

                # Create notification
                notification = Notification(
                    user_id=admin_user.id,
                    notification_type='discount_alert',
                    title=f'🎉 Popust na {product.title}!',
                    message=f'Proizvod koji pratite sada ima {discount_percentage}% popusta! Cijena je sada {product.discount_price:.2f} KM umjesto {product.base_price:.2f} KM.',
                    product_id=product.id,
                    action_url=f'/proizvodi/{product.id}',
                    is_read=False
                )

            db.session.add(notification)
            db.session.commit()

            logger.info(f"✅ Test notification created: {notification.title}")
            logger.info(f"   User: {admin_user.email}")
            logger.info(f"   Message: {notification.message}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating test notification: {e}")
            return False


def check_notifications():
    """Check existing notifications"""
    with app.app_context():
        try:
            admin_user = User.query.filter_by(email="adnanxteam@gmail.com").first()
            if not admin_user:
                logger.error("Admin user not found")
                return

            notifications = Notification.query.filter_by(user_id=admin_user.id).order_by(
                Notification.created_at.desc()
            ).limit(5).all()

            logger.info(f"\n📬 Found {len(notifications)} notifications for {admin_user.email}:")
            for notif in notifications:
                status = "❌ Unread" if not notif.is_read else "✅ Read"
                logger.info(f"   {status} - {notif.title}")
                logger.info(f"      {notif.message}")
                logger.info(f"      Created: {notif.created_at}")
                logger.info("")

        except Exception as e:
            logger.error(f"Error checking notifications: {e}")


def run_discount_check():
    """Run the discount checking job"""
    from jobs.check_discount_alerts import check_favorites_for_discounts
    logger.info("Running discount alert check...")
    count = check_favorites_for_discounts()
    logger.info(f"Created {count} discount notifications")


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("NOTIFICATION SYSTEM TEST")
    logger.info("=" * 60)

    # Check existing notifications
    logger.info("\n1. Checking existing notifications...")
    check_notifications()

    # Create test notification
    logger.info("\n2. Creating test notification...")
    create_test_notification()

    # Check notifications again
    logger.info("\n3. Checking notifications after test...")
    check_notifications()

    # Run discount check job
    logger.info("\n4. Running discount check job...")
    run_discount_check()

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETED")
    logger.info("=" * 60)
    logger.info("\nYou can now:")
    logger.info("1. Open the frontend and check the notification bell")
    logger.info("2. Click the bell icon to see notifications")
    logger.info("3. Test marking as read and deleting notifications")

    sys.exit(0)
