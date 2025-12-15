# Main routes for the marketplace application
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date, timedelta, time
from functools import wraps
import os
import json
import csv
import io
import re
from sqlalchemy import or_, and_, func, case
from sqlalchemy.orm.attributes import flag_modified
# import pdb  # Removed debug import
from app import app, db, csrf
from models import User, Package, Business, Product, UserSearch, ContactMessage, BusinessMembership, BusinessInvitation, user_has_business_role, UserFeedback
from replit_auth import make_replit_blueprint, require_login
from openai_utils import (parse_user_preferences, parse_product_text,
                          generate_single_ai_response,
                          normalize_text_for_search, extract_search_intent, match_products_by_tags, smart_rank_products, generate_bulk_product_tags, generate_enriched_description)
from infobip_email import send_contact_email, send_welcome_email, send_verification_email, generate_verification_token, send_invitation_email, send_password_reset_email
from models import SavingsStatistics
# Temporarily commenting PDF imports to fix server
# from pdf_parser import process_pdf_for_business, download_pdf_from_url, normalize_product_title

# Import admin embedding blueprint
from admin_embedding_routes import admin_embedding_bp
from admin_search_routes import admin_search_bp

# Import JWT-based auth API blueprint
from auth_api import auth_api_bp, require_jwt_auth, generate_jwt_token
from app import csrf

# Import shopping list and favorites API blueprint
from shopping_api import shopping_api_bp

# Import phone authentication API blueprint
from phone_auth_api import phone_auth_bp

# Import referral API blueprint
from referral_api import referral_api_bp

# Import engagement API blueprint
from engagement_api import engagement_bp

# Import activity tracking API blueprint
from activity_api import activity_api_bp

# Disable CSRF for API endpoints (JWT-based)
csrf.exempt(auth_api_bp)
csrf.exempt(shopping_api_bp)
csrf.exempt(phone_auth_bp)
csrf.exempt(referral_api_bp)
csrf.exempt(engagement_bp)
csrf.exempt(activity_api_bp)

# Register auth API blueprint
app.register_blueprint(auth_api_bp)

# Register shopping API blueprint
app.register_blueprint(shopping_api_bp)

# Register phone auth API blueprint
app.register_blueprint(phone_auth_bp)

# Register referral API blueprint
app.register_blueprint(referral_api_bp)

# Register engagement API blueprint
app.register_blueprint(engagement_bp)

# Register activity tracking API blueprint
app.register_blueprint(activity_api_bp)


# Helper function to parse user agent string
def parse_user_agent(user_agent_string):
    """Parse user agent string to extract device type, browser, and OS"""
    if not user_agent_string:
        return {'device_type': None, 'browser': None, 'os': None}

    ua = user_agent_string.lower()

    # Detect device type
    device_type = 'desktop'
    if 'mobile' in ua or 'android' in ua and 'mobile' in ua:
        device_type = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'tablet'
    elif 'android' in ua:
        device_type = 'tablet'  # Android without mobile is likely tablet

    # Detect OS
    os_name = None
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'linux' in ua:
        os_name = 'Linux'

    # Detect browser
    browser = None
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua and 'safari' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name
    }


# Helper function to format logo URL with full URL
def format_logo_url(logo_path):
    """Format logo path to include full URL for proper serving

    Handles both:
    - S3 URLs (already absolute): https://bucket.s3.region.amazonaws.com/...
    - Legacy local paths: uploads/business_logos/...
    """
    if logo_path:
        # If it's already an absolute URL (S3), return as-is
        if logo_path.startswith('http://') or logo_path.startswith('https://'):
            return logo_path
        # Otherwise, prepend backend URL for local static files
        backend_url = os.environ.get('BACKEND_URL', 'http://localhost:5001')
        return f"{backend_url}/static/{logo_path}"
    return None


# Decorator for admin-only routes
def require_admin(f):
    """Decorator to require admin privileges for API endpoints.
    Must be used AFTER @require_jwt_auth decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = getattr(request, 'current_user_id', None)
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401

        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403

        return f(*args, **kwargs)
    return decorated


# Register Replit Auth blueprint (only if running on Replit)
replit_bp = make_replit_blueprint()
if replit_bp:
    app.register_blueprint(replit_bp, url_prefix="/auth")

# Add Google OAuth support using Flask-Dance
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_error
import os

# Create Google OAuth blueprint with explicit redirect URL
# BACKEND_URL must be set in production (Railway env var)
google_client_id = os.environ.get("AI_PIJACA_GOOGLE_CLIENT_ID")
google_client_secret = os.environ.get("AI_PIJACA_GOOGLE_CLIENT_SECRET")
backend_url_for_oauth = os.environ.get("BACKEND_URL", "http://localhost:5001")
oauth_redirect_url = f"{backend_url_for_oauth}/auth/google/authorized"

print(f"🔐 Google OAuth config: BACKEND_URL={backend_url_for_oauth}, redirect={oauth_redirect_url}")

if google_client_id and google_client_secret:
    google_bp = make_google_blueprint(
        client_id=google_client_id,
        client_secret=google_client_secret,
        scope=[
            "openid", "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_url=oauth_redirect_url)
    app.register_blueprint(google_bp, url_prefix="/auth")
    print(f"🔐 Google OAuth initialized successfully")
else:
    google_bp = None
    app.logger.warning("Google OAuth credentials not found. Google login will not be available.")

# Register admin embedding blueprint
app.register_blueprint(admin_embedding_bp)
app.register_blueprint(admin_search_bp)

# Handle CORS preflight requests globally
@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        return '', 200


# Google OAuth authorized callback (only if Google OAuth is enabled)
if google_bp:
    # Helper to get frontend URL
    def get_frontend_url():
        frontend_url = os.environ.get('FRONTEND_URL')
        if frontend_url:
            return frontend_url
        # In production (Railway), FRONTEND_URL must be set
        # Only use localhost fallback in development
        flask_env = os.environ.get('FLASK_ENV', 'development')
        if flask_env == 'production':
            app.logger.error("FRONTEND_URL not set in production! This will cause redirect issues.")
            return 'https://popust.ba'  # Hardcoded fallback for safety
        return 'http://localhost:3000'

    # Handle OAuth errors (prevents infinite redirect loop)
    @oauth_error.connect_via(google_bp)
    def google_oauth_error(blueprint, message, response):
        app.logger.error(f"Google OAuth error: message={message}, response={response}")
        # Log session state for debugging
        app.logger.error(f"Session contents at error time: {dict(session)}")
        frontend_url = get_frontend_url()
        # Redirect to frontend with error instead of restarting OAuth
        from urllib.parse import quote
        error_msg = quote(str(message) if message else "OAuth authentication failed")
        return redirect(f"{frontend_url}/prijava?error={error_msg}")

    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        frontend_url = get_frontend_url()

        try:
            if not token:
                app.logger.error("OAuth token missing")
                return redirect(f"{frontend_url}/prijava?error=no_token")

            # Get user info from Google
            resp = blueprint.session.get("/oauth2/v1/userinfo")
            if not resp.ok:
                app.logger.error(
                    f"Failed to get Google user info: {resp.status_code}")
                return redirect(f"{frontend_url}/prijava?error=userinfo_failed")

            google_info = resp.json()
            google_user_id = str(google_info.get("id"))
            email = google_info.get("email")

            if not email:
                app.logger.error("No email provided by Google OAuth")
                return redirect(f"{frontend_url}/prijava?error=no_email")

            app.logger.info(f"Google OAuth login attempt for email: {email}")

            # Check if user exists by email (primary lookup)
            user = User.query.filter_by(email=email).first()

            if not user:
                # Check if user exists by Google ID to avoid duplicate ID conflicts
                existing_user_by_id = User.query.filter_by(
                    id=google_user_id).first()
                if existing_user_by_id:
                    app.logger.warning(
                        f"User with Google ID {google_user_id} already exists but different email. Using existing user."
                    )
                    user = existing_user_by_id
                    # Update email if needed
                    if user.email != email:
                        user.email = email
                        db.session.commit()
                else:
                    # Create new user
                    app.logger.info(f"Creating new user for Google OAuth: {email}")
                    user = User(
                        id=google_user_id,
                        email=email,
                        first_name=google_info.get("given_name", ""),
                        last_name=google_info.get("family_name", ""),
                        profile_image_url=google_info.get("picture"),
                        is_verified=True,  # Google accounts are pre-verified
                        package_id=1  # Default free package
                    )
                    db.session.add(user)

                    try:
                        db.session.commit()
                        app.logger.info(f"Successfully created user: {email}")

                        # Initialize credits for new user (auto-detects admin status)
                        try:
                            from credits_service_weekly import WeeklyCreditsService
                            result = WeeklyCreditsService.initialize_user_credits(user.id)
                            app.logger.info(f"Initialized {result['balance']} credits for new user: {email} (admin={user.is_admin})")
                        except Exception as credit_error:
                            app.logger.error(f"Failed to initialize credits: {credit_error}")

                        # Send welcome email (non-blocking)
                        try:
                            send_welcome_email(user.email, user.first_name
                                               or "User")
                        except Exception as email_error:
                            app.logger.warning(
                                f"Failed to send welcome email to {email}: {email_error}"
                            )

                    except Exception as db_error:
                        db.session.rollback()
                        app.logger.error(
                            f"Database error creating user {email}: {db_error}")
                        return redirect(f"{frontend_url}/prijava?error=db_error")
            else:
                app.logger.info(f"Existing user login via Google OAuth: {email}")

            login_user(user)
            app.logger.info(f"Successfully logged in user: {email}")

            # Generate JWT token for frontend
            token = generate_jwt_token(user.id, user.email)

            # Redirect to frontend with token
            return redirect(f"{frontend_url}/auth/callback?token={token}")

        except Exception as e:
            app.logger.error(f"OAuth callback error: {e}")
            db.session.rollback()
            return redirect(f"{frontend_url}/prijava?error=callback_error")


# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True


# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def product_to_dict(product, include_price_history=True):
    """Standardized product serializer that returns complete product schema with nested business data"""
    from datetime import datetime
    from models import ProductPriceHistory

    # Helper function to safely get values from either object or dictionary
    def safe_get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        else:
            return getattr(obj, key, default)

    # Get basic product data safely
    base_price = safe_get(product, 'base_price')
    discount_price = safe_get(product, 'discount_price')
    expires_val = safe_get(product, 'expires')

    # Normalize expiry date first (needed for has_discount check)
    expires_iso = None
    expires_date = None
    if expires_val:
        if isinstance(expires_val, str):
            try:
                # Try parsing date string
                expires_date = datetime.strptime(expires_val,
                                                 '%Y-%m-%d').date()
                expires_iso = expires_date.isoformat()
            except ValueError:
                try:
                    # Try parsing datetime string
                    expires_date = datetime.fromisoformat(
                        expires_val.replace('Z', '+00:00')).date()
                    expires_iso = expires_date.isoformat()
                except:
                    expires_iso = None
        elif hasattr(expires_val, 'isoformat'):
            expires_date = expires_val if isinstance(expires_val, date) else expires_val.date() if hasattr(expires_val, 'date') else None
            expires_iso = expires_val.isoformat()

    # Check if discount has expired
    is_expired = expires_date is not None and date.today() > expires_date

    # Calculate discount information - only show discount if not expired
    has_discount = (discount_price is not None
                    and base_price is not None
                    and float(discount_price) < float(base_price)
                    and not is_expired)

    discount_percentage = 0
    if has_discount:
        discount_percentage = round(
            ((float(base_price) - float(discount_price)) /
             float(base_price)) * 100)

    # Get business information
    business_data = {
        'id': None,
        'name': 'Nepoznat biznis',
        'logo_path': None,
        'city': None
    }

    # Handle business data for objects
    if hasattr(product, 'business') and safe_get(product, 'business'):
        business = safe_get(product, 'business')
        business_data = {
            'id': safe_get(business, 'id'),
            'name': safe_get(business, 'name') or 'Nepoznat biznis',
            'logo_path': safe_get(business, 'logo_path'),
            'city': safe_get(business, 'city')
        }
    # Handle business data from joined queries (both dict and object)
    elif safe_get(product, 'business_name'):
        business_data = {
            'id': safe_get(product, 'business_id'),
            'name': safe_get(product, 'business_name'),
            'logo_path': safe_get(product, 'logo_path'),
            'city': safe_get(product, 'business_city')
        }

    # Get price history data for "was on sale" feature
    price_history_data = None
    product_id = safe_get(product, 'id')

    if include_price_history and product_id and not has_discount:
        # Only show historical price if product is NOT currently on discount
        # First check ProductPriceHistory table for lowest historical discount price
        lowest_history = ProductPriceHistory.query.filter(
            ProductPriceHistory.product_id == product_id,
            ProductPriceHistory.discount_price.isnot(None)
        ).order_by(ProductPriceHistory.discount_price.asc()).first()

        # Count total price history entries for this product
        history_count = ProductPriceHistory.query.filter(
            ProductPriceHistory.product_id == product_id
        ).count()

        if lowest_history and lowest_history.discount_price:
            # We have historical data
            price_history_data = {
                'lowest_price': float(lowest_history.discount_price),
                'recorded_at': lowest_history.recorded_at.isoformat() if lowest_history.recorded_at else None,
                'potential_savings': round(float(base_price) - float(lowest_history.discount_price), 2) if base_price else 0,
                'history_count': history_count
            }
        elif discount_price and is_expired:
            # Fallback: if discount just expired, use that as "was on sale" price
            price_history_data = {
                'lowest_price': float(discount_price),
                'recorded_at': expires_iso,
                'potential_savings': round(float(base_price) - float(discount_price), 2) if base_price and discount_price else 0,
                'history_count': 1
            }
        elif history_count > 0:
            # Product has price history but no discount data - still show the count
            price_history_data = {
                'history_count': history_count
            }

    # If discount is expired, don't show discount info - product becomes regular
    return {
        'id': safe_get(product, 'id'),
        'title': safe_get(product, 'title'),
        'image_path': safe_get(product, 'image_path'),
        'base_price': float(base_price) if base_price else 0,
        'discount_price': float(discount_price) if has_discount else None,
        'expires': expires_iso if has_discount else None,
        'has_discount': has_discount,
        'discount_percentage': discount_percentage,
        'city': safe_get(product, 'city'),
        'category': safe_get(product, 'category'),
        'business': business_data,
        'enriched_description': safe_get(product, 'enriched_description'),
        'price_history': price_history_data,
    }


# Async product enrichment (tags + descriptions)
def schedule_async_product_enrichment(product_ids: list[int]) -> None:
    """
    Schedule AI enrichment (tags + descriptions) to run in the background

    Args:
        product_ids: List of product IDs to enrich
    """
    import threading
    from flask import current_app

    def run_enrichment_in_background(app, product_ids):
        with app.app_context():
            try:
                app.logger.info(f"Starting background AI enrichment for {len(product_ids)} products")

                # Fetch products
                products = Product.query.filter(Product.id.in_(product_ids)).all()
                if not products:
                    app.logger.warning("No products found for enrichment")
                    return

                # Batch generate tags for all products
                try:
                    app.logger.info(f"Generating AI tags for {len(products)} products...")
                    products_data = [{'title': p.title, 'category': p.category} for p in products]
                    all_tags = generate_bulk_product_tags(products_data)

                    # Update products with generated tags
                    for idx, product in enumerate(products):
                        if idx < len(all_tags) and all_tags[idx]:
                            product.tags = all_tags[idx]

                    db.session.commit()
                    app.logger.info(f"Successfully generated tags for {len(products)} products")
                except Exception as e:
                    app.logger.error(f"Tag generation failed: {e}")

                # Generate enriched descriptions for each product
                try:
                    app.logger.info(f"Generating enriched descriptions for {len(products)} products...")
                    for product in products:
                        try:
                            enriched_desc = generate_enriched_description(
                                product_title=product.title,
                                category=product.category
                            )
                            product.enriched_description = enriched_desc
                        except Exception as e:
                            app.logger.warning(f"Failed to generate description for product {product.id}: {e}")

                    db.session.commit()
                    app.logger.info(f"Successfully generated enriched descriptions")
                except Exception as e:
                    app.logger.error(f"Enriched description generation failed: {e}")

                app.logger.info(f"Background AI enrichment complete for {len(products)} products")
            except Exception as e:
                app.logger.error(f"Background enrichment failed: {e}", exc_info=True)

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_enrichment_in_background,
        args=(app, product_ids),
        daemon=True
    )
    thread.start()
    app.logger.info(f"Scheduled background AI enrichment for {len(product_ids)} products")


# Helper function to check daily query limit
def check_query_limit(user):
    if not user.package:
        return False

    today = date.today()
    today_searches = db.session.query(UserSearch).filter(
        UserSearch.user_id == user.id,
        db.func.date(UserSearch.created_at) == today).count()

    return today_searches < user.package.daily_limit


# Helper function to get dynamic chat examples
def get_chat_examples():
    # Static search examples - no dynamic content, no HTML formatting
    return [{
        "user":
        "Gdje mogu pronaći najjeftiniju piletinu?",
        "assistant":
        "🐔 Pronašao sam nekoliko odličnih ponuda za piletinu! Pogledajte rezultate da vidite trenutne cijene i popuste u vašem gradu."
    }]


def save_last_successful_search(query, response):
    """DISABLED - No longer saving dynamic search examples (kept static)"""
    pass


# Email verification required decorator
def verification_required(f):
    """Decorator to require email verification for sensitive actions"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and not current_user.is_verified and not current_user.is_admin:
            if request.is_json:
                return jsonify({
                    'error':
                    'Molimo vas prvo verifikujte vaš email račun za pristup ovoj funkciji.',
                    'verification_required': True
                }), 403
            else:
                flash(
                    'Molimo vas prvo verifikujte vaš email račun za pristup ovoj funkciji.',
                    'warning')
                return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


# Access control decorator for business management
def business_role_required(min_role='staff'):
    """Decorator to check if user has required role for business"""

    def decorator(f):

        def decorated_function(*args, **kwargs):
            # Get business_id from URL parameters
            business_id = kwargs.get('business_id')
            if not business_id:
                business_id = request.view_args.get('business_id')

            if not business_id:
                flash('Business ID not found.', 'error')
                return redirect(url_for('business_dashboard'))

            # Check if user has required role
            if not user_has_business_role(current_user.id, business_id,
                                          min_role):
                flash('Nemate dozvolu za pristup ovom biznisu.', 'error')
                return redirect(url_for('business_dashboard'))

            return f(*args, **kwargs)

        decorated_function.__name__ = f.__name__
        return decorated_function

    return decorator


# Helper functions for search limiting
def get_search_counts(user=None):
    """Get remaining search counts for logged-in users or anonymous sessions"""
    today = date.today()

    if user and user.is_authenticated:
        # For logged-in users, use credit system
        from credits_service_weekly import WeeklyCreditsService

        balance = WeeklyCreditsService.get_balance(user.id)
        current_balance = balance['total_credits']

        # For admins or users with high balances (>100), don't show weekly limit
        # Just show their total balance
        if getattr(user, 'is_admin', False) or current_balance > 100:
            return {
                'weekly_limit': current_balance,  # Show balance as limit for display
                'used_this_week': 0,
                'remaining': current_balance,
                'regular_credits': balance['regular_credits'],
                'extra_credits': balance['extra_credits'],
                'next_reset_date': balance['next_reset_date'].isoformat(),
                'user_type': 'logged_in',
                'is_unlimited': True
            }
        else:
            # For regular users, show standard weekly limit
            from credits_service_weekly import REGULAR_USER_WEEKLY_CREDITS
            weekly_limit = REGULAR_USER_WEEKLY_CREDITS
            return {
                'weekly_limit': weekly_limit,
                'used_this_week': max(0, weekly_limit - balance['regular_credits']),
                'remaining': max(0, current_balance),
                'regular_credits': balance['regular_credits'],
                'extra_credits': balance['extra_credits'],
                'next_reset_date': balance['next_reset_date'].isoformat(),
                'user_type': 'logged_in',
                'is_unlimited': False
            }
    else:
        # For anonymous users, use session tracking
        session_key = 'daily_searches'
        today_str = today.isoformat()

        # Initialize or get session search data
        searches_data = session.get(session_key, {})

        # Clean old dates and get today's count
        if not isinstance(searches_data, dict):
            searches_data = {}

        # Remove old entries (keep only today)
        searches_data = {
            date_str: count
            for date_str, count in searches_data.items()
            if date_str == today_str
        }

        today_searches = searches_data.get(today_str, 0)
        anonymous_limit = 1

        return {
            'daily_limit': anonymous_limit,
            'used_today': today_searches,
            'remaining': max(0, anonymous_limit - today_searches),
            'user_type': 'anonymous'
        }


def increment_search_count(user=None):
    """Increment search count for the user or session"""
    today_str = date.today().isoformat()

    if user and user.is_authenticated:
        # For logged-in users, searches are tracked in UserSearch table
        # No need to increment here as it's done when creating UserSearch record
        pass
    else:
        # For anonymous users, increment session counter
        session_key = 'daily_searches'
        searches_data = session.get(session_key, {})

        if not isinstance(searches_data, dict):
            searches_data = {}

        # Clean old dates and increment today's count
        searches_data = {
            date_str: count
            for date_str, count in searches_data.items()
            if date_str == today_str
        }
        searches_data[today_str] = searches_data.get(today_str, 0) + 1
        session[session_key] = searches_data
        session.permanent = True  # Make session persistent across browser sessions


def can_search(user=None):
    """Check if user or session can perform a search"""
    counts = get_search_counts(user)
    return counts['remaining'] > 0


# Health check endpoint for Railway/deployment
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'ai-market-backend'}), 200


# Homepage route - API info endpoint
@app.route('/')
def index():
    return jsonify({
        'service': 'popust.ba-api',
        'status': 'running',
        'version': '2.0',
        'docs': '/api'
    })


# API endpoint to get search counts
@app.route('/api/search-counts')
def api_search_counts():
    user = current_user if current_user.is_authenticated else None
    search_counts = get_search_counts(user)
    return jsonify(search_counts)


# API endpoint to get savings statistics for marketing banner
@app.route('/api/savings-stats')
def api_savings_stats():
    stats = SavingsStatistics.get_or_create_stats()

    # Calculate average savings per product if we have data
    average_savings = 0
    if stats.total_products_served > 0:
        average_savings = stats.total_savings_amount / stats.total_products_served

    return jsonify({
        'total_savings': round(stats.total_savings_amount, 2),
        'total_products': stats.total_products_served,
        'average_savings': round(average_savings, 2)
    })


