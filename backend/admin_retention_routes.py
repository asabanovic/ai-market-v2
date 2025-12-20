"""
Admin API routes for user retention/return activity tracking.
Uses JWT authentication (not flask_login session).
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import text, func, and_, or_

admin_retention_bp = Blueprint('admin_retention', __name__, url_prefix='/api/admin/retention')

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


@admin_retention_bp.route('/returning-users', methods=['GET'])
@jwt_admin_required
def get_returning_users():
    """
    Get users who have returned (logged in after registration).
    Ordered by last activity date (most recent first).

    Query params:
    - filter: 'today' | 'week' | 'month' | 'all' (default: 'all')
    - page: int (default 1)
    - per_page: int (default 50)

    Returns users with:
    - registration date
    - last activity date
    - return count (unique days active)
    - streak info
    - email click tracking (if available)
    """
    from app import db
    from models import User, UserSearch

    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        today = date.today()

        # Build date filter based on filter_type
        date_filter = None
        if filter_type == 'today':
            date_filter = User.last_activity_date == today
        elif filter_type == 'week':
            week_ago = today - timedelta(days=7)
            date_filter = User.last_activity_date >= week_ago
        elif filter_type == 'month':
            month_ago = today - timedelta(days=30)
            date_filter = User.last_activity_date >= month_ago

        # Query users who have returned (last_activity_date different from created_at date)
        # A "return" means they came back after their first day
        query = User.query.filter(
            User.is_admin == False,
            User.last_activity_date.isnot(None),
            # User came back if last_activity != registration date
            User.last_activity_date > func.date(User.created_at)
        )

        if date_filter is not None:
            query = query.filter(date_filter)

        # Order by last activity (most recent first)
        query = query.order_by(User.last_activity_date.desc(), User.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Get total returning users (for "today" highlight)
        today_count = User.query.filter(
            User.is_admin == False,
            User.last_activity_date == today,
            User.last_activity_date > func.date(User.created_at)
        ).count()

        # Format response
        users_data = []
        for user in pagination.items:
            # Calculate days since registration
            reg_date = user.created_at.date() if user.created_at else None
            days_since_reg = (today - reg_date).days if reg_date else 0

            # Calculate days between registration and first return
            first_return_gap = None
            if user.last_activity_date and reg_date:
                # First return is first day after registration
                first_return_gap = (user.last_activity_date - reg_date).days

            # Count unique active days (from searches)
            active_days_count = db.session.query(
                func.count(func.distinct(func.date(UserSearch.created_at)))
            ).filter(UserSearch.user_id == user.id).scalar() or 0

            users_data.append({
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
                'city': user.city,
                'registered_at': user.created_at.isoformat() if user.created_at else None,
                'last_activity_date': user.last_activity_date.isoformat() if user.last_activity_date else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'days_since_registration': days_since_reg,
                'first_return_gap_days': first_return_gap,
                'unique_active_days': active_days_count,
                'current_streak': user.current_streak or 0,
                'longest_streak': user.longest_streak or 0,
                'is_active_today': user.last_activity_date == today,
                'registration_method': user.registration_method or 'email',
                'is_verified': user.is_verified
            })

        # Calculate summary stats
        total_users = User.query.filter(User.is_admin == False).count()
        total_with_activity = User.query.filter(
            User.is_admin == False,
            User.last_activity_date.isnot(None)
        ).count()
        total_returned = User.query.filter(
            User.is_admin == False,
            User.last_activity_date.isnot(None),
            User.last_activity_date > func.date(User.created_at)
        ).count()

        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            },
            'stats': {
                'total_users': total_users,
                'total_with_activity': total_with_activity,
                'total_returned': total_returned,
                'returned_today': today_count,
                'return_rate': round((total_returned / total_users * 100), 1) if total_users > 0 else 0
            }
        })

    except Exception as e:
        logger.error(f"Error getting returning users: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/daily-activity', methods=['GET'])
@jwt_admin_required
def get_daily_activity():
    """
    Get daily return/activity breakdown for the last N days.
    Shows how many users returned each day.

    Query params:
    - days: int (default 30)

    Returns daily breakdown with new users vs returning users.
    """
    from app import db
    from models import User

    days = request.args.get('days', 30, type=int)

    try:
        today = date.today()
        start_date = today - timedelta(days=days)

        # Get daily registrations
        registrations_query = db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.is_admin == False,
            func.date(User.created_at) >= start_date
        ).group_by(func.date(User.created_at)).all()

        registrations_by_date = {str(r.date): r.count for r in registrations_query}

        # Get daily returns (users active on a day who registered before that day)
        returns_query = db.session.query(
            User.last_activity_date.label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.is_admin == False,
            User.last_activity_date >= start_date,
            User.last_activity_date > func.date(User.created_at)
        ).group_by(User.last_activity_date).all()

        returns_by_date = {str(r.date): r.count for r in returns_query}

        # Build daily breakdown
        daily_data = []
        for i in range(days + 1):
            d = start_date + timedelta(days=i)
            date_str = str(d)
            daily_data.append({
                'date': date_str,
                'new_users': registrations_by_date.get(date_str, 0),
                'returning_users': returns_by_date.get(date_str, 0)
            })

        return jsonify({
            'daily_activity': daily_data,
            'summary': {
                'total_new': sum(d['new_users'] for d in daily_data),
                'total_returning': sum(d['returning_users'] for d in daily_data)
            }
        })

    except Exception as e:
        logger.error(f"Error getting daily activity: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/cohort', methods=['GET'])
@jwt_admin_required
def get_cohort_analysis():
    """
    Get cohort analysis - for each registration week, how many returned.

    Query params:
    - weeks: int (default 8)

    Returns cohort data showing retention by registration week.
    """
    from app import db
    from models import User

    weeks = request.args.get('weeks', 8, type=int)

    try:
        today = date.today()

        cohorts = []
        for i in range(weeks):
            # Week start (Sunday) and end (Saturday)
            week_end = today - timedelta(days=today.weekday() + 1 + (i * 7))
            week_start = week_end - timedelta(days=6)

            # Users registered in this week
            registered = User.query.filter(
                User.is_admin == False,
                func.date(User.created_at) >= week_start,
                func.date(User.created_at) <= week_end
            ).count()

            # Of those, how many returned (have activity after registration date)
            returned = User.query.filter(
                User.is_admin == False,
                func.date(User.created_at) >= week_start,
                func.date(User.created_at) <= week_end,
                User.last_activity_date > func.date(User.created_at)
            ).count()

            cohorts.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'week_label': f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}",
                'registered': registered,
                'returned': returned,
                'return_rate': round((returned / registered * 100), 1) if registered > 0 else 0
            })

        # Reverse to show oldest first
        cohorts.reverse()

        return jsonify({'cohorts': cohorts})

    except Exception as e:
        logger.error(f"Error getting cohort analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/email-engagement', methods=['GET'])
@jwt_admin_required
def get_email_engagement():
    """
    Get email engagement statistics from SendGrid.

    Note: This requires SendGrid's Event Webhook to be set up to POST events
    to our API, or we need to query SendGrid's Stats API.

    For now, returns placeholder structure that can be populated once
    SendGrid webhook is configured.
    """
    import os
    from datetime import datetime, timedelta

    # Check if SendGrid API key is configured
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")

    if not sendgrid_api_key:
        return jsonify({
            'enabled': False,
            'message': 'SendGrid API key not configured',
            'stats': None
        })

    # TODO: Implement actual SendGrid stats API call
    # For now, return structure showing what data will be available

    try:
        # This would call SendGrid Stats API:
        # GET https://api.sendgrid.com/v3/stats?start_date=2024-01-01

        # Placeholder structure
        return jsonify({
            'enabled': True,
            'message': 'SendGrid integration ready - webhook setup required for click tracking',
            'setup_instructions': {
                'webhook_url': '/api/webhooks/sendgrid',
                'events_to_track': ['click', 'open', 'delivered'],
                'docs': 'https://docs.sendgrid.com/for-developers/tracking-events/event-webhook'
            },
            'stats': {
                'emails_sent': 0,
                'delivered': 0,
                'opened': 0,
                'clicked': 0,
                'click_rate': 0,
                'open_rate': 0
            }
        })

    except Exception as e:
        logger.error(f"Error getting email engagement: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
