"""
SendGrid Email Service for Popust.ba
Clean, minimalistic templates with white background and logo.
"""
import os
import logging
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

# SendGrid Configuration
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@popust.ba")
SENDGRID_FROM_NAME = os.environ.get("SENDGRID_FROM_NAME", "Popust.ba")

# Service availability check
SENDGRID_ENABLED = bool(SENDGRID_API_KEY)

if not SENDGRID_ENABLED:
    logger.warning("SendGrid API key not configured. Emails will be logged only.")

# Base URL
BASE_URL = os.environ.get("BASE_URL", "https://popust.ba")
LOGO_URL = "https://popust.ba/logo.png"


def plural_bs(n: int, singular: str, paucal: str, plural: str) -> str:
    """
    Return correct Bosnian/Croatian/Serbian plural form based on number.

    Rules:
    - 1 (or ends in 1, except 11): singular form
    - 2, 3, 4 (or ends in 2-4, except 12-14): paucal form
    - 0, 5-9, 11-14 (or ends in 0, 5-9): plural form

    Examples:
    - plural_bs(1, "novi proizvod", "nova proizvoda", "novih proizvoda") -> "novi proizvod"
    - plural_bs(2, "novi proizvod", "nova proizvoda", "novih proizvoda") -> "nova proizvoda"
    - plural_bs(5, "novi proizvod", "nova proizvoda", "novih proizvoda") -> "novih proizvoda"
    """
    n = abs(n)
    last_digit = n % 10
    last_two_digits = n % 100

    # Special case for teens (11-14) - always plural
    if 11 <= last_two_digits <= 14:
        return plural

    if last_digit == 1:
        return singular
    elif 2 <= last_digit <= 4:
        return paucal
    else:
        return plural


def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def add_utm_params(url: str, source: str = "email", medium: str = "email", campaign: str = None) -> str:
    """
    Add UTM tracking parameters to a URL.

    Args:
        url: The base URL to add parameters to
        source: utm_source (e.g., 'email', 'facebook')
        medium: utm_medium (e.g., 'email', 'social')
        campaign: utm_campaign (e.g., 'daily_summary', 'weekly_deals')

    Returns:
        URL with UTM parameters appended
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Add UTM params (don't override if already present)
    if 'utm_source' not in params:
        params['utm_source'] = [source]
    if 'utm_medium' not in params:
        params['utm_medium'] = [medium]
    if campaign and 'utm_campaign' not in params:
        params['utm_campaign'] = [campaign]

    # Flatten params (parse_qs returns lists)
    flat_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}

    new_query = urlencode(flat_params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


def get_tracked_url(path: str, campaign: str) -> str:
    """
    Get a fully tracked URL with UTM parameters.

    Args:
        path: URL path (e.g., '/moji-proizvodi')
        campaign: Email campaign name (e.g., 'daily_summary', 'price_alert')

    Returns:
        Full URL with tracking: https://popust.ba/moji-proizvodi?utm_source=email&utm_medium=email&utm_campaign=daily_summary
    """
    url = f"{BASE_URL}{path}"
    return add_utm_params(url, source="email", medium="email", campaign=campaign)


def get_magic_link_url(path: str, user_id: str, campaign: str) -> str:
    """
    Get a URL with magic link token for auto-login from emails.

    This enables one-click access when users open emails in embedded
    browsers (Gmail, Outlook) that don't share the main browser's session.

    Args:
        path: URL path (e.g., '/moji-proizvodi')
        user_id: User's ID to generate token for
        campaign: Email campaign name (e.g., 'daily_summary')

    Returns:
        Full URL with auth_token and UTM params:
        https://popust.ba/moji-proizvodi?auth_token=xxx&utm_source=email&utm_medium=email&utm_campaign=daily_summary
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    try:
        # Import here to avoid circular imports
        from models import EmailAuthToken

        # Generate magic link token for this user
        token = EmailAuthToken.generate_for_user(user_id, email_type=campaign)

        # Build URL with auth_token
        url = f"{BASE_URL}{path}"
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Add auth_token
        params['auth_token'] = [token]

        # Add UTM params
        params['utm_source'] = ['email']
        params['utm_medium'] = ['email']
        params['utm_campaign'] = [campaign]

        # Flatten params
        flat_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
        new_query = urlencode(flat_params)

        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    except Exception as e:
        logger.warning(f"Failed to generate magic link for user {user_id}: {e}")
        # Fallback to regular tracked URL without magic link
        return get_tracked_url(path, campaign)


def get_base_template(content: str, accent_color: str = "#7C3AED") -> str:
    """Base email template - clean white background with logo"""
    return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<table width="100%" style="background-color:#f5f5f5;">
<tr><td align="center" style="padding:40px 20px;">
<table width="100%" style="max-width:520px;background-color:#ffffff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">

<!-- Logo -->
<tr><td style="padding:32px 40px 24px;text-align:center;border-bottom:2px solid {accent_color};">
<img src="{LOGO_URL}" alt="Popust.ba" height="40">
</td></tr>

<!-- Content -->
<tr><td style="padding:32px 40px;">
{content}
</td></tr>

<!-- Footer -->
<tr><td style="padding:24px 40px;border-top:1px solid #eee;text-align:center;">
<p style="margin:0 0 8px;font-size:13px;color:#888;">© 2025 Popust.ba - Sva prava zadržana</p>
<p style="margin:0;font-size:12px;color:#aaa;">Vaša platforma za pronalaženje najboljih ponuda u Bosni i Hercegovini</p>
</td></tr>

</table>
</td></tr></table>
</body>
</html>'''


def get_button(text: str, url: str, color: str = "#7C3AED", campaign: str = None) -> str:
    """
    Generate a CTA button with optional UTM tracking.

    Args:
        text: Button text
        url: Target URL
        color: Button background color
        campaign: Optional campaign name for UTM tracking (e.g., 'daily_summary')
    """
    # Add UTM params if campaign is specified
    tracked_url = add_utm_params(url, campaign=campaign) if campaign else url

    return f'''<table style="margin:24px auto;"><tr>
<td style="background-color:{color};border-radius:8px;">
<a href="{tracked_url}" style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">{text}</a>
</td>
</tr></table>'''


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send email via SendGrid API

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not SENDGRID_ENABLED:
        logger.info(f"[DEV MODE] Email to {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body preview: {html_content[:200]}...")
        return True

    try:
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in [200, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return True

        logger.error(f"Email send failed with status {response.status_code}")
        return False

    except Exception as e:
        logger.error(f"Email send error for {to_email}: {e}")
        return False


def send_verification_email(user_email: str, user_name: str, verification_token: str, base_url: str = None) -> bool:
    """Send email verification to new users"""
    base = base_url or BASE_URL
    verification_url = f"{base}/verify/{verification_token}"

    greeting = f" {user_name}" if user_name else ""

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Dobro došli na Popust.ba</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Zahvaljujemo Vam na registraciji. Da biste aktivirali svoj račun i počeli koristiti sve pogodnosti naše platforme, potrebno je potvrditi Vašu email adresu.</p>
{get_button("Potvrdi email adresu", verification_url, "#10B981", campaign="verification")}
<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;">
<p style="margin:0;font-size:13px;color:#666;line-height:1.5;">
<strong>Napomena:</strong> Ovaj link vrijedi 24 sata. Ukoliko niste Vi zatražili registraciju, slobodno zanemarite ovu poruku.
</p>
</div>
'''

    subject = "Potvrdite Vašu email adresu - Popust.ba"
    html = get_base_template(content, "#10B981")
    return send_email(user_email, subject, html)


def send_welcome_email(user_email: str, user_name: str) -> bool:
    """Send welcome email to verified users"""
    greeting = f" {user_name}" if user_name else ""

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Vaš račun je uspješno aktiviran</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Čestitamo! Vaš račun na Popust.ba je sada aktivan. Od sada možete koristiti sve mogućnosti naše platforme:</p>

