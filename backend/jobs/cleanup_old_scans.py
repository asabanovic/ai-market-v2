#!/usr/bin/env python3
"""
Cleanup old scan data job.
Deletes scans older than 90 days to manage database size.

Schedule: Weekly on Sunday at 3 AM UTC (0 3 * * 0)
Command: python jobs/cleanup_old_scans.py
"""

import os
import sys
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import UserProductScan, UserScanResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RETENTION_DAYS = 90


def cleanup_old_scans():
    """Delete scans older than RETENTION_DAYS"""
    with app.app_context():
        try:
            cutoff_date = date.today() - timedelta(days=RETENTION_DAYS)

            # Get old scans
            old_scans = UserProductScan.query.filter(
                UserProductScan.scan_date < cutoff_date
            ).all()

            if not old_scans:
                logger.info("No old scans to clean up")
                return

            scan_ids = [s.id for s in old_scans]
            logger.info(f"Cleaning up {len(scan_ids)} scans older than {cutoff_date}")

            # Delete results first (cascade should handle this, but being explicit)
            deleted_results = UserScanResult.query.filter(
                UserScanResult.scan_id.in_(scan_ids)
            ).delete(synchronize_session=False)

            # Delete scans
            deleted_scans = UserProductScan.query.filter(
                UserProductScan.id.in_(scan_ids)
            ).delete(synchronize_session=False)

            db.session.commit()

            logger.info(f"Cleaned up {deleted_scans} scans and {deleted_results} results")

        except Exception as e:
            logger.error(f"Error cleaning up old scans: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()


if __name__ == '__main__':
    logger.info(f"Starting cleanup job (retention: {RETENTION_DAYS} days)")
    cleanup_old_scans()
    logger.info("Cleanup job finished")
