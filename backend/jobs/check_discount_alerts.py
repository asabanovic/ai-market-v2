#!/usr/bin/env python3
"""
Scheduled Job: Check Discount Alerts
Runs periodically to check if favorited products have new discounts and create notifications
Should run every hour or when product prices are updated
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Favorite, Product, Notification, User
from sqlalchemy import and_
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_discount_notification(user_id, product_id, discount_percentage):
    """
    Create a notification when a favorited product goes on discount

    Args:
        user_id: User ID to notify
        product_id: Product that went on discount
        discount_percentage: The discount percentage

    Returns:
        Notification object or None
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return None

        # Check if notification already exists (within last 24 hours)
        existing = Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.product_id == product_id,
                Notification.notification_type == 'discount_alert',
                Notification.created_at >= datetime.now() - timedelta(hours=24)
            )
        ).first()

        if existing:
            logger.debug(f"Notification already exists for user {user_id} and product {product_id}")
            return existing  # Don't create duplicate notification

        # Create new notification
        notification = Notification(
            user_id=user_id,
            notification_type='discount_alert',
            title=f'🎉 Popust na {product.title}!',
            message=f'Proizvod koji pratite sada ima {discount_percentage}% popusta! Cijena je sada {product.discount_price:.2f} KM umjesto {product.base_price:.2f} KM.',
            product_id=product_id,
            action_url=f'/proizvodi/{product_id}'
        )

        db.session.add(notification)
        logger.info(f"Created discount notification for user {user_id} and product {product_id} ({discount_percentage}% off)")
        return notification

    except Exception as e:
        logger.error(f"Error creating discount notification: {e}")
        return None


def check_favorites_for_discounts():
    """
    Check all user favorites for new discounts and create notifications

    Returns:
        int: Number of notifications created
    """
    with app.app_context():
        try:
            # Get all favorites with products that have discounts
            favorites = db.session.query(Favorite).join(Product).filter(
                Product.discount_price.isnot(None),
                Product.discount_price < Product.base_price
            ).all()

            if not favorites:
                logger.info("No favorited products with discounts found")
                return 0

            notifications_created = 0

            for favorite in favorites:
                product = favorite.product

                # Skip expired products
                if product.is_expired:
                    continue

                # Check if user wants notifications
                user = User.query.get(favorite.user_id)
                if not user:
                    continue

                # Respect user's notification preferences
                # If they have favorites or all notifications enabled
                if user.notification_preferences not in ['favorites', 'all']:
                    logger.debug(f"User {user.id} has notifications disabled")
                    continue

                # Calculate discount percentage
                discount_percentage = product.discount_percentage

                # Only notify for significant discounts (>= 5%)
                if discount_percentage < 5:
                    continue

                # Create notification
                notification = create_discount_notification(
                    user_id=favorite.user_id,
                    product_id=product.id,
                    discount_percentage=discount_percentage
                )

                if notification:
                    notifications_created += 1

            # Commit all notifications
            db.session.commit()
            logger.info(f"Created {notifications_created} discount notifications")
            return notifications_created

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error checking favorites for discounts: {e}")
            return 0


if __name__ == '__main__':
    logger.info("Starting discount alert checking job")
    notifications_count = check_favorites_for_discounts()
    logger.info(f"Job completed. Created {notifications_count} notifications")
    sys.exit(0)
