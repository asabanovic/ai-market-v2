"""
Infobip Email Service
Handles all email sending via Infobip Email API
Replaces SendGrid
"""
import os
import logging
import requests
import secrets
import base64
from typing import Dict

logger = logging.getLogger(__name__)

# Infobip API Configuration
INFOBIP_API_KEY = os.environ.get("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.environ.get("INFOBIP_BASE_URL", "https://api.infobip.com")
INFOBIP_EMAIL_FROM = os.environ.get("INFOBIP_EMAIL_FROM", "noreply@popust.ba")
INFOBIP_EMAIL_FROM_NAME = os.environ.get("INFOBIP_EMAIL_FROM_NAME", "Popust.ba")

# Service availability check
INFOBIP_ENABLED = bool(INFOBIP_API_KEY)

# Service-specific toggle (set to "false" in .env to disable)
INFOBIP_EMAIL_ENABLED = os.environ.get("INFOBIP_EMAIL_ENABLED", "true").lower() == "true"

if not INFOBIP_ENABLED:
    logger.warning("Infobip API key not configured. Emails will be logged only.")


def get_logo_base64():
    """Get logo as base64 string for email"""
    try:
        with open('static/images/logo.png', 'rb') as f:
            logo_data = f.read()
            return base64.b64encode(logo_data).decode('utf-8')
    except Exception:
        return ""


def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def send_email(to_email: str, subject: str, html_content: str, from_name: str = None) -> bool:
    """
    Send email via Infobip Email API

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        from_name: Optional sender name (defaults to INFOBIP_EMAIL_FROM_NAME)

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not INFOBIP_EMAIL_ENABLED:
        logger.warning(f"Email service is disabled. Cannot send to {to_email}")
        return False

    if not INFOBIP_ENABLED:
        logger.info(f"[DEV MODE] Email to {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body preview: {html_content[:200]}...")
        return True

    try:
        url = f"{INFOBIP_BASE_URL}/email/3/send"

        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "from": {
                "email": INFOBIP_EMAIL_FROM,
                "name": from_name or INFOBIP_EMAIL_FROM_NAME
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": subject,
            "html": html_content
        }

        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response_data = response.json()

        if response.status_code in [200, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return True

        logger.error(f"Email send failed: {response_data}")
        return False

    except Exception as e:
        logger.error(f"Email send error for {to_email}: {e}")
        return False


def send_contact_email(user_name: str, user_email: str, message: str) -> bool:
    """Send contact form email to admin"""
    subject = f"Nova poruka sa kontakt forme - {user_name}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px; background-color: #f9f9f9; }}
            .message-box {{ background-color: white; padding: 20px; border-radius: 8px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Nova poruka sa kontakt forme</h2>
            </div>
            <div class="content">
                <p><strong>Ime:</strong> {user_name}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <div class="message-box">
                    <p><strong>Poruka:</strong></p>
                    <p>{message}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    admin_email = "adnanxteam@gmail.com"
    return send_email(admin_email, subject, html_content)


def send_verification_email(user_email: str, user_name: str, verification_token: str, base_url: str) -> bool:
    """Send email verification to new users"""
    verification_url = f"{base_url}/verify/{verification_token}"
    logo_base64 = get_logo_base64()

    subject = "Verifikacija računa - Popust.ba"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Verifikacija računa - Popust.ba</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #10B981; }}
            .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #10B981; }}
            .content {{ padding: 30px 0; }}
            .button {{ display: inline-block; background-color: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">
                    {f'<img src="data:image/png;base64,{logo_base64}" alt="Popust.ba" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                    Popust.ba
                </div>
            </div>

            <div class="content">
                <h2>Dobrodošli na Popust.ba!</h2>
                <p>Pozdrav {user_name},</p>
                <p>Hvala vam što ste se registrovali na Popust.ba platformu. Da biste dovršili registraciju, molimo vas da verifikujete vašu email adresu klikom na dugme ispod:</p>

                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verifikuj email adresu</a>
                </div>

                <p>Ili kopirajte i zalijepite sljedeći link u vaš web preglednik:</p>
                <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{verification_url}</p>

                <p>Ovaj link će isteći za 24 sata.</p>

                <p>Ako se niste registrovali na našu platformu, molimo vas da ignorišete ovaj email.</p>

                <p>Srdačan pozdrav,<br>Tim Popust.ba</p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Popust.ba. Sva prava zadržana.</p>
                <p>Ako imate problema sa verifikacijom, kontaktirajte nas odgovorom na ovaj email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_content)


def send_welcome_email(user_email: str, user_name: str) -> bool:
    """Send welcome email to verified users"""
    subject = "Dobrodošli na Popust.ba!"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ padding: 30px; background-color: #f9f9f9; }}
            .features {{ list-style: none; padding: 0; }}
            .features li {{ padding: 10px 0; padding-left: 30px; position: relative; }}
            .features li:before {{ content: "✓"; position: absolute; left: 0; color: #10B981; font-weight: bold; font-size: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Dobrodošli, {user_name}!</h2>
            </div>
            <div class="content">
                <p>Hvala vam što ste se registrovali na Popust.ba platformu za pronalaženje najboljih popusta u Bosni i Hercegovini.</p>
                <p>Sada možete:</p>
                <ul class="features">
                    <li>Pretražiti najnovije popuste u vašem gradu</li>
                    <li>Dodati proizvode u omiljene i biti obavješteni o popustima</li>
                    <li>Kreirati shopping liste i kupovati pametno</li>
                    <li>Pratiti cijene i uštediti novac</li>
                </ul>
                <p>Počnite sa pretraživanjem već danas i uštedite na svakoj kupovini!</p>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="https://rabat.ba" style="display: inline-block; background-color: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Počnite pretraživanje</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_content)


def send_invitation_email(email: str, business_name: str, role: str, invitation_token: str, base_url: str) -> bool:
    """Send business invitation email"""
    invitation_url = f"{base_url}/invite/accept/{invitation_token}"
    logo_base64 = get_logo_base64()

    # Translate role to Bosnian
    role_translations = {
        'owner': 'vlasnik',
        'manager': 'menadžer',
        'staff': 'zaposleni'
    }
    role_bosnian = role_translations.get(role, role)

    subject = f"Poziv za pristup biznisu - {business_name}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Poziv za pristup biznisu - Popust.ba</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #10B981; }}
            .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #10B981; }}
            .content {{ padding: 30px 0; }}
            .button {{ display: inline-block; background-color: #10B981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .info-box {{ background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">
                    {f'<img src="data:image/png;base64,{logo_base64}" alt="Popust.ba" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                    Popust.ba
                </div>
            </div>

            <div class="content">
                <h2>Pozivani ste da upravljate biznisom!</h2>
                <p>Pozdrav,</p>
                <p>Pozivani ste da pristupite upravljanju biznisa <strong>{business_name}</strong> kroz Popust.ba platformu.</p>

                <div class="info-box">
                    <h3>Detalji poziva:</h3>
                    <p><strong>Biznis:</strong> {business_name}</p>
                    <p><strong>Uloga:</strong> {role_bosnian.title()}</p>
                    <p><strong>Platforma:</strong> Popust.ba</p>
                </div>

                <p>Sa ovom ulogom moći ćete:</p>
                <ul>
                    {'<li>Dodavati, mijenjati i brisati proizvode</li><li>Upravljati informacijama o biznisu</li><li>Pozivati i upravljati drugim članovima tima</li>' if role == 'owner' else ''}
                    {'<li>Dodavati, mijenjati i brisati proizvode</li><li>Upravljati informacijama o biznisu</li>' if role == 'manager' else ''}
                    {'<li>Dodavati nove proizvode</li><li>Pregledati statistike biznisa</li>' if role == 'staff' else ''}
                </ul>

                <div style="text-align: center;">
                    <a href="{invitation_url}" class="button">Prihvati poziv</a>
                </div>

                <p>Ili kopirajte i zalijepite sljedeći link u vaš web preglednik:</p>
                <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{invitation_url}</p>

                <p><strong>Napomena:</strong> Ovaj poziv vrijedi 7 dana i može se koristiti samo jednom.</p>

                <p>Ako se niste aplicirali za ovaj biznis ili niste očekivali ovaj poziv, molimo vas da ignorišete ovaj email.</p>

                <p>Srdačan pozdrav,<br>Tim Popust.ba</p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Popust.ba. Sva prava zadržana.</p>
                <p>Ako imate problema sa pozivom, kontaktirajte nas odgovorom na ovaj email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(email, subject, html_content)


def send_password_reset_email(user_email: str, user_name: str, reset_token: str, base_url: str) -> bool:
    """Send password reset email to users"""
    reset_url = f"{base_url}/reset-password/{reset_token}"
    logo_base64 = get_logo_base64()

    subject = "Resetiranje lozinke - Popust.ba"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Resetiranje lozinke - Popust.ba</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #EF4444; }}
            .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #EF4444; }}
            .content {{ padding: 30px 0; }}
            .button {{ display: inline-block; background-color: #EF4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
            .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 14px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">
                    {f'<img src="data:image/png;base64,{logo_base64}" alt="Popust.ba" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                    Popust.ba
                </div>
            </div>

            <div class="content">
                <h2>Resetiranje lozinke</h2>
                <p>Pozdrav {user_name},</p>
                <p>Dobili ste zahtjev za resetiranje lozinke za vaš Popust.ba račun. Da biste resetirali vašu lozinku, kliknite na dugme ispod:</p>

                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Resetiraj lozinku</a>
                </div>

                <p>Ili kopirajte i zalijepite sljedeći link u vaš web preglednik:</p>
                <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{reset_url}</p>

                <p>Ovaj link će isteći za 1 sat iz sigurnosnih razloga.</p>

                <p>Ako niste zahtjevali resetiranje lozinke, molimo vas da ignorišete ovaj email. Vaša lozinka neće biti promijenjena.</p>

                <p>Srdačan pozdrav,<br>Tim Popust.ba</p>
            </div>

            <div class="footer">
                <p>&copy; 2025 Popust.ba. Sva prava zadržana.</p>
                <p>Ako imate problema sa resetiranjem lozinke, kontaktirajte nas odgovorom na ovaj email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(user_email, subject, html_content)
