"""
Support Messages API - Admin and user support chat functionality
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from auth_api import require_jwt_auth
from models import db, User, SupportMessage, UserFeedback
from sendgrid_utils import send_email, get_base_template, get_button, get_magic_link_url

support_bp = Blueprint('support', __name__, url_prefix='/api/support')

logger = logging.getLogger(__name__)


def send_support_notification_email(user: User, message_preview: str) -> bool:
    """Send email notification when admin sends a support message"""
    if not user.email:
        logger.warning(f"Cannot send support notification - user {user.id} has no email")
        return False

    # Get magic link URL for auto-login to support page
    support_url = get_magic_link_url('/podrska', user.id, 'support_message')

    # Truncate message preview
    preview = message_preview[:200] + '...' if len(message_preview) > 200 else message_preview

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Nova poruka od Popust.ba podrške</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani,</p>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Imate novu poruku od našeg tima podrške:</p>

<div style="margin:20px 0;padding:16px;background:#F3F4F6;border-radius:8px;border-left:4px solid #7C3AED;">
<p style="margin:0;font-size:14px;color:#374151;line-height:1.6;font-style:italic;">"{preview}"</p>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Kliknite na dugme ispod da vidite cijelu poruku i odgovorite:</p>

{get_button("Pogledaj poruku", support_url, "#7C3AED", campaign="support_message")}

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;">
<p style="margin:0;font-size:13px;color:#666;line-height:1.5;">
Ovaj email je poslan jer ste korisnik Popust.ba platforme. Ako imate pitanja, slobodno odgovorite na ovu poruku.
</p>
</div>
'''

    subject = "✉️ Nova poruka od Popust.ba podrške"
    html = get_base_template(content, "#7C3AED")
    return send_email(user.email, subject, html)


# ==================== ADMIN ENDPOINTS ====================

@support_bp.route('/admin/search-users', methods=['GET'])
@require_jwt_auth
def admin_search_users():
    """Search users by email for starting new conversations"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    query = request.args.get('q', '').strip().lower()
    if len(query) < 2:
        return jsonify({'success': True, 'users': []})

    # Search users by email (partial match)
    users = User.query.filter(
        User.email.ilike(f'%{query}%')
    ).limit(10).all()

    result = []
    for user in users:
        result.append({
            'id': user.id,
            'email': user.email,
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
        })

    return jsonify({
        'success': True,
        'users': result
    })


@support_bp.route('/admin/conversations', methods=['GET'])
@require_jwt_auth
def admin_get_conversations():
    """Get list of all support conversations for admin"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Get unique users who have support messages, with latest message info
    # Using a subquery to get latest message per user
    from sqlalchemy import func, desc

    # Get all users who have support messages
    conversations = db.session.query(
        SupportMessage.user_id,
        User.email,
        User.first_name,
        User.last_name,
        func.max(SupportMessage.created_at).label('last_message_at'),
        func.count(SupportMessage.id).label('message_count'),
        func.sum(
            db.case(
                (db.and_(SupportMessage.sender_type == 'user', SupportMessage.is_read == False), 1),
                else_=0
            )
        ).label('unread_count')
    ).join(User, SupportMessage.user_id == User.id
    ).group_by(SupportMessage.user_id, User.email, User.first_name, User.last_name
    ).order_by(desc('last_message_at')).all()

    result = []
    for conv in conversations:
        # Get the latest message for preview
        latest_msg = SupportMessage.query.filter_by(user_id=conv.user_id).order_by(
            SupportMessage.created_at.desc()
        ).first()

        result.append({
            'user_id': conv.user_id,
            'user_email': conv.email,
            'user_name': f"{conv.first_name or ''} {conv.last_name or ''}".strip() or conv.email,
            'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
            'message_count': conv.message_count,
            'unread_count': conv.unread_count,
            'last_message_preview': latest_msg.message[:100] if latest_msg else None,
            'last_message_sender': latest_msg.sender_type if latest_msg else None
        })

    return jsonify({
        'success': True,
        'conversations': result
    })


@support_bp.route('/admin/messages/<user_id>', methods=['GET'])
@require_jwt_auth
def admin_get_messages(user_id):
    """Get all messages for a specific user conversation"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Get the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get all messages for this user
    messages = SupportMessage.query.filter_by(user_id=user_id).order_by(
        SupportMessage.created_at.asc()
    ).all()

    # Mark user messages as read
    unread_messages = SupportMessage.query.filter_by(
        user_id=user_id,
        sender_type='user',
        is_read=False
    ).all()
    for msg in unread_messages:
        msg.is_read = True
        msg.read_at = datetime.now()
    db.session.commit()

    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'is_read': msg.is_read,
            'feedback_id': msg.feedback_id
        })

    # Get user info
    user_info = {
        'id': user.id,
        'email': user.email,
        'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }

    return jsonify({
        'success': True,
        'user': user_info,
        'messages': result
    })


@support_bp.route('/admin/send', methods=['POST'])
@require_jwt_auth
def admin_send_message():
    """Admin sends a message to a user"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    message_text = data.get('message', '').strip()
    feedback_id = data.get('feedback_id')  # Optional - if replying to feedback
    send_notification = data.get('send_email', True)  # Default to sending email

    if not user_id or not message_text:
        return jsonify({'error': 'user_id and message are required'}), 400

    # Get the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Create the message
    msg = SupportMessage(
        user_id=user_id,
        sender_type='admin',
        admin_user_id=admin.id,
        message=message_text,
        feedback_id=feedback_id,
        is_read=False  # User hasn't read it yet
    )
    db.session.add(msg)
    db.session.commit()

    # Send email notification
    email_sent = False
    if send_notification and user.email:
        email_sent = send_support_notification_email(user, message_text)
        if email_sent:
            msg.email_sent = True
            msg.email_sent_at = datetime.now()
            db.session.commit()

    logger.info(f"Admin {admin.email} sent support message to user {user_id}, email_sent={email_sent}")

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'email_sent': email_sent
        }
    })


@support_bp.route('/admin/feedback/<int:feedback_id>/reply', methods=['POST'])
@require_jwt_auth
def admin_reply_to_feedback(feedback_id):
    """Admin replies to a specific feedback item"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Get the feedback
    feedback = UserFeedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404

    if not feedback.user_id:
        return jsonify({'error': 'Cannot reply to anonymous feedback'}), 400

    data = request.get_json()
    message_text = data.get('message', '').strip()
    send_notification = data.get('send_email', True)

    if not message_text:
        return jsonify({'error': 'message is required'}), 400

    # Get the user
    user = User.query.get(feedback.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Create the message linked to feedback
    msg = SupportMessage(
        user_id=feedback.user_id,
        sender_type='admin',
        admin_user_id=admin.id,
        message=message_text,
        feedback_id=feedback_id,
        is_read=False
    )
    db.session.add(msg)
    db.session.commit()

    # Send email notification
    email_sent = False
    if send_notification and user.email:
        email_sent = send_support_notification_email(user, message_text)
        if email_sent:
            msg.email_sent = True
            msg.email_sent_at = datetime.now()
            db.session.commit()

    logger.info(f"Admin {admin.email} replied to feedback {feedback_id} for user {user.id}")

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'email_sent': email_sent
        }
    })


