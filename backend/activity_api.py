"""API endpoints for user activity tracking."""

import re
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app import db
from models import UserActivity, UserLogin, User
from auth_api import require_jwt_auth, decode_jwt_token


def parse_user_agent(user_agent):
    """Parse user agent string to extract device type, OS, and browser.

    Returns:
        dict with keys: device_type, os_name, browser_name
    """
    if not user_agent:
        return {'device_type': None, 'os_name': None, 'browser_name': None}

    ua = user_agent.lower()

    # Detect device type
    device_type = 'desktop'
    if 'mobile' in ua or 'android' in ua and 'mobile' not in ua:
        if 'tablet' in ua or 'ipad' in ua:
            device_type = 'tablet'
        elif any(x in ua for x in ['iphone', 'ipod', 'android', 'mobile', 'phone']):
            device_type = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'tablet'

    # Detect OS
    os_name = None
    if 'windows nt 10' in ua or 'windows nt 11' in ua:
        os_name = 'Windows'
    elif 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os x' in ua or 'macintosh' in ua:
        if 'iphone' in ua or 'ipad' in ua or 'ipod' in ua:
            os_name = 'iOS'
        else:
            os_name = 'macOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'linux' in ua:
        os_name = 'Linux'
    elif 'cros' in ua:
        os_name = 'ChromeOS'

    # Detect browser
    browser_name = None
    if 'edg/' in ua or 'edge/' in ua:
        browser_name = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser_name = 'Opera'
    elif 'chrome' in ua and 'chromium' not in ua:
        browser_name = 'Chrome'
    elif 'safari' in ua and 'chrome' not in ua:
        browser_name = 'Safari'
    elif 'firefox' in ua:
        browser_name = 'Firefox'
    elif 'msie' in ua or 'trident' in ua:
        browser_name = 'Internet Explorer'
    elif 'samsung' in ua:
        browser_name = 'Samsung Browser'

    return {
        'device_type': device_type,
        'os_name': os_name,
        'browser_name': browser_name
    }

# Create blueprint
activity_api_bp = Blueprint('activity_api', __name__, url_prefix='/api/activity')


def get_user_id_from_token():
    """Extract user ID from JWT token in Authorization header."""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if payload:
                return payload.get('user_id')
        except Exception as e:
            current_app.logger.warning(f"Failed to decode JWT token: {e}")
    return None


def get_client_ip():
    """Get client IP address from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


@activity_api_bp.route('/track', methods=['POST'])
def track_activity():
    """Track user activity.

    Request JSON:
        - activity_type (str): Type of activity ('page_view', 'filter', 'pagination', etc.)
        - page (str): Page name (e.g., 'proizvodi', 'favorites')
        - data (dict): Additional context data

    Returns:
        JSON response with success status.
    """
    try:
        user_id = get_user_id_from_token()

        # Only track logged-in users
        if not user_id:
            return jsonify({"success": True, "tracked": False, "reason": "anonymous"}), 200

        data = request.get_json() or {}
        activity_type = data.get('activity_type', 'unknown')
        page = data.get('page')
        activity_data = data.get('data', {})

        # Add IP to activity data
        activity_data['ip_address'] = get_client_ip()
        activity_data['user_agent'] = request.headers.get('User-Agent', '')[:500]

        # Create activity record
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            page=page,
            activity_data=activity_data
        )

        db.session.add(activity)
        db.session.commit()

        current_app.logger.info(f"Tracked activity: {activity_type} on {page} for user {user_id}")

        return jsonify({
            "success": True,
            "tracked": True,
            "activity_id": activity.id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to track activity: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@activity_api_bp.route('/batch', methods=['POST'])
def track_batch():
    """Track multiple activities in a single request.

    Request JSON:
        - activities (list): List of activity objects
            - activity_type (str)
            - page (str)
            - data (dict)
            - timestamp (str, optional): ISO timestamp for when activity occurred

    Returns:
        JSON response with count of tracked activities.
    """
    try:
        user_id = get_user_id_from_token()

        if not user_id:
            return jsonify({"success": True, "tracked": 0, "reason": "anonymous"}), 200

        data = request.get_json() or {}
        activities = data.get('activities', [])

        if not activities:
            return jsonify({"success": True, "tracked": 0}), 200

        ip_address = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')[:500]

        tracked_count = 0
        for activity_item in activities[:50]:  # Limit to 50 activities per batch
            activity_data = activity_item.get('data', {})
            activity_data['ip_address'] = ip_address
            activity_data['user_agent'] = user_agent

            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_item.get('activity_type', 'unknown'),
                page=activity_item.get('page'),
                activity_data=activity_data
            )
            db.session.add(activity)
            tracked_count += 1

        db.session.commit()
        current_app.logger.info(f"Batch tracked {tracked_count} activities for user {user_id}")

        return jsonify({
            "success": True,
            "tracked": tracked_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Failed to batch track activities: {e}")
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


def log_user_login(user_id, login_method='email', ip_address=None, user_agent=None):
    """Log a user login event. Call this from login endpoints.

    Args:
        user_id: The user's ID
        login_method: 'email', 'phone', 'google', etc.
        ip_address: Client IP address
        user_agent: Client user agent string
    """
    try:
        # Update user's last_login timestamp
        user = User.query.get(user_id)
        if user:
            user.last_login = datetime.now()

        # Parse user agent for device info
        device_info = parse_user_agent(user_agent)

        # Create login record
        login = UserLogin(
            user_id=user_id,
            login_method=login_method,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            device_type=device_info['device_type'],
            os_name=device_info['os_name'],
            browser_name=device_info['browser_name']
        )
        db.session.add(login)
        db.session.commit()

        current_app.logger.info(f"Logged login for user {user_id} via {login_method} on {device_info['device_type']}/{device_info['os_name']}")
        return True

    except Exception as e:
        current_app.logger.error(f"Failed to log login: {e}")
        db.session.rollback()
        return False
