"""Database utilities for agents."""

from typing import List, Dict, Any, Optional, Callable
from sqlalchemy import text
from agents.common.llm_utils import get_embedding_model


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
    # Set ivfflat probes for better recall
    db_session.execute(text("SET ivfflat.probes = 10"))

    # Build the WHERE clause - show all products (expired discounts become regular products)
    where_clauses = ["1=1"]

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
            p.business_id,
            b.name as business_name,
            b.logo_path as business_logo,
            b.city as business_city,
            1 - (pe.embedding <=> '{vector_str}'::vector) as similarity
        FROM products p
        INNER JOIN product_embeddings pe ON p.id = pe.product_id
        LEFT JOIN businesses b ON p.business_id = b.id
        WHERE {where_sql}
        ORDER BY pe.embedding <=> '{vector_str}'::vector
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
            "similarity": float(row.similarity),
            "business": {
                "id": row.business_id,
                "name": row.business_name,
                "logo": row.business_logo,
                "city": row.business_city or row.city,
            }
        }

        # Apply custom filter if provided
        if filter_fn and not filter_fn(product):
            continue

        products.append(product)

        if len(products) >= k:
            break

    return products


async def search_by_vector_grouped(
    db_session,
    search_items: List[Dict[str, Any]],
    embedding_model: str,
    k: int = 5,
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Search for products using vector similarity for multiple items, grouped by item.

    Args:
        db_session: SQLAlchemy database session.
        search_items: List of search item dicts with 'original', 'query', and 'expanded_query'.
        embedding_model: Name of the embedding model to use.
        k: Number of results to return per item.
        filter_fn: Optional custom filter function.
        category: Optional category filter.
        max_price: Optional maximum price filter.

    Returns:
        Dictionary mapping original item names to their search results.
    """
    embed_fn = get_embedding_model(embedding_model)
    grouped_results = {}

    for item in search_items:
        # Use expanded_query if available, otherwise fall back to query
        query_text = item.get("expanded_query", item.get("query", ""))

        # Use corrected spelling for display, fallback to original if not available
        display_name = item.get("corrected", item.get("original", query_text))

        # Generate embedding for this item
        query_vector = embed_fn(query_text)

        # Search for this specific item
        results = search_by_vector(
            db_session=db_session,
            query_vector=query_vector,
            k=k,
            filter_fn=filter_fn,
            category=category,
            max_price=max_price,
        )

        grouped_results[display_name] = results

    return grouped_results
