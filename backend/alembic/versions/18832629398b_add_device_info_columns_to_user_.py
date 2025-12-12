"""Add device info columns to user_searches table

Revision ID: 18832629398b
Revises: 31ea1132e7f2
Create Date: 2025-12-11 19:10:29.764926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18832629398b'
down_revision: Union[str, None] = '31ea1132e7f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add device info columns to user_searches table
    op.add_column('user_searches', sa.Column('user_agent', sa.String(length=500), nullable=True))
    op.add_column('user_searches', sa.Column('device_type', sa.String(length=50), nullable=True))
    op.add_column('user_searches', sa.Column('browser', sa.String(length=100), nullable=True))
    op.add_column('user_searches', sa.Column('os', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('user_searches', 'os')
    op.drop_column('user_searches', 'browser')
    op.drop_column('user_searches', 'device_type')
    op.drop_column('user_searches', 'user_agent')
