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
from PIL import Image, ImageOps
import io
import base64

from app import db
from models import User, Business, Receipt, ReceiptItem, APIUsageLog
from auth_api import require_jwt_auth
import time

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

    # Fix EXIF orientation (mobile photos often have rotation in metadata)
    img = ImageOps.exif_transpose(img)

    # Convert to RGB if necessary (for PNG with transparency)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize to max 2000px on longest side (need high res for OCR reprocessing)
    max_size = 2000
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


def upload_cropped_receipt_image(image_bytes, user_id, receipt_id):
    """
    Upload the cropped/processed receipt image to S3 for debugging
    This shows exactly what the OCR model is analyzing
    Returns the S3 URL
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')

    # Path: /receipts/{user_id}/{receipt_id}_cropped.jpg
    filename = f"receipts/{user_id}/{receipt_id}_cropped.jpg"

    # Upload to S3
    s3.upload_fileobj(
        io.BytesIO(image_bytes),
        bucket,
        filename,
        ExtraArgs={
            'ContentType': 'image/jpeg'
        }
    )

    # Return full URL
    return f"https://{bucket}.s3.eu-central-1.amazonaws.com/{filename}"


def upload_split_part_image(image_bytes, user_id, receipt_id, part_name):
    """
    Upload a split receipt part (top or bottom) to S3 for admin debugging.

    Args:
        image_bytes: Raw image bytes
        user_id: User ID
        receipt_id: Receipt ID
        part_name: 'top' or 'bottom'

    Returns the S3 URL
    """
    s3 = get_s3_client()
    bucket = os.environ.get('AWS_S3_BUCKET') or os.environ.get('S3_BUCKET_NAME', 'aipijaca')

    # Path: /receipts/{user_id}/{receipt_id}_{part_name}.jpg
    filename = f"receipts/{user_id}/{receipt_id}_{part_name}.jpg"

    # Upload to S3
    s3.upload_fileobj(
        io.BytesIO(image_bytes),
        bucket,
        filename,
        ExtraArgs={
            'ContentType': 'image/jpeg'
        }
    )

    # Return full URL
    return f"https://{bucket}.s3.eu-central-1.amazonaws.com/{filename}"


def resize_image_for_ocr(file_data, use_precrop=True, return_bytes=False):
    """
    Resize image for OCR processing - optionally pre-crop to receipt area.

    Args:
        file_data: Raw image bytes
        use_precrop: If True, detect receipt bounds and crop first (adds ~$0.0005 cost)
        return_bytes: If True, also return raw bytes for S3 upload

    Returns:
        If return_bytes=False: base64 encoded image string
        If return_bytes=True: tuple (base64_string, raw_bytes)
    """
    img = Image.open(io.BytesIO(file_data))

    # Fix EXIF orientation (mobile photos often have rotation in metadata)
    img = ImageOps.exif_transpose(img)

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Pre-crop to receipt area if enabled (reduces main OCR costs)
    original_size = (img.width, img.height)
    if use_precrop and max(img.width, img.height) > 1000:
        import logging
        logging.info(f"Pre-crop: Original image size {img.width}x{img.height}")

        # First resize to smaller size for cheap detection
        detect_max = 1000
        detect_img = img.copy()
        if max(detect_img.width, detect_img.height) > detect_max:
            if detect_img.width > detect_img.height:
                ratio = detect_max / detect_img.width
            else:
                ratio = detect_max / detect_img.height
            new_w = int(detect_img.width * ratio)
            new_h = int(detect_img.height * ratio)
            detect_img = detect_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Get detection image as base64
        detect_buffer = io.BytesIO()
        detect_img.save(detect_buffer, format='JPEG', quality=70)
        detect_buffer.seek(0)
        detect_base64 = base64.b64encode(detect_buffer.read()).decode('utf-8')

        # Detect receipt bounds
        logging.info("Pre-crop: Calling GPT-4o-mini for receipt detection...")
        bounds = detect_receipt_bounds(detect_base64)
        logging.info(f"Pre-crop: Detection returned bounds={bounds}")

        if bounds:
            # Crop the ORIGINAL image (not the detection copy) with no padding for tight crop
            img = crop_image_to_receipt(img, bounds, padding_percent=0)
            logging.info(f"Pre-crop: Cropped to {img.width}x{img.height}")
        else:
            logging.warning("Pre-crop: No bounds detected, using original image")

    # Keep larger size for better OCR accuracy (4000px max)
    # Receipts have small text that needs high resolution
    max_size = 4000
    if max(img.width, img.height) > max_size:
        if img.width > img.height:
            ratio = max_size / img.width
        else:
            ratio = max_size / img.height
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save to buffer with higher quality
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90, optimize=True)
    buffer.seek(0)

    raw_bytes = buffer.read()
    base64_str = base64.b64encode(raw_bytes).decode('utf-8')

    if return_bytes:
        return base64_str, raw_bytes
    return base64_str


def prepare_images_for_ocr(file_data, use_precrop=True):
    """
    Prepare image(s) for OCR - splits tall images into top/bottom halves.

    For long receipts (height > width * 2), splits with 10% overlap to ensure
    no items are cut off at the boundary.

    Args:
        file_data: Raw image bytes
        use_precrop: If True, detect receipt bounds and crop first

    Returns:
        dict with:
            - 'images': list of base64 encoded images for OCR
            - 'is_split': True if image was split
            - 'combined_bytes': Raw bytes of combined/side-by-side image for S3 storage
            - 'parts': list of dicts with 'position' ('top'/'bottom'/'full') and 'base64'
    """
    import logging

    img = Image.open(io.BytesIO(file_data))

    # Fix EXIF orientation
    img = ImageOps.exif_transpose(img)

    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Pre-crop to receipt area if enabled
    if use_precrop and max(img.width, img.height) > 1000:
        logging.info(f"Pre-crop: Original image size {img.width}x{img.height}")

        # First resize to smaller size for cheap detection
        detect_max = 1000
        detect_img = img.copy()
        if max(detect_img.width, detect_img.height) > detect_max:
            if detect_img.width > detect_img.height:
                ratio = detect_max / detect_img.width
            else:
                ratio = detect_max / detect_img.height
            new_w = int(detect_img.width * ratio)
            new_h = int(detect_img.height * ratio)
            detect_img = detect_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Get detection image as base64
        detect_buffer = io.BytesIO()
        detect_img.save(detect_buffer, format='JPEG', quality=70)
        detect_buffer.seek(0)
        detect_base64 = base64.b64encode(detect_buffer.read()).decode('utf-8')

        # Detect receipt bounds
        bounds = detect_receipt_bounds(detect_base64)

        if bounds:
            img = crop_image_to_receipt(img, bounds, padding_percent=0)
            logging.info(f"Pre-crop: Cropped to {img.width}x{img.height}")

    # Check if image is portrait (height > width) - always split portrait receipts
    aspect_ratio = img.height / img.width if img.width > 0 else 1
    should_split = img.height > img.width  # Split any portrait-orientation receipt

    logging.info(f"Image {img.width}x{img.height}, aspect ratio: {aspect_ratio:.2f}, should_split: {should_split}")

    if should_split:
        # Split into top and bottom with 17% overlap
        # For 600px image: top=0-400, bottom=200-600, overlap=200-400
        overlap_percent = 17
        overlap_pixels = int(img.height * overlap_percent / 100)
        mid_point = img.height // 2

        # Top half: from 0 to mid_point + overlap
        top_bottom = min(mid_point + overlap_pixels, img.height)
        top_img = img.crop((0, 0, img.width, top_bottom))

        # Bottom half: from mid_point - overlap to end
        bottom_top = max(mid_point - overlap_pixels, 0)
        bottom_img = img.crop((0, bottom_top, img.width, img.height))

        logging.info(f"Split image: top={top_img.width}x{top_img.height}, bottom={bottom_img.width}x{bottom_img.height}")

        # Resize each half to max 4000px
        max_size = 4000
        images_data = []

        for part_name, part_img in [('top', top_img), ('bottom', bottom_img)]:
            if max(part_img.width, part_img.height) > max_size:
                if part_img.width > part_img.height:
                    ratio = max_size / part_img.width
                else:
                    ratio = max_size / part_img.height
                new_w = int(part_img.width * ratio)
                new_h = int(part_img.height * ratio)
                part_img = part_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            part_img.save(buffer, format='JPEG', quality=90, optimize=True)
            buffer.seek(0)
            raw_bytes = buffer.read()
            base64_str = base64.b64encode(raw_bytes).decode('utf-8')

            images_data.append({
                'position': part_name,
                'base64': base64_str,
                'bytes': raw_bytes,
                'width': part_img.width,
                'height': part_img.height
            })

        # Create combined side-by-side image for storage (debugging)
        # Stack them vertically with a red divider line
        combined_height = images_data[0]['height'] + images_data[1]['height'] + 10
        combined_width = max(images_data[0]['width'], images_data[1]['width'])
        combined_img = Image.new('RGB', (combined_width, combined_height), (255, 0, 0))  # Red background for divider

        # Paste top and bottom
        top_resized = Image.open(io.BytesIO(images_data[0]['bytes']))
        bottom_resized = Image.open(io.BytesIO(images_data[1]['bytes']))
        combined_img.paste(top_resized, (0, 0))
        combined_img.paste(bottom_resized, (0, images_data[0]['height'] + 10))

        combined_buffer = io.BytesIO()
        combined_img.save(combined_buffer, format='JPEG', quality=85)
        combined_buffer.seek(0)
        combined_bytes = combined_buffer.read()

        return {
            'images': [d['base64'] for d in images_data],
            'is_split': True,
            'combined_bytes': combined_bytes,
            'parts': images_data
        }

    else:
        # Single image - just resize
        max_size = 4000
        if max(img.width, img.height) > max_size:
            if img.width > img.height:
                ratio = max_size / img.width
            else:
                ratio = max_size / img.height
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=90, optimize=True)
        buffer.seek(0)
        raw_bytes = buffer.read()
        base64_str = base64.b64encode(raw_bytes).decode('utf-8')

        return {
            'images': [base64_str],
            'is_split': False,
            'combined_bytes': raw_bytes,
            'parts': [{
                'position': 'full',
                'base64': base64_str,
                'bytes': raw_bytes
            }]
        }


def detect_receipt_bounds(image_base64):
    """
    Use GPT-4o-mini with low detail to detect receipt bounding box.
    Returns percentage-based coordinates: (left, top, right, bottom)
    Returns None if detection fails or no receipt found.
    Cost: ~$0.0005 per detection
    """
    from openai_utils import openai_client

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You detect receipt boundaries in images. Return ONLY JSON with percentage coordinates."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Find the receipt paper in this image. Return the bounding box as PERCENTAGE coordinates (0-100).

Return JSON: {"found": true/false, "left": X, "top": Y, "right": X, "bottom": Y}

- left: percentage from left edge where receipt starts
- top: percentage from top where receipt starts
- right: percentage from left edge where receipt ends
- bottom: percentage from top where receipt ends

If no receipt found, return {"found": false}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "low"  # Use low detail for cheap detection
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=100,
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)

        if not result.get('found', False):
            return None

        return (
            result.get('left', 0),
            result.get('top', 0),
            result.get('right', 100),
            result.get('bottom', 100)
        )

    except Exception as e:
        # If detection fails, return None (will skip cropping)
        import logging
        logging.warning(f"Receipt detection failed: {e}")
        return None


def crop_image_to_receipt(img, bounds, padding_percent=5):
    """
    Crop image to receipt bounds with padding.

    Args:
        img: PIL Image object
        bounds: (left_pct, top_pct, right_pct, bottom_pct) as percentages
        padding_percent: Extra padding to add around detected bounds

    Returns:
        Cropped PIL Image
    """
    if not bounds:
        return img

    left_pct, top_pct, right_pct, bottom_pct = bounds

    # Add padding (clamped to 0-100)
    left_pct = max(0, left_pct - padding_percent)
    top_pct = max(0, top_pct - padding_percent)
    right_pct = min(100, right_pct + padding_percent)
    bottom_pct = min(100, bottom_pct + padding_percent)

    # Convert percentages to pixels
    width, height = img.size
    left = int(width * left_pct / 100)
    top = int(height * top_pct / 100)
    right = int(width * right_pct / 100)
    bottom = int(height * bottom_pct / 100)

    # Ensure valid crop box
    if right <= left or bottom <= top:
        return img

    return img.crop((left, top, right, bottom))


def check_duplicate_receipt(user_id, jib, receipt_serial, receipt_date, exclude_receipt_id=None):
    """
    Check if a receipt with same identifiers already exists.
    Returns existing receipt if found, None otherwise.

    Only checks duplicates if JIB is present - this prevents false positives
    when users upload multiple photos of different parts of a long receipt.
    """
    # JIB is required for duplicate detection
    if not jib:
        return None

    # Only check completed receipts to avoid race conditions
    query = Receipt.query.filter(
        Receipt.user_id == user_id,
        Receipt.processing_status == 'completed'
    )

    # Exclude the current receipt being processed
    if exclude_receipt_id:
        query = query.filter(Receipt.id != exclude_receipt_id)

    # Check by JIB + serial combination (most reliable)
    if receipt_serial:
        existing = query.filter(
            Receipt.jib == jib,
            Receipt.receipt_serial_number == receipt_serial
        ).first()
        if existing:
            return existing

    # Check by JIB + date (same store, same day = likely duplicate)
    if receipt_date:
        date_only = receipt_date.date() if isinstance(receipt_date, datetime) else receipt_date
        existing = query.filter(
            Receipt.jib == jib,
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
    businesses = Business.query.all()
    for biz in businesses:
        if biz.name and biz.name.lower() in store_name_lower:
            return biz.id

    return None


def call_ocr_api(image_base64, system_prompt, user_prompt, model, is_claude):
    """
    Helper function to call OCR API (OpenAI or Claude).
    Returns: (result_text, input_tokens, output_tokens, response_time_ms)
    """
    start_time = time.time()
    input_tokens = 0
    output_tokens = 0

    if is_claude:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        claude_model_map = {
            'claude-sonnet': 'claude-sonnet-4-20250514',
            'claude-haiku': 'claude-3-haiku-20240307',
        }
        claude_model = claude_model_map.get(model, 'claude-3-haiku-20240307')

        response = anthropic_client.messages.create(
            model=claude_model,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]
        )
        result_text = response.content[0].text.strip()
        if hasattr(response, 'usage'):
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
    else:
        from openai_utils import openai_client
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=3000,
            temperature=0.1
        )
        result_text = response.choices[0].message.content.strip()
        if hasattr(response, 'usage') and response.usage:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

    response_time_ms = int((time.time() - start_time) * 1000)
    return result_text, input_tokens, output_tokens, response_time_ms


def merge_split_ocr_results(top_result, bottom_result):
    """
    Merge OCR results from top and bottom halves of a split receipt.
    - Store info (name, address, JIB, PIB) comes from TOP
    - Total amount comes from BOTTOM
    - Items are combined (top items first, then bottom items, deduped by raw_name)
    """
    import logging
    logging.info(f"Merging split results: top has {len(top_result.get('items', []))} items, bottom has {len(bottom_result.get('items', []))} items")

    merged = {
        # Store info from top (usually at the top of receipt)
        'store_name': top_result.get('store_name') or bottom_result.get('store_name'),
        'store_address': top_result.get('store_address') or bottom_result.get('store_address'),
        'jib': top_result.get('jib') or bottom_result.get('jib'),
        'pib': top_result.get('pib') or bottom_result.get('pib'),
        'ibfm': top_result.get('ibfm') or bottom_result.get('ibfm'),
        'receipt_serial_number': top_result.get('receipt_serial_number') or bottom_result.get('receipt_serial_number'),
        'receipt_date': top_result.get('receipt_date') or bottom_result.get('receipt_date'),
        # Total from bottom (usually at the bottom of receipt)
        'total_amount': bottom_result.get('total_amount') or top_result.get('total_amount'),
        'receipt_format': top_result.get('receipt_format') or bottom_result.get('receipt_format'),
        'items': []
    }

    # Combine items, dedup by raw_name (items in overlap region might appear in both)
    seen_raw_names = set()
    all_items = top_result.get('items', []) + bottom_result.get('items', [])

    for item in all_items:
        raw_name = item.get('raw_name', '').strip()
        if raw_name and raw_name not in seen_raw_names:
            seen_raw_names.add(raw_name)
            merged['items'].append(item)

    logging.info(f"Merged result has {len(merged['items'])} items after dedup")
    return merged


def process_receipt_ocr(receipt_id, image_data, app_context, model="gpt-4o", is_split=False):
    """
    Background task to process receipt OCR
    Supports: gpt-4o-mini, gpt-4o (OpenAI), claude-sonnet (Anthropic)

    Args:
        receipt_id: ID of the receipt to process
        image_data: Either a single base64 string OR a dict with 'images' list and 'is_split' flag
        app_context: Flask app context
        model: Which model to use for OCR
        is_split: If True, image_data is a dict with split image parts
    """
    with app_context:
        try:
            receipt = Receipt.query.get(receipt_id)
            if not receipt:
                return

            receipt.processing_status = 'processing'
            db.session.commit()

            # Determine which API to use based on model
            is_claude = model.startswith('claude')

            # OCR extraction prompt with product type rules from extract-matching
            system_prompt = """You are a receipt OCR specialist for Bosnian grocery stores. Extract data from receipt images.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! CRITICAL PRICE EXTRACTION RULE - READ THIS FIRST !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

