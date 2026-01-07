"""
Coupon API routes for Exclusive Discounts feature.
Handles coupon CRUD, purchase, redemption, and ratings.

NOTE: All authenticated endpoints use JWT tokens, not Flask-Login sessions.
The @jwt_required and @jwt_admin_required decorators handle authentication.
Use get_jwt_user() to get the current user after authentication.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from app import db
from models import (
    Coupon, UserCoupon, Business, FeatureFlag, User,
    BusinessMembership, user_has_business_role, Store, Campaign
)
from credits_service_monthly import MonthlyCreditsService
from sendgrid_utils import (
    send_coupon_purchase_email,
    send_coupon_sale_notification_email,
    send_coupon_redemption_email,
    send_new_rating_notification_email
)
import pytz
import logging

logger = logging.getLogger(__name__)

coupon_bp = Blueprint('coupons', __name__)


def slugify_title(title: str) -> str:
    """Convert title to URL-friendly slug for S3 filenames"""
    import re
    import unicodedata
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)
    # Convert to lowercase
    slug = slug.lower()
    # Replace special Bosnian characters with ASCII equivalents
    replacements = {'č': 'c', 'ć': 'c', 'š': 's', 'ž': 'z', 'đ': 'd'}
    for char, replacement in replacements.items():
        slug = slug.replace(char, replacement)
    # Remove non-alphanumeric characters except spaces and hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    # Limit length
    return slug[:50]


def jwt_required(f):
    """Decorator to require authentication via JWT token (for regular users)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token

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
            if not user:
                return jsonify({'error': 'User not found'}), 401

            request.jwt_user = user
            request.jwt_user_id = user_id

        except Exception as e:
            logger.error(f"JWT auth error: {e}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)
    return decorated_function


def jwt_admin_required(f):
    """Decorator to require admin privileges via JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token

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


def get_jwt_user():
    """Get the current user from JWT token (call after jwt_required)"""
    return getattr(request, 'jwt_user', None)


def get_optional_jwt_user():
    """Try to get user from JWT token, return None if not authenticated.
    Use this for public endpoints that optionally check user status."""
    from auth_api import decode_jwt_token

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if not payload:
            return None
        user_id = payload.get('user_id')
        return User.query.get(user_id)
    except Exception:
        return None

# Bosnia timezone
BOSNIA_TZ = pytz.timezone('Europe/Sarajevo')


def get_bosnia_time():
    """Get current time in Bosnia timezone"""
    return datetime.now(BOSNIA_TZ)


def is_feature_enabled(user=None):
    """Check if exclusive coupons feature is enabled (admins always see it)"""
    if user and user.is_admin:
        return True
    return FeatureFlag.is_enabled('exclusive_coupons_enabled', default=False)


# ==================== PUBLIC ENDPOINTS ====================

@coupon_bp.route('/api/coupons', methods=['GET'])
def get_coupons():
    """Get all active coupons (public endpoint)"""
    # Check feature flag - optionally get user from JWT
    user = get_optional_jwt_user()
    if not is_feature_enabled(user):
        return jsonify({'error': 'Feature not available', 'coupons': []}), 200

    # Get active coupons with remaining quantity
    coupons = Coupon.query.filter(
        Coupon.is_active == True,
        Coupon.remaining_quantity > 0
    ).order_by(Coupon.created_at.desc()).all()

    result = []
    for coupon in coupons:
        business = coupon.business
        result.append({
            'id': coupon.id,
            'article_name': coupon.article_name,
            'description': coupon.description,
            'normal_price': coupon.normal_price,
            'discount_percent': coupon.discount_percent,
            'final_price': coupon.final_price,
            'savings': coupon.savings,
            'quantity_description': coupon.quantity_description,
            'total_quantity': coupon.total_quantity,
            'remaining_quantity': coupon.remaining_quantity,
            'credits_cost': coupon.credits_cost,
            'valid_days': coupon.valid_days,
            'business': {
                'id': business.id,
                'name': business.name,
                'slug': business.slug,
                'logo_path': business.logo_path,
                'city': business.city,
                'address': business.address,
                'google_link': business.google_link,
                'working_hours': business.working_hours,
                'is_open': business.is_open_now(),
                'average_rating': business.average_rating,
                'total_reviews': business.total_reviews,
            }
        })

    return jsonify({'coupons': result})


@coupon_bp.route('/api/coupons/<int:coupon_id>', methods=['GET'])
def get_coupon(coupon_id):
    """Get single coupon details"""
    user = get_optional_jwt_user()
    if not is_feature_enabled(user):
        return jsonify({'error': 'Feature not available'}), 404

    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    business = coupon.business

    # Get reviews for this coupon
    reviews = []
    user_coupons = UserCoupon.query.filter(
        UserCoupon.coupon_id == coupon_id,
        UserCoupon.buyer_to_business_rating.isnot(None)
    ).order_by(UserCoupon.redeemed_at.desc()).limit(10).all()

    for uc in user_coupons:
        reviews.append({
            'rating': uc.buyer_to_business_rating,
            'comment': uc.buyer_to_business_comment,
            'product_review': uc.buyer_product_review,
            'user_name': f"{uc.user.first_name or ''} {(uc.user.last_name or '')[:1]}.".strip() or 'Korisnik',
            'date': uc.redeemed_at.isoformat() if uc.redeemed_at else None
        })

    return jsonify({
        'coupon': {
            'id': coupon.id,
            'article_name': coupon.article_name,
            'description': coupon.description,
            'normal_price': coupon.normal_price,
            'discount_percent': coupon.discount_percent,
            'final_price': coupon.final_price,
            'savings': coupon.savings,
            'quantity_description': coupon.quantity_description,
            'total_quantity': coupon.total_quantity,
            'remaining_quantity': coupon.remaining_quantity,
            'credits_cost': coupon.credits_cost,
            'valid_days': coupon.valid_days,
            'is_sold_out': coupon.is_sold_out,
            'business': {
                'id': business.id,
                'name': business.name,
                'slug': business.slug,
                'logo_path': business.logo_path,
                'city': business.city,
                'address': business.address,
                'description': business.description,
                'google_link': business.google_link,
                'working_hours': business.working_hours,
                'is_open': business.is_open_now(),
                'average_rating': business.average_rating,
                'total_reviews': business.total_reviews,
            },
            'reviews': reviews
        }
    })


@coupon_bp.route('/api/coupons/feature-status', methods=['GET'])
def get_feature_status():
    """Check if exclusive coupons feature is enabled"""
    user = get_optional_jwt_user()
    return jsonify({
        'enabled': is_feature_enabled(user),
        'is_admin': user.is_admin if user else False
    })


# ==================== USER COUPON ENDPOINTS ====================

@coupon_bp.route('/api/coupons/<int:coupon_id>/purchase', methods=['POST'])
@jwt_required
def purchase_coupon(coupon_id):
    """Purchase a coupon with credits"""
    current_user = get_jwt_user()
    if not is_feature_enabled(current_user):
        return jsonify({'error': 'Feature not available'}), 403

    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    if not coupon.is_active:
        return jsonify({'error': 'Kupon više nije aktivan'}), 400

    if coupon.remaining_quantity <= 0:
        return jsonify({'error': 'Svi kuponi su rasprodani'}), 400

    # Check if user already has an active coupon for this
    existing = UserCoupon.query.filter(
        UserCoupon.user_id == current_user.id,
        UserCoupon.coupon_id == coupon_id,
        UserCoupon.status == 'active'
    ).first()
    if existing:
        return jsonify({'error': 'Već imate aktivan kupon za ovu ponudu'}), 400

    # Check credits
    balance = MonthlyCreditsService.get_balance(current_user.id)
    available = balance.get('total_available', 0)
    if available < coupon.credits_cost:
        return jsonify({
            'error': 'Nedovoljno kredita',
            'available': available,
            'required': coupon.credits_cost
        }), 400

    # Spend credits
    result = MonthlyCreditsService.deduct_credits(
        current_user.id,
        coupon.credits_cost,
        'COUPON_PURCHASE',
        {'coupon_id': coupon_id, 'article': coupon.article_name}
    )
    if not result.get('success'):
        return jsonify({'error': 'Greška pri plaćanju kreditima'}), 500

    # Calculate expiry date in Bosnia timezone
    bosnia_now = get_bosnia_time()
    expires_at = bosnia_now + timedelta(days=coupon.valid_days)

    # Create user coupon
    user_coupon = UserCoupon(
        coupon_id=coupon_id,
        user_id=current_user.id,
        redemption_code=UserCoupon.generate_redemption_code(),
        status='active',
        purchased_at=datetime.utcnow(),
        expires_at=expires_at.replace(tzinfo=None)  # Store as naive UTC
    )

    # Decrease remaining quantity
    coupon.remaining_quantity -= 1

    db.session.add(user_coupon)
    db.session.commit()

    # Send email notification to buyer
    try:
        coupon_data = {
            'redemption_code': user_coupon.redemption_code,
            'article_name': coupon.article_name,
            'business_name': coupon.business.name,
            'business_address': coupon.business.address or '',
            'original_price': coupon.normal_price,
            'final_price': coupon.final_price,
            'discount_percent': coupon.discount_percent,
            'expires_at': expires_at.strftime('%d.%m.%Y'),
            'valid_days': coupon.valid_days
        }
        send_coupon_purchase_email(
            current_user.email,
            current_user.first_name or '',
            coupon_data
        )
    except Exception as e:
        logger.error(f"Failed to send purchase email to buyer: {e}")

    # Send notification to business owner
    try:
        # Find business owner
        owner_membership = BusinessMembership.query.filter(
            BusinessMembership.business_id == coupon.business_id,
            BusinessMembership.role == 'owner',
            BusinessMembership.is_active == True
        ).first()

        if owner_membership:
            sale_data = {
                'buyer_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or 'Korisnik',
                'article_name': coupon.article_name,
                'final_price': coupon.final_price,
                'remaining_quantity': coupon.remaining_quantity,
                'total_sold': coupon.total_quantity - coupon.remaining_quantity
            }
            send_coupon_sale_notification_email(
                owner_membership.user.email,
                coupon.business.name,
                sale_data
            )
    except Exception as e:
        logger.error(f"Failed to send sale notification to business: {e}")

    return jsonify({
        'success': True,
        'user_coupon': {
            'id': user_coupon.id,
            'redemption_code': user_coupon.redemption_code,
            'expires_at': user_coupon.expires_at.isoformat(),
            'article_name': coupon.article_name,
            'business_name': coupon.business.name,
            'google_link': coupon.business.google_link
        }
    })


@coupon_bp.route('/api/user/coupons', methods=['GET'])
@jwt_required
def get_user_coupons():
    """Get current user's purchased coupons"""
    current_user = get_jwt_user()
    status_filter = request.args.get('status', 'all')  # 'all', 'active', 'redeemed', 'expired'

    query = UserCoupon.query.filter(UserCoupon.user_id == current_user.id)

    if status_filter == 'active':
        query = query.filter(UserCoupon.status == 'active')
    elif status_filter == 'redeemed':
        query = query.filter(UserCoupon.status == 'redeemed')
    elif status_filter == 'expired':
        query = query.filter(UserCoupon.status == 'expired')

    user_coupons = query.order_by(UserCoupon.purchased_at.desc()).all()

    result = []
    for uc in user_coupons:
        coupon = uc.coupon
        business = coupon.business

        # Check if expired but not marked
        if uc.status == 'active' and uc.is_expired:
            uc.status = 'expired'
            db.session.commit()

        result.append({
            'id': uc.id,
            'redemption_code': uc.redemption_code,
            'status': uc.status,
            'purchased_at': uc.purchased_at.isoformat(),
            'expires_at': uc.expires_at.isoformat(),
            'redeemed_at': uc.redeemed_at.isoformat() if uc.redeemed_at else None,
            'can_review': uc.status == 'redeemed' and not uc.buyer_to_business_rating,
            'can_product_review': uc.can_submit_product_review,
            'coupon': {
                'id': coupon.id,
                'article_name': coupon.article_name,
                'discount_percent': coupon.discount_percent,
                'final_price': coupon.final_price,
                'normal_price': coupon.normal_price,
            },
            'business': {
                'id': business.id,
                'name': business.name,
                'logo_path': business.logo_path,
                'google_link': business.google_link,
                'address': business.address,
            }
        })

    return jsonify({'coupons': result})


@coupon_bp.route('/api/user/coupons/<int:user_coupon_id>/review', methods=['POST'])
@jwt_required
def submit_review(user_coupon_id):
    """Submit review for a redeemed coupon"""
    current_user = get_jwt_user()
    user_coupon = UserCoupon.query.filter(
        UserCoupon.id == user_coupon_id,
        UserCoupon.user_id == current_user.id
    ).first()

    if not user_coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    if user_coupon.status != 'redeemed':
        return jsonify({'error': 'Kupon mora biti iskorišten prije ocjenjivanja'}), 400

    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Ocjena mora biti između 1 i 5'}), 400

    user_coupon.buyer_to_business_rating = rating
    user_coupon.buyer_to_business_comment = comment

    # Update business rating cache
    user_coupon.coupon.business.update_rating_cache()

    db.session.commit()

    # Send notification to business owner about new rating
    try:
        owner_membership = BusinessMembership.query.filter(
            BusinessMembership.business_id == user_coupon.coupon.business_id,
            BusinessMembership.role == 'owner',
            BusinessMembership.is_active == True
        ).first()

        if owner_membership:
            rating_data = {
                'rater_name': f"{current_user.first_name or ''} {(current_user.last_name or '')[:1]}.".strip() or 'Korisnik',
                'rating': rating,
                'comment': comment,
                'article_name': user_coupon.coupon.article_name
            }
            send_new_rating_notification_email(
                owner_membership.user.email,
                owner_membership.user.first_name or '',
                rating_data,
                is_business=True
            )
    except Exception as e:
        logger.error(f"Failed to send rating notification to business: {e}")

    return jsonify({'success': True})


@coupon_bp.route('/api/user/coupons/<int:user_coupon_id>/product-review', methods=['POST'])
@jwt_required
def submit_product_review(user_coupon_id):
    """Submit product review (available 24h after redemption)"""
    current_user = get_jwt_user()
    user_coupon = UserCoupon.query.filter(
        UserCoupon.id == user_coupon_id,
        UserCoupon.user_id == current_user.id
    ).first()

    if not user_coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    if not user_coupon.can_submit_product_review:
        return jsonify({'error': 'Review artikla još nije dostupan'}), 400

    data = request.get_json()
    review = data.get('review', '')

    if len(review) < 20:
        return jsonify({'error': 'Review mora imati minimalno 20 karaktera'}), 400

    user_coupon.buyer_product_review = review
    user_coupon.buyer_review_submitted_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'success': True})