<table width="100%">
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<span style="display:inline-block;width:24px;height:24px;background:#ECFDF5;border-radius:50%;text-align:center;line-height:24px;color:#10B981;font-size:14px;">✓</span>
<span style="font-size:14px;color:#444;margin-left:8px;">Pretražujte aktuelne popuste iz svih trgovina</span>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<span style="display:inline-block;width:24px;height:24px;background:#ECFDF5;border-radius:50%;text-align:center;line-height:24px;color:#10B981;font-size:14px;">✓</span>
<span style="font-size:14px;color:#444;margin-left:8px;">Spremajte omiljene proizvode za brži pristup</span>
</td></tr>
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<span style="display:inline-block;width:24px;height:24px;background:#ECFDF5;border-radius:50%;text-align:center;line-height:24px;color:#10B981;font-size:14px;">✓</span>
<span style="font-size:14px;color:#444;margin-left:8px;">Kreirajte personalizirane liste za kupovinu</span>
</td></tr>
<tr><td style="padding:12px 0;">
<span style="display:inline-block;width:24px;height:24px;background:#ECFDF5;border-radius:50%;text-align:center;line-height:24px;color:#10B981;font-size:14px;">✓</span>
<span style="font-size:14px;color:#444;margin-left:8px;">Pratite cijene proizvoda i primajte obavještenja o sniženjima</span>
</td></tr>
</table>

{get_button("Započnite pretragu", BASE_URL, "#7C3AED", campaign="welcome")}
<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">Uživajte u pronalaženju najboljih ponuda!</p>
'''

    subject = "Dobro došli na Popust.ba - Vaš račun je aktivan"
    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


def send_password_reset_email(user_email: str, user_name: str, reset_token: str, base_url: str = None) -> bool:
    """Send password reset email to users"""
    base = base_url or BASE_URL
    reset_url = f"{base}/reset-password/{reset_token}"

    greeting = f" {user_name}" if user_name else ""

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Zahtjev za promjenu lozinke</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Zaprimili smo Vaš zahtjev za promjenu lozinke. Kliknite na dugme ispod kako biste postavili novu lozinku za Vaš račun:</p>
{get_button("Postavite novu lozinku", reset_url, "#EF4444", campaign="password_reset")}
<div style="margin:24px 0;padding:16px;background:#FEF2F2;border-radius:8px;border-left:3px solid #EF4444;">
<p style="margin:0;font-size:13px;color:#991B1B;line-height:1.5;">
<strong>Važna napomena:</strong> Ovaj link vrijedi samo 1 sat iz sigurnosnih razloga. Ukoliko niste Vi zatražili promjenu lozinke, slobodno zanemarite ovu poruku - Vaš račun ostaje siguran.
</p>
</div>
'''

    subject = "Promjena lozinke - Popust.ba"
    html = get_base_template(content, "#EF4444")
    return send_email(user_email, subject, html)


def send_invitation_email(email: str, business_name: str, role: str, invitation_token: str, base_url: str = None) -> bool:
    """Send business invitation email"""
    base = base_url or BASE_URL
    invitation_url = f"{base}/invite/accept/{invitation_token}"

    role_translations = {
        'owner': 'Vlasnik',
        'manager': 'Menadžer',
        'staff': 'Zaposlenik'
    }
    role_display = role_translations.get(role, role.title())

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Pozivnica za upravljanje poslovanjem</h1>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Pozvani ste da se pridružite timu za upravljanje poslovanjem <strong>{business_name}</strong> na platformi Popust.ba.</p>

<div style="background-color:#F9FAFB;border-radius:8px;padding:16px;margin-bottom:24px;">
<table width="100%">
<tr>
<td style="font-size:13px;color:#666;padding:8px 0;">Naziv poslovanja:</td>
<td style="font-size:14px;color:#1a1a1a;font-weight:600;text-align:right;">{business_name}</td>
</tr>
<tr>
<td style="font-size:13px;color:#666;padding:8px 0;">Vaša uloga:</td>
<td style="font-size:14px;color:#7C3AED;font-weight:600;text-align:right;">{role_display}</td>
</tr>
</table>
</div>

{get_button("Prihvatite pozivnicu", invitation_url, "#10B981", campaign="business_invitation")}
<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;">
<p style="margin:0;font-size:13px;color:#666;line-height:1.5;">
<strong>Napomena:</strong> Ova pozivnica vrijedi 7 dana. Ukoliko niste očekivali ovaj poziv ili mislite da se radi o grešci, slobodno zanemarite ovu poruku.
</p>
</div>
'''

    subject = f"Pozivnica za upravljanje - {business_name}"
    html = get_base_template(content, "#10B981")
    return send_email(email, subject, html)


def send_contact_email(user_name: str, user_email: str, message: str) -> bool:
    """Send contact form email to admin"""
    from datetime import datetime

    current_time = datetime.now().strftime("%d.%m.%Y u %H:%M")

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Nova poruka putem kontakt forme</h1>
<p style="margin:0 0 16px;font-size:13px;color:#888;">Zaprimljeno: {current_time}</p>

<div style="background-color:#F9FAFB;border-radius:8px;padding:16px;margin-bottom:16px;">
<table width="100%">
<tr>
<td style="font-size:13px;color:#666;padding:8px 0;width:80px;vertical-align:top;">Ime:</td>
<td style="font-size:14px;color:#1a1a1a;font-weight:500;padding:8px 0;">{user_name}</td>
</tr>
<tr>
<td style="font-size:13px;color:#666;padding:8px 0;vertical-align:top;">Email:</td>
<td style="font-size:14px;color:#1a1a1a;padding:8px 0;"><a href="mailto:{user_email}" style="color:#7C3AED;text-decoration:none;">{user_email}</a></td>
</tr>
</table>
</div>

<div style="background-color:#ffffff;border:1px solid #eee;border-radius:8px;padding:16px;">
<p style="margin:0 0 12px;font-size:13px;color:#666;font-weight:600;">Sadržaj poruke:</p>
<p style="margin:0;font-size:14px;color:#444;line-height:1.6;white-space:pre-wrap;">{message}</p>
</div>
'''

    subject = f"Kontakt forma - {user_name}"
    html = get_base_template(content, "#7C3AED")
    admin_email = "info@popust.ba"
    return send_email(admin_email, subject, html)


