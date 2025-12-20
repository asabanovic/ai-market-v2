"""
Semantic Search using Vector Embeddings
Uses OpenAI embeddings and PostgreSQL pgvector for similarity search
"""
import os
import logging
from datetime import date
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
    min_similarity: float = 0.45,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    category: Optional[str] = None,
    business_ids: Optional[List[int]] = None
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
        business_ids: List of business IDs to filter by (optional)

    Returns:
        List of product dictionaries with similarity scores
    """
    try:
        # Generate query embedding (normalize to lowercase for case-insensitive search)
        query_normalized = query.lower() if query else query
        logger.info(f"Generating embedding for query: {query} (normalized: {query_normalized})")
        query_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query_normalized
        )
        query_embedding = query_response.data[0].embedding

        # Format embedding as PostgreSQL array literal
        # pgvector expects format: '[0.1,0.2,0.3,...]'
        embedding_str = '[' + ','.join(str(float(x)) for x in query_embedding) + ']'

        # Set ivfflat probes for better recall
        db.session.execute(text("SET ivfflat.probes = 10"))

        # Build SQL query with vector similarity search
        # Using pgvector's <=> operator for cosine distance
        # Cosine distance = 1 - cosine similarity
        # Note: We use direct string substitution for the vector since SQLAlchemy
        # doesn't handle vector type binding well with text()

        # Escape query for SQL LIKE pattern
        query_escaped = query_normalized.replace("'", "''").replace("%", "\\%").replace("_", "\\_")
        # Use first 4 chars as stem for Bosnian word matching (piletina -> pile, mlijeko -> mlij)
        query_stem = query_escaped[:4] if len(query_escaped) >= 4 else query_escaped

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
                (1 - (pe.embedding <=> '{embedding_str}'::vector)) as raw_similarity,
                CASE
                    WHEN LOWER(p.title) LIKE '%{query_escaped}%' THEN 0.5
                    WHEN LOWER(p.title) LIKE '%{query_stem}%' THEN 0.3
                    ELSE 0
                END as text_bonus,
                (1 - (pe.embedding <=> '{embedding_str}'::vector)) +
                    CASE
                        WHEN LOWER(p.title) LIKE '%{query_escaped}%' THEN 0.5
                        WHEN LOWER(p.title) LIKE '%{query_stem}%' THEN 0.3
                        ELSE 0
                    END as similarity
            FROM products p
            INNER JOIN product_embeddings pe ON p.id = pe.product_id
            INNER JOIN businesses b ON p.business_id = b.id
            WHERE 1=1
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

        # Filter by business IDs if provided
        if business_ids is not None and len(business_ids) > 0:
            sql_parts.append("AND p.business_id = ANY(:business_ids)")
            params['business_ids'] = business_ids

        # Add similarity threshold and ordering
        sql_parts.append(f"""
            AND (1 - (pe.embedding <=> '{embedding_str}'::vector)) >= :min_similarity
            ORDER BY similarity DESC,
                     CASE WHEN p.discount_price IS NOT NULL AND p.base_price IS NOT NULL AND p.base_price > 0
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

            # Check if discount has expired
            is_expired = False
            if row.expires:
                is_expired = date.today() > row.expires

            # Calculate discount info - only show discount if not expired
            if product['discount_price'] and product['base_price'] and not is_expired:
                product['discount_percent'] = round(
                    ((product['base_price'] - product['discount_price']) / product['base_price']) * 100
                )
                product['savings'] = round(product['base_price'] - product['discount_price'], 2)
            else:
                # If expired, treat as regular product (no discount)
                if is_expired:
                    product['discount_price'] = None
                    product['price'] = product['base_price']
                    product['expires'] = None
                product['discount_percent'] = 0
                product['savings'] = 0

            products.append(product)

        logger.info(f"Found {len(products)} products for query: {query}")
        return products

    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        raise


def get_user_context_data(user_id: str) -> dict:
    """
    Build context data from user's favorite products.
    Returns embedding and categories for filtering.

    Returns:
        Dict with 'embedding' (list or None) and 'categories' (set of category names)
    """
    from models import Favorite, Product
    import numpy as np

    result = {'embedding': None, 'categories': set()}

    try:
        # Get user's favorite products (last 50 to build context)
        favorites = Favorite.query.filter_by(user_id=user_id).order_by(
            Favorite.created_at.desc()
        ).limit(50).all()

        if not favorites:
            return result

        # Get product titles and categories for context
        product_ids = [f.product_id for f in favorites]
        products = Product.query.filter(Product.id.in_(product_ids)).all()

        if not products:
            return result

        # Collect categories from favorites
        for p in products:
            if p.category:
                result['categories'].add(p.category)

        # Create context text from favorite product titles
        # This builds a "taste profile" like: "piletina salama sir mlijeko jogurt"
        context_titles = [p.title.lower() for p in products if p.title]
        if not context_titles:
            return result

        # Combine titles into context string (max 500 chars to stay within embedding limits)
        context_text = " ".join(context_titles)[:500]

        logger.info(f"Building context embedding for user {user_id} from {len(context_titles)} favorites, categories: {result['categories']}")

        # Generate embedding for user's context
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=context_text
        )
        result['embedding'] = response.data[0].embedding
        return result

    except Exception as e:
        logger.error(f"Error building user context data: {e}")
        return result


