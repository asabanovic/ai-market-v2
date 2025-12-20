# JWT-based authentication API for frontend
import jwt
import os
from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from functools import wraps
from app import app, db
from models import User, UserDailyVisit
from constants import BOSNIAN_CITIES


# Streak milestone bonuses: {days: bonus_credits}
STREAK_MILESTONES = {
    3: 5,    # 3 days streak = +5 credits
    7: 10,   # 7 days streak = +10 credits
    14: 20,  # 14 days streak = +20 credits
    30: 50,  # 30 days streak = +50 credits
    60: 100, # 60 days streak = +100 credits
}

DAILY_ACTIVITY_BONUS = 2  # +2 credits for first activity each day


def track_daily_visit(user_id: str):
    """
    Track a daily visit for a user. Creates one record per user per day.
    If a record already exists for today, updates last_seen and increments page_views.

    Also handles:
    - Daily activity bonus: +2 credits for first activity of the day
    - Streak tracking: consecutive days of activity
    - Milestone bonuses: extra credits at 3, 7, 14, 30, 60 day streaks

    Returns dict with bonus info if any credits were awarded.
    """
    bonus_info = {
        'daily_bonus': 0,
        'streak_bonus': 0,
        'current_streak': 0,
        'milestone_reached': None
    }

    try:
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Get the user
        user = User.query.get(user_id)
        if not user:
            return bonus_info

        # Try to find existing visit for today
        visit = UserDailyVisit.query.filter_by(
            user_id=user_id,
            visit_date=today
        ).first()

        if visit:
            # Update existing visit
            visit.last_seen = datetime.now()
            visit.page_views = (visit.page_views or 1) + 1
        else:
            # Create new visit for today - this is first activity of the day!
            visit = UserDailyVisit(
                user_id=user_id,
                visit_date=today,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                page_views=1,
                daily_bonus_claimed=False
            )
            db.session.add(visit)

        # Award daily bonus if not claimed yet today
        if not visit.daily_bonus_claimed:
            user.extra_credits = (user.extra_credits or 0) + DAILY_ACTIVITY_BONUS
            visit.daily_bonus_claimed = True
            bonus_info['daily_bonus'] = DAILY_ACTIVITY_BONUS

            # Update streak
            if user.last_activity_date == yesterday:
                # Consecutive day - increment streak
                user.current_streak = (user.current_streak or 0) + 1
            elif user.last_activity_date == today:
                # Already updated today, don't change streak
                pass
            else:
                # Streak broken - start fresh
                user.current_streak = 1

            # Update last activity date
            user.last_activity_date = today

            # Update longest streak if current is higher
            if user.current_streak > (user.longest_streak or 0):
                user.longest_streak = user.current_streak

            # Check for milestone bonus
            current_streak = user.current_streak
            last_milestone = user.last_streak_milestone or 0

            for milestone_days, bonus_credits in sorted(STREAK_MILESTONES.items()):
                if current_streak >= milestone_days and milestone_days > last_milestone:
                    # Award milestone bonus
                    user.extra_credits = (user.extra_credits or 0) + bonus_credits
                    user.last_streak_milestone = milestone_days
                    bonus_info['streak_bonus'] = bonus_credits
                    bonus_info['milestone_reached'] = milestone_days
                    app.logger.info(f"User {user_id} reached {milestone_days}-day streak, awarded {bonus_credits} bonus credits")
                    break  # Only award one milestone at a time

            bonus_info['current_streak'] = user.current_streak

        db.session.commit()

        if bonus_info['daily_bonus'] > 0 or bonus_info['streak_bonus'] > 0:
            app.logger.info(f"User {user_id} daily visit: +{bonus_info['daily_bonus']} daily, +{bonus_info['streak_bonus']} streak bonus, streak={bonus_info['current_streak']}")

        return bonus_info

    except Exception as e:
        # Don't fail the main request if tracking fails
        app.logger.error(f"Error tracking daily visit for user {user_id}: {e}")
        db.session.rollback()
        return bonus_info

# Create blueprint
auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/auth')

