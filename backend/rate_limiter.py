"""
Rate limiting configuration for anti-scraping protection.

These limits are designed to be IMPOSSIBLE for normal human users to hit,
but will catch automated scrapers and bots trying to exploit the API.

Human browsing behavior:
- Fastest clicking: ~2-3 clicks/second = 120-180/min
- Realistic browsing: 1 page every 2-5 seconds = 12-30/min

Bot/scraper behavior:
- Can easily do 100+ requests/second = 6000+/min
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMIT CONFIGURATION
# All limits are PER IP ADDRESS - generous enough that no human could hit them
# ============================================================================

# Global default: 600 requests/minute (10/sec) - impossible for human clicking
DEFAULT_LIMIT = "600 per minute"

# Search endpoints (expensive - LLM/embedding calls)
# Human: max 1 search every 2 seconds = 30/min
# Limit: 100/min - still 3x faster than humanly possible
SEARCH_LIMIT = "100 per minute"

# Product listing/detail pages (cheaper but valuable data)
# Human: browsing products = maybe 60/min if clicking fast
# Limit: 300/min - 5x faster than humanly possible
PRODUCTS_LIMIT = "300 per minute"

# Authentication endpoints (brute force protection)
# Human: typing login credentials = maybe 2-3 attempts/min
# Limit: 20/min - prevents credential stuffing
AUTH_LIMIT = "20 per minute"

# File uploads (storage/processing costs)
# Human: uploading images = maybe 5/min max
# Limit: 30/min - generous but prevents abuse
UPLOAD_LIMIT = "30 per minute"

# Cart/checkout (prevent shopping cart abuse)
# Human: adding items = maybe 10/min if shopping fast
# Limit: 60/min - generous for power users
CART_LIMIT = "60 per minute"

# Admin endpoints (sensitive operations)
# Even admins don't need more than this
ADMIN_LIMIT = "120 per minute"


def get_client_ip():
    """
    Get the real client IP, handling proxies (Railway, Cloudflare, etc.)
    """
    # Check for forwarded IP headers (in order of preference)
    forwarded_headers = [
        'CF-Connecting-IP',  # Cloudflare
        'X-Real-IP',  # nginx
        'X-Forwarded-For',  # Standard proxy header
    ]

    for header in forwarded_headers:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, get the first (client)
            return ip.split(',')[0].strip()

    return get_remote_address()


def get_rate_limit_key():
    """
    Generate rate limit key based on IP and optionally user ID.
    Authenticated users get their own limit pool (prevents one user
    from blocking an entire office/NAT IP).
    """
    ip = get_client_ip()

    # Check if user is authenticated via JWT
    user_id = getattr(g, 'current_user_id', None)

    if user_id:
        return f"user:{user_id}"

    return f"ip:{ip}"


def init_limiter(app):
    """
    Initialize the rate limiter with the Flask app.

    Uses in-memory storage by default (suitable for single-instance).
    For multi-instance deployments, configure RATELIMIT_STORAGE_URL
    with Redis: redis://localhost:6379
    """
    # Get storage URL from environment (Redis for production, memory for dev)
    storage_url = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    limiter = Limiter(
        key_func=get_rate_limit_key,
        app=app,
        default_limits=[DEFAULT_LIMIT],
        storage_uri=storage_url,
        strategy="fixed-window",  # Simple and predictable
        headers_enabled=True,  # Add X-RateLimit-* headers to responses
    )

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """Return JSON error when rate limit is exceeded"""
        logger.warning(f"Rate limit exceeded: {get_client_ip()} - {request.path}")
        return jsonify({
            'error': 'Previše zahtjeva. Molimo pričekajte prije ponovnog pokušaja.',
            'error_en': 'Too many requests. Please wait before trying again.',
            'retry_after': e.description
        }), 429

    logger.info(f"Rate limiter initialized (storage: {storage_url})")

    return limiter


# ============================================================================
# DECORATOR SHORTCUTS for applying limits to routes
# ============================================================================

def limit_search(limiter):
    """Decorator for search endpoints"""
    return limiter.limit(SEARCH_LIMIT)


def limit_products(limiter):
    """Decorator for product endpoints"""
    return limiter.limit(PRODUCTS_LIMIT)


def limit_auth(limiter):
    """Decorator for authentication endpoints"""
    return limiter.limit(AUTH_LIMIT)


def limit_upload(limiter):
    """Decorator for file upload endpoints"""
    return limiter.limit(UPLOAD_LIMIT)


def limit_cart(limiter):
    """Decorator for cart endpoints"""
    return limiter.limit(CART_LIMIT)


def limit_admin(limiter):
    """Decorator for admin endpoints"""
    return limiter.limit(ADMIN_LIMIT)


# ============================================================================
# WHITELIST FUNCTIONALITY (optional - for trusted IPs)
# ============================================================================

# IPs that bypass rate limiting (e.g., monitoring services, load balancers)
WHITELIST_IPS = set(
    os.environ.get('RATELIMIT_WHITELIST', '').split(',')
) - {''}  # Remove empty strings


def is_whitelisted():
    """Check if current request IP is whitelisted"""
    return get_client_ip() in WHITELIST_IPS
