"""
Phone Authentication API
Handles WhatsApp/SMS OTP authentication flow via Infobip
"""
import secrets
import logging
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from models import User, OTPCode
from infobip_service import send_otp_with_fallback
from auth_api import generate_jwt_token
from credits_service_weekly import WeeklyCreditsService

logger = logging.getLogger(__name__)

phone_auth_bp = Blueprint('phone_auth', __name__, url_prefix='/api/auth')


def generate_otp() -> str:
    """Generate 6-digit OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def get_client_ip():
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to E.164 format
    Accepts: +387 6X XXX XXX, 06X XXX XXX, 3876XXXXXXX, etc.
    Returns: +3876XXXXXXX
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # If starts with 387, add +
    if digits.startswith('387'):
        return f'+{digits}'

    # If starts with 0, replace with +387
    if digits.startswith('0'):
        return f'+387{digits[1:]}'

    # If no prefix, assume BA and add +387
    if len(digits) == 8 or len(digits) == 9:
        return f'+387{digits}'

    # Already has +
    if phone.startswith('+'):
        return f'+{digits}'

    return f'+{digits}'


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Validate phone number for Bosnia and Herzegovina
    Returns: (is_valid, error_message)
    """
    try:
        normalized = normalize_phone(phone)

        # Check if it's BA number (+387)
        if not normalized.startswith('+387'):
            return False, 'Podržani su samo brojevi telefona za Bosnu i Hercegovinu (+387)'

        # Check length (should be +387 + 8-9 digits)
        if len(normalized) < 12 or len(normalized) > 13:
            return False, 'Nevažeći format broja telefona'

        return True, ''
    except Exception as e:
        logger.error(f"Phone validation error: {e}")
        return False, 'Nevažeći format broja telefona'


