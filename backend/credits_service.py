"""
Credits Service
Handles credit balance management and transaction logging for user actions
"""
from datetime import datetime, date
from app import db
from models import User, CreditTransaction
import logging

logger = logging.getLogger(__name__)

# Credit amounts
ADMIN_DAILY_CREDITS = 100000
REGULAR_USER_DAILY_CREDITS = 10


class InsufficientCreditsError(Exception):
    """Raised when user doesn't have enough credits for an operation"""
    def __init__(self, credits_needed, credits_available):
        self.credits_needed = credits_needed
        self.credits_available = credits_available
        super().__init__(f"Insufficient credits: need {credits_needed}, have {credits_available}")


class CreditsService:
    """Service for managing user credits and transactions"""

    @staticmethod
    def get_balance(user_id: str, auto_reset_daily: bool = True) -> int:
        """
        Get the current credit balance for a user, with optional daily reset

        Args:
            user_id: User ID
            auto_reset_daily: If True, automatically reset credits to appropriate daily amount

        Returns:
            Current credit balance (integer)
        """
        # Check if user is admin
        user = User.query.get(user_id)
        is_admin = user and user.is_admin
        daily_credits = ADMIN_DAILY_CREDITS if is_admin else REGULAR_USER_DAILY_CREDITS

        # Get the most recent transaction to get balance
        last_transaction = CreditTransaction.query.filter_by(
            user_id=user_id
        ).order_by(CreditTransaction.created_at.desc()).first()

        if not last_transaction:
            return 0  # No transactions = 0 credits

        current_balance = last_transaction.balance_after

        # Check if we need to reset credits for a new day
        if auto_reset_daily:
            today = date.today()
            last_transaction_date = last_transaction.created_at.date()

            # If last transaction was on a previous day, reset to daily credits
            if last_transaction_date < today:
                logger.info(f"Daily credit reset for user {user_id} (admin={is_admin}): {current_balance} -> {daily_credits}")
                CreditsService._perform_daily_reset(user_id, daily_credits)
                return daily_credits

        return current_balance

    @staticmethod
    def _perform_daily_reset(user_id: str, daily_credits: int) -> None:
        """
        Internal method to perform daily credit reset

        Args:
            user_id: User ID
            daily_credits: Amount to reset to (10 for regular users, 100000 for admins)
        """
        # Get current balance
        last_transaction = CreditTransaction.query.filter_by(
            user_id=user_id
        ).order_by(CreditTransaction.created_at.desc()).first()

        current_balance = last_transaction.balance_after if last_transaction else 0

        # Calculate delta to reach daily credits
        delta = daily_credits - current_balance

        # Create reset transaction
        transaction = CreditTransaction(
            user_id=user_id,
            delta=delta,
            balance_after=daily_credits,
            action='DAILY_RESET',
            transaction_metadata={'previous_balance': current_balance, 'reset_to': daily_credits}
        )

        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Daily reset completed for user {user_id}: {current_balance} -> {daily_credits} (delta: {delta})")

    @staticmethod
    def deduct_credits(
        user_id: str,
        amount: int,
        action: str,
        metadata: dict = None
    ) -> dict:
        """
        Deduct credits from user balance

        Args:
            user_id: User ID
            amount: Number of credits to deduct (positive integer)
            action: Action name (e.g., 'ADD_TO_CART', 'ADD_FAVORITE')
            metadata: Optional metadata dict (e.g., {'product_id': 123})

        Returns:
            dict with 'balance', 'transaction_id'

        Raises:
            InsufficientCreditsError: If user doesn't have enough credits
        """
        current_balance = CreditsService.get_balance(user_id)

        if current_balance < amount:
            raise InsufficientCreditsError(amount, current_balance)

        new_balance = current_balance - amount

        # Create transaction record
        transaction = CreditTransaction(
            user_id=user_id,
            delta=-amount,  # Negative for deduction
            balance_after=new_balance,
            action=action,
            transaction_metadata=metadata or {}
        )

        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Deducted {amount} credits from user {user_id} for {action}. New balance: {new_balance}")

        return {
            'balance': new_balance,
            'transaction_id': transaction.id,
            'deducted': amount
        }

    @staticmethod
    def add_credits(
        user_id: str,
        amount: int,
        action: str = 'TOP_UP',
        metadata: dict = None
    ) -> dict:
        """
        Add credits to user balance

        Args:
            user_id: User ID
            amount: Number of credits to add (positive integer)
            action: Action name (e.g., 'TOP_UP', 'REFUND', 'PROMO')
            metadata: Optional metadata dict

        Returns:
            dict with 'balance', 'transaction_id'
        """
        current_balance = CreditsService.get_balance(user_id)
        new_balance = current_balance + amount

        # Create transaction record
        transaction = CreditTransaction(
            user_id=user_id,
            delta=amount,  # Positive for addition
            balance_after=new_balance,
            action=action,
            transaction_metadata=metadata or {}
        )

        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Added {amount} credits to user {user_id} for {action}. New balance: {new_balance}")

        return {
            'balance': new_balance,
            'transaction_id': transaction.id,
            'added': amount
        }

    @staticmethod
    def has_sufficient_credits(user_id: str, amount: int) -> bool:
        """
        Check if user has sufficient credits

        Args:
            user_id: User ID
            amount: Number of credits needed

        Returns:
            True if user has enough credits, False otherwise
        """
        return CreditsService.get_balance(user_id) >= amount

    @staticmethod
    def record_free_transaction(
        user_id: str,
        action: str,
        metadata: dict = None
    ) -> dict:
        """
        Record a transaction that costs 0 credits (e.g., promo checkout)

        Args:
            user_id: User ID
            action: Action name (e.g., 'CHECKOUT_SMS')
            metadata: Optional metadata dict (should include promo=True)

        Returns:
            dict with 'balance', 'transaction_id'
        """
        current_balance = CreditsService.get_balance(user_id)

        # Create transaction record with delta=0
        transaction = CreditTransaction(
            user_id=user_id,
            delta=0,
            balance_after=current_balance,
            action=action,
            transaction_metadata=metadata or {}
        )

        db.session.add(transaction)
        db.session.commit()

        logger.info(f"Recorded free transaction for user {user_id}: {action}")

        return {
            'balance': current_balance,
            'transaction_id': transaction.id,
            'charged': 0
        }

    @staticmethod
    def get_transaction_history(user_id: str, limit: int = 50) -> list:
        """
        Get user's transaction history

        Args:
            user_id: User ID
            limit: Maximum number of transactions to return

        Returns:
            List of transaction dicts
        """
        transactions = CreditTransaction.query.filter_by(
            user_id=user_id
        ).order_by(CreditTransaction.created_at.desc()).limit(limit).all()

        return [
            {
                'id': t.id,
                'delta': t.delta,
                'balance_after': t.balance_after,
                'action': t.action,
                'metadata': t.transaction_metadata,
                'created_at': t.created_at.isoformat()
            }
            for t in transactions
        ]

    @staticmethod
    def initialize_user_credits(user_id: str, initial_amount: int = None) -> dict:
        """
        Initialize credits for a new user

        Args:
            user_id: User ID
            initial_amount: Starting credit amount (None = auto-detect based on admin status)

        Returns:
            dict with 'balance', 'transaction_id'
        """
        # Check if user already has transactions
        existing_balance = CreditsService.get_balance(user_id, auto_reset_daily=False)
        if existing_balance > 0:
            logger.warning(f"User {user_id} already has credits: {existing_balance}")
            return {'balance': existing_balance, 'transaction_id': None}

        # Auto-detect initial amount based on admin status
        if initial_amount is None:
            user = User.query.get(user_id)
            is_admin = user and user.is_admin
            initial_amount = ADMIN_DAILY_CREDITS if is_admin else REGULAR_USER_DAILY_CREDITS

        return CreditsService.add_credits(
            user_id=user_id,
            amount=initial_amount,
            action='INITIAL_CREDITS',
            metadata={'message': 'Welcome bonus'}
        )