# Add CORS headers to all responses in this blueprint
@auth_api_bp.after_request
def after_request(response):
    # Get origin from request and validate against allowed origins
    origin = request.headers.get('Origin', 'http://localhost:3000')
    cors_origins_env = os.environ.get("CORS_ORIGINS", "")
    allowed_origins = ['http://localhost:3000', 'http://127.0.0.1:3000']
    if cors_origins_env:
        allowed_origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

    # Only set the origin if it's in our allowed list
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', allowed_origins[0])

    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# JWT configuration
JWT_SECRET = os.environ.get("SESSION_SECRET") or "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 30  # 30 days


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
            'onboarding_completed': user.onboarding_completed or False,
            'welcome_guide_seen': user.welcome_guide_seen or False
        }

        app.logger.info(f"API login successful for: {email}")

        # Log the login event
        try:
            from activity_api import log_user_login
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()
            user_agent = request.headers.get('User-Agent', '')
            log_user_login(user.id, 'email', ip_address, user_agent)
        except Exception as login_track_error:
            app.logger.warning(f"Failed to track login: {login_track_error}")

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

        # Track daily visit and get bonus info
        bonus_info = track_daily_visit(user.id)

        # Refresh user to get updated credit values
        db.session.refresh(user)

        # Calculate next milestone
        current_streak = user.current_streak or 0
        next_milestone = None
        next_milestone_bonus = None
        for days, bonus in sorted(STREAK_MILESTONES.items()):
            if days > current_streak:
                next_milestone = days
                next_milestone_bonus = bonus
                break

        user_data = {
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'city': user.city,
            'is_admin': user.is_admin,
            'onboarding_completed': user.onboarding_completed or False,
            'welcome_guide_seen': user.welcome_guide_seen or False,
            'preferences': user.preferences or {},
            'first_search_reward_claimed': user.first_search_reward_claimed or False,
            # Streak info
            'current_streak': current_streak,
            'longest_streak': user.longest_streak or 0,
            'next_milestone': next_milestone,
            'next_milestone_bonus': next_milestone_bonus,
            'milestones': STREAK_MILESTONES
        }

        response_data = {'user': user_data}

        # Include bonus info if any credits were just awarded
        if bonus_info and (bonus_info.get('daily_bonus', 0) > 0 or bonus_info.get('streak_bonus', 0) > 0):
            response_data['bonus_awarded'] = bonus_info

        return jsonify(response_data), 200

    except Exception as e:
        app.logger.error(f"API verify error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_api_bp.route('/register', methods=['POST'])
def api_register():
    """Register a new user"""
    try:
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        from credits_service_weekly import WeeklyCreditsService

        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        email = data.get('email')
        password = data.get('password')
        referral_code = data.get('referral_code', '').strip().upper() if data.get('referral_code') else None

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
            package_id=1,  # Free package
            registration_method='email',
            referred_by_code=referral_code  # Save who referred this user
        )

        db.session.add(new_user)
        db.session.commit()

        # Initialize credits for new user
        try:
            WeeklyCreditsService.initialize_user_credits(new_user.id)
        except Exception as credit_error:
            app.logger.error(f"Failed to initialize credits: {credit_error}")

        # Award referral bonus if referral code provided
        if referral_code:
            try:
                result = WeeklyCreditsService.award_referral_bonus(referral_code, new_user.id)
                if result['success']:
                    app.logger.info(f"Referral bonus awarded: {referral_code} referred {new_user.id}")
                else:
                    app.logger.warning(f"Failed to award referral bonus: {result.get('error')}")
            except Exception as ref_error:
                app.logger.error(f"Error awarding referral bonus: {ref_error}")

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