# API endpoint for single product
@app.route('/api/products/<int:product_id>')
def api_product_detail(product_id):
    """Get single product details"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Use standardized product serializer that includes price_history
    return jsonify(product_to_dict(product))


# API endpoint for product price history
@app.route('/api/products/<int:product_id>/price-history')
def api_product_price_history(product_id):
    """Get price history for a product"""
    from models import ProductPriceHistory

    history = ProductPriceHistory.query.filter_by(product_id=product_id)\
        .order_by(ProductPriceHistory.recorded_at.desc())\
        .limit(10)\
        .all()

    return jsonify([{
        'base_price': h.base_price,
        'discount_price': h.discount_price,
        'recorded_at': h.recorded_at.isoformat() if h.recorded_at else None
    } for h in history])


# API endpoint for products list
# Category mapping: UI category ID -> list of DB category names
CATEGORY_MAPPING = {
    'meso': ['Meso i mesni proizvodi', 'Delikates'],
    'mlijeko': ['Mliječni proizvodi'],
    'pica': ['Pića'],
    'voce_povrce': ['Voće i povrće'],
    'kuhinja': ['Namirnice'],  # Ulje, brašno, začini, tjestenina
    'ves': ['Kućne potrepštine'],  # Will need sub-filtering
    'ciscenje': ['Kućne potrepštine'],  # Will need sub-filtering
    'higijena': ['Higijena'],
    'slatkisi': ['Slatkiši', 'Grickalice'],
    'kafa': ['Namirnice'],  # Kafa/čaj subset - will need sub-filtering
    'smrznuto': ['Smrznuto'],
    'pekara': ['Pekara'],
    'ljubimci': ['Kućni ljubimci'],
    'bebe': ['Higijena'],  # Baby products subset
}

@app.route('/api/products')
def api_products():
    """API endpoint for products listing with pagination.

    Credits: Page 1 is free, pages 2+ cost 3 credits.
    If user doesn't have enough credits, returns credits_required error.
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 24))
        category = request.args.get('category')
        business_id = request.args.get('business')
        stores = request.args.get('stores')  # Comma-separated store IDs
        search = request.args.get('search')
        sort = request.args.get('sort', 'discount_desc')

        # Credit check for pages beyond page 1
        PRODUCTS_PAGE_COST = 3
        credits_remaining = None
        user = None
        can_paginate = True  # Whether user has enough credits for next page

        # Try to get authenticated user (for any page, to show credit status)
        from auth_api import decode_jwt_token
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
                payload = decode_jwt_token(token)
                if payload:
                    user = User.query.get(payload.get('user_id'))
            except Exception:
                pass

        if page > 1:
            if not auth_header:
                return jsonify({
                    'error': 'credits_required',
                    'message': 'Morate biti prijavljeni da biste pregledali više proizvoda.',
                    'credits_needed': PRODUCTS_PAGE_COST,
                    'credits_remaining': 0
                }), 401

            if not user:
                return jsonify({
                    'error': 'credits_required',
                    'message': 'Morate biti prijavljeni da biste pregledali više proizvoda.',
                    'credits_needed': PRODUCTS_PAGE_COST,
                    'credits_remaining': 0
                }), 401

            # Check and deduct credits
            from agents_api import check_and_deduct_credits
            success, message, credits_remaining = check_and_deduct_credits(user, PRODUCTS_PAGE_COST)

            if not success:
                # Calculate remaining credits for response
                weekly_remaining = user.weekly_credits - user.weekly_credits_used
                total_remaining = weekly_remaining + user.extra_credits

                return jsonify({
                    'error': 'insufficient_credits',
                    'message': 'Nemate dovoljno kredita za pregled ove stranice.',
                    'credits_needed': PRODUCTS_PAGE_COST,
                    'credits_remaining': total_remaining,
                    'earn_credits_message': 'Zaradite kredite tako što ćete ostaviti komentar (+5) ili glasati za proizvode (+2). Pomozite drugima da donesu bolju odluku pri kupovini!'
                }), 402  # Payment Required
        elif user:
            # For page 1, just get user's credits for display (no deduction)
            from agents_api import get_available_credits
            credits_remaining = get_available_credits(user)

        # Determine if user can paginate (has enough credits for page 2+)
        if user and credits_remaining is not None:
            can_paginate = credits_remaining >= PRODUCTS_PAGE_COST

        # Base query - show all products (expired discounts become regular products)
        query = Product.query.join(Business)

        # Filter out products with base_price = 0 unless they have an active discount
        today = date.today()
        query = query.filter(
            db.or_(
                # Products with base_price > 0
                Product.base_price > 0,
                # OR products with base_price = 0 but have active discount
                db.and_(
                    Product.base_price == 0,
                    Product.discount_price.isnot(None),
                    Product.discount_price > 0,
                    db.or_(Product.expires.is_(None), Product.expires >= today)
                )
            )
        )

        # Apply filters
        if category:
            # First try to match by category_group (our new simplified categories)
            query = query.filter(Product.category_group == category)
        if stores:
            # Filter by multiple store IDs
            store_ids = [int(s) for s in stores.split(',') if s.strip().isdigit()]
            if store_ids:
                query = query.filter(Product.business_id.in_(store_ids))
        elif business_id:
            # Legacy single business filter
            query = query.filter(Product.business_id == int(business_id))
        if search:
            query = query.filter(Product.title.ilike(f'%{search}%'))

        # Apply sorting
        if sort == 'discount_desc':
            # Sort by discount percentage (highest first)
            # Calculate discount as (base_price - discount_price) / base_price
            # Products with discount_price get sorted by percentage, others go to end
            # Only count discount if not expired (expires is null or expires >= today)
            query = query.order_by(
                db.case(
                    (db.and_(
                        Product.base_price > 0,
                        Product.discount_price.isnot(None),
                        Product.discount_price < Product.base_price,
                        db.or_(Product.expires.is_(None), Product.expires >= today)
                    ),
                     (Product.base_price - Product.discount_price) / Product.base_price),
                    else_=0
                ).desc()
            )
        elif sort == 'price_asc':
            # Sort by effective price (discount_price if available, else base_price)
            query = query.order_by(
                db.case(
                    (Product.discount_price.isnot(None), Product.discount_price),
                    else_=Product.base_price
                ).asc()
            )
        elif sort == 'price_desc':
            # Sort by effective price (discount_price if available, else base_price)
            query = query.order_by(
                db.case(
                    (Product.discount_price.isnot(None), Product.discount_price),
                    else_=Product.base_price
                ).desc()
            )
        elif sort == 'newest':
            query = query.order_by(Product.created_at.desc())
        else:
            # Default: discount descending
            # Only count discount if not expired (expires is null or expires >= today)
            query = query.order_by(
                db.case(
                    (db.and_(
                        Product.base_price > 0,
                        Product.discount_price.isnot(None),
                        Product.discount_price < Product.base_price,
                        db.or_(Product.expires.is_(None), Product.expires >= today)
                    ),
                     (Product.base_price - Product.discount_price) / Product.base_price),
                    else_=0
                ).desc()
            )

        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        products = []
        for product in paginated.items:
            products.append(product_to_dict(product))

        # Calculate category counts (for the UI filter) - using category_group
        # Also filter out zero-price products without active discounts
        category_counts_query = db.session.query(
            Product.category_group,
            func.count(Product.id)
        ).join(Business).filter(
            Product.category_group.isnot(None),
            db.or_(
                Product.base_price > 0,
                db.and_(
                    Product.base_price == 0,
                    Product.discount_price.isnot(None),
                    Product.discount_price > 0,
                    db.or_(Product.expires.is_(None), Product.expires >= today)
                )
            )
        )

        if stores:
            store_ids = [int(s) for s in stores.split(',') if s.strip().isdigit()]
            if store_ids:
                category_counts_query = category_counts_query.filter(Product.business_id.in_(store_ids))
        elif business_id:
            category_counts_query = category_counts_query.filter(Product.business_id == int(business_id))

        category_counts_result = category_counts_query.group_by(Product.category_group).all()

        # Convert to dict
        category_counts = {cat: count for cat, count in category_counts_result if cat}

        response_data = {
            'products': products,
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'total_pages': paginated.pages,
            'category_counts': category_counts,
            'credits_cost': PRODUCTS_PAGE_COST if page > 1 else 0,
            'can_paginate': can_paginate
        }

        # Include credits remaining if user is authenticated
        if credits_remaining is not None:
            response_data['credits_remaining'] = credits_remaining

        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error in products API: {e}")
        return jsonify({'error': 'Failed to load products'}), 500


# API endpoint for businesses list
@app.route('/api/businesses')
def api_businesses():
    """API endpoint for businesses listing - only returns businesses with products"""
    try:
        # Check if we want all businesses (for store filter) or only those with products
        include_all = request.args.get('all', 'false').lower() == 'true'

        if include_all:
            # Return all active businesses regardless of products
            businesses = Business.query.filter(Business.status == 'active').order_by(Business.name).all()
        else:
            # Only return businesses that have at least one product (legacy behavior)
            businesses = db.session.query(Business).join(Product).filter(
                Business.status == 'active'
            ).distinct().all()

        result = []
        for business in businesses:
            result.append({
                'id': business.id,
                'name': business.name,
                'city': business.city,
                'logo_path': format_logo_url(business.logo_path),
                'contact_phone': business.contact_phone,
                'google_link': business.google_link
            })

        return jsonify({'businesses': result})

    except Exception as e:
        app.logger.error(f"Error in businesses API: {e}")
        return jsonify({'error': 'Failed to load businesses'}), 500


@app.route('/api/store-discounts-freshness')
def api_store_discounts_freshness():
    """Get the latest discount expiration date per store for freshness ticker"""
    try:
        today = date.today()

        # Query to get each store's latest non-expired discount expiration date and count
        query = db.session.query(
            Business.id,
            Business.name,
            Business.logo_path,
            func.max(Product.expires).label('latest_expires'),
            func.count(Product.id).label('discount_count')
        ).join(Product, Business.id == Product.business_id).filter(
            Business.status == 'active',
            Product.discount_price.isnot(None),
            Product.expires >= today
        ).group_by(Business.id, Business.name, Business.logo_path).all()

        stores = []
        for row in query:
            stores.append({
                'id': row.id,
                'name': row.name,
                'logo': format_logo_url(row.logo_path),
                'latest_expires': row.latest_expires.isoformat() if row.latest_expires else None,
                'discount_count': row.discount_count
            })

        # Sort by latest_expires (soonest first)
        stores.sort(key=lambda x: x['latest_expires'] or '9999-12-31')

        return jsonify({'stores': stores})

    except Exception as e:
        app.logger.error(f"Error in store discounts freshness API: {e}")
        return jsonify({'error': 'Failed to load store freshness data'}), 500


# API endpoint to create a new business
@app.route('/api/businesses', methods=['POST'])
@require_jwt_auth
@require_admin
def api_create_business():
    """Create a new business - admin only"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        name = (data.get('name') or '').strip()
        city = (data.get('city') or '').strip()
        contact_phone = (data.get('contact_phone') or '').strip() or None
        google_link = (data.get('google_link') or '').strip() or None

        if not name:
            return jsonify({'success': False, 'error': 'Naziv radnje je obavezan'}), 400

        if not city:
            return jsonify({'success': False, 'error': 'Grad je obavezan'}), 400

        # Check if business with same name and city already exists
        existing = Business.query.filter_by(name=name, city=city).first()
        if existing:
            return jsonify({'success': False, 'error': 'Radnja sa istim nazivom već postoji u tom gradu'}), 400

        # Create new business
        business = Business(
            name=name,
            city=city,
            contact_phone=contact_phone,
            google_link=google_link,
            status='active'
        )

        db.session.add(business)
        db.session.commit()

        app.logger.info(f"Created new business: {name} in {city} (ID: {business.id})")

        return jsonify({
            'success': True,
            'message': 'Radnja uspješno kreirana',
            'business': {
                'id': business.id,
                'name': business.name,
                'city': business.city
            }
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating business: {e}")
        return jsonify({'success': False, 'error': 'Greška prilikom kreiranja radnje'}), 500


# Public API endpoint for business page (no auth required)
@app.route('/api/radnja/<int:business_id>')
def api_public_business_page(business_id):
    """Public API endpoint for business page with products"""
    try:
        business = Business.query.filter_by(id=business_id, status='active').first()

        if not business:
            return jsonify({'error': 'Radnja nije pronađena'}), 404

        # Get active products with discounts
        products = Product.query.filter(
            Product.business_id == business_id,
            Product.discount_price.isnot(None),
            Product.discount_price < Product.base_price
        ).order_by(Product.created_at.desc()).limit(20).all()

        return jsonify({
            'business': {
                'id': business.id,
                'name': business.name,
                'city': business.city,
                'logo_path': f"/static/{business.logo_path}" if business.logo_path else None,
                'contact_phone': business.contact_phone,
                'google_link': business.google_link,
                'product_count': business.products.count(),
                'views': business.views
            },
            'products': [{
                'id': p.id,
                'title': p.title,
                'base_price': p.base_price,
                'discount_price': p.discount_price,
                'discount_percentage': p.discount_percentage,
                'image_path': p.image_path,
                'category': p.category,
                'expires': p.expires.isoformat() if p.expires else None
            } for p in products],
            'has_more': business.products.count() > 20
        })

    except Exception as e:
        app.logger.error(f"Error in public business page: {e}")
        return jsonify({'error': 'Greška pri učitavanju radnje'}), 500


@app.route('/api/radnja/<int:business_id>/products')
def api_public_business_products(business_id):
    """Public API endpoint for paginated business products"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20

        business = Business.query.filter_by(id=business_id, status='active').first()
        if not business:
            return jsonify({'error': 'Radnja nije pronađena'}), 404

        # Get products with pagination
        pagination = Product.query.filter(
            Product.business_id == business_id,
            Product.discount_price.isnot(None),
            Product.discount_price < Product.base_price
        ).order_by(Product.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'products': [{
                'id': p.id,
                'title': p.title,
                'base_price': p.base_price,
                'discount_price': p.discount_price,
                'discount_percentage': p.discount_percentage,
                'image_path': p.image_path,
                'category': p.category,
                'expires': p.expires.isoformat() if p.expires else None
            } for p in pagination.items],
            'has_more': pagination.has_next,
            'page': page,
            'total': pagination.total
        })

    except Exception as e:
        app.logger.error(f"Error in business products: {e}")
        return jsonify({'error': 'Greška pri učitavanju proizvoda'}), 500


# API endpoint for single business
@app.route('/api/businesses/<int:business_id>')
@require_jwt_auth
def api_business_detail(business_id):
    """API endpoint for single business details"""
    try:
        business = Business.query.get_or_404(business_id)

        result = {
            'id': business.id,
            'name': business.name,
            'city': business.city,
            'logo_path': format_logo_url(business.logo_path),
            'contact_phone': business.contact_phone,
            'google_link': business.google_link,
            'pdf_url': business.pdf_url,
            'last_sync': business.last_sync.isoformat() if business.last_sync else None
        }

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in business detail API: {e}")
        return jsonify({'error': 'Failed to load business'}), 500


# API endpoint for business products
@app.route('/api/businesses/<int:business_id>/products')
@require_jwt_auth
def api_business_products(business_id):
    """API endpoint for business products listing with pagination"""
    try:
        business = Business.query.get_or_404(business_id)

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '', type=str).strip()
        sort = request.args.get('sort', 'created_at_desc', type=str)

        # Ensure per_page is within reasonable bounds
        per_page = min(per_page, 100)  # Max 100 items per page

        # Build base query with search filter
        from models import ProductEmbedding
        base_query = Product.query.filter_by(business_id=business_id)

        if search:
            base_query = base_query.filter(Product.title.ilike(f'%{search}%'))

        # Get total count
        total_count = base_query.count()

        # Calculate pagination
        total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
        offset = (page - 1) * per_page

        # Get paginated products with embeddings
        products_query = db.session.query(Product, ProductEmbedding).outerjoin(
            ProductEmbedding, Product.id == ProductEmbedding.product_id
        ).filter(Product.business_id == business_id)

        if search:
            products_query = products_query.filter(Product.title.ilike(f'%{search}%'))

        # Apply sorting
        sort_mapping = {
            'created_at_desc': Product.created_at.desc(),
            'created_at_asc': Product.created_at.asc(),
            'views_desc': Product.views.desc().nullslast(),
            'views_asc': Product.views.asc().nullsfirst(),
            'price_desc': Product.discount_price.desc().nullslast(),
            'price_asc': Product.discount_price.asc().nullsfirst(),
            'title_asc': Product.title.asc(),
            'title_desc': Product.title.desc(),
        }

        # For discount sorting, we need to calculate discount percentage
        if sort == 'discount_desc':
            # Sort by discount percentage (highest first)
            products_query = products_query.order_by(
                db.case(
                    (db.and_(Product.discount_price != None, Product.base_price > 0),
                     ((Product.base_price - Product.discount_price) / Product.base_price * 100)),
                    else_=0
                ).desc()
            )
        elif sort == 'discount_asc':
            # Sort by discount percentage (lowest first)
            products_query = products_query.order_by(
                db.case(
                    (db.and_(Product.discount_price != None, Product.base_price > 0),
                     ((Product.base_price - Product.discount_price) / Product.base_price * 100)),
                    else_=0
                ).asc()
            )
        elif sort in sort_mapping:
            products_query = products_query.order_by(sort_mapping[sort])
        else:
            products_query = products_query.order_by(Product.created_at.desc())

        products_query = products_query.limit(per_page).offset(offset).all()

        products_list = []
        for product, embedding in products_query:
            # Calculate discount percentage
            discount_percentage = 0
            if product.discount_price and product.base_price:
                discount_percentage = round(
                    ((product.base_price - product.discount_price) / product.base_price) * 100
                )

            products_list.append({
                'id': product.id,
                'title': product.title,
                'base_price': product.base_price,
                'discount_price': product.discount_price,
                'discount_percentage': discount_percentage,
                'category': product.category,
                'tags': product.tags if product.tags else [],
                'image_path': product.image_path,
                'expires': product.expires.isoformat() if product.expires else None,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'views': product.views if hasattr(product, 'views') else 0,
                'is_expired': product.is_expired if hasattr(product, 'is_expired') else False,
                'enriched_description': product.enriched_description,
                'embedding_text': embedding.embedding_text if embedding else None,
                'has_embedding': embedding is not None
            })

        return jsonify({
            'success': True,
            'products': products_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })

    except Exception as e:
        app.logger.error(f"Error in business products API: {e}")
        return jsonify({'error': 'Failed to load products'}), 500


# API endpoint for admin to view all businesses
@app.route('/api/businesses/my')
@require_jwt_auth
def api_my_businesses():
    """API endpoint for admin to view all businesses they can manage"""
    try:
        # Get user from JWT token
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # For admin, return all businesses
        if user.is_admin:
            businesses = Business.query.all()
        else:
            # For non-admin, return only businesses where user has a role
            memberships = BusinessMembership.query.filter_by(
                user_id=user.id
            ).all()
            business_ids = [m.business_id for m in memberships]
            businesses = Business.query.filter(Business.id.in_(business_ids)).all() if business_ids else []

        result = []
        for business in businesses:
            # Get product count
            product_count = Product.query.filter_by(business_id=business.id).count()

            # Get count of products with AI category assigned
            categorized_count = Product.query.filter(
                Product.business_id == business.id,
                Product.category_group.isnot(None),
                Product.category_group != ''
            ).count()

            # Get total views for all products
            total_views = db.session.query(db.func.sum(Product.views)).filter_by(
                business_id=business.id
            ).scalar() or 0

            # Get user role for this business
            user_role = None
            if user.is_admin:
                user_role = 'admin'
            else:
                membership = BusinessMembership.query.filter_by(
                    user_id=user.id,
                    business_id=business.id
                ).first()
                if membership:
                    user_role = membership.role

            result.append({
                'id': business.id,
                'name': business.name,
                'city': business.city,
                'logo_path': format_logo_url(business.logo_path),
                'contact_phone': business.contact_phone,
                'google_link': business.google_link,
                'pdf_url': business.pdf_url,
                'last_sync': business.last_sync.isoformat() if business.last_sync else None,
                'product_count': product_count,
                'categorized_count': categorized_count,
                'views': total_views,
                'user_role': user_role,
                'status': business.status
            })

        return jsonify({
            'success': True,
            'businesses': result
        })

    except Exception as e:
        app.logger.error(f"Error in my businesses API: {e}")
        return jsonify({'error': 'Failed to load businesses'}), 500


# API endpoint for uploading business logo
@app.route('/api/businesses/<int:business_id>/logo', methods=['POST'])
@require_jwt_auth
def api_upload_business_logo(business_id):
    """Upload business logo with JWT auth to S3"""
    try:
        import boto3
        import uuid
        import re

        business = Business.query.get_or_404(business_id)

        # Check if file was uploaded
        if 'logo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nijedan fajl nije odabran'
            }), 400

        file = request.files['logo']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nijedan fajl nije odabran'
            }), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

        if file_extension not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'Dozvoljen tip fajla: {", ".join(allowed_extensions)}'
            }), 400

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'eu-central-1')
        )

        bucket_name = os.environ.get('AWS_S3_BUCKET', 'aipijaca')

        # Delete old logo from S3 if it exists
        if business.logo_path and 'amazonaws.com' in business.logo_path:
            try:
                match = re.search(r'amazonaws\.com/(.+)$', business.logo_path)
                if match:
                    old_s3_key = match.group(1)
                    app.logger.info(f"Deleting old logo from S3: {old_s3_key}")
                    s3_client.delete_object(Bucket=bucket_name, Key=old_s3_key)
            except Exception as e:
                app.logger.warning(f"Failed to delete old logo from S3: {e}")

        # Generate unique filename
        unique_filename = f"{business_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        s3_key = f"assets/images/business_logos/{business_id}/{unique_filename}"

        # Upload to S3
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type
            }
        )

        # Generate S3 URL
        logo_url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'eu-central-1')}.amazonaws.com/{s3_key}"

        # Update business record
        business.logo_path = logo_url
        db.session.commit()

        app.logger.info(f"Logo uploaded for business {business_id}: {logo_url}")

        return jsonify({'success': True, 'logo_path': logo_url})

    except Exception as e:
        app.logger.error(f"Error uploading logo: {e}")
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom postavljanja loga'
        }), 500


