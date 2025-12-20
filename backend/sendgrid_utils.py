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


def generate_verification_token():
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


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


def get_button(text: str, url: str, color: str = "#7C3AED") -> str:
    """Generate a CTA button"""
    return f'''<table style="margin:24px auto;"><tr>
<td style="background-color:{color};border-radius:8px;">
<a href="{url}" style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">{text}</a>
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
{get_button("Potvrdi email adresu", verification_url, "#10B981")}
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

{get_button("Započnite pretragu", BASE_URL, "#7C3AED")}
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
{get_button("Postavite novu lozinku", reset_url, "#EF4444")}
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

{get_button("Prihvatite pozivnicu", invitation_url, "#10B981")}
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
    admin_email = "adnanxteam@gmail.com"
    return send_email(admin_email, subject, html)


def send_scan_summary_email(user_email: str, user_name: str, summary: dict) -> bool:
    """Send daily product scan summary email"""
    total = summary.get('total_products', 0)
    new_products = summary.get('new_products', 0)
    new_discounts = summary.get('new_discounts', 0)
    terms = summary.get('terms', [])

    greeting = f" {user_name}" if user_name else ""

    # Dynamic subject - professional tone
    if new_products > 0:
        subject = f"Pronađeno {new_products} novih proizvoda na Vašoj listi"
    elif new_discounts > 0:
        subject = f"{new_discounts} novih sniženja na proizvodima koje pratite"
    else:
        subject = f"Dnevni pregled - {total} proizvoda pronađeno"

    # Build terms list
    terms_html = ""
    for term in terms[:5]:
        lowest_price = term.get('lowest_price', 0)
        lowest_store = term.get('lowest_store', '')
        new_count = term.get("new_count", 0)
        new_badge = f'<span style="display:inline-block;padding:2px 8px;background:#ECFDF5;color:#10B981;font-size:11px;border-radius:10px;margin-left:8px;">+{new_count} novo</span>' if new_count > 0 else ''

        terms_html += f'''
<tr><td style="padding:12px 0;border-bottom:1px solid #f0f0f0;">
<div style="font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:4px;">{term.get('search_term', '')}{new_badge}</div>
<div style="font-size:13px;color:#666;">Najniža cijena: <strong style="color:#10B981;">{lowest_price:.2f} KM</strong> u trgovini {lowest_store}</div>
</td></tr>
'''

    # Badges
    badges = ""
    if new_products > 0:
        badges += f'<span style="display:inline-block;padding:4px 12px;background:#ECFDF5;color:#10B981;font-size:13px;border-radius:12px;margin:0 4px;">{new_products} novih</span>'
    if new_discounts > 0:
        badges += f'<span style="display:inline-block;padding:4px 12px;background:#FEF3C7;color:#F59E0B;font-size:13px;border-radius:12px;margin:0 4px;">{new_discounts} sniženih</span>'

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Dnevni pregled Vaših proizvoda</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Pripremili smo pregled cijena za proizvode koje pratite. Evo najnovijih informacija:</p>

<div style="background:#F5F3FF;border-radius:12px;padding:20px;text-align:center;margin-bottom:24px;">
<div style="font-size:36px;font-weight:700;color:#7C3AED;">{total}</div>
<div style="font-size:14px;color:#666;margin-top:4px;">proizvoda pronađeno</div>
<div style="margin-top:12px;">{badges}</div>
</div>

<p style="margin:0 0 16px;font-size:14px;font-weight:600;color:#1a1a1a;">Pregled po kategorijama:</p>
<table width="100%">{terms_html}</table>

{get_button("Pogledajte sve proizvode", f"{BASE_URL}/moji-proizvodi", "#7C3AED")}
<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:12px;color:#888;">
Primate ovaj email jer imate aktivno praćenje proizvoda na Popust.ba.
Za upravljanje obavještenjima posjetite postavke Vašeg računa.
</p>
</div>
'''

    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)


def send_weekly_summary_email(user_email: str, user_name: str, summary: dict) -> bool:
    """
    Send weekly comprehensive summary email with all tracked products.

    summary should contain:
    - total_products: int (number of tracked terms)
    - total_matches: int (top N products per term)
    - total_savings: float (potential savings - realistic, 1 per term)
    - best_deals: list of top deals [{product, store, original_price, discount_price, savings_percent}]
    - tracked_items: list of top products per term with current best prices
    - price_drops: list of products that dropped in price this week
    - new_products: list of newly added products matching user's terms
    - terms_count: int (how many terms had matches)
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
<div style="font-size:12px;color:#888;text-decoration:line-through;">{deal.get('original_price', 0):.2f} KM</div>
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

    content = f'''
<h1 style="margin:0 0 16px;font-size:22px;font-weight:600;color:#1a1a1a;">Sedmični pregled Vaših proizvoda</h1>
<p style="margin:0 0 16px;font-size:15px;color:#444;line-height:1.6;">Poštovani{greeting},</p>
<p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.6;">Pripremili smo detaljan pregled svih proizvoda koje pratite. Evo šta se dogodilo ove sedmice:</p>

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
<div style="font-size:28px;font-weight:700;color:#10B981;">{total_savings:.2f} KM</div>
<div style="font-size:12px;color:#666;margin-top:4px;">potencijalna ušteda</div>
</td>
</tr></table>

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

{get_button("Pogledajte sve detalje", f"{BASE_URL}/moji-proizvodi", "#7C3AED")}

<!-- Engagement hooks -->
<div style="margin:24px 0;padding:20px;background:#F9FAFB;border-radius:12px;text-align:center;">
<p style="margin:0 0 16px;font-size:14px;color:#1a1a1a;font-weight:500;">Želite pronaći još povoljnijih ponuda?</p>
<table style="margin:0 auto;"><tr>
<td style="padding:0 8px;">
<a href="{BASE_URL}/pretraga" style="display:inline-block;padding:10px 20px;background:#ffffff;border:1px solid #7C3AED;border-radius:6px;font-size:13px;color:#7C3AED;text-decoration:none;">Pretražite ponude</a>
</td>
<td style="padding:0 8px;">
<a href="{BASE_URL}/favoriti" style="display:inline-block;padding:10px 20px;background:#ffffff;border:1px solid #7C3AED;border-radius:6px;font-size:13px;color:#7C3AED;text-decoration:none;">Moji favoriti</a>
</td>
</tr></table>
</div>

<div style="margin:24px 0 0;padding:16px;background:#F9FAFB;border-radius:8px;text-align:center;">
<p style="margin:0;font-size:12px;color:#888;">
Primate ovaj email jednom sedmično jer imate aktivno praćenje proizvoda na Popust.ba.
<br>Za upravljanje obavještenjima posjetite <a href="{BASE_URL}/profil" style="color:#7C3AED;">Vaš profil</a>.
</p>
</div>
'''

    subject = f"Sedmični pregled: {total_products} artikala koje pratite | Ušteda do {total_savings:.2f} KM"
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

{get_button("Iskoristite kredite", f"{BASE_URL}/pretraga", "#10B981")}

<p style="margin:24px 0 0;font-size:13px;color:#888;text-align:center;">
Hvala Vam što ste dio Popust.ba zajednice!
</p>
'''

    subject = f"🎁 Dobili ste {credits_amount} bonus kredita! | {reason}"
    html = get_base_template(content, "#7C3AED")
    return send_email(user_email, subject, html)
