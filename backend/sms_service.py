"""
SMS Service
Handles SMS sending via Twilio for shopping list receipts
"""
import os
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app import db
from models import SMSOutbox
import logging

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages via Twilio"""

    def __init__(self):
        """Initialize Twilio client"""
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_phone = os.environ.get('TWILIO_PHONE_NUMBER')

        # Only initialize client if credentials are present
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not configured. SMS service disabled.")

    def queue_sms(
        self,
        user_id: str,
        phone: str,
        body: str,
        list_id: int = None
    ) -> dict:
        """
        Queue an SMS message for sending

        Args:
            user_id: User ID
            phone: Recipient phone number (E.164 format, e.g., +38761234567)
            body: SMS message body
            list_id: Optional shopping list ID

        Returns:
            dict with 'sms_id', 'status'
        """
        # Create SMS outbox entry
        sms = SMSOutbox(
            user_id=user_id,
            list_id=list_id,
            phone=phone,
            body=body,
            status='QUEUED'
        )

        db.session.add(sms)
        db.session.commit()

        logger.info(f"Queued SMS {sms.id} for user {user_id} to {phone}")

        return {
            'sms_id': sms.id,
            'status': 'QUEUED',
            'phone': phone
        }

    def send_sms_now(
        self,
        user_id: str,
        phone: str,
        body: str,
        list_id: int = None
    ) -> dict:
        """
        Send an SMS immediately (queue and send)

        Args:
            user_id: User ID
            phone: Recipient phone number (E.164 format)
            body: SMS message body
            list_id: Optional shopping list ID

        Returns:
            dict with 'sms_id', 'status', 'message_sid'

        Raises:
            Exception: If SMS sending fails
        """
        # Queue the message first
        result = self.queue_sms(user_id, phone, body, list_id)
        sms_id = result['sms_id']

        # Attempt to send
        sms = SMSOutbox.query.get(sms_id)
        self._send_queued_message(sms)

        db.session.refresh(sms)

        return {
            'sms_id': sms.id,
            'status': sms.status,
            'message_sid': sms.provider_message_id,
            'phone': phone
        }

    def _send_queued_message(self, sms: SMSOutbox) -> bool:
        """
        Internal method to send a queued SMS

        Args:
            sms: SMSOutbox instance

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            # Mark as failed if Twilio not configured
            sms.status = 'FAILED'
            sms.error_message = 'Twilio not configured'
            db.session.commit()
            logger.error(f"Cannot send SMS {sms.id}: Twilio not configured")
            return False

        try:
            # Send via Twilio
            message = self.client.messages.create(
                to=sms.phone,
                from_=self.from_phone,
                body=sms.body
            )

            # Update status
            sms.status = 'SENT'
            sms.provider_message_id = message.sid
            sms.sent_at = datetime.now()
            db.session.commit()

            logger.info(f"Sent SMS {sms.id} via Twilio. Message SID: {message.sid}")
            return True

        except TwilioRestException as e:
            # Handle Twilio errors
            sms.status = 'FAILED'
            sms.error_message = str(e)
            db.session.commit()

            logger.error(f"Failed to send SMS {sms.id}: {e}")
            return False

        except Exception as e:
            # Handle unexpected errors
            sms.status = 'FAILED'
            sms.error_message = f"Unexpected error: {str(e)}"
            db.session.commit()

            logger.error(f"Unexpected error sending SMS {sms.id}: {e}")
            return False

    def process_queued_messages(self, limit: int = 10) -> dict:
        """
        Process queued SMS messages (for background job)

        Args:
            limit: Maximum number of messages to process

        Returns:
            dict with 'processed', 'sent', 'failed'
        """
        # Get queued messages
        queued = SMSOutbox.query.filter_by(status='QUEUED').order_by(
            SMSOutbox.created_at.asc()
        ).limit(limit).all()

        processed = 0
        sent = 0
        failed = 0

        for sms in queued:
            processed += 1
            if self._send_queued_message(sms):
                sent += 1
            else:
                failed += 1

        logger.info(f"Processed {processed} SMS: {sent} sent, {failed} failed")

        return {
            'processed': processed,
            'sent': sent,
            'failed': failed
        }

    @staticmethod
    def format_receipt_sms(receipt_data: dict) -> str:
        """
        Format shopping list receipt as SMS text

        Args:
            receipt_data: Receipt data from shopping list sidebar endpoint

        Returns:
            Formatted SMS text
        """
        lines = []
        lines.append("🛒 VAŠA LISTA ZA KUPOVINU")
        lines.append("")

        # Group by store
        for group in receipt_data.get('groups', []):
            store_name = group['store']['name']
            lines.append(f"📍 {store_name}")
            lines.append("-" * 30)

            for item in group['items']:
                name = item['name'][:30]  # Truncate long names
                qty = item['qty']
                price = item['unit_price']
                subtotal = item['subtotal']

                # Format item line
                lines.append(f"{name}")
                lines.append(f"  {qty}x {price:.2f}KM = {subtotal:.2f}KM")

                # Show saving if present
                if item.get('estimated_saving', 0) > 0:
                    saving = item['estimated_saving']
                    lines.append(f"  💰 Ušteda: {saving:.2f}KM")

            lines.append(f"Ukupno: {group['group_subtotal']:.2f}KM")
            lines.append("")

        # Grand totals
        lines.append("=" * 30)
        lines.append(f"UKUPNO: {receipt_data['grand_total']:.2f}KM")

        if receipt_data.get('grand_saving', 0) > 0:
            lines.append(f"💰 UKUPNA UŠTEDA: {receipt_data['grand_saving']:.2f}KM")

        lines.append("")
        lines.append("⏰ Lista važi danas")
        lines.append("")
        lines.append("AI Pijaca - aipijaca.com")

        return "\n".join(lines)

    @staticmethod
    def validate_phone_number(phone: str) -> tuple:
        """
        Validate and format phone number for Bosnia and Herzegovina

        Args:
            phone: Phone number (various formats accepted)

        Returns:
            tuple (is_valid: bool, formatted_phone: str, error_message: str)
        """
        # Remove spaces, dashes, parentheses
        cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Check if it starts with country code
        if cleaned.startswith('+387'):
            # Already has country code
            formatted = cleaned
        elif cleaned.startswith('387'):
            # Has country code without +
            formatted = '+' + cleaned
        elif cleaned.startswith('0'):
            # Local format (06x xxx xxxx)
            formatted = '+387' + cleaned[1:]
        else:
            # Invalid format
            return (False, '', 'Broj telefona mora počinjati sa 06x ili +38706x')

        # Validate length (should be +387 + 8-9 digits)
        if len(formatted) < 12 or len(formatted) > 13:
            return (False, '', 'Neispravan broj telefona za BiH')

        # Validate that it starts with valid mobile prefix (061, 062, 063, 065, 066)
        valid_prefixes = ['+38761', '+38762', '+38763', '+38765', '+38766']
        if not any(formatted.startswith(prefix) for prefix in valid_prefixes):
            return (False, '', 'Broj mora biti mobilni (061, 062, 063, 065, ili 066)')

        return (True, formatted, '')


# Singleton instance
sms_service = SMSService()
