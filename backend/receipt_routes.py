"""
Receipt Upload & Purchase Analytics API Routes
Handles user receipt photo uploads, OCR processing, and purchase statistics
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date, timedelta
from functools import wraps
from decimal import Decimal
import boto3
import uuid
import os
import json
import threading
from PIL import Image
import io
import base64

from app import db
from models import User, Business, Receipt, ReceiptItem
from auth_api import require_jwt_auth

receipts_bp = Blueprint('receipts', __name__)


def login_required(f):
    """Decorator to require authentication (wraps require_jwt_auth)"""
    @wraps(f)
    @require_jwt_auth
    def decorated_function(*args, **kwargs):
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return f(user, *args, **kwargs)
    return decorated_function


def get_s3_client():
    """Get configured S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'eu-central-1')
    )


def upload_receipt_image(file_data, user_id, receipt_id):
    """
    Upload receipt image to S3 with resizing to 600px
    Returns the S3 URL
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')

    # Path: /receipts/{user_id}/{receipt_id}.jpg
    filename = f"receipts/{user_id}/{receipt_id}.jpg"

    # Process image - resize to max 600px for LLM (per requirement)
    img = Image.open(io.BytesIO(file_data))

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize to max 800px on longest side (larger = better OCR accuracy)
    max_size = 800
    if max(img.width, img.height) > max_size:
        if img.width > img.height:
            ratio = max_size / img.width
        else:
            ratio = max_size / img.height
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)

    # Upload to S3
    s3.upload_fileobj(
        buffer,
        bucket,
        filename,
        ExtraArgs={
            'ContentType': 'image/jpeg'
        }
    )

    # Return full URL
    return f"https://{bucket}.s3.eu-central-1.amazonaws.com/{filename}"


def resize_image_for_ocr(file_data):
    """
    Resize image to ~600px for OCR processing
    Returns base64 encoded image
    """
    img = Image.open(io.BytesIO(file_data))

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize to max 800px on longest side (larger = better OCR accuracy)
    max_size = 800
    if max(img.width, img.height) > max_size:
        if img.width > img.height:
            ratio = max_size / img.width
        else:
            ratio = max_size / img.height
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to buffer
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85, optimize=True)
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8')


def check_duplicate_receipt(user_id, jib, receipt_serial, receipt_date):
    """
    Check if a receipt with same identifiers already exists
    Returns existing receipt if found, None otherwise
    """
    if not jib and not receipt_serial:
        return None

    query = Receipt.query.filter(Receipt.user_id == user_id)

    # Check by JIB + serial + date combination
    if jib and receipt_serial:
        existing = query.filter(
            Receipt.jib == jib,
            Receipt.receipt_serial_number == receipt_serial
        ).first()
        if existing:
            return existing

    # Check by date + serial (same day, same serial = likely duplicate)
    if receipt_serial and receipt_date:
        date_only = receipt_date.date() if isinstance(receipt_date, datetime) else receipt_date
        existing = query.filter(
            Receipt.receipt_serial_number == receipt_serial,
            db.func.date(Receipt.receipt_date) == date_only
        ).first()
        if existing:
            return existing

    return None


def match_business_by_name(store_name):
    """
    Match store name to existing business using semantic similarity
    Returns business_id if found, None otherwise
    """
    if not store_name:
        return None

    # Normalize store name
    store_name_lower = store_name.lower().strip()

    # Try exact match first
    business = Business.query.filter(
        db.func.lower(Business.name) == store_name_lower
    ).first()
    if business:
        return business.id

    # Try partial match (contains)
    business = Business.query.filter(
        db.func.lower(Business.name).contains(store_name_lower)
    ).first()
    if business:
        return business.id

    # Try if store name contains business name
    businesses = Business.query.filter(Business.is_active == True).all()
    for biz in businesses:
        if biz.name.lower() in store_name_lower:
            return biz.id

    return None


def process_receipt_ocr(receipt_id, image_base64, app_context):
    """
    Background task to process receipt OCR
    Uses GPT-4o-mini for cost efficiency (receipts are simple text on white)
    """
    with app_context:
        try:
            receipt = Receipt.query.get(receipt_id)
            if not receipt:
                return

            receipt.processing_status = 'processing'
            db.session.commit()

            from openai_utils import openai_client

            # OCR extraction prompt with product type rules from extract-matching
            system_prompt = """You are a receipt OCR specialist for Bosnian grocery stores. Extract data from receipt images.