On the PRICE LINE (the line with "N.NNNx"), there are THREE numbers:
  [QTY]x    [UNIT_PRICE]    [LINE_TOTAL]
  LEFT      MIDDLE          RIGHT (far right edge, often ends with "E")

ALWAYS use the RIGHTMOST number for line_total - this is the ACTUAL AMOUNT CHARGED!
NEVER use the middle number for line_total - that's just the unit price!

Example: "5.000x 1.20 6.00E"
- qty = 5 (left, ends with x)
- unit_price = 1.20 (middle)
- line_total = 6.00 (RIGHT - this is what goes in line_total!)

Example: "2.000x 2.95 5.90E"
- qty = 2
- unit_price = 2.95
- line_total = 5.90 (NOT 2.95!)

VALIDATION: Sum of all line_totals should approximately equal the receipt's TOTAL.
If your sum is much lower than the receipt total, you're using unit_prices by mistake!

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

IMPORTANT - BOSNIAN LANGUAGE & CHARACTERS:
This is a Bosnian receipt. Use proper Bosnian characters: č, ć, š, ž, đ (NOT c, s, z, d).
Common Bosnian street name patterns:
- "Ulica [Name]" or just "[Name] ulica"
- "BB" means "bez broja" (no street number)
- Postal codes are 5 digits (e.g., 75000 Tuzla, 71000 Sarajevo, 78000 Banja Luka)
- Common street names: Zmaja od Bosne, Maršala Tita, Alije Izetbegovića, Mehmeda Spahe

