#!/usr/bin/env python3
"""
Social media post generator job.
Generates scheduled posts for the next 5 days with top discount products.

Schedule: Daily at midnight (00:05 UTC)
Command: python jobs/social_media_generator.py
"""

import os
import sys
from datetime import datetime, date, timedelta
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Product, Business, SocialMediaPost

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
POSTS_PER_DAY = 4
PRODUCTS_PER_POST = 5
DAYS_TO_SCHEDULE = 5

# Posting times in UTC (Bosnia is UTC+1, so these are 9am, 12pm, 3pm, 6pm local)
POST_HOURS_UTC = [8, 11, 14, 17]


def get_top_discounts(limit: int = 5, exclude_product_ids: list = None) -> list:
    """
    Get products with highest discount percentage.

    Args:
        limit: Number of products to return
        exclude_product_ids: Product IDs to exclude (already used in recent posts)

    Returns:
        List of Product objects
    """
    today = date.today()

    query = Product.query.join(Business).filter(
        Product.discount_price.isnot(None),
        Product.base_price.isnot(None),
        Product.discount_price < Product.base_price,
        Product.base_price > 0,
        # Only active discounts (not expired)
        db.or_(
            Product.expires.is_(None),
            Product.expires >= today
        )
    )

    # Exclude already used products
    if exclude_product_ids:
        query = query.filter(~Product.id.in_(exclude_product_ids))

    # Calculate discount percentage and order by it
    # (base_price - discount_price) / base_price * 100
    query = query.order_by(
        ((Product.base_price - Product.discount_price) / Product.base_price).desc()
    )

    return query.limit(limit).all()