@auth_api_bp.route('/user/welcome-guide-seen', methods=['POST', 'OPTIONS'])
@require_jwt_auth
def mark_welcome_guide_seen():
    """Mark welcome guide as seen by the user"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        # Get user from JWT
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401

        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        user = User.query.filter_by(id=payload['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Mark welcome guide as seen
        user.welcome_guide_seen = True
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Welcome guide marked as seen'
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Welcome guide seen error: {e}")
        return jsonify({'error': 'Error updating user'}), 500


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


@auth_api_bp.route('/user/interests', methods=['PUT', 'OPTIONS'])
def update_user_interests():
    """Update user grocery interests and optionally phone number"""
    from sqlalchemy.orm.attributes import flag_modified

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

        user = User.query.filter_by(id=payload['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        # Update phone if provided
        if 'phone' in data and data['phone']:
            phone = data['phone'].strip()
            # Validate phone format (basic validation)
            clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if clean_phone and len(clean_phone) >= 9:
                # Check if phone is already used by another user
                existing = User.query.filter(User.phone == phone, User.id != user.id).first()
                if existing:
                    return jsonify({'error': 'Ovaj broj telefona je već registrovan'}), 400
                user.phone = phone

        # Update grocery interests
        if 'grocery_interests' in data:
            interests = data['grocery_interests']
            if isinstance(interests, list):
                # Ensure preferences is a dict
                if not user.preferences:
                    user.preferences = {}
                elif not isinstance(user.preferences, dict):
                    user.preferences = {}

                # Clean and deduplicate interests
                clean_interests = list(set([i.strip() for i in interests if i and i.strip()]))
                user.preferences['grocery_interests'] = clean_interests

                # Mark preferences as modified for SQLAlchemy to detect the change
                flag_modified(user, 'preferences')

        db.session.commit()

        app.logger.info(f"Interests updated for user: {user.email}, interests: {user.preferences.get('grocery_interests', [])}")

        return jsonify({
            'success': True,
            'message': 'Interesi uspješno sačuvani',
            'grocery_interests': user.preferences.get('grocery_interests', []) if user.preferences else []
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Update interests error: {e}")
        return jsonify({'error': 'Greška pri spremanju interesa'}), 500


@auth_api_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of Bosnian cities with optional coordinates"""
    from models import City

    # Check if coordinates are requested
    include_coords = request.args.get('coords', 'false').lower() == 'true'

    # Try to get from database first
    db_cities = City.query.order_by(City.name).all()

    if db_cities:
        if include_coords:
            cities = [{
                'name': city.name,
                'latitude': city.latitude,
                'longitude': city.longitude
            } for city in db_cities]
            return jsonify({'cities': cities}), 200
        else:
            # Return just names for backward compatibility
            return jsonify({'cities': [city.name for city in db_cities]}), 200
    else:
        # Fallback to constants if no cities in DB
        return jsonify({'cities': BOSNIAN_CITIES}), 200


@auth_api_bp.route('/cities/populate', methods=['POST'])
@require_jwt_auth
def populate_cities_endpoint():
    """Admin endpoint to populate cities with coordinates from OpenStreetMap"""
    from models import City, User
    import time
    import requests

    # Check if user is admin
    user = User.query.get(request.current_user_id)
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Nominatim API endpoint (free, no API key required)
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    HEADERS = {
        "User-Agent": "PopustBA/1.0 (https://popust.ba; contact@popust.ba)"
    }

    def geocode_city(city_name, country="Bosnia and Herzegovina"):
        params = {
            "q": f"{city_name}, {country}",
            "format": "json",
            "limit": 1
        }
        try:
            response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data and len(data) > 0:
                return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
            return None
        except Exception:
            return None

    # Create cities table if needed
    db.create_all()

    success_count = 0
    failed_cities = []

    for city_name in BOSNIAN_CITIES:
        # Check if city exists
        existing = City.query.filter_by(name=city_name).first()
        if existing and existing.latitude and existing.longitude:
            success_count += 1
            continue

        if not existing:
            city = City(name=city_name)
            db.session.add(city)
        else:
            city = existing

        # Geocode
        result = geocode_city(city_name)
        if result:
            city.latitude = result["lat"]
            city.longitude = result["lon"]
            db.session.commit()
            success_count += 1
        else:
            # Try without country
            result = geocode_city(city_name, "")
            if result:
                city.latitude = result["lat"]
                city.longitude = result["lon"]
                db.session.commit()
                success_count += 1
            else:
                db.session.commit()
                failed_cities.append(city_name)

        # Rate limiting: 1 request per second (Nominatim requirement)
        time.sleep(1.1)

    return jsonify({
        'success': True,
        'total': len(BOSNIAN_CITIES),
        'geocoded': success_count,
        'failed': failed_cities
    }), 200