STORE INFO EXTRACTION:
At the top of Bosnian receipts, you'll typically see:
- Line 1: Store/company name (e.g., "BINGO d.o.o.", "BELAMIONIX d.o.o.")
- Line 2: Company HQ address (sjedište firme) - IGNORE THIS
- Line 3+: THIS store's location address (where the purchase was made) - EXTRACT THIS

Extract these fields:
- store_name: Name of the store/company (e.g., "BINGO", "KONZUM", "MERCATOR")
- store_address: The specific store/branch location where the purchase was made (NOT the company HQ address!)
  Look for the address after the company HQ - it's usually the actual store location with street, city, postal code
  IMPORTANT: Use correct Bosnian characters (č, ć, š, ž, đ) in street names!
- jib: Jedinstveni identifikacioni broj (13-digit number)
- pib: Poreski identifikacioni broj (12-digit number starting with 4)
- ibfm: ID broja fiskalnog modula
- receipt_serial_number: Receipt/fiscal number (often labeled "Račun br." or "Fiskalni račun")
- receipt_date: Date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
- total_amount: Final TOTAL amount in KM including VAT (look for "TOTAL:" line, NOT "OSN. E:" which is base before tax)
- receipt_format: "two_row" or "one_row" (see below)

=== RECEIPT FORMAT DETECTION ===
Bosnian receipts come in TWO formats. FIRST detect which format this receipt uses:

