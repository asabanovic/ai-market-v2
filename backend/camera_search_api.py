"""
Camera Search API - Snap a product photo to find it in the database
"""
from flask import Blueprint, jsonify, request
import base64
import logging
from auth_api import require_jwt_auth
from openai_utils import openai_client
from image_search import upload_to_s3
from datetime import datetime
import json
import threading
import time

camera_search_bp = Blueprint('camera_search', __name__, url_prefix='/api/camera')

logger = logging.getLogger(__name__)


def log_camera_search_background(user_id: int, image_base64: str, vision_result: dict, product_results: list):
    """Background task to upload image to S3 and log search - doesn't block response"""
    from flask import current_app
    from models import db, SearchLog

    try:
        # Import app for application context
        from app import app

        with app.app_context():
            # Upload image to S3
            image_s3_path = None
            try:
                image_bytes = base64.b64decode(image_base64)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_path = f"popust/camera-searches/{user_id}/{timestamp}.jpg"
                image_s3_path = upload_to_s3(image_bytes, s3_path, 'image/jpeg')
                if image_s3_path:
                    logger.info(f"Camera search image uploaded to S3: {image_s3_path}")
            except Exception as e:
                logger.error(f"Failed to upload camera search image to S3: {e}")

            # Log to SearchLog
            try:
                search_query = vision_result.get('title') or ' '.join(vision_result.get('search_terms', []))
                search_log = SearchLog(
                    query=search_query[:500] if search_query else 'camera_search',
                    user_id=user_id,
                    search_type='camera',
                    image_path=image_s3_path,
                    vision_result=vision_result,
                    result_count=len(product_results),
                    results_detail=[{
                        'product_id': p['id'],
                        'title': p['title'],
                        'price': p.get('discount_price') or p.get('base_price'),
                        'store_name': p['business']['name'] if p.get('business') else None
                    } for p in product_results[:10]]
                )
                db.session.add(search_log)
                db.session.commit()
                logger.info(f"Camera search logged for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to log camera search: {e}")
                db.session.rollback()
    except Exception as e:
        logger.error(f"Background camera search logging failed: {e}")