# API endpoint for editing business
@app.route('/api/businesses/<int:business_id>', methods=['POST'])
@require_jwt_auth
def api_edit_business(business_id):
    """Edit business with JWT auth"""
    try:
        business = Business.query.get_or_404(business_id)
        data = request.get_json() if request.is_json else request.form

        # Update business fields
        if 'name' in data:
            business.name = data['name'].strip()
        if 'contact_phone' in data:
            business.contact_phone = data['contact_phone']
        if 'city' in data:
            business.city = data['city'].strip()

        google_link = data.get('google_link', business.google_link)
        if google_link and google_link.strip():
            google_link = google_link.strip()
            if not (google_link.startswith('http://') or google_link.startswith('https://')):
                return jsonify({
                    'success': False,
                    'error': 'Google link mora počinjati sa http:// ili https://'
                }), 400
            business.google_link = google_link
        else:
            business.google_link = None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Biznis je uspešno ažuriran',
            'business': {
                'id': business.id,
                'name': business.name,
                'contact_phone': business.contact_phone,
                'city': business.city,
                'google_link': business.google_link
            }
        })

    except Exception as e:
        app.logger.error(f"Error editing business: {e}")
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom ažuriranja biznisa'
        }), 500


@app.route('/api/businesses/<int:business_id>', methods=['DELETE'])
@require_jwt_auth
def api_delete_business(business_id):
    """Delete a business and all its products with JWT auth"""
    try:
        business = Business.query.get_or_404(business_id)

        # Check if user has permission to delete (must be owner or admin)
        user_id = request.user_id
        user = User.query.get(user_id)

        if not user:
            return jsonify({'success': False, 'error': 'Korisnik nije pronađen'}), 404

        # Check permissions - admin or business owner
        is_admin = user.is_admin
        membership = BusinessMembership.query.filter_by(
            business_id=business_id,
            user_id=user_id,
            is_active=True
        ).first()

        is_owner = membership and membership.role == 'owner'

        if not is_admin and not is_owner:
            return jsonify({
                'success': False,
                'error': 'Nemate dozvolu za brisanje ove radnje'
            }), 403

        business_name = business.name

        # Delete all products associated with this business (CASCADE handles related records)
        Product.query.filter_by(business_id=business_id).delete()

        # Delete all business memberships
        BusinessMembership.query.filter_by(business_id=business_id).delete()

        # Delete any invitations
        if hasattr(BusinessInvitation, 'query'):
            BusinessInvitation.query.filter_by(business_id=business_id).delete()

        # Delete the business
        db.session.delete(business)
        db.session.commit()

        app.logger.info(f"Business '{business_name}' (ID: {business_id}) deleted by user {user_id}")

        return jsonify({
            'success': True,
            'message': f'Radnja "{business_name}" je uspješno obrisana'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting business: {e}")
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom brisanja radnje'
        }), 500


# API endpoint for inviting users to business
@app.route('/api/businesses/<int:business_id>/invite', methods=['POST'])
@require_jwt_auth
def api_invite_business_member(business_id):
    """Invite user to business with JWT auth"""
    try:
        business = Business.query.get_or_404(business_id)
        data = request.get_json() if request.is_json else request.form

        email = data.get('email', '').strip().lower()
        role = data.get('role', 'staff')

        # Validate input
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Molimo unesite valjan email'}), 400

        if role not in ['owner', 'manager', 'staff']:
            return jsonify({'success': False, 'error': 'Nevažeća uloga'}), 400

        # Check if user exists and is already a member
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            existing_membership = BusinessMembership.query.filter_by(
                business_id=business_id,
                user_id=existing_user.id
            ).first()

            if existing_membership and existing_membership.is_active:
                return jsonify({'success': False, 'error': 'Korisnik je već član ovog biznisa'}), 400

        # Create invitation
        invitation = BusinessInvitation(
            business_id=business_id,
            email=email,
            role=role,
            invited_by=request.current_user_id
        )
        db.session.add(invitation)
        db.session.commit()

        # Send invitation email
        try:
            send_invitation_email(email, business.name, role, invitation.token)
        except Exception as e:
            app.logger.error(f"Failed to send invitation email: {e}")

        return jsonify({
            'success': True,
            'message': f'Poziv je poslan na {email}'
        })

    except Exception as e:
        app.logger.error(f"Error inviting user: {e}")
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom slanja poziva'
        }), 500


# API endpoint for active businesses with logos
@app.route('/api/active-businesses')
def api_active_businesses():
    """API endpoint for active businesses with logos (for homepage)"""
    try:
        today = date.today()

        # Get businesses that:
        # 1. Have is_promo_active = True
        # 2. Have at least one active (non-expired) product
        # 3. Have a logo
        businesses = db.session.query(Business).filter(
            Business.is_promo_active == True,
            Business.logo_path.isnot(None)
        ).all()

        # Filter by checking if they have products (all products, including expired discounts)
        active_businesses = []
        for business in businesses:
            has_products = db.session.query(Product).filter(
                Product.business_id == business.id
            ).first() is not None

            if has_products:
                active_businesses.append({
                    'id': business.id,
                    'name': business.name,
                    'logo': format_logo_url(business.logo_path),
                    'city': business.city
                })

        return jsonify(active_businesses)

    except Exception as e:
        app.logger.error(f"Error in active businesses API: {e}")
        return jsonify({'error': 'Failed to load businesses'}), 500


# API endpoint for categories
@app.route('/api/categories')
def api_categories():
    """API endpoint for distinct categories"""
    try:
        categories = db.session.query(Product.category).distinct().filter(
            Product.category.isnot(None)
        ).order_by(Product.category).all()

        result = [cat[0] for cat in categories if cat[0]]

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in categories API: {e}")
        return jsonify({'error': 'Failed to load categories'}), 500


# API endpoint for featured data (homepage)
@app.route('/api/featured-data')
def api_featured_data():
    """API endpoint for featured products and deals"""
    try:
        # Get featured products (products with discounts and good images, limited to 6)
        # Calculate discount percentage inline for ordering
        discount_expr = case(
            (Product.discount_price < Product.base_price,
             ((Product.base_price - Product.discount_price) / Product.base_price * 100)),
            else_=0
        )

        # Get today's date for filtering expired products
        today = date.today()

        # First, try to get products WITH images (cleaner look for homepage)
        featured_products = Product.query.join(Business).filter(
            Product.discount_price.isnot(None),
            Product.discount_price < Product.base_price,
            Product.image_path.isnot(None),  # Must have an image
            Product.image_path != '',  # Image path not empty
            or_(Product.expires.is_(None), Product.expires >= today)  # Filter out expired products
        ).order_by(
            func.random()  # Randomize for variety
        ).limit(12).all()  # Get more, then sort by discount

        # Sort by discount percentage and take top 6
        featured_products = sorted(
            featured_products,
            key=lambda p: ((p.base_price - p.discount_price) / p.base_price * 100) if p.base_price and p.discount_price else 0,
            reverse=True
        )[:6]

        # If not enough products with images, fall back to any products with discounts
        if len(featured_products) < 6:
            existing_ids = [p.id for p in featured_products]
            additional = Product.query.join(Business).filter(
                Product.discount_price.isnot(None),
                Product.discount_price < Product.base_price,
                Product.id.notin_(existing_ids) if existing_ids else True,
                or_(Product.expires.is_(None), Product.expires >= today)
            ).order_by(discount_expr.desc()).limit(6 - len(featured_products)).all()
            featured_products.extend(additional)

        products = []
        for product in featured_products:
            products.append(product_to_dict(product))

        # Get popular categories (categories with most products)
        popular_categories = db.session.query(
            Product.category,
            func.count(Product.id).label('count')
        ).filter(
            Product.category.isnot(None)
        ).group_by(Product.category).order_by(
            func.count(Product.id).desc()
        ).limit(6).all()

        categories = [{'name': cat[0], 'count': cat[1]} for cat in popular_categories]

        # Get businesses with active products
        businesses = db.session.query(Business).join(Product).filter(
            or_(Product.expires.is_(None), Product.expires >= date.today())
        ).distinct().order_by(Business.name).all()

        businesses_list = []
        for business in businesses:
            businesses_list.append({
                'id': business.id,
                'name': business.name,
                'city': business.city,
                'logo_path': format_logo_url(business.logo_path)
            })

        return jsonify({
            'products': products,  # Changed from 'featured_products' to 'products' for consistency
            'businesses': businesses_list,
            'popular_categories': categories,
            'total_products': Product.query.count(),
            'total_businesses': Business.query.filter_by(status='active').count()
        })

    except Exception as e:
        app.logger.error(f"Error in featured data API: {e}")
        return jsonify({'error': 'Failed to load featured data'}), 500


# API endpoint for complete product details
@app.route('/api/product/<int:product_id>')
def api_product_details(product_id):
    """API endpoint for complete product details"""
    try:
        # Get product with business information
        product = Product.query.join(Business).filter(
            Product.id == product_id).first()

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Use standardized product serializer
        product_data = product_to_dict(product)

        # Add extra fields for details page
        product_data['contact_phone'] = product.business.contact_phone
        product_data['google_link'] = product.business.google_link
        product_data['views'] = product.views or 0

        return jsonify(product_data)

    except Exception as e:
        app.logger.error(f"Error in product details API: {e}")
        return jsonify({'error': 'Failed to load product details'}), 500


# Chat/Search endpoint - Using semantic search with vector embeddings
@app.route('/search', methods=['POST'])
@csrf.exempt
def search():
    data = request.get_json()
    query = data.get('query', '').strip()
    business_ids = data.get('business_ids', None)  # Optional list of business IDs to filter

    if not query:
        return jsonify({'error': 'Upit ne može biti prazan'}), 400

    # Try to get user from JWT token (optional - anonymous searches are allowed)
    authenticated_user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            from auth_api import decode_jwt_token
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if payload:
                authenticated_user_id = payload['user_id']
                app.logger.info(f"Search by authenticated user: {authenticated_user_id}")
        except Exception as e:
            app.logger.warning(f"Failed to decode JWT token in search: {e}")

    # Check search limits for both logged-in and anonymous users
    user = current_user if current_user.is_authenticated else None
    search_counts = get_search_counts(user)

    if not can_search(user):
        if search_counts['user_type'] == 'anonymous':
            return jsonify({
                'error': 'limit_exceeded',
                'message':
                f'Dnevni limit od {search_counts["daily_limit"]} kredita je iskorišten. Registrujte se besplatno za {10 - search_counts["daily_limit"]} dodatnih kredita dnevno!',
                'remaining_searches': search_counts['remaining']
            }), 429
        else:
            return jsonify({
                'error': 'limit_exceeded',
                'message':
                'Danas ste iskoristili sve kredite za svoj paket. Nadogradite paket ili vratite se sutra.',
                'remaining_searches': search_counts['remaining']
            }), 429

    try:
        # Import agent-based search (with query expansion and multi-item parsing)
        from agent_search import run_agent_search, format_agent_products

        # Perform agent-based semantic search
        # This uses LangGraph to:
        # 1. Parse query into multiple items (e.g., "mlijeko, jaja i hljeb" -> 3 searches)
        # 2. Expand each item with synonyms for better matching
        # 3. Return grouped results
        try:
            agent_result = run_agent_search(
                query=query,
                user_id=authenticated_user_id,
                k=10,  # Results per item
                business_ids=business_ids,
            )

            # Format and flatten products for API response
            raw_products = agent_result.get("products", [])
            products = format_agent_products(raw_products)

            # Store explanation for later use
            agent_explanation = agent_result.get("explanation")
            is_grouped = agent_result.get("grouped", False)

            app.logger.info(f"Agent search found {len(products)} products (grouped={is_grouped})")
        except Exception as e:
            app.logger.error(f"Semantic search failed: {e}")

            # Rollback any failed transaction before logging
            db.session.rollback()

            # Log failed search attempts for tracking
            from models import UserSearch
            user_agent = request.headers.get('User-Agent', '')
            ua_info = parse_user_agent(user_agent)
            search_log = UserSearch(
                user_id=authenticated_user_id,
                query=query,
                results=json.dumps([]),  # Empty results for failed search
                user_agent=user_agent[:500] if user_agent else None,
                device_type=ua_info['device_type'],
                browser=ua_info['browser'],
                os=ua_info['os']
            )
            db.session.add(search_log)
            db.session.commit()
            app.logger.info(f"Logged failed search: '{query}' by {'user ' + authenticated_user_id if authenticated_user_id else 'anonymous'}")

            return jsonify({
                'success': False,
                'error': 'search_failed',
                'message': 'Pretraga nije uspjela. Pokušajte ponovo.',
                'products': [],
                'products_count': 0
            }), 500

        # Products are already fully formatted from semantic_search
        # Limit to top 12 results for response
        if products:
            products = products[:12]

        # Format results for logging (products are already formatted dicts from semantic_search)
        results_data = products if products else []

        # Get UserSearch model for logging
        from models import UserSearch

        # Log ALL searches (both with and without results) for tracking purposes
        # This helps track user behavior and improve search quality
        user_agent = request.headers.get('User-Agent', '')
        ua_info = parse_user_agent(user_agent)
        search_log = UserSearch(
            user_id=authenticated_user_id,
            query=query,
            results=json.dumps(results_data),
            user_agent=user_agent[:500] if user_agent else None,
            device_type=ua_info['device_type'],
            browser=ua_info['browser'],
            os=ua_info['os']
        )
        db.session.add(search_log)
        db.session.commit()

        app.logger.info(f"Logged search: '{query}' by {'user ' + authenticated_user_id if authenticated_user_id else 'anonymous'} - {len(results_data)} results ({ua_info['device_type']}/{ua_info['browser']})")

        # Check if semantic search returned no results
        if not products:
            app.logger.info("Semantic search - No products found")
            return jsonify({
                'success': False,
                'error': 'no_results',
                'message': 'Nažalost, nema proizvoda koji odgovaraju vašoj pretrazi.',
                'suggestion': 'Pokušajte proširiti pretragu ili promijeniti kriterije.',
                'products': [],
                'products_count': 0
            }), 404

        # Prepare debug information with proper security gating
        debug_available = current_user.is_authenticated and (getattr(
            current_user, 'is_admin', False) or app.config.get('DEBUG', False))

        # Deduct credits and increment counters ONLY for successful searches (with results)
        first_search_bonus_awarded = False
        if current_user.is_authenticated:
            from credits_service_weekly import WeeklyCreditsService
            try:
                WeeklyCreditsService.deduct_credits(
                    user_id=current_user.id,
                    amount=1,
                    action='SEARCH',
                    metadata={'query': query}
                )
                app.logger.info(f"Deducted 1 credit for search by user {current_user.id}")

                # Check and award first search bonus (+3 extra credits)
                if not current_user.first_search_reward_claimed:
                    current_user.extra_credits += 3
                    current_user.first_search_reward_claimed = True
                    first_search_bonus_awarded = True
                    app.logger.info(f"Awarded +3 first search bonus to user {current_user.id}")
            except Exception as credit_error:
                app.logger.error(f"Failed to deduct credit: {credit_error}")
        else:
            # Increment search count for anonymous users
            increment_search_count()

        db.session.commit()

        # Single AI call to generate structured response
        if products:

            # Increment view count for each product that appears in search results
            # Use SQL UPDATE since products are mock objects, not real SQLAlchemy models
            product_ids = []
            for product in products:
                pid = product.get('id') if isinstance(product, dict) else getattr(product, 'id', None)
                if pid:
                    product_ids.append(pid)
            
            if product_ids:
                from sqlalchemy import text
                # Detect database type (PostgreSQL vs SQLite)
                db_url = str(db.engine.url)
                is_postgres = 'postgresql' in db_url

                if is_postgres:
                    # PostgreSQL: use ANY with array
                    update_sql = text("""
                        UPDATE products
                        SET views = COALESCE(views, 0) + 1
                        WHERE id = ANY(:product_ids)
                    """)
                    db.session.execute(update_sql, {'product_ids': product_ids})
                else:
                    # SQLite: use IN clause with placeholders
                    placeholders = ','.join([':id' + str(i) for i in range(len(product_ids))])
                    update_sql = text(f"""
                        UPDATE products
                        SET views = COALESCE(views, 0) + 1
                        WHERE id IN ({placeholders})
                    """)
                    params = {f'id{i}': pid for i, pid in enumerate(product_ids)}
                    db.session.execute(update_sql, params)

                db.session.commit()

            # Calculate savings for marketing tracking
            total_savings = 0.0
            products_with_discounts = 0

            for product in products:
                # Safely get discount and base price from both dict and object
                discount_price = product.get('discount_price') if isinstance(product, dict) else getattr(product, 'discount_price', None)
                base_price = product.get('base_price') if isinstance(product, dict) else getattr(product, 'base_price', None)
                
                if discount_price and base_price and float(discount_price) < float(base_price):
                    savings_amount = float(base_price) - float(discount_price)
                    total_savings += savings_amount
                    products_with_discounts += 1

            # Add to global savings statistics
            if products_with_discounts > 0:
                SavingsStatistics.add_savings(products_with_discounts,
                                              total_savings)

            db.session.commit()

            response_data = generate_single_ai_response(query, results_data)

            # Save this successful search as the new homepage example
            if response_data.get('response') and len(products) > 0:
                save_last_successful_search(query, response_data['response'])

            # Always include basic fields
            response_data['products_count'] = len(products)

            # Ensure products have the proper nested structure for frontend
            response_data['products'] = results_data

            # Add first search bonus flag if awarded
            if first_search_bonus_awarded:
                response_data['first_search_bonus'] = True

            # Add debug info only if authorized
            if debug_available:
                response_data['sql_query'] = 'Semantic search with vector embeddings'
                response_data['search_keywords'] = []
                response_data['llm_parsed'] = {}
            else:
                response_data['sql_query'] = 'Debug not available'
                response_data['search_keywords'] = []
                response_data['llm_parsed'] = {}

            return jsonify(response_data)
        else:
            # No results found - this search is free (don't deduct credits)
            return jsonify({
                'success':
                True,
                'response':
                'Nažalost, nisam pronašao proizvode koji odgovaraju vašoj pretrazi. 💝 Častimo vas ovim kreditom - pokušajte sa drugačijim upitom!',
                'products_count':
                0,
                'products': [],
                'sql_query':
                'Semantic search (no results)',
                'search_keywords':
                [],
                'llm_parsed':
                {},
                'free_search':
                True  # Indicate this was a free search
            })

    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")

        # Log unexpected search failures for tracking
        try:
            # Rollback any failed transaction before logging
            db.session.rollback()

            from models import UserSearch
            user_agent = request.headers.get('User-Agent', '')
            ua_info = parse_user_agent(user_agent)
            search_log = UserSearch(
                user_id=authenticated_user_id,
                query=query,
                results=json.dumps([]),  # Empty results for failed search
                user_agent=user_agent[:500] if user_agent else None,
                device_type=ua_info['device_type'],
                browser=ua_info['browser'],
                os=ua_info['os']
            )
            db.session.add(search_log)
            db.session.commit()
            app.logger.info(f"Logged error search: '{query}' by {'user ' + authenticated_user_id if authenticated_user_id else 'anonymous'}")
        except Exception as log_error:
            app.logger.error(f"Failed to log search: {log_error}")

        return jsonify({
            'success': False,
            'response':
            'Izvini, imao sam problema sa pretraživanjem. Molim te pokušaj ponovo.',
            'products_count': 0,
            'products': []
        })


# Registration routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        preferences_text = data.get('preferences', '')

        # Validate required fields
        if not email or not password or not name:
            return jsonify({'error': 'Sva polja su obavezna'}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error':
                            'Korisnik sa ovim emailom već postoji'}), 400

        # Check for invitation token
        invitation = None
        invitation_token = data.get('invitation_token') or session.get(
            'invitation_token')
        if invitation_token:
            token_hash = BusinessInvitation.hash_token(invitation_token)
            invitation = BusinessInvitation.query.filter_by(
                token_hash=token_hash).first()

            # Validate invitation
            if not invitation or not invitation.is_active:
                return jsonify({'error':
                                'Poziv je nevažeći ili je istekao'}), 400

            # Enforce email match for invitations
            if invitation.email != email:
                return jsonify({'error':
                                'Email mora biti isti kao u pozivu'}), 400

        # Parse preferences using OpenAI
        preferences = parse_user_preferences(preferences_text)

        # Generate verification token with 24h expiry
        verification_token = generate_verification_token()
        token_expires = datetime.now() + timedelta(hours=24)

        # Create new user (unverified)
        user = User(
            id=str(datetime.now().timestamp()),  # Generate unique ID
            email=email,
            password_hash=generate_password_hash(password),
            first_name=name,
            city=preferences.get('city', 'Tuzla'),
            preferences=preferences,
            package_id=1,  # Default to Free package
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=token_expires)

        db.session.add(user)
        db.session.commit()

        # Send verification email
        base_url = request.url_root.rstrip('/')
        send_verification_email(email, name, verification_token, base_url)

        # Auto-login the user after successful registration
        # Note: User can use the app but will be prompted for verification for sensitive actions
        login_user(user)

        if request.is_json:
            return jsonify({
                'success': True,
                'message':
                'Registracija uspješna! Automatski ste prijavljeni. Molimo vas provjerite vaš email za verifikaciju računa.',
                'verification_required': True,
                'redirect':
                url_for('index')  # Redirect to home instead of login
            })
        else:
            flash(
                'Registracija uspješna! Automatski ste prijavljeni. Molimo vas provjerite vaš email za verifikaciju računa.',
                'success')
            return redirect(
                url_for('index'))  # Redirect to home instead of login

    return render_template('register.html')


