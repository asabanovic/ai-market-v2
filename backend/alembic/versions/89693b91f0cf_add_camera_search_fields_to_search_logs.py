"""Add camera search fields to search_logs

Revision ID: 89693b91f0cf
Revises: c4e8f9a1b2d3
Create Date: 2026-01-07 18:46:40.985012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89693b91f0cf'
down_revision: Union[str, None] = 'c4e8f9a1b2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add camera search tracking fields to search_logs
    op.add_column('search_logs', sa.Column('search_type', sa.String(length=20), nullable=True))
    op.add_column('search_logs', sa.Column('image_path', sa.String(length=500), nullable=True))
    op.add_column('search_logs', sa.Column('vision_result', sa.JSON(), nullable=True))
    op.create_index('idx_search_logs_search_type', 'search_logs', ['search_type'], unique=False)

    # Set default value for existing rows
    op.execute("UPDATE search_logs SET search_type = 'text' WHERE search_type IS NULL")


def downgrade() -> None:
    op.drop_index('idx_search_logs_search_type', table_name='search_logs')
    op.drop_column('search_logs', 'vision_result')
    op.drop_column('search_logs', 'image_path')
    op.drop_column('search_logs', 'search_type')
