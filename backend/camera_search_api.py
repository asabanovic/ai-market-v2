"""
Camera Search API - Snap a product photo to find it in the database
"""
from flask import Blueprint, jsonify, request
import base64
import logging
from auth_api import require_jwt_auth
from openai_utils import openai_client
import json

camera_search_bp = Blueprint('camera_search', __name__, url_prefix='/api/camera')

logger = logging.getLogger(__name__)


def analyze_product_image(image_base64: str) -> dict:
    """Use GPT-4o Vision to extract product info from image"""

    system_prompt = """You are a product identification expert for Bosnian supermarkets.
Analyze this product image and extract:
- Product name/title (in Bosnian if possible)
- Brand name
- Product type/category
- Size/weight if visible
- Any distinguishing features

Return JSON format:
{
    "title": "full product name with brand and size",
    "brand": "brand name or null",
    "product_type": "category like mlijeko, čokolada, sok, etc.",
    "size_value": "numeric size or null",
    "size_unit": "g, kg, ml, L, kom, etc. or null",
    "search_terms": ["array", "of", "search", "keywords"],
    "confidence": "high" | "medium" | "low"
}

Be specific with search_terms - include brand variations, common misspellings, and related terms.
For Bosnian products, include both Latin and local names."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify this product for supermarket search."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low"  # Fast processing
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # Clean markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        return json.loads(content)

    except Exception as e:
        logger.error(f"Vision API error: {e}")
        return {
            "title": None,
            "brand": None,
            "product_type": None,
            "search_terms": [],
            "confidence": "low",
            "error": str(e)
        }


def search_products_by_vision_result(vision_result: dict, user_city: str = None, limit: int = 10):
    """Search products database using vision analysis results"""
    from models import Product, Business
    from sqlalchemy import or_, func

    search_terms = vision_result.get('search_terms', [])
    title = vision_result.get('title', '')
    brand = vision_result.get('brand', '')
    product_type = vision_result.get('product_type', '')

    # Build search query
    if title:
        search_terms.append(title)
    if brand:
        search_terms.append(brand)
    if product_type:
        search_terms.append(product_type)

    if not search_terms:
        return []

    # Create search conditions
    conditions = []
    for term in search_terms[:5]:  # Limit to 5 terms for performance
        term_lower = term.lower().strip()
        if len(term_lower) >= 2:
            conditions.append(func.lower(Product.title).contains(term_lower))
            conditions.append(func.lower(Product.brand).contains(term_lower))

    if not conditions:
        return []

    # Query products
    query = Product.query.join(Business).filter(
        Business.status == 'active',
        or_(*conditions)
    )

    # Filter by city if provided
    if user_city:
        query = query.filter(Business.city == user_city)

    # Order by discount availability
    products = query.order_by(
        Product.discount_price.isnot(None).desc(),
        Product.id.desc()
    ).limit(limit).all()

    return products


@camera_search_bp.route('/search', methods=['POST'])
@require_jwt_auth
def camera_search():
    """
    Search for products using a camera photo

    Expected: multipart/form-data with 'image' file
    Or: JSON with 'image_base64' field
    """
    from models import db, UserTrackedProduct, User

    # Get current user from request (set by require_jwt_auth decorator)
    current_user = User.query.filter_by(telegram_id=request.current_user_id).first()
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    try:
        # Get image data
        image_base64 = None

        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400

            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400

            # Read and encode
            image_data = file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        else:
            # Handle JSON with base64
            data = request.get_json()
            if not data or 'image_base64' not in data:
                return jsonify({'error': 'No image data provided'}), 400

            image_base64 = data['image_base64']
            # Remove data URL prefix if present
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

        # Analyze image with Vision API
        logger.info(f"Camera search for user {current_user.id}")
        vision_result = analyze_product_image(image_base64)

        if vision_result.get('error'):
            return jsonify({
                'error': 'Could not analyze image',
                'details': vision_result.get('error')
            }), 400

        # Search products
        user_city = current_user.city if current_user else None
        products = search_products_by_vision_result(vision_result, user_city)

        # Format results
        product_results = []
        for p in products:
            product_results.append({
                'id': p.id,
                'title': p.title,
                'brand': p.brand,
                'base_price': float(p.base_price) if p.base_price else None,
                'discount_price': float(p.discount_price) if p.discount_price else None,
                'image_path': p.image_path,
                'has_discount': p.discount_price and p.base_price and p.discount_price < p.base_price,
                'business': {
                    'id': p.business_id,
                    'name': p.business.name if p.business else 'Nepoznat'
                }
            })

        # Auto-add to tracked products if product identified with high confidence
        interest_added = False
        if vision_result.get('confidence') in ['high', 'medium'] and vision_result.get('title'):
            # Check if tracked product already exists
            search_term = vision_result.get('title', '')[:100]
            existing = UserTrackedProduct.query.filter_by(
                user_id=current_user.id,
                search_term=search_term
            ).first()

            if not existing and search_term:
                new_tracked = UserTrackedProduct(
                    user_id=current_user.id,
                    search_term=search_term,
                    original_text=vision_result.get('title'),
                    source='camera_scan',
                    is_active=True
                )
                db.session.add(new_tracked)
                db.session.commit()
                interest_added = True
                logger.info(f"Added camera tracked product '{search_term}' for user {current_user.id}")

        return jsonify({
            'success': True,
            'identified_product': {
                'title': vision_result.get('title'),
                'brand': vision_result.get('brand'),
                'product_type': vision_result.get('product_type'),
                'confidence': vision_result.get('confidence')
            },
            'products': product_results,
            'interest_added': interest_added,
            'search_terms': vision_result.get('search_terms', [])
        })

    except Exception as e:
        logger.error(f"Camera search error: {e}", exc_info=True)
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500