def send_scan_summary_email(user_email: str, user_name: str, summary: dict, user_id: str = None) -> bool:
    """Send daily product scan summary email with optional magic link authentication"""
    import random

    total = summary.get('total_products', 0)
    new_products = summary.get('new_products', 0)
    new_discounts = summary.get('new_discounts', 0)
    terms = summary.get('terms', [])

    greeting = f" {user_name}" if user_name else ""

    # Dynamic subject - implies work done for user, adds personal benefit
    if new_products > 0:
        product_text = plural_bs(new_products, "nova ponuda", "nove ponude", "novih ponuda")
        subject_options = [
            f"Pronađeno {new_products} {product_text} na Vašoj listi",
            f"Danas: {new_products} {product_text} za Vas",
            f"{new_products} {product_text} (provjereno danas)",
        ]
        subject = random.choice(subject_options)
    elif new_discounts > 0:
        discount_text = plural_bs(new_discounts, "novo sniženje", "nova sniženja", "novih sniženja")
        subject_options = [
            f"{new_discounts} {discount_text} na proizvodima koje pratite",
            f"Danas: {new_discounts} novih prilika za uštedu",
            f"Pronašli smo {new_discounts} {discount_text} za Vas",
        ]
        subject = random.choice(subject_options)
    else:
        subject = f"Dnevni pregled - {total} proizvoda pronađeno"

    # Calculate potential savings: use actual discount savings (base_price - discount_price)
    total_savings = 0.0
    terms_with_savings = []
    for term in terms:
        # Use best_saving from the job (actual discount: base_price - discount_price)
        saving = term.get('best_saving', 0) or term.get('lowest_actual_saving', 0)
        if saving > 0:
            total_savings += saving
        terms_with_savings.append({**term, 'saving': saving})

    # Sort terms by saving (biggest first)
    terms_with_savings.sort(key=lambda x: -x.get('saving', 0))

    # First paragraph variations - imply work done for user
    intro_variations = [
        "Provjerili smo cijene za proizvode koje pratite — evo šta se promijenilo danas:",
        "Jutros smo pregledali sve trgovine za Vas. Evo šta smo pronašli:",
        "Upravo smo završili provjeru cijena. Pogledajte današnje rezultate:",
        "Danas smo za Vas pretražili ponude u svim trgovinama:",
        "Cijene su provjerene — evo pregleda za proizvode koje pratite:",
        "Vaša dnevna provjera cijena je završena. Evo rezultata:",
    ]
    intro_text = random.choice(intro_variations)

    # Build terms list (reordered by savings)
    terms_html = ""
    for term in terms_with_savings[:5]:
        lowest_price = term.get('lowest_price', 0)
        lowest_store = term.get('lowest_store', '')
        new_count = term.get("new_count", 0)
        saving = term.get('saving', 0)

        new_badge = f'<span style="display:inline-block;padding:2px 8px;background:#ECFDF5;color:#10B981;font-size:11px;border-radius:10px;margin-left:8px;">+{new_count} novo</span>' if new_count > 0 else ''
        saving_badge = f'<span style="display:inline-block;padding:2px 8px;background:#FEF3C7;color:#F59E0B;font-size:11px;border-radius:10px;margin-left:4px;">ušteda {saving:.2f} KM</span>' if saving > 0 else ''

        terms_html += f'''
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:4px;">{term.get('search_term', '')}{new_badge}{saving_badge}</div>
<div style="font-size:13px;color:#666;">Najniža cijena: <strong style="color:#10B981;">{lowest_price:.2f} KM</strong> u trgovini {lowest_store}</div>
</td></tr>
'''

    # Random CTA button text
    cta_options = [
        "Provjerite gdje je danas najjeftinije",
        "Ne preplaćujte – provjerite cijene",
        "Pogledajte gdje možete uštedjeti"
    ]
    cta_text = random.choice(cta_options)

    # Format savings display
    savings_display = f"do {total_savings:.2f} KM" if total_savings > 0 else "potencijalna ušteda"

    # Generate magic link URLs for auto-login when user_id is provided
    if user_id:
        moji_proizvodi_url = get_magic_link_url('/moji-proizvodi', user_id, 'daily_summary')
        profil_url = get_magic_link_url('/profil', user_id, 'daily_summary')
    else:
        moji_proizvodi_url = add_utm_params(f"{BASE_URL}/moji-proizvodi", campaign='daily_summary')
        profil_url = add_utm_params(f"{BASE_URL}/profil", campaign='daily_summary')

    content = f'''
<h1 style="margin:0 0 8px;font-size:22px;font-weight:600;color:#1a1a1a;">💰 Danas ima novih popusta na Vašoj listi</h1>
<p style="margin:0 0 24px;font-size:14px;color:#666;line-height:1.5;">{intro_text}</p>

<div style="background:#ECFDF5;border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
<div style="font-size:14px;color:#059669;margin-bottom:4px;">Potencijalna ušteda danas:</div>
<div style="font-size:32px;font-weight:700;color:#10B981;">👉 {savings_display}</div>
<div style="font-size:13px;color:#666;margin-top:8px;">na proizvodima koje već kupujete</div>
</div>

<p style="margin:0 0 16px;font-size:14px;font-weight:600;color:#1a1a1a;">Pregled po kategorijama:</p>
<table width="100%">{terms_html}</table>

<div style="margin:24px 0 16px;padding:12px 16px;background:#FEF3C7;border-radius:8px;border-left:3px solid #F59E0B;">
<p style="margin:0;font-size:13px;color:#92400E;">⚠️ Cijene se mijenjaju – provjerite prije odlaska u kupovinu.</p>
</div>

{get_button(cta_text, moji_proizvodi_url, "#7C3AED")}
<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:12px;color:#888;">
Vi dobijate ovaj email jer ste aktivirali praćenje proizvoda na Popust.ba.
<br>Možete upravljati obavijestima u <a href="{profil_url}" style="color:#7C3AED;">profilu</a>.
</p>
</div>
'''

    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


