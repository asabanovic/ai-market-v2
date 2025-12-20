"""
Monthly Credits Service with Two-Bucket System
Handles regular credits (reset monthly) and extra credits (accumulate)
"""
from datetime import datetime, date, timedelta
from calendar import monthrange
from app import db
from models import User, CreditTransaction, Referral
import logging
import secrets
import string
import os

logger = logging.getLogger(__name__)

# Credit amounts - configurable via environment variables
ADMIN_MONTHLY_CREDITS = int(os.environ.get('ADMIN_MONTHLY_CREDITS', 100000))
REGULAR_USER_MONTHLY_CREDITS = int(os.environ.get('REGULAR_USER_MONTHLY_CREDITS', 40))
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


def get_next_month_first() -> date:
    """Get the date of first day of next month (when credits reset)"""
    today = date.today()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    else:
        return date(today.year, today.month + 1, 1)


def is_new_month(last_reset_date: date) -> bool:
    """Check if we're in a new month compared to the last reset date"""
    today = date.today()
    if last_reset_date is None:
        return True
    # New month if current month/year is different from last reset
    return today.year > last_reset_date.year or (
        today.year == last_reset_date.year and today.month > last_reset_date.month
    )


class MonthlyCreditsService:
    """Service for managing monthly credits with two-bucket system"""

    @staticmethod
    def get_balance(user_id: str, auto_reset_monthly: bool = True) -> dict:
        """
        Get the current credit balance for a user with two buckets

        Args:
            user_id: User ID
            auto_reset_monthly: If True, automatically reset regular credits monthly

        Returns:
            dict with 'regular_credits', 'extra_credits', 'total_credits', 'next_reset_date'
        """
        user = User.query.get(user_id)
        if not user:
            return {
                'regular_credits': 0,
                'extra_credits': 0,
                'total_credits': 0,
                'next_reset_date': get_next_month_first()
            }

        # Check if user is admin
        is_admin = user.is_admin
        monthly_credits_max = ADMIN_MONTHLY_CREDITS if is_admin else REGULAR_USER_MONTHLY_CREDITS

        # For admins, always ensure they have maximum credits
        if is_admin and (user.monthly_credits or 0) < monthly_credits_max:
            logger.info(f"Auto-upgrading admin credits for user {user_id}: {user.monthly_credits} -> {monthly_credits_max}")
            user.monthly_credits = monthly_credits_max
            user.monthly_credits_used = 0
            user.monthly_credits_reset_date = date.today()
            db.session.commit()

        # Check if we need to reset monthly credits
        if auto_reset_monthly:
            last_reset_date = user.monthly_credits_reset_date

            if is_new_month(last_reset_date):
                logger.info(f"Monthly credit reset for user {user_id} (admin={is_admin})")
                MonthlyCreditsService._perform_monthly_reset(user_id, monthly_credits_max)
                user = User.query.get(user_id)  # Refresh

        # Calculate available regular credits
        monthly_credits = user.monthly_credits or 0
        monthly_credits_used = user.monthly_credits_used or 0
        regular_credits_available = max(0, monthly_credits - monthly_credits_used)

        return {
            'regular_credits': regular_credits_available,
            'extra_credits': user.extra_credits or 0,
            'total_credits': regular_credits_available + (user.extra_credits or 0),
            'next_reset_date': get_next_month_first(),
            'monthly_limit': monthly_credits_max,
            'is_unlimited': is_admin
        }

    @staticmethod
    def _perform_monthly_reset(user_id: str, monthly_credits_max: int) -> None:
        """
        Internal method to perform monthly credit reset

        Args:
            user_id: User ID
            monthly_credits_max: Maximum monthly credits (40 for users, 100000 for admins)
        """
        user = User.query.get(user_id)
        if not user:
            return

        # Reset regular credits to max (overwrite, don't accumulate)
        old_monthly_used = user.monthly_credits_used or 0
        user.monthly_credits = monthly_credits_max
        user.monthly_credits_used = 0
        user.monthly_credits_reset_date = date.today()

        db.session.commit()

        logger.info(f"Monthly reset for user {user_id}: Set to {monthly_credits_max} regular credits (was {old_monthly_used} used)")

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
        balance = MonthlyCreditsService.get_balance(user_id)

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
        user.monthly_credits_used = (user.monthly_credits_used or 0) + regular_used

        # Track lifetime credits spent (for feedback bonus eligibility)
        user.lifetime_credits_spent = (user.lifetime_credits_spent or 0) + amount

        db.session.commit()

        logger.info(f"Deducted {amount} credits from user {user_id}: {extra_used} extra + {regular_used} regular (lifetime spent: {user.lifetime_credits_spent})")

        new_balance = MonthlyCreditsService.get_balance(user_id, auto_reset_monthly=False)

        return {
            'balance': new_balance['total_credits'],
            'regular_credits': new_balance['regular_credits'],
            'extra_credits': new_balance['extra_credits'],
            'deducted': amount
        }

    @staticmethod
    def refund_credits(user_id: str, amount: int, action: str = 'REFUND') -> dict:
        """
        Refund credits to user (add back to monthly credits first, then extra)
        Used when user removes a tracked item

        Args:
            user_id: User ID
            amount: Number of credits to refund
            action: Action name

        Returns:
            dict with balance info
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Refund to monthly_credits_used first (reduce the used amount)
        monthly_credits_used = user.monthly_credits_used or 0
        if monthly_credits_used >= amount:
            user.monthly_credits_used = monthly_credits_used - amount
        else:
            # If more than monthly_credits_used, add remainder to extra_credits
            remainder = amount - monthly_credits_used
            user.monthly_credits_used = 0
            user.extra_credits = (user.extra_credits or 0) + remainder

        db.session.commit()

        logger.info(f"Refunded {amount} credits to user {user_id}")

        new_balance = MonthlyCreditsService.get_balance(user_id, auto_reset_monthly=False)

        return {
            'balance': new_balance['total_credits'],
            'regular_credits': new_balance['regular_credits'],
            'extra_credits': new_balance['extra_credits'],
            'refunded': amount
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

        balance = MonthlyCreditsService.get_balance(user_id, auto_reset_monthly=False)

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
        initial_credits = ADMIN_MONTHLY_CREDITS if is_admin else REGULAR_USER_MONTHLY_CREDITS

        # Set initial credits (monthly)
        user.monthly_credits = initial_credits
        user.monthly_credits_used = 0
        user.monthly_credits_reset_date = date.today()
        user.extra_credits = user.extra_credits or 0

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

        logger.info(f"Initialized user {user_id} with {initial_credits} monthly credits, referral code {user.referral_code}, and custom code {user.custom_referral_code}")

        balance = MonthlyCreditsService.get_balance(user_id, auto_reset_monthly=False)

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


# Backward compatibility - alias for migration period
WeeklyCreditsService = MonthlyCreditsService
