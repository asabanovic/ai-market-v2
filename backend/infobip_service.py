"""
Infobip Service for WhatsApp, SMS, and Email messaging
Handles OTP delivery via WhatsApp with SMS fallback, and email sending
"""
import os
import logging
import requests
from typing import Dict, Optional
import secrets
import base64

logger = logging.getLogger(__name__)

# Infobip API Configuration
INFOBIP_API_KEY = os.environ.get("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.environ.get("INFOBIP_BASE_URL", "https://api.infobip.com")
# SMS uses alphanumeric sender (e.g., "Popust")
INFOBIP_SMS_SENDER = os.environ.get("INFOBIP_SMS_SENDER", os.environ.get("INFOBIP_SENDER", "Popust"))
# WhatsApp uses phone number sender (e.g., "+38761234567")
INFOBIP_WHATSAPP_SENDER = os.environ.get("INFOBIP_WHATSAPP_SENDER", os.environ.get("INFOBIP_SENDER", ""))
INFOBIP_EMAIL_FROM = os.environ.get("INFOBIP_EMAIL_FROM", "noreply@popust.ba")
INFOBIP_EMAIL_FROM_NAME = os.environ.get("INFOBIP_EMAIL_FROM_NAME", "Popust.ba")

# Service availability check
INFOBIP_ENABLED = bool(INFOBIP_API_KEY)

# Service-specific toggles (set to "false" in .env to disable)
INFOBIP_WHATSAPP_ENABLED = os.environ.get("INFOBIP_WHATSAPP_ENABLED", "true").lower() == "true"
INFOBIP_SMS_ENABLED = os.environ.get("INFOBIP_SMS_ENABLED", "true").lower() == "true"

if not INFOBIP_ENABLED:
    logger.warning("Infobip API key not configured. WhatsApp/SMS/Email will be logged only.")


def send_whatsapp_otp(phone: str, code: str) -> Dict:
    """
    Send OTP code via WhatsApp using Infobip

    Args:
        phone: Phone number with country code (e.g., +38761234567)
        code: 6-digit OTP code

    Returns:
        dict: {
            'success': bool,
            'message_id': str (if successful),
            'error': str (if failed),
            'channel': 'whatsapp'
        }
    """
    if not INFOBIP_WHATSAPP_ENABLED:
        logger.warning(f"WhatsApp service is disabled. Cannot send to {phone}")
        return {
            'success': False,
            'error': 'WhatsApp service is disabled',
            'channel': 'whatsapp'
        }

    if not INFOBIP_ENABLED:
        logger.info(f"[DEV MODE] WhatsApp OTP to {phone}: {code}")
        return {
            'success': True,
            'message_id': 'dev-mode-whatsapp',
            'channel': 'whatsapp',
            'dev_mode': True
        }

    try:
        # Infobip WhatsApp API endpoint
        url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/text"

        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # WhatsApp message payload
        payload = {
            "from": INFOBIP_WHATSAPP_SENDER,
            "to": phone,
            "messageId": f"whatsapp-otp-{phone}-{code[:3]}",
            "content": {
                "text": f"Vaš Popust.ba verifikacioni kod je: {code}\n\nKod važi 10 minuta.\n\nAko niste Vi zatražili ovaj kod, molimo zanemarite ovu poruku."
            },
            "callbackData": "otp-verification"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('messages'):
            message_info = response_data['messages'][0]
            if message_info.get('status', {}).get('groupName') == 'PENDING':
                logger.info(f"WhatsApp OTP sent successfully to {phone}")
                return {
                    'success': True,
                    'message_id': message_info.get('messageId'),
                    'channel': 'whatsapp'
                }

        logger.error(f"WhatsApp send failed: {response_data}")
        return {
            'success': False,
            'error': 'WhatsApp delivery failed',
            'channel': 'whatsapp',
            'details': response_data
        }

    except Exception as e:
        logger.error(f"WhatsApp OTP error for {phone}: {e}")
        return {
            'success': False,
            'error': str(e),
            'channel': 'whatsapp'
        }


def send_sms_otp(phone: str, code: str) -> Dict:
    """
    Send OTP code via SMS using Infobip

    Args:
        phone: Phone number with country code (e.g., +38761234567)
        code: 6-digit OTP code

    Returns:
        dict: {
            'success': bool,
            'message_id': str (if successful),
            'error': str (if failed),
            'channel': 'sms'
        }
    """
    if not INFOBIP_SMS_ENABLED:
        logger.warning(f"SMS service is disabled. Cannot send to {phone}")
        return {
            'success': False,
            'error': 'SMS service is disabled',
            'channel': 'sms'
        }

    if not INFOBIP_ENABLED:
        logger.info(f"[DEV MODE] SMS OTP to {phone}: {code}")
        return {
            'success': True,
            'message_id': 'dev-mode-sms',
            'channel': 'sms',
            'dev_mode': True
        }

    try:
        # Infobip SMS API endpoint
        url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"

        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # SMS message payload
        payload = {
            "messages": [
                {
                    "from": INFOBIP_SMS_SENDER,
                    "destinations": [
                        {"to": phone}
                    ],
                    "text": f"Vaš Popust.ba verifikacioni kod je: {code}\n\nKod važi 10 minuta."
                }
            ]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()

        logger.info(f"SMS API Response - Status: {response.status_code}, Data: {response_data}")

        if response.status_code == 200 and response_data.get('messages'):
            message_info = response_data['messages'][0]
            status = message_info.get('status', {})
            logger.info(f"SMS Status - GroupName: {status.get('groupName')}, Name: {status.get('name')}")

            if status.get('groupName') == 'PENDING':
                logger.info(f"SMS OTP sent successfully to {phone}")
                return {
                    'success': True,
                    'message_id': message_info.get('messageId'),
                    'channel': 'sms'
                }

        logger.error(f"SMS send failed - Status: {response.status_code}, Response: {response_data}")
        return {
            'success': False,
            'error': 'SMS delivery failed',
            'channel': 'sms',
            'details': response_data
        }

    except Exception as e:
        logger.error(f"SMS OTP error for {phone}: {e}")
        return {
            'success': False,
            'error': str(e),
            'channel': 'sms'
        }


def send_otp_with_fallback(phone: str, code: str, prefer_whatsapp: bool = True) -> Dict:
    """
    Send OTP with intelligent fallback from WhatsApp to SMS

    Args:
        phone: Phone number with country code
        code: 6-digit OTP code
        prefer_whatsapp: If True, try WhatsApp first, then SMS. If False, send SMS only.

    Returns:
        dict: {
            'success': bool,
            'channel': 'whatsapp' or 'sms',
            'message_id': str,
            'fallback_used': bool,
            'error': str (if both failed)
        }
    """
    if prefer_whatsapp:
        # Try WhatsApp first
        logger.info(f"Attempting WhatsApp OTP delivery to {phone}")
        whatsapp_result = send_whatsapp_otp(phone, code)

        if whatsapp_result['success']:
            logger.info(f"WhatsApp OTP delivered successfully to {phone}")
            return {
                **whatsapp_result,
                'fallback_used': False
            }

        # WhatsApp failed, fallback to SMS
        logger.warning(f"WhatsApp failed for {phone}, falling back to SMS")
        sms_result = send_sms_otp(phone, code)

        if sms_result['success']:
            logger.info(f"SMS OTP delivered successfully to {phone} (fallback)")
            return {
                **sms_result,
                'fallback_used': True,
                'primary_channel_failed': 'whatsapp'
            }

        # Both failed
        logger.error(f"Both WhatsApp and SMS failed for {phone}")
        return {
            'success': False,
            'error': 'Both WhatsApp and SMS delivery failed',
            'whatsapp_error': whatsapp_result.get('error'),
            'sms_error': sms_result.get('error')
        }
    else:
        # SMS only
        logger.info(f"Sending SMS OTP to {phone} (user prefers SMS)")
        return send_sms_otp(phone, code)


def send_promotional_message(phone: str, message: str, use_whatsapp: bool = True) -> Dict:
    """
    Send promotional/notification message via WhatsApp or SMS

    Args:
        phone: Phone number with country code
        message: Message text
        use_whatsapp: If True, use WhatsApp. If False, use SMS.

    Returns:
        dict with success status and details
    """
    if use_whatsapp:
        return send_whatsapp_message(phone, message)
    else:
        return send_sms_message(phone, message)


def send_whatsapp_message(phone: str, message: str) -> Dict:
    """Send a WhatsApp message (non-OTP)"""
    if not INFOBIP_ENABLED:
        logger.info(f"[DEV MODE] WhatsApp to {phone}: {message}")
        return {'success': True, 'channel': 'whatsapp', 'dev_mode': True}

    try:
        url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/text"
        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": INFOBIP_WHATSAPP_SENDER,
            "to": phone,
            "content": {"text": message}
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return {
            'success': response.status_code == 200,
            'channel': 'whatsapp',
            'response': response.json()
        }
    except Exception as e:
        logger.error(f"WhatsApp message error: {e}")
        return {'success': False, 'error': str(e), 'channel': 'whatsapp'}


def send_sms_message(phone: str, message: str) -> Dict:
    """Send an SMS message (non-OTP)"""
    if not INFOBIP_ENABLED:
        logger.info(f"[DEV MODE] SMS to {phone}: {message}")
        return {'success': True, 'channel': 'sms', 'dev_mode': True}

    try:
        url = f"{INFOBIP_BASE_URL}/sms/2/text/advanced"
        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{
                "from": INFOBIP_SMS_SENDER,
                "destinations": [{"to": phone}],
                "text": message
            }]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return {
            'success': response.status_code == 200,
            'channel': 'sms',
            'response': response.json()
        }
    except Exception as e:
        logger.error(f"SMS message error: {e}")
        return {'success': False, 'error': str(e), 'channel': 'sms'}
