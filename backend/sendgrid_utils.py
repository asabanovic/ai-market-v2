# SendGrid email utilities for marketplace application
import os
import sys
import secrets
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

sendgrid_key = os.environ.get('SENDGRID_API_KEY')
if not sendgrid_key:
    print('Warning: SENDGRID_API_KEY environment variable not set')


def send_contact_email(user_name, user_email, message):
    """Send contact form email to admin"""
    if not sendgrid_key:
        return False
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        # Email content
        subject = f"Nova poruka sa kontakt forme - {user_name}"
        html_content = f"""
        <h2>Nova poruka sa kontakt forme</h2>
        <p><strong>Ime:</strong> {user_name}</p>
        <p><strong>Email:</strong> {user_email}</p>
        <p><strong>Poruka:</strong></p>
        <p>{message}</p>
        """
        
        message = Mail(
            from_email=Email("noreply@aipijaca.com"),
            to_emails=To("adnanxteam@gmail.com"),
            subject=subject
        )
        message.content = Content("text/html", html_content)
        
        response = sg.send(message)
        return True
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False


def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def get_logo_base64():
    """Get logo as base64 string for email"""
    try:
        with open('static/images/logo.png', 'rb') as f:
            logo_data = f.read()
            return base64.b64encode(logo_data).decode('utf-8')
    except Exception:
        return ""


