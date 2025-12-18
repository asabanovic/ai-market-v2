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
                        package_id=1,  # Default free package
                        registration_method='google'  # Mark as Google OAuth registration
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


def get_bulk_match_counts(product_ids: list) -> dict:
    """
    Get match counts (clones, siblings, brand_variants) for multiple products in a single query.

    Args:
        product_ids: List of product IDs to get match counts for

    Returns:
        Dict mapping product_id -> {'clones': N, 'siblings': N, 'brand_variants': N}
    """
    if not product_ids:
        return {}

    from models import ProductMatch
    from sqlalchemy import case, func

    # Query to count matches by type for each product
    # A product can appear as either product_a or product_b in a match
    results = db.session.query(
        case(
            (ProductMatch.product_a_id.in_(product_ids), ProductMatch.product_a_id),
            else_=ProductMatch.product_b_id
        ).label('product_id'),
        ProductMatch.match_type,
        func.count(ProductMatch.id).label('count')
    ).filter(
        db.or_(
            ProductMatch.product_a_id.in_(product_ids),
            ProductMatch.product_b_id.in_(product_ids)
        )
    ).group_by(
        case(
            (ProductMatch.product_a_id.in_(product_ids), ProductMatch.product_a_id),
            else_=ProductMatch.product_b_id
        ),
        ProductMatch.match_type
    ).all()

    # Build result dict
    match_counts = {pid: {'clones': 0, 'siblings': 0, 'brand_variants': 0} for pid in product_ids}

    for row in results:
        product_id = row.product_id
        match_type = row.match_type
        count = row.count

        if product_id in match_counts:
            # Map match_type to key
            if match_type == 'clone':
                match_counts[product_id]['clones'] = count
            elif match_type == 'sibling':
                match_counts[product_id]['siblings'] = count
            elif match_type == 'brand_variant':
                match_counts[product_id]['brand_variants'] = count

    return match_counts


# ==================== UNIFIED AI PRODUCT PROCESSING ====================
# Combines enrichment (tags, description) + categorization (brand, type, size, variant) in ONE API call

def schedule_unified_ai_processing(product_ids: list[int], business_id: int = None) -> None:
    """
    Unified AI processing that extracts ALL product data in a single OpenAI call:
    - tags (for search)
    - enriched_description (for display)
    - category_group (for filtering)
    - brand, product_type, size_value, size_unit, variant (for matching)

    This replaces both schedule_async_product_enrichment AND run_background_categorization.
    """
    import threading
    from flask import current_app
    from openai_utils import openai_client

    # ASCII category groups matching frontend CategorySelector.vue
    VALID_CATEGORY_GROUPS = [
        'meso', 'mlijeko', 'pica', 'voce_povrce', 'kuhinja', 'ves', 'ciscenje',
        'higijena', 'slatkisi', 'kafa', 'smrznuto', 'pekara', 'ljubimci', 'bebe'
    ]

    def run_unified_processing(app, product_ids, business_id):
        with app.app_context():
            try:
                app.logger.info(f"Starting unified AI processing for {len(product_ids)} products")

                # Fetch products
                products = Product.query.filter(Product.id.in_(product_ids)).all()
                if not products:
                    app.logger.warning("No products found for unified processing")
                    return

                # Process in batches of 10 to avoid token limits
                batch_size = 10
                total_processed = 0

                for batch_start in range(0, len(products), batch_size):
                    batch = products[batch_start:batch_start + batch_size]

                    # Prepare products for AI (text only - no images to save tokens)
                    products_for_ai = []

                    for p in batch:
                        product_info = {
                            'id': p.id,
                            'title': p.title,
                            'category': p.category or ''
                        }
                        products_for_ai.append(product_info)
                        # NOTE: Removed image collection - images burned too many tokens
                        # Product titles are sufficient for categorization

                    # System prompt for unified extraction
                    system_prompt = """You are a product data extraction expert for a Bosnian marketplace.

MOST IMPORTANT: Extract brand, product_type, size_value, size_unit for EVERY product - these are critical for product matching!

For each product, extract ALL of the following:

1. category_group - Pick the BEST match from: meso, mlijeko, pica, voce_povrce, kuhinja, ves, ciscenje, higijena, slatkisi, kafa, smrznuto, pekara, ljubimci, bebe
   - meso: meat, sausages, deli meats, fish, seafood
   - mlijeko: milk, dairy, cheese, yogurt, butter, cream
   - pica: drinks, juices, sodas, water, beer, wine, alcohol
   - voce_povrce: fruits and vegetables, fresh produce
   - kuhinja: cooking ingredients, oil, spices, pasta, rice, canned goods, flour, sugar, salt, sauces, condiments
   - ves: laundry detergents, fabric softeners, stain removers
   - ciscenje: cleaning products, household cleaners, dishwashing, air fresheners
   - higijena: personal hygiene, soap, shampoo, toothpaste, deodorant, toilet paper, tissues
   - slatkisi: sweets, chocolate, candy, chips, snacks, cookies, biscuits
   - kafa: coffee, tea
   - smrznuto: frozen foods, frozen vegetables, ice cream
   - pekara: bread, bakery products, pastries
   - ljubimci: pet food and supplies
   - bebe: baby products, diapers, baby food

   If product doesn't fit any category well, use the closest match (e.g., vitamins -> higijena, office supplies -> kuhinja)

2. brand - The brand/manufacturer. ALWAYS try to extract this! Look for brand names in title. Use null ONLY if truly unknown.

3. product_type - Normalized product type in lowercase (e.g., "mlijeko", "čokolada", "deterdžent", "vitamin"). ALWAYS extract this!

4. size_value - Numeric size value (e.g., 100, 1.5, 500). Extract from title patterns like "500ml", "1kg", "200g".

5. size_unit - Size unit in lowercase (g, kg, ml, l, kom, pak).

6. variant - Product variant/flavor (e.g., "lješnjak", "jagoda", "original", "light"). Use null if none.

7. tags - Array of 3-5 search keywords in lowercase for finding this product.

8. description - Short 1-sentence marketing description (max 100 chars).

Return ONLY valid JSON:
{
  "products": [
    {
      "id": 123,
      "category_group": "slatkisi",
      "brand": "Milka",
      "product_type": "čokolada",
      "size_value": 100,
      "size_unit": "g",
      "variant": "lješnjak",
      "tags": ["čokolada", "milka", "slatkiš", "lješnjak"],
      "description": "Kremasta Milka čokolada s lješnjacima."
    }
  ]
}"""

                    user_prompt = f"""Extract ALL data for these products:

{json.dumps(products_for_ai, ensure_ascii=False, indent=2)}

Return: id, category_group, brand, product_type, size_value, size_unit, variant, tags, description."""

                    try:
                        # Build messages (text only - images removed to save tokens)
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]

                        response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            response_format={"type": "json_object"},
                            temperature=0.2,
                            max_tokens=4000
                        )

                        result_text = response.choices[0].message.content.strip()
                        result = json.loads(result_text)

                        if isinstance(result, dict) and 'products' in result:
                            extractions = result['products']
                        elif isinstance(result, list):
                            extractions = result
                        else:
                            extractions = []

                        # Update products with extracted data
                        for item in extractions:
                            product_id = item.get('id')
                            if not product_id:
                                continue

                            product = Product.query.get(product_id)
                            if not product:
                                continue

                            # Update category_group
                            cat_group = (item.get('category_group') or '').lower()
                            if cat_group in VALID_CATEGORY_GROUPS:
                                product.category_group = cat_group

                            # Update brand
                            brand = item.get('brand')
                            if brand and brand.lower() not in ['null', 'none', '']:
                                product.brand = brand

                            # Update product_type
                            ptype = item.get('product_type')
                            if ptype and ptype.lower() not in ['null', 'none', '']:
                                product.product_type = ptype.lower()

                            # Update size_value
                            size_val = item.get('size_value')
                            if size_val is not None and str(size_val).lower() != 'null':
                                try:
                                    product.size_value = float(size_val)
                                except (ValueError, TypeError):
                                    pass

                            # Update size_unit
                            size_unit = item.get('size_unit')
                            if size_unit and size_unit.lower() not in ['null', 'none', '']:
                                product.size_unit = size_unit.lower()

                            # Update variant
                            variant = item.get('variant')
                            if variant and str(variant).lower() not in ['null', 'none', '']:
                                product.variant = variant

                            # Update tags
                            tags = item.get('tags')
                            if tags and isinstance(tags, list):
                                product.tags = tags

                            # Update enriched_description
                            desc = item.get('description')
                            if desc and desc.lower() not in ['null', 'none', '']:
                                product.enriched_description = desc

                            # Update match_key
                            product.update_match_key()

                            total_processed += 1

                        db.session.commit()
                        app.logger.info(f"Unified AI: Processed batch {batch_start//batch_size + 1}, {len(extractions)} products")

                    except Exception as e:
                        app.logger.error(f"Unified AI batch error: {e}")
                        continue

                    # Small delay between batches
                    import time as time_module
                    time_module.sleep(1)

                app.logger.info(f"Unified AI processing complete: {total_processed} products")

                # After AI processing, run clone detection for new products
                try:
                    clones_found = find_and_create_clone_matches(product_ids)
                    app.logger.info(f"Unified AI: Found {clones_found} clone matches")
                except Exception as e:
                    app.logger.error(f"Clone detection after unified AI failed: {e}")

                # Trigger lazy sibling matching
                try:
                    schedule_lazy_sibling_matching()
                except Exception as e:
                    app.logger.error(f"Lazy sibling matching trigger failed: {e}")

            except Exception as e:
                app.logger.error(f"Unified AI processing failed: {e}", exc_info=True)

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_unified_processing,
        args=(app, product_ids, business_id),
        daemon=True
    )
    thread.start()
    app.logger.info(f"Scheduled unified AI processing for {len(product_ids)} products")


