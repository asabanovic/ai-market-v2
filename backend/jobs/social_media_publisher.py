#!/usr/bin/env python3
"""
Social media post publisher job.
Publishes scheduled posts to Facebook when their time comes.

Schedule: Runs at each posting time (8, 11, 14, 17 UTC)
Command: python jobs/social_media_publisher.py
"""

import os
import sys
from datetime import datetime, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import SocialMediaPost, JobRun
from facebook_service import get_facebook_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Grace period for publishing (minutes before/after scheduled time)
GRACE_MINUTES_BEFORE = 5
GRACE_MINUTES_AFTER = 30


def publish_due_posts():
    """
    Publish all posts that are due to be published.
    A post is due if:
    - Status is 'scheduled'
    - Scheduled time is within the grace period (5 min before to 30 min after)
    """
    with app.app_context():
        logger.info("Starting social media publisher")

        job_run = JobRun.start('social_media_publish')

        try:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=GRACE_MINUTES_AFTER)
            window_end = now + timedelta(minutes=GRACE_MINUTES_BEFORE)

            # Get posts due for publishing
            due_posts = SocialMediaPost.query.filter(
                SocialMediaPost.status == 'scheduled',
                SocialMediaPost.scheduled_time >= window_start,
                SocialMediaPost.scheduled_time <= window_end
            ).all()

            logger.info(f"Found {len(due_posts)} posts to publish")

            if not due_posts:
                job_run.complete(records_processed=0, records_success=0, records_failed=0)
                return 0, 0

            fb = get_facebook_service()
            success_count = 0
            failed_count = 0

            for post in due_posts:
                logger.info(f"Publishing post {post.id} scheduled for {post.scheduled_time}")

                try:
                    # Publish to Facebook
                    if post.image_url:
                        result = fb.post_with_image(post.content, post.image_url)
                    else:
                        result = fb.post_text(post.content)

                    if result.get('status') == 'success':
                        post.status = 'published'
                        post.published_at = datetime.utcnow()
                        post.facebook_post_id = result.get('post_id')
                        post.error_message = None
                        success_count += 1
                        logger.info(f"Post {post.id} published successfully: {result.get('post_id')}")

                    elif result.get('status') == 'dev_mode':
                        # In dev mode, mark as published but note it wasn't actually posted
                        post.status = 'published'
                        post.published_at = datetime.utcnow()
                        post.error_message = 'DEV MODE - Not actually posted to Facebook'
                        success_count += 1
                        logger.info(f"Post {post.id} marked as published (DEV MODE)")

                    else:
                        post.status = 'failed'
                        post.error_message = result.get('error', 'Unknown error')
                        failed_count += 1
                        logger.error(f"Post {post.id} failed: {post.error_message}")

                except Exception as e:
                    post.status = 'failed'
                    post.error_message = str(e)
                    failed_count += 1
                    logger.error(f"Error publishing post {post.id}: {e}", exc_info=True)

                db.session.commit()

            logger.info(f"Publishing complete: {success_count} success, {failed_count} failed")

            job_run.complete(
                records_processed=len(due_posts),
                records_success=success_count,
                records_failed=failed_count
            )

            return success_count, failed_count

        except Exception as e:
            logger.error(f"Publisher job failed: {e}", exc_info=True)
            job_run.fail(str(e))
            raise


def publish_single_post(post_id: int, force: bool = False) -> dict:
    """
    Manually publish a single post.

    Args:
        post_id: ID of the post to publish
        force: If True, publish regardless of scheduled time

    Returns:
        dict with result status
    """
    with app.app_context():
        post = SocialMediaPost.query.get(post_id)

        if not post:
            return {'status': 'error', 'message': 'Post not found'}

        if post.status == 'published':
            return {'status': 'error', 'message': 'Post already published'}

        if post.status == 'cancelled':
            return {'status': 'error', 'message': 'Post was cancelled'}

        if not force and post.scheduled_time > datetime.utcnow():
            return {'status': 'error', 'message': 'Post not yet due for publishing'}

        fb = get_facebook_service()

        try:
            if post.image_url:
                result = fb.post_with_image(post.content, post.image_url)
            else:
                result = fb.post_text(post.content)

            if result.get('status') in ['success', 'dev_mode']:
                post.status = 'published'
                post.published_at = datetime.utcnow()
                post.facebook_post_id = result.get('post_id')
                if result.get('status') == 'dev_mode':
                    post.error_message = 'DEV MODE - Not actually posted'
                else:
                    post.error_message = None
                db.session.commit()
                return {'status': 'success', 'post_id': result.get('post_id')}
            else:
                post.status = 'failed'
                post.error_message = result.get('error')
                db.session.commit()
                return {'status': 'failed', 'error': result.get('error')}

        except Exception as e:
            post.status = 'failed'
            post.error_message = str(e)
            db.session.commit()
            return {'status': 'error', 'message': str(e)}


if __name__ == '__main__':
    logger.info("Running social media publisher")
    success, failed = publish_due_posts()
    logger.info(f"Done: {success} published, {failed} failed")
