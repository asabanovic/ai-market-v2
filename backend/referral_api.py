"""
Referral System API
Handles referral codes and tracking
"""
from flask import Blueprint, request, jsonify
from auth_api import require_jwt_auth
from models import User
from credits_service_weekly import WeeklyCreditsService
from app import db
import logging
import re

logger = logging.getLogger(__name__)

# Create blueprint
referral_api_bp = Blueprint('referral_api', __name__, url_prefix='/api')

# Reserved codes that cannot be used as custom referral codes
RESERVED_CODES = {
    'admin', 'api', 'auth', 'login', 'register', 'registracija', 'prijava',
    'logout', 'profile', 'profil', 'user', 'korisnik', 'help', 'about',
    'contact', 'kontakt', 'home', 'proizvodi', 'products', 'kako-radimo',
    'code', 'r', 'ref', 'referral', 'referrali', 'krediti', 'credits',
    'moje-liste', 'favorites', 'omiljeni', 'rabat', 'settings', 'postavke'
}


@referral_api_bp.route('/user/referral-info', methods=['GET'])
@require_jwt_auth
def get_referral_info():
    """
    Get user's referral code and referral statistics

    Response:
        {
            "referral_code": "175ABC12",
            "total_referrals": 5,
            "total_credits_earned": 500,
            "referral_url": "https://rabat.ba/registracija?ref=175ABC12"
        }
    """
    try:
        user_id = request.current_user_id

        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get referrals (can be referred by either auto or custom code)
        referrals = WeeklyCreditsService.get_referrals(user.referral_code)
        total_referrals = len(referrals)
        total_credits_earned = sum(r['credits_awarded'] for r in referrals)

        # Build referral URL - use custom code if available
        base_url = "https://rabat.ba"  # Update when deployed
        display_code = user.custom_referral_code or user.referral_code

        # Use short /r/:code URL if custom code exists, otherwise use query param
        if user.custom_referral_code:
            referral_url = f"{base_url}/r/{user.custom_referral_code}"
        else:
            referral_url = f"{base_url}/registracija?ref={user.referral_code}"

        return jsonify({
            'referral_code': user.referral_code,  # Auto-generated code
            'custom_referral_code': user.custom_referral_code,  # Custom code (auto or user-set)
            'custom_code_changed': user.custom_code_changed,  # Has user customized it?
            'display_code': display_code,  # The one to show (custom or auto)
            'total_referrals': total_referrals,
            'total_credits_earned': total_credits_earned,
            'referral_url': referral_url
        }), 200

    except Exception as e:
        logger.error(f"Error getting referral info: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@referral_api_bp.route('/user/custom-referral-code', methods=['POST'])
@require_jwt_auth
def set_custom_referral_code():
    """
    Set a custom referral code for the user

    Request body:
        {
            "code": "adnan"
        }

    Response:
        {
            "success": true,
            "custom_code": "adnan",
            "referral_url": "https://rabat.ba/r/adnan"
        }
    """
    try:
        user_id = request.current_user_id
        data = request.get_json()

        if not data or 'code' not in data:
            return jsonify({'error': 'Kod je obavezan'}), 400

        custom_code = data['code'].strip().lower()

        # Validation: Length (3-20 characters)
        if len(custom_code) < 3 or len(custom_code) > 20:
            return jsonify({'error': 'Kod mora imati između 3 i 20 karaktera'}), 400

        # Validation: Only alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-z0-9_-]+$', custom_code):
            return jsonify({'error': 'Kod može sadržavati samo slova, brojeve, crtice i podvlake'}), 400

        # Validation: Reserved words
        if custom_code in RESERVED_CODES:
            return jsonify({'error': 'Ovaj kod je rezervisan i ne može se koristiti'}), 400

        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user has already customized their code
        if user.custom_code_changed:
            return jsonify({'error': 'Već ste jednom prilagodili svoj kod. Nije moguće ga ponovo mijenjati.'}), 400

        # Check if code is already taken
        existing = User.query.filter(
            (User.custom_referral_code == custom_code) | (User.referral_code == custom_code)
        ).first()

        if existing:
            return jsonify({'error': 'Ovaj kod je već zauzet'}), 400

        # Set custom code and mark as changed
        user.custom_referral_code = custom_code
        user.custom_code_changed = True
        db.session.commit()

        logger.info(f"User {user_id} customized referral code from auto-generated to: {custom_code}")

        base_url = "https://rabat.ba"
        referral_url = f"{base_url}/r/{custom_code}"

        return jsonify({
            'success': True,
            'custom_code': custom_code,
            'referral_url': referral_url
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting custom referral code: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@referral_api_bp.route('/user/referrals', methods=['GET'])
@require_jwt_auth
def get_user_referrals():
    """
    Get list of users referred by the current user

    Response:
        {
            "referrals": [
                {
                    "id": 1,
                    "referred_user_id": "phone_abc123",
                    "referred_user_email": "user@example.com",
                    "referred_user_phone": "+38761234567",
                    "credits_awarded": 100,
                    "created_at": "2025-11-23T10:30:00"
                }
            ],
            "total_count": 5
        }
    """
    try:
        user_id = request.current_user_id

        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get referrals
        referrals = WeeklyCreditsService.get_referrals(user.referral_code)

        return jsonify({
            'referrals': referrals,
            'total_count': len(referrals)
        }), 200

    except Exception as e:
        logger.error(f"Error getting user referrals: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@referral_api_bp.route('/auth/register-with-referral', methods=['POST'])
def register_with_referral():
    """
    Register a new user with a referral code
    This is used internally during registration when a referral code is provided

    Request body:
        {
            "user_id": "newly_created_user_id",
            "referral_code": "175ABC12"
        }

    Response:
        {
            "success": true,
            "credits_awarded": 100,
            "referrer_id": "referrer_user_id"
        }
    """
    try:
        data = request.get_json()

        if not data or 'user_id' not in data or 'referral_code' not in data:
            return jsonify({'error': 'user_id and referral_code are required'}), 400

        user_id = data['user_id']
        referral_code = data['referral_code'].strip().upper()

        # Award referral bonus
        result = WeeklyCreditsService.award_referral_bonus(referral_code, user_id)

        if result['success']:
            logger.info(f"Referral bonus awarded: {referral_code} referred {user_id}")
            return jsonify(result), 200
        else:
            logger.warning(f"Failed to award referral bonus: {result.get('error')}")
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error registering with referral: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@referral_api_bp.route('/validate-referral-code', methods=['POST'])
def validate_referral_code():
    """
    Validate a referral code before registration

    Request body:
        {
            "referral_code": "175ABC12"
        }

    Response:
        {
            "valid": true,
            "referrer_name": "John Doe",
            "bonus_credits": 100
        }
    """
    try:
        data = request.get_json()

        if not data or 'referral_code' not in data:
            return jsonify({'error': 'referral_code is required'}), 400

        referral_code = data['referral_code'].strip()

        # Find referrer - check both auto-generated and custom codes
        # Custom codes are lowercase, auto-generated are uppercase
        referrer = User.query.filter(
            (User.referral_code == referral_code.upper()) |
            (User.custom_referral_code == referral_code.lower())
        ).first()

        if not referrer:
            return jsonify({
                'valid': False,
                'error': 'Invalid referral code'
            }), 200

        # Get referrer name
        referrer_name = f"{referrer.first_name or ''} {referrer.last_name or ''}".strip()
        if not referrer_name:
            referrer_name = referrer.email or referrer.phone or "User"

        return jsonify({
            'valid': True,
            'referrer_name': referrer_name,
            'bonus_credits': 100  # From REFERRAL_BONUS_CREDITS constant
        }), 200

    except Exception as e:
        logger.error(f"Error validating referral code: {e}")
        return jsonify({'error': 'Internal server error'}), 500