FORMAT 1: TWO-ROW (supermarkets like BINGO, KONZUM, etc.)
Each product takes 2 rows:
  ROW 1: [PRODUCT_CODE] [PRODUCT_NAME]
  ROW 2: [QUANTITY]x [UNIT_PRICE]    [LINE_TOTAL]

How to identify: Look for lines with pattern like "1.000x" or "0.302x" followed by numbers.
The "x" after a decimal number indicates quantity multiplier.

FORMAT 2: ONE-ROW (bakeries, small shops like Pekara KABIL)
Each product is on 1 line:
  [PRODUCT_NAME] [SIZE] [PRICE]

How to identify: NO quantity lines with "Nx" pattern. Products show only name and final price.
Example: "COKOLADNI JASTUCIC 100 G/KOM 1,60E"

=== FORMAT 1: TWO-ROW EXTRACTION (BINGO, KONZUM, etc.) ===

ROW 1: [PRODUCT_CODE] [PRODUCT_NAME]
ROW 2: [QUANTITY]x [UNIT_PRICE]    [LINE_TOTAL]

The second row ALWAYS contains THREE numbers in this order:
- FIRST number: QUANTITY (how many items bought) - format: "N.NNNx" (ends with "x")
- SECOND number: UNIT PRICE (price for 1 item/kg)
- THIRD number: LINE TOTAL (the actual charged amount) - ALWAYS at the END of the line, often ends with "E"

