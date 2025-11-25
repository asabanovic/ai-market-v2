# Product engagement API endpoints - comments, votes, and engagement history
from flask import Blueprint, request, jsonify
from auth_api import require_jwt_auth
from app import db
from models import Product, ProductComment, ProductVote, UserEngagement, User
from datetime import datetime
from sqlalchemy import desc

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

        # Award credits (+2 for comments)
        user = User.query.get(user_id)
        user.extra_credits += 2

        # Record engagement
        engagement = UserEngagement(
            user_id=user_id,
            activity_type='comment',
            product_id=product_id,
            credits_earned=2
        )
        db.session.add(engagement)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment added successfully',
            'credits_earned': 2,
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

                # Deduct the credit they earned for voting
                user = User.query.get(user_id)
                if user.extra_credits > 0:
                    user.extra_credits -= 1
                    credits_earned = -1  # Indicate credit was taken back

                message = 'Vote removed'
            else:
                # Different vote - update it (no credit change, they already earned 1)
                existing_vote.vote_type = vote_type
                existing_vote.updated_at = datetime.now()
                message = 'Vote updated'
        else:
            # New vote - award credits (+1 for votes)
            vote = ProductVote(
                product_id=product_id,
                user_id=user_id,
                vote_type=vote_type
            )
            db.session.add(vote)

            # Award credits
            user = User.query.get(user_id)
            user.extra_credits += 1
            credits_earned = 1

            # Record engagement
            engagement = UserEngagement(
                user_id=user_id,
                activity_type=f'vote_{vote_type}',
                product_id=product_id,
                credits_earned=1
            )
            db.session.add(engagement)

            message = 'Vote recorded'

        db.session.commit()

        # Get current vote counts
        upvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='up').count()
        downvotes = ProductVote.query.filter_by(product_id=product_id, vote_type='down').count()

        return jsonify({
            'success': True,
            'message': message,
            'credits_earned': credits_earned,
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
