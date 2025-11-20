#!/usr/bin/env python3
"""
Quick script to vectorize all Bingo products
"""
import sys
from app import app, db
from models import Product
from auto_vectorize import batch_vectorize_products

def main():
    with app.app_context():
        # Get all Bingo product IDs (business_id = 2)
        bingo_products = Product.query.filter_by(business_id=2).all()
        product_ids = [p.id for p in bingo_products]

        print(f"Found {len(product_ids)} Bingo products to vectorize")
        print("Starting vectorization...")

        # Vectorize all products with force=True to ensure they all get embeddings
        stats = batch_vectorize_products(product_ids=product_ids, force=True)

        print(f"\nVectorization complete!")
        print(f"  Processed: {stats['processed']}")
        print(f"  Succeeded: {stats['succeeded']}")
        print(f"  Failed: {stats['failed']}")

        if stats['failed'] > 0:
            print("\nWARNING: Some products failed to vectorize. Check logs for details.")
            sys.exit(1)
        else:
            print("\nAll Bingo products vectorized successfully!")
            sys.exit(0)

if __name__ == "__main__":
    main()
