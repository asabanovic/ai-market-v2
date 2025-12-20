"""
SendGrid Event Webhook handler.
Receives email events (opens, clicks, bounces, etc.) from SendGrid.

To configure in SendGrid:
1. Go to Settings > Mail Settings > Event Webhook
2. Set HTTP Post URL to: https://popust.ba/api/webhooks/sendgrid
3. Enable events: Opened, Clicked, Delivered, Bounced, Dropped
4. Save
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

sendgrid_webhook_bp = Blueprint('sendgrid_webhook', __name__, url_prefix='/api/webhooks')

logger = logging.getLogger(__name__)


@sendgrid_webhook_bp.route('/sendgrid', methods=['POST'])
def handle_sendgrid_events():
    """
    Receive and process SendGrid event webhook.

    SendGrid sends an array of events in the request body.
    Each event contains: email, event, timestamp, sg_event_id, etc.
    """
    from app import db
    from models import EmailEvent, User

    try:
        events = request.get_json()

        if not events or not isinstance(events, list):
            logger.warning("Invalid SendGrid webhook payload")
            return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400

        processed = 0
        skipped = 0

        for event in events:
            try:
                email = event.get('email')
                event_type = event.get('event')
                sg_event_id = event.get('sg_event_id')
                timestamp = event.get('timestamp')

                if not email or not event_type:
                    skipped += 1
                    continue

                # Check for duplicate (SendGrid may retry)
                if sg_event_id:
                    existing = EmailEvent.query.filter_by(sg_event_id=sg_event_id).first()
                    if existing:
                        skipped += 1
                        continue

                # Find user by email
                user = User.query.filter_by(email=email).first()

                # Parse timestamp
                event_time = datetime.now()
                if timestamp:
                    try:
                        event_time = datetime.fromtimestamp(int(timestamp))
                    except (ValueError, TypeError):
                        pass

                # Create email event record
                email_event = EmailEvent(
                    email=email,
                    event_type=event_type,
                    user_id=user.id if user else None,
                    sg_message_id=event.get('sg_message_id'),
                    sg_event_id=sg_event_id,
                    url=event.get('url'),  # For click events
                    user_agent=event.get('useragent'),
                    ip=event.get('ip'),
                    timestamp=event_time
                )

                db.session.add(email_event)
                processed += 1

            except Exception as e:
                logger.error(f"Error processing event: {e}")
                skipped += 1
                continue

        db.session.commit()
        logger.info(f"SendGrid webhook: processed {processed}, skipped {skipped}")

        return jsonify({
            'status': 'ok',
            'processed': processed,
            'skipped': skipped
        })

    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
