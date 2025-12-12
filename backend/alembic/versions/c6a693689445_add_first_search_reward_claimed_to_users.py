"""Add first_search_reward_claimed to users

Revision ID: c6a693689445
Revises: 3701202b8202
Create Date: 2025-12-12 13:45:01.423371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6a693689445'
down_revision: Union[str, None] = '3701202b8202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add first_search_reward_claimed column with server_default for existing rows
    op.add_column('users', sa.Column('first_search_reward_claimed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'first_search_reward_claimed')