@phone_auth_bp.route('/phone/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP code to phone number via WhatsApp or SMS

    Request body:
        {
            "phone": "+387 6X XXX XXX",
            "whatsapp_available": true  # Optional, defaults to true
        }

    Response:
        {
            "success": true,
            "message": "Kod poslan preko WhatsApp/SMS",
            "channel": "whatsapp" or "sms",
            "fallback_used": false,
            "expires_in": 300,
            "dev_mode": false  # Only in dev mode
        }
    """
    data = request.get_json()
    phone = data.get('phone', '').strip()
    whatsapp_available = data.get('whatsapp_available', True)  # Default to WhatsApp

    if not phone:
        return jsonify({'success': False, 'error': 'Broj telefona je obavezan'}), 400

    # Validate phone number
    is_valid, error_msg = validate_phone(phone)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # Normalize phone
    normalized_phone = normalize_phone(phone)

    # Rate limiting: Max 3 OTP requests per phone per hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_otps = OTPCode.query.filter(
        OTPCode.phone == normalized_phone,
        OTPCode.created_at >= one_hour_ago
    ).count()

    if recent_otps >= 3:
        return jsonify({
            'success': False,
            'error': 'Previše zahtjeva. Pokušajte ponovo za 1 sat.'
        }), 429

    # Check if there's a valid OTP that hasn't expired (resend protection)
    existing_otp = OTPCode.query.filter(
        OTPCode.phone == normalized_phone,
        OTPCode.expires_at > datetime.now(),
        OTPCode.is_used == False
    ).order_by(OTPCode.created_at.desc()).first()

    if existing_otp:
        # If OTP was created less than 60 seconds ago, don't send new one
        if (datetime.now() - existing_otp.created_at).total_seconds() < 60:
            return jsonify({
                'success': False,
                'error': 'Kod je već poslan. Pokušajte ponovo za 60 sekundi.'
            }), 429

    # Generate new OTP
    otp_code = generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)

    # Save OTP to database
    otp = OTPCode(
        phone=normalized_phone,
        code=otp_code,
        expires_at=expires_at
    )
    db.session.add(otp)
    db.session.commit()

    # Send OTP via WhatsApp (with SMS fallback) or SMS only
    result = send_otp_with_fallback(normalized_phone, otp_code, prefer_whatsapp=whatsapp_available)

    if result['success']:
        channel = result.get('channel', 'unknown')
        fallback_used = result.get('fallback_used', False)

        logger.info(f"OTP sent to {normalized_phone} via {channel} (fallback: {fallback_used})")

        # Build response message
        if channel == 'whatsapp':
            message = 'Kod poslan na WhatsApp ✓'
        elif channel == 'sms':
            if fallback_used:
                message = 'Kod poslan kao SMS (WhatsApp nedostupan)'
            else:
                message = 'Kod poslan kao SMS ✓'
        else:
            message = 'Kod poslan ✓'

        response = {
            'success': True,
            'message': message,
            'channel': channel,
            'fallback_used': fallback_used,
            'expires_in': 300  # 5 minutes in seconds
        }

        # In dev mode, return the code for testing
        if result.get('dev_mode'):
            response['dev_mode'] = True
            response['otp_code'] = otp_code  # Only for development!

        return jsonify(response), 200
    else:
        # Failed to send
        logger.error(f"Failed to send OTP to {normalized_phone}: {result.get('error')}")
        return jsonify({
            'success': False,
            'error': 'Greška prilikom slanja koda. Pokušajte ponovo.'
        }), 500


@phone_auth_bp.route('/phone/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP and login/register user

    Request body:
        {
            "phone": "+387 6X XXX XXX",
            "code": "123456",
            "referral_code": "175ABC12",  # Optional
            "whatsapp_available": true  # Optional, user preference
        }

    Response:
        {
            "success": true,
            "token": "jwt_token_here",
            "user": {
                "id": "user_id",
                "phone": "+387XXXXXXXXX",
                "whatsapp_available": true,
                "is_new": true/false
            }
        }
    """
    data = request.get_json()
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    referral_code = data.get('referral_code', '').strip().upper() if data.get('referral_code') else None
    whatsapp_available = data.get('whatsapp_available', True)  # Default to True

    if not phone or not code:
        return jsonify({'success': False, 'error': 'Telefon i kod su obavezni'}), 400

    # Normalize phone
    normalized_phone = normalize_phone(phone)

    # Find valid OTP
    otp = OTPCode.query.filter(
        OTPCode.phone == normalized_phone,
        OTPCode.code == code,
        OTPCode.is_used == False,
        OTPCode.expires_at > datetime.now()
    ).order_by(OTPCode.created_at.desc()).first()

    if not otp:
        # Check if OTP exists but is expired or wrong
        any_otp = OTPCode.query.filter(
            OTPCode.phone == normalized_phone
        ).order_by(OTPCode.created_at.desc()).first()

        if any_otp:
            if any_otp.is_used:
                return jsonify({'success': False, 'error': 'Ovaj kod je već iskorišten'}), 400
            elif any_otp.expires_at <= datetime.now():
                return jsonify({'success': False, 'error': 'Kod je istekao. Zatražite novi.'}), 400
            else:
                # Track failed attempts
                any_otp.attempts += 1
                db.session.commit()

                if any_otp.attempts >= 5:
                    return jsonify({'success': False, 'error': 'Previše neuspješnih pokušaja. Zatražite novi kod.'}), 400

                return jsonify({'success': False, 'error': f'Pogrešan kod. Preostalo pokušaja: {5 - any_otp.attempts}'}), 400

        return jsonify({'success': False, 'error': 'Nevažeći ili istekao kod'}), 400

    # Mark OTP as used
    otp.is_used = True
    db.session.commit()

    # Check if user exists
    user = User.query.filter_by(phone=normalized_phone).first()
    is_new_user = False

    if not user:
        # Create new user
        user_id = f"phone_{secrets.token_urlsafe(16)}"
        user = User(
            id=user_id,
            phone=normalized_phone,
            phone_verified=True,
            registration_method='phone',
            is_verified=True,  # Phone verified = account verified
            whatsapp_available=whatsapp_available,  # Save WhatsApp preference
            referred_by_code=referral_code  # Save who referred this user
        )
        db.session.add(user)
        db.session.commit()

        # Initialize credits for new user
        WeeklyCreditsService.initialize_user_credits(user.id)

        # Award referral bonus if referral code provided
        if referral_code:
            try:
                result = WeeklyCreditsService.award_referral_bonus(referral_code, user.id)
                if result['success']:
                    logger.info(f"Referral bonus awarded: {referral_code} referred {user.id}")
                else:
                    logger.warning(f"Failed to award referral bonus: {result.get('error')}")
            except Exception as ref_error:
                logger.error(f"Error awarding referral bonus: {ref_error}")

        is_new_user = True
        logger.info(f"New user registered via phone: {user.id}")
    else:
        # Update verification status if not already verified
        if not user.phone_verified:
            user.phone_verified = True
            user.is_verified = True
            db.session.commit()

    # Generate JWT token
    token = generate_jwt_token(user.id, user.email or user.phone)

    # Log the login event
    try:
        from activity_api import log_user_login
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')
        log_user_login(user.id, 'phone', ip_address, user_agent)
    except Exception as login_track_error:
        logger.warning(f"Failed to track phone login: {login_track_error}")

    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'phone': user.phone,
            'email': user.email,
            'whatsapp_available': user.whatsapp_available,
            'is_new': is_new_user,
            'registration_method': user.registration_method
        }
    }), 200


@phone_auth_bp.route('/phone/resend-otp', methods=['POST'])
def resend_otp():
    """
    Resend OTP code (same as send-otp but with different messaging)
    """
    return send_otp()
