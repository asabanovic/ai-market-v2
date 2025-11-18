#!/usr/bin/env python3
"""
Scheduled Job: Expire Shopping Lists
Runs every 10 minutes to expire ACTIVE shopping lists past their 24-hour TTL
"""
import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import ShoppingList
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def expire_shopping_lists():
    """Expire shopping lists that have passed their TTL"""
    with app.app_context():
        try:
            # Find all ACTIVE lists that have expired
            expired_lists = ShoppingList.query.filter(
                ShoppingList.status == 'ACTIVE',
                ShoppingList.expires_at < datetime.now()
            ).all()

            if not expired_lists:
                logger.info("No shopping lists to expire")
                return 0

            # Update status to EXPIRED
            count = 0
            for shopping_list in expired_lists:
                shopping_list.status = 'EXPIRED'
                count += 1
                logger.info(f"Expired shopping list {shopping_list.id} for user {shopping_list.user_id}")

            db.session.commit()
            logger.info(f"Expired {count} shopping lists")
            return count

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error expiring shopping lists: {e}")
            return 0


if __name__ == '__main__':
    logger.info("Starting shopping list expiration job")
    expired_count = expire_shopping_lists()
    logger.info(f"Job completed. Expired {expired_count} lists")
    sys.exit(0)