def get_recently_posted_product_ids(hours: int = 48) -> list:
    """
    Get product IDs that were posted recently OR are scheduled for future posts.
    This prevents duplicating products across posts.

    Args:
        hours: Number of hours to look back for published posts

    Returns:
        List of product IDs
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Get products from recent published posts AND all scheduled posts
    recent_posts = SocialMediaPost.query.filter(
        db.or_(
            SocialMediaPost.created_at >= cutoff,  # Recent posts
            SocialMediaPost.status == 'scheduled'   # All scheduled posts
        )
    ).all()

    product_ids = []
    for post in recent_posts:
        if post.products_data:
            for product in post.products_data:
                if 'id' in product:
                    product_ids.append(product['id'])

    return list(set(product_ids))


import random

# Hook templates - {savings} = ušteda u KM, {pct} = procenat, {product} = ime proizvoda
HOOK_TEMPLATES = [
    "Uštedi {savings} KM na ovim proizvodima!",
    "{product} je na -{pct}% - ne propusti!",
    "Znaš li da {product} košta samo {price} KM?",
    "Ovo moraš vidjeti: {product} UPOLA CIJENE",
    "Najveći popusti danas: do -{pct}%",
    "Ako kupuješ {product}, ovo ti treba!",
    "{pct}% popusta na {product}!",
    "Uštedi danas: {product} sa {savings} KM popusta",
]


def generate_post_content(products: list) -> str:
    """
    Generate engaging Bosnian post text with hook.

    Args:
        products: List of Product objects

    Returns:
        Formatted post text
    """
    if not products:
        return ""

    # Get the product with biggest discount for the hook
    best_product = max(products, key=lambda p: (p.base_price - p.discount_price) / p.base_price)
    best_pct = round((best_product.base_price - best_product.discount_price) / best_product.base_price * 100)
    best_savings = best_product.base_price - best_product.discount_price

    # Truncate product name for hook
    product_name = best_product.title
    if len(product_name) > 30:
        product_name = product_name[:27] + "..."

    # Generate hook
    hook_template = random.choice(HOOK_TEMPLATES)
    hook = hook_template.format(
        savings=f"{best_savings:.2f}",
        pct=best_pct,
        product=product_name,
        price=f"{best_product.discount_price:.2f}"
    )

    lines = [hook]
    lines.append("")

    # Group products by store
    stores = {}
    for product in products:
        store_name = product.business.name if product.business else "Nepoznata trgovina"
        if store_name not in stores:
            stores[store_name] = []
        stores[store_name].append(product)

    for store_name, store_products in stores.items():
        lines.append(f"[ {store_name.upper()} ]")
        for product in store_products:
            discount_pct = round((product.base_price - product.discount_price) / product.base_price * 100)
            savings = product.base_price - product.discount_price

            # Truncate long titles
            title = product.title
            if len(title) > 40:
                title = title[:37] + "..."

            lines.append(f"• {title}")
            lines.append(f"  {product.discount_price:.2f} KM (ušteda {savings:.2f} KM) -{discount_pct}%")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Želiš ovakve akcije direktno u inbox?")
    lines.append("Registruj se za 10 sekundi i napiši šta kupuješ - mi pratimo cijene umjesto tebe!")
    lines.append("")
    lines.append("popust.ba")

    return "\n".join(lines)


def get_product_image_url(products: list) -> str:
    """
    Get the image URL for the post.
    Uses the first product's image if available.

    Args:
        products: List of Product objects

    Returns:
        Image URL or None
    """
    for product in products:
        if product.image_path:
            # Assume images are served from the same domain
            # Adjust this based on your actual image hosting
            if product.image_path.startswith('http'):
                return product.image_path
            else:
                # Construct full URL for Railway deployment
                base_url = os.environ.get('FRONTEND_URL', 'https://popust.ba')
                return f"{base_url}{product.image_path}"
    return None


def products_to_data(products: list) -> list:
    """
    Convert Product objects to JSON-serializable data.

    Args:
        products: List of Product objects

    Returns:
        List of dicts with product data
    """
    base_url = os.environ.get('FRONTEND_URL', 'https://popust.ba')

    data = []
    for product in products:
        discount_pct = round((product.base_price - product.discount_price) / product.base_price * 100)

        # Build full image URL
        image_url = None
        if product.image_path:
            if product.image_path.startswith('http'):
                image_url = product.image_path
            else:
                image_url = f"{base_url}{product.image_path}"

        data.append({
            'id': product.id,
            'title': product.title,
            'store': product.business.name if product.business else None,
            'base_price': float(product.base_price),
            'discount_price': float(product.discount_price),
            'discount_pct': discount_pct,
            'image_url': image_url
        })
    return data


def generate_scheduled_posts():
    """
    Generate social media posts for the next 5 days.
    Creates posts for each time slot if they don't already exist.
    """
    with app.app_context():
        logger.info("Starting social media post generation")

        now = datetime.utcnow()
        created_count = 0
        skipped_count = 0

        # Get recently posted products to avoid repetition
        recent_product_ids = get_recently_posted_product_ids(hours=48)
        logger.info(f"Excluding {len(recent_product_ids)} recently posted products")

        for day_offset in range(DAYS_TO_SCHEDULE):
            target_date = date.today() + timedelta(days=day_offset)

            for hour in POST_HOURS_UTC:
                scheduled_time = datetime(
                    target_date.year,
                    target_date.month,
                    target_date.day,
                    hour, 0, 0
                )

                # Skip if already exists
                existing = SocialMediaPost.query.filter_by(
                    scheduled_time=scheduled_time
                ).first()
                if existing:
                    skipped_count += 1
                    continue

                # Skip if in the past
                if scheduled_time < now:
                    skipped_count += 1
                    continue

                # Get top discounts
                products = get_top_discounts(
                    limit=PRODUCTS_PER_POST,
                    exclude_product_ids=recent_product_ids
                )

                if len(products) < PRODUCTS_PER_POST:
                    # If not enough products without exclusions, get any top discounts
                    products = get_top_discounts(limit=PRODUCTS_PER_POST)

                if not products:
                    logger.warning(f"No products found for {scheduled_time}")
                    continue

                # Generate content
                content = generate_post_content(products)
                image_url = get_product_image_url(products)
                products_data = products_to_data(products)

                # Create post
                post = SocialMediaPost(
                    scheduled_time=scheduled_time,
                    status='scheduled',
                    content=content,
                    image_url=image_url,
                    products_data=products_data
                )
                db.session.add(post)
                created_count += 1

                # Add these products to exclusion list for next slots
                for p in products:
                    recent_product_ids.append(p.id)

                logger.info(f"Created post for {scheduled_time}")

        db.session.commit()
        logger.info(f"Post generation complete: {created_count} created, {skipped_count} skipped")

        return created_count, skipped_count


def regenerate_single_post(post_id: int) -> bool:
    """
    Regenerate content for a single scheduled post.

    Args:
        post_id: ID of the post to regenerate

    Returns:
        True if successful, False otherwise
    """
    with app.app_context():
        post = SocialMediaPost.query.get(post_id)
        if not post:
            logger.error(f"Post {post_id} not found")
            return False

        if post.status != 'scheduled':
            logger.error(f"Cannot regenerate post {post_id} - status is {post.status}")
            return False

        # Get current product IDs to exclude them
        current_ids = [p['id'] for p in post.products_data] if post.products_data else []

        # Get new products
        products = get_top_discounts(
            limit=PRODUCTS_PER_POST,
            exclude_product_ids=current_ids
        )

        if not products:
            logger.warning("No alternative products found")
            return False

        # Update post
        post.content = generate_post_content(products)
        post.image_url = get_product_image_url(products)
        post.products_data = products_to_data(products)
        post.updated_at = datetime.utcnow()

        db.session.commit()
        logger.info(f"Regenerated post {post_id}")
        return True


if __name__ == '__main__':
    logger.info("Running social media post generator")
    generate_scheduled_posts()
    logger.info("Done")
