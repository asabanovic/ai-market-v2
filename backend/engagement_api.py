# Product engagement API endpoints - comments, votes, reports, and engagement history
from flask import Blueprint, request, jsonify
from auth_api import require_jwt_auth, decode_jwt_token
from app import db
from models import Product, ProductComment, ProductVote, UserEngagement, User, ProductReport, Business
from datetime import datetime
from sqlalchemy import desc, func

engagement_bp = Blueprint('engagement', __name__, url_prefix='/api')

# ==================== PRODUCT COMMENTS ====================

@engagement_bp.route('/products/<int:product_id>/comments', methods=['GET'])
def get_product_comments(product_id):
    """Get all comments for a product (latest first)"""
    try:
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get all comments for this product (latest first)
        comments = ProductComment.query.filter_by(product_id=product_id)\
            .order_by(desc(ProductComment.created_at))\
            .all()

        comments_data = []
        for comment in comments:
            # Get user info
            user = User.query.get(comment.user_id)
            comments_data.append({
                'id': comment.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat(),
                'user': {
                    'id': user.id if user else None,
                    'first_name': user.first_name if user else 'Anonymous',
                    'last_name': user.last_name if user else '',
                }
            })

        return jsonify({
            'success': True,
            'comments': comments_data,
            'count': len(comments_data)
        })

    except Exception as e:
        print(f"Error getting comments: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/products/<int:product_id>/comments', methods=['POST'])
@require_jwt_auth
def add_product_comment(product_id):
    """Add a comment to a product (requires authentication)"""
    try:
        user_id = request.current_user_id
        data = request.get_json()

        # Validate input
        comment_text = data.get('comment_text', '').strip()
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400

        # Validate length (20-1000 characters)
        if len(comment_text) < 20:
            return jsonify({'error': 'Comment must be at least 20 characters'}), 400
        if len(comment_text) > 1000:
            return jsonify({'error': 'Comment must be less than 1000 characters'}), 400

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Create comment
        comment = ProductComment(
            product_id=product_id,
            user_id=user_id,
            comment_text=comment_text
        )
        db.session.add(comment)

        # Award credits (+5 for comments)
        user = User.query.get(user_id)
        user.extra_credits += 5

        # Record engagement
        engagement = UserEngagement(
            user_id=user_id,
            activity_type='comment',
            product_id=product_id,
            credits_earned=5
        )
        db.session.add(engagement)

        db.session.commit()

        # Get total credits for gamified display (remaining weekly + extra)
        regular_credits_remaining = max(0, (user.weekly_credits or 0) - (user.weekly_credits_used or 0))
        total_credits = regular_credits_remaining + (user.extra_credits or 0)

        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'credits_earned': 5,
            'total_credits': total_credits,
            'comment': {
                'id': comment.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat(),
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error adding comment: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== PRODUCT VOTES ====================

@engagement_bp.route('/products/<int:product_id>/vote', methods=['POST'])
@require_jwt_auth
def vote_product(product_id):
    """Vote on a product (thumbs up or down)"""
    try:
        user_id = request.current_user_id
        data = request.get_json()

        # Validate input
        vote_type = data.get('vote_type', '').lower()
        if vote_type not in ['up', 'down']:
            return jsonify({'error': 'Vote type must be "up" or "down"'}), 400

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Check if user already voted
        existing_vote = ProductVote.query.filter_by(
            product_id=product_id,
            user_id=user_id
        ).first()

        credits_earned = 0
        message = ''

        if existing_vote:
            # User is changing their vote
            if existing_vote.vote_type == vote_type:
                # Same vote - remove it (toggle off)
                db.session.delete(existing_vote)

                # Deduct the credits they earned for voting
                user = User.query.get(user_id)
                if user.extra_credits >= 2:
                    user.extra_credits -= 2
                    credits_earned = -2  # Indicate credits were taken back

                message = 'Vote removed'
            else:
                # Different vote - update it (no credit change, they already earned 1)
                existing_vote.vote_type = vote_type
                existing_vote.updated_at = datetime.now()
                message = 'Vote updated'
        else:
            # New vote - award credits (+2 for votes)
            vote = ProductVote(
                product_id=product_id,
                user_id=user_id,
                vote_type=vote_type
            )
            db.session.add(vote)

            # Award credits
            user = User.query.get(user_id)
            user.extra_credits += 2
            credits_earned = 2

            # Record engagement
            engagement = UserEngagement(
                user_id=user_id,
                activity_type=f'vote_{vote_type}',
                product_id=product_id,
                credits_earned=2
            )
            db.session.add(engagement)

            message = 'Vote recorded'

        db.session.commit()

        # Get current vote counts
        upvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='up').count()
        downvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='down').count()

        # Get updated total credits (remaining weekly + extra)
        user = User.query.get(user_id)
        regular_credits_remaining = max(0, (user.weekly_credits or 0) - (user.weekly_credits_used or 0))
        total_credits = regular_credits_remaining + (user.extra_credits or 0)

        return jsonify({
            'success': True,
            'message': message,
            'credits_earned': credits_earned,
            'total_credits': total_credits,
            'vote_stats': {
                'upvotes': upvotes,
                'downvotes': downvotes
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error voting on product: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/products/<int:product_id>/votes', methods=['GET'])
def get_product_votes(product_id):
    """Get vote statistics for a product"""
    try:
        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get vote counts
        upvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='up').count()
        downvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='down').count()

        # If user is authenticated, get their vote
        user_vote = None
        try:
            if hasattr(request, 'current_user_id') and request.current_user_id:
                user_vote_obj = ProductVote.query.filter_by(
                    product_id=product_id,
                    user_id=request.current_user_id
                ).first()
                if user_vote_obj:
                    user_vote = user_vote_obj.vote_type
        except:
            pass

        return jsonify({
            'success': True,
            'upvotes': upvotes,
            'downvotes': downvotes,
            'user_vote': user_vote
        })

    except Exception as e:
        print(f"Error getting votes: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== USER ENGAGEMENT HISTORY ====================

@engagement_bp.route('/user/engagement-history', methods=['GET'])
@require_jwt_auth
def get_engagement_history():
    """Get user's engagement history (comments, votes)"""
    try:
        user_id = request.current_user_id

        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Query engagements
        engagements_query = UserEngagement.query.filter_by(user_id=user_id)\
            .order_by(desc(UserEngagement.created_at))

        # Paginate
        pagination = engagements_query.paginate(page=page, per_page=per_page, error_out=False)
        engagements = pagination.items

        # Format data
        engagement_data = []
        for eng in engagements:
            product = Product.query.get(eng.product_id)
            engagement_data.append({
                'id': eng.id,
                'date': eng.created_at.isoformat(),
                'activity': eng.activity_type,
                'product': {
                    'id': product.id if product else None,
                    'title': product.title if product else 'Unknown Product'
                },
                'credits_earned': eng.credits_earned
            })

        return jsonify({
            'success': True,
            'engagements': engagement_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })

    except Exception as e:
        print(f"Error getting engagement history: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== PRODUCT REPORTS ====================

@engagement_bp.route('/products/<int:product_id>/report/status', methods=['GET'])
@require_jwt_auth
def get_report_status(product_id):
    """Check if user has already reported this product."""
    try:
        user_id = request.current_user_id

        # Check if user has any report for this product (any status)
        existing_report = ProductReport.query.filter_by(
            product_id=product_id,
            user_id=user_id
        ).first()

        return jsonify({
            'success': True,
            'has_reported': existing_report is not None,
            'status': existing_report.status if existing_report else None
        })

    except Exception as e:
        print(f"Error checking report status: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/products/<int:product_id>/report', methods=['POST'])
@require_jwt_auth
def report_product(product_id):
    """Report a product issue (requires authentication). Awards 5 credits."""
    try:
        user_id = request.current_user_id
        data = request.get_json() or {}

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Proizvod nije pronadjen'}), 404

        # Check if user already reported this product (any status - prevent duplicate reports)
        existing_report = ProductReport.query.filter_by(
            product_id=product_id,
            user_id=user_id
        ).first()

        if existing_report:
            return jsonify({
                'error': 'Vec ste prijavili ovaj proizvod. Cekamo pregled.',
                'already_reported': True
            }), 400

        # Get optional reason (explanation)
        reason = data.get('reason', '').strip() if data.get('reason') else None

        # Create the report
        report = ProductReport(
            product_id=product_id,
            user_id=user_id,
            reason=reason
        )
        db.session.add(report)

        # Award credits (+5 for reporting)
        user = User.query.get(user_id)
        user.extra_credits += 5

        # Record engagement
        engagement = UserEngagement(
            user_id=user_id,
            activity_type='report',
            product_id=product_id,
            credits_earned=5
        )
        db.session.add(engagement)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Hvala na prijavi! Pregledacemo ovaj proizvod.',
            'credits_earned': 5,
            'report_id': report.id
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error reporting product: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/products/<int:product_id>/report', methods=['PUT'])
@require_jwt_auth
def update_report(product_id):
    """Update an existing report with additional feedback (reason)."""
    try:
        user_id = request.current_user_id
        data = request.get_json() or {}

        # Find the user's pending report for this product
        report = ProductReport.query.filter_by(
            product_id=product_id,
            user_id=user_id,
            status='pending'
        ).first()

        if not report:
            return jsonify({'error': 'Prijava nije pronadjena'}), 404

        # Update the reason
        reason = data.get('reason', '').strip()
        if reason:
            report.reason = reason
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Prijava je azurirana. Hvala na dodatnim informacijama!'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating report: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== ADMIN REPORTS MANAGEMENT ====================

@engagement_bp.route('/admin/reports', methods=['GET'])
@require_jwt_auth
def get_all_reports():
    """Get all product reports (admin only)"""
    try:
        user_id = request.current_user_id
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({'error': 'Nemate dozvolu za ovu akciju'}), 403

        # Get query parameters
        status_filter = request.args.get('status', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Build query
        query = ProductReport.query.order_by(desc(ProductReport.created_at))

        if status_filter:
            query = query.filter_by(status=status_filter)

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        reports = pagination.items

        # Format data
        reports_data = []
        for report in reports:
            product = Product.query.get(report.product_id)
            reporter = User.query.get(report.user_id)
            business = Business.query.get(product.business_id) if product else None

            reports_data.append({
                'id': report.id,
                'product': {
                    'id': product.id if product else None,
                    'title': product.title if product else 'Obrisan proizvod',
                    'image_path': product.image_path if product else None,
                    'base_price': product.base_price if product else None,
                    'discount_price': product.discount_price if product else None,
                    'business': {
                        'id': business.id if business else None,
                        'name': business.name if business else 'Nepoznato'
                    } if business else None
                } if product else None,
                'reporter': {
                    'id': reporter.id if reporter else None,
                    'first_name': reporter.first_name if reporter else 'Nepoznat',
                    'last_name': reporter.last_name if reporter else '',
                    'email': reporter.email if reporter else None
                },
                'reason': report.reason,
                'status': report.status,
                'admin_notes': report.admin_notes,
                'created_at': report.created_at.isoformat(),
                'reviewed_at': report.reviewed_at.isoformat() if report.reviewed_at else None
            })

        return jsonify({
            'success': True,
            'reports': reports_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'stats': {
                'pending': ProductReport.query.filter_by(status='pending').count(),
                'reviewed': ProductReport.query.filter_by(status='reviewed').count(),
                'resolved': ProductReport.query.filter_by(status='resolved').count(),
                'dismissed': ProductReport.query.filter_by(status='dismissed').count()
            }
        })

    except Exception as e:
        print(f"Error getting reports: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/admin/reports/<int:report_id>', methods=['PUT'])
@require_jwt_auth
def update_report_status(report_id):
    """Update a report's status (admin only)"""
    try:
        user_id = request.current_user_id
        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return jsonify({'error': 'Nemate dozvolu za ovu akciju'}), 403

        data = request.get_json()
        report = ProductReport.query.get(report_id)

        if not report:
            return jsonify({'error': 'Prijava nije pronadjena'}), 404

        # Update status
        new_status = data.get('status')
        if new_status and new_status in ['pending', 'reviewed', 'resolved', 'dismissed']:
            report.status = new_status
            report.reviewed_at = datetime.now()
            report.reviewed_by = user_id

        # Update admin notes
        if 'admin_notes' in data:
            report.admin_notes = data.get('admin_notes')

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Prijava je azurirana',
            'report': {
                'id': report.id,
                'status': report.status,
                'admin_notes': report.admin_notes,
                'reviewed_at': report.reviewed_at.isoformat() if report.reviewed_at else None
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating report: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== BULK ENGAGEMENT STATS ====================

@engagement_bp.route('/products/engagement-stats', methods=['POST'])
def get_bulk_engagement_stats():
    """Get engagement stats (votes, comments) for multiple products at once.

    This is more efficient than making individual requests for each product.
    Also returns the current user's votes if authenticated.
    """
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])

        if not product_ids or len(product_ids) > 100:
            return jsonify({'error': 'Provide 1-100 product IDs'}), 400

        # Get current user if authenticated
        user_id = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
                payload = decode_jwt_token(token)
                if payload:
                    user_id = payload.get('user_id')
            except:
                pass

        # Get vote counts (upvotes and downvotes)
        upvote_counts = db.session.query(
            ProductVote.product_id,
            func.count(ProductVote.id)
        ).filter(
            ProductVote.product_id.in_(product_ids),
            ProductVote.vote_type == 'up'
        ).group_by(ProductVote.product_id).all()

        downvote_counts = db.session.query(
            ProductVote.product_id,
            func.count(ProductVote.id)
        ).filter(
            ProductVote.product_id.in_(product_ids),
            ProductVote.vote_type == 'down'
        ).group_by(ProductVote.product_id).all()

        # Get comment counts
        comment_counts = db.session.query(
            ProductComment.product_id,
            func.count(ProductComment.id)
        ).filter(
            ProductComment.product_id.in_(product_ids)
        ).group_by(ProductComment.product_id).all()

        # Get user's votes if authenticated
        user_votes = {}
        if user_id:
            votes = ProductVote.query.filter(
                ProductVote.product_id.in_(product_ids),
                ProductVote.user_id == user_id
            ).all()
            for vote in votes:
                user_votes[vote.product_id] = vote.vote_type

        # Build response
        upvotes_map = {pid: count for pid, count in upvote_counts}
        downvotes_map = {pid: count for pid, count in downvote_counts}
        comments_map = {pid: count for pid, count in comment_counts}

        stats = {}
        for pid in product_ids:
            stats[str(pid)] = {
                'upvotes': upvotes_map.get(pid, 0),
                'downvotes': downvotes_map.get(pid, 0),
                'comments': comments_map.get(pid, 0),
                'user_vote': user_votes.get(pid, None)
            }

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        print(f"Error getting bulk engagement stats: {e}")
        return jsonify({'error': str(e)}), 500


@engagement_bp.route('/products/<int:product_id>/quick-comment', methods=['POST'])
@require_jwt_auth
def add_quick_comment(product_id):
    """Add a quick comment to a product (shorter minimum, for quick feedback).

    Quick comments are for short reactions (min 5 chars instead of 20).
    Awards +5 credits for sharing experience.
    """
    try:
        user_id = request.current_user_id
        data = request.get_json()

        # Validate input
        comment_text = data.get('comment_text', '').strip()
        if not comment_text:
            return jsonify({'error': 'Komentar je obavezan'}), 400

        # Shorter minimum for quick comments (5 chars)
        if len(comment_text) < 5:
            return jsonify({'error': 'Komentar mora imati najmanje 5 karaktera'}), 400
        if len(comment_text) > 280:
            return jsonify({'error': 'Komentar mora imati manje od 280 karaktera'}), 400

        # Check if product exists
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Proizvod nije pronadjen'}), 404

        # Create comment
        comment = ProductComment(
            product_id=product_id,
            user_id=user_id,
            comment_text=comment_text
        )
        db.session.add(comment)

        # Award credits (+5 for quick comments)
        user = User.query.get(user_id)
        user.extra_credits += 5

        # Record engagement
        engagement = UserEngagement(
            user_id=user_id,
            activity_type='quick_comment',
            product_id=product_id,
            credits_earned=5
        )
        db.session.add(engagement)

        db.session.commit()

        # Get updated comment count
        comment_count = ProductComment.query.filter_by(product_id=product_id).count()

        # Get total credits for gamified display (remaining weekly + extra)
        regular_credits_remaining = max(0, (user.weekly_credits or 0) - (user.weekly_credits_used or 0))
        total_credits = regular_credits_remaining + (user.extra_credits or 0)

        return jsonify({
            'success': True,
            'message': 'Komentar dodan!',
            'credits_earned': 5,
            'total_credits': total_credits,
            'comment_count': comment_count,
            'comment': {
                'id': comment.id,
                'comment_text': comment.comment_text,
                'created_at': comment.created_at.isoformat(),
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error adding quick comment: {e}")
        return jsonify({'error': str(e)}), 500