CRITICAL: line_total is ALWAYS the RIGHTMOST/LAST number on the line!
- "5.000x 1.20 6.00E" → qty=5, unit_price=1.20, line_total=6.00 (NOT 1.20!)
- "1.000x 4.75 4.75E" → qty=1, unit_price=4.75, line_total=4.75

VALIDATION: quantity × unit_price should equal line_total (within rounding)

REAL EXAMPLES:
  E10121 KEKS SUHI 300G PLAZMA BAMBI
  1.000x              4.75         4.75E   → qty=1, unit=4.75, total=4.75 ✓

  J10459 SVJEZE BROKULE
  0.302x              7.50         2.27E   → qty=0.302, unit=7.50, total=2.27 (0.302×7.50=2.265≈2.27) ✓

  C00730 COKOLADNI DESERT 28G KINDER M
  5.000x              1.20         6.00E   → qty=5, unit=1.20, total=6.00 ✓

QUANTITY FORMAT: "4.000x" means 4 items, "0.302x" means 0.302 kg
IMPORTANT: You MUST read BOTH rows. Do NOT assume quantity=1!

=== FORMAT 2: ONE-ROW EXTRACTION (Bakeries, small shops) ===

Each line shows: [PRODUCT_NAME] [optional SIZE] [PRICE]

REAL EXAMPLES:
  COKOLADNI JASTUCIC 100 G/KOM 1,60E  → name="Čokoladni jastučić", price=1.60
  LISNATO TIJESTO MALINA - VANILIJA
  110 G/KOM                    1,60E  → name="Lisnato tijesto malina-vanilija", price=1.60
  PIZZA LISNATO TIJESTO 90 G/KOM
                               1,60E  → name="Pizza lisnato tijesto", price=1.60

For one-row format:
- quantity = 1 (assumed, cannot be verified)
- unit_price = line_total (same value)
- No validation possible