STORE INFO EXTRACTION:
- store_name: Name of the store (e.g., "BINGO", "KONZUM", "MERCATOR")
- store_address: Full address if visible
- jib: Jedinstveni identifikacioni broj (13-digit number)
- pib: Poreski identifikacioni broj (12-digit number starting with 4)
- ibfm: ID broja fiskalnog modula
- receipt_serial_number: Receipt/fiscal number (often labeled "Račun br." or "Fiskalni račun")
- receipt_date: Date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
- total_amount: Total amount in KM (number only)

CRITICAL - BOSNIAN RECEIPT FORMAT:
Bosnian receipts typically show items in this format:
  [CODE] PRODUCT NAME
  [QUANTITY] x [UNIT_PRICE] = [LINE_TOTAL]

Example:
  81019 FILET LOSOSA 400G
  2 x 15.70 = 31.40

This means: quantity=2, unit_price=15.70, line_total=31.40

IMPORTANT: The quantity line may appear BELOW the product name!
Look for these QUANTITY PATTERNS:
- "2 x 15.70" or "2x15.70" - means quantity 2
- "4.000x" or "4.000 x" - means quantity 4 (the .000 is decimal formatting)
- "2.000x 15.70" - means quantity 2
- "1x4" or "1 x 4" - may mean quantity 4
- "3 * 5.99" - means quantity 3
- Any number followed by "x" indicates quantity

The quantity is often shown with decimal places like "2.000" which just means 2.
Parse "4.000x" as quantity=4.

If you see a line with numbers like "2 x 15.70 = 31.40" or "4.000x 7.85",
this belongs to the product on the line ABOVE it.

ITEM EXTRACTION RULES:
For each line item, extract:
- raw_name: EXACT text as printed on receipt (preserve original, include the product code at start)
- parsed_name: Clean product name (remove codes, clean up)
- brand: Brand if identifiable (use "UNKNOWN" if not found)
- product_type: Generic product type in Bosnian, lowercase:
  * "mlijeko", "jogurt", "sir", "kajmak", "pavlaka" (dairy)
  * "kafa", "čaj" (beverages)
  * "čokolada", "keks", "bomboni", "grickalice" (sweets)
  * "deterdžent", "omekšivač" (cleaning)
  * "šampon", "sapun", "pasta za zube" (hygiene)
  * "hljeb", "pecivo" (bakery)
  * "piletina", "govedina", "svinjetina", "riba", "losos" (meat/fish)
  * "sok", "voda", "pivo" (drinks)
  * "voće", "povrće" (produce)
  * "vrećica", "kesa" (bags)
- quantity: Number of items - VERY IMPORTANT: check for "N x price" pattern!
- unit: "kom" for pieces, "kg" for weight, "l" for volume
- pack_size: Package size as shown (e.g., "1l", "500g", "400g")
- unit_price: Price per SINGLE unit (if "2 x 15.70 = 31.40", unit_price is 15.70)
- line_total: Total for this line (the final amount after multiplication)
- size_value: Numeric size (e.g., 500 from "500g", 400 from "400g")
- size_unit: Normalized unit: "g", "kg", "ml", "l", "kom"

SIZE EXTRACTION RULES:
- "1kg" → size_value: 1, size_unit: "kg"
- "500g" → size_value: 500, size_unit: "g"
- "400g" → size_value: 400, size_unit: "g"
- "1l" → size_value: 1, size_unit: "l"
- "500ml" → size_value: 500, size_unit: "ml"
- "330ml" → size_value: 330, size_unit: "ml"
- "6x0.5l" → size_value: 3, size_unit: "l" (total volume)
- "10 kom" → size_value: 10, size_unit: "kom"