def analyze_product_image(image_base64: str) -> dict:
    """Use GPT-4o Vision to extract product info from image"""

    system_prompt = """You are a product identification expert for Bosnian supermarkets.
Analyze this product image and extract:
- Product name/title (MUST be in Bosnian language - use Bosnian spelling, NOT Serbian or Croatian)
- Brand name
- Product type/category
- Size/weight if visible
- Any distinguishing features

IMPORTANT: All text output MUST be in Bosnian language. Use Bosnian-specific terms:
- Use "hljeb" not "hleb" (Serbian) or "kruh" (Croatian)
- Use "mlijeko" not "mleko" (Serbian)
- Use "sedmica" not "nedelja" (Serbian) or "tjedan" (Croatian)
- Use "kahva/kafa" for coffee
- Use "čokolada", "sok", "jogurt", "maslac", "sir", "jaja", etc.

Return JSON format:
{
    "title": "full product name with brand and size in Bosnian",
    "brand": "brand name or null",
    "product_type": "category in Bosnian like mlijeko, čokolada, sok, etc.",
    "size_value": "numeric size or null",
    "size_unit": "g, kg, ml, L, kom, etc. or null",
    "search_terms": ["array", "of", "Bosnian", "search", "keywords"],
    "confidence": "high" | "medium" | "low"
}

Be specific with search_terms - include brand variations, common misspellings, and related Bosnian terms.
For products, include both Latin script and common Bosnian names."""

    try:
        api_start = time.time()
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using mini for faster response
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
        api_time = time.time() - api_start
        logger.info(f"[TIMING] Vision API call took {api_time:.2f}s")

        content = response.choices[0].message.content
        if not content:
            logger.warning("Vision API returned empty content")
            return {
                "title": None,
                "brand": None,
                "product_type": None,
                "search_terms": [],
                "confidence": "low",
                "error": "Empty response from Vision API"
            }

        content = content.strip()

        # Clean markdown if present
        if content.startswith("```"):
            parts = content.split("```")
            # Take the content between first ``` and second ```
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

        # Check for empty content after cleaning
        if not content:
            logger.warning(f"Vision API content empty after cleaning. Raw: {response.choices[0].message.content[:200]}")
            return {
                "title": None,
                "brand": None,
                "product_type": None,
                "search_terms": [],
                "confidence": "low",
                "error": "Could not parse Vision API response"
            }

        return json.loads(content)

    except json.JSONDecodeError as e:
        raw_content = response.choices[0].message.content[:500] if response and response.choices else "N/A"
        logger.error(f"Vision API JSON parse error: {e}. Raw content: {raw_content}")
        return {
            "title": None,
            "brand": None,
            "product_type": None,
            "search_terms": [],
            "confidence": "low",
            "error": f"JSON parse error: {str(e)}"
        }
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
    """Search products using semantic search (same as homepage) for better results"""
    from agent_search import run_agent_search, format_agent_products

    # Build search query from vision result
    title = vision_result.get('title', '')
    brand = vision_result.get('brand', '')

    # Combine title and brand for better search
    search_query = title
    if brand and brand.lower() not in title.lower():
        search_query = f"{brand} {title}"

    if not search_query or not search_query.strip():
        return []

    logger.info(f"[TIMING] Camera semantic search query: {search_query}")

    # Use the same agent search as homepage for semantic matching
    agent_result = run_agent_search(
        query=search_query,
        k=limit,
    )

    # Format products to match expected structure
    raw_products = agent_result.get("products", [])
    formatted_products = format_agent_products(raw_products)

    # Transform for ProductCardMobile compatibility (add image_path, has_discount)
    for p in formatted_products:
        # ProductCardMobile expects image_path, agent_search returns image_url
        if 'image_url' in p and 'image_path' not in p:
            p['image_path'] = p['image_url']
        # Add has_discount flag
        if 'has_discount' not in p:
            p['has_discount'] = bool(
                p.get('discount_price') and
                p.get('base_price') and
                p['discount_price'] < p['base_price']
            )

    return formatted_products


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
    # The JWT stores the user's id directly, not telegram_id
    current_user = User.query.get(request.current_user_id)
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    try:
        total_start = time.time()

        # Get image data
        image_base64 = None
        image_size_kb = 0

        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400

            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No image selected'}), 400

            # Read and encode
            image_data = file.read()
            image_size_kb = len(image_data) / 1024
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
            image_size_kb = len(base64.b64decode(image_base64)) / 1024

        # Analyze image with Vision API
        logger.info(f"[TIMING] Camera search START for user {current_user.id}, image size: {image_size_kb:.1f}KB")
        vision_result = analyze_product_image(image_base64)

        if vision_result.get('error'):
            return jsonify({
                'error': 'Could not analyze image',
                'details': vision_result.get('error')
            }), 400

        # Search products using semantic search (same as homepage)
        db_start = time.time()
        user_city = current_user.city if current_user else None
        product_results = search_products_by_vision_result(vision_result, user_city)
        db_time = time.time() - db_start
        logger.info(f"[TIMING] Semantic search took {db_time:.2f}s, found {len(product_results)} products")

        # Log search and upload image in background thread (non-blocking for faster response)
        thread = threading.Thread(
            target=log_camera_search_background,
            args=(current_user.id, image_base64, vision_result, product_results)
        )
        thread.daemon = True
        thread.start()

        # Auto-add to tracked products if product identified with high confidence
        interest_added = False
        already_tracked = False
        if vision_result.get('confidence') in ['high', 'medium'] and vision_result.get('title'):
            # Check if tracked product already exists
            search_term = vision_result.get('title', '')[:100]
            existing = UserTrackedProduct.query.filter_by(
                user_id=current_user.id,
                search_term=search_term
            ).first()

            if existing:
                already_tracked = True
                logger.info(f"Camera tracked product '{search_term}' already exists for user {current_user.id}")
            elif search_term:
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

        total_time = time.time() - total_start
        logger.info(f"[TIMING] Camera search COMPLETE for user {current_user.id} - TOTAL: {total_time:.2f}s, results: {len(product_results)}")

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
            'already_tracked': already_tracked,
            'search_terms': vision_result.get('search_terms', []),
            'timing': {
                'total_seconds': round(total_time, 2)
            }
        })

    except Exception as e:
        logger.error(f"Camera search error: {e}", exc_info=True)
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500
