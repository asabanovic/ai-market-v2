"""Unified API endpoint for AI agents with LangGraph."""

import json
from datetime import date
from flask import Blueprint, request, jsonify, current_app
from app import db
from agents.graph import graph
from agents.context import AgentContext
from agents.state import InputState, OutputState
from auth_api import require_jwt_auth, decode_jwt_token
from models import UserSearch, User, AnonymousSearch, SearchLog

# Create blueprint
agents_api_bp = Blueprint('agents_api', __name__, url_prefix='/api')


def get_user_id_from_token():
    """Extract user ID from JWT token in Authorization header."""
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if payload:
                return payload.get('user_id')
        except Exception as e:
            current_app.logger.warning(f"Failed to decode JWT token: {e}")
    return None


def parse_query_items(query):
    """Parse query into individual product items.

    Examples:
        - "brasno" -> ["brasno"]
        - "brasno, cokolada, mlijeko" -> ["brasno", "cokolada", "mlijeko"]
        - "lista: hljeb, mlijeko, jaja" -> ["hljeb", "mlijeko", "jaja"]

    Returns:
        list: List of individual item strings
    """
    # Remove common prefixes like "lista:", "trebam:", etc.
    query_clean = query
    for prefix in ['lista:', 'lista za kupovinu:', 'trebam:', 'želim:', 'treba mi:']:
        query_clean = query_clean.lower().replace(prefix, '')
        query_clean = query.replace(prefix.capitalize(), '').replace(prefix.upper(), '')

    # Parse by commas (most common separator)
    if ',' in query_clean:
        items = [item.strip() for item in query_clean.split(',') if item.strip()]
        return items

    # Parse by newlines
    if '\n' in query_clean:
        items = [item.strip() for item in query_clean.split('\n') if item.strip() and not item.strip().startswith('-')]
        return items

    # Single item
    return [query_clean.strip()] if query_clean.strip() else []


def count_products_in_query(query):
    """Count the number of products/items in a search query.

    Examples:
        - "brasno" -> 1
        - "brasno, cokolada, mlijeko" -> 3
        - "lista: hljeb, mlijeko, jaja" -> 3
    """
    items = parse_query_items(query)
    return max(len(items), 1)


def reset_daily_credits_if_needed(user):
    """Reset user's weekly credits if it's a new week (Monday)."""
    from datetime import datetime, timedelta
    today = date.today()

    # Check if we need to reset (it's Monday and reset date is before today)
    if user.weekly_credits_reset_date != today:
        # Calculate days since last reset
        days_since_reset = (today - user.weekly_credits_reset_date).days

        # Reset if it's been 7+ days (a week has passed)
        if days_since_reset >= 7:
            user.weekly_credits_used = 0
            # Set next reset to next Monday
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            user.weekly_credits_reset_date = today + timedelta(days=days_until_monday)
            db.session.commit()
            current_app.logger.info(f"Reset weekly credits for user {user.id}")


def check_and_deduct_credits(user, credits_needed):
    """Check if user has enough credits and deduct them.

    Returns:
        tuple: (success: bool, message: str, credits_remaining: int)
    """
    # Reset credits if it's a new week
    reset_daily_credits_if_needed(user)

    # Calculate total available credits (weekly + extra)
    weekly_remaining = user.weekly_credits - user.weekly_credits_used
    total_remaining = weekly_remaining + user.extra_credits

    if total_remaining < credits_needed:
        return False, f"Nemate dovoljno kredita. Potrebno: {credits_needed}, dostupno: {total_remaining}. Krediti se obnavljaju sljedeće sedmice!", total_remaining

    # Deduct from weekly credits first, then extra credits
    if weekly_remaining >= credits_needed:
        user.weekly_credits_used += credits_needed
    else:
        # Use remaining weekly credits
        user.weekly_credits_used = user.weekly_credits
        # Use extra credits for the rest
        remaining_needed = credits_needed - weekly_remaining
        user.extra_credits -= remaining_needed

    db.session.commit()
    new_total_remaining = (user.weekly_credits - user.weekly_credits_used) + user.extra_credits

    current_app.logger.info(f"Deducted {credits_needed} credits from user {user.id}. Remaining: {new_total_remaining}")
    return True, "Success", new_total_remaining


def get_available_credits(user):
    """Get user's available credits without deducting.

    Returns:
        int: Total available credits (weekly + extra)
    """
    # Reset credits if it's a new week
    reset_daily_credits_if_needed(user)

    weekly_remaining = user.weekly_credits - user.weekly_credits_used
    return weekly_remaining + user.extra_credits


def deduct_credits(user, credits_to_deduct):
    """Deduct a specific amount of credits from user.

    Returns:
        int: Credits remaining after deduction
    """
    weekly_remaining = user.weekly_credits - user.weekly_credits_used

    # Deduct from extra credits first, then weekly credits
    if user.extra_credits >= credits_to_deduct:
        user.extra_credits -= credits_to_deduct
    else:
        # Use all extra credits first
        remaining_needed = credits_to_deduct - user.extra_credits
        user.extra_credits = 0
        # Then use weekly credits
        user.weekly_credits_used += remaining_needed

    # Track lifetime spending
    user.lifetime_credits_spent += credits_to_deduct

    db.session.commit()

    new_weekly_remaining = user.weekly_credits - user.weekly_credits_used
    return new_weekly_remaining + user.extra_credits