Return JSON:
{
    "store_name": "...",
    "store_address": "...",
    "jib": "...",
    "pib": "...",
    "ibfm": "...",
    "receipt_serial_number": "...",
    "receipt_date": "YYYY-MM-DDTHH:MM:SS",
    "total_amount": 123.45,
    "items": [
        {
            "raw_name": "EXACT TEXT FROM RECEIPT",
            "parsed_name": "...",
            "brand": "...",
            "product_type": "...",
            "quantity": 1,
            "unit": "kom",
            "pack_size": "...",
            "unit_price": 1.99,
            "line_total": 1.99,
            "size_value": null,
            "size_unit": null
        }
    ]
}"""

            # Call GPT-4o-mini (cheap, good for OCR on white background)
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all data from this receipt image:"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "auto"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.1
            )

            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)

            # Update receipt with extracted data
            if result.get('store_name'):
                receipt.store_name = result['store_name']
                # Try to match to existing business
                receipt.business_id = match_business_by_name(result['store_name'])

            if result.get('store_address'):
                receipt.store_address = result['store_address']
            if result.get('jib'):
                receipt.jib = result['jib']
            if result.get('pib'):
                receipt.pib = result['pib']
            if result.get('ibfm'):
                receipt.ibfm = result['ibfm']
            if result.get('receipt_serial_number'):
                receipt.receipt_serial_number = result['receipt_serial_number']
            if result.get('receipt_date'):
                try:
                    receipt.receipt_date = datetime.fromisoformat(result['receipt_date'].replace('Z', '+00:00'))
                except:
                    pass
            if result.get('total_amount'):
                receipt.total_amount = Decimal(str(result['total_amount']))

            # Check for duplicates now that we have extracted data
            duplicate = check_duplicate_receipt(
                receipt.user_id,
                receipt.jib,
                receipt.receipt_serial_number,
                receipt.receipt_date
            )
            if duplicate and duplicate.id != receipt.id:
                # Mark as duplicate - user can delete manually if they want
                receipt.processing_status = 'duplicate'
                receipt.processing_error = f'Ovaj račun je već učitan. Originalni račun ima ID: {duplicate.id}.'
                receipt.duplicate_of_id = duplicate.id
                db.session.commit()
                current_app.logger.info(f"Receipt {receipt.id} marked as duplicate of {duplicate.id}")
                return

            # Create receipt items
            items = result.get('items', [])
            for item_data in items:
                item = ReceiptItem(
                    receipt_id=receipt.id,
                    raw_name=item_data.get('raw_name', ''),
                    parsed_name=item_data.get('parsed_name'),
                    brand=item_data.get('brand', 'UNKNOWN'),
                    product_type=item_data.get('product_type'),
                    quantity=Decimal(str(item_data.get('quantity', 1))) if item_data.get('quantity') else Decimal('1'),
                    unit=item_data.get('unit'),
                    pack_size=item_data.get('pack_size'),
                    unit_price=Decimal(str(item_data['unit_price'])) if item_data.get('unit_price') else None,
                    line_total=Decimal(str(item_data['line_total'])) if item_data.get('line_total') else None,
                    size_value=Decimal(str(item_data['size_value'])) if item_data.get('size_value') else None,
                    size_unit=item_data.get('size_unit')
                )
                db.session.add(item)

            receipt.processing_status = 'completed'
            receipt.processed_at = datetime.now()
            db.session.commit()

            current_app.logger.info(f"Receipt {receipt_id} processed successfully with {len(items)} items")

        except Exception as e:
            receipt = Receipt.query.get(receipt_id)
            if receipt:
                receipt.processing_status = 'failed'
                receipt.processing_error = str(e)[:500]
                db.session.commit()
            current_app.logger.error(f"Error processing receipt {receipt_id}: {e}")


# ==================== USER ENDPOINTS ====================

@receipts_bp.route('/api/receipts/upload', methods=['POST'])
@login_required
def upload_receipt(user):
    """
    Upload a receipt image
    Returns immediately with receipt ID, processes OCR in background
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400

    # Check file size (max 10MB)
    file_data = file.read()
    if len(file_data) > 10 * 1024 * 1024:
        return jsonify({'error': 'File too large. Maximum 10MB allowed'}), 400

    try:
        # Create receipt record first to get ID
        receipt = Receipt(
            user_id=user.id,
            receipt_image_url='',  # Will be updated after upload
            processing_status='pending'
        )
        db.session.add(receipt)
        db.session.flush()  # Get the ID

        # Upload to S3 with proper path
        image_url = upload_receipt_image(file_data, user.id, receipt.id)
        receipt.receipt_image_url = image_url
        db.session.commit()

        # Prepare image for OCR (resize to 600px)
        image_base64 = resize_image_for_ocr(file_data)

        # Start background processing
        app_context = current_app._get_current_object().app_context()
        thread = threading.Thread(
            target=process_receipt_ocr,
            args=(receipt.id, image_base64, app_context)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'receipt': receipt.to_dict(),
            'message': 'Receipt uploaded, processing started'
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading receipt: {e}")
        return jsonify({'error': 'Failed to upload receipt'}), 500


@receipts_bp.route('/api/receipts', methods=['GET'])
@login_required
def get_receipts(user):
    """Get user's receipts with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')  # Filter by status

    query = Receipt.query.filter(Receipt.user_id == user.id)

    if status:
        query = query.filter(Receipt.processing_status == status)

    query = query.order_by(Receipt.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'receipts': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@receipts_bp.route('/api/receipts/<int:receipt_id>', methods=['GET'])
@login_required
def get_receipt(user, receipt_id):
    """Get single receipt with items"""
    receipt = Receipt.query.filter(
        Receipt.id == receipt_id,
        Receipt.user_id == user.id
    ).first()

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    return jsonify({
        'receipt': receipt.to_dict(include_items=True)
    })


@receipts_bp.route('/api/receipts/<int:receipt_id>', methods=['DELETE'])
@login_required
def delete_receipt(user, receipt_id):
    """Delete a receipt"""
    receipt = Receipt.query.filter(
        Receipt.id == receipt_id,
        Receipt.user_id == user.id
    ).first()

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    # Delete from S3
    try:
        s3 = get_s3_client()
        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
        key = f"receipts/{user.id}/{receipt_id}.jpg"
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        current_app.logger.warning(f"Failed to delete S3 object: {e}")

    db.session.delete(receipt)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Receipt deleted'})


@receipts_bp.route('/api/receipts/<int:receipt_id>/reprocess', methods=['POST'])
@login_required
def reprocess_receipt(user, receipt_id):
    """Re-run OCR on existing receipt"""
    receipt = Receipt.query.filter(
        Receipt.id == receipt_id,
        Receipt.user_id == user.id
    ).first()

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    # Delete existing items
    ReceiptItem.query.filter(ReceiptItem.receipt_id == receipt_id).delete()

    # Reset receipt
    receipt.processing_status = 'pending'
    receipt.processing_error = None
    receipt.store_name = None
    receipt.store_address = None
    receipt.jib = None
    receipt.pib = None
    receipt.ibfm = None
    receipt.receipt_serial_number = None
    receipt.receipt_date = None
    receipt.total_amount = None
    receipt.business_id = None
    db.session.commit()

    # Download image from S3 and reprocess
    try:
        import urllib.request
        with urllib.request.urlopen(receipt.receipt_image_url) as response:
            image_data = response.read()

        image_base64 = resize_image_for_ocr(image_data)

        # Start background processing
        app_context = current_app._get_current_object().app_context()
        thread = threading.Thread(
            target=process_receipt_ocr,
            args=(receipt.id, image_base64, app_context)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Reprocessing started'
        })

    except Exception as e:
        current_app.logger.error(f"Error reprocessing receipt: {e}")
        return jsonify({'error': 'Failed to reprocess receipt'}), 500


@receipts_bp.route('/api/receipts/<int:receipt_id>/items/<int:item_id>', methods=['PUT'])
@login_required
def update_receipt_item(user, receipt_id, item_id):
    """Update a receipt item's raw_name for reprocessing"""
    receipt = Receipt.query.filter(
        Receipt.id == receipt_id,
        Receipt.user_id == user.id
    ).first()

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    item = ReceiptItem.query.filter(
        ReceiptItem.id == item_id,
        ReceiptItem.receipt_id == receipt_id
    ).first()

    if not item:
        return jsonify({'error': 'Item not found'}), 404

    data = request.get_json()
    if 'raw_name' in data:
        item.raw_name = data['raw_name']
    if 'parsed_name' in data:
        item.parsed_name = data['parsed_name']
    if 'brand' in data:
        item.brand = data['brand']
    if 'product_type' in data:
        item.product_type = data['product_type']
    if 'quantity' in data:
        item.quantity = Decimal(str(data['quantity']))
    if 'unit' in data:
        item.unit = data['unit']
    if 'unit_price' in data:
        item.unit_price = Decimal(str(data['unit_price'])) if data['unit_price'] else None
    if 'line_total' in data:
        item.line_total = Decimal(str(data['line_total'])) if data['line_total'] else None

    db.session.commit()

    return jsonify({
        'success': True,
        'item': item.to_dict()
    })


# ==================== ITEMS ENDPOINT ====================

@receipts_bp.route('/api/receipts/items', methods=['GET'])
@login_required
def get_all_receipt_items(user):
    """
    Get all receipt items for the user with receipt date information
    Used for expenses/statistics aggregation on frontend
    """
    per_page = request.args.get('per_page', 1000, type=int)

    # Get all completed receipts for user
    receipts = Receipt.query.filter(
        Receipt.user_id == user.id,
        Receipt.processing_status == 'completed'
    ).all()

    receipt_ids = [r.id for r in receipts]
    receipt_map = {r.id: r for r in receipts}

    if not receipt_ids:
        return jsonify({'items': [], 'total': 0})

    # Get all items with receipt info
    items = ReceiptItem.query.filter(
        ReceiptItem.receipt_id.in_(receipt_ids)
    ).limit(per_page).all()

    result = []
    for item in items:
        receipt = receipt_map.get(item.receipt_id)
        result.append({
            'id': item.id,
            'receipt_id': item.receipt_id,
            'receipt_date': receipt.receipt_date.isoformat() if receipt and receipt.receipt_date else None,
            'created_at': receipt.created_at.isoformat() if receipt and receipt.created_at else None,
            'store_name': receipt.store_name if receipt else None,
            'raw_name': item.raw_name,
            'parsed_name': item.parsed_name,
            'brand': item.brand,
            'product_type': item.product_type,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price) if item.unit_price else None,
            'line_total': float(item.line_total) if item.line_total else None,
            'pack_size': item.pack_size
        })

    return jsonify({
        'items': result,
        'total': len(result)
    })