# Email verification route
@app.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        return render_template(
            'verify_error.html',
            error_message="Link za verifikaciju je nevažeći.")

    if user.is_verified:
        flash('Vaš račun je već verifikovan.', 'info')
        return redirect(url_for('login'))

    # Check if token has expired
    if user.verification_token_expires and datetime.now(
    ) > user.verification_token_expires:
        return render_template(
            'verify_error.html',
            error_message=
            "Link za verifikaciju je istekao. Molimo vas registrujte se ponovo."
        )

    # Verify the user
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.session.commit()

    # Send welcome email now that they're verified
    send_welcome_email(user.email, user.first_name)

    # Check for pending invitation token
    invitation_token = session.get('invitation_token')
    if invitation_token:
        try:
            token_hash = BusinessInvitation.hash_token(invitation_token)
            invitation = BusinessInvitation.query.filter_by(
                token_hash=token_hash).first()

            if invitation and invitation.is_active and invitation.email == user.email:
                # Create business membership
                membership = BusinessMembership(
                    business_id=invitation.business_id,
                    user_id=user.id,
                    role=invitation.role)

                # Mark invitation as accepted
                invitation.accepted_at = datetime.now()
                invitation.redeemed_by_user_id = user.id

                db.session.add(membership)
                db.session.commit()

                # Clear invitation token from session
                session.pop('invitation_token', None)

                flash(
                    f'Email verifikovan i uspješno ste pristupili biznisu "{invitation.business.name}"!',
                    'success')
                return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(
                f"Error processing invitation after verification: {e}")

    flash('Email je uspješno verifikovan! Možete se prijaviti.', 'success')
    return render_template('verify_success.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        email = data.get('email')
        password = data.get('password')

        # DEBUG: Log login attempt
        app.logger.info(f"Login attempt for email: {email}")

        # Validate required fields
        if not email or not password:
            error_msg = 'Email i lozinka su obavezni'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # DEBUG: Log user lookup result
        if user:
            app.logger.info(f"User found: {user.email}, has_password: {bool(user.password_hash)}, is_verified: {user.is_verified}")
            if user.password_hash:
                pwd_check = check_password_hash(user.password_hash, password)
                app.logger.info(f"Password check result: {pwd_check}")
        else:
            app.logger.info("User not found in database")

        # Validate credentials - use generic error to prevent user enumeration
        if not user or not user.password_hash or not check_password_hash(
                user.password_hash, password):
            error_msg = 'Neispravni podaci za prijavu'  # Generic error message
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            else:
                flash(error_msg, 'error')
                return render_template('login.html')

        # Login is successful
        # Check if user is verified (unless they're Replit OAuth users or admin)
        if not user.is_verified and user.password_hash and not user.is_admin:
            error_msg = 'Molimo vas prvo verifikujte vaš email prije prijave.'
            if request.is_json:
                return jsonify({
                    'error': error_msg,
                    'verification_required': True
                }), 403
            else:
                flash(error_msg, 'error')
                return render_template('login.html')

        login_user(user)

        # Check for pending invitation token
        invitation_token = session.get('invitation_token')
        if invitation_token:
            try:
                token_hash = BusinessInvitation.hash_token(invitation_token)
                invitation = BusinessInvitation.query.filter_by(
                    token_hash=token_hash).first()

                if invitation and invitation.is_active and invitation.email == user.email:
                    # Create business membership
                    membership = BusinessMembership(
                        business_id=invitation.business_id,
                        user_id=user.id,
                        role=invitation.role)

                    # Mark invitation as accepted
                    invitation.accepted_at = datetime.now()
                    invitation.redeemed_by_user_id = user.id

                    db.session.add(membership)
                    db.session.commit()

                    # Clear invitation token from session
                    session.pop('invitation_token', None)

                    success_msg = f'Uspješno ste se prijavili i pristupili biznisu "{invitation.business.name}"!'
                    if request.is_json:
                        return jsonify({
                            'success': True,
                            'redirect': url_for('manage_products',
                                    business_id=invitation.business_id)
                        })
                    else:
                        flash(success_msg, 'success')
                        return redirect(
                            url_for('manage_products',
                                    business_id=invitation.business_id))
            except Exception as e:
                app.logger.error(
                    f"Error processing invitation after login: {e}")

        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('index')})
        else:
            flash('Uspješno ste se prijavili!', 'success')
            return redirect(url_for('index'))

    return render_template('login.html')


# Admin account creation function
def create_admin_account():
    """Create admin account for adnanxteam@gmail.com if it doesn't exist"""
    admin_email = "adnanxteam@gmail.com"
    admin_user = User.query.filter_by(email=admin_email).first()

    if not admin_user:
        # Create admin user
        admin_user = User(id=str(datetime.now().timestamp()),
                          email=admin_email,
                          first_name="Admin",
                          last_name="User",
                          city="Tuzla",
                          is_verified=True,
                          is_admin=True,
                          package_id=1)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin account created for {admin_email}")
    else:
        # Make sure existing user is admin and verified
        admin_user.is_admin = True
        admin_user.is_verified = True
        db.session.commit()
        print(f"Admin privileges updated for {admin_email}")


# Logout route
@app.route('/logout')
def logout():
    logout_user()
    flash('Uspješno ste se odjavili!', 'success')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')

        if not email:
            error_msg = 'Email je obavezan'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if user and user.password_hash:  # Only for email/password users, not OAuth users
            # Generate reset token (1 hour expiry)
            reset_token = generate_verification_token()
            token_expires = datetime.now() + timedelta(hours=1)

            user.reset_token = reset_token
            user.reset_token_expires = token_expires
            db.session.commit()

            # Send password reset email
            base_url = request.url_root.rstrip('/')
            send_password_reset_email(user.email, user.first_name or "User",
                                      reset_token, base_url)

        # Always show success message for security (don't reveal if email exists)
        success_msg = 'Ako je email registrovan, poslat je link za resetiranje lozinke.'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        flash(success_msg, 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user:
        flash('Link za resetiranje je nevažeći.', 'error')
        return redirect(url_for('forgot_password'))

    # Check if token has expired
    if user.reset_token_expires and datetime.now() > user.reset_token_expires:
        flash('Link za resetiranje je istekao. Molimo vas zatražite novi.',
              'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not password or not confirm_password:
            error_msg = 'Sva polja su obavezna'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('reset_password.html', token=token)

        if password != confirm_password:
            error_msg = 'Lozinke se ne poklapaju'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('reset_password.html', token=token)

        if len(password) < 6:
            error_msg = 'Lozinka mora imati najmanje 6 karaktera'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('reset_password.html', token=token)

        # Update password and clear reset token
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        success_msg = 'Lozinka je uspješno resetirana! Možete se prijaviti.'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        flash(success_msg, 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


# Products catalog page
@app.route('/proizvodi')
def products():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('search', '')
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    business_id = request.args.get('business', '', type=str)
    sort_by = request.args.get('sort', 'newest')

    query = Product.query.join(Business)

    # Apply filters
    if search_term:
        query = query.filter(Product.title.ilike(f'%{search_term}%'))

    if category:
        query = query.filter(Product.category.ilike(f'%{category}%'))

    if city:
        query = query.filter(
            or_(Product.city.ilike(f'%{city}%'),
                Business.city.ilike(f'%{city}%')))

    if business_id:
        query = query.filter(Product.business_id == int(business_id))

    # Show all products (expired discounts become regular products)
    # No expiry filter - products stay in catalog after discount expires

    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.base_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.base_price.desc())
    elif sort_by == 'discount':
        query = query.filter(Product.discount_price.isnot(None)).order_by(
            ((Product.base_price - Product.discount_price) /
             Product.base_price).desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    products_paginated = query.paginate(page=page,
                                        per_page=12,
                                        error_out=False)

    # Get available categories, cities, and businesses for filters
    categories = db.session.query(Product.category).distinct().filter(
        Product.category.isnot(None)).all()
    categories = [cat[0] for cat in categories if cat[0]]

    cities = db.session.query(Business.city).distinct().all()
    cities = [city[0] for city in cities if city[0]]

    # Get businesses that have products
    businesses = db.session.query(Business).join(Product).distinct().order_by(Business.name).all()

    # Calculate savings statistics for current page products
    page_products = products_paginated.items
    total_savings_on_page = 0
    products_with_discounts = 0

    for product in page_products:
        if product.discount_price and product.discount_price < product.base_price:
            savings = product.base_price - product.discount_price
            total_savings_on_page += savings
            products_with_discounts += 1

    # Calculate average savings per discounted product
    average_savings_per_product = 0
    if products_with_discounts > 0:
        average_savings_per_product = total_savings_on_page / products_with_discounts

    # Get total count of products with discounts (for all pages, not just current)
    total_discounted_products = query.filter(
        Product.discount_price.isnot(None)).filter(
            Product.discount_price < Product.base_price).count()

    savings_stats = {
        'page_total_savings': round(total_savings_on_page, 2),
        'page_discounted_products': products_with_discounts,
        'page_average_savings': round(average_savings_per_product, 2),
        'total_discounted_products': total_discounted_products,
        'total_products_shown': len(page_products)
    }

    return render_template('products.html',
                           products=products_paginated,
                           categories=categories,
                           cities=cities,
                           businesses=businesses,
                           current_search=search_term,
                           current_category=category,
                           current_city=city,
                           current_business=business_id,
                           current_sort=sort_by,
                           savings_stats=savings_stats)


# Contact page
@app.route('/kontakt', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        name = data.get('name')
        email = data.get('email')
        message = data.get('message')

        # Save to database
        contact_msg = ContactMessage(user_name=name,
                                     user_email=email,
                                     message=message)
        db.session.add(contact_msg)
        db.session.commit()

        # Send email
        email_sent = send_contact_email(name, email, message)

        success_msg = 'Hvala, vaša poruka je uspješno poslana.'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        else:
            flash(success_msg, 'success')
            return redirect(url_for('contact'))

    return render_template('contact.html')


# How it works page
@app.route('/kako-radimo')
def how_it_works():
    return render_template('how_it_works.html')


# User profile page
@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Handle profile update
        data = request.get_json() if request.is_json else request.form

        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        city = data.get('city', '').strip()

        # Validate required fields
        if not first_name:
            if request.is_json:
                return jsonify({'error': 'Ime je obavezno'}), 400
            else:
                flash('Ime je obavezno', 'error')
                return redirect(url_for('profile'))

        # Update user information
        current_user.first_name = first_name
        current_user.last_name = last_name if last_name else None
        current_user.city = city if city else None
        current_user.updated_at = datetime.now()

        try:
            db.session.commit()
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Profil je uspješno ažuriran'
                })
            else:
                flash('Profil je uspješno ažuriran', 'success')
                return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating profile: {e}")
            if request.is_json:
                return jsonify({
                    'error':
                    'Došlo je do greške prilikom ažuriranja profila'
                }), 500
            else:
                flash('Došlo je do greške prilikom ažuriranja profila',
                      'error')
                return redirect(url_for('profile'))

    # GET request - display profile
    # Get user's search count for today
    today = date.today()
    today_searches = db.session.query(UserSearch).filter(
        and_(UserSearch.user_id == current_user.id,
             db.func.date(UserSearch.created_at) == today)).count()

    # Get recent searches
    recent_searches = db.session.query(UserSearch).filter_by(
        user_id=current_user.id).order_by(
            UserSearch.created_at.desc()).limit(10).all()

    return render_template('profile.html',
                           user=current_user,
                           today_searches=today_searches,
                           recent_searches=recent_searches)


# Invitation routes
@app.route('/invite/accept/<token>')
def accept_invitation(token):
    """Accept a business invitation"""
    try:
        # Find invitation by token hash
        token_hash = BusinessInvitation.hash_token(token)
        invitation = BusinessInvitation.query.filter_by(
            token_hash=token_hash).first()

        if not invitation or not invitation.is_active:
            return render_template(
                'invite_error.html',
                error_message=
                "Poziv je nevažeći, istekao je ili je već iskorišten.")

        # If user is logged in, check email match and process immediately
        if current_user.is_authenticated:
            if current_user.email != invitation.email:
                return render_template(
                    'invite_error.html',
                    error_message=
                    "Ovaj poziv je namijenjen drugoj email adresi.")

            if not current_user.is_verified:
                return render_template(
                    'invite_error.html',
                    error_message="Molimo vas prvo verifikujte vaš email račun."
                )

            # Create business membership
            membership = BusinessMembership(business_id=invitation.business_id,
                                            user_id=current_user.id,
                                            role=invitation.role)

            # Mark invitation as accepted
            invitation.accepted_at = datetime.now()
            invitation.redeemed_by_user_id = current_user.id

            db.session.add(membership)
            db.session.commit()

            flash(
                f'Uspješno ste pristupili biznisu "{invitation.business.name}" kao {invitation.role}!',
                'success')
            return redirect(
                url_for('manage_products', business_id=invitation.business_id))

        else:
            # Redirect to registration/login with token carried
            session['invitation_token'] = token
            flash(
                'Molimo vas prijavite se ili registrujte da prihvatite poziv.',
                'info')
            return redirect(url_for('login'))

    except Exception as e:
        return render_template(
            'invite_error.html',
            error_message="Došlo je do greške prilikom obrađivanja poziva.")


# Business dashboard (hidden page, accessible by direct URL)
@app.route('/biznisi')
@login_required
def business_dashboard():
    # For now, allow any logged-in user to access
    # In production, you might want to add role-based access
    businesses = Business.query.all()
    return render_template('business_dashboard.html',
                           businesses=businesses,
                           user_has_business_role=user_has_business_role)


# Add business
@app.route('/biznisi/dodaj', methods=['GET', 'POST'])
@login_required
def add_business():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form

        business = Business(name=data.get('name'),
                            contact_phone=data.get('phone'),
                            city=data.get('city', 'Tuzla'),
                            google_link=data.get('google_link'))

        db.session.add(business)
        db.session.commit()

        if request.is_json:
            return jsonify({'success': True, 'business_id': business.id})
        else:
            flash('Biznis je uspješno dodat!', 'success')
            return redirect(url_for('business_dashboard'))

    return render_template('add_business.html')


# Upload business logo
@app.route('/biznisi/<int:business_id>/upload-logo', methods=['POST'])
@login_required
@business_role_required('staff')  # Require at least staff role
def upload_business_logo(business_id):
    from PIL import Image
    import io
    import uuid
    import boto3
    import re

    business = Business.query.get_or_404(business_id)

    if 'logo' not in request.files:
        return jsonify({'success': False, 'error': 'Nema datoteke za upload'})

    file = request.files['logo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nema odabrane datoteke'})

    try:
        # Read file content for validation
        file_content = file.read()
        file.seek(0)  # Reset file pointer

        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'Datoteka je prevelika (max 5MB)'
            })

        # Validate image using Pillow
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()  # Verify it's a valid image

            # Re-open for processing (verify() closes the image)
            image = Image.open(io.BytesIO(file_content))

            # Check image dimensions (prevent extremely large images)
            max_dimension = 4096
            if image.width > max_dimension or image.height > max_dimension:
                return jsonify({
                    'success':
                    False,
                    'error':
                    f'Slika je prevelika (max {max_dimension}x{max_dimension} piksela)'
                })

            # Convert to RGB if necessary and resize if too large
            if image.mode in ('RGBA', 'LA'):
                # Convert to RGB with white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(
                    image, mask=image.split()[-1])  # Use alpha channel as mask
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Resize if image is too large (while maintaining aspect ratio)
            max_size = (1024, 1024)
            if image.width > max_size[0] or image.height > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'Datoteka nije validna slika'
            })

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'eu-central-1')
        )

        bucket_name = os.environ.get('AWS_S3_BUCKET', 'aipijaca')

        # Delete old logo from S3 if it exists
        if business.logo_path and 'amazonaws.com' in business.logo_path:
            try:
                match = re.search(r'amazonaws\.com/(.+)$', business.logo_path)
                if match:
                    old_s3_key = match.group(1)
                    app.logger.info(f"Deleting old logo from S3: {old_s3_key}")
                    s3_client.delete_object(Bucket=bucket_name, Key=old_s3_key)
            except Exception as e:
                app.logger.warning(f"Failed to delete old logo from S3: {e}")

        # Create unique filename with UUID
        file_extension = 'png'  # Always save as PNG for consistency
        unique_filename = f"{business_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        s3_key = f"assets/images/business_logos/{business_id}/{unique_filename}"

        # Save processed image to BytesIO buffer
        buffer = io.BytesIO()
        image.save(buffer, 'PNG', optimize=True)
        buffer.seek(0)

        # Upload to S3
        s3_client.upload_fileobj(
            buffer,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': 'image/png'
            }
        )

        # Generate S3 URL
        logo_url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'eu-central-1')}.amazonaws.com/{s3_key}"

        # Update business record
        business.logo_path = logo_url
        db.session.commit()

        app.logger.info(f"Logo uploaded for business {business_id}: {logo_url}")

        return jsonify({'success': True, 'logo_path': logo_url})

    except Exception as e:
        app.logger.error(f"Error uploading logo: {e}")
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom obrade datoteke'
        })


# Edit business
@app.route('/biznisi/<int:business_id>/uredi', methods=['POST'])
@login_required
@business_role_required('staff')  # Require at least staff role
def edit_business(business_id):
    """Edit business basic information"""
    try:
        business = Business.query.get_or_404(business_id)
        data = request.get_json() if request.is_json else request.form

        # Update business fields
        business.name = data.get('name', business.name).strip()
        business.contact_phone = data.get('phone', business.contact_phone)
        business.city = data.get('city', business.city).strip()
        google_link = data.get('google_link', business.google_link)

        # Validate Google link if provided
        if google_link and google_link.strip():
            google_link = google_link.strip()
            if not (google_link.startswith('http://')
                    or google_link.startswith('https://')):
                return jsonify({
                    'success':
                    False,
                    'error':
                    'Google link mora počinjati sa http:// ili https://'
                })
            business.google_link = google_link
        else:
            business.google_link = None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Biznis je uspešno ažuriran',
            'business': {
                'id': business.id,
                'name': business.name,
                'contact_phone': business.contact_phone,
                'city': business.city,
                'google_link': business.google_link
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success':
            False,
            'error':
            'Došlo je do greške prilikom ažuriranja biznisa'
        })


# Set PDF URL for business
@app.route('/biznisi/<int:business_id>/set-pdf-url', methods=['POST'])
@require_jwt_auth
@business_role_required('owner')
def set_business_pdf_url(business_id):
    """Set PDF URL for automated product sync"""
    try:
        business = Business.query.get_or_404(business_id)
        data = request.get_json()
        pdf_url = data.get('pdf_url', '').strip()

        if pdf_url:
            # Basic URL validation
            if not (pdf_url.startswith('http://')
                    or pdf_url.startswith('https://')):
                return jsonify({
                    'success':
                    False,
                    'error':
                    'URL mora počinjati sa http:// ili https://'
                })

        business.pdf_url = pdf_url if pdf_url else None
        db.session.commit()

        return jsonify({
            'success':
            True,
            'message':
            'PDF URL je uspešno ažuriran' if pdf_url else 'PDF URL je uklonjen'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success':
            False,
            'error':
            'Došlo je do greške prilikom ažuriranja PDF URL-a'
        })


# Upload PDF for immediate processing
@app.route('/biznisi/<int:business_id>/upload-pdf', methods=['POST'])
@require_jwt_auth
@business_role_required('manager')
def upload_business_pdf(business_id):
    """Upload and process PDF file for products"""
    try:
        business = Business.query.get_or_404(business_id)

        if 'pdf_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nijedan fajl nije odabran'
            })

        file = request.files['pdf_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nijedan fajl nije odabran'
            })

        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'error': 'Dozvoljena su samo PDF fajlovi'
            })

        # Check file size (20MB limit)
        file.seek(0, 2)  # Move to end of file
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 20 * 1024 * 1024:  # 20MB
            return jsonify({
                'success':
                False,
                'error':
                'Fajl je prevelik. Maksimalna veličina je 20MB'
            })

        # Process PDF content
        pdf_content = file.read()
        result = process_pdf_for_business(pdf_content)

        if not result['success']:
            return jsonify({
                'success':
                False,
                'error':
                f'Greška pri obradi PDF-a: {result["error"]}'
            })

        # Add products to business with duplicate detection
        added_count = 0
        skipped_count = 0

        for product_data in result['products']:
            # Check for duplicates
            normalized_title = normalize_product_title(product_data['title'])

            existing_product = Product.query.filter(
                Product.business_id == business_id).filter(
                    db.func.lower(Product.title) == normalized_title).first()

            if existing_product:
                skipped_count += 1
                continue

            # Create new product
            new_product = Product(
                business_id=business_id,
                title=product_data['title'],
                base_price=product_data.get('base_price'),
                discount_price=product_data.get('discount_price'),
                category=product_data.get('category', 'Ostalo'),
                tags=json.dumps(product_data.get('tags', []),
                                ensure_ascii=False)
                if product_data.get('tags') else None,
                views=0)

            db.session.add(new_product)
            added_count += 1

        # Update last sync
        business.last_sync = datetime.now()
        db.session.commit()

        return jsonify({
            'success':
            True,
            'added':
            added_count,
            'skipped':
            skipped_count,
            'total_found':
            len(result['products']),
            'method':
            result['method'],
            'pages_processed':
            result['pages_processed'],
            'message':
            f'Dodano {added_count} proizvoda, preskočeno {skipped_count} duplikata'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Došlo je do greške prilikom obrade PDF fajla'
        })


# Sync products from PDF URL
@app.route('/biznisi/<int:business_id>/sync-pdf', methods=['POST'])
@require_jwt_auth
@business_role_required('manager')
def sync_business_pdf(business_id):
    """Sync products from business PDF URL"""
    try:
        business = Business.query.get_or_404(business_id)

        if not business.pdf_url:
            return jsonify({
                'success': False,
                'error': 'PDF URL nije postavljen za ovaj biznis'
            })

        # Download PDF from URL
        try:
            pdf_content = download_pdf_from_url(business.pdf_url)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Greška pri preuzimanju PDF-a: {str(e)}'
            })

        # Process PDF content
        result = process_pdf_for_business(pdf_content)

        if not result['success']:
            return jsonify({
                'success':
                False,
                'error':
                f'Greška pri obradi PDF-a: {result["error"]}'
            })

        # Add products to business with duplicate detection
        added_count = 0
        skipped_count = 0
        updated_count = 0
        products_to_vectorize = []  # Track products that need vectorization

        for product_data in result['products']:
            # Check for duplicates
            normalized_title = normalize_product_title(product_data['title'])

            existing_product = Product.query.filter(
                Product.business_id == business_id).filter(
                    db.func.lower(Product.title) == normalized_title).first()

            if existing_product:
                # Update prices if they've changed
                base_price = product_data.get('base_price')
                discount_price = product_data.get('discount_price')

                if (base_price and base_price != existing_product.base_price) or \
                   (discount_price != existing_product.discount_price):
                    existing_product.base_price = base_price
                    existing_product.discount_price = discount_price
                    products_to_vectorize.append(existing_product)
                    updated_count += 1
                else:
                    skipped_count += 1
                continue

            # Create new product
            new_product = Product(
                business_id=business_id,
                title=product_data['title'],
                base_price=product_data.get('base_price'),
                discount_price=product_data.get('discount_price'),
                category=product_data.get('category', 'Ostalo'),
                tags=json.dumps(product_data.get('tags', []),
                                ensure_ascii=False)
                if product_data.get('tags') else None,
                views=0)

            db.session.add(new_product)
            products_to_vectorize.append(new_product)
            added_count += 1

        # Update last sync
        business.last_sync = datetime.now()
        db.session.commit()

        # Auto-vectorize updated and new products
        if products_to_vectorize:
            try:
                from auto_vectorize import batch_vectorize_products
                product_ids = [p.id for p in products_to_vectorize]
                app.logger.info(f"Auto-vectorizing {len(product_ids)} products from PDF sync")
                batch_vectorize_products(product_ids=product_ids, force=False)
            except Exception as e:
                app.logger.error(f"Auto-vectorization failed after PDF sync: {e}")

        return jsonify({
            'success':
            True,
            'added':
            added_count,
            'updated':
            updated_count,
            'skipped':
            skipped_count,
            'total_found':
            len(result['products']),
            'method':
            result['method'],
            'pages_processed':
            result['pages_processed'],
            'message':
            f'Dodano {added_count} novih proizvoda, ažurirano {updated_count}, preskočeno {skipped_count} duplikata'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success':
            False,
            'error':
            'Došlo je do greške prilikom sinhronizacije PDF-a'
        })