ITEM EXTRACTION RULES:
For each line item, extract:
- raw_name: EXACT text as printed on receipt (preserve original, include the product code at start)
- parsed_name: Clean product name with ONLY typo/OCR fixes - DO NOT change meaning:
  * Fix missing Bosnian characters: "COKOLADA" → "Čokolada", "SECER" → "Šećer", "BRASNO" → "Brašno"
  * Fix obvious OCR typos: "UREICA" → "Vrećica", "UBRUS" stays "Ubrus" (don't change to vrećica!)
  * "KECAP" → "Kečap", "MUSLI" → "Müsli"
  * Remove leading product codes from parsed_name
  * Use proper Bosnian characters: č, ć, š, ž, đ
  * Make names human-readable (capitalize properly)
  * IMPORTANT: Do NOT change the product meaning - only fix typos!
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
  * "gorivo" (fuel - benzin, dizel, eurosuper, etc.)
  * "taksa" (taxes/fees like "Posebna taksa na gorivo")
- is_fuel: BOOLEAN - Set to true ONLY for actual fuel purchases (benzin, dizel, eurosuper, premium).
  IMPORTANT: "Posebna taksa na gorivo" and similar tax/fee lines are NOT fuel - set is_fuel=false for those!
- quantity: Number of items - VERY IMPORTANT: check for "N x price" pattern!
- unit: "kom" for pieces, "kg" for weight, "l" for volume
- pack_size: Package size as shown (e.g., "1l", "500g", "400g")
- unit_price: Price per SINGLE unit (the MIDDLE number on the price line)
- line_total: !!!CRITICAL!!! Use the FAR RIGHT number on the price line! NOT the middle number!
  * On "5.000x 1.20 6.00E": line_total = 6.00 (far right), NOT 1.20 (middle)!
  * On "2.000x 2.95 5.90E": line_total = 5.90 (far right), NOT 2.95 (middle)!
  * The far right number should equal qty × unit_price
  * Format: usually ends with "E" like "6.00E" meaning 6.00 KM
  * If you use the middle number, the receipt total won't match!
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
    "receipt_format": "two_row" or "one_row",
    "items": [
        {
            "raw_name": "EXACT TEXT FROM RECEIPT (include product code for two_row format)",
            "parsed_name": "Clean product name",
            "brand": "Brand or UNKNOWN",
            "product_type": "mlijeko, kafa, hljeb, etc.",
            "is_fuel": false,
            "quantity": 1,
            "unit": "kom",
            "pack_size": "500g, 1l, etc.",
            "unit_price": 1.99,
            "line_total": 1.99,
            "size_value": 500,
            "size_unit": "g",
            "validated": true (for two_row: qty×unit_price≈line_total, for one_row: always false)
        }
    ]
}"""

            # Call appropriate API based on model
            # Track timing and usage for logging
            total_input_tokens = 0
            total_output_tokens = 0
            total_response_time_ms = 0
            actual_model = model

            # Handle split vs single image
            if is_split and isinstance(image_data, dict) and image_data.get('is_split'):
                # Split image: process top and bottom halves separately
                current_app.logger.info(f"Processing split receipt {receipt_id} with {len(image_data.get('images', []))} parts")

                top_prompt = """⚠️ THIS IS THE **TOP HALF** OF A SPLIT RECEIPT (the header section).

The TOP of a Bosnian receipt ALWAYS contains:
1. **STORE NAME** - The business name (e.g., BINGO, KONZUM, TROPIC) - EXTRACT THIS!
2. **STORE ADDRESS** - The store location with street, city, postal code
3. **JIB** - 13-digit tax ID
4. **PIB** - 12-digit number starting with 4
5. **IBFM** - Fiscal module ID
6. **Receipt date and serial number**
7. First portion of items

CRITICAL: The store name is at the VERY TOP of the receipt - don't confuse it with item names below!
Look for the company/business name in the first few lines, NOT in the item list.

Return ONLY valid JSON. Extract store_name, store_address, jib, pib, ibfm, receipt_serial_number, receipt_date, and any items visible."""

                bottom_prompt = """⚠️ THIS IS THE **BOTTOM HALF** OF A SPLIT RECEIPT (the footer/totals section).

The BOTTOM of a Bosnian receipt ALWAYS contains:
1. **Remaining items** - Continue extracting items from where the top half ended
2. **TOTAL AMOUNT** - CRITICAL: Read the correct line!
3. **Payment method** - Gotovina (cash), Kartica (card)

⚠️⚠️⚠️ CRITICAL - BOSNIAN RECEIPT VAT STRUCTURE ⚠️⚠️⚠️
Bosnian receipts show THREE amounts at the bottom - you MUST use the CORRECT one:

  OSN. E: 70.99   ← BASE AMOUNT (before tax) - DO NOT USE THIS!
  PDV U:  12.07   ← VAT AMOUNT (17% tax)
  TOTAL:  83.06   ← FINAL AMOUNT (what customer pays) - USE THIS!

ALWAYS look for "TOTAL:" or "UKUPNO:" line - this is the FINAL amount including VAT!
NEVER use "OSN." or "OSN. E:" - that's just the base amount before 17% VAT!

The total_amount should be approximately: base + 17% = final
Example: 70.99 + 12.07 = 83.06 KM

DO NOT extract store_name from this section - it should come from the TOP half.
Focus on: items in this portion and the total_amount (from TOTAL: line!).

