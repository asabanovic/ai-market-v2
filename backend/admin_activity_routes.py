"""
Admin API routes for user activity logs.
Uses JWT authentication (not flask_login session).
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import desc

admin_activity_bp = Blueprint('admin_activity', __name__, url_prefix='/api/admin/activity')

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


@admin_activity_bp.route('/logs', methods=['GET'])
@jwt_admin_required
def get_activity_logs():
    """
    Get user activity logs for admin audit.

    Query params:
    - filter: 'today' | 'week' | 'month' | 'all' (default: 'all')
    - activity_type: filter by type (e.g., 'profile_update')
    - user_id: filter by specific user
    - page: int (default 1)
    - per_page: int (default 50)

    Returns list of activity logs with user info.
    """
    from app import db
    from models import UserActivityLog

    filter_type = request.args.get('filter', 'all')
    activity_type = request.args.get('activity_type')
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        today = date.today()

        # Base query
        query = UserActivityLog.query

        # Date filter
        if filter_type == 'today':
            query = query.filter(
                db.func.date(UserActivityLog.created_at) == today
            )
        elif filter_type == 'week':
            week_ago = today - timedelta(days=7)
            query = query.filter(
                db.func.date(UserActivityLog.created_at) >= week_ago
            )
        elif filter_type == 'month':
            month_ago = today - timedelta(days=30)
            query = query.filter(
                db.func.date(UserActivityLog.created_at) >= month_ago
            )

        # Activity type filter
        if activity_type:
            query = query.filter(UserActivityLog.activity_type == activity_type)

        # User filter
        if user_id:
            query = query.filter(UserActivityLog.user_id == user_id)

        # Get total count
        total = query.count()

        # Order by most recent and paginate
        logs = query.order_by(desc(UserActivityLog.created_at)).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return jsonify({
            'logs': [log.to_dict() for log in logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })

    except Exception as e:
        logger.error(f"Error fetching activity logs: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch activity logs'}), 500


@admin_activity_bp.route('/stats', methods=['GET'])
@jwt_admin_required
def get_activity_stats():
    """
    Get activity statistics.

    Returns:
    - Total logs count
    - Logs by activity type
    - Recent activity count (last 24h, 7d, 30d)
    """
    from app import db
    from models import UserActivityLog

    try:
        today = date.today()
        now = datetime.now()

        # Total count
        total = UserActivityLog.query.count()

        # Count by activity type
        type_counts = db.session.query(
            UserActivityLog.activity_type,
            db.func.count(UserActivityLog.id)
        ).group_by(UserActivityLog.activity_type).all()

        # Recent counts
        last_24h = UserActivityLog.query.filter(
            UserActivityLog.created_at >= now - timedelta(hours=24)
        ).count()

        last_7d = UserActivityLog.query.filter(
            UserActivityLog.created_at >= now - timedelta(days=7)
        ).count()

        last_30d = UserActivityLog.query.filter(
            UserActivityLog.created_at >= now - timedelta(days=30)
        ).count()

        return jsonify({
            'total': total,
            'by_type': {t: c for t, c in type_counts},
            'last_24h': last_24h,
            'last_7d': last_7d,
            'last_30d': last_30d
        })

    except Exception as e:
        logger.error(f"Error fetching activity stats: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch stats'}), 500