def parse_user_agent(user_agent_string):
    """Parse user agent string to extract device type, browser, and OS"""
    if not user_agent_string:
        return {'device_type': None, 'browser': None, 'os': None}

    ua = user_agent_string.lower()

    # Detect device type
    device_type = 'desktop'
    if 'mobile' in ua or ('android' in ua and 'mobile' in ua):
        device_type = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device_type = 'tablet'
    elif 'android' in ua:
        device_type = 'tablet'

    # Detect OS
    os_name = None
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'linux' in ua:
        os_name = 'Linux'

    # Detect browser
    browser = None
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua and 'safari' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'

    return {
        'device_type': device_type,
        'browser': browser,
        'os': os_name
    }


def log_search(user_id, query, results, user_ip=None, only_discounted=False):
    """Log search to UserSearch table for tracking."""
    try:
        # Custom JSON encoder to handle date objects
        def json_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        # Get user agent and parse device info
        user_agent = request.headers.get('User-Agent', '')
        ua_info = parse_user_agent(user_agent)

        search_log = UserSearch(
            user_id=user_id,
            query=query,
            results=json.dumps(results, default=json_serializer) if results else json.dumps([]),
            user_ip=user_ip,
            user_agent=user_agent[:500] if user_agent else None,
            device_type=ua_info['device_type'],
            browser=ua_info['browser'],
            os=ua_info['os'],
            only_discounted=only_discounted
        )
        db.session.add(search_log)
        db.session.commit()
        discount_indicator = " [SAMO POPUSTI]" if only_discounted else ""
        current_app.logger.info(f"Logged search: '{query}'{discount_indicator} by {'user ' + str(user_id) if user_id else f'anonymous ({user_ip})'} ({ua_info['device_type']}/{ua_info['browser']})")
    except Exception as e:
        current_app.logger.error(f"Failed to log search: {e}")
        db.session.rollback()


def log_search_quality(query, results, metadata, search_items=None):
    """Log search results to SearchLog table for quality evaluation.

    Args:
        query: The original search query
        results: List of product results
        metadata: Search metadata including params
        search_items: Parsed query items from LLM (if any)
    """
    try:
        search_params = metadata.get("search_params", {})

        # Build results detail with scores
        results_detail = []
        rank = 1

        # Handle both grouped (dict) and flat (list) results
        if isinstance(results, dict):
            for group_name, group_products in results.items():
                for product in group_products:
                    results_detail.append({
                        "product_id": product.get("id"),
                        "title": product.get("title"),
                        "image_path": product.get("image_path"),
                        "group": group_name,
                        "similarity": product.get("similarity", 0),
                        "vector_score": product.get("vector_score", 0),
                        "text_score": product.get("text_score", 0),
                        "rank": rank,
                    })
                    rank += 1
        else:
            for product in results:
                results_detail.append({
                    "product_id": product.get("id"),
                    "title": product.get("title"),
                    "image_path": product.get("image_path"),
                    "group": product.get("search_group"),
                    "similarity": product.get("similarity", 0),
                    "vector_score": product.get("vector_score", 0),
                    "text_score": product.get("text_score", 0),
                    "rank": rank,
                })
                rank += 1

        # Create log entry
        log_entry = SearchLog(
            query=query,
            similarity_threshold=search_params.get("similarity_threshold"),
            k=search_params.get("k"),
            result_count=metadata.get("result_count", len(results_detail)),
            total_before_filter=metadata.get("total_before_filter"),
            results_detail=results_detail,
            parsed_query=search_items,
        )

        db.session.add(log_entry)
        db.session.commit()
        current_app.logger.info(f"Logged search quality: '{query}' with {len(results_detail)} results")

    except Exception as e:
        current_app.logger.error(f"Failed to log search quality: {e}")
        db.session.rollback()


