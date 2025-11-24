"""add_anonymous_searches_table

Revision ID: dd6d2044bc58
Revises: 54ddaa720251
Create Date: 2025-11-24 01:44:03.363596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd6d2044bc58'
down_revision: Union[str, None] = '54ddaa720251'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create anonymous_searches table
    op.create_table(
        'anonymous_searches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_anonymous_searches_ip', 'anonymous_searches', ['ip_address'])
    op.create_index('idx_anonymous_searches_created_at', 'anonymous_searches', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_anonymous_searches_created_at', table_name='anonymous_searches')
    op.drop_index('idx_anonymous_searches_ip', table_name='anonymous_searches')

    # Drop table
    op.drop_table('anonymous_searches')
