"""
Weekly Credits Service with Two-Bucket System
Handles regular credits (reset weekly) and extra credits (accumulate)
"""
from datetime import datetime, date, timedelta
from app import db
from models import User, CreditTransaction, Referral
import logging
import secrets
import string
import os

logger = logging.getLogger(__name__)

# Credit amounts - configurable via environment variables
ADMIN_WEEKLY_CREDITS = int(os.environ.get('ADMIN_WEEKLY_CREDITS', 100000))
REGULAR_USER_WEEKLY_CREDITS = int(os.environ.get('REGULAR_USER_WEEKLY_CREDITS', 10))
REFERRAL_BONUS_CREDITS = 100


def generate_referral_code(user_id: str) -> str:
    """
    Generate a unique referral code for a user

    Format: First 3 chars of user_id + 5 random alphanumeric chars
    Example: 175ABC123
    """
    # Use first 3 chars of user_id (or pad if shorter)
    prefix = str(user_id)[:3].upper().ljust(3, 'X')

    # Generate 5 random alphanumeric characters
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(5))

    code = f"{prefix}{suffix}"

    # Ensure uniqueness
    existing = User.query.filter_by(referral_code=code).first()
    if existing:
        # Rare collision, try again
        return generate_referral_code(user_id)

    return code


def generate_custom_referral_code(user_id: str, user_data: dict = None) -> str:
    """
    Auto-generate a custom referral code based on user info

    Priority:
    1. First name (if available)
    2. Email username (if available)
    3. Random words

    Format: lowercase, alphanumeric + hyphens
    Example: "adnan123", "user-abc", "friend789"
    """
    base_code = None

    # Try first name
    if user_data and user_data.get('first_name'):
        first_name = user_data['first_name'].lower().strip()
        # Remove non-alphanumeric except hyphens
        base_code = ''.join(c for c in first_name if c.isalnum() or c == '-')

    # Try email username
    elif user_data and user_data.get('email'):
        email_username = user_data['email'].split('@')[0].lower().strip()
        base_code = ''.join(c for c in email_username if c.isalnum() or c == '-')

    # Fallback to random
    if not base_code:
        base_code = 'user'

    # Ensure it's at least 3 chars
    if len(base_code) < 3:
        base_code = base_code + 'user'

    # Add random suffix for uniqueness
    chars = string.ascii_lowercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(3))

    code = f"{base_code}{suffix}"[:20]  # Max 20 chars

    # Ensure uniqueness
    existing = User.query.filter(
        (User.custom_referral_code == code) | (User.referral_code == code.upper())
    ).first()

    if existing:
        # Try with longer suffix
        suffix = ''.join(secrets.choice(chars) for _ in range(4))
        code = f"{base_code}{suffix}"[:20]

    return code


def get_next_monday() -> date:
    """Get the date of next Monday (when credits reset)"""
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # If today is Monday, next reset is in 7 days
    return today + timedelta(days=days_until_monday)


