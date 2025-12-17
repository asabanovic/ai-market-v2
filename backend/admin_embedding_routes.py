"""
Admin API routes for managing product embeddings
Uses JWT authentication (not flask_login session)
"""
from flask import Blueprint, jsonify, request
from functools import wraps
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List

# Will be imported in main app
admin_embedding_bp = Blueprint('admin_embeddings', __name__, url_prefix='/api/admin/embeddings')

logger = logging.getLogger(__name__)

# In-memory job tracking (in production, use Redis or database)
embedding_jobs: Dict[str, Dict] = {}


def jwt_admin_required(f):
    """Decorator to require admin privileges via JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from auth_api import decode_jwt_token
        from models import User

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = decode_jwt_token(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401

            user_id = payload.get('user_id')
            user = User.query.get(user_id)
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin access required'}), 403

            # Store user info on request for use in route
            request.jwt_user = user
            request.jwt_user_id = user_id

        except Exception as e:
            logger.error(f"JWT auth error: {e}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)
    return decorated_function


@admin_embedding_bp.route('/products/status', methods=['GET'])
@jwt_admin_required
def get_products_embedding_status():
    """
    Get embedding status for all products

    Query params:
    - page: int (default 1)
    - per_page: int (default 50)
    - filter: 'all' | 'needs_refresh' | 'no_embedding' | 'up_to_date'

    Returns list of products with their embedding status
    """
    from app import db
    from models import Product
    from sqlalchemy import text

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    filter_type = request.args.get('filter', 'all')

    try:
        # Query products with embedding status
        query = text("""
            SELECT
                p.id,
                p.title,
                p.category,
                p.content_hash as product_hash,
                pe.content_hash as embedding_hash,
                pe.updated_at as embedding_updated_at,
                CASE
                    WHEN pe.product_id IS NULL THEN 'no_embedding'
                    WHEN pe.content_hash IS NULL THEN 'needs_refresh'
                    WHEN pe.content_hash != p.content_hash THEN 'needs_refresh'
                    ELSE 'up_to_date'
                END as status
            FROM products p
            LEFT JOIN product_embeddings pe ON p.id = pe.product_id
            ORDER BY p.id
        """)

        result = db.session.execute(query)
        all_products = [dict(row._mapping) for row in result]

        # Apply filter
        if filter_type == 'needs_refresh':
            filtered = [p for p in all_products if p['status'] == 'needs_refresh']
        elif filter_type == 'no_embedding':
            filtered = [p for p in all_products if p['status'] == 'no_embedding']
        elif filter_type == 'up_to_date':
            filtered = [p for p in all_products if p['status'] == 'up_to_date']
        else:
            filtered = all_products

        # Calculate pagination
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered[start:end]

        # Calculate stats
        stats = {
            'total': len(all_products),
            'no_embedding': len([p for p in all_products if p['status'] == 'no_embedding']),
            'needs_refresh': len([p for p in all_products if p['status'] == 'needs_refresh']),
            'up_to_date': len([p for p in all_products if p['status'] == 'up_to_date'])
        }

        return jsonify({
            'products': paginated,
            'stats': stats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Error getting embedding status: {e}")
        return jsonify({'error': str(e)}), 500


@admin_embedding_bp.route('/regenerate', methods=['POST'])
@jwt_admin_required
def regenerate_embeddings():
    """
    Trigger embedding regeneration for products

    Body:
    - product_ids: List[int] - specific products to regenerate
    - all: bool - regenerate all products (full rebuild)
    - changed_only: bool - only regenerate changed products (smart mode)

    Returns job_id for tracking progress
    """
    data = request.get_json()
    product_ids = data.get('product_ids', [])
    regenerate_all = data.get('all', False)
    changed_only = data.get('changed_only', False)

    # Get user email from JWT
    user_email = request.jwt_user.email if hasattr(request, 'jwt_user') else 'unknown'

    # Create job
    job_id = str(uuid.uuid4())
    embedding_jobs[job_id] = {
        'id': job_id,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'created_by': user_email,
        'product_ids': product_ids if product_ids else None,
        'mode': 'full' if regenerate_all else ('smart' if changed_only else 'selected'),
        'progress': {
            'total': 0,
            'processed': 0,
            'succeeded': 0,
            'failed': 0
        }
    }

    # Start background job
    thread = threading.Thread(
        target=run_embedding_job,
        args=(job_id, product_ids, regenerate_all, changed_only)
    )
    thread.daemon = True
    thread.start()

    logger.info(f"Started embedding job {job_id} by {user_email}")

    return jsonify({
        'job_id': job_id,
        'status': 'started',
        'message': 'Embedding regeneration started'
    }), 202


@admin_embedding_bp.route('/job/<job_id>', methods=['GET'])
@jwt_admin_required
def get_job_status(job_id):
    """Get status of an embedding generation job"""
    job = embedding_jobs.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job)


@admin_embedding_bp.route('/jobs', methods=['GET'])
@jwt_admin_required
def list_jobs():
    """List all embedding jobs (recent first)"""
    jobs_list = sorted(
        embedding_jobs.values(),
        key=lambda x: x['created_at'],
        reverse=True
    )

    # Limit to last 50 jobs
    return jsonify({'jobs': jobs_list[:50]})


def run_embedding_job(job_id: str, product_ids: List[int], regenerate_all: bool, changed_only: bool):
    """
    Background worker function to run embedding generation

    This runs in a separate thread and updates the job status
    """
    try:
        # Import here to avoid circular imports
        from refresh_embeddings import refresh_product_embeddings

        # Update job status
        embedding_jobs[job_id]['status'] = 'processing'
        embedding_jobs[job_id]['started_at'] = datetime.now().isoformat()

        logger.info(f"Processing embedding job {job_id}")

        # Run the embedding refresh
        if product_ids:
            # Specific products
            stats = refresh_product_embeddings(product_ids=product_ids)
        elif regenerate_all:
            # Full rebuild
            stats = refresh_product_embeddings(full_rebuild=True)
        else:
            # Smart mode (changed only)
            stats = refresh_product_embeddings(full_rebuild=False)

        # Update job with results
        embedding_jobs[job_id]['status'] = 'completed'
        embedding_jobs[job_id]['completed_at'] = datetime.now().isoformat()
        embedding_jobs[job_id]['progress'] = stats

        logger.info(f"Completed embedding job {job_id}: {stats}")

    except Exception as e:
        logger.error(f"Error in embedding job {job_id}: {e}", exc_info=True)
        embedding_jobs[job_id]['status'] = 'failed'
        embedding_jobs[job_id]['error'] = str(e)
        embedding_jobs[job_id]['failed_at'] = datetime.now().isoformat()


# Stats endpoint
@admin_embedding_bp.route('/stats', methods=['GET'])
@jwt_admin_required
def get_embedding_stats():
    """Get overall embedding statistics"""
    from app import db
    from sqlalchemy import text

    try:
        query = text("""
            SELECT
                COUNT(*) as total_products,
                COUNT(pe.product_id) as products_with_embeddings,
                COUNT(CASE WHEN pe.content_hash IS NULL THEN 1 END) as needs_hash_update,
                COUNT(CASE WHEN pe.content_hash != p.content_hash THEN 1 END) as hash_mismatch
            FROM products p
            LEFT JOIN product_embeddings pe ON p.id = pe.product_id
        """)

        result = db.session.execute(query).fetchone()

        return jsonify({
            'total_products': result.total_products,
            'with_embeddings': result.products_with_embeddings,
            'needs_refresh': result.needs_hash_update + result.hash_mismatch,
            'up_to_date': result.products_with_embeddings - result.needs_hash_update - result.hash_mismatch
        })

    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        return jsonify({'error': str(e)}), 500


@admin_embedding_bp.route('/vectorize-batch', methods=['POST'])
@jwt_admin_required
def vectorize_batch():
    """
    Manually trigger batch vectorization for specific products or all products

    Body:
    - product_ids: List[int] - specific products (optional, if not provided vectorizes all)
    - force: bool - force re-vectorization even if up to date (default: false)
    """
    data = request.get_json() or {}
    product_ids = data.get('product_ids')
    force = data.get('force', False)

    try:
        from auto_vectorize import batch_vectorize_products

        stats = batch_vectorize_products(product_ids=product_ids, force=force)

        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Vectorized {stats['succeeded']}/{stats['processed']} products"
        })

    except Exception as e:
        logger.error(f"Batch vectorization error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