# Business products management
@app.route('/biznisi/<int:business_id>/proizvodi')
@login_required
@business_role_required('owner')
def manage_products(business_id):
    business = Business.query.get_or_404(business_id)
    products = Product.query.filter_by(business_id=business_id).order_by(
        Product.created_at.desc()).all()
    return render_template('manage_products.html',
                           business=business,
                           products=products)


# Add product to business
@app.route('/biznisi/<int:business_id>/proizvodi/dodaj', methods=['POST'])
@require_jwt_auth
def add_product(business_id):
    business = Business.query.get_or_404(business_id)
    data = request.get_json() if request.is_json else request.form

    # Check if it's free-text input that needs AI parsing
    if 'product_text' in data:
        parsed_data = parse_product_text(data['product_text'])

        product = Product(business_id=business_id,
                          title=parsed_data['title'],
                          base_price=parsed_data['base_price'],
                          discount_price=parsed_data.get('discount_price'),
                          category=parsed_data.get('category'),
                          tags=parsed_data.get('tags'),
                          product_metadata=parsed_data.get('product_metadata'),
                          city=business.city)
    else:
        # Manual form input - also use AI to generate tags
        expires = None
        if data.get('expires'):
            expires = datetime.strptime(data['expires'], '%Y-%m-%d').date()

        # Generate tags using AI based on title and category
        tags = []
        try:
            product_desc = f"{data['title']}, kategorija: {data.get('category', '')}"
            parsed_data = parse_product_text(product_desc)
            tags = parsed_data.get('tags', [])
        except Exception as e:
            app.logger.warning(f"Failed to generate tags for manual product: {e}")
            # Fallback: generate basic tags from title and category
            tags = []
            title_lower = data['title'].lower().strip()
            if title_lower:
                tags.append(title_lower)
            category = data.get('category', '').lower().strip()
            if category:
                tags.append(category)

        product = Product(business_id=business_id,
                          title=data['title'],
                          base_price=float(data['base_price']),
                          discount_price=float(data['discount_price'])
                          if data.get('discount_price') else None,
                          expires=expires,
                          category=data.get('category'),
                          tags=tags,
                          product_url=data.get('product_url'),
                          city=business.city)

    db.session.add(product)
    db.session.commit()

    # Generate enriched description for semantic search
    try:
        enriched_desc = generate_enriched_description(
            product_title=product.title,
            category=product.category
        )
        product.enriched_description = enriched_desc
        db.session.commit()
        app.logger.info(f"Generated enriched description for product {product.id}")
    except Exception as e:
        app.logger.warning(f"Failed to generate enriched description for product {product.id}: {e}")
        # Don't fail the request if description generation fails

    # Auto-vectorize the new product
    try:
        from auto_vectorize import auto_vectorize_on_save
        auto_vectorize_on_save(product)
    except Exception as e:
        app.logger.error(f"Auto-vectorization failed for product {product.id}: {e}")
        # Don't fail the request if vectorization fails

    if request.is_json:
        return jsonify({'success': True, 'product_id': product.id})
    else:
        flash('Proizvod je uspješno dodat!', 'success')
        return redirect(url_for('manage_products', business_id=business_id))


# Bulk import products from JSON
@app.route('/biznisi/<int:business_id>/proizvodi/bulk-import', methods=['POST'])
@require_jwt_auth
def bulk_import_products(business_id):
    business = Business.query.get_or_404(business_id)

    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({
                'success': False,
                'error': 'JSON mora imati "products" array'
            }), 400

        products_data = data['products']
        if not isinstance(products_data, list):
            return jsonify({
                'success': False,
                'error': '"products" mora biti array'
            }), 400

        imported_count = 0
        errors = []

        # First pass: Validate all products and prepare data
        validated_products = []
        for idx, product_data in enumerate(products_data):
            try:
                # Validate required fields
                if 'title' not in product_data or 'base_price' not in product_data:
                    errors.append(f"Proizvod #{idx + 1}: nedostaje 'title' ili 'base_price'")
                    continue

                # Parse expiry date if provided
                expires = None
                if product_data.get('expires'):
                    try:
                        expires = datetime.strptime(product_data['expires'], '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f"Proizvod #{idx + 1}: nevažeći datum format (koristite YYYY-MM-DD)")
                        continue

                validated_products.append({
                    'index': idx,
                    'data': product_data,
                    'expires': expires
                })

            except Exception as e:
                errors.append(f"Proizvod #{idx + 1} ({product_data.get('title', 'N/A')}): {str(e)}")
                continue

        # Generate simple fallback tags (FAST - no LLM)
        all_tags = []
        for p in validated_products:
            fallback_tags = []
            title = p['data']['title'].lower().strip()
            if title:
                fallback_tags.append(title)
            category = p['data'].get('category', '').lower().strip()
            if category:
                fallback_tags.append(category)
            all_tags.append(fallback_tags)

        # Second pass: Create or update products with generated tags
        updated_count = 0
        products_to_vectorize = []  # Track products that need vectorization
        for idx, validated_product in enumerate(validated_products):
            try:
                product_data = validated_product['data']
                expires = validated_product['expires']
                tags = all_tags[idx] if idx < len(all_tags) else [product_data['title'].lower()]

                # Check if product exists by matching title only (allows price updates)
                existing_product = Product.query.filter_by(
                    business_id=business_id,
                    title=product_data['title']
                ).first()

                if existing_product:
                    # Track price changes before updating
                    new_base = float(product_data['base_price'])
                    new_discount = float(product_data['discount_price']) if product_data.get('discount_price') else None

                    if existing_product.base_price != new_base or existing_product.discount_price != new_discount:
                        from models import ProductPriceHistory
                        price_history = ProductPriceHistory(
                            product_id=existing_product.id,
                            base_price=existing_product.base_price,
                            discount_price=existing_product.discount_price
                        )
                        db.session.add(price_history)

                    # Update existing product (including prices)
                    existing_product.base_price = new_base
                    existing_product.discount_price = new_discount
                    existing_product.expires = expires
                    existing_product.category = product_data.get('category')
                    existing_product.tags = tags
                    existing_product.product_metadata = product_data.get('product_metadata', {})
                    existing_product.image_path = product_data.get('image_url') or product_data.get('image_path')
                    existing_product.city = business.city
                    products_to_vectorize.append(existing_product)
                    updated_count += 1
                else:
                    # Create new product
                    product = Product(
                        business_id=business_id,
                        title=product_data['title'],
                        base_price=float(product_data['base_price']),
                        discount_price=float(product_data['discount_price']) if product_data.get('discount_price') else None,
                        expires=expires,
                        category=product_data.get('category'),
                        tags=tags,
                        product_metadata=product_data.get('product_metadata', {}),
                        image_path=product_data.get('image_url') or product_data.get('image_path'),
                        city=business.city
                    )
                    db.session.add(product)
                    products_to_vectorize.append(product)

                imported_count += 1

            except Exception as e:
                errors.append(f"Proizvod #{validated_product['index'] + 1} ({product_data.get('title', 'N/A')}): {str(e)}")
                continue

        # Commit all products first
        db.session.commit()

        # Schedule async enrichment (tags + descriptions) and vectorization
        if products_to_vectorize:
            product_ids = [p.id for p in products_to_vectorize]

            # Schedule background task for AI enrichment (tags + descriptions)
            try:
                app.logger.info(f"Scheduling async AI enrichment for {len(product_ids)} products")
                schedule_async_product_enrichment(product_ids)
            except Exception as e:
                app.logger.error(f"Failed to schedule async enrichment: {e}")

            # Schedule vectorization (will run after enrichment)
            try:
                from auto_vectorize import schedule_async_vectorization
                app.logger.info(f"Scheduling async vectorization for {len(product_ids)} products")
                schedule_async_vectorization(product_ids=product_ids, force=False)
            except Exception as e:
                app.logger.error(f"Failed to schedule async vectorization: {e}")

        created_count = imported_count - updated_count
        response = {
            'success': True,
            'imported_count': imported_count,
            'created_count': created_count,
            'updated_count': updated_count,
            'total_products': len(products_data)
        }

        if errors:
            response['errors'] = errors
            response['message'] = f"Obrađeno {imported_count}/{len(products_data)} proizvoda ({created_count} novo, {updated_count} ažurirano). Neki proizvodi nisu importovani."
        else:
            response['message'] = f"Uspješno obrađeno {imported_count} proizvoda ({created_count} novo, {updated_count} ažurirano)."

        return jsonify(response)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Bulk import error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri importu: {str(e)}'
        }), 500


# Delete all products for business
@app.route('/biznisi/<int:business_id>/proizvodi/obrisi-sve', methods=['POST'])
@require_jwt_auth
def delete_all_products(business_id):
    business = Business.query.get_or_404(business_id)

    # CASCADE will handle related records
    deleted_count = Product.query.filter_by(business_id=business_id).count()
    Product.query.filter_by(business_id=business_id).delete()
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'deleted_count': deleted_count})
    else:
        flash(f'Obrisano je {deleted_count} proizvoda.', 'success')
        return redirect(url_for('manage_products', business_id=business_id))


# Update single product
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>', methods=['PUT'])
@require_jwt_auth
def update_single_product(business_id, product_id):
    """Update a single product"""
    try:
        business = Business.query.get_or_404(business_id)

        # Find product and verify it belongs to this business
        product = Product.query.filter_by(
            id=product_id,
            business_id=business_id
        ).first()

        if not product:
            return jsonify({
                'success': False,
                'error': 'Proizvod nije pronađen ili ne pripada ovom biznisu'
            }), 404

        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Nedostaju podaci za ažuriranje'
            }), 400

        # Update fields
        if 'title' in data:
            product.title = data['title']
        if 'base_price' in data:
            product.base_price = float(data['base_price'])
        if 'discount_price' in data:
            product.discount_price = float(data['discount_price']) if data['discount_price'] else None
        if 'category' in data:
            product.category = data['category']
        if 'expires' in data:
            if data['expires']:
                product.expires = datetime.strptime(data['expires'], '%Y-%m-%d').date()
            else:
                product.expires = None
        if 'product_url' in data:
            product.product_url = data['product_url']
        if 'enriched_description' in data:
            product.enriched_description = data['enriched_description']
        if 'image_path' in data:
            product.image_path = data['image_path']
        if 'tags' in data:
            product.tags = data['tags']

        db.session.commit()

        # Re-vectorize if description changed
        if 'enriched_description' in data:
            try:
                from auto_vectorize import auto_vectorize_on_save
                auto_vectorize_on_save(product)
            except Exception as e:
                app.logger.error(f"Auto-vectorization failed after update for product {product.id}: {e}")

        app.logger.info(f"Product {product_id} updated in business {business_id}")

        return jsonify({
            'success': True,
            'message': 'Proizvod je uspješno ažuriran'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Update product error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri ažuriranju: {str(e)}'
        }), 500


# Delete single product
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>', methods=['DELETE'])
@csrf.exempt
@require_jwt_auth
def delete_single_product(business_id, product_id):
    """Delete a single product"""
    try:
        business = Business.query.get_or_404(business_id)

        # Find product and verify it belongs to this business
        product = Product.query.filter_by(
            id=product_id,
            business_id=business_id
        ).first()

        if not product:
            return jsonify({
                'success': False,
                'error': 'Proizvod nije pronađen ili ne pripada ovom biznisu'
            }), 404

        # Delete the product (CASCADE will handle related records)
        db.session.delete(product)
        db.session.commit()

        app.logger.info(f"Product {product_id} deleted from business {business_id}")

        return jsonify({
            'success': True,
            'message': 'Proizvod je uspješno obrisan'
        })

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        app.logger.error(f"Delete product error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri brisanju: {str(e)}'
        }), 500


# Upload product image to S3
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>/upload-image', methods=['POST'])
@csrf.exempt
@require_jwt_auth
def upload_product_image(business_id, product_id):
    """Upload product image to S3 and update product"""
    try:
        import boto3
        import uuid
        from werkzeug.utils import secure_filename
        import re

        business = Business.query.get_or_404(business_id)

        # Find product
        product = Product.query.filter_by(
            id=product_id,
            business_id=business_id
        ).first()

        if not product:
            return jsonify({
                'success': False,
                'error': 'Proizvod nije pronađen'
            }), 404

        # Check if image file is in request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nema slike u zahtevu'
            }), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nema odabrane slike'
            }), 400

        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': 'Nedozvoljeni tip fajla. Koristite JPG, PNG, GIF ili WEBP'
            }), 400

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_REGION', 'eu-central-1')
        )

        bucket_name = os.environ.get('AWS_S3_BUCKET', 'aipijaca')

        # Delete old image from S3 if it exists
        if product.image_path:
            try:
                # Extract S3 key from URL
                # URL format: https://aipijaca.s3.eu-central-1.amazonaws.com/products/123/filename.jpg
                match = re.search(r'amazonaws\.com/(.+)$', product.image_path)
                if match:
                    old_s3_key = match.group(1)
                    app.logger.info(f"Deleting old image from S3: {old_s3_key}")
                    s3_client.delete_object(Bucket=bucket_name, Key=old_s3_key)
                    app.logger.info(f"Successfully deleted old image: {old_s3_key}")
            except Exception as e:
                # Log error but continue with upload - don't fail if old image can't be deleted
                app.logger.warning(f"Failed to delete old image from S3: {e}")

        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        s3_key = f"products/{business_id}/{unique_filename}"

        # Upload new image to S3
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type
            }
        )

        # Generate S3 URL
        image_url = f"https://{bucket_name}.s3.{os.environ.get('AWS_REGION', 'eu-central-1')}.amazonaws.com/{s3_key}"

        # Update product
        product.image_path = image_url
        db.session.commit()

        app.logger.info(f"Image uploaded for product {product_id}: {image_url}")

        return jsonify({
            'success': True,
            'image_url': image_url,
            'message': 'Slika je uspješno uploadovana'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Image upload error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri uploadu slike: {str(e)}'
        }), 500


# Regenerate tags for single product
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>/regenerate-tags', methods=['POST'])
@require_jwt_auth
def regenerate_product_tags(business_id, product_id):
    """Regenerate tags for a single product using AI"""
    try:
        business = Business.query.get_or_404(business_id)

        product = Product.query.filter_by(
            id=product_id,
            business_id=business_id
        ).first()

        if not product:
            return jsonify({
                'success': False,
                'error': 'Proizvod nije pronađen'
            }), 404

        # Generate tags using AI
        product_desc = f"{product.title}, kategorija: {product.category or ''}"
        parsed_data = parse_product_text(product_desc)
        new_tags = parsed_data.get('tags', [])

        # Fallback if no tags generated
        if not new_tags:
            new_tags = []
            if product.title:
                new_tags.append(product.title.lower().strip())
            if product.category:
                new_tags.append(product.category.lower().strip())

        product.tags = new_tags
        db.session.commit()

        # Re-vectorize
        try:
            from auto_vectorize import auto_vectorize_on_save
            auto_vectorize_on_save(product)
        except Exception as e:
            app.logger.error(f"Auto-vectorization failed: {e}")

        app.logger.info(f"Tags regenerated for product {product_id}: {new_tags}")

        return jsonify({
            'success': True,
            'tags': new_tags,
            'message': 'Tagovi su uspješno regenerisani'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Regenerate tags error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri regeneraciji tagova: {str(e)}'
        }), 500


# Regenerate description for single product
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>/regenerate-description', methods=['POST'])
@require_jwt_auth
def regenerate_product_description(business_id, product_id):
    """Regenerate enriched description for a single product using AI"""
    try:
        business = Business.query.get_or_404(business_id)

        product = Product.query.filter_by(
            id=product_id,
            business_id=business_id
        ).first()

        if not product:
            return jsonify({
                'success': False,
                'error': 'Proizvod nije pronađen'
            }), 404

        # Generate rich semantic description using AI
        description = generate_enriched_description(
            product_title=product.title,
            category=product.category
        )

        product.enriched_description = description
        db.session.commit()

        # Re-vectorize
        try:
            from auto_vectorize import auto_vectorize_on_save
            auto_vectorize_on_save(product)
        except Exception as e:
            app.logger.error(f"Auto-vectorization failed: {e}")

        app.logger.info(f"Description regenerated for product {product_id}")

        return jsonify({
            'success': True,
            'description': description,
            'message': 'Opis je uspješno regenerisan'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Regenerate description error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri regeneraciji opisa: {str(e)}'
        }), 500


# Bulk delete selected products
@app.route('/biznisi/<int:business_id>/proizvodi/bulk-delete', methods=['POST'])
@require_jwt_auth
def bulk_delete_products(business_id):
    """Delete multiple selected products"""
    business = Business.query.get_or_404(business_id)

    try:
        data = request.get_json()
        if not data or 'product_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'Nedostaju IDs proizvoda'
            }), 400

        product_ids = data['product_ids']
        if not isinstance(product_ids, list):
            return jsonify({
                'success': False,
                'error': 'product_ids mora biti array'
            }), 400

        # CASCADE will handle related records

        # Validate all products belong to this business
        deleted_count = Product.query.filter(
            Product.id.in_(product_ids),
            Product.business_id == business_id
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Bulk delete error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri brisanju: {str(e)}'
        }), 500


# Regenerate tags for all products
@app.route('/biznisi/<int:business_id>/proizvodi/regenerate-tags', methods=['POST'])
@require_jwt_auth
def regenerate_all_tags(business_id):
    """Regenerate tags for all products in the business"""
    business = Business.query.get_or_404(business_id)

    try:
        # Get all products for this business
        products = Product.query.filter_by(business_id=business_id).all()

        if not products:
            return jsonify({
                'success': False,
                'error': 'Nema proizvoda za regeneraciju tagova'
            }), 400

        app.logger.info(f"Regenerating tags for {len(products)} products...")

        # Process products in batches of 20 to avoid JSON truncation
        BATCH_SIZE = 20
        updated_count = 0
        
        for i in range(0, len(products), BATCH_SIZE):
            batch = products[i:i + BATCH_SIZE]
            
            # Prepare batch data for tag generation
            products_data = []
            for product in batch:
                products_data.append({
                    'title': product.title,
                    'category': product.category,
                    'base_price': product.base_price
                })

            # Generate tags for this batch
            batch_tags = generate_bulk_product_tags(products_data)

            # Update each product in the batch with new tags
            for idx, product in enumerate(batch):
                if idx < len(batch_tags) and batch_tags[idx]:
                    product.tags = batch_tags[idx]
                    # CRITICAL: Mark the tags field as modified for SQLAlchemy to detect the change
                    flag_modified(product, 'tags')
                    updated_count += 1
            
            # Commit after each batch
            db.session.commit()
            app.logger.info(f"Batch {i//BATCH_SIZE + 1}: Generated tags for {len(batch)} products")

        app.logger.info(f"Successfully regenerated tags for {updated_count} products")

        return jsonify({
            'success': True,
            'updated_count': updated_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Tag regeneration error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri regeneraciji tagova: {str(e)}'
        }), 500


# Export products without images to CSV
@app.route('/biznisi/<int:business_id>/proizvodi/export-no-images', methods=['GET'])
@login_required
def export_products_without_images(business_id):
    """Export CSV of products without images for the business"""
    from datetime import date
    business = Business.query.get_or_404(business_id)

    # Get all products without images
    products = Product.query.filter_by(
        business_id=business_id
    ).filter(
        or_(Product.image_path.is_(None), Product.image_path == '')
    ).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['product_id', 'title', 'category', 'base_price', 'discount_price', 'image_url'])

    # Write product rows
    for product in products:
        writer.writerow([
            product.id,
            product.title,
            product.category or '',
            product.base_price,
            product.discount_price or '',
            ''  # Empty image_url column for user to fill
        ])

    # Prepare response
    output.seek(0)
    filename = f"{business.name.replace(' ', '_')}_{business_id}_products_no_images.csv"

    response = app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )

    return response


# Import product images from CSV
@app.route('/biznisi/<int:business_id>/proizvodi/import-images', methods=['POST'])
@login_required
def import_product_images(business_id):
    """Import product images from CSV with S3 URLs"""
    business = Business.query.get_or_404(business_id)

    try:
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nema CSV datoteke'
            }), 400

        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Datoteka nije odabrana'
            }), 400

        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'Datoteka mora biti CSV format'
            }), 400

        # Read CSV
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
        csv_reader = csv.DictReader(stream)

        # Validate headers
        required_headers = ['product_id', 'image_url']
        if not all(header in csv_reader.fieldnames for header in required_headers):
            return jsonify({
                'success': False,
                'error': f'CSV mora imati kolone: {", ".join(required_headers)}'
            }), 400

        updated_count = 0
        skipped_count = 0
        errors = []

        for idx, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
            try:
                product_id = row.get('product_id', '').strip()
                image_url = row.get('image_url', '').strip()

                # Skip if no image URL
                if not image_url:
                    skipped_count += 1
                    continue

                # Validate product belongs to this business
                product = Product.query.filter_by(
                    id=product_id,
                    business_id=business_id
                ).first()

                if not product:
                    errors.append(f"Red {idx}: Proizvod ID {product_id} nije pronađen")
                    skipped_count += 1
                    continue

                # Save S3 URL directly to database
                try:
                    # Validate that it's a valid URL
                    from urllib.parse import urlparse
                    parsed_url = urlparse(image_url)

                    if not parsed_url.scheme or not parsed_url.netloc:
                        errors.append(f"Red {idx}: Nevažeći URL format")
                        skipped_count += 1
                        continue

                    # Update product record with S3 URL
                    old_image = product.image_path
                    product.image_path = image_url

                    # Explicitly mark as modified and add to session
                    db.session.add(product)

                    app.logger.info(f"Updated product {product_id}: '{old_image}' -> '{image_url}'")
                    updated_count += 1

                except Exception as e:
                    errors.append(f"Red {idx}: Greška pri obradi URL-a - {str(e)}")
                    skipped_count += 1
                    continue

            except Exception as e:
                errors.append(f"Red {idx}: {str(e)}")
                skipped_count += 1
                continue

        # Flush and commit all changes
        if updated_count > 0:
            db.session.flush()
            app.logger.info(f"Flushed {updated_count} product image updates")

        db.session.commit()
        app.logger.info(f"Committed {updated_count} product image updates")

        response = {
            'success': True,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'message': f"Uspješno ažurirano {updated_count} slika proizvoda"
        }

        if errors:
            response['errors'] = errors
            response['message'] += f". Preskočeno {skipped_count} stavki."

        return jsonify(response)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Image import error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri importu: {str(e)}'
        }), 500


