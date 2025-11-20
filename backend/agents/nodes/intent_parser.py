"""Intent parser node - parses user queries into structured search items."""

import json
from typing import Dict
from langgraph.runtime import Runtime
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import INITIAL_PARSER_PROMPT
from agents.common.llm_utils import get_chat_model


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


async def intent_parser_node(state: AgentState, runtime: Runtime[AgentContext]) -> Dict:
    """Parse user query into structured search items with expanded queries.

    Args:
        state: Current agent state.
        runtime: LangGraph runtime with context.

    Returns:
        Updated state with search_items.
    """
    ctx = _get_context(runtime)
    query = state.query

    try:
        # Load model
        chat_model = await get_chat_model(
            model=ctx.chat_model,
            temperature=0.2
        )

        # Parse the query into individual items
        messages = [
            {"role": "system", "content": INITIAL_PARSER_PROMPT},
            {"role": "user", "content": query}
        ]

        response = await chat_model(messages)
        inputs = response if isinstance(response, str) else str(response)

        # Strip markdown code fences if present
        inputs = inputs.strip()
        if inputs.startswith("```json"):
            inputs = inputs[7:]  # Remove ```json
        elif inputs.startswith("```"):
            inputs = inputs[3:]  # Remove ```
        if inputs.endswith("```"):
            inputs = inputs[:-3]  # Remove trailing ```
        inputs = inputs.strip()

        parsed_inputs = json.loads(inputs)

        # Validate that we got a list
        if not isinstance(parsed_inputs, list):
            parsed_inputs = [parsed_inputs]

        return {"search_items": parsed_inputs}

    except Exception as e:
        # Fallback: create a simple search item from the original query
        print(f"Intent parser error: {e}")
        return {
            "search_items": [
                {
                    "original": query,
                    "query": query,
                    "expanded_query": query
                }
            ]
        }