# ==================== USER ENDPOINTS ====================

@support_bp.route('/messages', methods=['GET'])
@require_jwt_auth
def user_get_messages():
    """Get all support messages for the current user"""
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get all messages for this user
    messages = SupportMessage.query.filter_by(user_id=user.id).order_by(
        SupportMessage.created_at.asc()
    ).all()

    # Mark admin messages as read
    unread_messages = SupportMessage.query.filter_by(
        user_id=user.id,
        sender_type='admin',
        is_read=False
    ).all()
    for msg in unread_messages:
        msg.is_read = True
        msg.read_at = datetime.now()
    db.session.commit()

    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
            'is_read': msg.is_read
        })

    return jsonify({
        'success': True,
        'messages': result
    })


@support_bp.route('/send', methods=['POST'])
@require_jwt_auth
def user_send_message():
    """User sends a message to support"""
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    message_text = data.get('message', '').strip()

    if not message_text:
        return jsonify({'error': 'message is required'}), 400

    # Create the message
    msg = SupportMessage(
        user_id=user.id,
        sender_type='user',
        message=message_text,
        is_read=False  # Admin hasn't read it yet
    )
    db.session.add(msg)
    db.session.commit()

    logger.info(f"User {user.email} sent support message")

    return jsonify({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_type': msg.sender_type,
            'message': msg.message,
            'created_at': msg.created_at.isoformat() if msg.created_at else None
        }
    })


@support_bp.route('/unread-count', methods=['GET'])
@require_jwt_auth
def user_unread_count():
    """Get count of unread support messages for the current user"""
    user = User.query.get(request.current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Count unread admin messages
    unread_count = SupportMessage.query.filter_by(
        user_id=user.id,
        sender_type='admin',
        is_read=False
    ).count()

    return jsonify({
        'success': True,
        'unread_count': unread_count
    })


# ==================== ADMIN FEEDBACK ENDPOINT EXTENSION ====================

@support_bp.route('/admin/feedback/<int:feedback_id>', methods=['GET'])
@require_jwt_auth
def admin_get_feedback_detail(feedback_id):
    """Get feedback details with associated messages"""
    admin = User.query.get(request.current_user_id)
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    feedback = UserFeedback.query.get(feedback_id)
    if not feedback:
        return jsonify({'error': 'Feedback not found'}), 404

    # Get user info if available
    user_info = None
    if feedback.user_id:
        user = User.query.get(feedback.user_id)
        if user:
            user_info = {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
            }

    # Get associated support messages
    messages = []
    if feedback.user_id:
        support_messages = SupportMessage.query.filter_by(
            user_id=feedback.user_id
        ).order_by(SupportMessage.created_at.asc()).all()

        # Mark user messages as read
        unread_messages = SupportMessage.query.filter_by(
            user_id=feedback.user_id,
            sender_type='user',
            is_read=False
        ).all()
        for msg in unread_messages:
            msg.is_read = True
            msg.read_at = datetime.now()
        db.session.commit()

        for msg in support_messages:
            messages.append({
                'id': msg.id,
                'sender_type': msg.sender_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat() if msg.created_at else None,
                'is_read': msg.is_read,
                'feedback_id': msg.feedback_id
            })

    return jsonify({
        'success': True,
        'feedback': {
            'id': feedback.id,
            'rating': feedback.rating,
            'what_to_improve': feedback.what_to_improve,
            'how_to_help': feedback.how_to_help,
            'what_would_make_you_use': feedback.what_would_make_you_use,
            'comments': feedback.comments,
            'trigger_type': feedback.trigger_type,
            'device_type': feedback.device_type,
            'created_at': feedback.created_at.isoformat() if feedback.created_at else None
        },
        'user': user_info,
        'messages': messages
    })
