# JWT-based authentication API for frontend
import jwt
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from functools import wraps
from app import app, db
from models import User
from constants import BOSNIAN_CITIES

# Create blueprint
auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/auth')

# Add CORS headers to all responses in this blueprint
@auth_api_bp.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# JWT configuration
JWT_SECRET = os.environ.get("SESSION_SECRET") or "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_jwt_token(user_id: str, email: str) -> str:
    """Generate a JWT token for a user"""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str):
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_jwt_auth(f):
    """Decorator to require JWT authentication for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            app.logger.error("JWT auth: Missing authorization header")
            return jsonify({'error': 'Missing authorization header'}), 401

        try:
            # Expected format: "Bearer <token>"
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            app.logger.info(f"JWT auth: Attempting to decode token (first 20 chars): {token[:20]}...")
            payload = decode_jwt_token(token)

            if not payload:
                app.logger.error("JWT auth: Token decode returned None (expired or invalid)")
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Attach user info to request
            request.current_user_id = payload['user_id']
            request.current_user_email = payload['email']
            app.logger.info(f"JWT auth: Success for user {payload['email']}")

        except Exception as e:
            app.logger.error(f"JWT auth error: {e}")
            return jsonify({'error': 'Invalid authorization header'}), 401

        return f(*args, **kwargs)

    return decorated


@auth_api_bp.route('/login', methods=['POST'])
def api_login():
    """JWT-based login endpoint for API clients"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        email = data.get('email')
        password = data.get('password')

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email i lozinka su obavezni'}), 400

        # Find user
        user = User.query.filter_by(email=email).first()

        # Log login attempt
        app.logger.info(f"API login attempt for email: {email}")

        # Validate credentials
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            app.logger.info("API login failed: Invalid credentials")
            return jsonify({'error': 'Neispravni podaci za prijavu'}), 401

        # Check if user is verified (unless admin)
        if not user.is_verified and not user.is_admin:
            return jsonify({
                'error': 'Molimo vas prvo verifikujte vaš email prije prijave.',
                'verification_required': True
            }), 403

        # Generate JWT token
        token = generate_jwt_token(user.id, user.email)

        # Prepare user data
        user_data = {
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'city': user.city,
            'is_admin': user.is_admin,
            'onboarding_completed': user.onboarding_completed or False
        }

        app.logger.info(f"API login successful for: {email}")

        return jsonify({
            'token': token,
            'user': user_data
        }), 200

    except Exception as e:
        app.logger.error(f"API login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_api_bp.route('/verify', methods=['GET'])
@require_jwt_auth
def api_verify():
    """Verify JWT token and return user data"""
    try:
        user = User.query.filter_by(id=request.current_user_id).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_data = {
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'city': user.city,
            'is_admin': user.is_admin,
            'onboarding_completed': user.onboarding_completed or False
        }

        return jsonify({'user': user_data}), 200

    except Exception as e:
        app.logger.error(f"API verify error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_api_bp.route('/register', methods=['POST'])
def api_register():
    """Register a new user"""
    try:
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        from credits_service import CreditsService

        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        email = data.get('email')
        password = data.get('password')

        # Support both separate first_name/last_name and combined name field for backward compatibility
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        name = data.get('name', '').strip()

        # If name is provided but not first_name/last_name, split the name
        if name and not (first_name or last_name):
            name_parts = name.split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

        app.logger.info(f"Registration data - email: {email}, first_name: '{first_name}', last_name: '{last_name}', name: '{name}'")

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email i lozinka su obavezni'}), 400

        if not first_name:
            return jsonify({'error': 'Ime je obavezno'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Korisnik sa ovim emailom već postoji'}), 400

        # Create new user
        new_user = User(
            id=str(datetime.now().timestamp()),
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=generate_password_hash(password),
            is_verified=True,  # Auto-verify for now
            package_id=1  # Free package
        )

        db.session.add(new_user)
        db.session.commit()

        # Initialize credits for new user
        try:
            CreditsService.initialize_user_credits(new_user.id, initial_amount=10)
        except Exception as credit_error:
            app.logger.error(f"Failed to initialize credits: {credit_error}")

        # Generate JWT token
        token = generate_jwt_token(new_user.id, new_user.email)

        # Prepare user data
        user_data = {
            'id': new_user.id,
            'email': new_user.email,
            'name': f"{first_name} {last_name}".strip() or email,
            'first_name': first_name,
            'last_name': last_name
        }

        app.logger.info(f"New user registered: {email}")

        return jsonify({
            'success': True,
            'token': token,
            'user': user_data,
            'message': 'Uspješno ste se registrovali!'
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"API register error: {e}")
        return jsonify({'error': 'Greška pri registraciji'}), 500


@auth_api_bp.route('/logout', methods=['POST'])
@require_jwt_auth
def api_logout():
    """Logout endpoint (client should discard token)"""
    # With JWT, logout is handled client-side by removing the token
    # This endpoint exists for consistency and potential future server-side token blacklisting
    return jsonify({'success': True}), 200


@auth_api_bp.route('/user/phone', methods=['POST', 'OPTIONS'])
def update_phone():
    """Update user's phone number"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Require JWT auth for POST
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing authorization header'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        phone = data.get('phone', '').strip()

        if not phone:
            return jsonify({'error': 'Broj telefona je obavezan'}), 400

        # Find user
        user = User.query.filter_by(id=payload['user_id']).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update phone number
        user.phone = phone
        db.session.commit()

        app.logger.info(f"Phone number updated for user: {user.email}")

        return jsonify({
            'success': True,
            'message': 'Broj telefona je uspješno sačuvan'
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Update phone error: {e}")
        return jsonify({'error': 'Greška pri čuvanju broja telefona'}), 500


@auth_api_bp.route('/user/onboarding', methods=['POST', 'OPTIONS'])
@require_jwt_auth
def complete_onboarding():
    """Complete user onboarding - save phone and shopping preferences"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        typical_products = data.get('typical_products', '').strip()

        # Get user from JWT
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        user = User.query.filter_by(id=payload['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update user
        if phone:
            user.phone = phone

        # Save typical products to preferences
        if typical_products:
            if not user.preferences:
                user.preferences = {}
            user.preferences['typical_products'] = typical_products

        # Mark onboarding as completed
        user.onboarding_completed = True

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Dobrodošli! Obavijestit ćemo vas kada vaši omiljeni proizvodi budu na akciji.'
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Onboarding error: {e}")
        return jsonify({'error': 'Greška pri čuvanju podataka'}), 500


@auth_api_bp.route('/user/profile', methods=['GET', 'PUT', 'OPTIONS'])
def user_profile():
    """Get or update user profile"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Require JWT auth
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Missing authorization header'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Find user
        user = User.query.filter_by(id=payload['user_id']).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # GET - Return user profile
        if request.method == 'GET':
            return jsonify({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'city': user.city,
                'notification_preferences': user.notification_preferences or 'none',
                'is_admin': user.is_admin,
                'is_verified': user.is_verified
            }), 200

        # PUT - Update user profile
        if request.method == 'PUT':
            data = request.get_json()

            if not data:
                return jsonify({'error': 'Invalid request data'}), 400

            # Update fields if provided
            if 'first_name' in data:
                user.first_name = data['first_name'].strip() if data['first_name'] else None

            if 'last_name' in data:
                user.last_name = data['last_name'].strip() if data['last_name'] else None

            if 'phone' in data:
                user.phone = data['phone'].strip() if data['phone'] else None

            if 'city' in data:
                city = data['city'].strip() if data['city'] else None
                # Validate city is in the list
                if city and city not in BOSNIAN_CITIES:
                    return jsonify({'error': 'Invalid city selected'}), 400
                user.city = city

            if 'notification_preferences' in data:
                prefs = data['notification_preferences'].strip() if data['notification_preferences'] else 'none'
                # Validate notification preference
                if prefs not in ['none', 'favorites', 'all']:
                    return jsonify({'error': 'Invalid notification preference'}), 400
                user.notification_preferences = prefs

            db.session.commit()

            app.logger.info(f"Profile updated for user: {user.email}")

            return jsonify({
                'success': True,
                'message': 'Profil uspješno ažuriran',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'city': user.city,
                    'is_admin': user.is_admin
                }
            }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Profile error: {e}")
        return jsonify({'error': 'Greška pri ažuriranju profila'}), 500


@auth_api_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of Bosnian cities"""
    return jsonify({'cities': BOSNIAN_CITIES}), 200


@auth_api_bp.route('/search-counts', methods=['GET'])
def get_search_counts_jwt():
    """Get search counts for JWT authenticated user"""
    from credits_service import CreditsService
    from datetime import date

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')

    # If no auth header, return anonymous user limits
    if not auth_header:
        return jsonify({
            'daily_limit': 3,
            'used_today': 0,
            'remaining': 3,
            'user_type': 'anonymous',
            'is_unlimited': False
        }), 200

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({
                'daily_limit': 3,
                'used_today': 0,
                'remaining': 3,
                'user_type': 'anonymous',
                'is_unlimited': False
            }), 200

        # Find user
        user = User.query.filter_by(id=payload['user_id']).first()

        if not user:
            return jsonify({
                'daily_limit': 3,
                'used_today': 0,
                'remaining': 3,
                'user_type': 'anonymous',
                'is_unlimited': False
            }), 200

        # Get credit balance
        current_balance = CreditsService.get_balance(user.id)

        # For admins or users with high balances (>100), show unlimited
        if user.is_admin or current_balance > 100:
            return jsonify({
                'daily_limit': current_balance,
                'used_today': 0,
                'remaining': current_balance,
                'user_type': 'logged_in',
                'is_unlimited': True
            }), 200
        else:
            # For regular users, show standard daily limit
            daily_limit = 10
            return jsonify({
                'daily_limit': daily_limit,
                'used_today': max(0, daily_limit - current_balance),
                'remaining': max(0, current_balance),
                'user_type': 'logged_in',
                'is_unlimited': False
            }), 200

    except Exception as e:
        app.logger.error(f"Search counts error: {e}")
        return jsonify({
            'daily_limit': 3,
            'used_today': 0,
            'remaining': 3,
            'user_type': 'anonymous',
            'is_unlimited': False
        }), 200