# ==================== STATISTICS ENDPOINTS ====================

@receipts_bp.route('/api/receipts/statistics', methods=['GET'])
@login_required
def get_receipt_statistics(user):
    """
    Get aggregated purchase statistics
    Supports: daily, weekly, monthly aggregation
    """
    period = request.args.get('period', 'monthly')  # daily, weekly, monthly
    months_back = request.args.get('months', 3, type=int)

    # Calculate date range
    end_date = datetime.now()
    if period == 'daily':
        start_date = end_date - timedelta(days=30)
    elif period == 'weekly':
        start_date = end_date - timedelta(weeks=12)
    else:  # monthly
        start_date = end_date - timedelta(days=30 * months_back)

    # Get completed receipts in range
    receipts = Receipt.query.filter(
        Receipt.user_id == user.id,
        Receipt.processing_status == 'completed',
        Receipt.created_at >= start_date
    ).all()

    # Calculate totals
    total_spent = sum(float(r.total_amount or 0) for r in receipts)
    total_receipts = len(receipts)

    # Get all items
    receipt_ids = [r.id for r in receipts]
    items = ReceiptItem.query.filter(ReceiptItem.receipt_id.in_(receipt_ids)).all() if receipt_ids else []
    total_items = len(items)

    # Aggregate by brand
    by_brand = {}
    for item in items:
        brand = item.brand or 'UNKNOWN'
        if brand not in by_brand:
            by_brand[brand] = {'count': 0, 'total': 0}
        by_brand[brand]['count'] += 1
        by_brand[brand]['total'] += float(item.line_total or 0)

    # Aggregate by product_type with quantity tracking
    by_product_type = {}
    for item in items:
        ptype = item.product_type or 'ostalo'
        if ptype not in by_product_type:
            by_product_type[ptype] = {
                'count': 0,
                'total': 0,
                'quantity': {'kg': 0, 'g': 0, 'l': 0, 'ml': 0, 'kom': 0}
            }
        by_product_type[ptype]['count'] += 1
        by_product_type[ptype]['total'] += float(item.line_total or 0)

        # Track quantities
        if item.size_value and item.size_unit:
            unit = item.size_unit.lower()
            qty = float(item.size_value) * float(item.quantity or 1)
            if unit in by_product_type[ptype]['quantity']:
                by_product_type[ptype]['quantity'][unit] += qty

    # Normalize quantities (convert g to kg, ml to l)
    for ptype in by_product_type:
        qty = by_product_type[ptype]['quantity']
        # Convert g to kg
        if qty['g'] >= 1000:
            qty['kg'] += qty['g'] / 1000
            qty['g'] = qty['g'] % 1000
        # Convert ml to l
        if qty['ml'] >= 1000:
            qty['l'] += qty['ml'] / 1000
            qty['ml'] = qty['ml'] % 1000

    # Calculate monthly average
    if months_back > 0:
        monthly_average = total_spent / months_back
    else:
        monthly_average = total_spent

    # This month's spending
    this_month_start = date.today().replace(day=1)
    this_month_receipts = [r for r in receipts if r.created_at.date() >= this_month_start]
    this_month_spent = sum(float(r.total_amount or 0) for r in this_month_receipts)

    # Most frequent brand
    most_frequent_brand = max(by_brand.items(), key=lambda x: x[1]['count'])[0] if by_brand else None

    # Top product types
    top_product_types = sorted(
        by_product_type.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )[:10]

    return jsonify({
        'period': period,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'totals': {
            'spent': round(total_spent, 2),
            'receipts': total_receipts,
            'items': total_items
        },
        'monthly_average': round(monthly_average, 2),
        'this_month': round(this_month_spent, 2),
        'most_frequent_brand': most_frequent_brand,
        'by_brand': {k: {'count': v['count'], 'total': round(v['total'], 2)} for k, v in sorted(by_brand.items(), key=lambda x: x[1]['total'], reverse=True)[:20]},
        'by_product_type': [
            {
                'type': ptype,
                'count': data['count'],
                'total': round(data['total'], 2),
                'quantity': {k: round(v, 2) for k, v in data['quantity'].items() if v > 0}
            }
            for ptype, data in top_product_types
        ]
    })


