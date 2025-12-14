"""Add feedback_bonuses_claimed and lifetime_credits_spent to users

Revision ID: 036c24c43da0
Revises: c6a693689445
Create Date: 2025-12-14 18:24:14.003508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '036c24c43da0'
down_revision: Union[str, None] = 'c6a693689445'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add feedback_bonuses_claimed column with default 0
    op.add_column('users', sa.Column('feedback_bonuses_claimed', sa.Integer(), nullable=False, server_default='0'))
    # Add lifetime_credits_spent column with default 0
    op.add_column('users', sa.Column('lifetime_credits_spent', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'lifetime_credits_spent')
    op.drop_column('users', 'feedback_bonuses_claimed')
