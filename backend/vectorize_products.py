#!/usr/bin/env python3
"""
Script to generate embeddings for all products using OpenAI API
"""
import os
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Connect to PostgreSQL
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# Get all products
cur.execute("SELECT id, title, category, base_price, discount_price, city FROM products WHERE embedding IS NULL")
products = cur.fetchall()

print(f"Found {len(products)} products to vectorize")

# Process products in batches
batch_size = 20
total_processed = 0

for i in range(0, len(products), batch_size):
    batch = products[i:i+batch_size]
    print(f"\nProcessing batch {i//batch_size + 1}/{(len(products)-1)//batch_size + 1}")

    for product in batch:
        product_id, title, category, base_price, discount_price, city = product

        # Create a text representation of the product
        price_text = f"{discount_price if discount_price else base_price} KM"
        category_text = category if category else "Ostalo"
        city_text = city if city else ""

        product_text = f"{title}. Kategorija: {category_text}. Cijena: {price_text}. Grad: {city_text}"

        try:
            # Generate embedding
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=product_text
            )

            embedding = response.data[0].embedding

            # Update product with embedding
            cur.execute(
                "UPDATE products SET embedding = %s WHERE id = %s",
                (embedding, product_id)
            )

            total_processed += 1
            print(f"  ✓ Vectorized: {title[:50]}... (ID: {product_id})")

        except Exception as e:
            print(f"  ✗ Error vectorizing product {product_id}: {e}")
            continue

    # Commit after each batch
    conn.commit()
    print(f"  Committed batch. Total processed: {total_processed}/{len(products)}")

    # Small delay to avoid rate limits
    if i + batch_size < len(products):
        time.sleep(0.5)

# Create an index for faster vector similarity search
print("\nCreating vector index...")
try:
    cur.execute("""
        CREATE INDEX IF NOT EXISTS products_embedding_idx
        ON products
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    conn.commit()
    print("✓ Vector index created successfully")
except Exception as e:
    print(f"⚠ Could not create index (will still work without it): {e}")

conn.close()

print(f"\n✅ Vectorization complete! Processed {total_processed}/{len(products)} products")
