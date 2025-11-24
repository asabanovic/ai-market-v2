"""
Automatic Vectorization for Products
Triggers embedding generation when products are created or updated
"""
import os
import logging
import hashlib
from typing import Optional
from openai import OpenAI
from datetime import datetime
from app import db
from models import Product, ProductEmbedding

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def compute_product_hash(product: Product) -> str:
    """
    Compute a hash of product content to detect changes

    Args:
        product: Product object

    Returns:
        SHA256 hash of product content
    """
    # Combine only fields that affect the embedding (no prices/city)
    content = f"{product.title}|{product.category}"
    if product.tags:
        content += f"|{','.join(sorted(product.tags))}"
    if product.enriched_description:
        content += f"|{product.enriched_description}"

    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def build_embedding_text(product: Product) -> str:
    """
    Build the text to be embedded for a product.

    Focuses on semantic meaning - no prices or numbers to avoid
    polluting the embedding with non-semantic information.

    Args:
        product: Product object

    Returns:
        Text string for embedding
    """
    parts = []

    # Product title (most important)
    parts.append(product.title)

    # Category
    if product.category:
        parts.append(f"Kategorija: {product.category}")

    # Tags (semantic keywords)
    if product.tags:
        parts.append(f"Ključne riječi: {', '.join(product.tags)}")

    # Enriched description (most valuable for semantic search)
    if product.enriched_description:
        parts.append(product.enriched_description)

    return " ".join(parts)


def vectorize_product(product: Product, force: bool = False) -> Optional[ProductEmbedding]:
    """
    Generate and store embedding for a product

    Args:
        product: Product object to vectorize
        force: Force re-vectorization even if content hasn't changed

    Returns:
        ProductEmbedding object if successful, None otherwise
    """
    try:
        # Compute content hash
        current_hash = compute_product_hash(product)

        # Check if we need to update embedding
        existing = ProductEmbedding.query.filter_by(product_id=product.id).first()

        if not force and existing and existing.content_hash == current_hash:
            logger.info(f"Product {product.id} embedding is up to date, skipping")
            return existing

        # Build text for embedding
        embedding_text = build_embedding_text(product)

        # Generate embedding using OpenAI
        logger.info(f"Generating embedding for product {product.id}: {product.title}")
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=embedding_text
        )

        embedding_vector = response.data[0].embedding

        # Create or update ProductEmbedding
        if existing:
            # Update existing
            existing.embedding = embedding_vector
            existing.embedding_text = embedding_text
            existing.model_version = "text-embedding-3-small"
            existing.content_hash = current_hash
            existing.updated_at = datetime.now()
            logger.info(f"Updated embedding for product {product.id}")
        else:
            # Create new
            existing = ProductEmbedding(
                product_id=product.id,
                embedding=embedding_vector,
                embedding_text=embedding_text,
                model_version="text-embedding-3-small",
                content_hash=current_hash
            )
            db.session.add(existing)
            logger.info(f"Created new embedding for product {product.id}")

        # Update product content hash
        product.content_hash = current_hash

        # Commit changes
        db.session.commit()

        return existing

    except Exception as e:
        logger.error(f"Failed to vectorize product {product.id}: {e}", exc_info=True)
        db.session.rollback()
        return None


def auto_vectorize_on_save(product: Product) -> None:
    """
    Automatically vectorize a product after it's saved (created or updated)

    This function should be called after a product is added/updated in the database.

    Args:
        product: Product object that was just saved
    """
    try:
        vectorize_product(product, force=False)
        logger.info(f"Auto-vectorized product {product.id} after save")
    except Exception as e:
        logger.error(f"Auto-vectorization failed for product {product.id}: {e}")


def schedule_async_vectorization(product_ids: list[int], force: bool = False) -> None:
    """
    Schedule vectorization to run in the background (async)

    Args:
        product_ids: List of product IDs to vectorize
        force: Force re-vectorization even if content hasn't changed
    """
    import threading
    from flask import current_app

    def run_in_background(app, product_ids, force):
        with app.app_context():
            try:
                logger.info(f"Starting background vectorization for {len(product_ids)} products")
                stats = batch_vectorize_products(product_ids=product_ids, force=force)
                logger.info(f"Background vectorization complete: {stats}")
            except Exception as e:
                logger.error(f"Background vectorization failed: {e}", exc_info=True)

    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_in_background,
        args=(app, product_ids, force),
        daemon=True
    )
    thread.start()
    logger.info(f"Scheduled background vectorization for {len(product_ids)} products")


def batch_vectorize_products(product_ids: list[int] = None, force: bool = False) -> dict:
    """
    Vectorize multiple products in a batch

    Args:
        product_ids: List of product IDs to vectorize (None = all products)
        force: Force re-vectorization even if content hasn't changed

    Returns:
        Dict with statistics: {'processed': X, 'succeeded': Y, 'failed': Z}
    """
    stats = {'processed': 0, 'succeeded': 0, 'failed': 0}

    try:
        # Get products to vectorize
        if product_ids:
            products = Product.query.filter(Product.id.in_(product_ids)).all()
        else:
            products = Product.query.all()

        logger.info(f"Batch vectorizing {len(products)} products (force={force})")

        for product in products:
            stats['processed'] += 1
            result = vectorize_product(product, force=force)
            if result:
                stats['succeeded'] += 1
            else:
                stats['failed'] += 1

        logger.info(f"Batch vectorization complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Batch vectorization error: {e}", exc_info=True)
        return stats
