#!/usr/bin/env python3
"""
Unified job scheduler for all background tasks.
Runs as a single process and executes jobs at their scheduled times.

Usage:
  python jobs/scheduler.py

On Railway, run this as a separate worker service.
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory cache for last run times (also persisted to DB via JobRun)
last_run = {}


class Job:
    """Represents a scheduled job."""

    def __init__(self, name: str, hour: int, minute: int, func, enabled: bool = True):
        self.name = name
        self.hour = hour  # UTC hour (0-23)
        self.minute = minute  # Minute (0-59)
        self.func = func
        self.enabled = enabled

    def should_run(self, now: datetime) -> bool:
        """Check if job should run at current time."""
        if not self.enabled:
            return False

        # Check if it's the right time (within 1 minute window)
        if now.hour != self.hour or now.minute != self.minute:
            return False

        # Check if already ran today
        today = now.date()
        last = last_run.get(self.name)
        if last and last.date() == today:
            return False

        return True

    def run(self):
        """Execute the job."""
        try:
            logger.info(f"Starting job: {self.name}")
            start_time = time.time()

            self.func()

            elapsed = time.time() - start_time
            logger.info(f"Completed job: {self.name} in {elapsed:.1f}s")
            last_run[self.name] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Job {self.name} failed: {e}", exc_info=True)


def run_scan_job():
    """Run the product scan job."""
    from jobs.scan_user_products import run_daily_scan
    run_daily_scan()


def run_email_summary_job():
    """Run the email summary job."""
    from jobs.send_scan_email_summaries import run_email_summaries
    run_email_summaries()


def run_monthly_credits_job():
    """Run monthly credits allocation (1st of each month)."""
    now = datetime.utcnow()
    if now.day != 1:
        logger.info("Skipping monthly credits - not the 1st of month")
        return

    from credits_service_monthly import allocate_monthly_credits
    allocate_monthly_credits()


def run_coupon_reminders_job():
    """Run coupon reminder job (50% and expiry notifications)."""
    from jobs.coupon_reminders import run_coupon_reminders
    run_coupon_reminders()


def run_weekly_summary_job():
    """Run weekly summary emails for users with tracked products (Sundays)."""
    now = datetime.utcnow()
    if now.weekday() != 6:  # 6 = Sunday
        logger.info("Skipping weekly summary - not Sunday")
        return

    from jobs.weekly_summary import run_weekly_summaries
    run_weekly_summaries()


def run_biweekly_reengagement_job():
    """Run bi-weekly re-engagement emails for users without tracked products (1st and 15th of each month)."""
    now = datetime.utcnow()
    if now.day not in [1, 15]:
        logger.info("Skipping bi-weekly reengagement - not the 1st or 15th of month")
        return

    from jobs.monthly_reengagement import run_reengagement_emails
    run_reengagement_emails()


def run_social_media_generator_job():
    """Generate social media posts for the next 5 days."""
    from jobs.social_media_generator import generate_scheduled_posts
    generate_scheduled_posts()


def run_social_media_publisher_job():
    """Publish due social media posts to Facebook."""
    from jobs.social_media_publisher import publish_due_posts
    publish_due_posts()


# Define all scheduled jobs
JOBS = [
    # Product scan - runs at 6:00 AM UTC daily
    Job("product_scan", hour=6, minute=0, func=run_scan_job),

    # Daily email summaries - runs at 7:00 AM UTC daily (after scan completes)
    # Only sends if there are new products or price drops
    Job("email_summary", hour=7, minute=0, func=run_email_summary_job),

    # Weekly summary - runs at 8:00 AM UTC on Sundays (9 AM Bosnia time)
    # Comprehensive weekly overview for users with tracked products
    Job("weekly_summary", hour=8, minute=0, func=run_weekly_summary_job),

    # Monthly credits - runs at 0:05 AM UTC on 1st of month
    Job("monthly_credits", hour=0, minute=5, func=run_monthly_credits_job),

    # Coupon reminders - runs at 7:00 AM UTC daily (8 AM Bosnia time)
    Job("coupon_reminders", hour=7, minute=0, func=run_coupon_reminders_job),

    # Bi-weekly reengagement emails - runs at 8:00 AM UTC on 1st and 15th of month
    # For users without tracked products, encouraging them to set up tracking
    Job("biweekly_reengagement", hour=8, minute=0, func=run_biweekly_reengagement_job),

    # Social media post generator - runs at 0:05 AM UTC daily
    # Generates posts for the next 5 days
    Job("social_media_generate", hour=0, minute=5, func=run_social_media_generator_job),

    # Social media publisher - runs at posting times (9am, 12pm, 3pm, 6pm Bosnia time)
    Job("social_media_publish_9am", hour=8, minute=0, func=run_social_media_publisher_job),
    Job("social_media_publish_12pm", hour=11, minute=0, func=run_social_media_publisher_job),
    Job("social_media_publish_3pm", hour=14, minute=0, func=run_social_media_publisher_job),
    Job("social_media_publish_6pm", hour=17, minute=0, func=run_social_media_publisher_job),
]


def get_job_status():
    """Get status of all jobs for monitoring."""
    from models import JobRun

    status = []
    now = datetime.utcnow()

    for job in JOBS:
        next_run = datetime(now.year, now.month, now.day, job.hour, job.minute)
        if next_run <= now:
            next_run += timedelta(days=1)

        # Get last run from database
        last_job_run = JobRun.get_last_run(job.name)
        last_run_info = None
        if last_job_run:
            last_run_info = {
                'started_at': last_job_run.started_at.isoformat() if last_job_run.started_at else None,
                'completed_at': last_job_run.completed_at.isoformat() if last_job_run.completed_at else None,
                'status': last_job_run.status,
                'duration_seconds': last_job_run.duration_seconds,
                'records_processed': last_job_run.records_processed,
                'records_success': last_job_run.records_success,
                'records_failed': last_job_run.records_failed,
                'error_message': last_job_run.error_message
            }

        status.append({
            'name': job.name,
            'enabled': job.enabled,
            'scheduled_time': f"{job.hour:02d}:{job.minute:02d} UTC",
            'last_run': last_run_info,
            'next_run': next_run.isoformat(),
        })

    return status


def get_job_history(job_name: str = None, limit: int = 50):
    """Get job run history for monitoring."""
    from models import JobRun

    query = JobRun.query
    if job_name:
        query = query.filter_by(job_name=job_name)

    runs = query.order_by(JobRun.started_at.desc()).limit(limit).all()

    return [{
        'id': run.id,
        'job_name': run.job_name,
        'status': run.status,
        'started_at': run.started_at.isoformat() if run.started_at else None,
        'completed_at': run.completed_at.isoformat() if run.completed_at else None,
        'duration_seconds': run.duration_seconds,
        'records_processed': run.records_processed,
        'records_success': run.records_success,
        'records_failed': run.records_failed,
        'error_message': run.error_message
    } for run in runs]


def main():
    """Main scheduler loop."""
    logger.info("=" * 60)
    logger.info("Starting unified job scheduler")
    logger.info(f"Registered {len(JOBS)} jobs:")
    for job in JOBS:
        status = "enabled" if job.enabled else "disabled"
        logger.info(f"  - {job.name}: {job.hour:02d}:{job.minute:02d} UTC ({status})")
    logger.info("=" * 60)

    check_interval = 30  # Check every 30 seconds

    while True:
        try:
            now = datetime.utcnow()

            for job in JOBS:
                if job.should_run(now):
                    # Run job in a separate thread to not block scheduler
                    thread = threading.Thread(target=job.run, name=job.name)
                    thread.start()

            time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(60)  # Wait a bit before retrying


if __name__ == "__main__":
    # Import Flask app context
    from app import app

    with app.app_context():
        main()