@receipts_bp.route('/api/receipts/statistics/spending', methods=['GET'])
@login_required
def get_spending_over_time(user):
    """Get spending trends over time (for charts)"""
    period = request.args.get('period', 'daily')  # daily, weekly, monthly
    days_back = request.args.get('days', 30, type=int)

    start_date = datetime.now() - timedelta(days=days_back)

    receipts = Receipt.query.filter(
        Receipt.user_id == user.id,
        Receipt.processing_status == 'completed',
        Receipt.created_at >= start_date
    ).order_by(Receipt.created_at).all()

    # Group by period
    spending = {}
    for receipt in receipts:
        if period == 'daily':
            key = receipt.created_at.strftime('%Y-%m-%d')
        elif period == 'weekly':
            # Get week number
            key = receipt.created_at.strftime('%Y-W%W')
        else:  # monthly
            key = receipt.created_at.strftime('%Y-%m')

        if key not in spending:
            spending[key] = {'total': 0, 'count': 0}
        spending[key]['total'] += float(receipt.total_amount or 0)
        spending[key]['count'] += 1

    return jsonify({
        'period': period,
        'data': [
            {'date': k, 'total': round(v['total'], 2), 'count': v['count']}
            for k, v in sorted(spending.items())
        ]
    })


# ==================== ADMIN ENDPOINTS ====================