# ==================== BUSINESS OWNER ENDPOINTS ====================

@coupon_bp.route('/api/business/<int:business_id>/coupons', methods=['GET'])
@jwt_required
def get_business_coupons(business_id):
    """Get coupons for a business (owner/admin only)"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    coupons = Coupon.query.filter(Coupon.business_id == business_id).order_by(Coupon.created_at.desc()).all()

    result = []
    for coupon in coupons:
        # Get pending redemptions
        pending_count = UserCoupon.query.filter(
            UserCoupon.coupon_id == coupon.id,
            UserCoupon.status == 'active'
        ).count()

        redeemed_count = UserCoupon.query.filter(
            UserCoupon.coupon_id == coupon.id,
            UserCoupon.status == 'redeemed'
        ).count()

        result.append({
            'id': coupon.id,
            'campaign_id': coupon.campaign_id,
            'campaign_name': coupon.campaign.name if coupon.campaign else None,
            'article_name': coupon.article_name,
            'description': coupon.description,
            'normal_price': coupon.normal_price,
            'discount_percent': coupon.discount_percent,
            'final_price': coupon.final_price,
            'quantity_description': coupon.quantity_description,
            'total_quantity': coupon.total_quantity,
            'remaining_quantity': coupon.remaining_quantity,
            'valid_days': coupon.valid_days,
            'is_active': coupon.is_active,
            'created_at': coupon.created_at.isoformat(),
            'stats': {
                'sold': coupon.total_quantity - coupon.remaining_quantity,
                'pending': pending_count,
                'redeemed': redeemed_count
            }
        })

    return jsonify({
        'coupons': result,
        'business': {
            'id': business.id,
            'name': business.name,
            'max_campaigns_allowed': business.max_campaigns_allowed,
            'campaigns_count': business.get_campaigns_count(),
            'active_coupons_count': business.get_active_coupons_count(),
            'can_create_campaign': business.can_create_campaign()
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/coupons', methods=['POST'])
@jwt_required
def create_coupon(business_id):
    """Create a new coupon within a campaign (owner/admin only)"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    if not business.has_exclusive_coupons:
        return jsonify({'error': 'Ekskluzivni kuponi nisu omogućeni za ovaj biznis'}), 400

    data = request.get_json()

    # Validate campaign_id is provided
    campaign_id = data.get('campaign_id')
    if not campaign_id:
        return jsonify({'error': 'campaign_id je obavezan. Morate prvo kreirati kampanju.'}), 400

    # Validate campaign exists and belongs to this business
    campaign = Campaign.query.filter_by(id=campaign_id, business_id=business_id).first()
    if not campaign:
        return jsonify({'error': 'Kampanja nije pronađena'}), 404

    if not campaign.is_active:
        return jsonify({'error': 'Kampanja nije aktivna'}), 400

    # Check campaign coupon limit (admin can bypass)
    if not campaign.can_add_coupon() and not current_user.is_admin:
        return jsonify({
            'error': f'Maksimalan broj kupona u ovoj kampaniji ({campaign.max_coupons}) je dostignut'
        }), 400

    # Validate required fields
    required = ['article_name', 'normal_price', 'discount_percent', 'total_quantity', 'valid_days']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Polje {field} je obavezno'}), 400

    # Validate values
    if data['discount_percent'] < 1 or data['discount_percent'] > 99:
        return jsonify({'error': 'Popust mora biti između 1% i 99%'}), 400

    if data['valid_days'] < 1 or data['valid_days'] > 30:
        return jsonify({'error': 'Broj dana važenja mora biti između 1 i 30'}), 400

    if data['total_quantity'] < 1 or data['total_quantity'] > 100:
        return jsonify({'error': 'Broj kupona mora biti između 1 i 100'}), 400

    # Parse expires_at if provided (coupon-level expiration)
    # If not provided, use campaign expiration if set
    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    elif campaign.expires_at:
        expires_at = campaign.expires_at

    coupon = Coupon(
        business_id=business_id,
        campaign_id=campaign_id,
        store_id=data.get('store_id'),  # Optional: specific store location
        article_name=data['article_name'],
        description=data.get('description'),
        normal_price=data['normal_price'],
        discount_percent=data['discount_percent'],
        quantity_description=data.get('quantity_description'),
        total_quantity=data['total_quantity'],
        remaining_quantity=data['total_quantity'],
        credits_cost=20,  # Fixed at 20 credits
        valid_days=data['valid_days'],
        expires_at=expires_at,
        is_active=True,
        created_by_user_id=current_user.id
    )

    db.session.add(coupon)
    db.session.commit()

    return jsonify({
        'success': True,
        'coupon': {
            'id': coupon.id,
            'article_name': coupon.article_name,
            'campaign_id': campaign_id
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/coupons/<int:coupon_id>', methods=['PUT'])
@jwt_required
def update_coupon(business_id, coupon_id):
    """Update a coupon (owner/admin only)"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    coupon = Coupon.query.filter(
        Coupon.id == coupon_id,
        Coupon.business_id == business_id
    ).first()

    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    data = request.get_json()

    # Can only update certain fields
    if 'is_active' in data:
        coupon.is_active = data['is_active']

    if 'description' in data:
        coupon.description = data['description']

    # Admin can update more fields
    if current_user.is_admin:
        if 'total_quantity' in data:
            diff = data['total_quantity'] - coupon.total_quantity
            coupon.total_quantity = data['total_quantity']
            coupon.remaining_quantity = max(0, coupon.remaining_quantity + diff)

    db.session.commit()

    return jsonify({'success': True})


@coupon_bp.route('/api/business/<int:business_id>/pending-coupons', methods=['GET'])
@jwt_required
def get_pending_redemptions(business_id):
    """Get pending coupon redemptions for a business"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    pending = UserCoupon.query.join(Coupon).filter(
        Coupon.business_id == business_id,
        UserCoupon.status == 'active'
    ).order_by(UserCoupon.purchased_at.desc()).all()

    result = []
    for uc in pending:
        result.append({
            'id': uc.id,
            'redemption_code': uc.redemption_code,
            'purchased_at': uc.purchased_at.isoformat(),
            'expires_at': uc.expires_at.isoformat(),
            'user': {
                'name': f"{uc.user.first_name or ''} {uc.user.last_name or ''}".strip() or 'Korisnik',
                'email': uc.user.email
            },
            'coupon': {
                'id': uc.coupon.id,
                'article_name': uc.coupon.article_name,
                'discount_percent': uc.coupon.discount_percent
            }
        })

    return jsonify({'pending': result})


@coupon_bp.route('/api/business/<int:business_id>/redeem', methods=['POST'])
@jwt_required
def redeem_coupon(business_id):
    """Redeem a coupon by entering 6-digit code"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    code = data.get('code', '').strip()

    if len(code) != 6 or not code.isdigit():
        return jsonify({'error': 'Kod mora biti 6 cifara'}), 400

    # Find the user coupon
    user_coupon = UserCoupon.query.join(Coupon).filter(
        Coupon.business_id == business_id,
        UserCoupon.redemption_code == code,
        UserCoupon.status == 'active'
    ).first()

    if not user_coupon:
        return jsonify({'error': 'Kupon nije pronađen ili je već iskorišten'}), 404

    # Check if expired
    if user_coupon.is_expired:
        user_coupon.status = 'expired'
        db.session.commit()
        return jsonify({'error': 'Kupon je istekao'}), 400

    # Redeem
    user_coupon.status = 'redeemed'
    user_coupon.redeemed_at = datetime.utcnow()
    user_coupon.buyer_review_unlocked_at = datetime.utcnow() + timedelta(hours=24)

    db.session.commit()

    # Send email to buyer about successful redemption
    try:
        coupon = user_coupon.coupon
        redemption_data = {
            'article_name': coupon.article_name,
            'business_name': coupon.business.name,
            'final_price': coupon.final_price,
            'savings': coupon.savings,
            'redeemed_at': datetime.utcnow().strftime('%d.%m.%Y u %H:%M')
        }
        send_coupon_redemption_email(
            user_coupon.user.email,
            user_coupon.user.first_name or '',
            redemption_data
        )
    except Exception as e:
        logger.error(f"Failed to send redemption email to buyer: {e}")

    # TODO: Send WebSocket notification to buyer for real-time update

    return jsonify({
        'success': True,
        'user_coupon': {
            'id': user_coupon.id,
            'user_name': f"{user_coupon.user.first_name or ''} {user_coupon.user.last_name or ''}".strip(),
            'article_name': user_coupon.coupon.article_name
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/rate-buyer/<int:user_coupon_id>', methods=['POST'])
@jwt_required
def rate_buyer(business_id, user_coupon_id):
    """Business rates a buyer after redemption"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    user_coupon = UserCoupon.query.join(Coupon).filter(
        UserCoupon.id == user_coupon_id,
        Coupon.business_id == business_id,
        UserCoupon.status == 'redeemed'
    ).first()

    if not user_coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Ocjena mora biti između 1 i 5'}), 400

    user_coupon.business_to_buyer_rating = rating
    user_coupon.business_to_buyer_comment = comment

    db.session.commit()

    # Send notification to buyer about rating from business
    try:
        rating_data = {
            'rater_name': user_coupon.coupon.business.name,
            'rating': rating,
            'comment': comment,
            'article_name': user_coupon.coupon.article_name,
            'business_name': user_coupon.coupon.business.name
        }
        send_new_rating_notification_email(
            user_coupon.user.email,
            user_coupon.user.first_name or '',
            rating_data,
            is_business=False
        )
    except Exception as e:
        logger.error(f"Failed to send rating notification to buyer: {e}")

    return jsonify({'success': True})


# ==================== ADMIN ENDPOINTS ====================

@coupon_bp.route('/api/admin/feature-flags', methods=['GET'])
@jwt_admin_required
def get_feature_flags():
    """Get all feature flags (admin only)"""
    flags = FeatureFlag.query.all()
    return jsonify({
        'flags': [{
            'id': f.id,
            'key': f.key,
            'value': f.value,
            'description': f.description,
            'updated_at': f.updated_at.isoformat() if f.updated_at else None
        } for f in flags]
    })


@coupon_bp.route('/api/admin/feature-flags/<key>', methods=['PUT'])
@jwt_admin_required
def update_feature_flag(key):
    """Update a feature flag (admin only)"""
    data = request.get_json()
    value = data.get('value')

    if value is None:
        return jsonify({'error': 'Value is required'}), 400

    flag = FeatureFlag.set_flag(key, value)

    return jsonify({
        'success': True,
        'flag': {
            'key': flag.key,
            'value': flag.value
        }
    })


@coupon_bp.route('/api/admin/businesses/with-coupons', methods=['GET'])
@jwt_admin_required
def get_businesses_with_coupons():
    """Get all businesses that can have exclusive coupons (admin only)"""
    businesses = Business.query.filter(
        Business.has_exclusive_coupons == True
    ).order_by(Business.name).all()

    result = []
    for b in businesses:
        result.append({
            'id': b.id,
            'name': b.name,
            'city': b.city,
            'business_type': b.business_type,
            'max_campaigns_allowed': b.max_campaigns_allowed,
            'campaigns_count': b.get_campaigns_count(),
            'active_coupons': b.get_active_coupons_count(),
            'average_rating': b.average_rating,
            'total_reviews': b.total_reviews,
            'working_hours': b.working_hours,
            'is_open': b.is_open_now()
        })

    return jsonify({'businesses': result})


@coupon_bp.route('/api/admin/businesses/<int:business_id>/enable-coupons', methods=['POST'])
@jwt_admin_required
def enable_business_coupons(business_id):
    """Enable exclusive coupons for a business (admin only)"""
    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json() or {}

    business.has_exclusive_coupons = True
    business.business_type = data.get('business_type', 'local_business')
    business.max_campaigns_allowed = data.get('max_campaigns_allowed', 1)

    if 'description' in data:
        business.description = data['description']
    if 'address' in data:
        business.address = data['address']
    if 'working_hours' in data:
        business.working_hours = data['working_hours']

    db.session.commit()

    return jsonify({'success': True})


@coupon_bp.route('/api/admin/businesses/<int:business_id>/disable-coupons', methods=['POST'])
@jwt_admin_required
def disable_business_coupons(business_id):
    """Disable exclusive coupons for a business (admin only)"""
    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    business.has_exclusive_coupons = False
    db.session.commit()

    return jsonify({'success': True})


@coupon_bp.route('/api/admin/coupons/stats', methods=['GET'])
@jwt_admin_required
def get_coupon_stats():
    """Get overall coupon statistics (admin only)"""
    from sqlalchemy import func

    total_coupons = Coupon.query.count()
    active_coupons = Coupon.query.filter(Coupon.is_active == True, Coupon.remaining_quantity > 0).count()
    total_sold = db.session.query(func.sum(Coupon.total_quantity - Coupon.remaining_quantity)).scalar() or 0
    total_redeemed = UserCoupon.query.filter(UserCoupon.status == 'redeemed').count()
    total_expired = UserCoupon.query.filter(UserCoupon.status == 'expired').count()

    # Calculate total credits spent on coupons
    total_credits = db.session.query(
        func.sum(Coupon.credits_cost)
    ).join(UserCoupon).filter(UserCoupon.coupon_id == Coupon.id).scalar() or 0

    return jsonify({
        'stats': {
            'total_coupons': total_coupons,
            'active_coupons': active_coupons,
            'total_sold': int(total_sold),
            'total_redeemed': total_redeemed,
            'total_expired': total_expired,
            'redemption_rate': round(total_redeemed / total_sold * 100, 1) if total_sold > 0 else 0,
            'total_credits_spent': int(total_credits)
        }
    })


@coupon_bp.route('/api/admin/all-coupons', methods=['GET'])
@jwt_admin_required
def get_all_coupons_admin():
    """Get all coupons for admin view"""
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()

    result = []
    for coupon in coupons:
        result.append({
            'id': coupon.id,
            'article_name': coupon.article_name,
            'discount_percent': coupon.discount_percent,
            'normal_price': coupon.normal_price,
            'final_price': coupon.final_price,
            'total_quantity': coupon.total_quantity,
            'remaining_quantity': coupon.remaining_quantity,
            'valid_days': coupon.valid_days,
            'is_active': coupon.is_active,
            'created_at': coupon.created_at.isoformat(),
            'business': {
                'id': coupon.business.id,
                'name': coupon.business.name
            }
        })

    return jsonify({'coupons': result})


@coupon_bp.route('/api/admin/all-transactions', methods=['GET'])
@jwt_admin_required
def get_all_transactions_admin():
    """Get all coupon transactions for admin view"""
    # Get pagination params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', None)

    query = UserCoupon.query.join(Coupon).join(Business).join(
        User, User.id == UserCoupon.user_id
    )

    if status_filter:
        query = query.filter(UserCoupon.status == status_filter)

    # Order by most recent first
    query = query.order_by(UserCoupon.purchased_at.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    transactions = pagination.items

    result = []
    for uc in transactions:
        result.append({
            'id': uc.id,
            'status': uc.status,
            'redemption_code': uc.redemption_code,
            'purchased_at': uc.purchased_at.isoformat() if uc.purchased_at else None,
            'redeemed_at': uc.redeemed_at.isoformat() if uc.redeemed_at else None,
            'expires_at': uc.expires_at.isoformat() if uc.expires_at else None,
            'credits_spent': uc.credits_spent,
            'user': {
                'id': uc.user.id,
                'email': uc.user.email,
                'display_name': uc.user.display_name
            } if uc.user else None,
            'coupon': {
                'id': uc.coupon.id,
                'article_name': uc.coupon.article_name,
                'discount_percent': uc.coupon.discount_percent,
                'final_price': uc.coupon.final_price
            } if uc.coupon else None,
            'business': {
                'id': uc.coupon.business.id,
                'name': uc.coupon.business.name
            } if uc.coupon and uc.coupon.business else None
        })

    return jsonify({
        'transactions': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@coupon_bp.route('/api/admin/businesses/search', methods=['GET'])
@jwt_admin_required
def search_businesses():
    """Search businesses for coupon assignment (admin only)"""
    search = request.args.get('search', '')

    query = Business.query

    if search:
        query = query.filter(Business.name.ilike(f'%{search}%'))

    businesses = query.order_by(Business.name).limit(20).all()

    return jsonify({
        'businesses': [{
            'id': b.id,
            'name': b.name,
            'city': b.city,
            'slug': b.slug,
            'logo_path': b.logo_path,
            'has_exclusive_coupons': b.has_exclusive_coupons
        } for b in businesses]
    })


@coupon_bp.route('/api/products/for-engagement', methods=['GET'])
@jwt_required
def get_products_for_engagement():
    """Get random products for engagement (earning credits)"""
    current_user = get_jwt_user()
    from models import Product
    from sqlalchemy.sql.expression import func

    limit = request.args.get('limit', 20, type=int)

    # Get random products with images, prioritizing discounted ones
    products = Product.query.filter(
        Product.image_path.isnot(None)
    ).order_by(func.random()).limit(limit).all()

    result = []
    for p in products:
        result.append({
            'id': p.id,
            'title': p.title,
            'base_price': p.base_price,
            'discount_price': p.discount_price,
            'image_url': p.image_path,
            'category': p.category,
            'business': {
                'id': p.business.id,
                'name': p.business.name
            } if p.business else None
        })

    return jsonify({'products': result})


@coupon_bp.route('/api/user/business-membership', methods=['GET'])
@jwt_required
def get_user_business_membership():
    """Get user's business membership for business owner dashboard"""
    current_user = get_jwt_user()
    membership = BusinessMembership.query.filter(
        BusinessMembership.user_id == current_user.id,
        BusinessMembership.is_active == True
    ).first()

    if not membership:
        return jsonify({'business': None})

    business = membership.business

    return jsonify({
        'business': {
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'city': business.city,
            'logo_path': business.logo_path,
            'description': business.description,
            'address': business.address,
            'google_link': business.google_link,
            'working_hours': business.working_hours,
            'is_open': business.is_open_now(),
            'average_rating': business.average_rating,
            'total_reviews': business.total_reviews,
            'max_campaigns_allowed': business.max_campaigns_allowed,
            'campaigns_count': business.get_campaigns_count(),
            'has_exclusive_coupons': business.has_exclusive_coupons
        },
        'role': membership.role
    })


# ==================== STORE MANAGEMENT ENDPOINTS ====================

@coupon_bp.route('/api/business/<int:business_id>/stores', methods=['GET'])
@jwt_required
def get_business_stores(business_id):
    """Get all stores for a business"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    stores = Store.query.filter_by(business_id=business_id, is_active=True).all()
    return jsonify({'stores': [s.to_dict() for s in stores]})


@coupon_bp.route('/api/business/<int:business_id>/stores', methods=['POST'])
@jwt_required
def create_store(business_id):
    """Create a new store for a business"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()

    store = Store(
        business_id=business_id,
        name=data.get('name'),
        address=data.get('address'),
        city=data.get('city', business.city),
        phone=data.get('phone'),
        latitude=data.get('latitude'),
        longitude=data.get('longitude'),
        google_maps_link=data.get('google_maps_link'),
        working_hours=data.get('working_hours'),
        is_primary=data.get('is_primary', False)
    )

    # If this is primary, make sure no other store is primary
    if store.is_primary:
        Store.query.filter_by(business_id=business_id, is_primary=True).update({'is_primary': False})

    db.session.add(store)
    db.session.commit()

    return jsonify({'success': True, 'store': store.to_dict()})


@coupon_bp.route('/api/business/<int:business_id>/stores/<int:store_id>', methods=['PUT'])
@jwt_required
def update_store(business_id, store_id):
    """Update a store"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    store = Store.query.filter_by(id=store_id, business_id=business_id).first()
    if not store:
        return jsonify({'error': 'Store not found'}), 404

    data = request.get_json()

    if 'name' in data:
        store.name = data['name']
    if 'address' in data:
        store.address = data['address']
    if 'city' in data:
        store.city = data['city']
    if 'phone' in data:
        store.phone = data['phone']
    if 'latitude' in data:
        store.latitude = data['latitude']
    if 'longitude' in data:
        store.longitude = data['longitude']
    if 'google_maps_link' in data:
        store.google_maps_link = data['google_maps_link']
    if 'working_hours' in data:
        store.working_hours = data['working_hours']
    if 'is_primary' in data:
        if data['is_primary']:
            Store.query.filter_by(business_id=business_id, is_primary=True).update({'is_primary': False})
        store.is_primary = data['is_primary']

    db.session.commit()
    return jsonify({'success': True, 'store': store.to_dict()})


@coupon_bp.route('/api/business/<int:business_id>/stores/<int:store_id>', methods=['DELETE'])
@jwt_required
def delete_store(business_id, store_id):
    """Delete (deactivate) a store"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    store = Store.query.filter_by(id=store_id, business_id=business_id).first()
    if not store:
        return jsonify({'error': 'Store not found'}), 404

    store.is_active = False
    db.session.commit()

    return jsonify({'success': True})


# ==================== CAMPAIGN MANAGEMENT ENDPOINTS ====================

@coupon_bp.route('/api/business/<int:business_id>/campaigns', methods=['GET'])
@jwt_required
def get_business_campaigns(business_id):
    """Get all campaigns for a business"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    campaigns = Campaign.query.filter_by(business_id=business_id).order_by(Campaign.created_at.desc()).all()

    return jsonify({
        'campaigns': [c.to_dict() for c in campaigns],
        'business': {
            'id': business.id,
            'name': business.name,
            'max_campaigns_allowed': business.max_campaigns_allowed,
            'campaigns_count': business.get_campaigns_count(),
            'can_create_campaign': business.can_create_campaign()
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/campaigns', methods=['POST'])
@jwt_required
def create_campaign(business_id):
    """Create a new campaign for a business"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    if not business.has_exclusive_coupons:
        return jsonify({'error': 'Ekskluzivni kuponi nisu omogućeni za ovaj biznis'}), 400

    # Check campaign limit (admin can bypass)
    if not business.can_create_campaign() and not current_user.is_admin:
        return jsonify({
            'error': f'Maksimalan broj kampanja ({business.max_campaigns_allowed}) je dostignut. Kontaktirajte podršku za više.'
        }), 400

    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Naziv kampanje je obavezan'}), 400

    # Parse dates if provided
    starts_at = None
    expires_at = None
    if data.get('starts_at'):
        try:
            starts_at = datetime.fromisoformat(data['starts_at'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

    # Admin can set custom max_coupons, others get default 20
    max_coupons = 20
    if current_user.is_admin and data.get('max_coupons'):
        max_coupons = min(100, max(1, int(data['max_coupons'])))  # Between 1 and 100

    campaign = Campaign(
        business_id=business_id,
        name=data['name'],
        description=data.get('description'),
        max_coupons=max_coupons,
        starts_at=starts_at,
        expires_at=expires_at,
        is_active=True,
        created_by_user_id=current_user.id
    )

    db.session.add(campaign)
    db.session.commit()

    return jsonify({
        'success': True,
        'campaign': campaign.to_dict()
    })


@coupon_bp.route('/api/business/<int:business_id>/campaigns/<int:campaign_id>', methods=['GET'])
@jwt_required
def get_campaign(business_id, campaign_id):
    """Get a single campaign with its coupons"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    campaign = Campaign.query.filter_by(id=campaign_id, business_id=business_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    # Get coupons for this campaign
    coupons = Coupon.query.filter_by(campaign_id=campaign_id).order_by(Coupon.created_at.desc()).all()

    coupon_list = []
    for coupon in coupons:
        coupon_list.append({
            'id': coupon.id,
            'article_name': coupon.article_name,
            'description': coupon.description,
            'normal_price': coupon.normal_price,
            'discount_percent': coupon.discount_percent,
            'final_price': coupon.final_price,
            'total_quantity': coupon.total_quantity,
            'remaining_quantity': coupon.remaining_quantity,
            'credits_cost': coupon.credits_cost,
            'valid_days': coupon.valid_days,
            'is_active': coupon.is_active,
            'created_at': coupon.created_at.isoformat() if coupon.created_at else None
        })

    return jsonify({
        'campaign': campaign.to_dict(),
        'coupons': coupon_list
    })


@coupon_bp.route('/api/business/<int:business_id>/campaigns/<int:campaign_id>', methods=['PUT'])
@jwt_required
def update_campaign(business_id, campaign_id):
    """Update a campaign"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    campaign = Campaign.query.filter_by(id=campaign_id, business_id=business_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    data = request.get_json()

    if 'name' in data:
        campaign.name = data['name']
    if 'description' in data:
        campaign.description = data['description']
    if 'is_active' in data:
        campaign.is_active = data['is_active']

    # Parse dates if provided
    if 'starts_at' in data:
        if data['starts_at']:
            try:
                campaign.starts_at = datetime.fromisoformat(data['starts_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        else:
            campaign.starts_at = None

    if 'expires_at' in data:
        if data['expires_at']:
            try:
                campaign.expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        else:
            campaign.expires_at = None

    # Only admin can change max_coupons
    if current_user.is_admin and 'max_coupons' in data:
        campaign.max_coupons = min(100, max(1, int(data['max_coupons'])))

    db.session.commit()

    return jsonify({
        'success': True,
        'campaign': campaign.to_dict()
    })


@coupon_bp.route('/api/business/<int:business_id>/campaigns/<int:campaign_id>', methods=['DELETE'])
@jwt_required
def delete_campaign(business_id, campaign_id):
    """Delete (deactivate) a campaign"""
    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    campaign = Campaign.query.filter_by(id=campaign_id, business_id=business_id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    # Deactivate the campaign and all its coupons
    campaign.is_active = False
    Coupon.query.filter_by(campaign_id=campaign_id).update({'is_active': False})

    db.session.commit()

    return jsonify({'success': True})


# Admin endpoint to update business campaign limit
@coupon_bp.route('/api/admin/businesses/<int:business_id>/campaign-limit', methods=['PUT'])
@jwt_admin_required
def update_business_campaign_limit(business_id):
    """Update max campaigns allowed for a business (admin only)"""
    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    max_campaigns = data.get('max_campaigns_allowed', 1)

    business.max_campaigns_allowed = min(50, max(1, int(max_campaigns)))
    db.session.commit()

    return jsonify({
        'success': True,
        'max_campaigns_allowed': business.max_campaigns_allowed
    })


# Admin endpoint to update campaign coupon limit
@coupon_bp.route('/api/admin/campaigns/<int:campaign_id>/coupon-limit', methods=['PUT'])
@jwt_admin_required
def update_campaign_coupon_limit(campaign_id):
    """Update max coupons allowed for a campaign (admin only)"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    data = request.get_json()
    max_coupons = data.get('max_coupons', 20)

    campaign.max_coupons = min(100, max(1, int(max_coupons)))
    db.session.commit()

    return jsonify({
        'success': True,
        'max_coupons': campaign.max_coupons
    })


# ==================== PUBLIC BUSINESS LANDING PAGE ====================

@coupon_bp.route('/api/ekskluzivno/<slug>', methods=['GET'])
def get_business_landing_page(slug):
    """
    Get public business landing page data with active coupons.
    This is for the public-facing business page with FOMO countdown.
    """
    business = Business.query.filter_by(slug=slug).first()
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    if not business.has_exclusive_coupons:
        return jsonify({'error': 'Business does not have exclusive coupons'}), 404

    # Get active coupons for this business
    coupons = Coupon.query.filter(
        Coupon.business_id == business.id,
        Coupon.is_active == True,
        Coupon.remaining_quantity > 0
    ).order_by(Coupon.created_at.desc()).all()

    # Get stores for this business
    stores = Store.query.filter_by(business_id=business.id, is_active=True).all()

    coupon_list = []
    for c in coupons:
        # Calculate expiration for FOMO countdown
        # Use coupon's expires_at if set, otherwise calculate from valid_days
        if c.expires_at:
            countdown_to = c.expires_at
        else:
            # Expiration is based on when coupon was created + valid_days
            countdown_to = c.created_at + timedelta(days=c.valid_days)

        coupon_data = {
            'id': c.id,
            'article_name': c.article_name,
            'description': c.description,
            'normal_price': c.normal_price,
            'discount_percent': c.discount_percent,
            'final_price': c.final_price,
            'savings': c.savings,
            'quantity_description': c.quantity_description,
            'image_path': c.image_path,
            'total_quantity': c.total_quantity,
            'remaining_quantity': c.remaining_quantity,
            'credits_cost': c.credits_cost,
            'valid_days': c.valid_days,
            'expires_at': countdown_to.isoformat() if countdown_to else None,
            'store': c.store.to_dict() if c.store else None
        }
        coupon_list.append(coupon_data)

    return jsonify({
        'business': {
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'description': business.description,
            'category': business.business_type,
            'logo_path': business.logo_path,
            'cover_image_path': business.cover_image_path,
            'city': business.city,
            'address': business.address,
            'phone': business.contact_phone,
            'google_link': business.google_link,
            'working_hours': business.working_hours,
            'is_open': business.is_open_now(),
            'average_rating': business.average_rating,
            'total_reviews': business.total_reviews
        },
        'stores': [s.to_dict() for s in stores],
        'coupons': coupon_list,
        'share': {
            'url': f'https://popust.ba/ekskluzivno/{business.slug}',
            'title': f'{business.name} - Ekskluzivni Popusti',
            'description': f'Registruj se BESPLATNO i preuzmi ekskluzivne popuste do {max([c["discount_percent"] for c in coupon_list])}% u {business.name}!' if coupon_list else f'Otkrij ekskluzivne popuste u {business.name}!'
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/cover-image', methods=['POST'])
@jwt_required
def upload_cover_image(business_id):
    """Upload cover/storefront image for business landing page"""
    import os
    from werkzeug.utils import secure_filename

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, webp'}), 400

    # Create filename and save path
    filename = secure_filename(f"cover_{business_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'business_covers')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Update business cover image path
    business.cover_image_path = f'uploads/business_covers/{filename}'
    db.session.commit()

    return jsonify({
        'success': True,
        'cover_image_path': business.cover_image_path
    })


@coupon_bp.route('/api/coupons/<int:coupon_id>/image', methods=['POST'])
@jwt_required
def upload_coupon_image(coupon_id):
    """Upload image for a coupon"""
    import os
    from werkzeug.utils import secure_filename

    current_user = get_jwt_user()
    coupon = Coupon.query.get(coupon_id)

    if not coupon:
        return jsonify({'error': 'Coupon not found'}), 404

    if not current_user.is_admin and not user_has_business_role(current_user.id, coupon.business_id, 'owner'):
        return jsonify({'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, webp'}), 400

    # Create filename and save path
    filename = secure_filename(f"coupon_{coupon_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'coupon_images')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Update coupon image path
    coupon.image_path = f'uploads/coupon_images/{filename}'
    db.session.commit()

    return jsonify({
        'success': True,
        'image_path': coupon.image_path
    })


# ==================== BUSINESS PRODUCT MANAGEMENT ENDPOINTS ====================

@coupon_bp.route('/api/business/<int:business_id>/products', methods=['GET'])
@jwt_required
def get_business_products(business_id):
    """Get all products for a business (owner/staff only)"""
    from models import Product

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Get pagination params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '').strip()
    show_discounted = request.args.get('discounted', 'all')  # 'all', 'yes', 'no'

    query = Product.query.filter(Product.business_id == business_id)

    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))

    if show_discounted == 'yes':
        query = query.filter(Product.discount_price.isnot(None), Product.discount_price < Product.base_price)
    elif show_discounted == 'no':
        query = query.filter(db.or_(Product.discount_price.is_(None), Product.discount_price >= Product.base_price))

    query = query.order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    products = []
    for p in pagination.items:
        products.append({
            'id': p.id,
            'title': p.title,
            'base_price': p.base_price,
            'discount_price': p.discount_price,
            'has_discount': p.has_discount,
            'expires': p.expires.isoformat() if p.expires else None,
            'category': p.category,
            'category_group': p.category_group,
            'image_path': p.image_path,
            'views': p.views,
            'created_at': p.created_at.isoformat() if p.created_at else None,
            'brand': p.brand,
            'product_type': p.product_type,
            'size_value': p.size_value,
            'size_unit': p.size_unit,
            'variant': p.variant
        })

    return jsonify({
        'products': products,
        'business': {
            'id': business.id,
            'name': business.name
        },
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/products', methods=['POST'])
@jwt_required
def create_business_product(business_id):
    """Create a new product for a business (staff or higher)"""
    from models import Product
    from datetime import date

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Validate required fields
    if not data.get('title'):
        return jsonify({'error': 'Naziv proizvoda je obavezan'}), 400
    if not data.get('base_price') or data['base_price'] <= 0:
        return jsonify({'error': 'Cijena mora biti veća od 0'}), 400

    # Parse expiry date if provided
    expires = None
    if data.get('expires'):
        try:
            expires = date.fromisoformat(data['expires'])
        except ValueError:
            return jsonify({'error': 'Neispravan format datuma isteka'}), 400

    # Validate discount price
    discount_price = data.get('discount_price')
    if discount_price is not None:
        if discount_price <= 0:
            return jsonify({'error': 'Cijena na popustu mora biti veća od 0'}), 400
        if discount_price >= data['base_price']:
            return jsonify({'error': 'Cijena na popustu mora biti manja od osnovne cijene'}), 400

    product = Product(
        business_id=business_id,
        city=business.city,
        title=data['title'],
        base_price=data['base_price'],
        discount_price=discount_price,
        expires=expires,
        category=data.get('category'),
        category_group=data.get('category_group'),
        tags=data.get('tags'),
        enriched_description=data.get('description'),
        brand=data.get('brand'),
        product_type=data.get('product_type'),
        size_value=data.get('size_value'),
        size_unit=data.get('size_unit'),
        variant=data.get('variant')
    )

    db.session.add(product)
    db.session.commit()

    logger.info(f"Product {product.id} created by user {current_user.id} for business {business_id}")

    # Handle image_base64 if provided - upload directly to S3
    image_path = None
    if data.get('image_base64'):
        try:
            import base64
            from image_search import upload_to_s3

            image_data = base64.b64decode(data['image_base64'])
            # Create slugified filename from product title
            title_slug = slugify_title(product.title)
            s3_path = f"popust/business-products/{business_id}/{product.id}-{title_slug}.jpg"
            uploaded_path = upload_to_s3(image_data, s3_path, 'image/jpeg')

            if uploaded_path:
                product.image_path = uploaded_path
                db.session.commit()
                image_path = uploaded_path
                logger.info(f"Product {product.id} image uploaded to S3: {uploaded_path}")
        except Exception as e:
            logger.error(f"Failed to upload image for product {product.id}: {e}")

    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': product.base_price,
            'discount_price': product.discount_price,
            'image_path': image_path
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>', methods=['GET'])
@jwt_required
def get_business_product(business_id, product_id):
    """Get a single product details"""
    from models import Product

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': product.base_price,
            'discount_price': product.discount_price,
            'has_discount': product.has_discount,
            'expires': product.expires.isoformat() if product.expires else None,
            'category': product.category,
            'category_group': product.category_group,
            'image_path': product.image_path,
            'views': product.views,
            'created_at': product.created_at.isoformat() if product.created_at else None
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>', methods=['PUT'])
@jwt_required
def update_business_product(business_id, product_id):
    """Update a product (staff, manager, or owner)"""
    from models import Product, ProductPriceHistory
    from datetime import date

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Capture old prices before update for price history
    old_base_price = product.base_price
    old_discount_price = product.discount_price

    # Update fields if provided
    if 'title' in data:
        if not data['title']:
            return jsonify({'error': 'Naziv proizvoda je obavezan'}), 400
        product.title = data['title']

    if 'base_price' in data:
        if data['base_price'] <= 0:
            return jsonify({'error': 'Cijena mora biti veća od 0'}), 400
        product.base_price = data['base_price']

    if 'discount_price' in data:
        if data['discount_price'] is not None:
            if data['discount_price'] <= 0:
                return jsonify({'error': 'Cijena na popustu mora biti veća od 0'}), 400
            base = data.get('base_price') or product.base_price
            # If discount_price equals base_price, treat as "no discount"
            if data['discount_price'] >= base:
                product.discount_price = None
            else:
                product.discount_price = data['discount_price']
        else:
            product.discount_price = None

    if 'expires' in data:
        if data['expires']:
            try:
                product.expires = date.fromisoformat(data['expires'])
            except ValueError:
                return jsonify({'error': 'Neispravan format datuma isteka'}), 400
        else:
            product.expires = None

    if 'category' in data:
        product.category = data['category']

    if 'category_group' in data:
        product.category_group = data['category_group']

    # Update product meta fields
    if 'brand' in data:
        product.brand = data['brand']
    if 'product_type' in data:
        product.product_type = data['product_type']
    if 'size_value' in data:
        product.size_value = data['size_value']
    if 'size_unit' in data:
        product.size_unit = data['size_unit']
    if 'variant' in data:
        product.variant = data['variant']

    # Record price history if price changed
    price_changed = (product.base_price != old_base_price or product.discount_price != old_discount_price)
    if price_changed:
        price_history = ProductPriceHistory(
            product_id=product.id,
            base_price=product.base_price,
            discount_price=product.discount_price
        )
        db.session.add(price_history)
        logger.info(f"Price history recorded for product {product_id}: base={product.base_price}, discount={product.discount_price}")

    db.session.commit()

    logger.info(f"Product {product_id} updated by user {current_user.id}")

    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': product.base_price,
            'discount_price': product.discount_price
        }
    })


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>', methods=['DELETE'])
@jwt_required
def delete_business_product(business_id, product_id):
    """Delete a product (any business member)"""
    from models import Product

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    product_title = product.title
    db.session.delete(product)
    db.session.commit()

    logger.info(f"Product {product_id} ({product_title}) deleted by user {current_user.id}")

    return jsonify({
        'success': True,
        'message': f'Proizvod "{product_title}" je obrisan'
    })


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>/image', methods=['POST'])
@jwt_required
def upload_business_product_image(business_id, product_id):
    """Upload image for a business product"""
    import os
    from werkzeug.utils import secure_filename
    from models import Product

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, webp'}), 400

    # Create filename and save path
    filename = secure_filename(f"product_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}")
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'product_images')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Keep original image path if not set
    if not product.original_image_path:
        product.original_image_path = product.image_path

    # Update product image path
    product.image_path = f'uploads/product_images/{filename}'
    db.session.commit()

    logger.info(f"Product {product_id} image uploaded by user {current_user.id}")

    return jsonify({
        'success': True,
        'image_path': product.image_path
    })


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>/suggest-images', methods=['GET'])
@jwt_required
def business_product_suggest_images(business_id, product_id):
    """AI-powered image search for a business product"""
    from models import Product
    from image_search import search_duckduckgo_images

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Get attempt number for query variation
    attempt = request.args.get('attempt', 1, type=int)

    # Build search query using product title
    search_query = product.title
    if product.brand and product.brand.lower() != 'unknown':
        search_query = f"{product.brand} {product.title}"

    # Vary the query based on attempt number
    if attempt == 2:
        search_query += " product"
    elif attempt == 3:
        search_query += " packaging"
    elif attempt >= 4:
        search_query = f"{product.title} Bosnia"

    try:
        images = search_duckduckgo_images(search_query, num_results=8)
        logger.info(f"Business product {product_id} image suggestions: found {len(images)} images for query '{search_query}'")
        return jsonify({'images': images})
    except Exception as e:
        logger.error(f"Error searching images for business product {product_id}: {e}")
        return jsonify({'images': [], 'error': str(e)})


@coupon_bp.route('/api/business/<int:business_id>/products/<int:product_id>/set-image', methods=['POST'])
@jwt_required
def business_product_set_image(business_id, product_id):
    """Set product image from a URL - downloads and uploads to S3"""
    from models import Product
    from image_search import upload_to_s3
    import requests as http_requests

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    product = Product.query.filter_by(id=product_id, business_id=business_id).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({'error': 'image_url is required'}), 400

    image_url = data['image_url']

    # Keep original image path if not set
    if not product.original_image_path and product.image_path:
        product.original_image_path = image_url

    # Download image from external URL and upload to S3
    try:
        logger.info(f"Downloading image from {image_url} for product {product_id}")

        # Download the image
        response = http_requests.get(image_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        image_data = response.content

        # Create slugified filename from product title
        title_slug = slugify_title(product.title)
        s3_path = f"popust/business-products/{business_id}/{product_id}-{title_slug}.jpg"

        # Upload to S3
        uploaded_path = upload_to_s3(image_data, s3_path, 'image/jpeg')

        if uploaded_path:
            product.image_path = uploaded_path
            db.session.commit()
            logger.info(f"Business product {product_id} image uploaded to S3: {uploaded_path}")

            return jsonify({
                'success': True,
                'image_path': product.image_path
            })
        else:
            logger.error(f"Failed to upload image to S3 for product {product_id}")
            return jsonify({'error': 'Failed to upload image to S3'}), 500

    except http_requests.RequestException as e:
        logger.error(f"Failed to download image from {image_url}: {e}")
        return jsonify({'error': f'Failed to download image: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Error setting image for product {product_id}: {e}")
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500


@coupon_bp.route('/api/business/<int:business_id>/products/bulk-ai-upload', methods=['POST'])
@jwt_required
def bulk_ai_product_upload(business_id):
    """
    Process multiple product images with AI to extract product data.
    Accepts up to 10 images, resizes them to max 600px, and returns extracted product info.
    """
    import os
    import io
    import base64
    from PIL import Image
    from openai_utils import extract_product_from_image

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400
    if len(files) > 10:
        return jsonify({'error': 'Maximum 10 images allowed'}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
    results = []

    for idx, file in enumerate(files):
        try:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if ext not in allowed_extensions:
                results.append({
                    'index': idx,
                    'filename': file.filename,
                    'success': False,
                    'error': 'Invalid file type'
                })
                continue

            # Read and resize image to max 600px
            img = Image.open(file)

            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize to max 600px while maintaining aspect ratio
            max_size = 600
            if img.width > max_size or img.height > max_size:
                if img.width > img.height:
                    new_width = max_size
                    new_height = int((max_size / img.width) * img.height)
                else:
                    new_height = max_size
                    new_width = int((max_size / img.height) * img.width)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

            # Extract product info using AI
            extracted_data = extract_product_from_image(image_base64)

            results.append({
                'index': idx,
                'filename': file.filename,
                'success': True,
                'data': extracted_data,
                'image_base64': image_base64
            })

        except Exception as e:
            logger.error(f"Error processing image {file.filename}: {e}")
            results.append({
                'index': idx,
                'filename': file.filename,
                'success': False,
                'error': str(e)
            })

    logger.info(f"Bulk AI upload for business {business_id}: processed {len(files)} images")

    return jsonify({
        'success': True,
        'results': results,
        'processed': len([r for r in results if r.get('success')]),
        'failed': len([r for r in results if not r.get('success')])
    })


@coupon_bp.route('/api/business/<int:business_id>/subscriber-count', methods=['GET'])
@jwt_required
def get_business_subscriber_count(business_id):
    """Get subscriber count and growth data for a business"""
    from models import User, UserActivity
    from sqlalchemy import func, text
    from datetime import datetime, timedelta

    current_user = get_jwt_user()
    if not current_user.is_admin and not user_has_business_role(current_user.id, business_id, 'staff'):
        return jsonify({'error': 'Unauthorized'}), 403

    business = Business.query.get(business_id)
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Count current subscribers using PostgreSQL JSON containment (cast to jsonb)
    current_count = db.session.query(func.count(User.id)).filter(
        User.preferences.isnot(None),
        text(f"(preferences::jsonb)->'preferred_stores' @> '[{business_id}]'::jsonb")
    ).scalar() or 0

    # Get growth data from activity logs (store_follow events) for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)

    daily_follows = db.session.query(
        func.date(UserActivity.created_at).label('date'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.activity_type == 'store_follow',
        UserActivity.activity_data.op('->>')('business_id') == str(business_id),
        UserActivity.created_at >= thirty_days_ago
    ).group_by(
        func.date(UserActivity.created_at)
    ).order_by(
        func.date(UserActivity.created_at)
    ).all()

    # Build growth data array with all dates
    growth_data = []
    current_date = thirty_days_ago.date()
    today = datetime.now().date()
    follow_dict = {str(row.date): row.count for row in daily_follows}

    # Calculate cumulative - start with estimated base
    total_recorded = sum(follow_dict.values())
    base = max(0, current_count - total_recorded)
    cumulative = base

    while current_date <= today:
        date_str = str(current_date)
        new_follows = follow_dict.get(date_str, 0)
        cumulative += new_follows
        growth_data.append({
            'date': date_str,
            'total': cumulative,
            'new': new_follows
        })
        current_date += timedelta(days=1)

    return jsonify({
        'success': True,
        'subscriber_count': current_count,
        'growth_data': growth_data
    })