# Legacy: Async product enrichment (tags + descriptions) - DEPRECATED, use schedule_unified_ai_processing
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
@require_jwt_auth
def api_product_detail(product_id):
    """Get single product details"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Use standardized product serializer that includes price_history
    return jsonify(product_to_dict(product))


# API endpoint for product price history
@app.route('/api/products/<int:product_id>/price-history')
@require_jwt_auth
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
@require_jwt_auth
def api_products():
    """API endpoint for products listing with pagination (requires authentication)."""
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

        # Get product IDs for bulk match counts query
        product_ids = [p.id for p in paginated.items]
        match_counts_map = get_bulk_match_counts(product_ids) if product_ids else {}

        products = []
        for product in paginated.items:
            product_dict = product_to_dict(product)
            # Add match counts for each product
            product_dict['match_counts'] = match_counts_map.get(product.id, {'clones': 0, 'siblings': 0, 'brand_variants': 0})
            products.append(product_dict)

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


# API endpoint for business page (requires authentication)
@app.route('/api/radnja/<int:business_id>')
@require_jwt_auth
def api_public_business_page(business_id):
    """API endpoint for business page with products (requires authentication)"""
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
@require_jwt_auth
def api_public_business_products(business_id):
    """API endpoint for paginated business products (requires authentication)"""
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

        # Get match counts for all products on this page
        product_ids = [p.id for p in pagination.items]
        match_counts_map = get_bulk_match_counts(product_ids) if product_ids else {}

        products = []
        for p in pagination.items:
            products.append({
                'id': p.id,
                'title': p.title,
                'base_price': p.base_price,
                'discount_price': p.discount_price,
                'discount_percentage': p.discount_percentage,
                'image_path': p.image_path,
                'category': p.category,
                'expires': p.expires.isoformat() if p.expires else None,
                'match_counts': match_counts_map.get(p.id, {'clones': 0, 'siblings': 0, 'brand_variants': 0})
            })

        return jsonify({
            'products': products,
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
                'has_embedding': embedding is not None,
                'product_url': product.product_url,
                # Product matching fields
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': product.size_value,
                'size_unit': product.size_unit,
                'variant': product.variant,
                'match_key': product.match_key
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

            # Add match counts for each product
            product_ids = [p['id'] for p in products if p.get('id')]
            match_counts_map = get_bulk_match_counts(product_ids) if product_ids else {}
            for product in products:
                pid = product.get('id')
                if pid:
                    product['match_counts'] = match_counts_map.get(pid, {'clones': 0, 'siblings': 0, 'brand_variants': 0})

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

                # Extract matching fields from top-level OR from product_metadata
                metadata = product_data.get('product_metadata', {})
                brand = product_data.get('brand') or metadata.get('brand')
                product_type = product_data.get('product_type') or metadata.get('product_type')
                size_value = product_data.get('size_value') if product_data.get('size_value') is not None else metadata.get('size_value')
                size_unit = product_data.get('size_unit') or metadata.get('size_unit')
                variant = product_data.get('variant') or metadata.get('variant')

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
                    existing_product.product_metadata = metadata
                    existing_product.image_path = product_data.get('image_url') or product_data.get('image_path')
                    existing_product.city = business.city
                    # Product matching fields (from top-level or product_metadata)
                    if brand:
                        existing_product.brand = brand
                    if product_type:
                        existing_product.product_type = product_type
                    if size_value is not None:
                        existing_product.size_value = float(size_value)
                    if size_unit:
                        existing_product.size_unit = size_unit
                    if variant:
                        existing_product.variant = variant
                    # Update match_key if matching fields are set
                    existing_product.update_match_key()
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
                        product_metadata=metadata,
                        image_path=product_data.get('image_url') or product_data.get('image_path'),
                        city=business.city,
                        # Product matching fields (from top-level or product_metadata)
                        brand=brand,
                        product_type=product_type,
                        size_value=float(size_value) if size_value is not None else None,
                        size_unit=size_unit,
                        variant=variant
                    )
                    # Generate match_key if matching fields are set
                    product.update_match_key()
                    db.session.add(product)
                    products_to_vectorize.append(product)

                imported_count += 1

            except Exception as e:
                errors.append(f"Proizvod #{validated_product['index'] + 1} ({product_data.get('title', 'N/A')}): {str(e)}")
                continue

        # Commit all products first
        db.session.commit()

        # Schedule unified AI processing and vectorization
        if products_to_vectorize:
            product_ids = [p.id for p in products_to_vectorize]

            # Schedule unified AI processing (tags + description + categorization + matching fields)
            # This combines enrichment AND categorization in ONE OpenAI call
            # Also handles clone detection and triggers lazy sibling matching after completion
            try:
                app.logger.info(f"Scheduling unified AI processing for {len(product_ids)} products")
                schedule_unified_ai_processing(product_ids, business_id)
            except Exception as e:
                app.logger.error(f"Failed to schedule unified AI processing: {e}")

            # Schedule vectorization
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

        # Product matching fields
        if 'brand' in data:
            product.brand = data['brand']
        if 'product_type' in data:
            product.product_type = data['product_type']
        if 'size_value' in data:
            product.size_value = float(data['size_value']) if data['size_value'] else None
        if 'size_unit' in data:
            product.size_unit = data['size_unit']
        if 'variant' in data:
            product.variant = data['variant']

        # Regenerate match_key if matching fields changed
        if any(key in data for key in ['brand', 'product_type', 'size_value', 'size_unit']):
            product.match_key = product.generate_match_key()

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


# Extract matching fields for single product using AI
@app.route('/biznisi/<int:business_id>/proizvodi/<int:product_id>/extract-matching', methods=['POST'])
@require_jwt_auth
def extract_product_matching_fields(business_id, product_id):
    """Extract brand, product_type, size, variant for a single product using AI"""
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

        # Prepare product info for AI
        tags_str = ''
        if product.tags:
            if isinstance(product.tags, list):
                tags_str = ', '.join(product.tags[:5])
            elif isinstance(product.tags, str):
                tags_str = product.tags

        product_info = {
            'id': product.id,
            'title': product.title,
            'category': product.category or '',
            'tags': tags_str
        }

        # System prompt for extraction
        system_prompt = """You are a product data extraction specialist. Extract product matching fields from product information.

SIZE EXTRACTION RULES:
- "1kg" or "1 kg" → size_value: 1, size_unit: "kg"
- "200g" → size_value: 200, size_unit: "g"
- "500ml" → size_value: 500, size_unit: "ml"
- "1l" or "1L" → size_value: 1, size_unit: "l"
- "6x0.5l" → size_value: 3, size_unit: "l" (total volume)
- "10 kom" or "10 komada" → size_value: 10, size_unit: "kom"

BRAND EXTRACTION RULES:
- Extract brand even if it's at the end of title (e.g., "Mlijeko 2.8% 1l Meggle" → brand: "Meggle")
- Common brands: Ariel, Persil, Meggle, Vindija, Dukat, Coca-Cola, Pepsi, Milka, Orbit, Gavrilović, etc.
- If no brand identifiable, return null

PRODUCT TYPE RULES:
- Extract the generic product type (e.g., "mlijeko", "jogurt", "cola", "salama", "deterdžent")
- Normalize to lowercase
- If not determinable, return null

VARIANT RULES:
- Extract flavor, fat percentage, or other variants (e.g., "zero", "light", "2.8%", "original")
- If not determinable, return null

Return ONLY valid JSON object with these fields:
{"brand": "...", "product_type": "...", "size_value": number, "size_unit": "...", "variant": "..."}

All fields can be null if not determinable."""

        user_prompt = f"""Extract matching fields for this product:

Title: {product_info['title']}
Category: {product_info['category']}
Tags: {product_info['tags']}

