"""
Admin API routes for camera button analytics.
Track user interactions with the floating camera button feature.
"""

from flask import Blueprint, jsonify, request
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, distinct, desc
import logging

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/api')
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


def get_optional_user():
    """Try to get user from JWT token, return None if not authenticated"""
    from auth_api import decode_jwt_token

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if payload:
            return payload.get('user_id')
    except:
        pass
    return None


# ============================================================
# PUBLIC TRACKING ENDPOINT
# ============================================================

@admin_analytics_bp.route('/track/camera-button', methods=['POST'])
def track_camera_button():
    """
    Track camera button interactions.
    Can be called by anyone (logged in or anonymous).

    Body:
    {
        "action": "button_click" | "expand" | "camera_click" | "gallery_click" | "upload_start" | "upload_complete" | "upload_cancel",
        "session_id": "optional-session-id",
        "page_url": "optional-current-url",
        "uploaded_image_id": optional-int (for upload_complete)
    }
    """
    from app import db
    from models import CameraButtonAnalytics

    try:
        data = request.get_json() or {}
        action = data.get('action')

        if not action:
            return jsonify({'error': 'action is required'}), 400

        valid_actions = ['button_click', 'expand', 'camera_click', 'gallery_click',
                        'upload_start', 'upload_complete', 'upload_cancel',
                        'add_product_click', 'receipt_click', 'receipt_camera_click',
                        'receipt_gallery_click', 'receipt_upload_start', 'receipt_upload_complete']
        if action not in valid_actions:
            return jsonify({'error': f'Invalid action. Must be one of: {valid_actions}'}), 400

        user_id = get_optional_user()

        analytics = CameraButtonAnalytics(
            user_id=user_id,
            session_id=data.get('session_id'),
            action=action,
            page_url=data.get('page_url'),
            user_agent=request.headers.get('User-Agent'),
            uploaded_image_id=data.get('uploaded_image_id')
        )

        db.session.add(analytics)
        db.session.commit()

        return jsonify({'success': True, 'id': analytics.id}), 201

    except Exception as e:
        logger.error(f"Error tracking camera button: {e}", exc_info=True)
        return jsonify({'error': 'Failed to track interaction'}), 500


# ============================================================
# ADMIN DASHBOARD ENDPOINTS
# ============================================================

# ============================================================
# PWA INSTALL TRACKING
# ============================================================

@admin_analytics_bp.route('/track/pwa-install', methods=['POST'])
def track_pwa_install():
    """
    Track PWA install events.
    Can be called by anyone (logged in or anonymous).

    Body:
    {
        "event": "prompt_shown" | "prompt_accepted" | "prompt_dismissed" | "installed" | "standalone_launch",
        "session_id": "optional-session-id",
        "page_url": "optional-current-url",
        "platform": "android" | "ios" | "desktop",
        "browser": "optional-browser-name"
    }
    """
    from app import db
    from models import PwaInstallAnalytics, User

    try:
        data = request.get_json() or {}
        event = data.get('event')

        if not event:
            return jsonify({'error': 'event is required'}), 400

        valid_events = ['prompt_shown', 'prompt_accepted', 'prompt_dismissed', 'installed', 'standalone_launch']
        if event not in valid_events:
            return jsonify({'error': f'Invalid event. Must be one of: {valid_events}'}), 400

        user_id = get_optional_user()

        analytics = PwaInstallAnalytics(
            user_id=user_id,
            session_id=data.get('session_id'),
            event=event,
            page_url=data.get('page_url'),
            user_agent=request.headers.get('User-Agent'),
            platform=data.get('platform'),
            browser=data.get('browser')
        )

        db.session.add(analytics)

        # Update user's PWA status when they launch from standalone mode
        if user_id and event == 'standalone_launch':
            user = User.query.get(user_id)
            if user:
                user.is_pwa_user = True
                user.last_pwa_access = datetime.now()
                user.pwa_access_count = (user.pwa_access_count or 0) + 1
                logger.info(f"Updated PWA status for user {user_id}, access count: {user.pwa_access_count}")

        db.session.commit()

        return jsonify({'success': True, 'id': analytics.id}), 201

    except Exception as e:
        logger.error(f"Error tracking PWA install: {e}", exc_info=True)
        return jsonify({'error': 'Failed to track event'}), 500