def send_weekly_summary_email(user_email: str, user_name: str, summary: dict) -> bool:
    """
    Send weekly comprehensive summary email with all tracked products.

    Features behavioral psychology:
    - Savings Framing: >= 10 KM uses direct savings, < 10 KM reframes as "avoided overpaying"
    - Preference Expansion: Users with <5 categories get soft guidance
    - Identity Reinforcement: "Smart shopper" messaging
    - Weekly Conclusion: Answer "Šta se najviše isplatilo pratiti?"
    - Value-driven CTAs

    summary should contain:
    - total_products: int (number of tracked terms)
    - total_matches: int (top N products per term)
    - total_savings: float (potential savings - realistic, 1 per term)
    - best_deals: list of top deals [{product, store, original_price, discount_price, savings_percent}]
    - tracked_items: list of top products per term with current best prices
    - price_drops: list of products that dropped in price this week
    - new_products: list of newly added products matching user's terms
    - terms_count: int (how many terms had matches)
    - max_price_diff_percent: float (highest % price difference between stores)
    - best_value_category: str (category with highest price spread)
    - category_insights: list of categories with their max % differences
    """
    greeting = f" {user_name}" if user_name else ""

    total_products = summary.get('total_products', 0)  # Number of tracked terms
    total_matches = summary.get('total_matches', len(summary.get('tracked_items', [])))  # Top N per term
    terms_count = summary.get('terms_count', total_products)
    total_savings = summary.get('total_savings', 0)
    best_deals = summary.get('best_deals', [])
    tracked_items = summary.get('tracked_items', [])
    price_drops = summary.get('price_drops', [])
    new_products = summary.get('new_products', [])
    hero_deal = summary.get('hero_deal')  # Single best deal with 90%+ match
    max_price_diff_percent = summary.get('max_price_diff_percent', 0)
    best_value_category = summary.get('best_value_category', '')
    category_insights = summary.get('category_insights', [])

    # === SAVINGS FRAMING LOGIC ===
    # If savings >= 10 KM: Direct savings language
    # If savings < 10 KM: Reframe as "avoided overpaying" + percentage emphasis
    if total_savings >= 10:
        savings_headline = f"Ove sedmice ste uštedjeli do {total_savings:.2f} KM"
        savings_box_title = "Potencijalna ušteda"
        savings_box_value = f"{total_savings:.2f} KM"
        savings_box_subtitle = "na proizvodima koje pratite"
    else:
        # Reframe: emphasize percentage difference and avoiding overpaying
        if max_price_diff_percent > 0:
            savings_headline = f"Izbjegli ste preplaćivanje do {max_price_diff_percent:.0f}%"
            savings_box_title = "Razlika u cijenama"
            savings_box_value = f"do {max_price_diff_percent:.0f}%"
            savings_box_subtitle = "između skuplje i jeftinije prodavnice"
        else:
            savings_headline = "Pratite cijene kao pametan kupac"
            savings_box_title = "Proizvoda pratite"
            savings_box_value = f"{total_products}"
            savings_box_subtitle = "svaki dan provjeravamo cijene za Vas"

    # === IDENTITY REINFORCEMENT ===
    # "Smart shopper" line near top
    identity_line = "Vi ste među pametnim kupcima koji ne preplaćuju."

    # === WEEKLY CONCLUSION ===
    # Answer: "Šta se ove sedmice najviše isplatilo pratiti?"
    weekly_conclusion = ""
    if best_value_category and max_price_diff_percent > 0:
        weekly_conclusion = f'''
<div style="margin:24px 0;padding:16px;background:#FEF3C7;border-radius:8px;border-left:3px solid #F59E0B;">
<p style="margin:0;font-size:14px;color:#92400E;line-height:1.5;">
<strong>Zaključak sedmice:</strong> Najviše se isplatilo pratiti <strong>"{best_value_category}"</strong> – razlika u cijenama između trgovina iznosi do {max_price_diff_percent:.0f}%.
</p>
</div>
'''

    # === PREFERENCE EXPANSION LOGIC ===
    # For users with <5 tracked terms, suggest tracking more (soft, encouraging tone)
    expansion_cta = ""
    if total_products < 5:
        expansion_cta = f'''
<div style="margin:24px 0;padding:20px;background:linear-gradient(135deg, #7C3AED 0%, #9333EA 100%);border-radius:12px;text-align:center;">
<p style="margin:0 0 8px;font-size:16px;color:#ffffff;font-weight:600;">Pratite {total_products} {'proizvod' if total_products == 1 else 'proizvoda'}</p>
<p style="margin:0 0 16px;font-size:13px;color:#E9D5FF;">Najveće uštede obično dolaze od artikala koje kupujete svake sedmice. Dodajte još proizvoda koje redovno kupujete.</p>
<a href="{add_utm_params(BASE_URL + '/moji-proizvodi', campaign='weekly_summary')}" style="display:inline-block;padding:12px 24px;background:#ffffff;border-radius:8px;font-size:14px;color:#7C3AED;text-decoration:none;font-weight:600;">Dodaj još proizvoda</a>
</div>
'''
    else:
        expansion_cta = f'''
<div style="margin:24px 0;padding:20px;background:linear-gradient(135deg, #7C3AED 0%, #9333EA 100%);border-radius:12px;text-align:center;">
<p style="margin:0 0 8px;font-size:16px;color:#ffffff;font-weight:600;">Pratite {total_products} proizvoda</p>
<p style="margin:0 0 16px;font-size:13px;color:#E9D5FF;">Nastavite pratiti cijene i mi ćemo Vas <strong>besplatno</strong> obavijestiti čim budu na akciji!</p>
<a href="{add_utm_params(BASE_URL + '/moji-proizvodi', campaign='weekly_summary')}" style="display:inline-block;padding:12px 24px;background:#ffffff;border-radius:8px;font-size:14px;color:#7C3AED;text-decoration:none;font-weight:600;">Pogledaj sve</a>
</div>
'''

    # Build best deals section
    best_deals_html = ""
    for deal in best_deals[:3]:
        savings_pct = deal.get('savings_percent', 0)
        best_deals_html += f'''
<tr><td style="padding:12px;background:#ECFDF5;border-radius:8px;margin-bottom:8px;">
<table width="100%"><tr>
<td style="vertical-align:top;">
<div style="font-size:14px;font-weight:600;color:#1a1a1a;">{deal.get('product', '')}</div>
<div style="font-size:12px;color:#666;margin-top:2px;">{deal.get('store', '')}</div>
</td>
<td style="text-align:right;vertical-align:top;">
{'<div style="font-size:12px;color:#888;text-decoration:line-through;">' + f"{deal.get('original_price', 0):.2f} KM</div>" if deal.get('original_price', 0) > 0 else ''}
<div style="font-size:16px;font-weight:700;color:#10B981;">{deal.get('discount_price', 0):.2f} KM</div>
<div style="font-size:11px;color:#10B981;">-{savings_pct:.0f}%</div>
</td>
</tr></table>
</td></tr>
<tr><td style="height:8px;"></td></tr>
'''

    # Build tracked items table
    tracked_html = ""
    for item in tracked_items[:10]:
        price_change = item.get('price_change', 0)
        change_color = '#10B981' if price_change < 0 else '#EF4444' if price_change > 0 else '#666'
        change_icon = '↓' if price_change < 0 else '↑' if price_change > 0 else '→'
        change_text = f"{change_icon} {abs(price_change):.2f}" if price_change != 0 else "—"

        tracked_html += f'''
<tr>
<td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#1a1a1a;">{item.get('product', '')}</td>
<td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#666;text-align:center;">{item.get('store', '')}</td>
<td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:13px;font-weight:600;color:#7C3AED;text-align:right;">{item.get('current_price', 0):.2f} KM</td>
<td style="padding:10px 0;border-bottom:1px solid #f0f0f0;font-size:12px;color:{change_color};text-align:right;">{change_text}</td>
</tr>
'''

    # Price drops section
    price_drops_html = ""
    if price_drops:
        drops_list = ""
        for drop in price_drops[:5]:
            drops_list += f'''
<tr><td style="padding:8px 0;border-bottom:1px solid #D1FAE5;">
<span style="font-size:13px;color:#1a1a1a;">{drop.get('product', '')}</span>
<span style="float:right;font-size:12px;color:#10B981;font-weight:600;">↓ {drop.get('drop_amount', 0):.2f} KM</span>
</td></tr>
'''
        price_drops_html = f'''
<div style="margin:24px 0;padding:16px;background:#ECFDF5;border-radius:8px;border-left:3px solid #10B981;">
<p style="margin:0 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Snižene cijene ove sedmice</p>
<table width="100%">{drops_list}</table>
</div>
'''

    # New products section
    new_products_html = ""
    if new_products:
        new_list = ""
        for prod in new_products[:5]:
            new_list += f'''
<tr><td style="padding:8px 0;border-bottom:1px solid #E9D5FF;">
<span style="font-size:13px;color:#1a1a1a;">{prod.get('product', '')}</span>
<span style="float:right;font-size:12px;color:#7C3AED;">{prod.get('store', '')} - {prod.get('price', 0):.2f} KM</span>
</td></tr>
'''
        new_products_html = f'''
<div style="margin:24px 0;padding:16px;background:#F5F3FF;border-radius:8px;border-left:3px solid #7C3AED;">
<p style="margin:0 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Novi proizvodi na Vašoj listi</p>
<table width="100%">{new_list}</table>
</div>
'''

    # Build hero deal section (prominent single deal with 90%+ match)
    hero_deal_html = ""
    if hero_deal:
        hero_savings = hero_deal.get('savings_amount', 0)
        hero_deal_html = f'''
<div style="margin:0 0 24px;padding:20px;background:linear-gradient(135deg, #10B981 0%, #059669 100%);border-radius:12px;text-align:center;">
<p style="margin:0 0 4px;font-size:12px;color:#D1FAE5;text-transform:uppercase;letter-spacing:1px;">Vaša najveća ušteda ove sedmice</p>
<p style="margin:0 0 8px;font-size:32px;font-weight:700;color:#ffffff;">-{hero_savings:.2f} KM</p>
<p style="margin:0 0 4px;font-size:14px;color:#ffffff;font-weight:500;">{hero_deal.get('product', '')}</p>
<p style="margin:0;font-size:12px;color:#A7F3D0;">{hero_deal.get('store', '')} | {'<span style="text-decoration:line-through;">' + f"{hero_deal.get('original_price', 0):.2f} KM</span> " if hero_deal.get('original_price', 0) > 0 else ''}<span style="font-weight:600;">{hero_deal.get('discount_price', 0):.2f} KM</span></p>
</div>
'''

    # === VALUE-DRIVEN CTA ===
    main_cta = get_button("Provjerite gdje je sada najjeftinije", f"{BASE_URL}/moji-proizvodi", "#7C3AED", campaign="weekly_summary")

    content = f'''
<h1 style="margin:0 0 8px;font-size:22px;font-weight:600;color:#1a1a1a;">Sedmični pregled Vaših proizvoda</h1>
<p style="margin:0 0 4px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 16px;font-size:14px;color:#7C3AED;font-weight:500;">{identity_line}</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">{savings_headline}</p>

{hero_deal_html}

<!-- Stats Overview -->
<table width="100%" style="margin-bottom:24px;"><tr>
<td style="width:32%;padding:16px;background:#F5F3FF;border-radius:8px;text-align:center;">
<div style="font-size:28px;font-weight:700;color:#7C3AED;">{total_products}</div>
<div style="font-size:12px;color:#666;margin-top:4px;">artikala pratite</div>
</td>
<td style="width:2%;"></td>
<td style="width:32%;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<div style="font-size:28px;font-weight:700;color:#1a1a1a;">{total_matches}</div>
<div style="font-size:12px;color:#666;margin-top:4px;">top ponuda</div>
</td>
<td style="width:2%;"></td>
<td style="width:32%;padding:16px;background:#ECFDF5;border-radius:8px;text-align:center;">
<div style="font-size:28px;font-weight:700;color:#10B981;">{savings_box_value}</div>
<div style="font-size:12px;color:#666;margin-top:4px;">{savings_box_subtitle}</div>
</td>
</tr></table>

{weekly_conclusion}

<!-- Best Deals -->
<p style="margin:0 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Najbolje ponude ove sedmice:</p>
<table width="100%">{best_deals_html}</table>

{price_drops_html}

{new_products_html}

<!-- Full List -->
<p style="margin:24px 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Top 2 ponude po svakom artiklu koji pratite:</p>
<table width="100%" style="font-size:12px;">
<tr style="background:#F9FAFB;">
<th style="padding:8px;text-align:left;color:#666;font-weight:500;">Proizvod</th>
<th style="padding:8px;text-align:center;color:#666;font-weight:500;">Trgovina</th>
<th style="padding:8px;text-align:right;color:#666;font-weight:500;">Cijena</th>
<th style="padding:8px;text-align:right;color:#666;font-weight:500;">Promjena</th>
</tr>
{tracked_html}
</table>

{main_cta}

{expansion_cta}

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:12px;color:#888;">
Primate ovaj email jednom sedmično jer imate aktivno praćenje proizvoda na Popust.ba.
<br>Za upravljanje obavještenjima posjetite <a href="{BASE_URL}/profil" style="color:#7C3AED;">Vaš profil</a>.
</p>
</div>
'''

    # Subject line - standardized order: savings first, then hero deal, then fallback
    # 1. Best (kad ima stvarne uštede) - prioritize showing savings amount
    if total_savings >= 1:
        subject = f"Ove sedmice: ušteda {total_savings:.2f} KM na Vašoj listi"
    # 2. Hero deal with context (product-specific)
    elif hero_deal:
        hero_savings = hero_deal.get('savings_amount', 0)
        subject = f"{hero_deal.get('product', '')[:30]}: sada {hero_savings:.2f} KM jeftinije"
    # 3. Fallback (bez hype-a)
    else:
        subject = f"Sedmični pregled Vaših praćenih proizvoda"

    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