Return JSON with: brand, product_type, size_value, size_unit, variant"""

        # Import OpenAI client
        from openai_utils import openai_client

        # Build messages (text only - images removed to save tokens)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=500
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        # Update product with extracted fields
        if result.get('brand'):
            product.brand = result['brand']
        if result.get('product_type'):
            product.product_type = result['product_type']
        if result.get('size_value') is not None:
            product.size_value = float(result['size_value'])
        if result.get('size_unit'):
            product.size_unit = result['size_unit']
        if result.get('variant'):
            product.variant = result['variant']

        # Generate match_key
        product.match_key = product.generate_match_key()

        db.session.commit()

        app.logger.info(f"Matching fields extracted for product {product_id}: {result}")

        return jsonify({
            'success': True,
            'brand': product.brand,
            'product_type': product.product_type,
            'size_value': product.size_value,
            'size_unit': product.size_unit,
            'variant': product.variant,
            'match_key': product.match_key,
            'message': 'Polja za uparivanje su uspješno ekstraktovana'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Extract matching fields error: {e}")
        return jsonify({
            'success': False,
            'error': f'Greška pri ekstrakciji: {str(e)}'
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

        # Get registration method stats for ALL users (not just current page)
        email_count = User.query.filter(User.registration_method == 'email').count()
        google_count = User.query.filter(User.registration_method == 'google').count()
        phone_count = User.query.filter(User.registration_method == 'phone').count()
        verified_count = User.query.filter(User.is_verified == True).count()

        return jsonify({
            'users': user_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            },
            'stats': {
                'total': pagination.total,
                'email': email_count,
                'google': google_count,
                'phone': phone_count,
                'verified': verified_count
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Admin users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/users/analytics')
def api_admin_users_analytics():
    """API endpoint for time-series analytics: user registrations and searches by hour/day/month"""
    from auth_api import decode_jwt_token
    from models import UserSearch
    from sqlalchemy import func, extract
    from datetime import timedelta

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

        # Get interval parameter: hour, day, or month
        interval = request.args.get('interval', 'day')  # default to day

        now = datetime.now()

        if interval == 'hour':
            # Last 24 hours, grouped by hour
            start_time = now - timedelta(hours=24)

            # User registrations by hour
            users_query = db.session.query(
                extract('hour', User.created_at).label('hour'),
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= start_time
            ).group_by(
                func.date(User.created_at),
                extract('hour', User.created_at)
            ).order_by(
                func.date(User.created_at),
                extract('hour', User.created_at)
            ).all()

            # Searches by hour
            searches_query = db.session.query(
                extract('hour', UserSearch.created_at).label('hour'),
                func.date(UserSearch.created_at).label('date'),
                func.count(UserSearch.id).label('count')
            ).filter(
                UserSearch.created_at >= start_time
            ).group_by(
                func.date(UserSearch.created_at),
                extract('hour', UserSearch.created_at)
            ).order_by(
                func.date(UserSearch.created_at),
                extract('hour', UserSearch.created_at)
            ).all()

            # Build time series data for last 24 hours
            users_data = []
            searches_data = []
            labels = []

            users_dict = {(str(r.date), int(r.hour)): r.count for r in users_query}
            searches_dict = {(str(r.date), int(r.hour)): r.count for r in searches_query}

            for i in range(24):
                time_point = now - timedelta(hours=23-i)
                date_str = time_point.strftime('%Y-%m-%d')
                hour = time_point.hour
                labels.append(time_point.strftime('%H:00'))
                users_data.append(users_dict.get((date_str, hour), 0))
                searches_data.append(searches_dict.get((date_str, hour), 0))

        elif interval == 'day':
            # Last 30 days, grouped by day
            start_time = now - timedelta(days=30)

            # User registrations by day
            users_query = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= start_time
            ).group_by(
                func.date(User.created_at)
            ).order_by(
                func.date(User.created_at)
            ).all()

            # Searches by day
            searches_query = db.session.query(
                func.date(UserSearch.created_at).label('date'),
                func.count(UserSearch.id).label('count')
            ).filter(
                UserSearch.created_at >= start_time
            ).group_by(
                func.date(UserSearch.created_at)
            ).order_by(
                func.date(UserSearch.created_at)
            ).all()

            # Build time series data for last 30 days
            users_data = []
            searches_data = []
            labels = []

            users_dict = {str(r.date): r.count for r in users_query}
            searches_dict = {str(r.date): r.count for r in searches_query}

            for i in range(30):
                time_point = now - timedelta(days=29-i)
                date_str = time_point.strftime('%Y-%m-%d')
                labels.append(time_point.strftime('%d.%m'))
                users_data.append(users_dict.get(date_str, 0))
                searches_data.append(searches_dict.get(date_str, 0))

        else:  # month
            # Last 12 months, grouped by month
            start_time = now - timedelta(days=365)

            # User registrations by month
            users_query = db.session.query(
                extract('year', User.created_at).label('year'),
                extract('month', User.created_at).label('month'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= start_time
            ).group_by(
                extract('year', User.created_at),
                extract('month', User.created_at)
            ).order_by(
                extract('year', User.created_at),
                extract('month', User.created_at)
            ).all()

            # Searches by month
            searches_query = db.session.query(
                extract('year', UserSearch.created_at).label('year'),
                extract('month', UserSearch.created_at).label('month'),
                func.count(UserSearch.id).label('count')
            ).filter(
                UserSearch.created_at >= start_time
            ).group_by(
                extract('year', UserSearch.created_at),
                extract('month', UserSearch.created_at)
            ).order_by(
                extract('year', UserSearch.created_at),
                extract('month', UserSearch.created_at)
            ).all()

            # Build time series data for last 12 months
            users_data = []
            searches_data = []
            labels = []

            users_dict = {(int(r.year), int(r.month)): r.count for r in users_query}
            searches_dict = {(int(r.year), int(r.month)): r.count for r in searches_query}

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

            for i in range(12):
                time_point = now - timedelta(days=(11-i)*30)  # Approximate
                year = time_point.year
                month = time_point.month
                labels.append(f"{month_names[month-1]} {year}")
                users_data.append(users_dict.get((year, month), 0))
                searches_data.append(searches_dict.get((year, month), 0))

        return jsonify({
            'interval': interval,
            'labels': labels,
            'datasets': {
                'users': {
                    'label': 'Novi korisnici',
                    'data': users_data,
                    'total': sum(users_data)
                },
                'searches': {
                    'label': 'Pretrage',
                    'data': searches_data,
                    'total': sum(searches_data)
                }
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Admin users analytics error: {e}")
        import traceback
        traceback.print_exc()
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
    """API endpoint to get products with server-side pagination for admin panel"""
    from auth_api import decode_jwt_token
    from sqlalchemy import func

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

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)  # Cap at 200 max

    # Optional filters
    business_id_filter = request.args.get('business_id', type=int)
    categorization_filter = request.args.get('categorization_filter', type=str)  # all, uncategorized, no_matches, has_matches
    search_query = request.args.get('search', type=str)

    # Build base query
    query = db.session.query(Product, Business).join(Business)
    if business_id_filter:
        query = query.filter(Product.business_id == business_id_filter)

    # Search filter - search in title, brand, product_type
    if search_query and search_query.strip():
        search_term = f'%{search_query.strip()}%'
        query = query.filter(
            db.or_(
                Product.title.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.product_type.ilike(search_term)
            )
        )

    # Categorization filter - uncategorized means missing product_type/size_value/size_unit
    # Note: brand can be null (truly unknown brand is valid, not a categorization issue)
    if categorization_filter == 'uncategorized':
        query = query.filter(
            db.or_(
                Product.product_type.is_(None),
                Product.product_type == '',
                Product.product_type == 'unknown',
                Product.size_value.is_(None),
                Product.size_unit.is_(None),
                Product.size_unit == '',
                Product.size_unit == 'unknown'
            )
        )

    # Get total count before pagination (for filters that can be applied at DB level)
    total_count = query.count()

    query = query.order_by(Business.name, Product.title)

    # Apply pagination at DB level for non-match filters
    # Note: no_matches/has_matches filters need to be applied after match_count is computed
    if categorization_filter not in ('no_matches', 'has_matches'):
        offset = (page - 1) * per_page
        products = query.offset(offset).limit(per_page).all()
    else:
        # For match-based filters, we need all products to compute match_count first
        products = query.all()

    # Pre-compute match counts for all products with a match_key
    # Count how many OTHER products have the same match_key (excluding self)
    match_key_counts = {}
    all_match_keys = [p.match_key for p, _ in products if p.match_key]
    if all_match_keys:
        # Get count of products per match_key
        count_query = db.session.query(
            Product.match_key,
            func.count(Product.id).label('count')
        ).filter(
            Product.match_key.in_(all_match_keys)
        ).group_by(Product.match_key).all()

        for match_key, count in count_query:
            match_key_counts[match_key] = count

    # Pre-compute sibling counts (same brand + product_type, any size)
    # sibling_key = brand:product_type
    sibling_key_counts = {}
    all_sibling_keys = []
    for p, _ in products:
        if p.brand and p.product_type:
            sibling_key = f"{p.brand}:{p.product_type}"
            all_sibling_keys.append(sibling_key)

    if all_sibling_keys:
        # Get count of products per sibling_key (brand + product_type combo)
        sibling_count_query = db.session.query(
            func.concat(Product.brand, ':', Product.product_type).label('sibling_key'),
            func.count(Product.id).label('count')
        ).filter(
            Product.brand.isnot(None),
            Product.product_type.isnot(None),
            func.concat(Product.brand, ':', Product.product_type).in_(list(set(all_sibling_keys)))
        ).group_by(func.concat(Product.brand, ':', Product.product_type)).all()

        for sibling_key, count in sibling_count_query:
            sibling_key_counts[sibling_key] = count

    # Pre-compute alternative counts (same product_type + size, different brand)
    # alternative_key = product_type:size_value:size_unit
    alternative_key_counts = {}
    all_alternative_keys = []
    for p, _ in products:
        if p.product_type and p.size_value is not None and p.size_unit:
            alt_key = f"{p.product_type}:{p.size_value}:{p.size_unit}"
            all_alternative_keys.append(alt_key)

    if all_alternative_keys:
        # Get count of products per alternative_key (product_type + size combo)
        alternative_count_query = db.session.query(
            func.concat(Product.product_type, ':', Product.size_value, ':', Product.size_unit).label('alt_key'),
            func.count(Product.id).label('count')
        ).filter(
            Product.product_type.isnot(None),
            Product.size_value.isnot(None),
            Product.size_unit.isnot(None),
            func.concat(Product.product_type, ':', Product.size_value, ':', Product.size_unit).in_(list(set(all_alternative_keys)))
        ).group_by(func.concat(Product.product_type, ':', Product.size_value, ':', Product.size_unit)).all()

        for alt_key, count in alternative_count_query:
            alternative_key_counts[alt_key] = count

    # Build flat products list with computed fields
    products_list = []
    for product, business in products:
        # Calculate match_count (other products with same match_key, excluding self)
        match_count = 0
        if product.match_key and product.match_key in match_key_counts:
            match_count = match_key_counts[product.match_key] - 1  # Exclude self

        # Calculate sibling_count (same brand + product_type, any size, excluding self)
        sibling_count = 0
        sibling_key = None
        if product.brand and product.product_type:
            sibling_key = f"{product.brand}:{product.product_type}"
            if sibling_key in sibling_key_counts:
                sibling_count = sibling_key_counts[sibling_key] - 1  # Exclude self

        # Calculate alternative_count (same product_type + size, different brand, excluding self)
        alternative_count = 0
        alternative_key = None
        if product.product_type and product.size_value is not None and product.size_unit:
            alternative_key = f"{product.product_type}:{product.size_value}:{product.size_unit}"
            if alternative_key in alternative_key_counts:
                alternative_count = alternative_key_counts[alternative_key] - 1  # Exclude self

        # Apply no_matches / has_matches filters (must be done after match_count is computed)
        if categorization_filter == 'no_matches' and match_count > 0:
            continue  # Skip products that have matches
        if categorization_filter == 'has_matches' and match_count == 0:
            continue  # Skip products that don't have matches

        products_list.append({
            'id': product.id,
            'title': product.title,
            'base_price': float(product.base_price) if product.base_price else 0,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_path': product.image_path,
            'expires': product.expires.isoformat() if product.expires else None,
            'category': product.category,
            'category_group': product.category_group,
            'tags': product.tags,
            'enriched_description': product.enriched_description,
            # Business info (flat structure for easier frontend handling)
            'business_id': business.id,
            'business_name': business.name,
            'business_logo': business.logo_path,
            # Product matching fields
            'brand': product.brand,
            'product_type': product.product_type,
            'size_value': float(product.size_value) if product.size_value is not None else None,
            'size_unit': product.size_unit,
            'variant': product.variant,
            'match_key': product.match_key,
            'sibling_key': sibling_key,  # brand:product_type for sibling lookup
            'alternative_key': alternative_key,  # product_type:size_value:size_unit for alternative lookup
            'match_count': match_count,  # Number of OTHER products with same match_key (exact clones)
            'sibling_count': sibling_count,  # Number of OTHER products with same brand:product_type (any size)
            'alternative_count': alternative_count  # Number of OTHER products with same type+size but different brand
        })

    # For match-based filters, we loaded all products - now paginate in memory
    if categorization_filter in ('no_matches', 'has_matches'):
        total_count = len(products_list)  # Update total after filtering
        offset = (page - 1) * per_page
        products_list = products_list[offset:offset + per_page]

    # Get all businesses for dropdown filter (even when filtering)
    all_businesses = Business.query.order_by(Business.name).all()
    businesses_list = [{'id': b.id, 'name': b.name} for b in all_businesses]

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page

    return jsonify({
        'products': products_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'total_pages': total_pages
        },
        'all_businesses': businesses_list  # For dropdown filter
    })


@app.route('/api/admin/products/<int:product_id>/related')
def api_admin_product_related(product_id):
    """Get products related to a specific product (matches and siblings)"""
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

    # Get the source product
    source_product = Product.query.get(product_id)
    if not source_product:
        return jsonify({'error': 'Product not found'}), 404

    # Get match_type from query params: 'matches' (exact clones) or 'siblings' (same brand+type, any size)
    match_type = request.args.get('type', 'matches')

    related_products = []

    if match_type == 'matches' and source_product.match_key:
        # Find products with exact same match_key (brand:product_type:size_value:size_unit)
        products = db.session.query(Product, Business).join(Business).filter(
            Product.match_key == source_product.match_key,
            Product.id != product_id  # Exclude self
        ).order_by(Business.name, Product.title).all()

        for product, business in products:
            related_products.append({
                'id': product.id,
                'title': product.title,
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': float(product.size_value) if product.size_value is not None else None,
                'size_unit': product.size_unit,
                'base_price': float(product.base_price) if product.base_price else 0,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'image_path': product.image_path,
                'business_name': business.name,
                'business_id': business.id,
                'match_key': product.match_key
            })

    elif match_type == 'siblings' and source_product.brand and source_product.product_type:
        # Find products with same brand + product_type (any size)
        products = db.session.query(Product, Business).join(Business).filter(
            Product.brand == source_product.brand,
            Product.product_type == source_product.product_type,
            Product.id != product_id  # Exclude self
        ).order_by(Business.name, Product.title).all()

        for product, business in products:
            related_products.append({
                'id': product.id,
                'title': product.title,
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': float(product.size_value) if product.size_value is not None else None,
                'size_unit': product.size_unit,
                'base_price': float(product.base_price) if product.base_price else 0,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'image_path': product.image_path,
                'business_name': business.name,
                'business_id': business.id,
                'match_key': product.match_key
            })

    elif match_type == 'alternatives' and source_product.product_type and source_product.size_value is not None and source_product.size_unit:
        # Find products with same product_type + size but different brand
        products = db.session.query(Product, Business).join(Business).filter(
            Product.product_type == source_product.product_type,
            Product.size_value == source_product.size_value,
            Product.size_unit == source_product.size_unit,
            Product.brand != source_product.brand,  # Different brand
            Product.id != product_id  # Exclude self
        ).order_by(Business.name, Product.title).all()

        for product, business in products:
            related_products.append({
                'id': product.id,
                'title': product.title,
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': float(product.size_value) if product.size_value is not None else None,
                'size_unit': product.size_unit,
                'base_price': float(product.base_price) if product.base_price else 0,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'image_path': product.image_path,
                'business_name': business.name,
                'business_id': business.id,
                'match_key': product.match_key
            })

    return jsonify({
        'source_product': {
            'id': source_product.id,
            'title': source_product.title,
            'brand': source_product.brand,
            'product_type': source_product.product_type,
            'size_value': float(source_product.size_value) if source_product.size_value is not None else None,
            'size_unit': source_product.size_unit,
            'match_key': source_product.match_key
        },
        'match_type': match_type,
        'related_products': related_products,
        'count': len(related_products)
    })


@app.route('/api/admin/products/<int:product_id>/categorization', methods=['PATCH'])
def api_admin_update_product_categorization(product_id):
    """Update product categorization fields (brand, product_type, size_value, size_unit, category_group)"""
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

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()

    # Update allowed fields
    allowed_fields = ['brand', 'product_type', 'size_value', 'size_unit', 'category_group', 'variant']
    updated_fields = []

    for field in allowed_fields:
        if field in data:
            old_value = getattr(product, field)
            new_value = data[field]

            # Handle size_value as float
            if field == 'size_value':
                try:
                    new_value = float(new_value) if new_value is not None and new_value != '' else None
                except (ValueError, TypeError):
                    continue

            setattr(product, field, new_value)
            updated_fields.append(field)

    if updated_fields:
        # Update match_key if any matching field changed
        product.update_match_key()
        db.session.commit()

    return jsonify({
        'success': True,
        'updated_fields': updated_fields,
        'product': {
            'id': product.id,
            'brand': product.brand,
            'product_type': product.product_type,
            'size_value': product.size_value,
            'size_unit': product.size_unit,
            'category_group': product.category_group,
            'variant': product.variant,
            'match_key': product.match_key
        }
    })


# ==================== ADMIN EMBEDDINGS API ====================

@app.route('/api/admin/embeddings/stats')
def api_admin_embeddings_stats():
    """Get embedding statistics for admin dashboard"""
    from auth_api import decode_jwt_token
    from sqlalchemy import func
    import hashlib

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

    # Get total product count
    total_products = Product.query.count()

    # Get count of products with embeddings
    products_with_embeddings = db.session.query(func.count(ProductEmbedding.product_id)).scalar() or 0

    # Products without embeddings
    no_embedding = total_products - products_with_embeddings

    # Check how many embeddings need refresh (content changed since embedding was created)
    # We compare content_hash stored in ProductEmbedding with current product content
    needs_refresh = 0

    # Get all products that have embeddings
    embeddings_with_products = db.session.query(
        ProductEmbedding.product_id,
        ProductEmbedding.content_hash,
        Product.title,
        Product.enriched_description,
        Product.category
    ).join(Product).all()

    for emb in embeddings_with_products:
        # Generate current content hash
        content = f"{emb.title or ''} {emb.enriched_description or ''} {emb.category or ''}"
        current_hash = hashlib.md5(content.encode()).hexdigest()

        if emb.content_hash and emb.content_hash != current_hash:
            needs_refresh += 1

    # Up to date = has embedding and doesn't need refresh
    up_to_date = products_with_embeddings - needs_refresh

    return jsonify({
        'total_products': total_products,
        'up_to_date': up_to_date,
        'needs_refresh': needs_refresh,
        'no_embedding': no_embedding
    })


@app.route('/api/admin/embeddings/products/status')
def api_admin_embeddings_products_status():
    """Get embedding status for all products"""
    from auth_api import decode_jwt_token
    from sqlalchemy import func
    import hashlib

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

    per_page = request.args.get('per_page', 100, type=int)

    # Get all products with their embedding info
    products_query = db.session.query(
        Product.id,
        Product.title,
        Product.enriched_description,
        Product.category,
        ProductEmbedding.content_hash,
        ProductEmbedding.updated_at.label('embedding_updated_at')
    ).outerjoin(ProductEmbedding).limit(per_page).all()

    product_statuses = {}
    for p in products_query:
        if p.content_hash is None:
            status = 'no_embedding'
        else:
            # Check if needs refresh
            content = f"{p.title or ''} {p.enriched_description or ''} {p.category or ''}"
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if p.content_hash != current_hash:
                status = 'needs_refresh'
            else:
                status = 'up_to_date'
        product_statuses[p.id] = status

    return jsonify({
        'product_statuses': product_statuses
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

        # Check if force refresh is requested
        force_refresh = request.get_json().get('force_refresh', False) if request.is_json else False

        # If we have suggestions, verify at least some exist in S3
        if suggested_images and not force_refresh:
            from image_matcher import check_image_exists
            # Check first 3 images - if none exist, we need to refresh
            existing = [p for p in suggested_images[:3] if check_image_exists(p)]
            if not existing:
                app.logger.info(f"Suggested images for product {product_id} no longer exist in S3, refreshing...")
                suggested_images = []

        if not suggested_images or force_refresh:
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

# Background categorization job tracking
import threading
import time as time_module
import uuid

categorization_jobs = {}  # job_id -> job_status dict

def run_background_categorization(job_id, business_id, app_context):
    """Background worker for slow drip categorization and product matching field extraction"""
    from openai_utils import openai_client
    import base64
    import requests

    with app_context:
        try:
            categorization_jobs[job_id]['status'] = 'running'
            categorization_jobs[job_id]['started_at'] = datetime.now().isoformat()

            # System prompt for categorization and product matching field extraction
            system_prompt = """You are a product categorization and data extraction expert for a Bosnian marketplace.

