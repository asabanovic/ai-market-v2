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
from models import User, Package, Business, Product, UserSearch, ContactMessage, BusinessMembership, BusinessInvitation, user_has_business_role
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

# Import JWT-based auth API blueprint
from auth_api import auth_api_bp, require_jwt_auth
from app import csrf

# Import shopping list and favorites API blueprint
from shopping_api import shopping_api_bp

# Import phone authentication API blueprint
from phone_auth_api import phone_auth_bp

# Import referral API blueprint
from referral_api import referral_api_bp

# Import engagement API blueprint
from engagement_api import engagement_bp

# Disable CSRF for API endpoints (JWT-based)
csrf.exempt(auth_api_bp)
csrf.exempt(shopping_api_bp)
csrf.exempt(phone_auth_bp)
csrf.exempt(referral_api_bp)
csrf.exempt(engagement_bp)

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

# Register Replit Auth blueprint (only if running on Replit)
replit_bp = make_replit_blueprint()
if replit_bp:
    app.register_blueprint(replit_bp, url_prefix="/auth")

# Add Google OAuth support using Flask-Dance
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
import os

# Create Google OAuth blueprint with proper redirect URL for production
# Use absolute URL for production, relative for development
base_url = os.environ.get("REPLIT_DOMAINS",
                          "http://localhost:5001").split(',')[0]
if not base_url.startswith('http'):
    base_url = f"https://{base_url}"

redirect_url = f"{base_url}/auth/google/authorized"

# Only initialize Google OAuth if credentials are provided
google_client_id = os.environ.get("AI_PIJACA_GOOGLE_CLIENT_ID")
google_client_secret = os.environ.get("AI_PIJACA_GOOGLE_CLIENT_SECRET")

