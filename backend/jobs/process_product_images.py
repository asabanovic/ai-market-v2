#!/usr/bin/env python3
"""
Process user-uploaded product images using AI Vision.
Extracts product names and adds them to user preferences.

Schedule: Every 5 minutes
Command: python jobs/process_product_images.py
"""

import os
import sys
import base64
import requests
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, UserProductImage, UserTrackedProduct
from sqlalchemy.orm.attributes import flag_modified
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Max images to process per run
MAX_IMAGES_PER_RUN = 10


def extract_product_name_from_image(image_url: str) -> dict:
    """
    Use OpenAI Vision to extract product name from image.

    Args:
        image_url: URL of the product image

    Returns:
        dict with 'product_name', 'price' (if visible), 'confidence'
    """
    if not openai_client:
        logger.error("OpenAI API key not configured")
        return None

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a product recognition assistant for a Bosnian grocery shopping app.

Analyze the image and extract:
1. Product name in Bosnian (or transliterate if foreign brand)
2. Price if visible on a price tag
3. Your confidence level (high/medium/low)

Return ONLY valid JSON:
{
  "product_name": "string - short product name, e.g. 'Coca Cola 2L', 'Milka čokolada', 'Piletina file'",
  "price": number or null,
  "confidence": "high" | "medium" | "low",
  "category": "optional category hint"
}

Rules:
- Keep product names short and searchable (2-5 words max)
- Use common Bosnian names for products
- If you can't identify the product, set product_name to null
- If price is not visible, set price to null"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What product is shown in this image? Extract the product name."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "low"  # Use low detail for cost efficiency
                            }
                        }
                    ]
                }
            ],
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        import json
        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        result_text = result_text.strip()

        result = json.loads(result_text)
        return result

    except Exception as e:
        logger.error(f"OpenAI Vision error: {e}")
        return None


def trigger_user_scan(user_id: str):
    """
    Trigger a product scan for a specific user after adding a new tracked product.
    This runs the scan immediately so the user sees matching products right away.
    """
    try:
        from jobs.scan_user_products import scan_single_user

        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for scan trigger")
            return

        logger.info(f"Triggering scan for user {user_id} after product image upload")
        result = scan_single_user(user)

        if result:
            total, new_count, discount_count = result
            logger.info(f"Scan complete for user {user_id}: {total} products, {new_count} new")
        else:
            logger.info(f"No products to scan for user {user_id}")

    except Exception as e:
        logger.error(f"Error triggering scan for user {user_id}: {e}")


def add_to_user_preferences(user_id: str, product_name: str) -> bool:
    """
    Add product name to user's grocery_interests preferences and tracked products.

    Args:
        user_id: User ID
        product_name: Product name to add

    Returns:
        True if successful
    """
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return False

        product_clean = product_name.strip()
        product_lower = product_clean.lower()

        # 1. Add to grocery_interests preferences
        if not user.preferences:
            user.preferences = {}
        elif not isinstance(user.preferences, dict):
            user.preferences = {}

        interests = user.preferences.get('grocery_interests', [])
        if not isinstance(interests, list):
            interests = []

        existing_lower = [i.lower().strip() for i in interests]
        if product_lower not in existing_lower:
            interests.append(product_clean)
            user.preferences['grocery_interests'] = interests
            flag_modified(user, 'preferences')
            logger.info(f"Added '{product_clean}' to user {user_id} preferences")

        # 2. Add to tracked products (for /moji-proizvodi)
        existing_tracked = UserTrackedProduct.query.filter_by(
            user_id=user_id,
            search_term=product_lower
        ).first()

        if not existing_tracked:
            tracked = UserTrackedProduct(
                user_id=user_id,
                search_term=product_lower,
                original_text=product_clean,
                source='product_image',
                is_active=True
            )
            db.session.add(tracked)
            logger.info(f"Added '{product_clean}' to user {user_id} tracked products")

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error adding to preferences: {e}")
        db.session.rollback()
        return False


def process_pending_images():
    """
    Process all pending product images.
    """
    with app.app_context():
        logger.info("Starting product image processing")

        # Get pending images
        pending_images = UserProductImage.query.filter_by(
            status='pending'
        ).order_by(UserProductImage.created_at.asc()).limit(MAX_IMAGES_PER_RUN).all()

        if not pending_images:
            logger.info("No pending images to process")
            return 0, 0

        logger.info(f"Found {len(pending_images)} pending images")

        processed = 0
        failed = 0

        for image in pending_images:
            try:
                # Mark as processing
                image.status = 'processing'
                db.session.commit()

                logger.info(f"Processing image {image.id} for user {image.user_id}")

                # Extract product info using AI Vision
                result = extract_product_name_from_image(image.image_url)

                if result and result.get('product_name'):
                    product_name = result['product_name']

                    # Update image record
                    image.extracted_name = product_name
                    if result.get('price'):
                        image.extracted_price = result['price']
                    image.extracted_data = result
                    image.status = 'processed'
                    image.processed_at = datetime.now()

                    # Add to user preferences
                    add_to_user_preferences(image.user_id, product_name)

                    # Trigger a scan for this user to find matching products
                    trigger_user_scan(image.user_id)

                    processed += 1
                    logger.info(f"Successfully processed image {image.id}: {product_name}")
                else:
                    # Could not extract product name
                    image.status = 'failed'
                    image.extracted_data = {'error': 'Could not identify product'}
                    image.processed_at = datetime.now()
                    failed += 1
                    logger.warning(f"Could not identify product in image {image.id}")

                db.session.commit()

            except Exception as e:
                logger.error(f"Error processing image {image.id}: {e}")
                image.status = 'failed'
                image.extracted_data = {'error': str(e)}
                image.processed_at = datetime.now()
                db.session.commit()
                failed += 1

        logger.info(f"Image processing complete: {processed} processed, {failed} failed")
        return processed, failed


if __name__ == '__main__':
    logger.info("Running product image processor")
    processed, failed = process_pending_images()
    logger.info(f"Done: {processed} processed, {failed} failed")
