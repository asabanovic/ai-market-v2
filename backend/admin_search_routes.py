"""
Admin API routes for search quality evaluation
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
from datetime import datetime

from app import db
from models import SearchLog, User
from agent_search import run_agent_search, format_agent_products
from auth_api import decode_jwt_token

admin_search_bp = Blueprint('admin_search', __name__, url_prefix='/api/admin/search')

logger = logging.getLogger(__name__)


def jwt_admin_required(f):
    """Decorator to require JWT admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)

            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401

            # Get user and check if admin
            user = User.query.filter_by(id=payload['user_id']).first()
            if not user or not user.is_admin:
                return jsonify({'error': 'Access denied'}), 403

            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({'error': 'Authentication failed'}), 401

    return decorated_function


@admin_search_bp.route('/logs', methods=['GET'])
@jwt_admin_required
def get_search_logs():
    """
    Get search logs for quality evaluation.

    Query params:
    - page: int (default 1)
    - per_page: int (default 50)
    - query: str (filter by query text)
    - min_results: int (filter by minimum result count)
    - max_results: int (filter by maximum result count)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    query_filter = request.args.get('query', '')
    min_results = request.args.get('min_results', type=int)
    max_results = request.args.get('max_results', type=int)

    try:
        # Build query - use db.session.query to avoid conflict with SearchLog.query column
        logs_query = db.session.query(SearchLog)

        if query_filter:
            logs_query = logs_query.filter(SearchLog.query.ilike(f'%{query_filter}%'))

        if min_results is not None:
            logs_query = logs_query.filter(SearchLog.result_count >= min_results)

        if max_results is not None:
            logs_query = logs_query.filter(SearchLog.result_count <= max_results)

        # Order by most recent first
        logs_query = logs_query.order_by(SearchLog.created_at.desc())

        # Paginate
        pagination = logs_query.paginate(page=page, per_page=per_page, error_out=False)

        logs = []
        for log in pagination.items:
            logs.append({
                'id': log.id,
                'query': log.query,
                'similarity_threshold': log.similarity_threshold,
                'k': log.k,
                'result_count': log.result_count,
                'total_before_filter': log.total_before_filter,
                'results_detail': log.results_detail,
                'parsed_query': log.parsed_query,
                'created_at': log.created_at.isoformat() if log.created_at else None,
            })

        return jsonify({
            'logs': logs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
            }
        })

    except Exception as e:
        logger.error(f"Error getting search logs: {e}")
        return jsonify({'error': str(e)}), 500


@admin_search_bp.route('/logs/<int:log_id>', methods=['GET'])
@jwt_admin_required
def get_search_log(log_id):
    """Get a single search log by ID."""
    try:
        log = db.session.query(SearchLog).get(log_id)
        if not log:
            return jsonify({'error': 'Log not found'}), 404

        return jsonify({
            'id': log.id,
            'query': log.query,
            'similarity_threshold': log.similarity_threshold,
            'k': log.k,
            'result_count': log.result_count,
            'total_before_filter': log.total_before_filter,
            'results_detail': log.results_detail,
            'parsed_query': log.parsed_query,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        })

    except Exception as e:
        logger.error(f"Error getting search log: {e}")
        return jsonify({'error': str(e)}), 500


@admin_search_bp.route('/rerun', methods=['POST'])
@jwt_admin_required
def rerun_search():
    """
    Re-run a search query to compare results.

    Body:
    - query: str (required) - the query to re-run
    - log_id: int (optional) - original log ID to compare against

    Returns new search results with comparison to original if log_id provided.
    """
    data = request.get_json()
    search_query = data.get('query')
    original_log_id = data.get('log_id')

    if not search_query:
        return jsonify({'error': 'Query is required'}), 400

    try:
        # Get original log for comparison if provided
        original_log = None
        if original_log_id:
            original_log = db.session.query(SearchLog).get(original_log_id)

        # Run new search
        result = run_agent_search(query=search_query)

        # Format products
        products = format_agent_products(result.get('products', []))

        # Build new results detail for comparison
        new_results_detail = []
        for i, product in enumerate(products):
            new_results_detail.append({
                'product_id': product.get('id'),
                'title': product.get('title'),
                'similarity': product.get('similarity_score', 0),
                'rank': i + 1,
            })

        # Build comparison if original log exists
        comparison = None
        if original_log and original_log.results_detail:
            original_products = {r['product_id']: r for r in original_log.results_detail}
            new_products = {r['product_id']: r for r in new_results_detail}

            # Find products in both, only in original, only in new
            both_ids = set(original_products.keys()) & set(new_products.keys())
            only_original_ids = set(original_products.keys()) - set(new_products.keys())
            only_new_ids = set(new_products.keys()) - set(original_products.keys())

            # Calculate score changes for products in both
            score_changes = []
            for pid in both_ids:
                orig = original_products[pid]
                new = new_products[pid]
                score_changes.append({
                    'product_id': pid,
                    'title': new.get('title') or orig.get('title'),
                    'original_score': orig.get('similarity', 0),
                    'new_score': new.get('similarity', 0),
                    'score_change': new.get('similarity', 0) - orig.get('similarity', 0),
                    'original_rank': orig.get('rank'),
                    'new_rank': new.get('rank'),
                })

            comparison = {
                'products_in_both': len(both_ids),
                'products_only_in_original': len(only_original_ids),
                'products_only_in_new': len(only_new_ids),
                'score_changes': sorted(score_changes, key=lambda x: abs(x['score_change']), reverse=True),
                'avg_score_original': sum(r.get('similarity', 0) for r in original_log.results_detail) / len(original_log.results_detail) if original_log.results_detail else 0,
                'avg_score_new': sum(r.get('similarity', 0) for r in new_results_detail) / len(new_results_detail) if new_results_detail else 0,
            }

        return jsonify({
            'query': search_query,
            'products': products,
            'result_count': len(products),
            'explanation': result.get('explanation'),
            'metadata': result.get('metadata', {}),
            'comparison': comparison,
            'original_log_id': original_log_id,
        })

    except Exception as e:
        logger.error(f"Error re-running search: {e}")
        return jsonify({'error': str(e)}), 500


@admin_search_bp.route('/stats', methods=['GET'])
@jwt_admin_required
def get_search_stats():
    """Get search statistics for quality evaluation."""
    from sqlalchemy import func

    try:
        # Get overall stats - use db.session.query to avoid conflict with SearchLog.query column
        total_searches = db.session.query(SearchLog).count()
        zero_result_searches = db.session.query(SearchLog).filter(SearchLog.result_count == 0).count()

        # Get average result count
        avg_results = db.session.query(func.avg(SearchLog.result_count)).scalar() or 0

        # Get top queries (most searched) - SearchLog.query is the column name
        top_queries = db.session.query(
            SearchLog.query,
            func.count(SearchLog.id).label('count'),
            func.avg(SearchLog.result_count).label('avg_results')
        ).group_by(SearchLog.query).order_by(func.count(SearchLog.id).desc()).limit(20).all()

        # Get queries with zero results
        zero_result_queries = db.session.query(
            SearchLog.query,
            func.count(SearchLog.id).label('count')
        ).filter(SearchLog.result_count == 0).group_by(SearchLog.query).order_by(func.count(SearchLog.id).desc()).limit(20).all()

        return jsonify({
            'total_searches': total_searches,
            'zero_result_searches': zero_result_searches,
            'zero_result_rate': (zero_result_searches / total_searches * 100) if total_searches > 0 else 0,
            'avg_results_per_search': round(float(avg_results), 2),
            'top_queries': [{'query': q[0], 'count': q[1], 'avg_results': round(float(q[2]), 2)} for q in top_queries],
            'zero_result_queries': [{'query': q[0], 'count': q[1]} for q in zero_result_queries],
        })

    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        return jsonify({'error': str(e)}), 500


@admin_search_bp.route('/logs/<int:log_id>', methods=['DELETE'])
@jwt_admin_required
def delete_search_log(log_id):
    """Delete a search log entry."""
    try:
        log = db.session.query(SearchLog).get(log_id)
        if not log:
            return jsonify({'error': 'Log not found'}), 404

        db.session.delete(log)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Log deleted'})

    except Exception as e:
        logger.error(f"Error deleting search log: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