if google_client_id and google_client_secret:
    google_bp = make_google_blueprint(
        client_id=google_client_id,
        client_secret=google_client_secret,
        scope=[
            "openid", "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
        redirect_url=redirect_url)
    app.register_blueprint(google_bp, url_prefix="/auth")
else:
    google_bp = None
    app.logger.warning("Google OAuth credentials not found. Google login will not be available.")

# Register admin embedding blueprint
app.register_blueprint(admin_embedding_bp)

# Handle CORS preflight requests globally
@app.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        return '', 200


# Google OAuth authorized callback (only if Google OAuth is enabled)
if google_bp:
    @oauth_authorized.connect_via(google_bp)
    def google_logged_in(blueprint, token):
        try:
            if not token:
                app.logger.error("OAuth token missing")
                return False

            # Get user info from Google
            resp = blueprint.session.get("/oauth2/v1/userinfo")
            if not resp.ok:
                app.logger.error(
                    f"Failed to get Google user info: {resp.status_code}")
                return False

            google_info = resp.json()
            google_user_id = str(google_info.get("id"))
            email = google_info.get("email")

            if not email:
                app.logger.error("No email provided by Google OAuth")
                return False

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
                        return False
            else:
                app.logger.info(f"Existing user login via Google OAuth: {email}")

            login_user(user)
            app.logger.info(f"Successfully logged in user: {email}")
            return redirect(
                url_for('index'))  # Redirect to home page after successful login

        except Exception as e:
            app.logger.error(f"OAuth callback error: {e}")
            db.session.rollback()
            return False


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


def product_to_dict(product):
    """Standardized product serializer that returns complete product schema with nested business data"""
    from datetime import datetime

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

    # Calculate discount information
    has_discount = (discount_price is not None
                    and base_price is not None and float(
                        discount_price) < float(base_price))

    discount_percentage = 0
    if has_discount:
        discount_percentage = round(
            ((float(base_price) - float(discount_price)) /
             float(base_price)) * 100)

    # Normalize expiry date
    expires_iso = None
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
            expires_iso = expires_val.isoformat()

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

    return {
        'id': safe_get(product, 'id'),
        'title': safe_get(product, 'title'),
        'image_path': safe_get(product, 'image_path'),
        'base_price': float(base_price) if base_price else 0,
        'discount_price': float(discount_price) if discount_price else None,
        'expires': expires_iso,
        'has_discount': has_discount,
        'discount_percentage': discount_percentage,
        'city': safe_get(product, 'city'),
        'category': safe_get(product, 'category'),
        'business': business_data
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
            weekly_limit = 10
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


# Homepage route
@app.route('/')
def index():
    chat_examples = get_chat_examples()

    # Get featured discount products with business relationship
    featured_products = db.session.query(Product).join(Business).filter(
        Product.discount_price.isnot(None),
        or_(Product.expires.is_(None), Product.expires
            >= date.today())).order_by(db.func.random()).limit(6).all()

    # Get businesses that have active products
    featured_businesses = db.session.query(Business).join(Product).filter(
        or_(Product.expires.is_(None), Product.expires >= date.today())
    ).distinct().order_by(Business.name).all()

    return render_template('index.html',
                           chat_examples=chat_examples,
                           featured_products=featured_products,
                           featured_businesses=featured_businesses)


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
@app.route('/api/products')
def api_products():
    """API endpoint for products listing with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 24))
        category = request.args.get('category')
        business_id = request.args.get('business')
        search = request.args.get('search')

        # Base query
        query = Product.query.join(Business)

        query = query.filter(
                or_(Product.expires.is_(None), Product.expires >= date.today())
            )

        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        if business_id:
            query = query.filter(Product.business_id == int(business_id))
        if search:
            query = query.filter(Product.title.ilike(f'%{search}%'))

        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        products = []
        for product in paginated.items:
            products.append(product_to_dict(product))

        return jsonify({
            'products': products,
            'page': page,
            'per_page': per_page,
            'total': paginated.total,
            'total_pages': paginated.pages
        })

    except Exception as e:
        app.logger.error(f"Error in products API: {e}")
        return jsonify({'error': 'Failed to load products'}), 500


# API endpoint for businesses list
@app.route('/api/businesses')
def api_businesses():
    """API endpoint for businesses listing"""
    try:
        businesses = Business.query.filter_by(status='active').all()

        result = []
        for business in businesses:
            result.append({
                'id': business.id,
                'name': business.name,
                'city': business.city,
                'logo_path': business.logo_path,
                'contact_phone': business.contact_phone,
                'google_link': business.google_link
            })

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in businesses API: {e}")
        return jsonify({'error': 'Failed to load businesses'}), 500


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
            'logo_path': business.logo_path,
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

        # Ensure per_page is within reasonable bounds
        per_page = min(per_page, 100)  # Max 100 items per page

        # Get total count
        total_count = Product.query.filter_by(business_id=business_id).count()

        # Calculate pagination
        total_pages = (total_count + per_page - 1) // per_page  # Ceiling division
        offset = (page - 1) * per_page

        # Get paginated products with embeddings
        from models import ProductEmbedding
        products_query = db.session.query(Product, ProductEmbedding).outerjoin(
            ProductEmbedding, Product.id == ProductEmbedding.product_id
        ).filter(Product.business_id == business_id).order_by(
            Product.created_at.desc()).limit(per_page).offset(offset).all()

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
                'logo_path': business.logo_path,
                'contact_phone': business.contact_phone,
                'google_link': business.google_link,
                'pdf_url': business.pdf_url,
                'last_sync': business.last_sync.isoformat() if business.last_sync else None,
                'product_count': product_count,
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
    """Upload business logo with JWT auth"""
    try:
        import uuid
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

        # Generate unique filename
        unique_filename = f"{business_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # Ensure upload directory exists
        upload_dir = os.path.join('static', 'uploads', 'business_logos', str(business_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # Update business record
        business.logo_path = f"uploads/business_logos/{business_id}/{unique_filename}"
        db.session.commit()

        return jsonify({'success': True, 'logo_path': business.logo_path})

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

        # Filter by checking if they have active products
        active_businesses = []
        for business in businesses:
            has_active_products = db.session.query(Product).filter(
                Product.business_id == business.id,
                or_(Product.expires.is_(None), Product.expires >= today)
            ).first() is not None

            if has_active_products:
                active_businesses.append({
                    'id': business.id,
                    'name': business.name,
                    'logo': business.logo_path,
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
        # Get featured products (products with discounts, limited to 6)
        # Calculate discount percentage inline for ordering
        discount_expr = case(
            (Product.discount_price < Product.base_price,
             ((Product.base_price - Product.discount_price) / Product.base_price * 100)),
            else_=0
        )

        # Get today's date for filtering expired products
        today = date.today()

        featured_products = Product.query.join(Business).filter(
            Product.discount_price.isnot(None),
            Product.discount_price < Product.base_price,
            or_(Product.expires.is_(None), Product.expires >= today)  # Filter out expired products
        ).order_by(discount_expr.desc()).limit(6).all()

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
                'logo_path': business.logo_path
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
        # Import semantic search
        from semantic_search import semantic_search, parse_price_filter_from_query

        # Parse price filters from query
        price_min, price_max = parse_price_filter_from_query(query)

        # Perform semantic search using vector embeddings
        try:
            products = semantic_search(
                query=query,
                k=50,  # Get more results for better variety
                min_similarity=0.3,  # Threshold for relevance
                price_min=price_min,
                price_max=price_max
            )
            app.logger.info(f"Semantic search found {len(products)} products")
        except Exception as e:
            app.logger.error(f"Semantic search failed: {e}")

            # Rollback any failed transaction before logging
            db.session.rollback()

            # Log failed search attempts for tracking
            from models import UserSearch
            search_log = UserSearch(
                user_id=authenticated_user_id,
                query=query,
                results=json.dumps([])  # Empty results for failed search
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
        search_log = UserSearch(
            user_id=authenticated_user_id,
            query=query,
            results=json.dumps(results_data)
        )
        db.session.add(search_log)
        db.session.commit()

        app.logger.info(f"Logged search: '{query}' by {'user ' + authenticated_user_id if authenticated_user_id else 'anonymous'} - {len(results_data)} results")

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
            search_log = UserSearch(
                user_id=authenticated_user_id,
                query=query,
                results=json.dumps([])  # Empty results for failed search
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

    # Only show non-expired products
    query = query.filter(
        or_(Product.expires.is_(None), Product.expires >= date.today()))

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
    businesses = db.session.query(Business).join(Product).filter(
        or_(Product.expires.is_(None), Product.expires >= date.today())
    ).distinct().order_by(Business.name).all()

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

        # Create unique filename with UUID
        file_extension = 'png'  # Always save as PNG for consistency
        unique_filename = f"{business_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

        # Ensure upload directory exists per business
        upload_dir = os.path.join('static', 'uploads', 'business_logos',
                                  str(business_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save processed image
        file_path = os.path.join(upload_dir, unique_filename)
        image.save(file_path, 'PNG', optimize=True)

        # Update business record (store path relative to static)
        business.logo_path = f"uploads/business_logos/{business_id}/{unique_filename}"
        db.session.commit()

        return jsonify({'success': True, 'logo_path': business.logo_path})

    except Exception as e:
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

        # Delete the product
        db.session.delete(product)
        db.session.commit()

        app.logger.info(f"Product {product_id} deleted from business {business_id}")

        return jsonify({
            'success': True,
            'message': 'Proizvod je uspješno obrisan'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Delete product error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri brisanju: {str(e)}'
        }), 500


# Upload product image to S3
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>/upload-image', methods=['POST'])
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

    # Get all products without images, only active ones where discount hasn't expired
    products = Product.query.filter_by(
        business_id=business_id
    ).filter(
        or_(Product.image_path.is_(None), Product.image_path == '')
    ).filter(
        or_(Product.expires.is_(None), Product.expires >= date.today())
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
        from models import ProductEmbedding
        products_with_embeddings = db.session.query(ProductEmbedding).count()
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

        # Get recent searches
        recent_searches = db.session.query(UserSearch, User).outerjoin(
            User, UserSearch.user_id == User.id).order_by(
            UserSearch.created_at.desc()).limit(10).all()

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
                'expired_products': expired_products
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
                'user_email': user.email if user else 'Anonymous',
                'created_at': search.created_at.isoformat() if search.created_at else None
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

        # Get OTP codes for each user
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
                'daily_credits': u.daily_credits,
                'daily_credits_used': u.daily_credits_used,
                'latest_otp': latest_otp
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
