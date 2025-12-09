"""Database utilities for agents."""

from datetime import date
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
    max_per_store: int = 2,
    business_ids: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """Search for products using vector similarity.

    Args:
        db_session: SQLAlchemy database session.
        query_vector: The query embedding vector.
        k: Number of results to return.
        filter_fn: Optional custom filter function.
        category: Optional category filter.
        max_price: Optional maximum price filter.
        max_per_store: Maximum products per store (default 2), then sorted by similarity.
        business_ids: Optional list of business IDs to filter by.

    Returns:
        List of product dictionaries with similarity scores.
    """
    # Set ivfflat probes for better recall
    db_session.execute(text("SET ivfflat.probes = 10"))

    # Build the WHERE clause - show all products (expired discounts become regular products)
    where_clauses = ["1=1"]

    if category:
        where_clauses.append(f"p.category = '{category}'")

    if business_ids:
        ids_str = ",".join(map(str, business_ids))
        where_clauses.append(f"p.business_id IN ({ids_str})")

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
        LIMIT {k * 10}
    """

    result = db_session.execute(text(query))
    all_products = []

    for row in result:
        # Check if discount has expired
        is_expired = False
        if row.expires:
            is_expired = date.today() > row.expires

        # If discount has expired, treat as regular product
        if is_expired:
            discount_price = None
            current_price = row.base_price
            expires = None
        else:
            discount_price = row.discount_price
            current_price = row.discount_price if row.discount_price else row.base_price
            expires = row.expires

        product = {
            "id": row.id,
            "title": row.title,
            "base_price": row.base_price,
            "discount_price": discount_price,
            "current_price": current_price,
            "category": row.category,
            "tags": row.tags,
            "enriched_description": row.enriched_description,
            "city": row.city,
            "expires": expires,
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

        all_products.append(product)

    # Apply max_per_store limit: take top N from each store, then sort all by similarity
    products = _limit_per_store(all_products, max_per_store=max_per_store, total_limit=k)

    return products


def _limit_per_store(
    products: List[Dict[str, Any]],
    max_per_store: int,
    total_limit: int
) -> List[Dict[str, Any]]:
    """Limit products per store, then return top results by similarity.

    Args:
        products: List of products sorted by similarity (highest first).
        max_per_store: Maximum products to keep per store.
        total_limit: Total number of results to return.

    Returns:
        Diversified list limited to max_per_store per store, sorted by similarity.
    """
    if not products or max_per_store <= 0:
        return products[:total_limit]

    from collections import defaultdict

    # Count products per store and collect top N from each
    store_counts: Dict[int, int] = defaultdict(int)
    selected = []

    for product in products:
        business_id = product.get("business", {}).get("id")
        if business_id is None:
            selected.append(product)
            continue

        if store_counts[business_id] < max_per_store:
            selected.append(product)
            store_counts[business_id] += 1

    # Sort by similarity (already sorted from DB, but re-sort after filtering)
    selected.sort(key=lambda p: p.get("similarity", 0), reverse=True)

    return selected[:total_limit]


async def search_by_vector_grouped(
    db_session,
    search_items: List[Dict[str, Any]],
    embedding_model: str,
    k: int = 5,
    filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    business_ids: Optional[List[int]] = None,
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
        business_ids: Optional list of business IDs to filter by.

    Returns:
        Dictionary mapping original item names to their search results.
    """
    embed_fn = get_embedding_model(embedding_model)
    grouped_results = {}

    for item in search_items:
        # Use embedding_text for vector search (optimized for semantic matching)
        # Falls back to normalized_query then query then original
        query_text = item.get("embedding_text") or item.get("normalized_query") or item.get("query") or item.get("original", "")

        # Normalize to lowercase for consistent embedding matching
        query_text_normalized = query_text.lower() if query_text else query_text

        # Use corrected spelling for display, fallback to original if not available
        display_name = item.get("corrected", item.get("original", query_text))

        # Generate embedding for this item (using normalized lowercase)
        query_vector = embed_fn(query_text_normalized)

        # Search for this specific item
        results = search_by_vector(
            db_session=db_session,
            query_vector=query_vector,
            k=k,
            filter_fn=filter_fn,
            category=category,
            max_price=max_price,
            business_ids=business_ids,
        )

        grouped_results[display_name] = results

    return grouped_results