Return ONLY valid JSON with items array and total_amount."""

                parts_results = []
                for i, img_base64 in enumerate(image_data.get('images', [])):
                    part_prompt = top_prompt if i == 0 else bottom_prompt
                    result_text, in_tokens, out_tokens, resp_time = call_ocr_api(
                        img_base64, system_prompt, part_prompt, model, is_claude
                    )
                    total_input_tokens += in_tokens
                    total_output_tokens += out_tokens
                    total_response_time_ms += resp_time

                    # Parse result
                    part_result = json.loads(result_text)
                    parts_results.append(part_result)
                    current_app.logger.info(f"Part {i+1}: {len(part_result.get('items', []))} items extracted")

                # Merge results
                if len(parts_results) >= 2:
                    result = merge_split_ocr_results(parts_results[0], parts_results[1])
                else:
                    result = parts_results[0] if parts_results else {}

            else:
                # Single image processing
                image_base64 = image_data if isinstance(image_data, str) else image_data.get('images', [''])[0]
                user_prompt = "Extract all data from this receipt image. Return ONLY valid JSON, no markdown formatting."

                result_text, total_input_tokens, total_output_tokens, total_response_time_ms = call_ocr_api(
                    image_base64, system_prompt, user_prompt, model, is_claude
                )
                result = json.loads(result_text)

            # Log API usage (total across all parts if split)
            try:
                provider = 'anthropic' if is_claude else 'openai'
                estimated_cost = APIUsageLog.calculate_cost(
                    provider, actual_model, total_input_tokens, total_output_tokens
                )
                usage_log = APIUsageLog(
                    provider=provider,
                    model=actual_model,
                    feature='receipt_ocr',
                    receipt_id=receipt_id,
                    user_id=receipt.user_id,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    total_tokens=total_input_tokens + total_output_tokens,
                    estimated_cost_cents=Decimal(str(estimated_cost)) if estimated_cost else None,
                    success=True,
                    response_time_ms=total_response_time_ms
                )
                db.session.add(usage_log)
                db.session.commit()
            except Exception as log_error:
                current_app.logger.warning(f"Failed to log API usage: {log_error}")

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
            # Note: We calculate total_amount from items, not from OCR
            # This is more reliable and allows partial receipt uploads

            # Check for duplicates now that we have extracted data
            duplicate = check_duplicate_receipt(
                receipt.user_id,
                receipt.jib,
                receipt.receipt_serial_number,
                receipt.receipt_date,
                exclude_receipt_id=receipt.id
            )
            if duplicate and duplicate.id != receipt.id:
                # Mark as duplicate - user can delete manually if they want
                receipt.processing_status = 'duplicate'
                receipt.processing_error = f'Ovaj račun je već učitan. Originalni račun ima ID: {duplicate.id}.'
                receipt.duplicate_of_id = duplicate.id
                db.session.commit()
                current_app.logger.info(f"Receipt {receipt.id} marked as duplicate of {duplicate.id}")
                return

            # Create receipt items and calculate total from items
            items = result.get('items', [])
            calculated_total = Decimal('0')
            for item_data in items:
                line_total = Decimal(str(item_data['line_total'])) if item_data.get('line_total') else None
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
                    line_total=line_total,
                    size_value=Decimal(str(item_data['size_value'])) if item_data.get('size_value') else None,
                    size_unit=item_data.get('size_unit')
                )
                db.session.add(item)
                # Add to calculated total
                if line_total:
                    calculated_total += line_total

            # Set total_amount from sum of items (not from OCR)
            if calculated_total > 0:
                receipt.total_amount = calculated_total

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

        # Prepare image(s) for OCR - splits tall images into top/bottom halves
        image_prep = prepare_images_for_ocr(file_data)
        is_split = image_prep.get('is_split', False)

        # Upload combined/cropped image to S3 for debugging (shows what OCR analyzes)
        cropped_url = upload_cropped_receipt_image(image_prep['combined_bytes'], user.id, receipt.id)
        receipt.cropped_image_url = cropped_url

        # If split, upload individual parts for admin debugging
        if is_split and 'parts' in image_prep:
            for part in image_prep['parts']:
                if part['position'] == 'top':
                    top_url = upload_split_part_image(part['bytes'], user.id, receipt.id, 'top')
                    receipt.cropped_top_url = top_url
                elif part['position'] == 'bottom':
                    bottom_url = upload_split_part_image(part['bytes'], user.id, receipt.id, 'bottom')
                    receipt.cropped_bottom_url = bottom_url

        db.session.commit()

        current_app.logger.info(f"Receipt {receipt.id}: is_split={is_split}, parts={len(image_prep.get('images', []))}")

        # Start background processing
        app_context = current_app._get_current_object().app_context()
        thread = threading.Thread(
            target=process_receipt_ocr,
            args=(receipt.id, image_prep, app_context),
            kwargs={'is_split': is_split}
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

        # Prepare image(s) for OCR - splits tall images
        image_prep = prepare_images_for_ocr(image_data)
        is_split = image_prep.get('is_split', False)

        # Start background processing
        app_context = current_app._get_current_object().app_context()
        thread = threading.Thread(
            target=process_receipt_ocr,
            args=(receipt.id, image_prep, app_context),
            kwargs={'is_split': is_split}
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


@receipts_bp.route('/api/admin/receipts/<int:receipt_id>/reprocess', methods=['POST'])
@jwt_admin_required
def admin_reprocess_receipt(receipt_id):
    """Admin: Re-run OCR on any receipt with model selection"""
    receipt = Receipt.query.get(receipt_id)
    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    # Get model from request body
    data = request.get_json() or {}
    model = data.get('model', 'claude-haiku')

    # Validate model
    allowed_models = ['gpt-4o-mini', 'gpt-4o', 'claude-sonnet', 'claude-haiku']
    if model not in allowed_models:
        return jsonify({'error': f'Invalid model. Allowed: {allowed_models}'}), 400

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

        # Prepare image(s) for OCR - splits tall images
        image_prep = prepare_images_for_ocr(image_data)
        is_split = image_prep.get('is_split', False)

        # Start background processing with specified model
        app_context = current_app._get_current_object().app_context()
        thread = threading.Thread(
            target=process_receipt_ocr,
            args=(receipt.id, image_prep, app_context, model),
            kwargs={'is_split': is_split}
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'Reprocessing started with {model}'
        })

    except Exception as e:
        current_app.logger.error(f"Error reprocessing receipt: {e}")
        return jsonify({'error': 'Failed to reprocess receipt'}), 500


# ==================== API USAGE ENDPOINTS ====================

@receipts_bp.route('/api/admin/api-usage', methods=['GET'])
@jwt_admin_required
def admin_get_api_usage():
    """Admin: Get API usage logs with pagination"""
    from sqlalchemy import func

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    days = request.args.get('days', 30, type=int)
    provider = request.args.get('provider')  # Filter by provider
    model_filter = request.args.get('model')  # Filter by model

    # Date filter
    start_date = datetime.now() - timedelta(days=days)

    query = APIUsageLog.query.filter(APIUsageLog.created_at >= start_date)

    if provider:
        query = query.filter(APIUsageLog.provider == provider)
    if model_filter:
        query = query.filter(APIUsageLog.model == model_filter)

    query = query.order_by(APIUsageLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@receipts_bp.route('/api/admin/api-usage/stats', methods=['GET'])
@jwt_admin_required
def admin_get_api_usage_stats():
    """Admin: Get aggregated API usage statistics"""
    from sqlalchemy import func

    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)

    # Total calls and tokens
    totals = db.session.query(
        func.count(APIUsageLog.id).label('total_calls'),
        func.sum(APIUsageLog.input_tokens).label('total_input_tokens'),
        func.sum(APIUsageLog.output_tokens).label('total_output_tokens'),
        func.sum(APIUsageLog.total_tokens).label('total_tokens'),
        func.sum(APIUsageLog.estimated_cost_cents).label('total_cost_cents'),
        func.avg(APIUsageLog.response_time_ms).label('avg_response_time')
    ).filter(
        APIUsageLog.created_at >= start_date
    ).first()

    # By provider
    by_provider = db.session.query(
        APIUsageLog.provider,
        func.count(APIUsageLog.id).label('calls'),
        func.sum(APIUsageLog.total_tokens).label('tokens'),
        func.sum(APIUsageLog.estimated_cost_cents).label('cost_cents')
    ).filter(
        APIUsageLog.created_at >= start_date
    ).group_by(APIUsageLog.provider).all()

    # By model
    by_model = db.session.query(
        APIUsageLog.model,
        APIUsageLog.provider,
        func.count(APIUsageLog.id).label('calls'),
        func.sum(APIUsageLog.total_tokens).label('tokens'),
        func.sum(APIUsageLog.estimated_cost_cents).label('cost_cents'),
        func.avg(APIUsageLog.response_time_ms).label('avg_response_time')
    ).filter(
        APIUsageLog.created_at >= start_date
    ).group_by(APIUsageLog.model, APIUsageLog.provider).all()

    # Daily breakdown
    daily_stats = db.session.query(
        func.date(APIUsageLog.created_at).label('date'),
        func.count(APIUsageLog.id).label('calls'),
        func.sum(APIUsageLog.total_tokens).label('tokens'),
        func.sum(APIUsageLog.estimated_cost_cents).label('cost_cents')
    ).filter(
        APIUsageLog.created_at >= start_date
    ).group_by(func.date(APIUsageLog.created_at)).order_by(func.date(APIUsageLog.created_at)).all()

    # Success rate
    success_count = APIUsageLog.query.filter(
        APIUsageLog.created_at >= start_date,
        APIUsageLog.success == True
    ).count()
    total_count = totals.total_calls or 0
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0

    return jsonify({
        'period_days': days,
        'totals': {
            'calls': totals.total_calls or 0,
            'input_tokens': int(totals.total_input_tokens or 0),
            'output_tokens': int(totals.total_output_tokens or 0),
            'total_tokens': int(totals.total_tokens or 0),
            'cost_cents': float(totals.total_cost_cents or 0),
            'cost_usd': round(float(totals.total_cost_cents or 0) / 100, 4),
            'avg_response_time_ms': int(totals.avg_response_time or 0),
            'success_rate': round(success_rate, 1)
        },
        'by_provider': [
            {
                'provider': p.provider,
                'calls': p.calls,
                'tokens': int(p.tokens or 0),
                'cost_cents': float(p.cost_cents or 0),
                'cost_usd': round(float(p.cost_cents or 0) / 100, 4)
            }
            for p in by_provider
        ],
        'by_model': [
            {
                'model': m.model,
                'provider': m.provider,
                'calls': m.calls,
                'tokens': int(m.tokens or 0),
                'cost_cents': float(m.cost_cents or 0),
                'cost_usd': round(float(m.cost_cents or 0) / 100, 4),
                'avg_response_time_ms': int(m.avg_response_time or 0)
            }
            for m in by_model
        ],
        'daily': [
            {
                'date': str(d.date),
                'calls': d.calls,
                'tokens': int(d.tokens or 0),
                'cost_cents': float(d.cost_cents or 0)
            }
            for d in daily_stats
        ]
    })