def send_bonus_credits_email(user_email: str, user_name: str, credits_amount: int, reason: str, admin_message: str = None) -> bool:
    """
    Send exciting bonus credits notification email.

    Args:
        user_email: Recipient email
        user_name: User's name
        credits_amount: Number of bonus credits awarded
        reason: Short reason/title for the bonus (e.g., "Feedback nagrada", "Posebna promocija")
        admin_message: Optional custom message from admin

    Returns:
        bool: True if sent successfully
    """
    greeting = f" {user_name}" if user_name else ""

    # Custom message section
    custom_message_html = ""
    if admin_message:
        custom_message_html = f'''
<div style="margin:20px 0;padding:16px;background:#F9FAFB;border-radius:8px;border-left:3px solid #7C3AED;">
<p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-style:italic;">"{admin_message}"</p>
<p style="margin:8px 0 0;font-size:12px;color:#888;">— Tim Popust.ba</p>
</div>
'''

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">🎉</div>
<h1 style="margin:0 0 8px;font-size:26px;font-weight:700;color:#1a1a1a;">Čestitamo!</h1>
<p style="margin:0;font-size:16px;color:#666;">Dobili ste bonus kredite</p>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;text-align:center;">Poštovani{greeting},</p>

<div style="background:linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);border-radius:16px;padding:32px;text-align:center;margin:24px 0;">
<div style="font-size:64px;font-weight:800;color:#ffffff;text-shadow:0 2px 4px rgba(0,0,0,0.2);">+{credits_amount}</div>
<div style="font-size:18px;color:#E9D5FF;font-weight:500;margin-top:8px;">bonus kredita</div>
<div style="margin-top:16px;padding:8px 20px;background:rgba(255,255,255,0.2);border-radius:20px;display:inline-block;">
<span style="font-size:14px;color:#ffffff;font-weight:600;">{reason}</span>
</div>
</div>

{custom_message_html}

<p style="margin:24px 0;font-size:15px;color:#444;line-height:1.6;text-align:center;">
Ovi krediti su dodani na Vaš račun i možete ih odmah koristiti za praćenje proizvoda i pronalaženje najboljih ponuda!
</p>

<div style="background:#ECFDF5;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%"><tr>
<td style="vertical-align:middle;width:50px;">
<div style="width:40px;height:40px;background:#10B981;border-radius:50%;text-align:center;line-height:40px;">
<span style="color:#fff;font-size:18px;">✓</span>
</div>
</td>
<td style="vertical-align:middle;">
<div style="font-size:14px;font-weight:600;color:#1a1a1a;">Krediti su aktivni</div>
<div style="font-size:13px;color:#666;">Bonus krediti se nikad ne resetuju!</div>
</td>
</tr></table>
</div>

{get_button("Iskoristite kredite", f"{BASE_URL}/pretraga", "#10B981", campaign="bonus_credits")}

<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">
Hvala Vam što ste dio Popust.ba zajednice!
</p>
'''

    subject = f"🎁 Dobili ste {credits_amount} bonus kredita! | {reason}"
    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


# =============================================================================
# EXCLUSIVE COUPONS EMAIL FUNCTIONS
# =============================================================================

def send_coupon_purchase_email(user_email: str, user_name: str, coupon_data: dict) -> bool:
    """
    Send coupon purchase confirmation to buyer with redemption code.

    coupon_data should contain:
    - redemption_code: str (6-digit code)
    - article_name: str
    - business_name: str
    - business_address: str
    - original_price: float
    - final_price: float
    - discount_percent: int
    - expires_at: str (formatted date)
    - valid_days: int
    """
    greeting = f" {user_name}" if user_name else ""

    redemption_code = coupon_data.get('redemption_code', '------')
    article_name = coupon_data.get('article_name', '')
    business_name = coupon_data.get('business_name', '')
    business_address = coupon_data.get('business_address', '')
    original_price = coupon_data.get('original_price', 0)
    final_price = coupon_data.get('final_price', 0)
    discount_percent = coupon_data.get('discount_percent', 0)
    expires_at = coupon_data.get('expires_at', '')
    valid_days = coupon_data.get('valid_days', 0)

    # Only show original price row if original_price > 0
    original_price_row = f'''<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Originalna cijena</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;color:#888;text-decoration:line-through;">{original_price:.2f} KM</span>
</td>
</tr>''' if original_price > 0 else ''

    # Format redemption code with spaces for readability
    formatted_code = ' '.join([redemption_code[i:i+2] for i in range(0, len(redemption_code), 2)])

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">🎟️</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a1a;">Kupon uspješno kupljen!</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Čestitamo! Uspješno ste kupili ekskluzivni kupon. Ispod su detalji Vašeg kupona:</p>

<!-- Redemption Code Box -->
<div style="background:linear-gradient(135deg, #10B981 0%, #059669 100%);border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#A7F3D0;font-weight:500;margin-bottom:8px;">VAŠ KOD ZA ISKORIŠTAVANJE</div>
<div style="font-size:42px;font-weight:800;color:#ffffff;letter-spacing:8px;font-family:monospace;">{formatted_code}</div>
<div style="font-size:12px;color:#A7F3D0;margin-top:12px;">Pokažite ovaj kod na blagajni</div>
</div>

<!-- Coupon Details -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Artikal</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{article_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Trgovina</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{business_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Adresa</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;color:#444;">{business_address}</span>
</td>
</tr>
{original_price_row}
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Vaša cijena</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:18px;font-weight:700;color:#10B981;">{final_price:.2f} KM</span>
<span style="display:inline-block;padding:2px 8px;background:#ECFDF5;color:#10B981;font-size:11px;border-radius:10px;margin-left:8px;">-{discount_percent}%</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<span style="font-size:13px;color:#666;">Vrijedi do</span>
</td>
<td style="padding:10px 0;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#EF4444;">{expires_at}</span>
<span style="font-size:12px;color:#888;margin-left:4px;">({valid_days} dana)</span>
</td>
</tr>
</table>
</div>

<!-- Important Notice -->
<div style="margin:24px 0;padding:16px;background:#FEF3C7;border-radius:8px;border-left:3px solid #F59E0B;">
<p style="margin:0;font-size:13px;color:#92400E;line-height:1.5;">
<strong>Važno:</strong> Kupon možete iskoristiti samo jednom. Pokažite kod na blagajni trgovine {business_name} prije isteka roka.
</p>
</div>

{get_button("Pogledajte moje kupone", f"{BASE_URL}/profil/kuponi", "#7C3AED", campaign="coupon_purchase")}

<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">
Uživajte u uštedi!
</p>
'''

    subject = f"🎟️ Vaš kupon za {article_name} | Kod: {formatted_code}"
    html = get_base_template(content, "#10B981")
    return send_email(user_email, subject, html)


