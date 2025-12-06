"""
Agent-based semantic search wrapper.

This module provides a synchronous wrapper around the async LangGraph agent
for use in Flask routes.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date

from app import db
from agents import graph
from agents.context import AgentContext
from agents.state import InputState


def run_agent_search(
    query: str,
    user_id: Optional[str] = None,
    k: int = 8,
    business_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Run the agent-based semantic search synchronously.

    This runs the LangGraph agent which:
    1. Parses the query with intent parser (splits multi-item queries, expands with synonyms)
    2. Performs semantic search with the expanded queries
    3. Returns grouped results with explanations

    Args:
        query: User's search query
        user_id: Optional user ID for personalization
        k: Number of results per item
        business_ids: Optional list of business IDs to filter by

    Returns:
        Dict with 'products', 'explanation', 'grouped', 'metadata'
    """
    # Create context with db session
    context = AgentContext(
        db_session=db.session,
        default_k=k,
    )

    # Create input state
    input_state = {
        "query": query,
        "user_id": user_id,
        "parameters": {
            "k": k,
            "business_ids": business_ids,
        },
        "metadata": {
            "business_ids": business_ids,
        }
    }

    # Run the graph
    try:
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async graph synchronously
        # Pass context via config for langgraph 0.2.x compatibility
        config = {"configurable": {"context": context}}
        result = loop.run_until_complete(
            graph.ainvoke(input_state, config=config)
        )

        # Process results
        raw_results = result.get("results", [])
        explanation = result.get("explanation")
        metadata = result.get("metadata", {})

        # Check if results are grouped (dict) or flat (list)
        if isinstance(raw_results, dict):
            # Grouped results - flatten them into a single list for the API
            products = []
            for group_name, group_products in raw_results.items():
                for product in group_products:
                    # Add group info to each product
                    product["search_group"] = group_name
                    products.append(product)

            return {
                "products": products,
                "grouped_results": raw_results,  # Keep grouped version too
                "explanation": explanation,
                "grouped": True,
                "metadata": metadata,
            }
        else:
            # Flat results
            return {
                "products": raw_results if raw_results else [],
                "explanation": explanation,
                "grouped": False,
                "metadata": metadata,
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "products": [],
            "explanation": None,
            "grouped": False,
            "metadata": {},
            "error": str(e),
        }


def format_agent_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format agent search products to match the expected API format.

    Args:
        products: Raw products from agent search

    Returns:
        Formatted products matching semantic_search output format
    """
    formatted = []

    for product in products:
        # Check if discount has expired
        expires = product.get("expires")
        is_expired = False
        if expires:
            if isinstance(expires, str):
                from datetime import datetime
                try:
                    expires_date = datetime.fromisoformat(expires).date()
                    is_expired = date.today() > expires_date
                except:
                    pass
            elif isinstance(expires, date):
                is_expired = date.today() > expires

        base_price = product.get("base_price")
        discount_price = product.get("discount_price")

        # If expired, treat as regular product
        if is_expired:
            discount_price = None
            expires = None

        current_price = discount_price if discount_price else base_price

        formatted_product = {
            "id": product.get("id"),
            "title": product.get("title"),
            "base_price": float(base_price) if base_price else None,
            "discount_price": float(discount_price) if discount_price else None,
            "price": float(current_price) if current_price else None,
            "expires": expires.isoformat() if hasattr(expires, 'isoformat') else expires,
            "category": product.get("category"),
            "tags": product.get("tags"),
            "city": product.get("city"),
            "image_url": product.get("image_path"),
            "product_url": product.get("product_url"),
            "views": product.get("views"),
            "enriched_description": product.get("enriched_description"),
            "similarity_score": product.get("similarity", 0),
            "_score": product.get("similarity", 0),
            "search_group": product.get("search_group"),  # From grouped search
        }

        # Add business info
        business = product.get("business", {})
        if business:
            formatted_product["business"] = {
                "id": business.get("id"),
                "name": business.get("name"),
                "logo": business.get("logo"),
                "city": business.get("city"),
                "phone": business.get("phone"),
            }

        # Calculate discount info
        if formatted_product["discount_price"] and formatted_product["base_price"] and not is_expired:
            formatted_product["discount_percent"] = round(
                ((formatted_product["base_price"] - formatted_product["discount_price"]) / formatted_product["base_price"]) * 100
            )
            formatted_product["savings"] = round(formatted_product["base_price"] - formatted_product["discount_price"], 2)
        else:
            formatted_product["discount_percent"] = 0
            formatted_product["savings"] = 0

        formatted.append(formatted_product)

    return formatted
