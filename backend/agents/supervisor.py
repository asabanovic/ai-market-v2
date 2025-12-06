"""Supervisor node for intent detection and routing."""

import json
import re
from typing import Any, Dict
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import SUPERVISOR_SYSTEM_PROMPT
from agents.common.llm_utils import get_chat_model


def _get_context(runtime: Any) -> AgentContext:
    """Get context from runtime or create default.

    Args:
        runtime: LangGraph runtime or config dict.

    Returns:
        AgentContext: The context object.
    """
    if runtime is None:
        return AgentContext()
    if isinstance(runtime, dict):
        configurable = runtime.get('configurable', {})
        return configurable.get('context', AgentContext())
    if hasattr(runtime, 'context') and runtime.context is not None:
        return runtime.context
    return AgentContext()


async def supervisor_node(state: AgentState, runtime: Any = None) -> Dict:
    """Analyze user query and determine intent.

    This is the entry point that routes queries to specialized agents.

    Args:
        state: Current agent state with user query.
        runtime: LangGraph runtime with context.

    Returns:
        Updated state with intent and parameters.
    """
    query = state.query
    context = _get_context(runtime)

    try:
        # Get chat model
        chat_model = await get_chat_model(
            model=context.chat_model,
            temperature=0.1  # Low temperature for intent detection
        )

        # Prepare messages
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analiz user query intent:\n\n\"{query}\""}
        ]

        # Get intent analysis
        response = await chat_model(messages, response_format={"type": "json_object"})

        # Parse response
        intent_data = json.loads(response)

        intent = intent_data.get("intent", "semantic_search")
        confidence = float(intent_data.get("confidence", 0.5))
        parameters = intent_data.get("parameters", {})

        # Extract price filter from query if not in parameters
        if "max_price" not in parameters:
            max_price = _extract_price_filter(query)
            if max_price:
                parameters["max_price"] = max_price

        # Set default k if not specified
        if "k" not in parameters:
            parameters["k"] = context.default_k or 5

        # Validate confidence
        if confidence < context.intent_confidence_threshold:
            # Default to semantic search for ambiguous queries
            intent = "semantic_search"

        return {
            "intent": intent,
            "confidence": confidence,
            "parameters": parameters,
            "next_node": intent,
            "metadata": {
                "reasoning": intent_data.get("reasoning", "")
            }
        }

    except Exception as e:
        # Fallback to semantic search on error
        context = _get_context(runtime) if 'runtime' in locals() else AgentContext()
        return {
            "intent": "semantic_search",
            "confidence": 0.5,
            "parameters": {"k": context.default_k or 5},
            "next_node": "semantic_search",
            "error": f"Intent detection error: {str(e)}"
        }


def _extract_price_filter(query: str) -> float | None:
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