class WeeklyCreditsService:
    """Service for managing weekly credits with two-bucket system"""

    @staticmethod
    def get_balance(user_id: str, auto_reset_weekly: bool = True) -> dict:
        """
        Get the current credit balance for a user with two buckets

        Args:
            user_id: User ID
            auto_reset_weekly: If True, automatically reset regular credits weekly

        Returns:
            dict with 'regular_credits', 'extra_credits', 'total_credits', 'next_reset_date'
        """
        user = User.query.get(user_id)
        if not user:
            return {
                'regular_credits': 0,
                'extra_credits': 0,
                'total_credits': 0,
                'next_reset_date': get_next_monday()
            }

        # Check if user is admin
        is_admin = user.is_admin
        weekly_credits_max = ADMIN_WEEKLY_CREDITS if is_admin else REGULAR_USER_WEEKLY_CREDITS

        # For admins, always ensure they have maximum credits
        # This handles the case where an admin was created before the credits were set up
        if is_admin and (user.weekly_credits < weekly_credits_max):
            logger.info(f"Auto-upgrading admin credits for user {user_id}: {user.weekly_credits} -> {weekly_credits_max}")
            user.weekly_credits = weekly_credits_max
            user.weekly_credits_used = 0
            user.weekly_credits_reset_date = date.today()
            db.session.commit()

        # Check if we need to reset weekly credits
        if auto_reset_weekly:
            today = date.today()
            last_reset_date = user.weekly_credits_reset_date or today

            # Reset on Monday (weekday 0)
            if today.weekday() == 0 and last_reset_date < today:
                logger.info(f"Weekly credit reset for user {user_id} (admin={is_admin})")
                WeeklyCreditsService._perform_weekly_reset(user_id, weekly_credits_max)
                user = User.query.get(user_id)  # Refresh

        # Calculate available regular credits
        regular_credits_available = max(0, user.weekly_credits - user.weekly_credits_used)

        return {
            'regular_credits': regular_credits_available,
            'extra_credits': user.extra_credits or 0,
            'total_credits': regular_credits_available + (user.extra_credits or 0),
            'next_reset_date': get_next_monday()
        }

    @staticmethod
    def _perform_weekly_reset(user_id: str, weekly_credits_max: int) -> None:
        """
        Internal method to perform weekly credit reset

        Args:
            user_id: User ID
            weekly_credits_max: Maximum weekly credits (10 for users, 100000 for admins)
        """
        user = User.query.get(user_id)
        if not user:
            return

        # Reset regular credits to max (overwrite, don't accumulate)
        old_weekly_used = user.weekly_credits_used
        user.weekly_credits = weekly_credits_max
        user.weekly_credits_used = 0
        user.weekly_credits_reset_date = date.today()

        db.session.commit()

        logger.info(f"Weekly reset for user {user_id}: Set to {weekly_credits_max} regular credits (was {old_weekly_used}/{user.weekly_credits})")

    @staticmethod
    def deduct_credits(user_id: str, amount: int, action: str, metadata: dict = None) -> dict:
        """
        Deduct credits from user balance (extra credits first, then regular)

        Args:
            user_id: User ID
            amount: Number of credits to deduct
            action: Action name
            metadata: Optional metadata

        Returns:
            dict with balance info

        Raises:
            InsufficientCreditsError: If not enough credits
        """
        balance = WeeklyCreditsService.get_balance(user_id)

        if balance['total_credits'] < amount:
            from credits_service import InsufficientCreditsError
            raise InsufficientCreditsError(amount, balance['total_credits'])

        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Use extra credits first, then regular credits
        extra_used = min(amount, user.extra_credits or 0)
        regular_used = amount - extra_used

        user.extra_credits = (user.extra_credits or 0) - extra_used
        user.weekly_credits_used += regular_used

        db.session.commit()

        logger.info(f"Deducted {amount} credits from user {user_id}: {extra_used} extra + {regular_used} regular")

        new_balance = WeeklyCreditsService.get_balance(user_id, auto_reset_weekly=False)

        return {
            'balance': new_balance['total_credits'],
            'regular_credits': new_balance['regular_credits'],
            'extra_credits': new_balance['extra_credits'],
            'deducted': amount
        }

    @staticmethod
    def add_extra_credits(user_id: str, amount: int, action: str = 'REFERRAL_BONUS', metadata: dict = None) -> dict:
        """
        Add extra credits (these accumulate, never reset)

        Args:
            user_id: User ID
            amount: Number of credits to add
            action: Action name (e.g., 'REFERRAL_BONUS', 'PURCHASE')
            metadata: Optional metadata

        Returns:
            dict with balance info
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.extra_credits = (user.extra_credits or 0) + amount
        db.session.commit()

        logger.info(f"Added {amount} extra credits to user {user_id} for {action}. New extra credits: {user.extra_credits}")

        balance = WeeklyCreditsService.get_balance(user_id, auto_reset_weekly=False)

        return {
            'balance': balance['total_credits'],
            'regular_credits': balance['regular_credits'],
            'extra_credits': balance['extra_credits'],
            'added': amount
        }

    @staticmethod
    def award_referral_bonus(referrer_code: str, referred_user_id: str) -> dict:
        """
        Award referral bonus to the referrer

        Args:
            referrer_code: Referral code of the person who referred
            referred_user_id: ID of the newly registered user

        Returns:
            dict with success status and credits awarded
        """
        # Find referrer by code - check both auto-generated and custom codes
        referrer = User.query.filter(
            (User.referral_code == referrer_code.upper()) |
            (User.custom_referral_code == referrer_code.lower())
        ).first()
        if not referrer:
            logger.warning(f"Referral code {referrer_code} not found")
            return {'success': False, 'error': 'Invalid referral code'}

        # Check if referral already exists
        existing = Referral.query.filter_by(referred_user_id=referred_user_id).first()
        if existing:
            logger.warning(f"User {referred_user_id} already has a referral record")
            return {'success': False, 'error': 'Already referred'}

        # Create referral record
        referral = Referral(
            referrer_code=referrer_code,
            referred_user_id=referred_user_id,
            credits_awarded=REFERRAL_BONUS_CREDITS
        )
        db.session.add(referral)

        # Add bonus credits to referrer
        referrer.extra_credits = (referrer.extra_credits or 0) + REFERRAL_BONUS_CREDITS

        db.session.commit()

        logger.info(f"Awarded {REFERRAL_BONUS_CREDITS} credits to {referrer.id} for referring {referred_user_id}")

        return {
            'success': True,
            'credits_awarded': REFERRAL_BONUS_CREDITS,
            'referrer_id': referrer.id
        }

    @staticmethod
    def initialize_user_credits(user_id: str) -> dict:
        """
        Initialize credits for a new user and generate referral code

        Args:
            user_id: User ID

        Returns:
            dict with initial balance and referral code
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Check if user is admin
        is_admin = user.is_admin
        initial_credits = ADMIN_WEEKLY_CREDITS if is_admin else REGULAR_USER_WEEKLY_CREDITS

        # Set initial credits
        user.weekly_credits = initial_credits
        user.weekly_credits_used = 0
        user.weekly_credits_reset_date = date.today()
        user.extra_credits = 0

        # Generate referral code if not exists
        if not user.referral_code:
            user.referral_code = generate_referral_code(user_id)

        # Auto-generate custom referral code if not exists
        if not user.custom_referral_code:
            user_data = {
                'first_name': user.first_name,
                'email': user.email
            }
            user.custom_referral_code = generate_custom_referral_code(user_id, user_data)

        db.session.commit()

        logger.info(f"Initialized user {user_id} with {initial_credits} weekly credits, referral code {user.referral_code}, and custom code {user.custom_referral_code}")

        balance = WeeklyCreditsService.get_balance(user_id, auto_reset_weekly=False)

        return {
            'balance': balance['total_credits'],
            'regular_credits': balance['regular_credits'],
            'extra_credits': balance['extra_credits'],
            'referral_code': user.referral_code,
            'next_reset_date': balance['next_reset_date']
        }

    @staticmethod
    def get_referrals(referral_code: str) -> list:
        """
        Get all referrals for a given referral code

        Args:
            referral_code: Referral code to lookup

        Returns:
            List of referral dicts with user info
        """
        referrals = Referral.query.filter_by(referrer_code=referral_code).order_by(Referral.created_at.desc()).all()

        return [{
            'id': r.id,
            'referred_user_id': r.referred_user_id,
            'referred_user_email': r.referred_user.email if r.referred_user else None,
            'referred_user_phone': r.referred_user.phone if r.referred_user else None,
            'credits_awarded': r.credits_awarded,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in referrals]
