"""Meal planning agent node."""

import json
from typing import Dict
from langgraph.runtime import Runtime
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import MEAL_PLANNING_SYSTEM_PROMPT
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


async def meal_planner_node(state: AgentState, runtime: Runtime[AgentContext]) -> Dict:
    """Generate meal suggestions based on available products.

    Args:
        state: Current agent state.
        runtime: LangGraph runtime with context.

    Returns:
        Updated state with meal suggestions.
    """
    context = _get_context(runtime)
    query = state.query
    params = state.parameters
    meal_type = params.get("meal_type", "ručak")
    max_budget = params.get("max_budget")
    preferences = params.get("preferences", [])

    try:
        # Get relevant products
        products = await _get_relevant_products(meal_type, max_budget, context)

        if not products:
            return {
                "results": [],
                "explanation": "Nema dostupnih proizvoda za planiranje obroka.",
                "error": None
            }

        # Generate meal plan
        meal_plan = await _generate_meal_plan(
            products, meal_type, preferences, query, context
        )

        return {
            "results": meal_plan.get("meals", []),
            "explanation": meal_plan.get("summary", ""),
            "metadata": {
                **state.metadata,
                "meal_type": meal_type,
                "available_products": len(products),
                "max_budget": max_budget,
            }
        }

    except Exception as e:
        return {
            "results": [],
            "explanation": None,
            "error": f"Meal planning error: {str(e)}"
        }


async def _get_relevant_products(
    meal_type: str,
    max_budget: float | None,
    context: AgentContext
) -> list:
    """Get products relevant for the meal type."""
    # Get database session
    db_session = _get_db_session(context)
    if db_session is None:
        return []

    # Define search queries for meal types
    meal_queries = {
        "doručak": "jaja mlijeko kruh sir džem",
        "ručak": "meso povrće pirinač tjestenina",
        "večera": "riba piletina salata povrće",
    }

    query = meal_queries.get(meal_type.lower(), "namirnice za kuhanje")

    # Get embedding
    embed_fn = get_embedding_model(context.embedding_model)
    query_vector = embed_fn(query)

    # Search
    products = search_by_vector(
        db_session,
        query_vector=query_vector,
        k=20,
        max_price=max_budget,
    )

    return products


async def _generate_meal_plan(
    products: list,
    meal_type: str,
    preferences: list,
    original_query: str,
    context: AgentContext
) -> dict:
    """Generate meal plan using AI."""
    # Format products
    product_list = []
    for p in products[:15]:
        price = p.get("discount_price") or p.get("current_price")
        product_list.append(f"- {p['title']} ({price:.2f} KM)")

    products_text = "\n".join(product_list)
    preferences_text = ", ".join(preferences) if preferences else "nema posebnih preferencija"

    try:
        chat_model = await get_chat_model(
            model=context.chat_model,
            temperature=0.7  # Higher temperature for creativity
        )

        user_prompt = f"""Korisnik pita: "{original_query}"

Tip obroka: {meal_type}
Dostupni proizvodi:
{products_text}

Preferencije: {preferences_text}

Predloži 3 različite ideje za {meal_type}. Za svaku ideju navedi:
1. Naziv jela
2. Potrebne namirnice sa cijenama
3. Kratke korake pripreme
4. Ukupna cijena

Format kao JSON:
{{
  "summary": "Kratko uvodno objašnjenje (1 rečenica)",
  "meals": [
    {{
      "name": "Naziv jela",
      "ingredients": [{{"product": "naziv", "price": 5.5}}],
      "steps": ["Korak 1", "Korak 2"],
      "total_price": 15.00,
      "prep_time": "30 minuta"
    }}
  ]
}}"""

        messages = [
            {"role": "system", "content": MEAL_PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = await chat_model(messages, response_format={"type": "json_object"})
        meal_plan = json.loads(response)
        return meal_plan

    except Exception as e:
        return {
            "summary": f"Greška: {str(e)}",
            "meals": []
        }
