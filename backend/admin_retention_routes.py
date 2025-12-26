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

        # Get total returning users (for tab counts)
        today_count = User.query.filter(
            User.is_admin == False,
            User.last_activity_date == today,
            User.last_activity_date > func.date(User.created_at)
        ).count()

        week_ago = today - timedelta(days=7)
        week_count = User.query.filter(
            User.is_admin == False,
            User.last_activity_date >= week_ago,
            User.last_activity_date > func.date(User.created_at)
        ).count()

        month_ago = today - timedelta(days=30)
        month_count = User.query.filter(
            User.is_admin == False,
            User.last_activity_date >= month_ago,
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
                'returned_week': week_count,
                'returned_month': month_count,
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
            # Calculate Sunday of this week (i=0 = current week, i=1 = last week, etc.)
            days_since_sunday = (today.weekday() + 1) % 7
            week_start = today - timedelta(days=days_since_sunday + (i * 7))
            week_end = week_start + timedelta(days=6)

            # Cap at today for current week (partial week)
            if week_end > today:
                week_end = today

            # Users registered in this week
            registered = User.query.filter(
                User.is_admin == False,
                func.date(User.created_at) >= week_start,
                func.date(User.created_at) <= week_end
            ).count()

            # Users who returned this week (registered BEFORE this week, active this week)
            returned = User.query.filter(
                User.is_admin == False,
                func.date(User.created_at) < week_start,  # Must have registered before this week
                User.last_activity_date >= week_start,
                User.last_activity_date <= week_end
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
    Get email engagement statistics from our database (populated by SendGrid webhook).

    Query params:
    - days: int (default 30) - number of days to look back
    """
    from app import db
    from models import EmailEvent

    days = request.args.get('days', 30, type=int)

    try:
        today = date.today()
        start_date = today - timedelta(days=days)

        # Count events by type
        delivered_count = EmailEvent.query.filter(
            EmailEvent.event_type == 'delivered',
            func.date(EmailEvent.timestamp) >= start_date
        ).count()

        opened_count = EmailEvent.query.filter(
            EmailEvent.event_type == 'open',
            func.date(EmailEvent.timestamp) >= start_date
        ).count()

        clicked_count = EmailEvent.query.filter(
            EmailEvent.event_type == 'click',
            func.date(EmailEvent.timestamp) >= start_date
        ).count()

        bounced_count = EmailEvent.query.filter(
            EmailEvent.event_type.in_(['bounce', 'dropped']),
            func.date(EmailEvent.timestamp) >= start_date
        ).count()

        # Unique users who opened/clicked
        unique_openers = db.session.query(func.count(func.distinct(EmailEvent.email))).filter(
            EmailEvent.event_type == 'open',
            func.date(EmailEvent.timestamp) >= start_date
        ).scalar() or 0

        unique_clickers = db.session.query(func.count(func.distinct(EmailEvent.email))).filter(
            EmailEvent.event_type == 'click',
            func.date(EmailEvent.timestamp) >= start_date
        ).scalar() or 0

        # Calculate rates
        open_rate = round((opened_count / delivered_count * 100), 1) if delivered_count > 0 else 0
        click_rate = round((clicked_count / delivered_count * 100), 1) if delivered_count > 0 else 0

        # Daily breakdown for chart
        daily_events = db.session.query(
            func.date(EmailEvent.timestamp).label('date'),
            EmailEvent.event_type,
            func.count(EmailEvent.id).label('count')
        ).filter(
            func.date(EmailEvent.timestamp) >= start_date
        ).group_by(
            func.date(EmailEvent.timestamp),
            EmailEvent.event_type
        ).all()

        # Build daily data
        daily_data = {}
        for event in daily_events:
            date_str = str(event.date)
            if date_str not in daily_data:
                daily_data[date_str] = {'date': date_str, 'delivered': 0, 'opened': 0, 'clicked': 0}
            if event.event_type == 'delivered':
                daily_data[date_str]['delivered'] = event.count
            elif event.event_type == 'open':
                daily_data[date_str]['opened'] = event.count
            elif event.event_type == 'click':
                daily_data[date_str]['clicked'] = event.count

        # Sort by date
        daily_list = sorted(daily_data.values(), key=lambda x: x['date'])

        # Recent click URLs (what users are clicking on)
        recent_clicks = db.session.query(
            EmailEvent.url,
            func.count(EmailEvent.id).label('count')
        ).filter(
            EmailEvent.event_type == 'click',
            EmailEvent.url.isnot(None),
            func.date(EmailEvent.timestamp) >= start_date
        ).group_by(EmailEvent.url).order_by(func.count(EmailEvent.id).desc()).limit(10).all()

        top_urls = [{'url': r.url, 'clicks': r.count} for r in recent_clicks]

        return jsonify({
            'enabled': True,
            'webhook_url': 'https://popust.ba/api/webhooks/sendgrid',
            'stats': {
                'delivered': delivered_count,
                'opened': opened_count,
                'clicked': clicked_count,
                'bounced': bounced_count,
                'unique_openers': unique_openers,
                'unique_clickers': unique_clickers,
                'open_rate': open_rate,
                'click_rate': click_rate
            },
            'daily_activity': daily_list,
            'top_clicked_urls': top_urls,
            'period_days': days
        })

    except Exception as e:
        logger.error(f"Error getting email engagement: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/jobs', methods=['GET'])
@jwt_admin_required
def get_jobs_status():
    """Get status of all scheduled jobs from database."""
    from jobs.scheduler import get_job_status

    try:
        jobs_status = get_job_status()
        return jsonify({'jobs': jobs_status})
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/jobs/history', methods=['GET'])
@jwt_admin_required
def get_jobs_history():
    """Get job run history from database."""
    from jobs.scheduler import get_job_history

    job_name = request.args.get('job_name')
    limit = request.args.get('limit', 50, type=int)

    try:
        history = get_job_history(job_name, limit)
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Error getting job history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/emails', methods=['GET'])
@jwt_admin_required
def get_email_notifications():
    """Get email notification history."""
    from models import EmailNotification, User

    email_type = request.args.get('type')
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    try:
        query = EmailNotification.query

        if email_type:
            query = query.filter_by(email_type=email_type)
        if user_id:
            query = query.filter_by(user_id=user_id)

        # Get total count
        total = query.count()

        # Get paginated results
        emails = query.order_by(EmailNotification.sent_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        result = []
        for email in emails:
            user_name = None
            if email.user_id:
                user = User.query.get(email.user_id)
                user_name = user.display_name if user else None

            result.append({
                'id': email.id,
                'email': email.email,
                'email_type': email.email_type,
                'subject': email.subject,
                'status': email.status,
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'user_id': email.user_id,
                'user_name': user_name,
                'extra_data': email.extra_data,
                'error_message': email.error_message
            })

        return jsonify({
            'emails': result,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Error getting email notifications: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/emails/stats', methods=['GET'])
@jwt_admin_required
def get_email_stats():
    """Get email notification statistics."""
    from app import db
    from models import EmailNotification

    try:
        today = date.today()
        week_ago = today - timedelta(days=7)

        # Get counts by type for past week
        stats_query = db.session.query(
            EmailNotification.email_type,
            func.count(EmailNotification.id).label('count'),
            func.count().filter(EmailNotification.status == 'sent').label('sent_count'),
            func.count().filter(EmailNotification.status == 'failed').label('failed_count')
        ).filter(
            EmailNotification.sent_at >= week_ago
        ).group_by(EmailNotification.email_type).all()

        type_stats = []
        for stat in stats_query:
            type_stats.append({
                'email_type': stat.email_type,
                'total': stat.count,
                'sent': stat.sent_count,
                'failed': stat.failed_count
            })

        # Get daily counts for past week
        daily_query = db.session.query(
            func.date(EmailNotification.sent_at).label('day'),
            func.count(EmailNotification.id).label('count')
        ).filter(
            EmailNotification.sent_at >= week_ago
        ).group_by(func.date(EmailNotification.sent_at)).order_by(
            func.date(EmailNotification.sent_at)
        ).all()

        daily_stats = [{'date': str(d.day), 'count': d.count} for d in daily_query]

        return jsonify({
            'by_type': type_stats,
            'daily': daily_stats,
            'total_week': sum(s['total'] for s in type_stats)
        })

    except Exception as e:
        logger.error(f"Error getting email stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_retention_bp.route('/jobs/<job_name>/run', methods=['POST'])
@jwt_admin_required
def trigger_job(job_name):
    """Manually trigger a job by name."""
    import threading
    from jobs.scheduler import last_run
    from datetime import datetime

    def run_and_track(job_func, job_name):
        """Run job and update last_run tracking."""
        try:
            job_func()
            last_run[job_name] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Job {job_name} failed: {e}", exc_info=True)

    try:
        if job_name == 'product_scan':
            from jobs.scan_user_products import run_daily_scan
            thread = threading.Thread(target=run_and_track, args=(run_daily_scan, job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        elif job_name == 'email_summary':
            from jobs.send_scan_email_summaries import run_email_summaries
            thread = threading.Thread(target=run_and_track, args=(run_email_summaries, job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        elif job_name == 'monthly_credits':
            from credits_service_monthly import allocate_monthly_credits
            thread = threading.Thread(target=run_and_track, args=(allocate_monthly_credits, job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        elif job_name == 'coupon_reminders':
            from jobs.coupon_reminders import run_coupon_reminders
            thread = threading.Thread(target=run_and_track, args=(run_coupon_reminders, job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        elif job_name == 'weekly_summary':
            from jobs.weekly_summary import run_weekly_summaries
            # Force=True to bypass Sunday check for manual triggers
            thread = threading.Thread(target=lambda: run_and_track(lambda: run_weekly_summaries(force=True), job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        elif job_name == 'biweekly_reengagement':
            from jobs.monthly_reengagement import run_reengagement_emails
            thread = threading.Thread(target=run_and_track, args=(run_reengagement_emails, job_name))
            thread.start()
            return jsonify({'status': 'started', 'job': job_name})

        else:
            return jsonify({'error': f'Unknown job: {job_name}'}), 404

    except Exception as e:
        logger.error(f"Error triggering job {job_name}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
