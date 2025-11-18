"""General assistant node for generic queries."""

from typing import Dict
from langgraph.runtime import Runtime
from agents.state import AgentState
from agents.context import AgentContext
from agents.prompts import GENERAL_ASSISTANT_PROMPT
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


async def general_assistant_node(state: AgentState, runtime: Runtime[AgentContext]) -> Dict:
    """Handle general queries about the marketplace.

    Args:
        state: Current agent state.
        runtime: LangGraph runtime with context.

    Returns:
        Updated state with assistant response.
    """
    context = _get_context(runtime)
    query = state.query

    try:
        chat_model = await get_chat_model(
            model=context.chat_model,
            temperature=context.temperature
        )

        messages = [
            {"role": "system", "content": GENERAL_ASSISTANT_PROMPT},
            {"role": "user", "content": query}
        ]

        response = await chat_model(messages)

        return {
            "results": [],
            "explanation": response.strip(),
            "metadata": {
                **state.metadata,
                "response_type": "general_assistant"
            }
        }

    except Exception as e:
        return {
            "results": [],
            "explanation": "Izvini, trenutno ne mogu odgovoriti na to pitanje.",
            "error": f"General assistant error: {str(e)}"
        }
