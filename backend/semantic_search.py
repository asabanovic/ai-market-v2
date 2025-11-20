"""
Semantic Search using Vector Embeddings
Uses OpenAI embeddings and PostgreSQL pgvector for similarity search
"""
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from sqlalchemy import text
from app import db
from models import Product, ProductEmbedding, Business

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def semantic_search(
    query: str,
    k: int = 10,
    min_similarity: float = 0.3,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform semantic search using vector embeddings

    Args:
        query: User's search query
        k: Number of results to return
        min_similarity: Minimum cosine similarity threshold (0-1)
        price_max: Maximum price filter
        price_min: Minimum price filter
        category: Category filter

    Returns:
        List of product dictionaries with similarity scores
    """
    try:
        # Generate query embedding
        logger.info(f"Generating embedding for query: {query}")
        query_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = query_response.data[0].embedding

        # Format embedding as PostgreSQL array literal
        # pgvector expects format: '[0.1,0.2,0.3,...]'
        embedding_str = '[' + ','.join(str(float(x)) for x in query_embedding) + ']'

        # Build SQL query with vector similarity search
        # Using pgvector's <=> operator for cosine distance
        # Cosine distance = 1 - cosine similarity
        # Note: We use direct string substitution for the vector since SQLAlchemy
        # doesn't handle vector type binding well with text()
        sql_parts = [f"""
            SELECT
                p.id,
                p.title,
                p.base_price,
                p.discount_price,
                p.expires,
                p.category,
                p.tags,
                p.city,
                p.image_path,
                p.product_url,
                p.views,
                p.enriched_description,
                b.id as business_id,
                b.name as business_name,
                b.logo_path as business_logo,
                b.city as business_city,
                b.contact_phone as business_phone,
                (1 - (pe.embedding <=> '{embedding_str}'::vector)) as similarity
            FROM products p
            INNER JOIN product_embeddings pe ON p.id = pe.product_id
            INNER JOIN businesses b ON p.business_id = b.id
            WHERE (p.expires IS NULL OR p.expires >= CURRENT_DATE)
        """]

        params = {
            'k': k
        }

        # Add filters
        if price_max is not None:
            sql_parts.append("AND COALESCE(p.discount_price, p.base_price) <= :price_max")
            params['price_max'] = price_max

        if price_min is not None:
            sql_parts.append("AND COALESCE(p.discount_price, p.base_price) >= :price_min")
            params['price_min'] = price_min

        if category is not None:
            sql_parts.append("AND p.category = :category")
            params['category'] = category

        # Add similarity threshold and ordering
        sql_parts.append(f"""
            AND (1 - (pe.embedding <=> '{embedding_str}'::vector)) >= :min_similarity
            ORDER BY similarity DESC,
                     CASE WHEN p.discount_price IS NOT NULL
                          THEN (p.base_price - p.discount_price) / p.base_price
                          ELSE 0 END DESC
            LIMIT :k
        """)
        params['min_similarity'] = min_similarity

        # Execute query
        sql_query = text(' '.join(sql_parts))
        result = db.session.execute(sql_query, params)

        # Format results
        products = []
        for row in result:
            product = {
                'id': row.id,
                'title': row.title,
                'base_price': float(row.base_price) if row.base_price else None,
                'discount_price': float(row.discount_price) if row.discount_price else None,
                'price': float(row.discount_price if row.discount_price else row.base_price),
                'expires': row.expires.isoformat() if row.expires else None,
                'category': row.category,
                'tags': row.tags,
                'city': row.city,
                'image_url': row.image_path,
                'product_url': row.product_url,
                'views': row.views,
                'enriched_description': row.enriched_description,
                'business': {
                    'id': row.business_id,
                    'name': row.business_name,
                    'logo': row.business_logo,
                    'city': row.business_city,
                    'phone': row.business_phone
                },
                'similarity_score': float(row.similarity),
                '_score': float(row.similarity)  # For compatibility
            }

            # Calculate discount info
            if product['discount_price'] and product['base_price']:
                product['discount_percent'] = round(
                    ((product['base_price'] - product['discount_price']) / product['base_price']) * 100
                )
                product['savings'] = round(product['base_price'] - product['discount_price'], 2)
            else:
                product['discount_percent'] = 0
                product['savings'] = 0

            products.append(product)

        logger.info(f"Found {len(products)} products for query: {query}")
        return products

    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        raise


def parse_price_filter_from_query(query: str) -> tuple[Optional[float], Optional[float]]:
    """
    Extract price filters from Bosnian query text

    Args:
        query: User's search query in Bosnian

    Returns:
        Tuple of (min_price, max_price) or (None, None) if no price found
    """
    import re

    q = query.lower().replace(',', '.')
    q = re.sub(r'\s+', ' ', q)

    # "ispod X KM" or "manje od X KM" (less than)
    m = re.search(r'(ispod|manje od)\s*([0-9]+(\.[0-9]+)?)\s*(km)?', q)
    if m:
        return (None, float(m.group(2)))

    # "iznad X KM" or "preko X KM" (greater than)
    m = re.search(r'(iznad|preko)\s*([0-9]+(\.[0-9]+)?)\s*(km)?', q)
    if m:
        return (float(m.group(2)), None)

    # "od X do Y KM" (range)
    m = re.search(r'od\s*([0-9]+(\.[0-9]+)?)\s*do\s*([0-9]+(\.[0-9]+)?)\s*(km)?', q)
    if m:
        return (float(m.group(1)), float(m.group(3)))

    return (None, None)
