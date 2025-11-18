"""Database utilities for agents."""

from typing import List, Dict, Any, Optional, Callable
from sqlalchemy import text


def search_by_vector(
    db_session,
    query_vector: List[float],
    k: int = 5,
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search for products using vector similarity.

    Args:
        db_session: SQLAlchemy database session.
        query_vector: The query embedding vector.
        k: Number of results to return.
        filter_fn: Optional custom filter function.
        category: Optional category filter.
        max_price: Optional maximum price filter.

    Returns:
        List of product dictionaries with similarity scores.
    """
    # Build the WHERE clause
    where_clauses = ["p.embedding IS NOT NULL"]

    if category:
        where_clauses.append(f"p.category = '{category}'")

    if max_price:
        where_clauses.append(f"COALESCE(p.discount_price, p.base_price) <= {max_price}")

    where_sql = " AND ".join(where_clauses)

    # Convert vector to PostgreSQL format
    vector_str = "[" + ",".join(map(str, query_vector)) + "]"

    query = f"""
        SELECT
            p.id,
            p.title,
            p.base_price,
            p.discount_price,
            p.category,
            p.tags,
            p.enriched_description,
            p.city,
            p.expires,
            p.image_path,
            b.name as business_name,
            1 - (p.embedding <=> '{vector_str}'::vector) as similarity
        FROM products p
        LEFT JOIN businesses b ON p.business_id = b.id
        WHERE {where_sql}
        ORDER BY p.embedding <=> '{vector_str}'::vector
        LIMIT {k * 2}
    """

    result = db_session.execute(text(query))
    products = []

    for row in result:
        product = {
            "id": row.id,
            "title": row.title,
            "base_price": row.base_price,
            "discount_price": row.discount_price,
            "current_price": row.discount_price if row.discount_price else row.base_price,
            "category": row.category,
            "tags": row.tags,
            "enriched_description": row.enriched_description,
            "city": row.city,
            "expires": row.expires,
            "image_path": row.image_path,
            "business_name": row.business_name,
            "similarity": float(row.similarity),
        }

        # Apply custom filter if provided
        if filter_fn and not filter_fn(product):
            continue

        products.append(product)

        if len(products) >= k:
            break

    return products