def send_verification_email(user_email, user_name, verification_token, base_url):
    """Send email verification to new users"""
    if not sendgrid_key:
        print("Warning: SendGrid not configured, verification email not sent")
        return False
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        verification_url = f"{base_url}/verify/{verification_token}"
        logo_base64 = get_logo_base64()
        
        subject = "Verifikacija računa - AI Pijaca"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verifikacija računa - AI Pijaca</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #4F46E5; }}
                .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #4F46E5; }}
                .content {{ padding: 30px 0; }}
                .button {{ display: inline-block; background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        {f'<img src="data:image/png;base64,{logo_base64}" alt="AI Pijaca" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                        AI Pijaca
                    </div>
                </div>
                
                <div class="content">
                    <h2>Dobrodošli u AI Pijaca!</h2>
                    <p>Pozdrav {user_name},</p>
                    <p>Hvala vam što ste se registrovali na AI Pijaca platformu. Da biste dovršili registraciju, molimo vas da verifikujete vašu email adresu klikom na dugme ispod:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verifikuj email adresu</a>
                    </div>
                    
                    <p>Ili kopirajte i zalijepite sljedeći link u vaš web preglednik:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{verification_url}</p>
                    
                    <p>Ovaj link će isteći za 24 sata.</p>
                    
                    <p>Ako se niste registrovali na našu platformu, molimo vas da ignorišete ovaj email.</p>
                    
                    <p>Srdačan pozdrav,<br>Tim AI Pijaca</p>
                </div>
                
                <div class="footer">
                    <p>&copy; 2025 AI Pijaca. Sva prava zadržana.</p>
                    <p>Ako imate problema sa verifikacijom, kontaktirajte nas odgovorom na ovaj email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=Email("noreply@aipijaca.com"),
            to_emails=To(user_email),
            subject=subject
        )
        message.content = Content("text/html", html_content)
        
        response = sg.send(message)
        return True
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False


def send_welcome_email(user_email, user_name):
    """Send welcome email to verified users"""
    if not sendgrid_key:
        return False
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        subject = "Dobrodošli na AI Pijaca!"
        html_content = f"""
        <h2>Dobrodošli, {user_name}!</h2>
        <p>Hvala vam što ste se registrovali na AI Pijaca platformu za pronalaženje lokalnih popusta.</p>
        <p>Sada možete:</p>
        <ul>
            <li>Pretražiti najnovije popuste u vašem gradu</li>
            <li>Koristiti AI asistenta za personalizirane preporuke</li>
            <li>Pratiti omiljene proizvode i radnje</li>
        </ul>
        <p>Počnite sa pretraživanjem već danas!</p>
        """
        
        message = Mail(
            from_email=Email("noreply@aipijaca.com"),
            to_emails=To(user_email),
            subject=subject
        )
        message.content = Content("text/html", html_content)
        
        response = sg.send(message)
        return True
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False


def send_invitation_email(email, business_name, role, invitation_token, base_url):
    """Send business invitation email"""
    if not sendgrid_key:
        print("Warning: SendGrid not configured, invitation email not sent")
        return False
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
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
            <title>Poziv za pristup biznisu - AI Pijaca</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #4F46E5; }}
                .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #4F46E5; }}
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
                        {f'<img src="data:image/png;base64,{logo_base64}" alt="AI Pijaca" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                        AI Pijaca
                    </div>
                </div>
                
                <div class="content">
                    <h2>Pozivani ste da upravljate biznisом!</h2>
                    <p>Pozdrav,</p>
                    <p>Pozivani ste da pristupite upravljanju biznisa <strong>{business_name}</strong> kroz AI Pijaca platformu.</p>
                    
                    <div class="info-box">
                        <h3>Detalji poziva:</h3>
                        <p><strong>Biznis:</strong> {business_name}</p>
                        <p><strong>Uloga:</strong> {role_bosnian.title()}</p>
                        <p><strong>Platforma:</strong> AI Pijaca</p>
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
                    
                    <p>Srdačan pozdrav,<br>Tim AI Pijaca</p>
                </div>
                
                <div class="footer">
                    <p>&copy; 2025 AI Pijaca. Sva prava zadržana.</p>
                    <p>Ako imate problema sa pozivom, kontaktirajte nas odgovorom na ovaj email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=Email("noreply@aipijaca.com"),
            to_emails=To(email),
            subject=subject
        )
        message.content = Content("text/html", html_content)
        
        response = sg.send(message)
        return True
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_password_reset_email(user_email, user_name, reset_token, base_url):
    """Send password reset email to users"""
    if not sendgrid_key:
        print("Warning: SendGrid not configured, password reset email not sent")
        return False
        
    try:
        sg = SendGridAPIClient(sendgrid_key)
        
        reset_url = f"{base_url}/reset-password/{reset_token}"
        logo_base64 = get_logo_base64()
        
        subject = "Resetiranje lozinke - AI Pijaca"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Resetiranje lozinke - AI Pijaca</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #4F46E5; }}
                .logo {{ display: inline-flex; align-items: center; font-size: 24px; font-weight: bold; color: #4F46E5; }}
                .content {{ padding: 30px 0; }}
                .button {{ display: inline-block; background-color: #EF4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
                .footer {{ border-top: 1px solid #eee; padding-top: 20px; text-align: center; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">
                        {f'<img src="data:image/png;base64,{logo_base64}" alt="AI Pijaca" style="height: 32px; width: 32px; margin-right: 8px;">' if logo_base64 else ''}
                        AI Pijaca
                    </div>
                </div>
                
                <div class="content">
                    <h2>Resetiranje lozinke</h2>
                    <p>Pozdrav {user_name},</p>
                    <p>Dobili ste zahtjev za resetiranje lozinke za vaš AI Pijaca račun. Da biste resetirali vašu lozinku, kliknite na dugme ispod:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Resetiraj lozinku</a>
                    </div>
                    
                    <p>Ili kopirajte i zalijepite sljedeći link u vaš web pregljednik:</p>
                    <p style="word-break: break-all; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">{reset_url}</p>
                    
                    <p>Ovaj link će isteći za 1 sat iz sigurnosnih razloga.</p>
                    
                    <p>Ako niste zahtjevali resetiranje lozinke, molimo vas da ignorišete ovaj email. Vaša lozinka neće biti promijenjena.</p>
                    
                    <p>Srdačan pozdrav,<br>Tim AI Pijaca</p>
                </div>
                
                <div class="footer">
                    <p>&copy; 2025 AI Pijaca. Sva prava zadržana.</p>
                    <p>Ako imate problema sa resetiranjem lozinke, kontaktirajte nas odgovorom na ovaj email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = Mail(
            from_email=Email("noreply@aipijaca.com"),
            to_emails=To(user_email),
            subject=subject
        )
        message.content = Content("text/html", html_content)
        
        response = sg.send(message)
        return True
        
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False