@auth_api_bp.route('/user/store-preferences', methods=['GET', 'PUT', 'OPTIONS'])
def user_store_preferences():
    """Get or update user's preferred stores for search filtering"""
    from models import Business

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

        user = User.query.filter_by(id=payload['user_id']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Initialize preferences if None
        if user.preferences is None:
            user.preferences = {}

        # GET - Return user's store preferences
        if request.method == 'GET':
            preferred_stores = user.preferences.get('preferred_stores', [])
            last_seen_store_id = user.preferences.get('last_seen_store_id', 0)

            # Get all active businesses for comparison
            businesses = Business.query.filter_by(status='active').order_by(Business.name).all()

            return jsonify({
                'preferred_stores': preferred_stores,
                'preferred_store_ids': preferred_stores,  # Alias for frontend compatibility
                'last_seen_store_id': last_seen_store_id,
                'all_stores': [
                    {
                        'id': b.id,
                        'name': b.name,
                        'logo': b.logo_path,
                        'city': b.city,
                        'is_selected': b.id in preferred_stores
                    }
                    for b in businesses
                ]
            }), 200

        # PUT - Update store preferences
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request data'}), 400

            # Update preferred stores (accept both field names for compatibility)
            store_ids = data.get('preferred_stores') or data.get('preferred_store_ids')
            if store_ids is not None:
                # Validate that all IDs are valid businesses
                if store_ids:
                    valid_ids = [b.id for b in Business.query.filter(Business.id.in_(store_ids), Business.status == 'active').all()]
                    user.preferences['preferred_stores'] = valid_ids
                else:
                    user.preferences['preferred_stores'] = []

            # Update last seen store ID (for new store popup tracking)
            if 'last_seen_store_id' in data:
                user.preferences['last_seen_store_id'] = data['last_seen_store_id']

            # Force SQLAlchemy to detect JSON change
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, 'preferences')

            db.session.commit()

            app.logger.info(f"Store preferences updated for user: {user.email}")

            return jsonify({
                'success': True,
                'message': 'Postavke prodavnica uspješno ažurirane',
                'preferred_stores': user.preferences.get('preferred_stores', [])
            }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Store preferences error: {e}")
        return jsonify({'error': 'Greška pri ažuriranju postavki'}), 500


@auth_api_bp.route('/new-stores', methods=['GET'])
def get_new_stores():
    """Get stores that are newer than user's last seen store ID"""
    from models import Business

    # Check JWT authentication (optional - works for both auth and anon)
    auth_header = request.headers.get('Authorization')
    last_seen_id = 0

    if auth_header:
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if payload:
                user = User.query.filter_by(id=payload['user_id']).first()
                if user and user.preferences:
                    last_seen_id = user.preferences.get('last_seen_store_id', 0)
        except Exception:
            pass

    # For anonymous users, check query param or localStorage value sent by frontend
    if last_seen_id == 0:
        last_seen_id = request.args.get('last_seen_id', 0, type=int)

    # Get businesses added after last_seen_id
    new_stores = Business.query.filter(
        Business.id > last_seen_id,
        Business.status == 'active'
    ).order_by(Business.id.asc()).all()

    if not new_stores:
        return jsonify({
            'has_new_stores': False,
            'new_stores': [],
            'latest_store_id': last_seen_id
        }), 200

    # Get the latest store ID for future reference
    latest_store_id = max(s.id for s in new_stores)

    return jsonify({
        'has_new_stores': True,
        'new_stores': [
            {
                'id': s.id,
                'name': s.name,
                'logo': f"/static/{s.logo_path}" if s.logo_path else None,
                'city': s.city,
                'google_link': s.google_link
            }
            for s in new_stores
        ],
        'latest_store_id': latest_store_id
    }), 200


@auth_api_bp.route('/search-counts', methods=['GET'])
def get_search_counts_jwt():
    """Get search counts for JWT authenticated user"""
    from credits_service_weekly import WeeklyCreditsService
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

        # Get credit balance (two-bucket system)
        balance = WeeklyCreditsService.get_balance(user.id)
        total_credits = balance['total_credits']

        # For admins or users with high balances (>100), show unlimited
        if user.is_admin or total_credits > 100:
            return jsonify({
                'weekly_limit': total_credits,
                'used_this_week': 0,
                'remaining': total_credits,
                'regular_credits': balance['regular_credits'],
                'extra_credits': balance['extra_credits'],
                'next_reset_date': balance['next_reset_date'].isoformat(),
                'user_type': 'logged_in',
                'is_unlimited': True
            }), 200
        else:
            # For regular users, show standard weekly limit
            from credits_service_weekly import REGULAR_USER_WEEKLY_CREDITS
            weekly_limit = REGULAR_USER_WEEKLY_CREDITS
            return jsonify({
                'weekly_limit': weekly_limit,  # Base weekly limit
                'used_this_week': weekly_limit - balance['regular_credits'],
                'remaining': total_credits,
                'regular_credits': balance['regular_credits'],
                'extra_credits': balance['extra_credits'],
                'next_reset_date': balance['next_reset_date'].isoformat(),
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


# =====================================================
# RESEND VERIFICATION EMAIL
# =====================================================

@auth_api_bp.route('/resend-verification', methods=['POST', 'OPTIONS'])
def resend_verification_email():
    """Resend verification email to user"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        from sendgrid_utils import send_verification_email, generate_verification_token

        data = request.get_json()
        email = data.get('email') if data else None

        # Check if request comes from authenticated user
        auth_header = request.headers.get('Authorization')
        user = None

        if auth_header:
            try:
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
                payload = decode_jwt_token(token)
                if payload:
                    user = User.query.filter_by(id=payload['user_id']).first()
            except Exception:
                pass

        # If no auth, require email in body
        if not user and not email:
            return jsonify({'error': 'Email je obavezan'}), 400

        # Find user by email if not authenticated
        if not user:
            user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({'error': 'Korisnik nije pronađen'}), 404

        if user.is_verified:
            return jsonify({'error': 'Email je već verifikovan'}), 400

        # Rate limiting: check if email was sent recently (within 60 seconds)
        if user.verification_email_sent_at:
            time_since_last = datetime.now() - user.verification_email_sent_at
            if time_since_last.total_seconds() < 60:
                remaining = 60 - int(time_since_last.total_seconds())
                return jsonify({
                    'error': f'Molimo sačekajte {remaining} sekundi prije ponovnog slanja',
                    'retry_after': remaining
                }), 429

        # Generate new verification token
        verification_token = generate_verification_token()
        user.verification_token = verification_token
        user.verification_token_expires = datetime.now() + timedelta(hours=24)
        user.verification_email_sent_at = datetime.now()

        db.session.commit()

        # Send verification email
        base_url = os.environ.get("BASE_URL", "https://popust.ba")
        if send_verification_email(user.email, user.first_name, verification_token, base_url):
            app.logger.info(f"Verification email resent to {user.email}")
            return jsonify({
                'success': True,
                'message': 'Verifikacijski email je poslan'
            }), 200
        else:
            return jsonify({'error': 'Greška pri slanju emaila'}), 500

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Resend verification error: {e}")
        return jsonify({'error': 'Greška pri slanju emaila'}), 500


# =====================================================
# ADMIN EMAIL TEST ENDPOINTS
# =====================================================

@auth_api_bp.route('/admin/test-email/<template_type>', methods=['POST', 'OPTIONS'])
@require_jwt_auth
def test_email_template(template_type):
    """Test email templates - Admin only. Sends to adnanxteam@gmail.com"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Check if user is admin
    user = User.query.get(request.current_user_id)
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    from sendgrid_utils import (
        send_verification_email, send_welcome_email, send_password_reset_email,
        send_invitation_email, send_contact_email, send_scan_summary_email,
        generate_verification_token
    )

    test_email = "adnanxteam@gmail.com"
    test_name = "Adnan"
    base_url = os.environ.get("BASE_URL", "https://popust.ba")

    try:
        if template_type == 'verification':
            token = generate_verification_token()
            success = send_verification_email(test_email, test_name, token, base_url)
            template_name = "Email Verification"

        elif template_type == 'welcome':
            success = send_welcome_email(test_email, test_name)
            template_name = "Welcome Email"

        elif template_type == 'password-reset':
            token = generate_verification_token()
            success = send_password_reset_email(test_email, test_name, token, base_url)
            template_name = "Password Reset"

        elif template_type == 'invitation':
            token = generate_verification_token()
            success = send_invitation_email(test_email, "Test Business", "manager", token, base_url)
            template_name = "Business Invitation"

        elif template_type == 'contact':
            success = send_contact_email(test_name, test_email, "Ovo je test poruka sa kontakt forme.")
            template_name = "Contact Form"

        elif template_type == 'scan-summary':
            # Create test summary data
            test_summary = {
                'total_products': 42,
                'new_products': 5,
                'new_discounts': 3,
                'terms': [
                    {
                        'search_term': 'Nutella',
                        'lowest_price': 7.99,
                        'lowest_store': 'Bingo',
                        'new_count': 2
                    },
                    {
                        'search_term': 'Mlijeko',
                        'lowest_price': 1.89,
                        'lowest_store': 'Konzum',
                        'new_count': 0
                    },
                    {
                        'search_term': 'Coca Cola',
                        'lowest_price': 2.49,
                        'lowest_store': 'Robot',
                        'new_count': 3
                    }
                ]
            }
            success = send_scan_summary_email(test_email, test_name, test_summary)
            template_name = "Scan Summary"

        elif template_type == 'weekly-summary':
            from sendgrid_utils import send_weekly_summary_email
            # Create comprehensive test data for weekly summary
            test_summary = {
                'total_products': 23,
                'total_savings': 47.50,
                'best_deals': [
                    {
                        'product': 'Nutella 750g',
                        'store': 'Bingo',
                        'original_price': 12.99,
                        'discount_price': 8.99,
                        'savings_percent': 31
                    },
                    {
                        'product': 'Coca Cola 2L',
                        'store': 'Konzum',
                        'original_price': 3.49,
                        'discount_price': 2.49,
                        'savings_percent': 29
                    },
                    {
                        'product': 'Cedevita 500g',
                        'store': 'Robot',
                        'original_price': 6.99,
                        'discount_price': 4.99,
                        'savings_percent': 29
                    }
                ],
                'tracked_items': [
                    {'product': 'Nutella 750g', 'store': 'Bingo', 'current_price': 8.99, 'price_change': -4.00},
                    {'product': 'Mlijeko Meggle 1L', 'store': 'Konzum', 'current_price': 1.89, 'price_change': 0},
                    {'product': 'Coca Cola 2L', 'store': 'Konzum', 'current_price': 2.49, 'price_change': -1.00},
                    {'product': 'Cedevita 500g', 'store': 'Robot', 'current_price': 4.99, 'price_change': -2.00},
                    {'product': 'Jaja 10kom', 'store': 'Bingo', 'current_price': 3.29, 'price_change': 0.20},
                    {'product': 'Pivo Sarajevsko 0.5L', 'store': 'Konzum', 'current_price': 1.79, 'price_change': 0},
                    {'product': 'Kafa Grand Gold 200g', 'store': 'Robot', 'current_price': 5.49, 'price_change': -0.50},
                    {'product': 'Ulje Zvijezda 1L', 'store': 'Bingo', 'current_price': 2.99, 'price_change': 0}
                ],
                'price_drops': [
                    {'product': 'Nutella 750g', 'drop_amount': 4.00},
                    {'product': 'Cedevita 500g', 'drop_amount': 2.00},
                    {'product': 'Coca Cola 2L', 'drop_amount': 1.00},
                    {'product': 'Kafa Grand Gold 200g', 'drop_amount': 0.50}
                ],
                'new_products': [
                    {'product': 'Milka Oreo 100g', 'store': 'Bingo', 'price': 2.99},
                    {'product': 'Dorina Lješnjak 200g', 'store': 'Konzum', 'price': 3.49},
                    {'product': 'Čokolino 500g', 'store': 'Robot', 'price': 4.29}
                ]
            }
            success = send_weekly_summary_email(test_email, test_name, test_summary)
            template_name = "Weekly Summary"

        else:
            return jsonify({'error': f'Unknown template type: {template_type}'}), 400

        if success:
            app.logger.info(f"Test email '{template_name}' sent to {test_email}")
            return jsonify({
                'success': True,
                'message': f'{template_name} email sent to {test_email}'
            }), 200
        else:
            return jsonify({'error': f'Failed to send {template_name} email'}), 500

    except Exception as e:
        app.logger.error(f"Test email error: {e}")
        return jsonify({'error': str(e)}), 500


@auth_api_bp.route('/admin/send-scan-summary/<user_id>', methods=['POST', 'OPTIONS'])
@require_jwt_auth
def admin_send_scan_summary(user_id):
    """Manually trigger scan summary email for a specific user - Admin only"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Check if user is admin
    admin_user = User.query.get(request.current_user_id)
    if not admin_user or not admin_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    from jobs.send_scan_email_summaries import get_scan_summary_for_user, send_scan_summary_email

    try:
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        if not target_user.email:
            return jsonify({'error': 'User has no email address'}), 400

        # Get today's scan summary
        today = date.today()
        summary = get_scan_summary_for_user(target_user.id, today)

        if not summary or summary['total_products'] == 0:
            return jsonify({
                'error': 'No scan data found for today. Run a scan first.',
                'has_scan': False
            }), 404

        # Send email
        if send_scan_summary_email(target_user, summary):
            app.logger.info(f"Admin triggered scan summary email for user {user_id}")
            return jsonify({
                'success': True,
                'message': f'Scan summary sent to {target_user.email}',
                'summary': {
                    'total_products': summary['total_products'],
                    'new_products': summary['new_products'],
                    'new_discounts': summary['new_discounts'],
                    'terms_count': len(summary['terms'])
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to send email (notifications may be disabled)'}), 500

    except Exception as e:
        app.logger.error(f"Admin scan summary error: {e}")
        return jsonify({'error': str(e)}), 500


def get_weekly_summary_for_user(user_id: str, top_n: int = 2) -> dict:
    """
    Generate weekly summary data from actual database records.

    Groups results by tracked search term and returns only TOP N products per term
    (sorted by lowest price). This provides realistic statistics instead of showing
    all 400+ matching products.

    Args:
        user_id: The user ID to generate summary for
        top_n: Number of top products to show per tracked term (default: 2)

    Returns dict formatted for send_weekly_summary_email function.
    """
    from models import UserTrackedProduct, UserProductScan, UserScanResult
    from datetime import timedelta

    # Get user's tracked products
    tracked_products = UserTrackedProduct.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()

    if not tracked_products:
        return None

    # Create lookup map for tracked products
    tracked_map = {tp.id: tp for tp in tracked_products}

    # Get scans from last 7 days
    week_ago = date.today() - timedelta(days=7)

    # Get the most recent scan
    latest_scan = UserProductScan.query.filter(
        UserProductScan.user_id == user_id,
        UserProductScan.scan_date >= week_ago,
        UserProductScan.status == 'completed'
    ).order_by(UserProductScan.scan_date.desc()).first()

    if not latest_scan:
        return None

    # Get all results from latest scan
    scan_results = UserScanResult.query.filter_by(scan_id=latest_scan.id).all()

    if not scan_results:
        return None

    # Group results by tracked product (search term)
    results_by_term = {}
    for result in scan_results:
        tracked = tracked_map.get(result.tracked_product_id)
        if not tracked:
            continue

        term = tracked.search_term
        if term not in results_by_term:
            results_by_term[term] = {
                'search_term': term,
                'original_text': tracked.original_text,
                'products': []
            }

        current_price = float(result.discount_price or result.base_price or 0)
        original_price = float(result.base_price or current_price)

        results_by_term[term]['products'].append({
            'product': result.product_title or term,
            'store': result.business_name or 'Nepoznato',
            'current_price': current_price,
            'original_price': original_price,
            'discount_price': float(result.discount_price) if result.discount_price else None,
            'is_new': result.is_new_today,
            'price_dropped': result.price_dropped_today
        })

    # Now select TOP N products per term (by lowest current price)
    tracked_items = []
    best_deals = []
    price_drops = []
    new_products = []
    total_savings = 0

    for term, data in results_by_term.items():
        # Sort products by current price (lowest first)
        products = sorted(data['products'], key=lambda x: x['current_price'] if x['current_price'] > 0 else float('inf'))

        # Take only TOP N products per term
        top_products = products[:top_n]

        for product in top_products:
            # Add to tracked items
            price_change = 0
            if product['discount_price'] and product['original_price'] > product['discount_price']:
                price_change = -(product['original_price'] - product['discount_price'])

            tracked_items.append({
                'product': product['product'],
                'store': product['store'],
                'current_price': product['current_price'],
                'price_change': price_change,
                'search_term': term  # Include term for grouping in email
            })

            # Best deals - products with discounts (calculate savings per item, not total)
            if product['discount_price'] and product['original_price'] > product['discount_price']:
                savings_pct = ((product['original_price'] - product['discount_price']) / product['original_price']) * 100

                best_deals.append({
                    'product': product['product'],
                    'store': product['store'],
                    'original_price': product['original_price'],
                    'discount_price': product['discount_price'],
                    'savings_percent': savings_pct
                })

            # Price drops
            if product['price_dropped']:
                if product['discount_price'] and product['original_price'] > product['discount_price']:
                    drop_amount = product['original_price'] - product['discount_price']
                    price_drops.append({
                        'product': product['product'],
                        'drop_amount': drop_amount
                    })

            # New products
            if product['is_new']:
                new_products.append({
                    'product': product['product'],
                    'store': product['store'],
                    'price': product['current_price']
                })

        # Calculate realistic savings: best deal per term (what user would actually buy)
        # Take only the BEST price per term for savings calculation
        if top_products:
            best_product = top_products[0]  # Already sorted by price
            if best_product['discount_price'] and best_product['original_price'] > best_product['discount_price']:
                total_savings += (best_product['original_price'] - best_product['discount_price'])

    # Sort best deals by savings percentage
    best_deals.sort(key=lambda x: x['savings_percent'], reverse=True)

    # Sort price drops by amount
    price_drops.sort(key=lambda x: x['drop_amount'], reverse=True)

    return {
        'total_products': len(tracked_products),  # Number of tracked TERMS, not all matches
        'total_matches': len(tracked_items),  # Total items shown (top_n per term)
        'total_savings': round(total_savings, 2),  # Realistic savings (1 item per term)
        'best_deals': best_deals[:5],
        'tracked_items': tracked_items,  # All top_n items per term
        'price_drops': price_drops[:5],
        'new_products': new_products[:5],
        'terms_count': len(results_by_term)  # How many terms had results
    }


@auth_api_bp.route('/admin/send-weekly-summary/<user_id>', methods=['POST', 'OPTIONS'])
@require_jwt_auth
def admin_send_weekly_summary(user_id):
    """Send weekly summary email with REAL data from database - Admin only"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    # Check if user is admin
    admin_user = User.query.get(request.current_user_id)
    if not admin_user or not admin_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    from sendgrid_utils import send_weekly_summary_email

    try:
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        if not target_user.email:
            return jsonify({'error': 'User has no email address'}), 400

        # Get real summary data from database
        summary = get_weekly_summary_for_user(target_user.id)

        if not summary or summary['total_products'] == 0:
            return jsonify({
                'error': 'No tracked products found for this user. Add products to track first.',
                'has_data': False
            }), 404

        # Get user name
        user_name = target_user.first_name or target_user.email.split('@')[0]

        # Send email with real data
        if send_weekly_summary_email(target_user.email, user_name, summary):
            app.logger.info(f"Admin triggered weekly summary email for user {user_id}")
            return jsonify({
                'success': True,
                'message': f'Weekly summary sent to {target_user.email}',
                'summary': {
                    'tracked_terms': summary['total_products'],  # Number of tracked terms
                    'top_matches': summary.get('total_matches', len(summary['tracked_items'])),  # Top N per term
                    'total_savings': summary['total_savings'],
                    'terms_with_results': summary.get('terms_count', 0),
                    'best_deals_count': len(summary['best_deals']),
                    'price_drops_count': len(summary['price_drops']),
                    'new_products_count': len(summary['new_products'])
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500

    except Exception as e:
        app.logger.error(f"Admin weekly summary error: {e}")
        return jsonify({'error': str(e)}), 500
