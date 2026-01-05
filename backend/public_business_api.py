"""
Public Business API - Public endpoints for viewing business information
No authentication required for basic info
"""
from flask import Blueprint, jsonify, request
import logging

public_business_bp = Blueprint('public_business', __name__, url_prefix='/api/prodavnica')

logger = logging.getLogger(__name__)


@public_business_bp.route('/<slug>', methods=['GET'])
def get_business_by_slug(slug):
    """
    Get public business information by slug
    No authentication required - returns only public info
    """
    from models import Business, Product

    business = Business.query.filter_by(slug=slug, status='active').first()
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Public business info (no auth required)
    business_info = {
        'id': business.id,
        'name': business.name,
        'slug': business.slug,
        'city': business.city,
        'address': business.address,
        'contact_phone': business.contact_phone,
        'description': business.description,
        'logo_path': business.logo_path,
        'cover_image_path': business.cover_image_path,
        'working_hours': business.working_hours,
        'google_link': business.google_link,
        'average_rating': business.average_rating,
        'total_reviews': business.total_reviews,
        'product_count': Product.query.filter_by(business_id=business.id).count()
    }

    return jsonify({'business': business_info})


@public_business_bp.route('/<slug>/products', methods=['GET'])
def get_business_products(slug):
    """
    Get business products - requires authentication
    """
    from auth_api import decode_jwt_token
    from models import Business, Product, User

    # Check authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({
            'error': 'Authentication required',
            'message': 'Registrujte se da vidite proizvode'
        }), 401

    try:
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid token',
                'message': 'Prijavite se ponovo'
            }), 401

        user_id = payload.get('user_id')
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401

    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({
            'error': 'Authentication failed',
            'message': 'Prijavite se da vidite proizvode'
        }), 401

    # Get business
    business = Business.query.filter_by(slug=slug, status='active').first()
    if not business:
        return jsonify({'error': 'Business not found'}), 404

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    search = request.args.get('search', '').strip()

    # Query products
    query = Product.query.filter_by(business_id=business.id)

    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))

    query = query.order_by(Product.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    products = [{
        'id': p.id,
        'title': p.title,
        'brand': p.brand,
        'product_type': p.product_type,
        'size_value': p.size_value,
        'size_unit': p.size_unit,
        'base_price': float(p.base_price) if p.base_price else 0,
        'discount_price': float(p.discount_price) if p.discount_price else None,
        'image_path': p.image_path,
        'has_discount': p.discount_price and p.base_price and p.discount_price < p.base_price,
        'business': {
            'id': business.id,
            'name': business.name
        }
    } for p in pagination.items]

    return jsonify({
        'products': products,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })
