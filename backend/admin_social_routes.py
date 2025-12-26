"""
Admin API routes for social media post management.
Allows viewing, deleting, and managing scheduled posts.
"""

from flask import Blueprint, jsonify, request
from functools import wraps
from datetime import datetime, date, timedelta
import logging

admin_social_bp = Blueprint('admin_social', __name__, url_prefix='/api/admin/social')
logger = logging.getLogger(__name__)


def jwt_admin_required(f):
    """Decorator to require admin privileges via JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token
        from models import User

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401

            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403

            request.jwt_user = user
            request.jwt_user_id = user_id
        except Exception as e:
            logger.error(f"JWT auth error: {e}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)
    return decorated_function


@admin_social_bp.route('/posts', methods=['GET'])
@jwt_admin_required
def get_scheduled_posts():
    """
    Get scheduled posts for the next N days.

    Query params:
    - days: int (default 5) - number of days to look ahead
    - status: str (optional) - filter by status (scheduled, published, failed)
    """
    from app import db
    from models import SocialMediaPost

    days = request.args.get('days', 5, type=int)
    status_filter = request.args.get('status', None)

    try:
        # Get posts from today to N days ahead
        start_date = datetime.combine(date.today(), datetime.min.time())
        end_date = start_date + timedelta(days=days)

        query = SocialMediaPost.query.filter(
            SocialMediaPost.scheduled_time >= start_date,
            SocialMediaPost.scheduled_time < end_date
        )

        if status_filter:
            query = query.filter(SocialMediaPost.status == status_filter)

        posts = query.order_by(SocialMediaPost.scheduled_time.asc()).all()

        # Group posts by date
        posts_by_date = {}
        for post in posts:
            date_key = post.scheduled_time.strftime('%Y-%m-%d')
            if date_key not in posts_by_date:
                posts_by_date[date_key] = []
            posts_by_date[date_key].append(post.to_dict())

        # Build response with all dates (even empty ones)
        result = []
        for i in range(days):
            target_date = date.today() + timedelta(days=i)
            date_key = target_date.strftime('%Y-%m-%d')
            result.append({
                'date': date_key,
                'day_name': target_date.strftime('%A'),
                'posts': posts_by_date.get(date_key, [])
            })

        # Get stats
        total_scheduled = SocialMediaPost.query.filter_by(status='scheduled').count()
        total_published = SocialMediaPost.query.filter_by(status='published').count()
        total_failed = SocialMediaPost.query.filter_by(status='failed').count()

        return jsonify({
            'days': result,
            'stats': {
                'scheduled': total_scheduled,
                'published': total_published,
                'failed': total_failed
            }
        })

    except Exception as e:
        logger.error(f"Error getting scheduled posts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/posts/<int:post_id>', methods=['GET'])
@jwt_admin_required
def get_post_detail(post_id):
    """Get details of a single post."""
    from models import SocialMediaPost

    try:
        post = SocialMediaPost.query.get(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        return jsonify(post.to_dict())

    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@jwt_admin_required
def delete_post(post_id):
    """
    Delete/cancel a scheduled post.
    Only scheduled posts can be deleted.
    """
    from app import db
    from models import SocialMediaPost

    try:
        post = SocialMediaPost.query.get(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404

        if post.status == 'published':
            return jsonify({'error': 'Cannot delete published posts'}), 400

        # Mark as cancelled instead of hard delete (for audit trail)
        post.status = 'cancelled'
        db.session.commit()

        logger.info(f"Post {post_id} cancelled by admin")
        return jsonify({'status': 'success', 'message': 'Post cancelled'})

    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/posts/<int:post_id>/regenerate', methods=['POST'])
@jwt_admin_required
def regenerate_post(post_id):
    """
    Regenerate content for a scheduled post.
    Selects new products and generates new content.
    """
    try:
        from jobs.social_media_generator import regenerate_single_post

        success = regenerate_single_post(post_id)

        if success:
            from models import SocialMediaPost
            post = SocialMediaPost.query.get(post_id)
            return jsonify({
                'status': 'success',
                'message': 'Post regenerated',
                'post': post.to_dict() if post else None
            })
        else:
            return jsonify({'error': 'Failed to regenerate post'}), 400

    except Exception as e:
        logger.error(f"Error regenerating post {post_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/posts/<int:post_id>/publish', methods=['POST'])
@jwt_admin_required
def publish_post_now(post_id):
    """
    Manually publish a post immediately.
    """
    try:
        from jobs.social_media_publisher import publish_single_post

        result = publish_single_post(post_id, force=True)

        if result.get('status') == 'success':
            from models import SocialMediaPost
            post = SocialMediaPost.query.get(post_id)
            return jsonify({
                'status': 'success',
                'message': 'Post published',
                'facebook_post_id': result.get('post_id'),
                'post': post.to_dict() if post else None
            })
        else:
            return jsonify({
                'error': result.get('error') or result.get('message', 'Unknown error')
            }), 400

    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/generate', methods=['POST'])
@jwt_admin_required
def trigger_generation():
    """
    Manually trigger post generation for the next 5 days.
    """
    try:
        from jobs.social_media_generator import generate_scheduled_posts

        created, skipped = generate_scheduled_posts()

        return jsonify({
            'status': 'success',
            'message': f'Generated {created} posts, skipped {skipped} existing slots',
            'created': created,
            'skipped': skipped
        })

    except Exception as e:
        logger.error(f"Error generating posts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/config', methods=['GET'])
@jwt_admin_required
def get_config():
    """
    Get social media configuration status.
    """
    from facebook_service import get_facebook_service

    try:
        fb = get_facebook_service()
        page_info = fb.get_page_info()

        return jsonify({
            'facebook': {
                'enabled': fb.enabled,
                'page_id': fb.page_id,
                'page_info': page_info
            },
            'posting_times': ['09:00', '12:00', '15:00', '18:00'],
            'timezone': 'Europe/Sarajevo',
            'products_per_post': 5,
            'days_scheduled': 5
        })

    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_social_bp.route('/history', methods=['GET'])
@jwt_admin_required
def get_post_history():
    """
    Get history of published/failed posts.

    Query params:
    - page: int (default 1)
    - per_page: int (default 20)
    - status: str (optional) - published, failed
    """
    from models import SocialMediaPost

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', None)

    try:
        query = SocialMediaPost.query.filter(
            SocialMediaPost.status.in_(['published', 'failed'])
        )

        if status_filter:
            query = query.filter(SocialMediaPost.status == status_filter)

        query = query.order_by(SocialMediaPost.scheduled_time.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'posts': [post.to_dict() for post in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })

    except Exception as e:
        logger.error(f"Error getting post history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
