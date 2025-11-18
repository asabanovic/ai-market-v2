"""Unified API endpoint for AI agents with LangGraph."""

from flask import Blueprint, request, jsonify
from app import db
from agents.graph import graph
from agents.context import AgentContext
from agents.state import InputState, OutputState
from auth_api import require_jwt_auth

# Create blueprint
agents_api_bp = Blueprint('agents_api', __name__, url_prefix='/api')


@agents_api_bp.route('/search', methods=['POST'])
@require_jwt_auth
def unified_search():
    """Unified search endpoint - the main entry point for all user queries.

    This endpoint uses a supervisor pattern to automatically route queries
    to the appropriate specialized agent based on intent detection.

    Request JSON:
        - query (str): User's search query

    Returns:
        JSON response with results, explanation, and metadata.

    Examples:
        - "piletina ispod 10 KM" → Routes to semantic_search
        - "šta da napravim za ručak" → Routes to meal_planning
        - "koje trgovine su dostupne" → Routes to general assistant
    """
    try:
        data = request.get_json() or {}

        # Validate query
        query = data.get("query", "").strip()
        if not query:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400

        # Get user ID from JWT token
        user_id = request.current_user_id if hasattr(request, 'current_user_id') else None

        # Create input state
        input_state = InputState(
            query=query,
            user_id=user_id
        )

        # Create context with DB session
        context = AgentContext(db_session=db.session)

        # Invoke the graph asynchronously
        import asyncio
        result = asyncio.run(graph.ainvoke(
            input_state.__dict__,
            context=context
        ))

        # Extract output
        output = OutputState(
            query=result.get("query", query),
            intent=result.get("intent", "unknown"),
            results=result.get("results", []),
            explanation=result.get("explanation"),
            metadata=result.get("metadata", {}),
            error=result.get("error")
        )

        # Check for errors
        if output.error:
            return jsonify({
                "success": False,
                "error": output.error,
                "intent": output.intent
            }), 500

        return jsonify({
            "success": True,
            "query": output.query,
            "intent": output.intent,
            "results": output.results,
            "explanation": output.explanation,
            "metadata": output.metadata,
            "count": len(output.results)
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@agents_api_bp.route('/agents/info', methods=['GET'])
def agents_info():
    """Get information about available agents and capabilities.

    Returns:
        JSON with agent descriptions and capabilities.
    """
    return jsonify({
        "success": True,
        "system": "AI Pijaca Multi-Agent System",
        "architecture": "LangGraph with Supervisor Pattern",
        "capabilities": {
            "semantic_search": {
                "description": "Pretražuje proizvode koristeći semantičko razumijevanje",
                "features": [
                    "Vector similarity search",
                    "Price filtering (ispod X KM)",
                    "Category filtering",
                    "AI-generated explanations"
                ],
                "examples": [
                    "piletina",
                    "najjeftinija mljeveno meso",
                    "meso ispod 10 KM"
                ]
            },
            "meal_planning": {
                "description": "Predlaže ideje za obroke na osnovu dostupnih proizvoda",
                "features": [
                    "Meal suggestions for breakfast/lunch/dinner",
                    "Recipe generation",
                    "Budget-aware recommendations",
                    "Ingredient listing with prices"
                ],
                "examples": [
                    "šta da napravim za ručak",
                    "brza večera do 15 KM",
                    "ideje za doručak"
                ]
            },
            "general": {
                "description": "Odgovara na općenita pitanja o marketplace-u",
                "features": [
                    "Store information",
                    "Platform help",
                    "General Q&A"
                ],
                "examples": [
                    "koje trgovine su dostupne",
                    "kako funkcioniše AI Pijaca",
                    "radno vrijeme"
                ]
            }
        },
        "routing": "Automatic intent detection routes queries to the best agent"
    }), 200


# Backward compatibility endpoints (optional)
@agents_api_bp.route('/agents/semantic_search', methods=['POST'])
@require_jwt_auth
def semantic_search_direct():
    """Direct semantic search endpoint (backward compatibility).

    Bypasses supervisor and goes directly to semantic search.
    """
    try:
        data = request.get_json() or {}
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"success": False, "error": "Query required"}), 400

        # Build a subgraph for direct semantic search
        from langgraph.graph import StateGraph, END
        from agents.state import AgentState, InputState
        from agents.nodes.semantic_search import semantic_search_node

        # Create a simple graph with just semantic search
        builder = StateGraph(AgentState, input_schema=InputState, context_schema=AgentContext)
        builder.add_node("search", semantic_search_node)
        builder.add_edge("__start__", "search")
        builder.add_edge("search", END)
        direct_graph = builder.compile()

        # Create input with forced parameters
        input_state = InputState(query=query)
        context = AgentContext(
            db_session=db.session,
            default_k=data.get("k", 5)
        )

        # Run search
        import asyncio
        result = asyncio.run(direct_graph.ainvoke(
            input_state.__dict__,
            context=context
        ))

        return jsonify({
            "success": True,
            "query": query,
            "results": result.get("results", []),
            "explanation": result.get("explanation"),
            "count": len(result.get("results", []))
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
