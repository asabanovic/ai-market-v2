"""Add first touch attribution fields to users

Revision ID: a8f3c7d2e1b9
Revises: 6632138fff92
Create Date: 2026-01-01 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8f3c7d2e1b9'
down_revision: Union[str, None] = '6632138fff92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add first-touch attribution columns to users table
    op.add_column('users', sa.Column('first_touch_source', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('first_touch_medium', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('first_touch_campaign', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('first_touch_fbclid', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('first_touch_timestamp', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('first_touch_landing_page', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('first_touch_referrer', sa.String(500), nullable=True))

    # Create index on source for analytics queries
    op.create_index('idx_users_first_touch_source', 'users', ['first_touch_source'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_users_first_touch_source', table_name='users')
    op.drop_column('users', 'first_touch_referrer')
    op.drop_column('users', 'first_touch_landing_page')
    op.drop_column('users', 'first_touch_timestamp')
    op.drop_column('users', 'first_touch_fbclid')
    op.drop_column('users', 'first_touch_campaign')
    op.drop_column('users', 'first_touch_medium')
    op.drop_column('users', 'first_touch_source')
