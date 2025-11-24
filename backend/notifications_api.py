"""
Notification API endpoints
Handles user notifications for discount alerts and other events
"""

from flask import Blueprint, request, jsonify
from app import db
from models import Notification, Product, User, Favorite
from auth_api import require_jwt_auth
from datetime import datetime, timedelta
from sqlalchemy import and_

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/api/notifications', methods=['GET'])
@require_jwt_auth
def get_notifications():
    """
    Get all notifications for the current user
    Query params:
    - unread_only: bool (default: false) - Only return unread notifications
    - limit: int (default: 50) - Max number of notifications to return
    """
    try:
        user_id = request.current_user_id
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 50)), 100)  # Cap at 100

        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'notifications': [{
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'product_id': n.product_id,
                'is_read': n.is_read,
                'action_url': n.action_url,
                'created_at': n.created_at.isoformat() if n.created_at else None
            } for n in notifications]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notifications_bp.route('/api/notifications/unread-count', methods=['GET'])
@require_jwt_auth
def get_unread_count():
    """Get count of unread notifications for badge display"""
    try:
        user_id = request.current_user_id
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

        return jsonify({
            'success': True,
            'unread_count': count
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@require_jwt_auth
def mark_notification_read(notification_id):
    """Mark a specific notification as read"""
    try:
        user_id = request.current_user_id

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404

        notification.is_read = True
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notifications_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@require_jwt_auth
def mark_all_read():
    """Mark all notifications as read for the current user"""
    try:
        user_id = request.current_user_id

        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({'is_read': True})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notifications_bp.route('/api/notifications/<int:notification_id>', methods=['DELETE'])
@require_jwt_auth
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        user_id = request.current_user_id

        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()

        if not notification:
            return jsonify({
                'success': False,
                'error': 'Notification not found'
            }), 404

        db.session.delete(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Notification deleted'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@notifications_bp.route('/api/notifications/clear-all', methods=['DELETE'])
@require_jwt_auth
def clear_all_notifications():
    """Delete all notifications for the current user"""
    try:
        user_id = request.current_user_id

        Notification.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'All notifications cleared'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== HELPER FUNCTIONS ====================

def create_discount_notification(user_id, product_id, discount_percentage):
    """
    Create a notification when a favorited product goes on discount

    Args:
        user_id: User ID to notify
        product_id: Product that went on discount
        discount_percentage: The discount percentage

    Returns:
        Notification object
    """
    try:
        product = Product.query.get(product_id)
        if not product:
            return None

        # Check if notification already exists (within last 24 hours)
        existing = Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.product_id == product_id,
                Notification.notification_type == 'discount_alert',
                Notification.created_at >= datetime.now() - timedelta(hours=24)
            )
        ).first()

        if existing:
            return existing  # Don't create duplicate notification

        notification = Notification(
            user_id=user_id,
            notification_type='discount_alert',
            title=f'🎉 Popust na {product.title}!',
            message=f'Proizvod koji pratite sada ima {discount_percentage}% popusta!',
            product_id=product_id,
            action_url=f'/proizvodi/{product_id}'
        )

        db.session.add(notification)
        db.session.commit()

        return notification

    except Exception as e:
        db.session.rollback()
        print(f"Error creating discount notification: {e}")
        return None


def check_favorites_for_discounts():
    """
    Background task: Check all user favorites for new discounts
    This should be run periodically (e.g., every hour or when products are updated)

    Returns:
        int: Number of notifications created
    """
    try:
        # Get all favorited products
        favorites = Favorite.query.all()
        notifications_created = 0

        for favorite in favorites:
            product = favorite.product

            # Check if product has a discount
            if product.has_discount and product.discount_percentage > 0:
                # Check if user wants notifications
                user = User.query.get(favorite.user_id)
                if not user or user.notification_preferences == 'none':
                    continue

                # Create notification
                notification = create_discount_notification(
                    user_id=favorite.user_id,
                    product_id=product.id,
                    discount_percentage=product.discount_percentage
                )

                if notification:
                    notifications_created += 1

        return notifications_created

    except Exception as e:
        print(f"Error checking favorites for discounts: {e}")
        return 0