@agents_api_bp.route('/search', methods=['POST'])
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
        user_id = get_user_id_from_token()

        # Get user's IP address for tracking (no limits for anonymous)
        user_ip = None
        credits_remaining = None
        is_anonymous = not user_id

        # Track if first search bonus should be awarded
        first_search_bonus_awarded = False

        # Track how many items were limited due to credits
        items_limited = 0
        original_query_count = 0

        # Check user credits if logged in
        if user_id:
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    "success": False,
                    "error": "User not found"
                }), 404

            # Count products in the query
            original_query_count = count_products_in_query(query)
            available_credits = get_available_credits(user)

            # If user has 0 credits, return error
            if available_credits <= 0:
                return jsonify({
                    "success": False,
                    "error": "credits_exhausted",
                    "message": "Nemate kredita. Krediti se obnavljaju sljedeće sedmice ili zaradite kredite komentarisanjem proizvoda!",
                    "credits_remaining": 0,
                    "credits_needed": original_query_count
                }), 403

            # Limit search to available credits if needed
            if original_query_count > available_credits:
                # Parse query items and take only what user can afford
                query_items = parse_query_items(query)
                limited_items = query_items[:available_credits]
                query = ', '.join(limited_items)
                items_limited = original_query_count - available_credits
                credits_to_charge = available_credits
                current_app.logger.info(f"Limited search from {original_query_count} to {available_credits} items for user {user_id}")
            else:
                credits_to_charge = original_query_count

            # Deduct credits for what we're actually searching
            credits_remaining = deduct_credits(user, credits_to_charge)

            # Check and award first search bonus (+3 extra credits)
            if not user.first_search_reward_claimed:
                user.extra_credits += 3
                user.first_search_reward_claimed = True
                # Recalculate remaining credits to include the bonus
                weekly_remaining = user.weekly_credits - user.weekly_credits_used
                credits_remaining = weekly_remaining + user.extra_credits
                first_search_bonus_awarded = True
                db.session.commit()
                current_app.logger.info(f"Awarded +3 first search bonus to user {user_id}")

        else:
            # Anonymous user - allow 1 free search, then require registration
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if user_ip:
                user_ip = user_ip.split(',')[0].strip()

            # Check if this IP has already used their free search
            if user_ip:
                existing_search = AnonymousSearch.query.filter_by(ip_address=user_ip).first()
                if existing_search:
                    return jsonify({
                        "success": False,
                        "error": "anonymous_limit_reached",
                        "message": "Iskoristili ste besplatnu pretragu. Molimo registrujte se da nastavite koristiti platformu.",
                        "requires_registration": True
                    }), 403

        # Get business_ids filter from request
        business_ids = data.get("business_ids")

        # Get only_discounted filter from request
        only_discounted = data.get("only_discounted", False)

        # Create input state
        input_state = InputState(
            query=query,
            user_id=user_id,
            business_ids=business_ids,
            only_discounted=only_discounted
        )

        # Create context with DB session
        context = AgentContext(db_session=db.session)

        # Invoke the graph asynchronously
        # Note: langgraph 0.2.x uses config dict instead of context parameter
        import asyncio
        result = asyncio.run(graph.ainvoke(
            input_state.__dict__,
            config={"configurable": {"context": context}}
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

        # Log search for tracking (both successful and failed)
        log_search(user_id, query, output.results, user_ip=user_ip, only_discounted=only_discounted)

        # Log search for quality evaluation (detailed scores)
        search_items = result.get("search_items")  # Parsed query items from LLM
        log_search_quality(query, output.results, output.metadata, search_items)

        # Record anonymous search (first time only)
        if is_anonymous and user_ip:
            try:
                anonymous_search = AnonymousSearch(ip_address=user_ip)
                db.session.add(anonymous_search)
                db.session.commit()
                current_app.logger.info(f"Recorded anonymous search for IP: {user_ip}")
            except Exception as e:
                current_app.logger.error(f"Failed to record anonymous search: {e}")
                db.session.rollback()

        # Check for errors
        if output.error:
            return jsonify({
                "success": False,
                "error": output.error,
                "intent": output.intent
            }), 500

        # For anonymous users, limit visible results to first 3 (rest are teasers)
        ANONYMOUS_TEASER_LIMIT = 3
        teaser_count = 0

        if is_anonymous and len(output.results) > ANONYMOUS_TEASER_LIMIT:
            # Mark results beyond the limit as teasers
            for i, result in enumerate(output.results):
                result['is_teaser'] = i >= ANONYMOUS_TEASER_LIMIT
            teaser_count = len(output.results) - ANONYMOUS_TEASER_LIMIT

        response_data = {
            "success": True,
            "query": output.query,
            "intent": output.intent,
            "results": output.results,
            "explanation": output.explanation,
            "metadata": output.metadata,
            "count": len(output.results),
            "is_anonymous": is_anonymous,
            "teaser_count": teaser_count  # Number of blurred results
        }

        # Add credits info for logged-in users
        if user_id and credits_remaining is not None:
            response_data["credits_remaining"] = credits_remaining

        # Add first search bonus flag if awarded
        if first_search_bonus_awarded:
            response_data["first_search_bonus"] = True

        # Add items_limited info if search was limited due to credits
        if items_limited > 0:
            response_data["items_limited"] = items_limited
            response_data["original_query_count"] = original_query_count
            response_data["limited_message"] = f"Prikazano {original_query_count - items_limited} od {original_query_count} proizvoda zbog ograničenih kredita. Zaradite kredite komentarisanjem proizvoda!"

        return jsonify(response_data), 200

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
        # Using simpler constructor for langgraph 0.2.x compatibility
        builder = StateGraph(AgentState)
        builder.add_node("search", semantic_search_node)
        builder.set_entry_point("search")
        builder.add_edge("search", END)
        direct_graph = builder.compile()

        # Create input with forced parameters
        input_state = InputState(query=query)
        context = AgentContext(
            db_session=db.session,
            default_k=data.get("k", 5)
        )

        # Run search with config dict pattern
        import asyncio
        result = asyncio.run(direct_graph.ainvoke(
            input_state.__dict__,
            config={"configurable": {"context": context}}
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