Your task: For each product, extract:
1. category_group - ONE of the valid categories
2. brand - The brand/manufacturer name (e.g., "Ariel", "Meggle", "Coca-Cola", "Milka")
3. product_type - Normalized product type in lowercase (e.g., "mlijeko", "deterdžent", "čokolada", "sok")
4. size_value - Numeric size (e.g., 1, 0.5, 500, 200, 1.5)
5. size_unit - Unit of measurement (e.g., "kg", "g", "l", "ml", "kom")
6. variant - Any variant/flavor info (e.g., "light", "bez laktoze", "gorka", "jagoda")

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

SIZE EXTRACTION RULES:
- "1l" or "1 l" → size_value: 1, size_unit: "l"
- "500ml" → size_value: 500, size_unit: "ml"
- "1kg" or "1 kg" → size_value: 1, size_unit: "kg"
- "200g" → size_value: 200, size_unit: "g"
- "6x0.5l" → size_value: 3, size_unit: "l" (total volume)
- "10 kom" or "10 komada" → size_value: 10, size_unit: "kom"

BRAND EXTRACTION RULES:
- Extract brand even if it's at the end of title (e.g., "Mlijeko 2.8% 1l Meggle" → brand: "Meggle")
- Common brands: Ariel, Persil, Meggle, Vindija, Dukat, Coca-Cola, Pepsi, Milka, Orbit, etc.
- If no brand identifiable, return null

RULES:
1. Return ONLY valid category group IDs from the list above
2. Use title, category AND tags together to make the best decision
3. If product has an image, use visual info to confirm/enhance extraction
4. ALWAYS return category_group - make your best guess if unsure
5. Other fields (brand, size, etc.) can be null if not determinable

Return ONLY valid JSON array:
[
  {"id": 123, "category_group": "meso", "brand": "Gavrilović", "product_type": "salama", "size_value": 200, "size_unit": "g", "variant": null},
  {"id": 456, "category_group": "mlijeko", "brand": "Meggle", "product_type": "mlijeko", "size_value": 1, "size_unit": "l", "variant": "2.8%"}
]"""

            total_updated = 0
            batch_size = 10  # Smaller batch for vision API (more expensive)
            delay_seconds = 10  # Wait 10 seconds between batches to avoid rate limits
            max_iterations = 1000  # Allow many more iterations for slow processing

            # Helper to check if product needs processing
            def needs_processing(p):
                """Product needs processing if missing product_type (required for match_key)"""
                return not p.product_type

            for iteration in range(max_iterations):
                # Check if job was cancelled
                if categorization_jobs[job_id].get('cancelled'):
                    categorization_jobs[job_id]['status'] = 'cancelled'
                    break

                # Get products needing processing - those missing ANY categorization field
                from sqlalchemy import or_
                products = Product.query.filter(
                    Product.business_id == business_id,
                    or_(
                        Product.category_group.is_(None),
                        Product.category_group == '',
                        Product.brand.is_(None),
                        Product.size_value.is_(None),
                        Product.size_unit.is_(None),
                        Product.product_type.is_(None)
                    )
                ).limit(batch_size).all()

                if not products:
                    break  # No more products to process

                # Update job progress - count products missing ANY field
                remaining = Product.query.filter(
                    Product.business_id == business_id,
                    or_(
                        Product.category_group.is_(None),
                        Product.category_group == '',
                        Product.brand.is_(None),
                        Product.size_value.is_(None),
                        Product.size_unit.is_(None),
                        Product.product_type.is_(None)
                    )
                ).count()

                categorization_jobs[job_id]['remaining'] = remaining
                categorization_jobs[job_id]['processed'] = total_updated
                categorization_jobs[job_id]['current_batch'] = iteration + 1

                # Prepare products for AI (text only - images removed to save tokens)
                products_for_ai = []
                for p in products:
                    tags_str = ''
                    if p.tags:
                        if isinstance(p.tags, list):
                            tags_str = ', '.join(p.tags[:5])
                        elif isinstance(p.tags, str):
                            tags_str = p.tags

                    product_info = {
                        'id': p.id,
                        'title': p.title,
                        'category': p.category or '',
                        'tags': tags_str
                    }
                    products_for_ai.append(product_info)

                    # NOTE: Removed image tracking - images burned too many tokens

                # Build user message (text only)
                user_prompt = f"""Extract category and product matching fields for these products:

