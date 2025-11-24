"""weekly_credits_and_referrals

Revision ID: 7f576724347d
Revises: 1323a07a04e1
Create Date: 2025-11-23 23:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f576724347d'
down_revision: Union[str, None] = '1323a07a04e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new weekly credits columns
    op.add_column('users', sa.Column('weekly_credits', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('weekly_credits_used', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('weekly_credits_reset_date', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('extra_credits', sa.Integer(), nullable=True))

    # Add referral columns
    op.add_column('users', sa.Column('referral_code', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('referred_by_code', sa.String(20), nullable=True))

    # Migrate existing daily credits to weekly credits
    op.execute("""
        UPDATE users
        SET weekly_credits = COALESCE(daily_credits, 10),
            weekly_credits_used = COALESCE(daily_credits_used, 0),
            weekly_credits_reset_date = COALESCE(daily_credits_reset_date, CURRENT_DATE),
            extra_credits = 0
        WHERE weekly_credits IS NULL
    """)

    # Set defaults for new columns
    op.alter_column('users', 'weekly_credits', nullable=False, server_default='10')
    op.alter_column('users', 'weekly_credits_used', nullable=False, server_default='0')
    op.alter_column('users', 'weekly_credits_reset_date', nullable=False, server_default=sa.func.current_date())
    op.alter_column('users', 'extra_credits', nullable=False, server_default='0')

    # Create unique constraint for referral_code
    op.create_unique_constraint('uq_users_referral_code', 'users', ['referral_code'])

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('referrer_code', sa.String(20), nullable=False),
        sa.Column('referred_user_id', sa.String(), nullable=False),
        sa.Column('credits_awarded', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['referrer_code'], ['users.referral_code']),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'])
    )
    op.create_index('idx_referrals_referrer_code', 'referrals', ['referrer_code'])
    op.create_index('idx_referrals_referred_user', 'referrals', ['referred_user_id'])

    # Set defaults
    op.execute("UPDATE referrals SET credits_awarded = 100 WHERE credits_awarded IS NULL")
    op.alter_column('referrals', 'credits_awarded', nullable=False, server_default='100')


def downgrade() -> None:
    # Drop referrals table
    op.drop_index('idx_referrals_referred_user', 'referrals')
    op.drop_index('idx_referrals_referrer_code', 'referrals')
    op.drop_table('referrals')

    # Drop referral columns from users
    op.drop_constraint('uq_users_referral_code', 'users', type_='unique')
    op.drop_column('users', 'referred_by_code')
    op.drop_column('users', 'referral_code')

    # Drop weekly credits columns
    op.drop_column('users', 'extra_credits')
    op.drop_column('users', 'weekly_credits_reset_date')
    op.drop_column('users', 'weekly_credits_used')
    op.drop_column('users', 'weekly_credits')
