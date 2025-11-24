"""add_custom_referral_codes

Revision ID: 909352703cce
Revises: 7f576724347d
Create Date: 2025-11-23 23:29:03.517673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '909352703cce'
down_revision: Union[str, None] = '7f576724347d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add custom_referral_code column
    op.add_column('users', sa.Column('custom_referral_code', sa.String(50), nullable=True))

    # Create unique constraint for custom codes
    op.create_unique_constraint('uq_users_custom_referral_code', 'users', ['custom_referral_code'])

    # Create index for faster lookups
    op.create_index('idx_users_custom_referral_code', 'users', ['custom_referral_code'])


def downgrade() -> None:
    # Drop index and constraint
    op.drop_index('idx_users_custom_referral_code', 'users')
    op.drop_constraint('uq_users_custom_referral_code', 'users', type_='unique')

    # Drop column
    op.drop_column('users', 'custom_referral_code')