{json.dumps(products_for_ai, ensure_ascii=False, indent=2)}

For each product, return: id, category_group, brand, product_type, size_value, size_unit, variant.
Use ALL available info (title + category + tags) to determine the fields."""

                try:
                    # Build messages (text only - images removed to save tokens)
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]

                    # Retry with exponential backoff for rate limits
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            response = openai_client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=messages,
                                response_format={"type": "json_object"},
                                temperature=0.2,
                                max_tokens=4000
                            )
                            break
                        except Exception as api_error:
                            if 'rate_limit' in str(api_error).lower() or '429' in str(api_error):
                                wait_time = (2 ** retry) * 5  # 5s, 10s, 20s
                                app.logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {retry + 1}/{max_retries}")
                                time_module.sleep(wait_time)
                                if retry == max_retries - 1:
                                    raise
                            else:
                                raise

                    result_text = response.choices[0].message.content.strip()
                    app.logger.info(f"Background job {job_id}: AI response: {result_text[:500]}")

                    # Parse response
                    try:
                        result = json.loads(result_text)
                        app.logger.info(f"Background job {job_id}: Parsed result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

                        if isinstance(result, dict) and 'products' in result:
                            categorizations = result['products']
                        elif isinstance(result, dict) and 'results' in result:
                            categorizations = result['results']
                        elif isinstance(result, list):
                            categorizations = result
                        elif isinstance(result, dict):
                            # Try to find a list in the result values
                            for key, val in result.items():
                                if isinstance(val, list):
                                    app.logger.info(f"Background job {job_id}: Found list in key '{key}' with {len(val)} items")
                                    categorizations = val
                                    break
                            else:
                                app.logger.warning(f"Background job {job_id}: No list found in result, using empty")
                                categorizations = []
                        else:
                            categorizations = []

                        app.logger.info(f"Background job {job_id}: Found {len(categorizations)} categorizations")
                    except Exception as parse_err:
                        app.logger.error(f"Background job {job_id}: Failed to parse AI response: {parse_err}")
                        categorizations = []

                    # If AI returned empty result, mark all products with defaults to prevent infinite loop
                    if not categorizations:
                        app.logger.warning(f"Background job {job_id}: Empty AI result, marking {len(products)} products with defaults")
                        for p in products:
                            # Set defaults for ALL fields that are in the OR filter
                            # Note: brand stays null if unknown (not set to 'unknown')
                            if not p.product_type:
                                p.product_type = 'unknown'
                            # brand intentionally left as null if not set
                            if p.size_value is None:
                                p.size_value = 0
                            if not p.size_unit:
                                p.size_unit = 'unknown'
                            if not p.category_group:
                                p.category_group = 'ostalo'
                            p.update_match_key()
                        db.session.commit()
                        total_updated += len(products)
                        categorization_jobs[job_id]['processed'] = total_updated
                        app.logger.info(f"Background job {job_id}: Batch {iteration + 1} - marked {len(products)} products with defaults")
                        time_module.sleep(delay_seconds)
                        continue

                    # Update products in database with all extracted fields
                    batch_updated = 0
                    for cat_item in categorizations:
                        product_id = cat_item.get('id')
                        category_group = cat_item.get('category_group', '').lower() if cat_item.get('category_group') else ''

                        if product_id:
                            product = Product.query.get(product_id)
                            if product:
                                # Update category_group if valid
                                if category_group in VALID_CATEGORY_GROUPS:
                                    product.category_group = category_group

                                # Update brand
                                brand = cat_item.get('brand')
                                if brand and brand.lower() not in ['null', 'none', '']:
                                    product.brand = brand

                                # Update product_type - ALWAYS set a value to mark as processed
                                product_type = cat_item.get('product_type')
                                if product_type and product_type.lower() not in ['null', 'none', '']:
                                    product.product_type = product_type.lower()
                                else:
                                    # Set default to mark product as processed (prevents infinite loop)
                                    product.product_type = 'unknown'

                                # Update size_value - set default if AI doesn't provide
                                size_value = cat_item.get('size_value')
                                if size_value is not None and size_value != 'null':
                                    try:
                                        product.size_value = float(size_value)
                                    except (ValueError, TypeError):
                                        if product.size_value is None:
                                            product.size_value = 0
                                elif product.size_value is None:
                                    product.size_value = 0

                                # Update size_unit - set default if AI doesn't provide
                                size_unit = cat_item.get('size_unit')
                                if size_unit and size_unit.lower() not in ['null', 'none', '']:
                                    product.size_unit = size_unit.lower()
                                elif not product.size_unit:
                                    product.size_unit = 'unknown'

                                # Brand stays null if not provided by AI (no 'unknown' fallback)

                                # Update category_group - set default if not set
                                if not product.category_group:
                                    product.category_group = 'ostalo'

                                # Update variant
                                variant = cat_item.get('variant')
                                if variant and variant not in ['null', 'none', '', None]:
                                    product.variant = variant

                                # Update match_key
                                product.update_match_key()
                                batch_updated += 1

                    db.session.commit()
                    total_updated += batch_updated
                    categorization_jobs[job_id]['processed'] = total_updated

                    app.logger.info(f"Background job {job_id}: Batch {iteration + 1} - processed {batch_updated} products")

                except Exception as e:
                    app.logger.error(f"Background job {job_id}: Error in batch {iteration + 1}: {e}")
                    categorization_jobs[job_id]['last_error'] = str(e)

                # Wait before next batch (slow drip)
                time_module.sleep(delay_seconds)

            # Mark job as completed
            categorization_jobs[job_id]['status'] = 'completed'
            categorization_jobs[job_id]['completed_at'] = datetime.now().isoformat()
            categorization_jobs[job_id]['processed'] = total_updated

            # Final count of remaining (products without product_type)
            final_remaining = Product.query.filter(
                Product.business_id == business_id,
                Product.product_type.is_(None)
            ).count()
            categorization_jobs[job_id]['remaining'] = final_remaining

            app.logger.info(f"Background job {job_id}: Completed! Total processed: {total_updated}")

        except Exception as e:
            categorization_jobs[job_id]['status'] = 'error'
            categorization_jobs[job_id]['error'] = str(e)
            app.logger.error(f"Background job {job_id}: Fatal error: {e}")


@app.route('/api/admin/products/categorize', methods=['POST'])
@csrf.exempt
def api_admin_categorize_products():
    """Start background categorization job for a business using AI (OpenAI)"""
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

        data = request.get_json()
        business_id = data.get('business_id')
        force = data.get('force', False)  # Force re-categorize all products

        if not business_id:
            return jsonify({'error': 'business_id is required'}), 400

        # Check if there's already a running job for this business
        for job_id, job in categorization_jobs.items():
            if job.get('business_id') == business_id and job.get('status') == 'running':
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'status': 'already_running',
                    'message': 'A categorization job is already running for this business'
                })

        # Count products needing processing
        from sqlalchemy import or_
        if force:
            # Force mode: process ALL products for this business
            remaining = Product.query.filter(
                Product.business_id == business_id
            ).count()
        else:
            # Normal mode: only missing category OR matching fields
            remaining = Product.query.filter(
                Product.business_id == business_id,
                or_(
                    Product.category_group.is_(None),
                    Product.category_group == '',
                    Product.brand.is_(None),
                    Product.brand == '',
                    Product.size_value.is_(None),
                    Product.size_unit.is_(None),
                    Product.size_unit == '',
                    Product.product_type.is_(None),
                    Product.product_type == ''
                )
            ).count()

        if remaining == 0:
            return jsonify({
                'success': True,
                'status': 'no_products',
                'message': 'All products are fully categorized with matching fields'
            })

        # Create new job
        job_id = str(uuid.uuid4())[:8]
        categorization_jobs[job_id] = {
            'business_id': business_id,
            'status': 'starting',
            'created_at': datetime.now().isoformat(),
            'processed': 0,
            'remaining': remaining,
            'total_initial': remaining
        }

        # Start background thread
        thread = threading.Thread(
            target=run_background_categorization,
            args=(job_id, business_id, app.app_context()),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started',
            'remaining': remaining,
            'message': f'Background categorization started for {remaining} products. Check status with job_id.'
        })

    except Exception as e:
        app.logger.error(f"Categorization error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/categorize/status/<job_id>', methods=['GET'])
@csrf.exempt
def api_admin_categorize_status(job_id):
    """Get status of a background categorization job"""
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

        job = categorization_jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify({
            'job_id': job_id,
            **job
        })

    except Exception as e:
        app.logger.error(f"Status check error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/categorize/cancel/<job_id>', methods=['POST'])
@csrf.exempt
def api_admin_categorize_cancel(job_id):
    """Cancel a running categorization job"""
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

        job = categorization_jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job['status'] != 'running':
            return jsonify({'error': 'Job is not running'}), 400

        categorization_jobs[job_id]['cancelled'] = True

        return jsonify({
            'success': True,
            'message': 'Job cancellation requested'
        })

    except Exception as e:
        app.logger.error(f"Cancel job error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/categorize/jobs', methods=['GET'])
@csrf.exempt
def api_admin_categorize_jobs():
    """List all categorization jobs"""
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

        # Return all jobs with their status
        jobs_list = []
        for job_id, job in categorization_jobs.items():
            jobs_list.append({
                'job_id': job_id,
                **job
            })

        # Sort by created_at descending
        jobs_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return jsonify({
            'jobs': jobs_list
        })

    except Exception as e:
        app.logger.error(f"List jobs error: {e}")
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
        # Product matching fields
        if 'brand' in data:
            product.brand = data['brand'] if data['brand'] else None
        if 'product_type' in data:
            product.product_type = data['product_type'].lower() if data['product_type'] else None
        if 'size_value' in data:
            product.size_value = float(data['size_value']) if data['size_value'] else None
        if 'size_unit' in data:
            product.size_unit = data['size_unit'].lower() if data['size_unit'] else None
        if 'variant' in data:
            product.variant = data['variant'] if data['variant'] else None

        # Update match_key if any matching field changed
        if any(k in data for k in ['brand', 'product_type', 'size_value', 'size_unit']):
            product.update_match_key()

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
                'category_group': product.category_group,
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': product.size_value,
                'size_unit': product.size_unit,
                'variant': product.variant,
                'match_key': product.match_key
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

@app.route('/api/admin/shopping-lists', methods=['GET'])
@csrf.exempt
def api_admin_shopping_lists():
    """Get all shopping lists with items for admin dashboard"""
    from auth_api import decode_jwt_token
    from models import ShoppingList, ShoppingListItem

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

        # Get all shopping lists with user info
        lists = db.session.query(
            ShoppingList, User.id.label('uid'), User.email, User.first_name, User.last_name, User.phone
        ).join(User, ShoppingList.user_id == User.id).order_by(
            ShoppingList.created_at.desc()
        ).all()

        result = []
        for sl, uid, email, first_name, last_name, phone in lists:
            # Get items for this list
            items = db.session.query(
                ShoppingListItem, Product.title, Business.name
            ).join(Product, ShoppingListItem.product_id == Product.id).join(
                Business, ShoppingListItem.business_id == Business.id
            ).filter(ShoppingListItem.list_id == sl.id).all()

            items_list = [{
                'id': item.ShoppingListItem.id,
                'product_title': item.title[:40] + '...' if len(item.title) > 40 else item.title,
                'business_name': item.name,
                'qty': item.ShoppingListItem.qty,
                'price': item.ShoppingListItem.price_snapshot,
                'purchased': item.ShoppingListItem.purchased_at is not None
            } for item in items]

            result.append({
                'id': sl.id,
                'user_id': uid,
                'user_email': email,
                'user_first_name': first_name,
                'user_last_name': last_name,
                'user_phone': phone,
                'status': sl.status,
                'items_count': len(items_list),
                'items': items_list,
                'created_at': sl.created_at.isoformat() if sl.created_at else None,
                'expires_at': sl.expires_at.isoformat() if sl.expires_at else None
            })

        return jsonify({
            'total': len(result),
            'lists': result
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting shopping lists: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/user-preferences', methods=['GET'])
@csrf.exempt
def api_admin_user_preferences():
    """Get all users with their preferences for admin dashboard"""
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

        # Get all users with preferences set
        users = User.query.filter(User.preferences.isnot(None)).order_by(
            User.created_at.desc()
        ).all()

        # Get store mappings
        stores = {b.id: b.name for b in Business.query.all()}

        result = []
        for user in users:
            prefs = user.preferences or {}
            preferred_store_ids = prefs.get('preferred_stores', [])
            preferred_store_names = [stores.get(sid, f'ID:{sid}') for sid in preferred_store_ids]
            grocery_interests = prefs.get('grocery_interests', [])

            result.append({
                'user_id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'city': user.city,
                'preferred_stores': preferred_store_names,
                'preferred_store_ids': preferred_store_ids,
                'grocery_interests': grocery_interests,
                'onboarding_completed': user.onboarding_completed,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })

        # Stats
        total_with_prefs = len(result)
        total_with_interests = len([u for u in result if u['grocery_interests']])
        total_onboarded = len([u for u in result if u['onboarding_completed']])

        # Count grocery interests
        interest_counts = {}
        for user in result:
            for interest in user['grocery_interests']:
                interest_lower = interest.lower().strip()
                interest_counts[interest_lower] = interest_counts.get(interest_lower, 0) + 1

        # Sort by count
        top_interests = sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        return jsonify({
            'total': total_with_prefs,
            'total_with_interests': total_with_interests,
            'total_onboarded': total_onboarded,
            'top_interests': [{'name': k, 'count': v} for k, v in top_interests],
            'users': result
        }), 200

    except Exception as e:
        app.logger.error(f"Error getting user preferences: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PRODUCT MATCHING ====================

# Background product matching job tracking
product_matching_jobs = {}  # job_id -> job_status dict


# Lazy sibling matching state
lazy_sibling_job = {
    'running': False,
    'last_processed_id': 0,
    'matches_created': 0,
    'started_at': None
}


def schedule_lazy_sibling_matching():
    """
    Schedule a slow-drip sibling/brand_variant matching job.
    Processes products slowly throughout the day to avoid overloading the system.
    Only one job runs at a time - if already running, does nothing.
    """
    import threading

    if lazy_sibling_job['running']:
        app.logger.info("Lazy sibling matching already running, skipping")
        return

    def run_lazy_matching():
        with app.app_context():
            try:
                lazy_sibling_job['running'] = True
                lazy_sibling_job['started_at'] = datetime.now().isoformat()
                lazy_sibling_job['matches_created'] = 0

                from models import ProductMatch
                import time as time_module

                # Get all products with match_key, process them slowly
                products_with_match_key = Product.query.filter(
                    Product.match_key.isnot(None),
                    Product.match_key != '',
                    Product.id > lazy_sibling_job['last_processed_id']
                ).order_by(Product.id).limit(500).all()  # Process up to 500 per job

                app.logger.info(f"Lazy sibling matching: Processing {len(products_with_match_key)} products")

                for product in products_with_match_key:
                    lazy_sibling_job['last_processed_id'] = product.id

                    # Find related products (same brand + product_type)
                    # Categorize as clone (same size) or sibling (different size)
                    if product.brand and product.product_type:
                        related = Product.query.filter(
                            Product.brand.ilike(product.brand),
                            Product.product_type.ilike(product.product_type),
                            Product.id != product.id,
                            Product.match_key.isnot(None),
                            Product.business_id != product.business_id  # Different store
                        ).limit(10).all()

                        for other in related:
                            # Compare sizes
                            size1 = product.size_value or 0
                            size2 = other.size_value or 0
                            same_size = (size1 == size2) or (size1 == 0 and size2 == 0)

                            # Compare variants (normalize for comparison)
                            v1 = (product.variant or '').lower().replace(' ', '').replace('.', '')
                            v2 = (other.variant or '').lower().replace(' ', '').replace('.', '')
                            same_variant = (v1 == v2) or (not v1 and not v2)

                            if same_size and same_variant:
                                # Same brand + same size + same variant + different store = CLONE
                                confidence = 95
                                match_type = 'clone'
                            elif same_size and not same_variant:
                                # Same size but different variant (e.g., 3.2% vs 2.8%) = same brand, different type
                                confidence = 75
                                match_type = 'sibling'  # Still sibling but different variant
                            elif not same_size and same_variant:
                                # Different size but SAME variant = SIBLING (e.g., 500ml 3.2% and 1L 3.2%)
                                confidence = 70
                                match_type = 'sibling'
                            else:
                                # Different size AND different variant = still related (same brand family)
                                confidence = 60
                                match_type = 'sibling'

                            _, created = ProductMatch.get_or_create_match(
                                product.id, other.id, match_type, confidence=confidence, created_by='auto'
                            )
                            if created:
                                lazy_sibling_job['matches_created'] += 1

                    # Find brand variants (same product_type + size, different brand)
                    if product.product_type and product.size_value and product.size_unit:
                        brand_variants = Product.query.filter(
                            Product.product_type.ilike(product.product_type),
                            Product.size_value == product.size_value,
                            Product.size_unit.ilike(product.size_unit),
                            ~Product.brand.ilike(product.brand) if product.brand else True,
                            Product.id != product.id,
                            Product.match_key.isnot(None)
                        ).limit(5).all()

                        for bv in brand_variants:
                            v1 = (product.variant or '').lower().strip()
                            v2 = (bv.variant or '').lower().strip()
                            if v1 and v2 and v1 == v2:
                                confidence = 90
                            elif not v1 and not v2:
                                confidence = 85
                            else:
                                confidence = 75

                            _, created = ProductMatch.get_or_create_match(
                                product.id, bv.id, 'brand_variant', confidence=confidence, created_by='auto'
                            )
                            if created:
                                lazy_sibling_job['matches_created'] += 1

                    # Commit every 10 products
                    if lazy_sibling_job['last_processed_id'] % 10 == 0:
                        db.session.commit()

                    # Slow drip: wait 2 seconds between products to spread load
                    time_module.sleep(2)

                db.session.commit()
                app.logger.info(f"Lazy sibling matching completed: {lazy_sibling_job['matches_created']} matches created")

                # Reset last_processed_id if we processed all products (for next cycle)
                if len(products_with_match_key) < 500:
                    lazy_sibling_job['last_processed_id'] = 0

            except Exception as e:
                app.logger.error(f"Lazy sibling matching error: {e}")
            finally:
                lazy_sibling_job['running'] = False

    thread = threading.Thread(target=run_lazy_matching, daemon=True)
    thread.start()
    return thread


def find_and_create_clone_matches(product_ids):
    """
    Quick clone detection for specific products.
    Finds products with same match_key in OTHER stores and creates clone matches.
    This is fast - just DB queries, no AI.
    Returns count of new matches created.
    """
    from models import ProductMatch

    if not product_ids:
        return 0

    clones_created = 0

    # Get products with their match_keys
    products = Product.query.filter(
        Product.id.in_(product_ids),
        Product.match_key.isnot(None),
        Product.match_key != ''
    ).all()

    for product in products:
        # Find other products with same match_key but different business
        matching_products = Product.query.filter(
            Product.match_key == product.match_key,
            Product.business_id != product.business_id,
            Product.id != product.id
        ).all()

        for match in matching_products:
            # Create clone match (100% confidence - same match_key)
            _, created = ProductMatch.get_or_create_match(
                product.id, match.id, 'clone', confidence=100, created_by='auto'
            )
            if created:
                clones_created += 1

    if clones_created > 0:
        db.session.commit()

    return clones_created


def schedule_product_processing_pipeline(product_ids, business_id, trigger_sibling_matching=True):
    """
    Hybrid processing pipeline for new/updated products:
    1. AI Categorization (for products missing fields) - async
    2. Quick Clone Detection (immediate after categorization)
    3. Sibling/Brand Variant Matching (lazy, scheduled) - optional

    This runs in a background thread.
    """
    import threading

    def run_pipeline():
        with app.app_context():
            try:
                app.logger.info(f"Starting product processing pipeline for {len(product_ids)} products")

                # Step 1: Check which products need AI categorization
                from sqlalchemy import or_
                products_needing_categorization = Product.query.filter(
                    Product.id.in_(product_ids),
                    or_(
                        Product.category_group.is_(None),
                        Product.category_group == '',
                        Product.brand.is_(None),
                        Product.size_value.is_(None),
                        Product.size_unit.is_(None)
                    )
                ).count()

                if products_needing_categorization > 0:
                    app.logger.info(f"Pipeline: {products_needing_categorization} products need AI categorization")

                    # Start categorization job and wait for it
                    job_id = str(uuid.uuid4())[:8]
                    categorization_jobs[job_id] = {
                        'business_id': business_id,
                        'status': 'starting',
                        'created_at': datetime.now().isoformat(),
                        'remaining': products_needing_categorization,
                        'processed': 0
                    }

                    # Run categorization synchronously in this thread
                    run_background_categorization(job_id, business_id, app.app_context())

                    app.logger.info(f"Pipeline: AI categorization completed for business {business_id}")
                else:
                    app.logger.info(f"Pipeline: All products already have categorization fields")

                # Step 2: Quick Clone Detection (fast - just DB queries)
                # Re-fetch products to get updated match_keys after categorization
                clones_found = find_and_create_clone_matches(product_ids)
                app.logger.info(f"Pipeline: Found {clones_found} new clone matches")

                # Step 3: Schedule lazy sibling/brand_variant matching (if requested)
                # Uses slow-drip approach instead of processing all products at once
                if trigger_sibling_matching:
                    app.logger.info(f"Pipeline: Scheduling lazy sibling/brand_variant matching")
                    schedule_lazy_sibling_matching()

                app.logger.info(f"Pipeline: Completed for {len(product_ids)} products")

            except Exception as e:
                app.logger.error(f"Pipeline error: {e}")

    # Start pipeline in background thread
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    return thread


def run_product_matching_job(job_id, app_context):
    """Background worker for finding product matches across stores"""
    with app_context:
        try:
            product_matching_jobs[job_id]['status'] = 'running'
            product_matching_jobs[job_id]['started_at'] = datetime.now().isoformat()

            from models import ProductMatch

            # Stats tracking
            clones_found = 0
            brand_variants_found = 0
            siblings_found = 0

            # Get all products with complete matching fields
            products_with_match_key = Product.query.filter(
                Product.match_key.isnot(None),
                Product.match_key != ''
            ).all()

            product_matching_jobs[job_id]['total_products'] = len(products_with_match_key)

            # Step 1: Find CLONES (same match_key, different stores)
            # Group products by match_key
            match_key_groups = {}
            for p in products_with_match_key:
                if p.match_key not in match_key_groups:
                    match_key_groups[p.match_key] = []
                match_key_groups[p.match_key].append(p)

            product_matching_jobs[job_id]['match_key_groups'] = len(match_key_groups)

            # Create clone matches for products with same match_key but different stores
            for match_key, products in match_key_groups.items():
                if len(products) > 1:
                    # Group by business_id
                    by_store = {}
                    for p in products:
                        if p.business_id not in by_store:
                            by_store[p.business_id] = []
                        by_store[p.business_id].append(p)

                    # If products exist in multiple stores, create clone matches
                    if len(by_store) > 1:
                        all_products = list(products)
                        for i in range(len(all_products)):
                            for j in range(i + 1, len(all_products)):
                                p1, p2 = all_products[i], all_products[j]
                                # Only match products from DIFFERENT stores
                                if p1.business_id != p2.business_id:
                                    _, created = ProductMatch.get_or_create_match(
                                        p1.id, p2.id, 'clone', confidence=100, created_by='auto'
                                    )
                                    if created:
                                        clones_found += 1

            db.session.commit()
            product_matching_jobs[job_id]['clones_found'] = clones_found

            # Step 2: Find BRAND VARIANTS (same product_type + size, different brand)
            # Group by product_type + size
            type_size_groups = {}
            for p in products_with_match_key:
                if p.product_type and p.size_value and p.size_unit:
                    # Normalize size for grouping
                    size_key = f"{p.product_type}:{p.size_value}{p.size_unit}"
                    if size_key not in type_size_groups:
                        type_size_groups[size_key] = []
                    type_size_groups[size_key].append(p)

            # Create brand variant matches
            for type_size_key, products in type_size_groups.items():
                if len(products) > 1:
                    # Group by brand (use '_no_brand_' as key for products without brand)
                    by_brand = {}
                    for p in products:
                        brand = (p.brand.lower() if p.brand else '_no_brand_')
                        if brand not in by_brand:
                            by_brand[brand] = []
                        by_brand[brand].append(p)

                    # If products have different brands, create brand variant matches
                    if len(by_brand) > 1:
                        brands = list(by_brand.keys())
                        for i in range(len(brands)):
                            for j in range(i + 1, len(brands)):
                                # Match one product from each brand
                                p1 = by_brand[brands[i]][0]  # First product of brand i
                                p2 = by_brand[brands[j]][0]  # First product of brand j
                                # Calculate confidence based on variant similarity
                                # Same variant = 90%, different variant = 75%
                                v1 = (p1.variant or '').lower().strip()
                                v2 = (p2.variant or '').lower().strip()
                                if v1 and v2 and v1 == v2:
                                    confidence = 90  # Same variant, different brand
                                elif not v1 and not v2:
                                    confidence = 85  # No variants specified
                                else:
                                    confidence = 75  # Different variants
                                _, created = ProductMatch.get_or_create_match(
                                    p1.id, p2.id, 'brand_variant', confidence=confidence, created_by='auto'
                                )
                                if created:
                                    brand_variants_found += 1

            db.session.commit()
            product_matching_jobs[job_id]['brand_variants_found'] = brand_variants_found

            # Step 3: Find SIBLINGS (same brand + product_type, different sizes or variants)
            # Group by brand + product_type
            brand_type_groups = {}
            for p in products_with_match_key:
                if p.product_type and p.brand:
                    key = f"{p.brand.lower().strip()}:{p.product_type.lower().strip()}"
                    if key not in brand_type_groups:
                        brand_type_groups[key] = []
                    brand_type_groups[key].append(p)

            # Create sibling matches (limit to avoid too many matches)
            for brand_type_key, products in brand_type_groups.items():
                if len(products) > 1:
                    # Group by size+variant to find unique products
                    unique_products = {}
                    for p in products:
                        size_key = f"{p.size_value}{p.size_unit}" if p.size_value and p.size_unit else 'unknown'
                        variant_key = (p.variant or '').lower().strip()
                        product_key = f"{size_key}:{variant_key}"
                        if product_key not in unique_products:
                            unique_products[product_key] = p

                    # Create sibling matches between different sizes/variants
                    product_list = list(unique_products.values())
                    for i in range(min(5, len(product_list))):  # Limit siblings
                        for j in range(i + 1, min(6, len(product_list))):
                            p1, p2 = product_list[i], product_list[j]
                            # Calculate confidence based on variant similarity
                            v1 = (p1.variant or '').lower().strip()
                            v2 = (p2.variant or '').lower().strip()
                            size1 = f"{p1.size_value}{p1.size_unit}" if p1.size_value else ''
                            size2 = f"{p2.size_value}{p2.size_unit}" if p2.size_value else ''

                            if v1 == v2 and size1 != size2:
                                confidence = 80  # Same variant, different size
                            elif v1 != v2 and size1 == size2:
                                confidence = 65  # Same size, different variant
                            else:
                                confidence = 60  # Different size and variant

                            _, created = ProductMatch.get_or_create_match(
                                p1.id, p2.id, 'sibling', confidence=confidence, created_by='auto'
                            )
                            if created:
                                siblings_found += 1

            db.session.commit()
            product_matching_jobs[job_id]['siblings_found'] = siblings_found

            # Mark job as completed
            product_matching_jobs[job_id]['status'] = 'completed'
            product_matching_jobs[job_id]['completed_at'] = datetime.now().isoformat()

            total_matches = clones_found + brand_variants_found + siblings_found
            product_matching_jobs[job_id]['total_matches_created'] = total_matches

            app.logger.info(f"Product matching job {job_id}: Completed! Created {total_matches} matches "
                          f"(clones: {clones_found}, brand_variants: {brand_variants_found}, siblings: {siblings_found})")

        except Exception as e:
            product_matching_jobs[job_id]['status'] = 'error'
            product_matching_jobs[job_id]['error'] = str(e)
            app.logger.error(f"Product matching job {job_id}: Fatal error: {e}")


@app.route('/api/admin/products/match', methods=['POST'])
@csrf.exempt
def api_admin_run_product_matching():
    """Start background product matching job"""
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

        # Check if there's already a running job
        for job_id, job in product_matching_jobs.items():
            if job.get('status') == 'running':
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'status': 'already_running',
                    'message': 'A product matching job is already running'
                })

        # Count products with match_key
        products_count = Product.query.filter(
            Product.match_key.isnot(None),
            Product.match_key != ''
        ).count()

        if products_count == 0:
            return jsonify({
                'success': True,
                'status': 'no_products',
                'message': 'No products with match keys to process. Run AI categorization first.'
            })

        # Create new job
        job_id = str(uuid.uuid4())[:8]
        product_matching_jobs[job_id] = {
            'status': 'starting',
            'created_at': datetime.now().isoformat(),
            'total_products': products_count,
            'clones_found': 0,
            'brand_variants_found': 0,
            'siblings_found': 0
        }

        # Start background thread
        thread = threading.Thread(
            target=run_product_matching_job,
            args=(job_id, app.app_context()),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started',
            'message': f'Product matching job started for {products_count} products'
        })

    except Exception as e:
        app.logger.error(f"Start product matching error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/match/status/<job_id>', methods=['GET'])
@csrf.exempt
def api_admin_product_matching_status(job_id):
    """Get status of a product matching job"""
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

        if job_id not in product_matching_jobs:
            return jsonify({'error': 'Job not found'}), 404

        job = product_matching_jobs[job_id]
        return jsonify({
            'job_id': job_id,
            **job
        })

    except Exception as e:
        app.logger.error(f"Get matching job status error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/matches', methods=['GET'])
@csrf.exempt
def api_admin_get_product_matches():
    """Get product matches for a specific product or browse all matches"""
    from auth_api import decode_jwt_token
    from models import ProductMatch

    # Check JWT authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)

        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        product_id = request.args.get('product_id', type=int)
        match_type = request.args.get('match_type')  # 'clone', 'brand_variant', 'sibling'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = ProductMatch.query

        if product_id:
            query = query.filter(
                (ProductMatch.product_a_id == product_id) |
                (ProductMatch.product_b_id == product_id)
            )

        if match_type:
            query = query.filter(ProductMatch.match_type == match_type)

        # Paginate
        total = query.count()
        matches = query.order_by(ProductMatch.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        result = []
        for m in matches:
            result.append({
                'id': m.id,
                'match_type': m.match_type,
                'confidence': m.confidence,
                'created_by': m.created_by,
                'created_at': m.created_at.isoformat() if m.created_at else None,
                'product_a': {
                    'id': m.product_a.id,
                    'title': m.product_a.title,
                    'brand': m.product_a.brand,
                    'product_type': m.product_a.product_type,
                    'size': f"{m.product_a.size_value}{m.product_a.size_unit}" if m.product_a.size_value else None,
                    'business_id': m.product_a.business_id,
                    'business_name': m.product_a.business.name if m.product_a.business else None,
                    'discount_price': m.product_a.discount_price,
                    'base_price': m.product_a.base_price,
                    'image_path': m.product_a.image_path
                },
                'product_b': {
                    'id': m.product_b.id,
                    'title': m.product_b.title,
                    'brand': m.product_b.brand,
                    'product_type': m.product_b.product_type,
                    'size': f"{m.product_b.size_value}{m.product_b.size_unit}" if m.product_b.size_value else None,
                    'business_id': m.product_b.business_id,
                    'business_name': m.product_b.business.name if m.product_b.business else None,
                    'discount_price': m.product_b.discount_price,
                    'base_price': m.product_b.base_price,
                    'image_path': m.product_b.image_path
                }
            })

        return jsonify({
            'matches': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })

    except Exception as e:
        app.logger.error(f"Get product matches error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/match-stats', methods=['GET'])
@csrf.exempt
def api_admin_product_match_stats():
    """Get statistics about product matches"""
    from auth_api import decode_jwt_token
    from models import ProductMatch
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

        # Count matches by type
        type_counts = db.session.query(
            ProductMatch.match_type,
            func.count(ProductMatch.id).label('count')
        ).group_by(ProductMatch.match_type).all()

        # Count products with match_key
        products_with_key = Product.query.filter(
            Product.match_key.isnot(None),
            Product.match_key != ''
        ).count()

        # Count unique match_keys
        unique_keys = db.session.query(func.count(func.distinct(Product.match_key))).filter(
            Product.match_key.isnot(None),
            Product.match_key != ''
        ).scalar()

        # Products missing matching fields
        from sqlalchemy import or_
        products_missing_fields = Product.query.filter(
            or_(
                Product.brand.is_(None),
                Product.size_value.is_(None),
                Product.size_unit.is_(None),
                Product.product_type.is_(None)
            )
        ).count()

        return jsonify({
            'matches_by_type': {t: c for t, c in type_counts},
            'total_matches': sum(c for _, c in type_counts),
            'products_with_match_key': products_with_key,
            'unique_match_keys': unique_keys,
            'products_missing_fields': products_missing_fields
        })

    except Exception as e:
        app.logger.error(f"Get match stats error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/products/match-groups', methods=['GET'])
@csrf.exempt
def api_admin_get_match_groups():
    """Get products grouped by match_key for cross-store comparison"""
    from auth_api import decode_jwt_token
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

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        only_cross_store = request.args.get('only_cross_store', 'false').lower() == 'true'

        # Find match_keys that have multiple products (potential matches)
        # Subquery to get match_keys with counts
        subq = db.session.query(
            Product.match_key,
            func.count(Product.id).label('product_count'),
            func.count(func.distinct(Product.business_id)).label('store_count')
        ).filter(
            Product.match_key.isnot(None),
            Product.match_key != ''
        ).group_by(Product.match_key)

        if only_cross_store:
            # Only groups with products from multiple stores
            subq = subq.having(func.count(func.distinct(Product.business_id)) > 1)
        else:
            # Groups with at least 2 products
            subq = subq.having(func.count(Product.id) > 1)

        subq = subq.subquery()

        # Get all match_keys with counts
        query = db.session.query(subq)

        if search:
            # Search in match_key
            query = query.filter(subq.c.match_key.ilike(f'%{search}%'))

        # Get total count
        total = query.count()

        # Get paginated match_keys
        match_keys_data = query.order_by(subq.c.store_count.desc(), subq.c.product_count.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()

        # Get products for each match_key
        groups = []
        for mk_data in match_keys_data:
            match_key = mk_data[0]
            products = Product.query.filter(
                Product.match_key == match_key
            ).order_by(Product.business_id).all()

            # Get business names
            business_ids = list(set(p.business_id for p in products))
            businesses = {b.id: b for b in Business.query.filter(Business.id.in_(business_ids)).all()}

            products_data = []
            for p in products:
                biz = businesses.get(p.business_id)
                products_data.append({
                    'id': p.id,
                    'title': p.title,
                    'brand': p.brand,
                    'product_type': p.product_type,
                    'size_value': p.size_value,
                    'size_unit': p.size_unit,
                    'variant': p.variant,
                    'base_price': float(p.base_price) if p.base_price else None,
                    'discount_price': float(p.discount_price) if p.discount_price else None,
                    'image_url': p.image_path,
                    'business_id': p.business_id,
                    'business_name': biz.name if biz else 'Unknown'
                })

            # Find lowest and highest price
            prices = [p['discount_price'] or p['base_price'] for p in products_data if (p['discount_price'] or p['base_price'])]

            groups.append({
                'match_key': match_key,
                'product_count': mk_data[1],
                'store_count': mk_data[2],
                'products': products_data,
                'lowest_price': min(prices) if prices else None,
                'highest_price': max(prices) if prices else None,
                'price_spread': max(prices) - min(prices) if len(prices) > 1 else 0
            })

        return jsonify({
            'groups': groups,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })

    except Exception as e:
        app.logger.error(f"Get match groups error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/products/<int:product_id>/related', methods=['GET'])
@require_jwt_auth
def api_get_product_related(product_id):
    """Get related products for a specific product (clones, brand variants, siblings)

    This is a public API endpoint for use on product detail pages to show:
    - clones: Same product in other stores (price comparison)
    - brand_variants: Same type/size but different brand
    - siblings: Same brand but different sizes

    If user is logged in, results are filtered to only show stores in their preferences.
    """
    from models import ProductMatch
    from auth_api import decode_jwt_token

    try:
        product = Product.query.get_or_404(product_id)
        source_business = Business.query.get(product.business_id)

        # Get user's preferred stores (if logged in)
        preferred_store_ids = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
                payload = decode_jwt_token(token)
                if payload:
                    user = User.query.filter_by(id=payload['user_id']).first()
                    if user and user.preferences:
                        preferred_store_ids = user.preferences.get('preferred_stores', [])
                        # If user has no stores selected, show all (don't filter)
                        if not preferred_store_ids:
                            preferred_store_ids = None
            except Exception:
                pass  # If token parsing fails, show all stores

        # Source product data for comparison
        source_price = float(product.discount_price or product.base_price or 0)

        # Get all matches involving this product
        matches = ProductMatch.query.filter(
            (ProductMatch.product_a_id == product_id) |
            (ProductMatch.product_b_id == product_id)
        ).all()

        # Organize by match type
        clones = []
        brand_variants = []
        siblings = []

        def build_product_data(p, business, confidence=None):
            """Helper to build product data dict with price comparison"""
            effective_price = float(p.discount_price or p.base_price or 0)
            price_diff = effective_price - source_price if source_price else 0
            price_diff_pct = round((price_diff / source_price) * 100, 1) if source_price else 0

            return {
                'id': p.id,
                'title': p.title,
                'brand': p.brand,
                'product_type': p.product_type,
                'size_value': p.size_value,
                'size_unit': p.size_unit,
                'variant': p.variant,
                'base_price': float(p.base_price) if p.base_price else None,
                'discount_price': float(p.discount_price) if p.discount_price else None,
                'effective_price': effective_price,
                'image_path': p.image_path,
                'business_id': p.business_id,
                'business_name': business.name if business else 'Unknown',
                'city': p.city or (business.city if business else None),
                'confidence': confidence,
                # Price comparison fields
                'price_diff': round(price_diff, 2),
                'price_diff_pct': price_diff_pct,
                'is_cheaper': price_diff < -0.01,
                'is_more_expensive': price_diff > 0.01,
                'expires': p.expires.isoformat() if p.expires else None
            }

        for m in matches:
            # Get the OTHER product in the match
            other_product = m.product_b if m.product_a_id == product_id else m.product_a

            if not other_product:
                continue

            # Filter by user's preferred stores (if set)
            if preferred_store_ids is not None and other_product.business_id not in preferred_store_ids:
                continue

            # Get business name
            business = Business.query.get(other_product.business_id)
            product_data = build_product_data(other_product, business, m.confidence)

            if m.match_type == 'clone':
                clones.append(product_data)
            elif m.match_type == 'brand_variant':
                brand_variants.append(product_data)
            elif m.match_type == 'sibling':
                siblings.append(product_data)

        # Also find clones by match_key (same product in other stores, even without explicit match)
        if product.match_key:
            same_key_query = Product.query.filter(
                Product.match_key == product.match_key,
                Product.id != product_id,
                Product.business_id != product.business_id
            )
            # Filter by preferred stores if set
            if preferred_store_ids is not None:
                same_key_query = same_key_query.filter(Product.business_id.in_(preferred_store_ids))

            same_key_products = same_key_query.all()

            existing_clone_ids = {p['id'] for p in clones}
            for p in same_key_products:
                if p.id not in existing_clone_ids:
                    business = Business.query.get(p.business_id)
                    clones.append(build_product_data(p, business, 100))

        # Sort clones by price (lowest first)
        clones.sort(key=lambda x: x['effective_price'] or 999999)

        # Sort siblings by size (smallest first)
        siblings.sort(key=lambda x: x['size_value'] or 999999)

        # Sort brand_variants by price (lowest first)
        brand_variants.sort(key=lambda x: x['effective_price'] or 999999)

        # Find cheapest clone
        cheapest_clone = clones[0] if clones else None
        has_cheaper_option = cheapest_clone and cheapest_clone['is_cheaper'] if cheapest_clone else False

        return jsonify({
            'success': True,
            'product_id': product_id,
            'source_product': {
                'id': product.id,
                'title': product.title,
                'brand': product.brand,
                'product_type': product.product_type,
                'size_value': product.size_value,
                'size_unit': product.size_unit,
                'variant': product.variant,
                'base_price': float(product.base_price) if product.base_price else None,
                'discount_price': float(product.discount_price) if product.discount_price else None,
                'effective_price': source_price,
                'business_name': source_business.name if source_business else 'Unknown',
                'city': product.city or (source_business.city if source_business else None)
            },
            'clones': clones,  # Same product in other stores
            'brand_variants': brand_variants,  # Same type, different brand
            'siblings': siblings,  # Same brand, different size
            'total_related': len(clones) + len(brand_variants) + len(siblings),
            'has_cheaper_option': has_cheaper_option,
            'cheapest_clone': cheapest_clone
        })

    except Exception as e:
        app.logger.error(f"Get product related error: {e}")
        import traceback
        traceback.print_exc()
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