def send_coupon_sale_notification_email(business_email: str, business_name: str, sale_data: dict) -> bool:
    """
    Send notification to business owner when someone purchases their coupon.

    sale_data should contain:
    - buyer_name: str
    - article_name: str
    - final_price: float
    - remaining_quantity: int
    - total_sold: int
    """
    buyer_name = sale_data.get('buyer_name', 'Korisnik')
    article_name = sale_data.get('article_name', '')
    final_price = sale_data.get('final_price', 0)
    remaining_quantity = sale_data.get('remaining_quantity', 0)
    total_sold = sale_data.get('total_sold', 0)

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">💰</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a1a;">Nova prodaja kupona!</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
Upravo je neko kupio Vaš ekskluzivni kupon na Popust.ba!
</p>

<!-- Sale Details -->
<div style="background:linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#E9D5FF;font-weight:500;margin-bottom:8px;">PRODATO</div>
<div style="font-size:24px;font-weight:700;color:#ffffff;">{article_name}</div>
<div style="font-size:32px;font-weight:800;color:#ffffff;margin-top:12px;">{final_price:.2f} KM</div>
</div>

<!-- Stats -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Kupac</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{buyer_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Ukupno prodato</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#7C3AED;">{total_sold}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<span style="font-size:13px;color:#666;">Preostalo</span>
</td>
<td style="padding:10px 0;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{remaining_quantity}</span>
</td>
</tr>
</table>
</div>

<p style="margin:24px 0;font-size:14px;color:#444;line-height:1.6;text-align:center;">
Kupac će doći u Vašu trgovinu sa kodom za iskorištavanje.
Kod možete potvrditi na Vašoj poslovnoj kontrolnoj ploči.
</p>

{get_button("Otvorite kontrolnu ploču", f"{BASE_URL}/moj-biznis", "#7C3AED", campaign="coupon_sold")}
'''

    subject = f"💰 Nova prodaja: {article_name} | {business_name}"
    html = get_base_template(content, "#7C3AED")
    return send_email(business_email, subject, html)


def send_coupon_halfway_reminder_email(user_email: str, user_name: str, coupon_data: dict) -> bool:
    """
    Send reminder when coupon is at 50% of its validity period.

    coupon_data should contain:
    - redemption_code: str
    - article_name: str
    - business_name: str
    - business_address: str
    - final_price: float
    - expires_at: str
    - days_remaining: int
    """
    greeting = f" {user_name}" if user_name else ""

    redemption_code = coupon_data.get('redemption_code', '------')
    article_name = coupon_data.get('article_name', '')
    business_name = coupon_data.get('business_name', '')
    business_address = coupon_data.get('business_address', '')
    final_price = coupon_data.get('final_price', 0)
    expires_at = coupon_data.get('expires_at', '')
    days_remaining = coupon_data.get('days_remaining', 0)

    formatted_code = ' '.join([redemption_code[i:i+2] for i in range(0, len(redemption_code), 2)])

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">⏰</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a1a;">Podsjetnik: Vaš kupon ističe uskoro</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
Podsjetnik da Vam je prešla polovina roka za iskorištavanje Vašeg ekskluzivnog kupona.
Ne zaboravite ga iskoristiti!
</p>

<!-- Time Warning -->
<div style="background:#FEF3C7;border-radius:12px;padding:20px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#92400E;font-weight:500;margin-bottom:4px;">PREOSTALO VRIJEME</div>
<div style="font-size:36px;font-weight:800;color:#F59E0B;">{days_remaining} dana</div>
<div style="font-size:13px;color:#92400E;margin-top:8px;">Ističe: {expires_at}</div>
</div>

<!-- Coupon Info -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Artikal</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{article_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Trgovina</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{business_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<span style="font-size:13px;color:#666;">Adresa</span>
</td>
<td style="padding:10px 0;text-align:right;">
<span style="font-size:14px;color:#444;">{business_address}</span>
</td>
</tr>
</table>
</div>

<!-- Redemption Code -->
<div style="background:#ECFDF5;border-radius:12px;padding:16px;text-align:center;margin:24px 0;">
<div style="font-size:12px;color:#059669;font-weight:500;margin-bottom:4px;">VAŠ KOD</div>
<div style="font-size:28px;font-weight:700;color:#10B981;letter-spacing:4px;font-family:monospace;">{formatted_code}</div>
</div>

{get_button("Pogledajte detalje kupona", f"{BASE_URL}/profil/kuponi", "#F59E0B", campaign="coupon_reminder")}
'''

    subject = f"⏰ Podsjetnik: Kupon za {article_name} ističe za {days_remaining} dana"
    html = get_base_template(content, "#F59E0B")
    return send_email(user_email, subject, html)


def send_coupon_expiry_reminder_email(user_email: str, user_name: str, coupon_data: dict) -> bool:
    """
    Send urgent reminder when coupon expires tomorrow.

    coupon_data should contain:
    - redemption_code: str
    - article_name: str
    - business_name: str
    - business_address: str
    - final_price: float
    - expires_at: str
    """
    greeting = f" {user_name}" if user_name else ""

    redemption_code = coupon_data.get('redemption_code', '------')
    article_name = coupon_data.get('article_name', '')
    business_name = coupon_data.get('business_name', '')
    business_address = coupon_data.get('business_address', '')
    final_price = coupon_data.get('final_price', 0)
    expires_at = coupon_data.get('expires_at', '')

    formatted_code = ' '.join([redemption_code[i:i+2] for i in range(0, len(redemption_code), 2)])

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">🚨</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#EF4444;">HITNO: Kupon ističe sutra!</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
<strong>Vaš ekskluzivni kupon ističe sutra!</strong> Ne propustite priliku za uštedu -
iskoristite kupon danas ili sutra prije isteka.
</p>

<!-- Urgent Warning -->
<div style="background:#FEE2E2;border-radius:12px;padding:20px;text-align:center;margin:24px 0;border:2px solid #EF4444;">
<div style="font-size:14px;color:#991B1B;font-weight:600;margin-bottom:4px;">⚠️ ISTIČE SUTRA ⚠️</div>
<div style="font-size:18px;font-weight:700;color:#EF4444;">{expires_at}</div>
</div>

<!-- Coupon Info -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Artikal</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{article_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Vaša cijena</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:18px;font-weight:700;color:#10B981;">{final_price:.2f} KM</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Trgovina</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{business_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<span style="font-size:13px;color:#666;">Adresa</span>
</td>
<td style="padding:10px 0;text-align:right;">
<span style="font-size:14px;color:#444;">{business_address}</span>
</td>
</tr>
</table>
</div>

<!-- Redemption Code - Prominent -->
<div style="background:linear-gradient(135deg, #10B981 0%, #059669 100%);border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#A7F3D0;font-weight:500;margin-bottom:8px;">VAŠ KOD ZA ISKORIŠTAVANJE</div>
<div style="font-size:42px;font-weight:800;color:#ffffff;letter-spacing:8px;font-family:monospace;">{formatted_code}</div>
</div>

{get_button("Pogledajte kupon", f"{BASE_URL}/profil/kuponi", "#EF4444", campaign="coupon_expired")}

<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">
Požurite dok nije kasno!
</p>
'''

    subject = f"🚨 HITNO: Kupon za {article_name} ističe SUTRA!"
    html = get_base_template(content, "#EF4444")
    return send_email(user_email, subject, html)


def send_coupon_redemption_email(user_email: str, user_name: str, redemption_data: dict) -> bool:
    """
    Send confirmation when coupon is redeemed, with prompt to leave review.

    redemption_data should contain:
    - article_name: str
    - business_name: str
    - final_price: float
    - savings: float
    - redeemed_at: str (formatted datetime)
    """
    greeting = f" {user_name}" if user_name else ""

    article_name = redemption_data.get('article_name', '')
    business_name = redemption_data.get('business_name', '')
    final_price = redemption_data.get('final_price', 0)
    savings = redemption_data.get('savings', 0)
    redeemed_at = redemption_data.get('redeemed_at', '')

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">✅</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#10B981;">Kupon uspješno iskorišten!</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
Čestitamo! Uspješno ste iskoristili Vaš ekskluzivni kupon.
Nadamo se da ste zadovoljni uslugom!
</p>

<!-- Success Box -->
<div style="background:#ECFDF5;border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#059669;font-weight:500;margin-bottom:8px;">UŠTEDJELI STE</div>
<div style="font-size:42px;font-weight:800;color:#10B981;">{savings:.2f} KM</div>
</div>

<!-- Details -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Artikal</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{article_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Trgovina</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{business_name}</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;">
<span style="font-size:13px;color:#666;">Plaćeno</span>
</td>
<td style="padding:10px 0;border-bottom:1px solid #e5e5e5;text-align:right;">
<span style="font-size:16px;font-weight:700;color:#1a1a1a;">{final_price:.2f} KM</span>
</td>
</tr>
<tr>
<td style="padding:10px 0;">
<span style="font-size:13px;color:#666;">Iskorišteno</span>
</td>
<td style="padding:10px 0;text-align:right;">
<span style="font-size:14px;color:#444;">{redeemed_at}</span>
</td>
</tr>
</table>
</div>

<!-- Review Prompt -->
<div style="margin:24px 0;padding:20px;background:#F5F3FF;border-radius:12px;text-align:center;">
<div style="font-size:28px;margin-bottom:8px;">⭐</div>
<p style="margin:0 0 12px;font-size:15px;font-weight:600;color:#1a1a1a;">Kako je bilo Vaše iskustvo?</p>
<p style="margin:0 0 16px;font-size:14px;color:#666;">
Vaša ocjena pomaže drugim korisnicima i poboljšava kvalitet ponuda.
</p>
{get_button("Ocijenite iskustvo", f"{BASE_URL}/profil/kuponi", "#7C3AED", campaign="coupon_feedback")}
</div>

<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">
Hvala što koristite Popust.ba ekskluzivne ponude!
</p>
'''

    subject = f"✅ Kupon iskorišten: {article_name} | Uštedjeli ste {savings:.2f} KM"
    html = get_base_template(content, "#10B981")
    return send_email(user_email, subject, html)


def send_reengagement_email(user_email: str, user_name: str, data: dict) -> bool:
    """
    Send monthly re-engagement email to users without tracked products.
    Shows popular items others are tracking and best current deals.

    data should contain:
    - popular_terms: list of dicts [{term, users_count}]
    - best_deals: list of dicts [{title, store, discount_price, discount_percent}]
    - total_users_tracking: int (how many users are tracking products)
    """
    import random

    greeting = f" {user_name}" if user_name else ""

    popular_terms = data.get('popular_terms', [])
    best_deals = data.get('best_deals', [])
    total_users = data.get('total_users_tracking', 0)

    # Build popular terms section
    terms_html = ""
    for term in popular_terms[:6]:
        terms_html += f'''
<tr><td style="padding:8px 12px;background:#F5F3FF;border-radius:8px;margin:4px 0;">
<span style="font-size:14px;font-weight:600;color:#7C3AED;">{term.get('term', '')}</span>
<span style="float:right;font-size:12px;color:#666;">popularno</span>
</td></tr>
<tr><td style="height:6px;"></td></tr>
'''

    # Build best deals section
    deals_html = ""
    for deal in best_deals[:5]:
        discount_pct = deal.get('discount_percent', 0)
        deals_html += f'''
<tr><td style="padding:12px;background:#ECFDF5;border-radius:8px;margin-bottom:8px;">
<table width="100%"><tr>
<td style="vertical-align:top;">
<div style="font-size:14px;font-weight:600;color:#1a1a1a;">{deal.get('title', '')[:40]}{'...' if len(deal.get('title', '')) > 40 else ''}</div>
<div style="font-size:12px;color:#666;margin-top:2px;">{deal.get('store', '')}</div>
</td>
<td style="text-align:right;vertical-align:top;white-space:nowrap;">
<div style="font-size:16px;font-weight:700;color:#10B981;">{deal.get('discount_price', 0):.2f} KM</div>
<div style="font-size:11px;color:#10B981;font-weight:600;">-{discount_pct}%</div>
</td>
</tr></table>
</td></tr>
<tr><td style="height:8px;"></td></tr>
'''

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">🛒</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a1a;">Treba Vam samo 10 sekundi</h1>
</div>

<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">
Dovoljno je da napišete 2–3 proizvoda koje kupujete svake sedmice.<br>
<strong>Mi ćemo pratiti cijene umjesto Vas.</strong>
</p>

<!-- Social Proof Box -->
<div style="background:linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#E9D5FF;font-weight:500;margin-bottom:4px;">ZAŠTO PRATITI PROIZVODE?</div>
<div style="font-size:24px;font-weight:700;color:#ffffff;">U prosjeku korisnici uštede 15% na proizvodima koje prate</div>
<div style="font-size:14px;color:#E9D5FF;margin-top:8px;">primajući dnevne obavijesti o cijenama</div>
</div>

<!-- Popular Terms -->
<p style="margin:24px 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Najpopularniji proizvodi koje korisnici prate:</p>
<table width="100%">{terms_html}</table>

<!-- Best Deals -->
<p style="margin:24px 0 12px;font-size:14px;font-weight:600;color:#1a1a1a;">Aktualne top ponude:</p>
<table width="100%">{deals_html}</table>

<!-- CTA -->
<div style="margin:32px 0;padding:24px;background:#F9FAFB;border-radius:12px;text-align:center;">
<p style="margin:0 0 16px;font-size:16px;font-weight:600;color:#1a1a1a;">Postavite praćenje u 2 minute!</p>
<p style="margin:0 0 20px;font-size:14px;color:#666;">
Samo odaberite proizvode koje redovno kupujete i mi ćemo Vas obavijestiti kada su na akciji.
</p>
{get_button("Postavi praćenje proizvoda", f"{BASE_URL}/moji-proizvodi", "#7C3AED", campaign="reengagement")}
</div>

<div style="margin:24px 0;padding:16px;background:#FEF3C7;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:13px;color:#92400E;">
<strong>Bonus:</strong> Svaki dan kada posjetite Popust.ba dobivate +2 kredita za praćenje proizvoda!
</p>
</div>

<p style="margin:24px 0 0;font-size:12px;color:#888;text-align:center;">
Ovaj email primate jednom mjesečno. Za upravljanje obavještenjima posjetite <a href="{BASE_URL}/profil" style="color:#7C3AED;">Vaš profil</a>.
</p>
'''

    # Action-focused subjects (rotate) - sell the action, not "best deals"
    subject_options = [
        "Treba Vam 10 sekundi da ovo postavite 🛒",
        "Popust.ba još ne zna šta kupujete",
        "Bez praćenja = bez obavijesti o akcijama",
        "Postavite praćenje za artikle koje već kupujete",
    ]
    subject = random.choice(subject_options)
    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


def send_new_rating_notification_email(recipient_email: str, recipient_name: str, rating_data: dict, is_business: bool = False) -> bool:
    """
    Send notification when someone receives a new rating.

    rating_data should contain:
    - rater_name: str (who gave the rating)
    - rating: int (1-5)
    - comment: str (optional)
    - article_name: str
    - business_name: str (if recipient is user)
    """
    greeting = f" {recipient_name}" if recipient_name else ""

    rater_name = rating_data.get('rater_name', 'Korisnik')
    rating = rating_data.get('rating', 5)
    comment = rating_data.get('comment', '')
    article_name = rating_data.get('article_name', '')
    business_name = rating_data.get('business_name', '')

    # Generate star rating visual
    stars = '★' * rating + '☆' * (5 - rating)
    star_color = '#F59E0B' if rating >= 4 else '#9CA3AF' if rating >= 2 else '#EF4444'

    if is_business:
        title = "Dobili ste novu ocjenu od kupca!"
        description = f"Kupac <strong>{rater_name}</strong> je ocijenio Vašu uslugu."
        context_label = "Artikal"
        context_value = article_name
    else:
        title = f"Trgovina {business_name} Vas je ocijenila!"
        description = f"Trgovina je ocijenila Vaše iskustvo prilikom korištenja kupona."
        context_label = "Trgovina"
        context_value = business_name

    comment_html = ""
    if comment:
        comment_html = f'''
<div style="margin:16px 0;padding:16px;background:#F9FAFB;border-radius:8px;border-left:3px solid #7C3AED;">
<p style="margin:0;font-size:14px;color:#444;line-height:1.6;font-style:italic;">"{comment}"</p>
</div>
'''

    content = f'''
<div style="text-align:center;margin-bottom:24px;">
<div style="font-size:48px;margin-bottom:8px;">⭐</div>
<h1 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1a1a1a;">{title}</h1>
</div>

<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">{description}</p>

<!-- Rating Display -->
<div style="background:#FEF3C7;border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:36px;color:{star_color};letter-spacing:4px;">{stars}</div>
<div style="font-size:24px;font-weight:700;color:#1a1a1a;margin-top:8px;">{rating}/5</div>
</div>

{comment_html}

<!-- Context -->
<div style="background:#F9FAFB;border-radius:12px;padding:16px;margin:24px 0;">
<table width="100%">
<tr>
<td style="padding:8px 0;">
<span style="font-size:13px;color:#666;">{context_label}</span>
</td>
<td style="padding:8px 0;text-align:right;">
<span style="font-size:14px;font-weight:600;color:#1a1a1a;">{context_value}</span>
</td>
</tr>
</table>
</div>

{get_button("Pogledajte detalje", f"{BASE_URL}/profil/kuponi" if not is_business else f"{BASE_URL}/moj-biznis", "#7C3AED", campaign="coupon_redeemed")}
'''

    subject = f"⭐ Nova ocjena: {rating}/5 | {article_name}"
    html = get_base_template(content, "#F59E0B")
    return send_email(recipient_email, subject, html)


# =============================================================================
# ACTIVATION / WIN-BACK EMAIL FOR INACTIVE USERS
# =============================================================================

def send_activation_email(user_email: str, user_name: str, example_savings: dict = None) -> bool:
    """
    Send weekly activation email to users WITHOUT tracked products.
    Shows example savings they could achieve to encourage feature adoption.

    example_savings should contain real platform data:
    - avg_weekly_savings: float (average savings across all users)
    - top_category: str (most popular tracked category)
    - top_category_savings: float (avg savings in that category)
    - example_products: list of sample products with savings
    """
    greeting = f" {user_name}" if user_name else ""

    # Default example data if not provided (use real platform averages)
    if not example_savings:
        example_savings = {
            'avg_weekly_savings': 12.50,
            'top_category': 'Mlijeko',
            'top_category_savings': 0.65,
            'example_products': [
                {'name': 'Meggle Mlijeko 2.8% 1L', 'store': 'Bingo', 'saving': 0.65, 'percent': 26},
                {'name': 'Grand Kafa Gold 200g', 'store': 'Konzum', 'saving': 1.91, 'percent': 21},
                {'name': 'Nutella 400g', 'store': 'Mercator', 'saving': 2.51, 'percent': 20},
            ]
        }

    avg_savings = example_savings.get('avg_weekly_savings', 12.50)
    top_category = example_savings.get('top_category', 'Mlijeko')
    example_products = example_savings.get('example_products', [])

    # Build example products table
    products_html = ""
    for product in example_products[:3]:
        products_html += f'''
<tr>
<td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<div style="font-size:14px;color:#1a1a1a;font-weight:500;">{product['name']}</div>
<div style="font-size:12px;color:#888;margin-top:2px;">{product['store']}</div>
</td>
<td style="padding:12px 0;border-bottom:1px solid #f0f0f0;text-align:right;">
<div style="font-size:14px;font-weight:600;color:#10B981;">-{product['saving']:.2f} KM</div>
<div style="font-size:11px;color:#888;">{product['percent']}% jeftinije</div>
</td>
</tr>
'''

    content = f'''
<h1 style="margin:0 0 8px;font-size:22px;font-weight:600;color:#1a1a1a;">10 sekundi za {avg_savings:.2f} KM uštede</h1>
<p style="margin:0 0 24px;font-size:15px;color:#666;line-height:1.6;">Poštovani{greeting},</p>

<p style="margin:0 0 20px;font-size:15px;color:#444;line-height:1.6;">
Dodajte 2–3 artikla koje kupujete svake sedmice. <strong>Mi ćemo pratiti cijene umjesto Vas.</strong>
</p>

<!-- Savings Showcase Box -->
<div style="background:linear-gradient(135deg, #10B981 0%, #059669 100%);border-radius:16px;padding:24px;text-align:center;margin:24px 0;">
<div style="font-size:14px;color:#D1FAE5;margin-bottom:8px;">Prosječna sedmična ušteda</div>
<div style="font-size:42px;font-weight:800;color:#ffffff;">{avg_savings:.2f} KM</div>
<div style="font-size:13px;color:#A7F3D0;margin-top:8px;">za korisnike koji prate proizvode</div>
</div>

<!-- How it works -->
<div style="margin:24px 0;">
<h3 style="margin:0 0 16px;font-size:16px;color:#1a1a1a;">Kako to funkcioniše?</h3>
<p style="margin:0 0 16px;font-size:14px;color:#666;line-height:1.6;">
Svaki dan provjeravamo cijene u svim trgovinama. Kad cijena padne — dobijate obavijest.
</p>
</div>

<!-- Example savings this week -->
<div style="background:#F9FAFB;border-radius:12px;padding:20px;margin:24px 0;">
<h3 style="margin:0 0 16px;font-size:15px;color:#1a1a1a;">Primjer: ove sedmice ste mogli uštedjeti na:</h3>
<table width="100%" style="border-collapse:collapse;">
{products_html}
</table>
</div>

<!-- CTA -->
{get_button("Dodajte svoje proizvode", f"{BASE_URL}/moji-proizvodi", "#7C3AED", campaign="weekly_activation")}

<p style="margin:24px 0;font-size:14px;color:#666;line-height:1.6;text-align:center;">
U prosjeku naši korisnici prate 10 artikala.<br>
Mi ćemo vas obavijestiti čim se pojavi bolja cijena!
</p>

<!-- Suggestion box -->
<div style="margin:24px 0;padding:16px;background:#FEF3C7;border-radius:8px;border-left:3px solid #F59E0B;">
<p style="margin:0;font-size:13px;color:#92400E;line-height:1.5;">
<strong>Prijedlog:</strong> Najpopularnije kategorije za praćenje su mlijeko, kafa, ulje i šećer – proizvodi koje kupujete svake sedmice!
</p>
</div>

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:12px;color:#888;">
Primate ovaj email jer ste registrovani na Popust.ba.
<br>Za upravljanje obavještenjima posjetite <a href="{BASE_URL}/profil" style="color:#7C3AED;">Vaš profil</a>.
</p>
</div>
'''

    # Subject with low-effort cues - rotate between options
    subject_options = [
        f"Uštedjeli biste {avg_savings:.2f} KM ove sedmice (treba 10 sekundi)",
        f"{avg_savings:.2f} KM potencijalne uštede — dodajte 2 artikla",
        f"Ovo je najlakša ušteda ove sedmice: {avg_savings:.2f} KM",
    ]
    subject = random.choice(subject_options)
    html = get_base_template(content, "#10B981")
    return send_email(user_email, subject, html)