def jwt_admin_required(f):
    """Decorator to require admin privileges via JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401

        try:
            token = auth_header.replace('Bearer ', '')
            payload = decode_jwt_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401

            user = User.query.get(payload.get('user_id'))
            if not user:
                return jsonify({'error': 'User not found'}), 404

            if not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403

            return f(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Admin auth error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function


@receipts_bp.route('/api/admin/receipts', methods=['GET'])
@jwt_admin_required
def admin_get_all_receipts():
    """Admin: Get all receipts with user info"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status')
    user_id = request.args.get('user_id')
    search = request.args.get('search', '')

    query = Receipt.query

    # Filters
    if status:
        query = query.filter(Receipt.processing_status == status)

    if user_id:
        query = query.filter(Receipt.user_id == user_id)

    if search:
        # Search by store name, JIB, or user email
        query = query.join(User, Receipt.user_id == User.id).filter(
            db.or_(
                Receipt.store_name.ilike(f'%{search}%'),
                Receipt.jib.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    query = query.order_by(Receipt.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get receipts with user info
    receipts_data = []
    for receipt in pagination.items:
        user = User.query.get(receipt.user_id)
        data = receipt.to_dict(include_items=True)
        data['user'] = {
            'id': user.id if user else None,
            'email': user.email if user else 'Unknown',
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() if user else 'Unknown'
        }
        receipts_data.append(data)

    return jsonify({
        'receipts': receipts_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@receipts_bp.route('/api/admin/receipts/<int:receipt_id>', methods=['GET'])
@jwt_admin_required
def admin_get_receipt(receipt_id):
    """Admin: Get single receipt with full details"""
    receipt = Receipt.query.get(receipt_id)
    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    user = User.query.get(receipt.user_id)
    data = receipt.to_dict(include_items=True)
    data['user'] = {
        'id': user.id if user else None,
        'email': user.email if user else 'Unknown',
        'name': f"{user.first_name or ''} {user.last_name or ''}".strip() if user else 'Unknown'
    }

    return jsonify({'receipt': data})


@receipts_bp.route('/api/admin/receipts/<int:receipt_id>', methods=['DELETE'])
@jwt_admin_required
def admin_delete_receipt(receipt_id):
    """Admin: Delete any receipt"""
    receipt = Receipt.query.get(receipt_id)
    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    # Delete from S3
    try:
        s3 = get_s3_client()
        bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')
        key = f"receipts/{receipt.user_id}/{receipt_id}.jpg"
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        current_app.logger.warning(f"Failed to delete S3 object: {e}")

    db.session.delete(receipt)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Receipt deleted'})


@receipts_bp.route('/api/admin/receipts/stats', methods=['GET'])
@jwt_admin_required
def admin_get_receipts_stats():
    """Admin: Get overall receipt statistics"""
    from sqlalchemy import func

    total_receipts = Receipt.query.count()
    total_completed = Receipt.query.filter(Receipt.processing_status == 'completed').count()
    total_failed = Receipt.query.filter(Receipt.processing_status == 'failed').count()
    total_pending = Receipt.query.filter(Receipt.processing_status == 'pending').count()

    # Users with receipts
    users_with_receipts = db.session.query(func.count(func.distinct(Receipt.user_id))).scalar()

    # Total items extracted
    total_items = ReceiptItem.query.count()

    # Total amount (all completed receipts)
    total_amount = db.session.query(func.sum(Receipt.total_amount)).filter(
        Receipt.processing_status == 'completed'
    ).scalar() or 0

    # Recent uploads (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_uploads = Receipt.query.filter(Receipt.created_at >= week_ago).count()

    # Count duplicates too
    total_duplicate = Receipt.query.filter(Receipt.processing_status == 'duplicate').count()

    return jsonify({
        'total_receipts': total_receipts,
        'by_status': {
            'completed': total_completed,
            'failed': total_failed,
            'pending': total_pending,
            'duplicate': total_duplicate
        },
        'users_with_receipts': users_with_receipts,
        'total_items': total_items,
        'total_amount': float(total_amount),
        'recent_uploads_7d': recent_uploads
    })


