#!/usr/bin/env python3
"""
Production-ready script to generate and refresh product embeddings for semantic search.

This script:
1. Enriches product data with AI-generated descriptions
2. Generates vector embeddings using OpenAI's text-embedding-3-small model
3. Stores embeddings in a separate product_embeddings table for performance
4. Supports both full rebuild and partial backfill
5. Includes batching, retry logic, and comprehensive logging
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('refresh_embeddings.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Validate environment variables
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set")
    sys.exit(1)

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set")
    sys.exit(1)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def enrich_product_data(product: Dict) -> Dict[str, str]:
    """
    Generate enriched product data for better semantic search.

    Creates:
    1. enriched_description: Rich description explaining what it is, what it's used for,
       when/why to use it, and target customer
    2. embedding_text: Optimized text for semantic search focusing on purpose,
       sensory traits, and context

    Args:
        product: Dictionary containing product data (name, description, category, etc.)

    Returns:
        Dictionary with 'enriched_description' and 'embedding_text' keys
    """
    try:
        name = product.get('name', '') or product.get('title', '')
        description = product.get('description', '') or ''
        category = product.get('category', '') or 'Ostalo'

        # Build context for enrichment
        context = f"Proizvod: {name}\n"
        if description:
            context += f"Opis: {description}\n"
        context += f"Kategorija: {category}"

        # Generate enriched description using GPT
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ti si pomoćnik koji kreira obogaćene opise proizvoda za bosnijski marketplace. "
                                 "Kreiraj kratki, informativan opis koji objašnjava šta je proizvod, za šta se koristi, "
                                 "kada i zašto bi ga neko koristio, i ko je ciljna grupa kupaca. "
                                 "Budi koncizan (2-3 rečenice) i fokusiraj se na korisnost proizvoda."
                    },
                    {
                        "role": "user",
                        "content": f"Kreiraj obogaćeni opis za:\n{context}"
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )
            enriched_description = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Could not generate enriched description for product {product.get('id')}: {e}")
            enriched_description = description or name

        # Create embedding text optimized for semantic search
        # Focus on purpose, sensory traits, context - avoid prices and store names
        embedding_parts = [name]

        if enriched_description:
            embedding_parts.append(enriched_description)

        # Add category context
        embedding_parts.append(f"Kategorija: {category}")

        # Combine into embedding text (keep under 100 tokens)
        embedding_text = ". ".join(embedding_parts)

        # Truncate if too long (rough estimate: ~4 chars per token)
        max_chars = 400
        if len(embedding_text) > max_chars:
            embedding_text = embedding_text[:max_chars] + "..."

        return {
            'enriched_description': enriched_description,
            'embedding_text': embedding_text
        }

    except Exception as e:
        logger.error(f"Error enriching product data for product {product.get('id')}: {e}")
        # Return minimal fallback
        name = product.get('name', '') or product.get('title', '')
        return {
            'enriched_description': name,
            'embedding_text': name
        }


def generate_embedding_with_retry(text: str, retries: int = MAX_RETRIES) -> Optional[List[float]]:
    """
    Generate embedding with retry logic for transient errors.

    Args:
        text: Text to generate embedding for
        retries: Number of retry attempts

    Returns:
        List of floats representing the embedding vector, or None if all retries fail
    """
    for attempt in range(retries):
        try:
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding

        except RateLimitError as e:
            logger.warning(f"Rate limit error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                sleep_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.info(f"Waiting {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
            else:
                logger.error("Max retries reached for rate limit error")
                return None

        except APIConnectionError as e:
            logger.warning(f"API connection error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached for connection error")
                return None

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {e}")
            return None

    return None


def refresh_product_embeddings(full_rebuild: bool = False, product_ids: List[int] = None) -> Dict[str, int]:
    """
    Refresh product embeddings in the database using hash-based change detection.

    This function:
    1. Selects products that need embeddings based on content_hash changes
    2. Enriches product data with AI-generated descriptions
    3. Generates vector embeddings using OpenAI
    4. Upserts results into product_embeddings table with content_hash
    5. Updates enriched_description in products table

    Args:
        full_rebuild: If True, regenerate embeddings for all products.
                     If False (default), only process products with changed content or no embeddings.
        product_ids: Optional list of specific product IDs to process. Overrides full_rebuild.

    Returns:
        Dictionary with statistics: {'processed': int, 'succeeded': int, 'failed': int}
    """
    stats = {'processed': 0, 'succeeded': 0, 'failed': 0}

    logger.info(f"Starting embedding refresh (full_rebuild={full_rebuild}, product_ids={product_ids})...")

    try:
        # Connect to database
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Select products that need embeddings based on hash or specific IDs
                if product_ids:
                    logger.info(f"Processing specific products: {product_ids}")
                    placeholders = ','.join(['%s'] * len(product_ids))
                    cur.execute(f"""
                        SELECT p.id, p.title, p.enriched_description, p.category,
                               p.base_price, p.discount_price, p.city, p.tags,
                               p.content_hash
                        FROM products p
                        WHERE p.id IN ({placeholders})
                        ORDER BY p.id
                    """, product_ids)
                elif full_rebuild:
                    logger.info("Full rebuild: selecting all products")
                    cur.execute("""
                        SELECT p.id, p.title, p.enriched_description, p.category,
                               p.base_price, p.discount_price, p.city, p.tags,
                               p.content_hash
                        FROM products p
                        ORDER BY p.id
                    """)
                else:
                    logger.info("Smart refresh: selecting products with changed content or no embeddings")
                    cur.execute("""
                        SELECT p.id, p.title, p.enriched_description, p.category,
                               p.base_price, p.discount_price, p.city, p.tags,
                               p.content_hash
                        FROM products p
                        LEFT JOIN product_embeddings pe ON p.id = pe.product_id
                        WHERE pe.product_id IS NULL
                           OR pe.content_hash IS NULL
                           OR pe.content_hash != p.content_hash
                        ORDER BY p.id
                    """)

                products = cur.fetchall()
                total_products = len(products)

                if total_products == 0:
                    logger.info("No products need processing")
                    return stats

                logger.info(f"Found {total_products} products to process")

                # Process products in batches
                for batch_start in range(0, total_products, BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, total_products)
                    batch = products[batch_start:batch_end]
                    batch_num = (batch_start // BATCH_SIZE) + 1
                    total_batches = (total_products - 1) // BATCH_SIZE + 1

                    logger.info(f"\nProcessing batch {batch_num}/{total_batches} "
                              f"(products {batch_start + 1}-{batch_end})")

                    for product in batch:
                        product_id = product['id']
                        product_name = product.get('name') or product.get('title', '')

                        try:
                            stats['processed'] += 1

                            # Enrich product data
                            enriched_data = enrich_product_data(product)
                            enriched_description = enriched_data['enriched_description']
                            embedding_text = enriched_data['embedding_text']

                            # Generate embedding
                            embedding = generate_embedding_with_retry(embedding_text)

                            if embedding is None:
                                logger.error(f"Failed to generate embedding for product {product_id}: {product_name}")
                                stats['failed'] += 1
                                continue

                            # Update enriched_description in products table
                            cur.execute("""
                                UPDATE products
                                SET enriched_description = %s
                                WHERE id = %s
                            """, (enriched_description, product_id))

                            # Upsert into product_embeddings table with content_hash
                            cur.execute("""
                                INSERT INTO product_embeddings (
                                    product_id, embedding, embedding_text, model_version, content_hash
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (product_id)
                                DO UPDATE SET
                                    embedding = EXCLUDED.embedding,
                                    embedding_text = EXCLUDED.embedding_text,
                                    model_version = EXCLUDED.model_version,
                                    content_hash = EXCLUDED.content_hash,
                                    updated_at = NOW()
                            """, (product_id, embedding, embedding_text, EMBEDDING_MODEL, product.get('content_hash')))

                            stats['succeeded'] += 1
                            logger.info(f"  ✓ Processed product {product_id}: {product_name[:50]}...")

                        except Exception as e:
                            logger.error(f"  ✗ Error processing product {product_id}: {e}")
                            stats['failed'] += 1
                            continue

                    # Commit after each batch
                    conn.commit()
                    logger.info(f"  Committed batch {batch_num}. "
                              f"Progress: {stats['succeeded']}/{total_products} succeeded, "
                              f"{stats['failed']} failed")

                    # Small delay to avoid rate limits
                    if batch_end < total_products:
                        time.sleep(0.5)

    except psycopg.Error as e:
        logger.error(f"Database error: {e}")
        return stats

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return stats

    # Log final statistics
    logger.info(f"\n{'='*60}")
    logger.info(f"Embedding refresh complete!")
    logger.info(f"  Total processed: {stats['processed']}")
    logger.info(f"  Succeeded: {stats['succeeded']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"{'='*60}\n")

    return stats


def main():
    """
    Main entry point for the script.

    Usage:
        python refresh_embeddings.py            # Partial backfill (new products only)
        python refresh_embeddings.py --full     # Full rebuild (all products)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate and refresh product embeddings for semantic search'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Full rebuild: regenerate embeddings for all products'
    )

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("Product Embeddings Refresh Script")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info(f"Mode: {'FULL REBUILD' if args.full else 'PARTIAL BACKFILL'}")
    logger.info("="*60)

    start_time = time.time()

    try:
        stats = refresh_product_embeddings(full_rebuild=args.full)

        elapsed_time = time.time() - start_time
        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")

        # Exit with appropriate code
        if stats['failed'] > 0:
            logger.warning("Some products failed to process. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("All products processed successfully!")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