# Business invitation creation
@app.route('/biznisi/<int:business_id>/invite', methods=['POST'])
@login_required
@business_role_required('owner')
def create_business_invitation(business_id):
    """Create and send business invitation"""
    business = Business.query.get_or_404(business_id)
    data = request.get_json() if request.is_json else request.form

    email = data.get('email', '').strip().lower()
    role = data.get('role', 'staff')

    # Validate input
    if not email or '@' not in email:
        return jsonify({'error': 'Molimo unesite valjan email'}), 400

    if role not in ['owner', 'manager', 'staff']:
        return jsonify({'error': 'Nevažeća uloga'}), 400

    # Check if user is already a member
    existing_membership = BusinessMembership.query.filter_by(
        business_id=business_id,
        user_id=db.session.query(
            User.id).filter_by(email=email).scalar()).first()

    if existing_membership and existing_membership.is_active:
        return jsonify({'error': 'Korisnik je već član ovog biznisa'}), 400

    # Check if there's already an active invitation
    existing_invitation = BusinessInvitation.query.filter_by(
        business_id=business_id,
        email=email).filter(BusinessInvitation.revoked_at.is_(None),
                            BusinessInvitation.accepted_at.is_(None),
                            BusinessInvitation.expires_at
                            > datetime.now()).first()

    if existing_invitation:
        return jsonify({'error':
                        'Aktivan poziv već postoji za ovaj email'}), 400

    try:
        # Generate invitation token
        token = BusinessInvitation.generate_token()
        token_hash = BusinessInvitation.hash_token(token)

        # Create invitation record
        invitation = BusinessInvitation(
            business_id=business_id,
            email=email,
            token_hash=token_hash,
            role=role,
            invited_by_user_id=current_user.id,
            expires_at=datetime.now() + timedelta(days=7)  # 7 days expiry
        )

        db.session.add(invitation)
        db.session.commit()

        # Send invitation email
        base_url = request.host_url.rstrip('/')
        email_sent = send_invitation_email(email=email,
                                           business_name=business.name,
                                           role=role,
                                           invitation_token=token,
                                           base_url=base_url)

        if email_sent:
            return jsonify({
                'success': True,
                'message': f'Poziv je uspješno poslan na {email}'
            })
        else:
            # Delete invitation if email failed
            db.session.delete(invitation)
            db.session.commit()
            return jsonify({'error': 'Greška pri slanju email poziva'}), 500

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Invitation creation error: {str(e)}")
        return jsonify({'error': 'Greška pri kreiranju poziva'}), 500


# Team management routes
@app.route('/biznisi/<int:business_id>/team')
@login_required
@business_role_required('owner')
def view_team(business_id):
    """View team members and invitations for a business"""
    business = Business.query.get_or_404(business_id)

    # Get all team members
    members = db.session.query(BusinessMembership, User).join(
        User, BusinessMembership.user_id == User.id).filter(
            BusinessMembership.business_id == business_id).all()

    # Get all invitations
    invitations = BusinessInvitation.query.filter_by(
        business_id=business_id).order_by(
            BusinessInvitation.created_at.desc()).all()

    return render_template('team_management.html',
                           business=business,
                           members=members,
                           invitations=invitations)


@app.route('/biznisi/<int:business_id>/team/data')
@login_required
@business_role_required('owner')
def get_team_data(business_id):
    """Get team data as JSON for AJAX requests"""
    business = Business.query.get_or_404(business_id)

    # Get team members with user info
    members_query = db.session.query(BusinessMembership, User).join(
        User, BusinessMembership.user_id == User.id).filter(
            BusinessMembership.business_id == business_id).all()

    members = []
    for membership, user in members_query:
        members.append({
            'id': membership.id,
            'user_id': user.id,
            'email': user.email,
            'role': membership.role,
            'joined_at': membership.created_at.strftime('%d.%m.%Y'),
            'is_active': membership.is_active
        })

    # Get invitations
    invitations_query = BusinessInvitation.query.filter_by(
        business_id=business_id).order_by(
            BusinessInvitation.created_at.desc()).all()

    invitations = []
    for invitation in invitations_query:
        status = 'pending'
        if invitation.is_revoked:
            status = 'revoked'
        elif invitation.is_accepted:
            status = 'accepted'
        elif invitation.is_expired:
            status = 'expired'

        invitations.append({
            'id':
            invitation.id,
            'email':
            invitation.email,
            'role':
            invitation.role,
            'status':
            status,
            'invited_at':
            invitation.created_at.strftime('%d.%m.%Y'),
            'expires_at':
            invitation.expires_at.strftime('%d.%m.%Y')
            if invitation.expires_at else 'N/A',
            'is_active':
            invitation.is_active
        })

    return jsonify({'members': members, 'invitations': invitations})


@app.route('/biznisi/<int:business_id>/invitations/<int:invitation_id>/revoke',
           methods=['POST'])
@login_required
@business_role_required('owner')
def revoke_invitation(business_id, invitation_id):
    """Revoke a business invitation"""
    invitation = BusinessInvitation.query.filter_by(
        id=invitation_id, business_id=business_id).first_or_404()

    if invitation.is_revoked:
        return jsonify({'error': 'Poziv je već opozvan'}), 400

    if invitation.is_accepted:
        return jsonify({'error': 'Ne možete opozvati prihvaćen poziv'}), 400

    invitation.revoked_at = datetime.now()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Poziv je uspješno opozvan'})


@app.route('/biznisi/<int:business_id>/members/<int:membership_id>/remove',
           methods=['POST'])
@login_required
@business_role_required('owner')
def remove_team_member(business_id, membership_id):
    """Remove a team member from business"""
    membership = BusinessMembership.query.filter_by(
        id=membership_id, business_id=business_id).first_or_404()

    # Don't allow removing yourself
    if membership.user_id == current_user.id:
        return jsonify({'error': 'Ne možete ukloniti sebe iz biznisa'}), 400

    # Check if this is the last owner
    if membership.role == 'owner':
        owner_count = BusinessMembership.query.filter_by(
            business_id=business_id, role='owner').count()
        if owner_count <= 1:
            return jsonify(
                {'error':
                 'Ne možete ukloniti poslednjeg vlasnika biznisa'}), 400

    db.session.delete(membership)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Član tima je uspješno uklonjen'
    })


@app.route('/biznisi/<int:business_id>/members/<int:membership_id>/role',
           methods=['POST'])
@login_required
@business_role_required('owner')
def change_member_role(business_id, membership_id):
    """Change a team member's role"""
    membership = BusinessMembership.query.filter_by(
        id=membership_id, business_id=business_id).first_or_404()

    data = request.get_json() if request.is_json else request.form
    new_role = data.get('role')

    if new_role not in ['owner', 'manager', 'staff']:
        return jsonify({'error': 'Nevažeća uloga'}), 400

    # Don't allow changing your own role if you're the owner
    if membership.user_id == current_user.id and membership.role == 'owner' and new_role != 'owner':
        return jsonify({'error':
                        'Ne možete promijeniti svoju ulogu vlasnika'}), 400

    # Check if this would remove the last owner
    if membership.role == 'owner' and new_role != 'owner':
        owner_count = BusinessMembership.query.filter_by(
            business_id=business_id, role='owner').count()
        if owner_count <= 1:
            return jsonify(
                {'error':
                 'Ne možete promijeniti ulogu poslednjeg vlasnika'}), 400

    membership.role = new_role
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Uloga je uspješno promijenjena'
    })


