"""Main LangGraph definition - Direct semantic search only."""

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import semantic_search_node, intent_parser_node

# Build the simplified graph - direct semantic search
# Using simpler StateGraph constructor for compatibility with langgraph 0.2.x
workflow = StateGraph(AgentState)

# Add only semantic search node
workflow.add_node("semantic_search", semantic_search_node)
workflow.add_node("intent_parser", intent_parser_node)

# Define edges - go directly to intent_parser
workflow.set_entry_point("intent_parser")
workflow.add_edge("intent_parser", "semantic_search")
workflow.add_edge("semantic_search", END)

# Compile the graph (without name parameter for compatibility)
graph = workflow.compile()

# For visualization (optional)
try:
    from IPython.display import Image, display
    import io

    def visualize_graph():
        """Visualize the graph structure."""
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            return Image(png_data)
        except Exception:
            return None
except ImportError:
    def visualize_graph():
        return None