def get_user_context_embedding(user_id: str) -> Optional[List[float]]:
    """
    Build a context embedding from user's favorite products.
    This represents the user's taste profile for boosting relevant results.

    Returns:
        Averaged embedding of user's favorite products, or None if no favorites
    """
    # For backwards compatibility, just return the embedding part
    return get_user_context_data(user_id).get('embedding')


def semantic_search_with_context(
    query: str,
    user_id: str,
    k: int = 50,
    min_similarity: float = 0.25,
    business_ids: Optional[List[int]] = None,
    context_weight: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Perform semantic search with user context boosting.
    Products similar to user's favorites get a context bonus.
    Products in categories user never bought (like pet food) get a penalty.

    Args:
        query: Search query
        user_id: User ID to get context from favorites
        k: Number of results to return
        min_similarity: Minimum raw similarity threshold
        business_ids: Optional store filter
        context_weight: How much to weight context similarity (0-1)

    Returns:
        List of products with adjusted similarity scores
    """
    import numpy as np

    # Get base search results (more than we need, we'll re-rank)
    results = semantic_search(
        query=query,
        k=k * 2,  # Get extra to account for filtering
        min_similarity=min_similarity,
        business_ids=business_ids
    )

    if not results:
        return []

    # Get user's full context data (embedding + categories)
    context_data = get_user_context_data(user_id)
    context_embedding = context_data.get('embedding')
    user_categories = context_data.get('categories', set())

    if context_embedding is None:
        # No favorites, return as-is
        return results[:k]

    context_embedding = np.array(context_embedding)

    # Categories that should be penalized if user doesn't have them in favorites
    # These are "niche" categories where presence in favorites is a strong signal
    PENALTY_CATEGORIES = {'Kućni ljubimci'}  # Pet food - strong negative signal if not in favorites
    CATEGORY_PENALTY = 0.4  # Penalty to subtract from score (enough to drop below threshold)

    # Bonus for products that are in user's favorites (exact match)
    FAVORITE_BONUS = 0.15  # Strong boost to ensure favorites rank at top

    # Get embeddings for result products and calculate context similarity
    product_ids = [r['id'] for r in results]

    # Get user's favorite product IDs for exact-match boosting
    from models import ProductEmbedding, Favorite
    user_favorite_ids = set(
        f.product_id for f in Favorite.query.filter_by(user_id=user_id).all()
    )

    # Query product embeddings
    embeddings = ProductEmbedding.query.filter(
        ProductEmbedding.product_id.in_(product_ids)
    ).all()

    embedding_map = {e.product_id: np.array(e.embedding) for e in embeddings}

    # Calculate context bonus for each product
    for product in results:
        product_embedding = embedding_map.get(product['id'])
        category_penalty = 0.0
        favorite_bonus = 0.0

        # Check if this exact product is in user's favorites
        is_favorite = product['id'] in user_favorite_ids
        if is_favorite:
            favorite_bonus = FAVORITE_BONUS
            logger.debug(f"Applying favorite bonus to '{product.get('title')}' (+{FAVORITE_BONUS})")

        # Apply penalty for categories user doesn't buy
        product_category = product.get('category')
        if product_category in PENALTY_CATEGORIES and product_category not in user_categories:
            category_penalty = CATEGORY_PENALTY
            logger.debug(f"Applying penalty to '{product.get('title')}' - category '{product_category}' not in user favorites")

        if product_embedding is not None:
            # Cosine similarity between product and user context
            context_sim = np.dot(product_embedding, context_embedding) / (
                np.linalg.norm(product_embedding) * np.linalg.norm(context_embedding)
            )
            # Context bonus scaled by weight (e.g., 0.2 * 0.8 = +0.16 for high match)
            context_bonus = max(0, float(context_sim) - 0.3) * context_weight  # Only boost if > 0.3 similarity
            # Convert numpy floats to Python floats for SQLAlchemy compatibility
            total_bonus = context_bonus + favorite_bonus - category_penalty
            product['context_bonus'] = float(round(total_bonus, 4))
            product['context_similarity'] = float(round(context_sim, 4))
            product['category_penalty'] = float(category_penalty)
            product['favorite_bonus'] = float(favorite_bonus)
            product['is_favorite'] = is_favorite
            # Adjust final score (keep raw score for proper ranking, UI can format display)
            original_score = product['similarity_score']
            adjusted_score = original_score + total_bonus
            product['similarity_score'] = float(round(adjusted_score, 4))
        else:
            total_bonus = favorite_bonus - category_penalty
            product['context_bonus'] = float(round(total_bonus, 4))
            product['context_similarity'] = 0
            product['category_penalty'] = float(category_penalty)
            product['favorite_bonus'] = float(favorite_bonus)
            product['is_favorite'] = is_favorite
            # Still apply bonus/penalty even without embedding
            product['similarity_score'] = float(round(product['similarity_score'] + total_bonus, 4))

    # Re-sort by adjusted score
    results.sort(key=lambda x: x['similarity_score'], reverse=True)

    # Return top k
    return results[:k]


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