# Admin PDF Import
@app.route('/admin/import-pdf', methods=['POST'])
@login_required
def import_pdf():
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({'error':
                        'Access denied. Admin privileges required.'}), 403

    try:
        data = request.get_json()
        pdf_url = data.get('pdf_url')

        if not pdf_url:
            return jsonify({'error': 'PDF URL is required'}), 400

        # Parse PDF - temporarily disabled due to PyMuPDF issue
        # result = parse_pdf_from_url(pdf_url)
        return jsonify(
            {'error':
             'PDF parsing temporarily disabled due to library issue'}), 500

        if not result['success']:
            return jsonify({'error': result['error']}), 500

        # Import businesses and products to database
        businesses_created = 0
        businesses_updated = 0
        products_created = 0
        products_updated = 0
        warnings = []

        for business_data in result['businesses']:
            # Check if business exists
            existing_business = Business.query.filter_by(
                name=business_data['name'],
                city=business_data.get('city', '')).first()

            if existing_business:
                # Update existing business
                existing_business.contact_phone = business_data.get(
                    'contact_phone', '')
                businesses_updated += 1
                business = existing_business
            else:
                # Create new business
                business = Business(name=business_data['name'],
                                    city=business_data.get('city', ''),
                                    contact_phone=business_data.get(
                                        'contact_phone', ''),
                                    category='Uvoz iz PDF',
                                    source_url=pdf_url,
                                    imported_at=datetime.utcnow())
                db.session.add(business)
                db.session.flush()  # Get business ID
                businesses_created += 1

            # Add products
            for product_data in business_data['products']:
                # Check if product exists
                existing_product = Product.query.filter_by(
                    business_id=business.id,
                    title=product_data['title']).first()

                if existing_product:
                    # Update existing product
                    existing_product.base_price = product_data.get(
                        'base_price', 0)
                    existing_product.discount_price = product_data.get(
                        'discount_price')
                    existing_product.discount_percentage = product_data.get(
                        'discount_percentage', 0)
                    existing_product.expires = product_data.get('expires')
                    products_updated += 1
                else:
                    # Create new product
                    product = Product(
                        business_id=business.id,
                        title=product_data['title'],
                        base_price=product_data.get('base_price', 0),
                        discount_price=product_data.get('discount_price'),
                        discount_percentage=product_data.get(
                            'discount_percentage', 0),
                        expires=product_data.get('expires'),
                        city=business.city,
                        source_url=pdf_url,
                        page_number=product_data.get('page', 1))
                    db.session.add(product)
                    products_created += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'summary': {
                'businesses_created': businesses_created,
                'businesses_updated': businesses_updated,
                'products_created': products_created,
                'products_updated': products_updated,
                'pages_processed': result['pages_processed'],
                'warnings': warnings
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


# Admin Dashboard
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Nemate dozvolu za pristup admin stranici.', 'error')
        return redirect(url_for('index'))

    # Get pagination parameters
    searches_page = request.args.get('searches_page', 1, type=int)
    per_page = 10

    # Get statistics
    total_users = db.session.query(User).count()
    total_businesses = db.session.query(Business).count()
    total_products = db.session.query(Product).count()
    total_searches = db.session.query(UserSearch).count()

    # Get recent activity
    recent_users = db.session.query(User).order_by(
        User.created_at.desc()).limit(5).all()

    # Get paginated searches with user information
    searches_query = db.session.query(UserSearch, User).outerjoin(
        User,
        UserSearch.user_id == User.id).order_by(UserSearch.created_at.desc())

    searches_pagination = searches_query.paginate(page=searches_page,
                                                  per_page=per_page,
                                                  error_out=False)

    recent_businesses = db.session.query(Business).order_by(
        Business.id.desc()).limit(5).all()

    # Get today's activity
    today = date.today()
    start_today = datetime.combine(today, time.min)
    end_today = start_today + timedelta(days=1)

    today_users = db.session.query(User).filter(
        and_(User.created_at >= start_today, User.created_at
             < end_today)).count()

    today_searches = db.session.query(UserSearch).filter(
        and_(UserSearch.created_at >= start_today, UserSearch.created_at
             < end_today)).count()

    # Get monthly statistics
    this_month = datetime.now().replace(day=1)
    monthly_users = db.session.query(User).filter(
        User.created_at >= this_month).count()

    monthly_searches = db.session.query(UserSearch).filter(
        UserSearch.created_at >= this_month).count()

    stats = {
        'total_users': total_users,
        'total_businesses': total_businesses,
        'total_products': total_products,
        'total_searches': total_searches,
        'today_users': today_users,
        'today_searches': today_searches,
        'monthly_users': monthly_users,
        'monthly_searches': monthly_searches
    }

    return render_template('admin_dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           searches_pagination=searches_pagination,
                           recent_businesses=recent_businesses)


# Parse PDF and add to specific business
@app.route('/admin/import-pdf-to-business', methods=['POST'])
@login_required
def import_pdf_to_business():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    pdf_url = data.get('pdf_url')
    business_name = data.get('business_name', '').strip()

    if not pdf_url or not business_name:
        return jsonify({'error': 'PDF URL and business name required'}), 400

    try:
        # Find the business
        business = db.session.query(Business).filter(
            Business.name.ilike(f'%{business_name}%')).first()

        if not business:
            return jsonify({'error':
                            f'Business "{business_name}" not found'}), 404

        # Parse PDF - temporarily disabled due to PyMuPDF issue
        # result = parse_pdf_from_url(pdf_url)
        return jsonify(
            {'error':
             'PDF parsing temporarily disabled due to library issue'}), 500

        if not result.get('success'):
            return jsonify({
                'error': 'Failed to parse PDF',
                'details': result.get('error')
            }), 500

        # Add products to the specific business
        products_added = 0
        businesses_data = result.get('businesses', [])

        # Find the matching business in the PDF data
        matched_business = None
        for business_data in businesses_data:
            pdf_business_name = business_data.get('name', '').lower()
            if business_name.lower(
            ) in pdf_business_name or pdf_business_name in business_name.lower(
            ):
                matched_business = business_data
                break

        if not matched_business:
            return jsonify({
                'error':
                f'No business matching "{business_name}" found in PDF. Found businesses: {[b.get("name", "Unknown") for b in businesses_data]}'
            }), 404

        # Process only the matched business's products
        business_data = matched_business
        products_data = business_data.get('products', [])

        for product_data in products_data:
            try:
                # Clean product title and ensure it's valid
                title = product_data.get('title', '').strip()
                if not title or len(title) < 3:
                    continue

                # Get price information
                base_price = product_data.get('base_price', 0)
                if base_price <= 0:
                    continue  # Skip products without valid prices

                # Check if product already exists for this business
                existing_product = db.session.query(Product).filter_by(
                    business_id=business.id, title=title).first()

                if existing_product:
                    continue  # Skip duplicates

                # Extract category from title if possible
                category = 'Ostalo'
                title_lower = title.lower()
                if any(word in title_lower for word in
                       ['meso', 'govedina', 'svinjski', 'piletina']):
                    category = 'Meso'
                elif any(word in title_lower
                         for word in ['mlijeko', 'sir', 'jogurt']):
                    category = 'Mlijećni proizvodi'
                elif any(word in title_lower
                         for word in ['ulje', 'filter', 'auto']):
                    category = 'Auto dijelovi'
                elif any(word in title_lower
                         for word in ['voće', 'povrće', 'banana', 'jabuka']):
                    category = 'Voće i povrće'

                # Create new product
                product = Product(
                    business_id=business.id,
                    title=title,
                    base_price=float(base_price),
                    discount_price=float(product_data.get('discount_price'))
                    if product_data.get('discount_price') else None,
                    category=category,
                    tags=[],
                    product_metadata={
                        'parsed_from_pdf':
                        True,
                        'page_number':
                        product_data.get('page', 1),
                        'discount_percentage':
                        product_data.get('discount_percentage', 0)
                    },
                    city=business.city,
                    created_at=datetime.utcnow())

                db.session.add(product)
                products_added += 1
                print(f"Added product: {title} - {base_price} KM")

            except Exception as e:
                print(
                    f"Error adding product {product_data.get('title', 'Unknown')}: {str(e)}"
                )
                continue

        db.session.commit()

        return jsonify({
            'success':
            True,
            'message':
            f'Successfully added {products_added} products to {business.name}',
            'business_name':
            business.name,
            'business_id':
            business.id,
            'products_added':
            products_added,
            'businesses_found':
            len(businesses_data),
            'matched_business':
            matched_business.get('name', 'Unknown'),
            'pages_processed':
            result.get('pages_processed', 0)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


# Admin view all products
@app.route('/admin/products')
@login_required
def admin_view_products():
    if not current_user.is_admin:
        flash('Nemate dozvolu za pristup admin stranici.', 'error')
        return redirect(url_for('index'))

    # Get all products with their business information
    products = db.session.query(Product, Business).join(Business).order_by(
        Business.name, Product.title).all()

    # Group products by business
    businesses_with_products = {}
    for product, business in products:
        if business.name not in businesses_with_products:
            businesses_with_products[business.name] = {
                'business': business,
                'products': []
            }
        businesses_with_products[business.name]['products'].append(product)

    # Get summary stats
    total_products = len(products)
    total_businesses_with_products = len(businesses_with_products)

    return render_template(
        'admin_products.html',
        businesses_with_products=businesses_with_products,
        total_products=total_products,
        total_businesses_with_products=total_businesses_with_products)


# Test PDF import endpoint (admin only)
@app.route('/admin/test-pdf-import')
@login_required
def test_pdf_import():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403

    # Test with the provided Google Drive URL
    test_url = "https://drive.google.com/file/d/1UggxsqeqUR78v8vLA8UV4lOq1H2JMmo7/view?usp=sharing"

    try:
        # result = parse_pdf_from_url(test_url)  # Temporarily disabled due to PyMuPDF issue
        return jsonify({
            'success':
            False,
            'error':
            'PDF parsing temporarily disabled due to library issue'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# Admin API endpoints (JWT-based)
@app.route('/api/admin/stats')
def api_admin_stats():
    """API endpoint for admin statistics - JWT protected"""
    from auth_api import require_jwt_auth

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from auth_api import decode_jwt_token
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        user = User.query.filter_by(id=payload['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get statistics
        total_users = db.session.query(User).count()
        total_businesses = db.session.query(Business).count()
        total_products = db.session.query(Product).count()
        total_searches = db.session.query(UserSearch).count()

        # Get embedding statistics
        from models import ProductEmbedding, ProductReport
        products_with_embeddings = db.session.query(ProductEmbedding).count()

        # Get pending reports count
        pending_reports = db.session.query(ProductReport).filter_by(status='pending').count()
        products_without_embeddings = total_products - products_with_embeddings

        # Get active (non-expired) products count
        active_products = db.session.query(Product).filter(
            db.or_(Product.expires == None, Product.expires >= date.today())
        ).count()
        expired_products = total_products - active_products

        # Get today's activity
        today = date.today()
        start_today = datetime.combine(today, time.min)
        end_today = start_today + timedelta(days=1)

        today_users = db.session.query(User).filter(
            and_(User.created_at >= start_today, User.created_at < end_today)).count()

        today_searches = db.session.query(UserSearch).filter(
            and_(UserSearch.created_at >= start_today, UserSearch.created_at < end_today)).count()

        # Get monthly statistics
        this_month = datetime.now().replace(day=1)
        monthly_users = db.session.query(User).filter(
            User.created_at >= this_month).count()

        monthly_searches = db.session.query(UserSearch).filter(
            UserSearch.created_at >= this_month).count()

        # Get recent users
        recent_users = db.session.query(User).order_by(
            User.created_at.desc()).limit(10).all()

        # Get recent searches (30 for full-width table)
        recent_searches = db.session.query(UserSearch, User).outerjoin(
            User, UserSearch.user_id == User.id).order_by(
            UserSearch.created_at.desc()).limit(30).all()

        # Get recent businesses
        recent_businesses = db.session.query(Business).order_by(
            Business.id.desc()).limit(10).all()

        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_businesses': total_businesses,
                'total_products': total_products,
                'total_searches': total_searches,
                'today_users': today_users,
                'today_searches': today_searches,
                'monthly_users': monthly_users,
                'monthly_searches': monthly_searches,
                'products_with_embeddings': products_with_embeddings,
                'products_without_embeddings': products_without_embeddings,
                'active_products': active_products,
                'expired_products': expired_products,
                'pending_reports': pending_reports
            },
            'recent_users': [{
                'id': u.id,
                'email': u.email,
                'name': f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'is_admin': u.is_admin,
                'is_verified': u.is_verified
            } for u in recent_users],
            'recent_searches': [{
                'id': search.id,
                'query': search.query,
                'user_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email if user else None,
                'user_email': user.email if user else None,
                'created_at': search.created_at.isoformat() if search.created_at else None,
                'device_type': search.device_type,
                'browser': search.browser,
                'os': search.os,
                'only_discounted': search.only_discounted
            } for search, user in recent_searches],
            'recent_businesses': [{
                'id': b.id,
                'name': b.name,
                'city': b.city,
                'status': b.status
            } for b in recent_businesses]
        }), 200

    except Exception as e:
        app.logger.error(f"Admin stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/users')
def api_admin_users():
    """API endpoint for admin to view all users with their registration method and OTP codes"""
    from auth_api import decode_jwt_token
    from models import OTPCode, UserLogin

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        user = User.query.filter_by(id=payload['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()

        # Build query
        query = User.query

        # Search filter
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f'%{search}%'),
                    User.phone.ilike(f'%{search}%'),
                    User.first_name.ilike(f'%{search}%'),
                    User.last_name.ilike(f'%{search}%')
                )
            )

        # Order by most recent
        query = query.order_by(User.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items

        # Get all businesses for mapping store IDs to names
        all_businesses = {b.id: b.name for b in Business.query.all()}

        # Get OTP codes and last login for each user
        user_data = []
        for u in users:
            latest_otp = None
            if u.phone:
                latest_otp_record = OTPCode.query.filter_by(
                    phone=u.phone
                ).order_by(OTPCode.created_at.desc()).first()

                if latest_otp_record:
                    latest_otp = {
                        'code': latest_otp_record.code,
                        'is_used': latest_otp_record.is_used,
                        'expires_at': latest_otp_record.expires_at.isoformat(),
                        'created_at': latest_otp_record.created_at.isoformat(),
                        'expired': latest_otp_record.expires_at < datetime.now()
                    }

            # Get last login info with device details
            last_login = None
            last_login_record = UserLogin.query.filter_by(
                user_id=u.id
            ).order_by(UserLogin.created_at.desc()).first()

            if last_login_record:
                last_login = {
                    'login_method': last_login_record.login_method,
                    'device_type': last_login_record.device_type,
                    'os_name': last_login_record.os_name,
                    'browser_name': last_login_record.browser_name,
                    'ip_address': last_login_record.ip_address,
                    'created_at': last_login_record.created_at.isoformat() if last_login_record.created_at else None
                }

            # Get user's preferred stores
            preferred_store_ids = u.preferences.get('preferred_stores', []) if u.preferences else []
            preferred_stores = [
                {'id': store_id, 'name': all_businesses.get(store_id, f'Unknown ({store_id})')}
                for store_id in preferred_store_ids
                if store_id in all_businesses
            ]

            user_data.append({
                'id': u.id,
                'email': u.email,
                'phone': u.phone,
                'phone_verified': u.phone_verified,
                'registration_method': u.registration_method,
                'is_admin': u.is_admin,
                'is_verified': u.is_verified,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'city': u.city,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'weekly_credits': u.weekly_credits,
                'weekly_credits_used': u.weekly_credits_used,
                'extra_credits': u.extra_credits,
                'latest_otp': latest_otp,
                'last_login': last_login,
                'preferred_stores': preferred_stores
            })

        return jsonify({
            'users': user_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Admin users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/users/<path:user_id>/activity')
def api_admin_user_activity(user_id):
    """API endpoint to get user's daily activity (searches, engagements, proizvodi visits) for the last 7 days"""
    from auth_api import decode_jwt_token
    from models import UserSearch, UserEngagement, UserActivity
    from datetime import timedelta
    from sqlalchemy import func

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get activity for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 7 days including today

        # Get daily search counts
        searches = db.session.query(
            func.date(UserSearch.created_at).label('date'),
            func.count(UserSearch.id).label('count')
        ).filter(
            UserSearch.user_id == user_id,
            UserSearch.created_at >= start_date
        ).group_by(func.date(UserSearch.created_at)).all()

        # Get daily engagement counts
        engagements = db.session.query(
            func.date(UserEngagement.created_at).label('date'),
            func.count(UserEngagement.id).label('count')
        ).filter(
            UserEngagement.user_id == user_id,
            UserEngagement.created_at >= start_date
        ).group_by(func.date(UserEngagement.created_at)).all()

        # Get daily proizvodi page visits
        proizvodi_visits = db.session.query(
            func.date(UserActivity.created_at).label('date'),
            func.count(UserActivity.id).label('count')
        ).filter(
            UserActivity.user_id == user_id,
            UserActivity.page == 'proizvodi',
            UserActivity.activity_type == 'page_view',
            UserActivity.created_at >= start_date
        ).group_by(func.date(UserActivity.created_at)).all()

        # Convert to dict for easier lookup
        search_dict = {str(s.date): s.count for s in searches}
        engagement_dict = {str(e.date): e.count for e in engagements}
        proizvodi_dict = {str(p.date): p.count for p in proizvodi_visits}

        # Build daily activity array for the last 7 days
        activity = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_str = day.strftime('%Y-%m-%d')
            activity.append({
                'date': day_str,
                'day': day.strftime('%a'),  # Short day name
                'searches': search_dict.get(day_str, 0),
                'engagements': engagement_dict.get(day_str, 0),
                'proizvodi': proizvodi_dict.get(day_str, 0)
            })

        return jsonify({
            'user_id': user_id,
            'activity': activity
        }), 200

    except Exception as e:
        app.logger.error(f"Admin user activity error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/otp-codes')
def api_admin_otp_codes():
    """API endpoint for admin to view recent OTP codes for testing"""
    from auth_api import decode_jwt_token
    from models import OTPCode

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        user = User.query.filter_by(id=payload['user_id']).first()
        if not user or not user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        phone_filter = request.args.get('phone', '').strip()

        # Build query
        query = OTPCode.query

        # Phone filter
        if phone_filter:
            query = query.filter(OTPCode.phone.ilike(f'%{phone_filter}%'))

        # Order by most recent
        query = query.order_by(OTPCode.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        otp_codes = pagination.items

        otp_data = [{
            'id': otp.id,
            'phone': otp.phone,
            'code': otp.code,
            'is_used': otp.is_used,
            'attempts': otp.attempts,
            'created_at': otp.created_at.isoformat(),
            'expires_at': otp.expires_at.isoformat(),
            'expired': otp.expires_at < datetime.now()
        } for otp in otp_codes]

        return jsonify({
            'otp_codes': otp_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Admin OTP codes error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/users/<path:user_id>/profile')
def api_admin_user_profile(user_id):
    """API endpoint for admin to get comprehensive user profile"""
    from auth_api import decode_jwt_token
    from models import (User, UserSearch, UserEngagement, CreditTransaction,
                        Favorite, ShoppingList, ProductComment, ProductVote,
                        ProductReport, Notification, BusinessMembership, OTPCode, UserLogin)

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the target user
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404

        # Get last login info
        last_login_record = UserLogin.query.filter_by(
            user_id=user_id
        ).order_by(UserLogin.created_at.desc()).first()

        last_login = None
        if last_login_record:
            last_login = {
                'login_method': last_login_record.login_method,
                'device_type': last_login_record.device_type,
                'os_name': last_login_record.os_name,
                'browser_name': last_login_record.browser_name,
                'ip_address': last_login_record.ip_address,
                'created_at': last_login_record.created_at.isoformat() if last_login_record.created_at else None
            }

        # Basic user info
        user_data = {
            'id': target_user.id,
            'email': target_user.email,
            'phone': target_user.phone,
            'first_name': target_user.first_name,
            'last_name': target_user.last_name,
            'city': target_user.city,
            'is_admin': target_user.is_admin,
            'is_verified': target_user.is_verified,
            'registration_method': target_user.registration_method,
            'referral_code': target_user.referral_code,
            'weekly_credits': target_user.weekly_credits,
            'weekly_credits_used': target_user.weekly_credits_used,
            'extra_credits': target_user.extra_credits,
            'weekly_credits_reset_date': target_user.weekly_credits_reset_date.isoformat() if target_user.weekly_credits_reset_date else None,
            'created_at': target_user.created_at.isoformat() if target_user.created_at else None,
            'updated_at': target_user.updated_at.isoformat() if target_user.updated_at else None,
            'last_login': last_login,
        }

        # Activity stats (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Searches - use db.session.query() because UserSearch has a 'query' column
        total_searches = db.session.query(UserSearch).filter_by(user_id=user_id).count()
        recent_searches = db.session.query(UserSearch).filter(
            UserSearch.user_id == user_id,
            UserSearch.created_at >= thirty_days_ago
        ).count()

        # Engagements (votes, comments, reports)
        total_engagements = UserEngagement.query.filter_by(user_id=user_id).count()
        recent_engagements = UserEngagement.query.filter(
            UserEngagement.user_id == user_id,
            UserEngagement.created_at >= thirty_days_ago
        ).count()

        # Favorites
        total_favorites = Favorite.query.filter_by(user_id=user_id).count()

        # Shopping lists
        total_shopping_lists = ShoppingList.query.filter_by(user_id=user_id).count()
        completed_lists = ShoppingList.query.filter_by(user_id=user_id, status='COMPLETED').count()

        # Comments
        total_comments = ProductComment.query.filter_by(user_id=user_id).count()

        # Votes
        total_votes = ProductVote.query.filter_by(user_id=user_id).count()
        upvotes = ProductVote.query.filter_by(user_id=user_id, vote_type='up').count()
        downvotes = ProductVote.query.filter_by(user_id=user_id, vote_type='down').count()

        # Reports submitted
        total_reports = ProductReport.query.filter_by(user_id=user_id).count()

        # Credits earned from engagements
        total_credits_earned = db.session.query(db.func.sum(UserEngagement.credits_earned)).filter(
            UserEngagement.user_id == user_id
        ).scalar() or 0

        stats = {
            'total_searches': total_searches,
            'recent_searches': recent_searches,
            'total_engagements': total_engagements,
            'recent_engagements': recent_engagements,
            'total_favorites': total_favorites,
            'total_shopping_lists': total_shopping_lists,
            'completed_lists': completed_lists,
            'total_comments': total_comments,
            'total_votes': total_votes,
            'upvotes': upvotes,
            'downvotes': downvotes,
            'total_reports': total_reports,
            'total_credits_earned': total_credits_earned,
        }

        # Activity chart data (last 30 days, grouped by day)
        activity_data = []
        for i in range(30):
            day = datetime.now() - timedelta(days=29-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_searches = db.session.query(UserSearch).filter(
                UserSearch.user_id == user_id,
                UserSearch.created_at >= day_start,
                UserSearch.created_at < day_end
            ).count()

            day_engagements = UserEngagement.query.filter(
                UserEngagement.user_id == user_id,
                UserEngagement.created_at >= day_start,
                UserEngagement.created_at < day_end
            ).count()

            activity_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'day': day_start.strftime('%d %b'),
                'searches': day_searches,
                'engagements': day_engagements
            })

        # Credit transactions (last 50)
        credit_transactions = CreditTransaction.query.filter_by(user_id=user_id).order_by(
            CreditTransaction.created_at.desc()
        ).limit(50).all()

        transactions_data = [{
            'id': t.id,
            'delta': t.delta,
            'balance_after': t.balance_after,
            'action': t.action,
            'metadata': t.metadata,
            'created_at': t.created_at.isoformat()
        } for t in credit_transactions]

        # Credit expenditure by action type
        credit_by_action = db.session.query(
            CreditTransaction.action,
            db.func.sum(CreditTransaction.delta).label('total')
        ).filter(
            CreditTransaction.user_id == user_id
        ).group_by(CreditTransaction.action).all()

        credit_breakdown = {action: int(total) for action, total in credit_by_action}

        # Recent searches (last 20)
        recent_search_list = db.session.query(UserSearch).filter_by(user_id=user_id).order_by(
            UserSearch.created_at.desc()
        ).limit(20).all()

        searches_data = [{
            'id': s.id,
            'query': s.query,
            'created_at': s.created_at.isoformat()
        } for s in recent_search_list]

        # Recent engagements (last 20)
        recent_engagement_list = UserEngagement.query.filter_by(user_id=user_id).order_by(
            UserEngagement.created_at.desc()
        ).limit(20).all()

        engagements_data = []
        for e in recent_engagement_list:
            product = Product.query.get(e.product_id)
            engagements_data.append({
                'id': e.id,
                'activity_type': e.activity_type,
                'product_id': e.product_id,
                'product_title': product.title if product else 'Obrisan proizvod',
                'credits_earned': e.credits_earned,
                'created_at': e.created_at.isoformat()
            })

        # Favorites (last 20)
        recent_favorites = Favorite.query.filter_by(user_id=user_id).order_by(
            Favorite.created_at.desc()
        ).limit(20).all()

        favorites_data = []
        for f in recent_favorites:
            product = Product.query.get(f.product_id)
            favorites_data.append({
                'id': f.id,
                'product_id': f.product_id,
                'product_title': product.title if product else 'Obrisan proizvod',
                'product_image': product.image_path if product else None,
                'created_at': f.created_at.isoformat()
            })

        # Business memberships
        memberships = BusinessMembership.query.filter_by(user_id=user_id, is_active=True).all()
        memberships_data = []
        for m in memberships:
            business = Business.query.get(m.business_id)
            memberships_data.append({
                'business_id': m.business_id,
                'business_name': business.name if business else 'Nepoznato',
                'role': m.role,
                'created_at': m.created_at.isoformat()
            })

        # Latest OTP code
        latest_otp = OTPCode.query.filter_by(phone=target_user.phone).order_by(
            OTPCode.created_at.desc()
        ).first() if target_user.phone else None

        otp_data = None
        if latest_otp:
            otp_data = {
                'code': latest_otp.code,
                'is_used': latest_otp.is_used,
                'created_at': latest_otp.created_at.isoformat(),
                'expires_at': latest_otp.expires_at.isoformat(),
                'expired': latest_otp.expires_at < datetime.now()
            }

        return jsonify({
            'user': user_data,
            'stats': stats,
            'activity_chart': activity_data,
            'credit_transactions': transactions_data,
            'credit_breakdown': credit_breakdown,
            'recent_searches': searches_data,
            'recent_engagements': engagements_data,
            'recent_favorites': favorites_data,
            'business_memberships': memberships_data,
            'latest_otp': otp_data
        }), 200

    except Exception as e:
        app.logger.error(f"Admin user profile error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ==================== ADMIN PRODUCTS API ====================

@app.route('/api/admin/products')
def api_admin_products():
    """API endpoint to get all products grouped by business for admin panel"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
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
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 401

    # Get all products with their business information
    products = db.session.query(Product, Business).join(Business).order_by(
        Business.name, Product.title).all()

    # Group products by business
    businesses_dict = {}
    for product, business in products:
        if business.id not in businesses_dict:
            businesses_dict[business.id] = {
                'id': business.id,
                'name': business.name,
                'logo': business.logo_path,
                'products': []
            }
        businesses_dict[business.id]['products'].append({
            'id': product.id,
            'title': product.title,
            'base_price': float(product.base_price) if product.base_price else 0,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_path': product.image_path,
            'expires': product.expires.isoformat() if product.expires else None,
            'category': product.category,
            'category_group': product.category_group,
            'tags': product.tags,
            'enriched_description': product.enriched_description
        })

    # Convert to list and sort by business name
    businesses_with_products = sorted(businesses_dict.values(), key=lambda x: x['name'])

    # Get summary stats
    total_products = len(products)
    total_businesses = len(businesses_with_products)
    products_with_images = sum(1 for p, _ in products if p.image_path)
    products_with_discounts = sum(1 for p, _ in products if p.discount_price and p.discount_price < (p.base_price or 0))

    return jsonify({
        'stats': {
            'total_products': total_products,
            'total_businesses': total_businesses,
            'products_with_images': products_with_images,
            'products_with_discounts': products_with_discounts
        },
        'businesses_with_products': businesses_with_products
    })


# ==================== IMAGE SUGGESTION ENDPOINTS ====================

@app.route('/api/admin/products/<int:product_id>/suggest-images', methods=['POST'])
def api_admin_suggest_images(product_id):
    """Search for images and upload suggestions to S3"""
    from auth_api import decode_jwt_token
    from image_search import search_and_upload_suggestions, delete_suggestions_from_s3

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Save original image if not already saved
        if not product.original_image_path and product.image_path:
            product.original_image_path = product.image_path
            db.session.commit()

        # Get custom query from request body, fallback to product title
        data = request.get_json() or {}
        custom_query = data.get('query')
        search_query = custom_query or product.title
        is_custom_query = bool(custom_query)

        # Delete old suggestions first
        delete_suggestions_from_s3(product_id)

        # Search and upload new suggestions
        # If user provided custom query, use it as-is; otherwise clean up product title
        suggestions = search_and_upload_suggestions(product_id, search_query, num_images=10, is_custom_query=is_custom_query)

        if not suggestions:
            return jsonify({
                'success': True,
                'suggested_images': [],
                'original_image_path': product.original_image_path,
                'message': 'No images found for this product'
            }), 200

        # Save suggestions to database
        product.suggested_images = suggestions
        db.session.commit()

        return jsonify({
            'success': True,
            'suggested_images': suggestions,
            'original_image_path': product.original_image_path
        }), 200

    except Exception as e:
        app.logger.error(f"Image suggestion error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>/select-image', methods=['POST'])
def api_admin_select_image(product_id):
    """Select one of the suggested images as the main product image"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        data = request.get_json()
        selected_path = data.get('image_path')

        if not selected_path:
            return jsonify({'error': 'image_path is required'}), 400

        # Verify the selected path is in suggestions
        if product.suggested_images and selected_path not in product.suggested_images:
            return jsonify({'error': 'Invalid image path'}), 400

        # Build the full S3 URL
        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
        region = os.environ.get('AWS_REGION', 'eu-central-1')
        full_url = f"https://{bucket}.s3.{region}.amazonaws.com/{selected_path}"

        # Store original image path if not already stored and current image exists
        if not product.original_image_path and product.image_path:
            product.original_image_path = product.image_path

        # Update product image with full URL
        product.image_path = full_url
        db.session.commit()

        return jsonify({
            'success': True,
            'image_path': product.image_path,
            'original_image': product.original_image_path
        }), 200

    except Exception as e:
        app.logger.error(f"Select image error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>/revert-image', methods=['POST'])
def api_admin_revert_image(product_id):
    """Revert to the original image"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if not product.original_image_path:
            return jsonify({'error': 'No original image available'}), 400

        # Revert to original
        product.image_path = product.original_image_path
        db.session.commit()

        return jsonify({
            'success': True,
            'image_path': product.image_path
        }), 200

    except Exception as e:
        app.logger.error(f"Revert image error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>/upload-cropped-image', methods=['POST'])
def api_admin_upload_cropped_image(product_id):
    """Upload a cropped image for a product"""
    from auth_api import decode_jwt_token
    import boto3
    from botocore.exceptions import ClientError
    import uuid

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get uploaded file
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        image_file = request.files['image']
        if not image_file:
            return jsonify({'error': 'Empty image file'}), 400

        # Read image data
        image_data = image_file.read()

        # Generate unique filename
        unique_id = uuid.uuid4().hex[:8]
        s3_path = f"popust/products/{product_id}/cropped_{unique_id}.jpg"

        # Upload to S3
        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
        region = os.environ.get('AWS_REGION', 'eu-central-1')

        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=region
        )

        s3_client.put_object(
            Bucket=bucket,
            Key=s3_path,
            Body=image_data,
            ContentType='image/jpeg',
            CacheControl='max-age=31536000'
        )

        # Build full URL
        full_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_path}"

        # Update product
        product.image_path = full_url
        db.session.commit()

        return jsonify({
            'success': True,
            'image_path': full_url
        }), 200

    except ClientError as e:
        app.logger.error(f"S3 upload error: {e}")
        return jsonify({'error': 'Failed to upload image'}), 500
    except Exception as e:
        app.logger.error(f"Upload cropped image error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>/suggested-images', methods=['GET'])
def api_admin_get_suggested_images(product_id):
    """Get suggested images for a product"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify({
            'suggestions': product.suggested_images or [],
            'current_image': product.image_path,
            'original_image': product.original_image_path
        }), 200

    except Exception as e:
        app.logger.error(f"Get suggested images error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/images', methods=['GET'])
def api_admin_products_images():
    """Get all products with image info for bulk image matching"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get all products with business info
        products = db.session.query(Product, Business).join(
            Business, Product.business_id == Business.id
        ).order_by(Product.id.desc()).all()

        products_list = []
        stats = {
            'total': 0,
            'has_image': 0,
            'no_image': 0,
            'has_original': 0,
            'has_suggestions': 0
        }

        for product, business in products:
            stats['total'] += 1

            has_image = bool(product.image_path)
            has_original = bool(product.original_image_path)
            has_suggestions = bool(product.suggested_images and len(product.suggested_images) > 0)

            if has_image:
                stats['has_image'] += 1
            else:
                stats['no_image'] += 1

            if has_original:
                stats['has_original'] += 1

            if has_suggestions:
                stats['has_suggestions'] += 1

            products_list.append({
                'id': product.id,
                'title': product.title,
                'image_path': product.image_path,
                'original_image_path': product.original_image_path,
                'suggested_images': product.suggested_images or [],
                'business_id': business.id,
                'business_name': business.name,
                'category': product.category
            })

        return jsonify({
            'products': products_list,
            'stats': stats
        }), 200

    except Exception as e:
        app.logger.error(f"Get products images error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>/ai-match-images', methods=['POST'])
@csrf.exempt
def api_admin_ai_match_images(product_id):
    """Run AI image matching for a product using GPT-4o Vision"""
    from auth_api import decode_jwt_token
    from image_search import search_and_upload_suggestions, delete_suggestions_from_s3
    from image_matcher import match_product_images

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get the product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Check if we already have suggested images, if not fetch them
        suggested_images = product.suggested_images or []

        if not suggested_images:
            # Delete old suggestions first
            delete_suggestions_from_s3(product_id)

            # Search and upload new suggestions
            suggested_images = search_and_upload_suggestions(
                product_id,
                product.title,
                num_images=10,
                is_custom_query=False
            )

            if suggested_images:
                product.suggested_images = suggested_images
                db.session.commit()

        if not suggested_images:
            return jsonify({
                'matches': [],
                'best_match': None,
                'analysis': 'No images found for this product'
            }), 200

        # Run AI matching with GPT-4o Vision
        result = match_product_images(
            product_title=product.title,
            original_image_path=product.original_image_path,
            suggested_image_paths=suggested_images
        )

        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"AI image match error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# Valid category groups for products
VALID_CATEGORY_GROUPS = [
    'meso', 'mlijeko', 'pica', 'voce_povrce', 'kuhinja', 'ves', 'ciscenje',
    'higijena', 'slatkisi', 'kafa', 'smrznuto', 'pekara', 'ljubimci', 'bebe'
]

@app.route('/api/admin/products/categorize', methods=['POST'])
@csrf.exempt
def api_admin_categorize_products():
    """Categorize products for a business using AI (OpenAI)"""
    from auth_api import decode_jwt_token
    from openai_utils import openai_client

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        business_id = data.get('business_id')

        if not business_id:
            return jsonify({'error': 'business_id is required'}), 400

        # System prompt for categorization
        system_prompt = """You are a product categorization expert for a Bosnian marketplace.

Your task: Assign each product to ONE of these category groups based on its title, category, and tags.

CATEGORY GROUPS:
- meso: Meat products (chicken, beef, pork, sausages, deli meats, salami, pašteta)
- mlijeko: Dairy products (milk, yogurt, cheese, kajmak, butter, cream, pudding, vrhnje)
- pica: Beverages (water, juice, soda, beer, wine, energy drinks, sokovi)
- voce_povrce: Fresh fruits and vegetables
- kuhinja: Kitchen staples (oil, flour, sugar, salt, spices, rice, pasta, canned goods, začini, ulje)
- ves: Laundry products (detergent, fabric softener, stain remover, deterdzent za veš, omekšivač)
- ciscenje: Cleaning products (floor cleaner, dish soap, disinfectant, wipes, odmašćivač, sredstvo za čišćenje, osvježivač)
- higijena: Personal hygiene (shampoo, soap, toothpaste, deodorant, toilet paper, šampon, gel za tuširanje, krema)
- slatkisi: Sweets and snacks (chocolate, candy, chips, cookies, biscuits, čokolada, keks, grickalice)
- kafa: Coffee and tea products (kafa, čaj, coffee, tea)
- smrznuto: Frozen products (frozen vegetables, pizza, ice cream, frozen meals, smrznuto)
- pekara: Bakery products (bread, rolls, pastries, hljeb, pecivo)
- ljubimci: Pet supplies (pet food, treats, accessories, hrana za pse, hrana za mačke)
- bebe: Baby products (diapers, baby food, wipes, formula, pelene, dječija hrana)

RULES:
1. Return ONLY valid category group IDs from the list above
2. Use title, category AND tags together to make the best decision
3. "Kućne potrepštine" could be: ves (laundry), ciscenje (cleaning), or higijena (personal care) - use title keywords
4. "Namirnice" could be: kuhinja, slatkisi, or other food categories - determine from specific product
5. Products with "deterdžent za veš" or "omekšivač" = ves
6. Products with "odmašćivač", "sredstvo za", "osvježivač" = ciscenje
7. Products with "šampon", "gel", "krema", "sapun" for body = higijena
8. ALWAYS return a category - make your best guess if unsure

Return ONLY valid JSON:
[
  {"id": 123, "category_group": "meso"},
  {"id": 456, "category_group": "mlijeko"}
]"""

        # Loop until all products are categorized
        total_updated = 0
        batch_size = 50  # Process 50 at a time for better accuracy
        max_iterations = 20  # Safety limit

        for iteration in range(max_iterations):
            # Get products without category_group for this business
            products = Product.query.filter(
                Product.business_id == business_id,
                (Product.category_group.is_(None) | (Product.category_group == ''))
            ).limit(batch_size).all()

            if not products:
                break  # No more products to categorize

            # Prepare products for AI - include tags for better categorization
            products_for_ai = []
            for p in products:
                # Get tags as string if available
                tags_str = ''
                if p.tags:
                    if isinstance(p.tags, list):
                        tags_str = ', '.join(p.tags[:5])  # Limit to 5 tags
                    elif isinstance(p.tags, str):
                        tags_str = p.tags

                products_for_ai.append({
                    'id': p.id,
                    'title': p.title,
                    'category': p.category or '',
                    'tags': tags_str
                })

            user_prompt = f"""Categorize these products using title, category and tags:

{json.dumps(products_for_ai, ensure_ascii=False, indent=2)}

Return category_group for each product ID. Use ALL available info (title + category + tags) to determine the best category."""

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=4000
            )

            result_text = response.choices[0].message.content.strip()

            # Parse response - handle both array and object with array
            try:
                result = json.loads(result_text)
                if isinstance(result, dict) and 'products' in result:
                    categorizations = result['products']
                elif isinstance(result, list):
                    categorizations = result
                else:
                    # Try to find array in the response
                    categorizations = list(result.values())[0] if result else []
            except:
                app.logger.error(f"Failed to parse AI response: {result_text}")
                continue  # Try next batch

            # Update products in database
            batch_updated = 0
            for cat_item in categorizations:
                product_id = cat_item.get('id')
                category_group = cat_item.get('category_group', '').lower()

                if product_id and category_group in VALID_CATEGORY_GROUPS:
                    product = Product.query.get(product_id)
                    if product:
                        product.category_group = category_group
                        batch_updated += 1

            db.session.commit()
            total_updated += batch_updated
            app.logger.info(f"Batch {iteration + 1}: categorized {batch_updated} products")

            # If no products were updated in this batch, they might be uncategorizable
            if batch_updated == 0:
                app.logger.warning(f"Batch {iteration + 1}: no products categorized, stopping")
                break

        # Check if there are more products to categorize
        remaining = Product.query.filter(
            Product.business_id == business_id,
            (Product.category_group.is_(None) | (Product.category_group == ''))
        ).count()

        return jsonify({
            'success': True,
            'categorized_count': total_updated,
            'remaining_count': remaining,
            'message': f'Categorized {total_updated} products. {remaining} remaining.'
        })

    except Exception as e:
        app.logger.error(f"Categorization error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/category-stats', methods=['GET'])
@csrf.exempt
def api_admin_category_stats():
    """Get category_group statistics for products"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        business_id = request.args.get('business_id')

        # Build query
        query = db.session.query(
            Product.business_id,
            Business.name.label('business_name'),
            func.count(Product.id).label('total'),
            func.count(Product.category_group).label('categorized')
        ).join(Business).group_by(Product.business_id, Business.name)

        if business_id:
            query = query.filter(Product.business_id == int(business_id))

        results = query.all()

        stats = []
        for row in results:
            stats.append({
                'business_id': row.business_id,
                'business_name': row.business_name,
                'total_products': row.total,
                'categorized_products': row.categorized,
                'uncategorized_products': row.total - row.categorized,
                'percentage': round((row.categorized / row.total * 100) if row.total > 0 else 0, 1)
            })

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        app.logger.error(f"Category stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/analysis', methods=['GET'])
@csrf.exempt
def api_admin_products_analysis():
    """Search products by title for price analysis across stores - no limit"""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Query parameters
        search = request.args.get('q', '').strip()
        category_group = request.args.get('category_group')
        business_id = request.args.get('business_id', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        per_page = min(per_page, 500)  # Cap at 500

        # Build query
        query = Product.query.join(Business)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(Product.title.ilike(search_term))

        if category_group:
            query = query.filter(Product.category_group == category_group)

        if business_id:
            query = query.filter(Product.business_id == business_id)

        if min_price is not None:
            query = query.filter(Product.base_price >= min_price)

        if max_price is not None:
            query = query.filter(Product.base_price <= max_price)

        # Order by title for easier comparison
        query = query.order_by(Product.title, Product.base_price)

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        products = []
        for p in pagination.items:
            effective_price = p.discount_price if (p.discount_price and p.discount_price < p.base_price) else p.base_price
            products.append({
                'id': p.id,
                'title': p.title,
                'category': p.category,
                'category_group': p.category_group,
                'base_price': p.base_price,
                'discount_price': p.discount_price,
                'effective_price': effective_price,
                'discount_percent': round((1 - p.discount_price / p.base_price) * 100) if (p.discount_price and p.base_price and p.discount_price < p.base_price) else 0,
                'business_id': p.business_id,
                'business_name': p.business.name,
                'business_city': p.business.city,
                'business_logo': p.business.logo_path,
                'image_path': p.image_path,
                'tags': p.tags or [],
                'created_at': p.created_at.isoformat() if p.created_at else None
            })

        # Get filter options
        businesses = db.session.query(Business.id, Business.name).filter(Business.status == 'active').order_by(Business.name).all()
        category_groups = db.session.query(Product.category_group).filter(Product.category_group.isnot(None)).distinct().all()

        return jsonify({
            'products': products,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'filters': {
                'businesses': [{'id': b.id, 'name': b.name} for b in businesses],
                'category_groups': sorted([c[0] for c in category_groups if c[0]])
            }
        })

    except Exception as e:
        app.logger.error(f"Products analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
@csrf.exempt
def api_admin_update_product(product_id):
    """Admin endpoint to update a product - title, image_path, etc."""
    from auth_api import decode_jwt_token

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Find product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields
        if 'title' in data:
            product.title = data['title']
        if 'image_path' in data:
            product.image_path = data['image_path']
        if 'base_price' in data:
            product.base_price = float(data['base_price'])
        if 'discount_price' in data:
            product.discount_price = float(data['discount_price']) if data['discount_price'] else None
        if 'category' in data:
            product.category = data['category']
        if 'category_group' in data:
            product.category_group = data['category_group']

        db.session.commit()

        app.logger.info(f"Admin updated product {product_id}: {data.keys()}")

        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'title': product.title,
                'image_path': product.image_path,
                'base_price': product.base_price,
                'discount_price': product.discount_price,
                'category': product.category,
                'category_group': product.category_group
            }
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Admin update product error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/search-test', methods=['POST'])
@csrf.exempt
def api_admin_search_test():
    """Admin search test endpoint - uses same agent search as homepage"""
    from auth_api import decode_jwt_token
    from agent_search import run_agent_search, format_agent_products

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user and check if admin
        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        query = data.get('query', '').strip()
        k = int(data.get('k', 10))

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Run agent-based search (same as homepage)
        agent_result = run_agent_search(
            query=query,
            user_id=payload['user_id'],
            k=k,
        )

        # Format and flatten products for API response
        raw_products = agent_result.get("products", [])
        products = format_agent_products(raw_products)

        return jsonify({
            'query': query,
            'products_count': len(products),
            'products': products,
            'explanation': agent_result.get("explanation"),
            'grouped': agent_result.get("grouped", False),
            'grouped_results': agent_result.get("grouped_results"),
        }), 200

    except Exception as e:
        app.logger.error(f"Admin search test error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== FEEDBACK API ====================

@app.route('/api/feedback', methods=['POST'])
@csrf.exempt
def api_submit_feedback():
    """Submit user feedback - works for both logged-in and anonymous users"""
    from auth_api import decode_jwt_token
    import hashlib

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Get user if logged in
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if payload:
                user_id = payload.get('user_id')
        except:
            pass

    # Generate anonymous ID from IP if not logged in
    anonymous_id = None
    if not user_id:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip:
            anonymous_id = hashlib.sha256(ip.encode()).hexdigest()[:32]

    # Parse device info
    user_agent = request.headers.get('User-Agent', '')
    device_type = 'desktop'
    if 'Mobile' in user_agent or 'Android' in user_agent:
        device_type = 'mobile'
    elif 'Tablet' in user_agent or 'iPad' in user_agent:
        device_type = 'tablet'

    # Truncate text fields to prevent abuse
    def truncate(text, max_len):
        if text and isinstance(text, str):
            return text[:max_len]
        return text

    try:
        # Get text fields
        what_to_improve = truncate(data.get('what_to_improve'), 500)
        how_to_help = truncate(data.get('how_to_help'), 500)
        what_would_make_you_use = truncate(data.get('what_would_make_you_use'), 500)
        comments = truncate(data.get('comments'), 1000)

        feedback = UserFeedback(
            user_id=user_id,
            anonymous_id=anonymous_id,
            rating=data.get('rating'),
            what_to_improve=what_to_improve,
            how_to_help=how_to_help,
            what_would_make_you_use=what_would_make_you_use,
            comments=comments,
            trigger_type=truncate(data.get('trigger_type'), 50),
            page_url=truncate(data.get('page_url'), 500),
            user_agent=user_agent[:500] if user_agent else None,
            device_type=device_type
        )
        db.session.add(feedback)

        # Award +5 credits if logged in user provides at least 20 characters in any text field
        # User can only claim one feedback bonus per 40 credits spent
        credits_awarded = False
        MIN_CHARS_FOR_CREDITS = 20
        CREDITS_PER_FEEDBACK_CYCLE = 40

        if user_id:
            # Check if any field has at least 20 characters
            qualifies = any([
                what_to_improve and len(what_to_improve.strip()) >= MIN_CHARS_FOR_CREDITS,
                how_to_help and len(how_to_help.strip()) >= MIN_CHARS_FOR_CREDITS,
                what_would_make_you_use and len(what_would_make_you_use.strip()) >= MIN_CHARS_FOR_CREDITS,
                comments and len(comments.strip()) >= MIN_CHARS_FOR_CREDITS
            ])

            if qualifies:
                user = User.query.get(user_id)
                if user:
                    # Use lifetime_credits_spent to track total credits ever spent
                    total_credits_spent = user.lifetime_credits_spent or 0

                    # How many feedback bonuses is the user entitled to?
                    # First bonus at 0 credits spent (new user gets one), then every 40 credits
                    # Bonus 1: 0+ credits spent
                    # Bonus 2: 40+ credits spent
                    # Bonus 3: 80+ credits spent
                    max_bonuses_allowed = (total_credits_spent // CREDITS_PER_FEEDBACK_CYCLE) + 1

                    # Check if user hasn't claimed their current entitlement
                    bonuses_claimed = user.feedback_bonuses_claimed or 0

                    if bonuses_claimed < max_bonuses_allowed:
                        user.extra_credits += 5
                        user.feedback_bonuses_claimed = bonuses_claimed + 1
                        credits_awarded = True
                        app.logger.info(f"Awarded +5 feedback credits to user {user_id} (bonus #{bonuses_claimed + 1}, lifetime_spent={total_credits_spent})")
                    else:
                        app.logger.info(f"User {user_id} not eligible for feedback bonus (claimed={bonuses_claimed}, max_allowed={max_bonuses_allowed}, lifetime_spent={total_credits_spent})")

        db.session.commit()

        app.logger.info(f"Feedback submitted: user={user_id or 'anonymous'}, rating={data.get('rating')}, trigger={data.get('trigger_type')}, credits_awarded={credits_awarded}")

        return jsonify({
            'success': True,
            'message': 'Hvala vam na povratnim informacijama!',
            'credits_awarded': credits_awarded
        }), 201

    except Exception as e:
        app.logger.error(f"Error submitting feedback: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit feedback'}), 500


@app.route('/api/feedback/check', methods=['GET'])
@csrf.exempt
def api_check_feedback_status():
    """Check if user should see feedback popup (for registered users - after 3 credits spent)"""
    from auth_api import decode_jwt_token
    from models import CreditTransaction

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'show_feedback': False}), 200

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'show_feedback': False}), 200

        user_id = payload.get('user_id')

        # Check if user has already given feedback
        existing_feedback = UserFeedback.query.filter_by(user_id=user_id).first()
        if existing_feedback:
            return jsonify({
                'show_feedback': False,
                'has_given_feedback': True
            }), 200

        # Count credits spent (negative transactions)
        credits_spent = db.session.query(func.abs(func.sum(CreditTransaction.delta))).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.delta < 0
        ).scalar() or 0

        # Show feedback popup after 3 credits spent
        show_feedback = credits_spent >= 3

        return jsonify({
            'show_feedback': show_feedback,
            'credits_spent': credits_spent,
            'has_given_feedback': False
        }), 200

    except Exception as e:
        app.logger.error(f"Error checking feedback status: {e}")
        return jsonify({'show_feedback': False}), 200


@app.route('/api/admin/feedback', methods=['GET'])
@csrf.exempt
def api_admin_get_feedback():
    """Get all feedback for admin dashboard"""
    from auth_api import decode_jwt_token

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401

        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get feedback with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        feedback_query = UserFeedback.query.order_by(UserFeedback.created_at.desc())
        feedback_paginated = feedback_query.paginate(page=page, per_page=per_page, error_out=False)

        feedback_list = []
        for fb in feedback_paginated.items:
            user_email = None
            if fb.user_id:
                user = User.query.get(fb.user_id)
                user_email = user.email if user else None

            feedback_list.append({
                'id': fb.id,
                'user_id': fb.user_id,
                'user_email': user_email,
                'anonymous_id': fb.anonymous_id[:8] + '...' if fb.anonymous_id else None,
                'rating': fb.rating,
                'what_to_improve': fb.what_to_improve,
                'how_to_help': fb.how_to_help,
                'what_would_make_you_use': fb.what_would_make_you_use,
                'comments': fb.comments,
                'trigger_type': fb.trigger_type,
                'device_type': fb.device_type,
                'created_at': fb.created_at.isoformat() if fb.created_at else None
            })

        return jsonify({
            'feedback': feedback_list,
            'total': feedback_paginated.total,
            'page': page,
            'pages': feedback_paginated.pages
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting feedback: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/engagement', methods=['GET'])
@csrf.exempt
def api_admin_engagement_stats():
    """Get engagement analytics for admin dashboard"""
    from auth_api import decode_jwt_token
    from models import ProductVote, ProductComment, Favorite, UserActivity

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401

        admin_user = User.query.filter_by(id=payload['user_id']).first()
        if not admin_user or not admin_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403

        # Get date ranges
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # === OVERALL STATS ===
        total_votes = ProductVote.query.count()
        total_upvotes = ProductVote.query.filter_by(vote_type='up').count()
        total_downvotes = ProductVote.query.filter_by(vote_type='down').count()
        total_comments = ProductComment.query.count()
        total_favorites = Favorite.query.count()

        # Today's stats
        today_votes = ProductVote.query.filter(func.date(ProductVote.created_at) == today).count()
        today_comments = ProductComment.query.filter(func.date(ProductComment.created_at) == today).count()
        today_favorites = Favorite.query.filter(func.date(Favorite.created_at) == today).count()

        # This week stats
        week_votes = ProductVote.query.filter(func.date(ProductVote.created_at) >= week_ago).count()
        week_comments = ProductComment.query.filter(func.date(ProductComment.created_at) >= week_ago).count()
        week_favorites = Favorite.query.filter(func.date(Favorite.created_at) >= week_ago).count()

        # === PROIZVODI PAGE VIEWS ===
        proizvodi_views_total = UserActivity.query.filter_by(
            activity_type='page_view',
            page='proizvodi'
        ).count()
        proizvodi_views_today = UserActivity.query.filter(
            UserActivity.activity_type == 'page_view',
            UserActivity.page == 'proizvodi',
            func.date(UserActivity.created_at) == today
        ).count()
        proizvodi_views_week = UserActivity.query.filter(
            UserActivity.activity_type == 'page_view',
            UserActivity.page == 'proizvodi',
            func.date(UserActivity.created_at) >= week_ago
        ).count()

        # Unique users who viewed proizvodi
        unique_proizvodi_users = db.session.query(func.count(func.distinct(UserActivity.user_id))).filter(
            UserActivity.activity_type == 'page_view',
            UserActivity.page == 'proizvodi'
        ).scalar() or 0

        # === RECENT ENGAGEMENT ACTIVITY ===
        # Recent votes with user info
        recent_votes = db.session.query(
            ProductVote, User.id.label('uid'), User.email, User.first_name, User.last_name, Product.title
        ).join(User, ProductVote.user_id == User.id).join(
            Product, ProductVote.product_id == Product.id
        ).order_by(ProductVote.created_at.desc()).limit(20).all()

        recent_votes_list = [{
            'id': v.ProductVote.id,
            'user_id': v.uid,
            'user_email': v.email,
            'user_first_name': v.first_name,
            'user_last_name': v.last_name,
            'product_title': v.title[:50] + '...' if len(v.title) > 50 else v.title,
            'vote_type': v.ProductVote.vote_type,
            'created_at': v.ProductVote.created_at.isoformat() if v.ProductVote.created_at else None
        } for v in recent_votes]

        # Recent comments with user info
        recent_comments = db.session.query(
            ProductComment, User.id.label('uid'), User.email, User.first_name, User.last_name, Product.title
        ).join(User, ProductComment.user_id == User.id).join(
            Product, ProductComment.product_id == Product.id
        ).order_by(ProductComment.created_at.desc()).limit(20).all()

        recent_comments_list = [{
            'id': c.ProductComment.id,
            'user_id': c.uid,
            'user_email': c.email,
            'user_first_name': c.first_name,
            'user_last_name': c.last_name,
            'product_title': c.title[:50] + '...' if len(c.title) > 50 else c.title,
            'comment_text': c.ProductComment.comment_text[:100] + '...' if len(c.ProductComment.comment_text) > 100 else c.ProductComment.comment_text,
            'created_at': c.ProductComment.created_at.isoformat() if c.ProductComment.created_at else None
        } for c in recent_comments]

        # Recent favorites with user info
        recent_favorites = db.session.query(
            Favorite, User.id.label('uid'), User.email, User.first_name, User.last_name, Product.title
        ).join(User, Favorite.user_id == User.id).join(
            Product, Favorite.product_id == Product.id
        ).order_by(Favorite.created_at.desc()).limit(20).all()

        recent_favorites_list = [{
            'id': f.Favorite.id,
            'user_id': f.uid,
            'user_email': f.email,
            'user_first_name': f.first_name,
            'user_last_name': f.last_name,
            'product_title': f.title[:50] + '...' if len(f.title) > 50 else f.title,
            'created_at': f.Favorite.created_at.isoformat() if f.Favorite.created_at else None
        } for f in recent_favorites]

        # Recent proizvodi page views
        recent_proizvodi_views = db.session.query(
            UserActivity, User.id.label('uid'), User.email, User.first_name, User.last_name
        ).join(User, UserActivity.user_id == User.id).filter(
            UserActivity.activity_type == 'page_view',
            UserActivity.page == 'proizvodi'
        ).order_by(UserActivity.created_at.desc()).limit(30).all()

        recent_proizvodi_list = [{
            'id': a.UserActivity.id,
            'user_id': a.uid,
            'user_email': a.email,
            'user_first_name': a.first_name,
            'user_last_name': a.last_name,
            'activity_data': a.UserActivity.activity_data,
            'created_at': a.UserActivity.created_at.isoformat() if a.UserActivity.created_at else None
        } for a in recent_proizvodi_views]

        # === USER ENGAGEMENT SUMMARY ===
        # Users who have engaged (voted, commented, or favorited)
        engaged_users_votes = db.session.query(func.count(func.distinct(ProductVote.user_id))).scalar() or 0
        engaged_users_comments = db.session.query(func.count(func.distinct(ProductComment.user_id))).scalar() or 0
        engaged_users_favorites = db.session.query(func.count(func.distinct(Favorite.user_id))).scalar() or 0

        # Top engaged users
        top_voters = db.session.query(
            User.id,
            User.email,
            User.first_name,
            User.last_name,
            func.count(ProductVote.id).label('vote_count')
        ).join(ProductVote, User.id == ProductVote.user_id).group_by(
            User.id, User.email, User.first_name, User.last_name
        ).order_by(func.count(ProductVote.id).desc()).limit(10).all()

        top_commenters = db.session.query(
            User.id,
            User.email,
            User.first_name,
            User.last_name,
            func.count(ProductComment.id).label('comment_count')
        ).join(ProductComment, User.id == ProductComment.user_id).group_by(
            User.id, User.email, User.first_name, User.last_name
        ).order_by(func.count(ProductComment.id).desc()).limit(10).all()

        return jsonify({
            'stats': {
                'total_votes': total_votes,
                'total_upvotes': total_upvotes,
                'total_downvotes': total_downvotes,
                'total_comments': total_comments,
                'total_favorites': total_favorites,
                'today_votes': today_votes,
                'today_comments': today_comments,
                'today_favorites': today_favorites,
                'week_votes': week_votes,
                'week_comments': week_comments,
                'week_favorites': week_favorites,
                'proizvodi_views_total': proizvodi_views_total,
                'proizvodi_views_today': proizvodi_views_today,
                'proizvodi_views_week': proizvodi_views_week,
                'unique_proizvodi_users': unique_proizvodi_users,
                'engaged_users_votes': engaged_users_votes,
                'engaged_users_comments': engaged_users_comments,
                'engaged_users_favorites': engaged_users_favorites,
            },
            'recent_votes': recent_votes_list,
            'recent_comments': recent_comments_list,
            'recent_favorites': recent_favorites_list,
            'recent_proizvodi_views': recent_proizvodi_list,
            'top_voters': [{'user_id': t[0], 'email': t[1], 'first_name': t[2], 'last_name': t[3], 'count': t[4]} for t in top_voters],
            'top_commenters': [{'user_id': t[0], 'email': t[1], 'first_name': t[2], 'last_name': t[3], 'count': t[4]} for t in top_commenters],
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting engagement stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    # Return JSON for API routes
    if request.path.startswith('/api/') or request.path.startswith('/auth/'):
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'error': 'Stranica nije pronađena'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    # Return JSON for API routes
    if request.path.startswith('/api/') or request.path.startswith('/auth/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Interna greška servera'}), 500
