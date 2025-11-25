"""
Twilio SMS Service for OTP and notifications
"""
import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for sending SMS via Twilio"""

    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')

        # Check if credentials are configured
        if self.account_sid and self.auth_token and self.phone_number:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("Twilio service initialized successfully")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not configured - SMS will be logged only")

    def send_sms(self, to_phone: str, message: str) -> dict:
        """
        Send SMS message

        Args:
            to_phone: Recipient phone number (format: +387XXXXXXXXX)
            message: Message text

        Returns:
            dict with 'success', 'message_sid', 'error'
        """
        if not self.enabled:
            # Development mode - just log the message
            logger.info(f"[DEV MODE] SMS to {to_phone}: {message}")
            return {
                'success': True,
                'message_sid': 'dev_mode_' + os.urandom(16).hex(),
                'dev_mode': True
            }

        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone(to_phone)

            # Send SMS via Twilio
            message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=normalized_phone
            )

            logger.info(f"SMS sent successfully to {normalized_phone}. SID: {message.sid}")

            return {
                'success': True,
                'message_sid': message.sid,
                'dev_mode': False
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_phone}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_otp(self, to_phone: str, otp_code: str) -> dict:
        """
        Send OTP code via SMS

        Args:
            to_phone: Recipient phone number
            otp_code: 6-digit OTP code

        Returns:
            dict with 'success', 'message_sid', 'error'
        """
        message = f"Vaš Popust.ba kod: {otp_code}\n\nKod važi 5 minuta."
        return self.send_sms(to_phone, message)

    def send_notification(self, to_phone: str, notification_text: str) -> dict:
        """
        Send notification SMS

        Args:
            to_phone: Recipient phone number
            notification_text: Notification message

        Returns:
            dict with 'success', 'message_sid', 'error'
        """
        message = f"Popust.ba obavještenje:\n\n{notification_text}"
        return self.send_sms(to_phone, message)

    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to E.164 format

        Accepts:
        - +387XXXXXXXXX (already normalized)
        - 387XXXXXXXXX (add +)
        - 06XXXXXXXX (add +387)
        - 06X XXX XXXX (remove spaces, add +387)

        Returns:
            Phone in E.164 format: +387XXXXXXXXX
        """
        # Remove all spaces, dashes, parentheses
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Already in E.164 format
        if phone.startswith('+387'):
            return phone

        # Missing + prefix
        if phone.startswith('387'):
            return '+' + phone

        # Local format (06X...)
        if phone.startswith('06'):
            return '+387' + phone[1:]  # Remove leading 0, add +387

        # If starts with just 6 (missing leading 0)
        if phone.startswith('6') and len(phone) == 8:
            return '+387' + phone

        # Default: assume it needs +387 prefix
        return '+387' + phone.lstrip('0')

    def validate_phone(self, phone: str) -> tuple[bool, str]:
        """
        Validate Bosnian phone number

        Args:
            phone: Phone number to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Remove spaces and special chars for validation
        clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # Check for Bosnian mobile prefixes (06X)
        valid_prefixes = ['060', '061', '062', '063', '064', '065', '066']

        try:
            normalized = self._normalize_phone(clean_phone)

            # Must be in format +387 6X XXXXXXX (total 13 chars including +)
            if len(normalized) != 13:
                return False, "Broj telefona mora imati 9 cifara (format: 06X XXX XXX)"

            # Check if it starts with valid Bosnian mobile prefix
            if not any(normalized.startswith('+387' + prefix[1:]) for prefix in valid_prefixes):
                return False, "Broj mora započeti sa 060, 061, 062, 063, 064, 065 ili 066"

            return True, ""

        except Exception as e:
            return False, f"Nevažeći format broja: {str(e)}"


# Global instance
twilio_service = TwilioService()
