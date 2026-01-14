"""
User Organization API - Endpoints for business members to manage their organization
Uses JWT authentication
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from datetime import datetime
import os
import uuid
from PIL import Image
import io

organization_bp = Blueprint('organization', __name__, url_prefix='/api/my-organization')

logger = logging.getLogger(__name__)


def jwt_auth_required(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token
        from models import User

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


def get_user_business(user):
    """Get the business associated with a user (if any)"""
    from models import BusinessMembership

    membership = BusinessMembership.query.filter_by(
        user_id=user.id,
        is_active=True
    ).first()

    if not membership:
        return None, None

    return membership.business, membership.role


@organization_bp.route('', methods=['GET'])
@jwt_auth_required
def get_my_organization():
    """
    Get the user's organization (business) info
    Returns business details if user is a member of one
    """
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({
            'has_organization': False,
            'organization': None
        })

    from models import Product

    # Get product count
    product_count = Product.query.filter_by(business_id=business.id).count()

    return jsonify({
        'has_organization': True,
        'organization': {
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'city': business.city,
            'logo_path': business.logo_path,
            'status': business.status,
            'product_count': product_count
        },
        'user_role': role
    })


@organization_bp.route('/products', methods=['GET'])
@jwt_auth_required
def get_organization_products():
    """
    Get products for the user's organization with pagination
    Query params:
    - page: page number (default 1)
    - per_page: items per page (default 30)
    - search: optional search term
    - has_discount: filter by discount status
    """
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    from models import Product

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    search = request.args.get('search', '').strip()
    has_discount = request.args.get('has_discount')

    query = Product.query.filter_by(business_id=business.id)

    if search:
        query = query.filter(Product.title.ilike(f'%{search}%'))

    if has_discount == 'true':
        query = query.filter(
            Product.discount_price.isnot(None),
            Product.discount_price < Product.base_price
        )
    elif has_discount == 'false':
        query = query.filter(
            (Product.discount_price.is_(None)) |
            (Product.discount_price >= Product.base_price)
        )

    query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    products = [{
        'id': p.id,
        'title': p.title,
        'base_price': float(p.base_price) if p.base_price else None,
        'discount_price': float(p.discount_price) if p.discount_price else None,
        'category': p.category,
        'category_group': p.category_group,
        'image_path': p.image_path,
        'brand': p.brand,
        'size_value': p.size_value,
        'size_unit': p.size_unit,
        'discount_starts': p.discount_starts.isoformat() if p.discount_starts else None,
        'expires': p.expires.isoformat() if p.expires else None,
        'has_discount': p.has_discount,
        'discount_percentage': p.discount_percentage,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in pagination.items]

    return jsonify({
        'products': products,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'business': {
            'id': business.id,
            'name': business.name
        }
    })


@organization_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_auth_required
def get_organization_product(product_id):
    """Get a single product details"""
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    from models import Product, ProductPriceHistory

    product = Product.query.filter_by(id=product_id, business_id=business.id).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Get price history
    price_history = ProductPriceHistory.query.filter_by(
        product_id=product_id
    ).order_by(ProductPriceHistory.recorded_at.desc()).limit(10).all()

    return jsonify({
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': float(product.base_price) if product.base_price else None,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'category': product.category,
            'category_group': product.category_group,
            'image_path': product.image_path,
            'original_image_path': product.original_image_path,
            'suggested_images': product.suggested_images,
            'brand': product.brand,
            'product_type': product.product_type,
            'size_value': product.size_value,
            'size_unit': product.size_unit,
            'variant': product.variant,
            'discount_starts': product.discount_starts.isoformat() if product.discount_starts else None,
            'expires': product.expires.isoformat() if product.expires else None,
            'tags': product.tags,
            'product_metadata': product.product_metadata,
            'enriched_description': product.enriched_description,
            'created_at': product.created_at.isoformat() if product.created_at else None
        },
        'price_history': [{
            'base_price': float(h.base_price) if h.base_price else None,
            'discount_price': float(h.discount_price) if h.discount_price else None,
            'recorded_at': h.recorded_at.isoformat() if h.recorded_at else None
        } for h in price_history]
    })


@organization_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_auth_required
def update_organization_product(product_id):
    """
    Update a product
    Records price history if price changed
    If only discount_price is set without base_price, copies discount to base
    """
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    from models import db, Product, ProductPriceHistory

    product = Product.query.filter_by(id=product_id, business_id=business.id).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    # Track if price changed for history
    old_base_price = product.base_price
    old_discount_price = product.discount_price
    price_changed = False

    # Update fields
    if 'title' in data:
        product.title = data['title']

    if 'base_price' in data:
        new_base = float(data['base_price']) if data['base_price'] else None
        if new_base != old_base_price:
            price_changed = True
        product.base_price = new_base

    if 'discount_price' in data:
        new_discount = float(data['discount_price']) if data['discount_price'] else None
        if new_discount != old_discount_price:
            price_changed = True
        product.discount_price = new_discount

    # If only discount_price provided without base_price, copy discount to base
    if product.discount_price and not product.base_price:
        product.base_price = product.discount_price
        price_changed = True

    if 'category' in data:
        product.category = data['category']

    if 'category_group' in data:
        product.category_group = data['category_group']

    if 'brand' in data:
        product.brand = data['brand']

    if 'product_type' in data:
        product.product_type = data['product_type']

    if 'size_value' in data:
        product.size_value = float(data['size_value']) if data['size_value'] else None

    if 'size_unit' in data:
        product.size_unit = data['size_unit']

    if 'expires' in data:
        if data['expires']:
            try:
                product.expires = datetime.fromisoformat(data['expires'].replace('Z', '+00:00'))
            except:
                pass
        else:
            product.expires = None

    if 'discount_starts' in data:
        if data['discount_starts']:
            try:
                product.discount_starts = datetime.fromisoformat(data['discount_starts'].replace('Z', '+00:00')).date()
            except:
                pass
        else:
            product.discount_starts = None

    if 'image_path' in data:
        product.image_path = data['image_path']

    # Record price history if price changed
    if price_changed:
        history = ProductPriceHistory(
            product_id=product.id,
            base_price=product.base_price,
            discount_price=product.discount_price,
            recorded_at=datetime.now()
        )
        db.session.add(history)

    # Update match key for product matching
    product.update_match_key()

    db.session.commit()

    logger.info(f"Product {product_id} updated by user {user.email}")

    return jsonify({
        'success': True,
        'message': 'Product updated successfully',
        'price_history_recorded': price_changed,
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': float(product.base_price) if product.base_price else None,
            'discount_price': float(product.discount_price) if product.discount_price else None
        }
    })


@organization_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_auth_required
def delete_organization_product(product_id):
    """Delete a product"""
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    # Only manager or owner can delete
    if role == 'staff':
        return jsonify({'error': 'Only managers and owners can delete products'}), 403

    from models import db, Product

    product = Product.query.filter_by(id=product_id, business_id=business.id).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    product_title = product.title
    db.session.delete(product)
    db.session.commit()

    logger.info(f"Product {product_id} ({product_title}) deleted by user {user.email}")

    return jsonify({
        'success': True,
        'message': f'Product "{product_title}" deleted successfully'
    })


@organization_bp.route('/products', methods=['POST'])
@jwt_auth_required
def create_organization_product():
    """
    Create a new product manually
    """
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    from models import db, Product

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400

    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    base_price = float(data.get('base_price', 0)) if data.get('base_price') else None
    discount_price = float(data.get('discount_price')) if data.get('discount_price') else None

    # If only discount_price, copy to base_price
    if discount_price and not base_price:
        base_price = discount_price

    product = Product(
        business_id=business.id,
        title=title,
        base_price=base_price,
        discount_price=discount_price,
        category=data.get('category'),
        category_group=data.get('category_group'),
        brand=data.get('brand'),
        product_type=data.get('product_type'),
        size_value=float(data.get('size_value')) if data.get('size_value') else None,
        size_unit=data.get('size_unit'),
        image_path=data.get('image_path'),
        city=business.city or 'Tuzla',
        created_at=datetime.now()
    )

    db.session.add(product)
    db.session.commit()

    # Update match key
    product.update_match_key()
    db.session.commit()

    logger.info(f"Product created: {product.title} by user {user.email}")

    return jsonify({
        'success': True,
        'message': 'Product created successfully',
        'product': {
            'id': product.id,
            'title': product.title,
            'base_price': float(product.base_price) if product.base_price else None,
            'discount_price': float(product.discount_price) if product.discount_price else None
        }
    }), 201


@organization_bp.route('/upload-images', methods=['POST'])
@jwt_auth_required
def upload_product_images():
    """
    Bulk upload product images for LLM processing
    Accepts multiple image files, processes them, and returns extracted product info
    """
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400

    files = request.files.getlist('images')

    if not files or len(files) == 0:
        return jsonify({'error': 'No images provided'}), 400

    # Limit batch size
    max_files = 10
    if len(files) > max_files:
        return jsonify({'error': f'Maximum {max_files} images per upload'}), 400

    results = []
    errors = []

    for file in files:
        if not file.filename:
            continue

        try:
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

            if ext not in allowed_extensions:
                errors.append({
                    'filename': file.filename,
                    'error': 'Invalid file type'
                })
                continue

            # Read and validate image
            image_data = file.read()

            if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
                errors.append({
                    'filename': file.filename,
                    'error': 'File too large (max 10MB)'
                })
                continue

            # Process image with PIL
            try:
                img = Image.open(io.BytesIO(image_data))

                # Convert RGBA to RGB if needed
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resize if too large
                max_dim = 2048
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

                # Save to buffer
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                processed_data = buffer.read()

            except Exception as e:
                errors.append({
                    'filename': file.filename,
                    'error': f'Invalid image: {str(e)}'
                })
                continue

            # Upload to S3
            from s3_utils import upload_to_s3
            import base64

            unique_filename = f"{uuid.uuid4()}.jpg"
            s3_path = f"assets/images/product_images/{business.id}/uploads/{unique_filename}"

            s3_url = upload_to_s3(processed_data, s3_path, content_type='image/jpeg')

            if not s3_url:
                errors.append({
                    'filename': file.filename,
                    'error': 'Failed to upload to storage'
                })
                continue

            # Process with LLM to extract product info
            product_info = process_image_with_llm(processed_data, file.filename)

            results.append({
                'filename': file.filename,
                'image_url': s3_url,
                'extracted_info': product_info
            })

        except Exception as e:
            logger.error(f"Error processing image {file.filename}: {e}", exc_info=True)
            errors.append({
                'filename': file.filename,
                'error': str(e)
            })

    return jsonify({
        'success': True,
        'processed': len(results),
        'errors': len(errors),
        'results': results,
        'error_details': errors
    })


def process_image_with_llm(image_data, filename):
    """
    Process an image with LLM to extract product information
    """
    import base64
    from openai import OpenAI

    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        # Encode image as base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a product information extractor. Analyze the product image and extract:
- title: Product name/title in Bosnian language
- brand: Brand name if visible
- category: Product category (e.g., "Mlijeko i mliječni proizvodi", "Voće i povrće", "Meso", "Pića", "Slatkiši", etc.)
- category_group: Simplified category (e.g., "hrana", "piće", "kućanstvo")
- base_price: Price if visible (number only, in KM)
- discount_price: Sale price if visible (number only, in KM)
- size_value: Size/weight value if visible (number only)
- size_unit: Size unit (kg, g, l, ml, kom)
- product_type: Normalized product type

Return JSON only, no markdown. Use null for missing values."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract product information from this image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        import json

        # Clean up response if wrapped in markdown
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        product_info = json.loads(result_text)

        return product_info

    except Exception as e:
        logger.error(f"LLM processing error for {filename}: {e}", exc_info=True)
        return {
            'title': None,
            'brand': None,
            'category': None,
            'category_group': None,
            'base_price': None,
            'discount_price': None,
            'size_value': None,
            'size_unit': None,
            'product_type': None,
            'error': str(e)
        }


@organization_bp.route('/products/<int:product_id>/upload-image', methods=['POST'])
@jwt_auth_required
def upload_product_image(product_id):
    """Upload a new image for a specific product"""
    user = request.jwt_user
    business, role = get_user_business(user)

    if not business:
        return jsonify({'error': 'You are not a member of any organization'}), 403

    from models import db, Product

    product = Product.query.filter_by(id=product_id, business_id=business.id).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    if not file.filename:
        return jsonify({'error': 'No image provided'}), 400

    try:
        # Validate and process image
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

        if ext not in allowed_extensions:
            return jsonify({'error': 'Invalid file type'}), 400

        image_data = file.read()

        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'error': 'File too large (max 10MB)'}), 400

        # Process with PIL
        img = Image.open(io.BytesIO(image_data))

        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if needed
        max_dim = 2048
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        processed_data = buffer.read()

        # Upload to S3
        from s3_utils import upload_to_s3

        unique_filename = f"{uuid.uuid4()}.jpg"
        s3_path = f"assets/images/product_images/{business.id}/{product_id}/{unique_filename}"

        s3_url = upload_to_s3(processed_data, s3_path, content_type='image/jpeg')

        if not s3_url:
            return jsonify({'error': 'Failed to upload image'}), 500

        # Update product
        product.image_path = s3_url
        db.session.commit()

        logger.info(f"Image uploaded for product {product_id} by user {user.email}")

        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'image_url': s3_url
        })

    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
