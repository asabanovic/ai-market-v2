#!/usr/bin/env python3
"""
Test script to verify the embeddings system works with a single product
"""
import os
import sys
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

# Load environment variables
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

print("Testing embeddings system...\n")

# Import the refresh function
from refresh_embeddings import enrich_product_data, generate_embedding_with_retry

# Connect to database and get a sample product
with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
    with conn.cursor() as cur:
        # Get one product
        cur.execute("""
            SELECT id, name, title, description, category
            FROM products
            LIMIT 1
        """)
        product = cur.fetchone()

        if not product:
            print("No products found in database!")
            sys.exit(1)

        print(f"Testing with product ID {product['id']}: {product.get('name') or product.get('title')}\n")

        # Test enrichment
        print("1. Testing product enrichment...")
        enriched = enrich_product_data(product)
        print(f"   ✓ Enriched description: {enriched['enriched_description'][:100]}...")
        print(f"   ✓ Embedding text: {enriched['embedding_text'][:100]}...\n")

        # Test embedding generation
        print("2. Testing embedding generation...")
        embedding = generate_embedding_with_retry(enriched['embedding_text'])
        if embedding:
            print(f"   ✓ Generated embedding vector with {len(embedding)} dimensions")
            print(f"   ✓ Sample values: {embedding[:5]}\n")
        else:
            print("   ✗ Failed to generate embedding")
            sys.exit(1)

        # Test database insertion
        print("3. Testing database operations...")
        try:
            # Update enriched_description
            cur.execute("""
                UPDATE products
                SET enriched_description = %s
                WHERE id = %s
            """, (enriched['enriched_description'], product['id']))

            # Upsert embedding
            cur.execute("""
                INSERT INTO product_embeddings (
                    product_id, embedding, embedding_text, model_version
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id)
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    embedding_text = EXCLUDED.embedding_text,
                    model_version = EXCLUDED.model_version,
                    updated_at = NOW()
            """, (product['id'], embedding, enriched['embedding_text'], 'text-embedding-3-small'))

            conn.commit()
            print("   ✓ Successfully inserted/updated database records\n")

        except Exception as e:
            print(f"   ✗ Database error: {e}")
            sys.exit(1)

        # Verify the data was stored correctly
        print("4. Verifying stored data...")
        cur.execute("""
            SELECT
                p.id,
                p.enriched_description,
                pe.embedding_text,
                pe.model_version,
                array_length(pe.embedding::float[], 1) as embedding_dim
            FROM products p
            JOIN product_embeddings pe ON p.id = pe.product_id
            WHERE p.id = %s
        """, (product['id'],))

        result = cur.fetchone()
        if result:
            print(f"   ✓ Product ID: {result['id']}")
            print(f"   ✓ Has enriched description: {'Yes' if result['enriched_description'] else 'No'}")
            print(f"   ✓ Embedding dimension: {result['embedding_dim']}")
            print(f"   ✓ Model version: {result['model_version']}\n")
        else:
            print("   ✗ Could not verify stored data")
            sys.exit(1)

print("="*60)
print("✅ All tests passed! The embeddings system is working correctly.")
print("="*60)
print("\nYou can now run the full script:")
print("  python3 refresh_embeddings.py           # Process new products only")
print("  python3 refresh_embeddings.py --full    # Rebuild all embeddings")
