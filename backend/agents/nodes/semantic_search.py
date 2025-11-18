"""Semantic search agent node."""

import re
from typing import Dict, Optional
from langgraph.runtime import Runtime
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import SEMANTIC_SEARCH_SYSTEM_PROMPT
from agents.common.db_utils import search_by_vector
from agents.common.llm_utils import get_embedding_model, get_chat_model


def _get_context(runtime: Runtime[AgentContext]) -> AgentContext:
    """Get context from runtime or create default.

    Args:
        runtime: LangGraph runtime.

    Returns:
        AgentContext: The context object.
    """
    if runtime.context is None:
        return AgentContext()
    return runtime.context


def _get_db_session(context: AgentContext):
    """Get database session from context or Flask app.

    Args:
        context: Agent context that may contain db_session.

    Returns:
        Database session.
    """
    # First try to get from context
    if context.db_session is not None:
        return context.db_session

    # Otherwise, try to get from Flask app context
    try:
        from flask import has_app_context
        if has_app_context():
            from app import db
            return db.session
    except ImportError:
        pass

    return None


async def semantic_search_node(state: AgentState, runtime: Runtime[AgentContext]) -> Dict:
    """Execute semantic product search.

    Args:
        state: Current agent state.
        runtime: LangGraph runtime with context.

    Returns:
        Updated state with search results.
    """
    context = _get_context(runtime)
    query = state.query
    params = state.parameters or {}

    # Extract parameters from query or use defaults
    k = params.get("k") or context.default_k or 10  # Ensure k is never None
    category = params.get("category")
    max_price = params.get("max_price") or _extract_price_from_query(query)

    try:
        # Get database session
        db_session = _get_db_session(context)
        if db_session is None:
            return {
                "results": [],
                "explanation": None,
                "error": "Database session not available"
            }

        # Generate query embedding
        embed_fn = get_embedding_model(context.embedding_model)
        query_vector = embed_fn(query)

        # Search database
        results = search_by_vector(
            db_session,
            query_vector=query_vector,
            k=k,
            category=category,
            max_price=max_price,
        )

        # Filter by similarity threshold
        similarity_threshold = context.similarity_threshold or 0.3
        filtered_results = [
            result for result in results
            if result.get('similarity', 0) >= similarity_threshold
        ]

        # Generate explanation
        explanation = await _generate_explanation(query, filtered_results, context)

        return {
            "intent": "semantic_search",  # Set intent directly
            "results": filtered_results,
            "explanation": explanation,
            "metadata": {
                **state.metadata,
                "search_params": {
                    "k": k,
                    "category": category,
                    "max_price": max_price,
                    "similarity_threshold": similarity_threshold,
                },
                "result_count": len(filtered_results),
                "total_before_filter": len(results)
            }
        }

    except Exception as e:
        return {
            "results": [],
            "explanation": None,
            "error": f"Search error: {str(e)}"
        }


async def _generate_explanation(query: str, results: list, context: AgentContext) -> str:
    """Generate AI explanation for search results."""
    if not results:
        return "Nisam našao relevantne proizvode za vašu pretragu."

    # Format top results
    bullets = []
    for i, product in enumerate(results[:5], 1):
        price = product.get("discount_price") or product.get("current_price") or 0
        bullets.append(
            f"{i}. {product['title']} — {price:.2f} KM (sličnost: {product['similarity']:.2f})"
        )

    bullets_text = "\n".join(bullets)

    try:
        chat_model = await get_chat_model(
            model=context.chat_model,
            temperature=context.temperature
        )

        messages = [
            {"role": "system", "content": SEMANTIC_SEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Korisnik je tražio: "{query}"

Pronađeni proizvodi:
{bullets_text}

Objasni kratko (1-2 rečenice) zašto su ovi proizvodi relevantni."""}
        ]

        explanation = await chat_model(messages)
        return explanation.strip()

    except Exception:
        return f"Pronašao sam {len(results)} relevantnih proizvoda."


def _extract_price_from_query(query: str) -> Optional[float]:
    """Extract price filter from query text.

    Args:
        query: User query string.

    Returns:
        Maximum price or None.
    """
    patterns = [
        r'ispod\s+(\d+(?:\.\d+)?)\s*(?:KM|km)?',
        r'do\s+(\d+(?:\.\d+)?)\s*(?:KM|km)?',
        r'<\s*(\d+(?:\.\d+)?)\s*(?:KM|km)?',
        r'(\d+(?:\.\d+)?)\s*(?:KM|km)\s+max',
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None
