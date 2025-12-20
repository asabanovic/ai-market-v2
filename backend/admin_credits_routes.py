"""
Admin API routes for managing user credits
Uses JWT authentication (not flask_login session)
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from datetime import datetime
from typing import List

admin_credits_bp = Blueprint('admin_credits', __name__, url_prefix='/api/admin/credits')

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


@admin_credits_bp.route('/award', methods=['POST'])
@jwt_admin_required
def award_bonus_credits():
    """
    Award bonus credits to one or more users with email notification.

    Body:
    - user_ids: List[str] - list of user IDs to award credits to
    - all_users: bool - award to all users (overrides user_ids)
    - amount: int - number of credits to award (required)
    - reason: str - short reason/title for the bonus (required)
    - message: str - optional custom message to include in email
    - send_email: bool - whether to send notification email (default: true)

    Returns:
    - success: bool
    - awarded_count: int - number of users who received credits
    - email_sent_count: int - number of emails sent
    """
    from app import db
    from models import User
    from credits_service_monthly import MonthlyCreditsService
    from sendgrid_utils import send_bonus_credits_email

    data = request.get_json()

    # Validate required fields
    amount = data.get('amount')
    reason = data.get('reason')

    if not amount or not isinstance(amount, int) or amount <= 0:
        return jsonify({'error': 'Valid amount is required (positive integer)'}), 400

    if not reason or not isinstance(reason, str) or len(reason.strip()) < 3:
        return jsonify({'error': 'Reason is required (at least 3 characters)'}), 400

    user_ids = data.get('user_ids', [])
    all_users = data.get('all_users', False)
    message = data.get('message', '')
    send_email_flag = data.get('send_email', True)

    try:
        # Get target users
        if all_users:
            users = User.query.filter(User.is_admin == False).all()
            logger.info(f"Awarding {amount} credits to ALL users ({len(users)} users)")
        elif user_ids:
            users = User.query.filter(User.id.in_(user_ids)).all()
            logger.info(f"Awarding {amount} credits to {len(users)} specific users")
        else:
            return jsonify({'error': 'Either user_ids or all_users must be provided'}), 400

        awarded_count = 0
        email_sent_count = 0
        errors = []

        for user in users:
            try:
                # Add credits as extra_credits (these never reset)
                MonthlyCreditsService.add_extra_credits(
                    user_id=user.id,
                    amount=amount,
                    action='ADMIN_BONUS',
                    metadata={
                        'reason': reason,
                        'message': message,
                        'awarded_by': request.jwt_user.email
                    }
                )
                awarded_count += 1

                # Send notification email
                if send_email_flag and user.email:
                    try:
                        email_sent = send_bonus_credits_email(
                            user_email=user.email,
                            user_name=user.first_name or user.phone,
                            credits_amount=amount,
                            reason=reason,
                            admin_message=message if message else None
                        )
                        if email_sent:
                            email_sent_count += 1
                    except Exception as email_error:
                        logger.warning(f"Failed to send email to {user.email}: {email_error}")

            except Exception as user_error:
                logger.error(f"Failed to award credits to user {user.id}: {user_error}")
                errors.append({'user_id': user.id, 'error': str(user_error)})

        admin_email = request.jwt_user.email
        logger.info(f"Admin {admin_email} awarded {amount} credits to {awarded_count} users. Reason: {reason}")

        return jsonify({
            'success': True,
            'awarded_count': awarded_count,
            'email_sent_count': email_sent_count,
            'amount': amount,
            'reason': reason,
            'errors': errors if errors else None
        })

    except Exception as e:
        logger.error(f"Error awarding bonus credits: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_credits_bp.route('/users', methods=['GET'])
@jwt_admin_required
def get_users_for_credits():
    """
    Get list of users with their credit balances for admin selection.

    Query params:
    - page: int (default 1)
    - per_page: int (default 50)
    - search: str - search by email, phone, or name

    Returns list of users with credit info
    """
    from models import User
    from credits_service_monthly import MonthlyCreditsService

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()

    try:
        query = User.query.filter(User.is_admin == False)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_pattern)) |
                (User.phone.ilike(search_pattern)) |
                (User.first_name.ilike(search_pattern)) |
                (User.last_name.ilike(search_pattern))
            )

        query = query.order_by(User.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users_data = []
        for user in pagination.items:
            balance = MonthlyCreditsService.get_balance(user.id, auto_reset_monthly=False)
            users_data.append({
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'regular_credits': balance['regular_credits'],
                'extra_credits': balance['extra_credits'],
                'total_credits': balance['total_credits']
            })

        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })

    except Exception as e:
        logger.error(f"Error getting users for credits: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_credits_bp.route('/history', methods=['GET'])
@jwt_admin_required
def get_credits_history():
    """
    Get history of admin credit awards.

    Query params:
    - page: int (default 1)
    - per_page: int (default 20)

    Returns list of credit award events
    """
    from app import db
    from sqlalchemy import text

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    try:
        # Query credit transactions for admin bonuses
        query = text("""
            SELECT
                ct.id,
                ct.user_id,
                u.email as user_email,
                ct.action,
                ct.credits_amount,
                ct.metadata,
                ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON ct.user_id = u.id
            WHERE ct.action = 'ADMIN_BONUS'
            ORDER BY ct.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        offset = (page - 1) * per_page
        result = db.session.execute(query, {'limit': per_page, 'offset': offset})
        transactions = [dict(row._mapping) for row in result]

        # Get total count
        count_query = text("SELECT COUNT(*) FROM credit_transactions WHERE action = 'ADMIN_BONUS'")
        total = db.session.execute(count_query).scalar()

        return jsonify({
            'transactions': transactions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Error getting credits history: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
