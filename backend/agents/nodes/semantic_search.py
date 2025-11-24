"""Semantic search agent node."""

import re
from typing import Dict, Optional
from langgraph.runtime import Runtime
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import SEMANTIC_SEARCH_SYSTEM_PROMPT
from agents.common.db_utils import search_by_vector, search_by_vector_grouped
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
    search_items = state.search_items or []

    # Extract parameters from query or use defaults
    k = params.get("k") or context.default_k or 10  # Ensure k is never None
    category = params.get("category")
    max_price = params.get("max_price") or _extract_price_from_query(query)
    similarity_threshold = context.similarity_threshold or 0.2

    try:
        # Get database session
        db_session = _get_db_session(context)
        if db_session is None:
            return {
                "results": [],
                "explanation": None,
                "error": "Database session not available"
            }

        # Check if we have parsed search items (from intent parser)
        if search_items:
            # Use grouped search for multiple items
            grouped_results = await search_by_vector_grouped(
                db_session=db_session,
                search_items=search_items,
                embedding_model=context.embedding_model,
                k=k,
                category=category,
                max_price=max_price,
            )

            # Filter by similarity threshold for each group
            filtered_grouped = {}
            total_before = 0
            total_after = 0

            for item_name, results in grouped_results.items():
                total_before += len(results)
                filtered = [
                    result for result in results
                    if result.get('similarity', 0) >= similarity_threshold
                ]
                filtered_grouped[item_name] = filtered
                total_after += len(filtered)

            # Generate explanation for grouped results
            explanation = await _generate_grouped_explanation(query, filtered_grouped, context)

            return {
                "intent": "semantic_search",
                "results": filtered_grouped,
                "explanation": explanation,
                "metadata": {
                    **state.metadata,
                    "search_params": {
                        "k": k,
                        "category": category,
                        "max_price": max_price,
                        "similarity_threshold": similarity_threshold,
                    },
                    "result_count": total_after,
                    "total_before_filter": total_before,
                    "grouped": True,
                    "num_groups": len(filtered_grouped)
                }
            }
        else:
            # Fallback to single query search (legacy behavior)
            embed_fn = get_embedding_model(context.embedding_model)
            query_vector = embed_fn(query)

            results = search_by_vector(
                db_session,
                query_vector=query_vector,
                k=k,
                category=category,
                max_price=max_price,
            )

            # Filter by similarity threshold
            filtered_results = [
                result for result in results
                if result.get('similarity', 0) >= similarity_threshold
            ]

            # Generate explanation
            explanation = await _generate_explanation(query, filtered_results, context)

            return {
                "intent": "semantic_search",
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
                    "total_before_filter": len(results),
                    "grouped": False
                }
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
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


async def _generate_grouped_explanation(query: str, grouped_results: Dict, context: AgentContext) -> str:
    """Generate AI explanation for grouped search results."""
    if not grouped_results or all(len(items) == 0 for items in grouped_results.values()):
        return "Nisam našao relevantne proizvode za vašu pretragu."

    # Format results by group
    bullets = []
    for group_name, products in grouped_results.items():
        if not products:
            continue
        bullets.append(f"\n[{group_name}]")
        for i, product in enumerate(products[:3], 1):  # Top 3 per group
            price = product.get("discount_price") or product.get("current_price") or 0
            bullets.append(
                f"  {i}. {product['title']} — {price:.2f} KM (sličnost: {product['similarity']:.2f})"
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

Pronađeni proizvodi (grupisani po stavkama):
{bullets_text}

Objasni kratko (1-2 rečenice) zašto su ovi proizvodi relevantni. Fokusiraj se na to da je svaka stavka pronađena."""}
        ]

        explanation = await chat_model(messages)
        return explanation.strip()

    except Exception:
        total_count = sum(len(items) for items in grouped_results.values())
        return f"Pronašao sam {total_count} relevantnih proizvoda za {len(grouped_results)} stavki."


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