@admin_analytics_bp.route('/admin/analytics/pwa-install', methods=['GET'])
@jwt_admin_required
def get_pwa_install_analytics():
    """
    Get PWA install analytics for admin dashboard.

    Query params:
    - days: Number of days to look back (default: 30)
    """
    from app import db
    from models import PwaInstallAnalytics, User

    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get event statistics
        event_stats = db.session.query(
            PwaInstallAnalytics.event,
            func.count(PwaInstallAnalytics.id).label('count'),
            func.count(distinct(PwaInstallAnalytics.user_id)).label('unique_users'),
            func.count(distinct(PwaInstallAnalytics.session_id)).label('unique_sessions')
        ).filter(
            PwaInstallAnalytics.created_at >= cutoff_date
        ).group_by(
            PwaInstallAnalytics.event
        ).all()

        events = {}
        for event, count, unique_users, unique_sessions in event_stats:
            events[event] = {
                'total': count,
                'unique_users': unique_users or 0,
                'unique_sessions': unique_sessions or 0
            }

        # Get platform breakdown
        platform_stats = db.session.query(
            PwaInstallAnalytics.platform,
            PwaInstallAnalytics.event,
            func.count(PwaInstallAnalytics.id).label('count')
        ).filter(
            PwaInstallAnalytics.created_at >= cutoff_date,
            PwaInstallAnalytics.platform.isnot(None)
        ).group_by(
            PwaInstallAnalytics.platform,
            PwaInstallAnalytics.event
        ).all()

        platforms = {}
        for platform, event, count in platform_stats:
            if platform not in platforms:
                platforms[platform] = {}
            platforms[platform][event] = count

        # Get users who installed - with potential duplicates
        installed_users_raw = db.session.query(
            PwaInstallAnalytics.user_id,
            PwaInstallAnalytics.session_id,
            User.email,
            User.first_name,
            User.last_name,
            PwaInstallAnalytics.platform,
            PwaInstallAnalytics.browser,
            PwaInstallAnalytics.created_at
        ).outerjoin(
            User, PwaInstallAnalytics.user_id == User.id
        ).filter(
            PwaInstallAnalytics.created_at >= cutoff_date,
            PwaInstallAnalytics.event == 'installed'
        ).order_by(
            desc(PwaInstallAnalytics.created_at)
        ).all()

        # Deduplicate: for logged-in users by user_id, for anonymous by session_id
        # Keep the first (most recent) install per user
        seen_users = set()
        seen_sessions = set()
        users_installed = []

        for row in installed_users_raw:
            # Skip if we've already seen this user
            if row.user_id:
                if row.user_id in seen_users:
                    continue
                seen_users.add(row.user_id)
            elif row.session_id:
                if row.session_id in seen_sessions:
                    continue
                seen_sessions.add(row.session_id)
            else:
                # No user_id or session_id - skip to avoid duplicates
                continue

            users_installed.append({
                'user_id': row.user_id,
                'email': row.email,
                'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or row.email or 'Anonymous',
                'platform': row.platform,
                'browser': row.browser,
                'installed_at': row.created_at.isoformat() if row.created_at else None
            })

            if len(users_installed) >= 100:
                break

        # Daily trend
        daily_trend = db.session.query(
            func.date(PwaInstallAnalytics.created_at).label('date'),
            PwaInstallAnalytics.event,
            func.count(PwaInstallAnalytics.id).label('count')
        ).filter(
            PwaInstallAnalytics.created_at >= cutoff_date
        ).group_by(
            func.date(PwaInstallAnalytics.created_at),
            PwaInstallAnalytics.event
        ).order_by(
            func.date(PwaInstallAnalytics.created_at)
        ).all()

        # Group by date
        trend_by_date = {}
        for d in daily_trend:
            date_str = str(d.date)
            if date_str not in trend_by_date:
                trend_by_date[date_str] = {}
            trend_by_date[date_str][d.event] = d.count

        # Calculate conversion rates
        prompt_shown = events.get('prompt_shown', {}).get('total', 0)
        prompt_accepted = events.get('prompt_accepted', {}).get('total', 0)
        installed = events.get('installed', {}).get('total', 0)

        conversion = {
            'prompt_to_accept': round((prompt_accepted / prompt_shown * 100), 1) if prompt_shown > 0 else 0,
            'accept_to_install': round((installed / prompt_accepted * 100), 1) if prompt_accepted > 0 else 0,
            'overall': round((installed / prompt_shown * 100), 1) if prompt_shown > 0 else 0
        }

        return jsonify({
            'events': events,
            'platforms': platforms,
            'users_installed': users_installed,
            'daily_trend': [
                {'date': date, 'events': evts}
                for date, evts in sorted(trend_by_date.items())
            ],
            'conversion': conversion,
            'summary': {
                'total_installs': installed,
                'total_prompts': prompt_shown,
                'days_analyzed': days
            }
        })

    except Exception as e:
        logger.error(f"Error getting PWA analytics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get analytics'}), 500


@admin_analytics_bp.route('/admin/analytics/camera-button', methods=['GET'])
@jwt_admin_required
def get_camera_button_analytics():
    """
    Get camera button analytics for admin dashboard.

    Query params:
    - days: Number of days to look back (default: 30)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    """
    from app import db
    from models import CameraButtonAnalytics, User, UserProductImage, SearchLog

    try:
        days = request.args.get('days', 30, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get funnel statistics
        funnel_stats = db.session.query(
            CameraButtonAnalytics.action,
            func.count(CameraButtonAnalytics.id).label('count'),
            func.count(distinct(CameraButtonAnalytics.user_id)).label('unique_users'),
            func.count(distinct(CameraButtonAnalytics.session_id)).label('unique_sessions')
        ).filter(
            CameraButtonAnalytics.created_at >= cutoff_date
        ).group_by(
            CameraButtonAnalytics.action
        ).all()

        funnel = {}
        for action, count, unique_users, unique_sessions in funnel_stats:
            funnel[action] = {
                'total': count,
                'unique_users': unique_users or 0,
                'unique_sessions': unique_sessions or 0
            }

        # Get unique users who interacted
        user_interactions = db.session.query(
            CameraButtonAnalytics.user_id,
            User.email,
            User.first_name,
            User.last_name,
            func.count(CameraButtonAnalytics.id).label('interaction_count'),
            func.min(CameraButtonAnalytics.created_at).label('first_interaction'),
            func.max(CameraButtonAnalytics.created_at).label('last_interaction'),
            func.array_agg(distinct(CameraButtonAnalytics.action)).label('actions')
        ).outerjoin(
            User, CameraButtonAnalytics.user_id == User.id
        ).filter(
            CameraButtonAnalytics.created_at >= cutoff_date,
            CameraButtonAnalytics.user_id.isnot(None)
        ).group_by(
            CameraButtonAnalytics.user_id,
            User.email,
            User.first_name,
            User.last_name
        ).order_by(
            desc('last_interaction')
        ).paginate(page=page, per_page=per_page, error_out=False)

        # For each user, get their uploaded images if they completed upload
        users_data = []
        for row in user_interactions.items:
            user_data = {
                'user_id': row.user_id,
                'email': row.email,
                'name': f"{row.first_name or ''} {row.last_name or ''}".strip() or row.email,
                'interaction_count': row.interaction_count,
                'first_interaction': row.first_interaction.isoformat() if row.first_interaction else None,
                'last_interaction': row.last_interaction.isoformat() if row.last_interaction else None,
                'actions': row.actions or [],
                'completed_upload': 'upload_complete' in (row.actions or []),
                'uploaded_images': []
            }

            # Get uploaded images from UserProductImage (original source)
            images = UserProductImage.query.filter_by(
                user_id=row.user_id
            ).order_by(
                UserProductImage.created_at.desc()
            ).limit(10).all()

            user_data['uploaded_images'] = [img.to_dict() for img in images]

            # Also get camera search images from SearchLog (new source)
            # Note: Use db.session.query() because SearchLog has a 'query' column that shadows .query
            # Check for both search_type='camera' AND image_path (for new entries)
            # OR entries with image_path that might not have search_type set yet
            camera_searches = db.session.query(SearchLog).filter(
                SearchLog.user_id == row.user_id,
                SearchLog.image_path.isnot(None)
            ).order_by(
                SearchLog.created_at.desc()
            ).limit(10).all()

            # Add camera searches to uploaded_images
            for s in camera_searches:
                user_data['uploaded_images'].append({
                    'id': f'search_{s.id}',
                    'image_url': s.image_path,
                    'thumbnail_url': s.image_path,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    'extracted_name': s.vision_result.get('title') if s.vision_result else s.query,
                    'extracted_price': None,
                    'status': f"{s.result_count} rezultata",
                    'vision_result': s.vision_result,
                    'source': 'camera_search'
                })

            # Mark as completed if they have any images
            if user_data['uploaded_images']:
                user_data['completed_upload'] = True

            users_data.append(user_data)

        # Count logged-in users before adding anonymous sessions
        logged_in_user_count = len(users_data)

        # Get anonymous sessions with their actions
        anon_session_data = db.session.query(
            CameraButtonAnalytics.session_id,
            func.count(CameraButtonAnalytics.id).label('interaction_count'),
            func.min(CameraButtonAnalytics.created_at).label('first_interaction'),
            func.max(CameraButtonAnalytics.created_at).label('last_interaction'),
            func.array_agg(distinct(CameraButtonAnalytics.action)).label('actions')
        ).filter(
            CameraButtonAnalytics.created_at >= cutoff_date,
            CameraButtonAnalytics.user_id.is_(None),
            CameraButtonAnalytics.session_id.isnot(None)
        ).group_by(
            CameraButtonAnalytics.session_id
        ).order_by(
            desc('last_interaction')
        ).all()

        # Add anonymous sessions to users_data
        for row in anon_session_data:
            users_data.append({
                'user_id': None,
                'email': None,
                'name': f"Anonimna sesija ({row.session_id[:8]}...)",
                'session_id': row.session_id,
                'interaction_count': row.interaction_count,
                'first_interaction': row.first_interaction.isoformat() if row.first_interaction else None,
                'last_interaction': row.last_interaction.isoformat() if row.last_interaction else None,
                'actions': row.actions or [],
                'completed_upload': 'upload_complete' in (row.actions or []),
                'uploaded_images': [],
                'is_anonymous': True
            })

        # Sort all users by last interaction
        users_data.sort(key=lambda x: x['last_interaction'] or '', reverse=True)

        anon_sessions = len(anon_session_data)

        # Daily trend
        daily_trend = db.session.query(
            func.date(CameraButtonAnalytics.created_at).label('date'),
            func.count(CameraButtonAnalytics.id).label('interactions'),
            func.count(distinct(CameraButtonAnalytics.user_id)).label('unique_users')
        ).filter(
            CameraButtonAnalytics.created_at >= cutoff_date
        ).group_by(
            func.date(CameraButtonAnalytics.created_at)
        ).order_by(
            func.date(CameraButtonAnalytics.created_at)
        ).all()

        return jsonify({
            'funnel': funnel,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': user_interactions.total,
                'pages': user_interactions.pages
            },
            'summary': {
                'total_interactions': sum(f['total'] for f in funnel.values()),
                'unique_logged_in_users': logged_in_user_count,
                'anonymous_sessions': anon_sessions,
                'days_analyzed': days
            },
            'daily_trend': [
                {
                    'date': str(d.date),
                    'interactions': d.interactions,
                    'unique_users': d.unique_users or 0
                }
                for d in daily_trend
            ]
        })

    except Exception as e:
        logger.error(f"Error getting camera analytics: {e}", exc_info=True)
        return jsonify({'error': 'Failed to get analytics'}), 500
