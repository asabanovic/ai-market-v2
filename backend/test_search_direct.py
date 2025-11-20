#!/usr/bin/env python3
"""
Direct test of semantic search to diagnose issues
"""
import sys
import logging
from app import app, db

logging.basicConfig(level=logging.INFO)

def test_semantic_search():
    with app.app_context():
        from semantic_search import semantic_search

        print("Testing semantic search for 'kafa'...")
        try:
            results = semantic_search(
                query="kafa",
                k=10,
                min_similarity=0.3
            )

            print(f"\nFound {len(results)} results:")
            for i, product in enumerate(results[:5], 1):
                print(f"\n{i}. {product['title']}")
                print(f"   Business: {product['business']['name']}")
                print(f"   Similarity: {product['similarity_score']:.3f}")
                print(f"   Price: {product['price']} KM")

            # Check if any Bingo products
            bingo_products = [p for p in results if p['business']['name'] == 'Bingo']
            print(f"\n✓ Found {len(bingo_products)} Bingo products")

            return True

        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_semantic_search()
    sys.exit(0 if success else 1)
