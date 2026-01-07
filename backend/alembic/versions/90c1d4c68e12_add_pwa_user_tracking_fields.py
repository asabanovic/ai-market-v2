"""Add PWA user tracking fields

Revision ID: 90c1d4c68e12
Revises: 89693b91f0cf
Create Date: 2026-01-07 23:19:30.548510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90c1d4c68e12'
down_revision: Union[str, None] = '89693b91f0cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add PWA tracking fields to users table
    # Add as nullable first, then set defaults, then make NOT NULL
    op.add_column('users', sa.Column('is_pwa_user', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('last_pwa_access', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('pwa_access_count', sa.Integer(), nullable=True))

    # Set default values for existing rows
    op.execute("UPDATE users SET is_pwa_user = FALSE WHERE is_pwa_user IS NULL")
    op.execute("UPDATE users SET pwa_access_count = 0 WHERE pwa_access_count IS NULL")

    # Now make columns NOT NULL
    op.alter_column('users', 'is_pwa_user', nullable=False)
    op.alter_column('users', 'pwa_access_count', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'pwa_access_count')
    op.drop_column('users', 'last_pwa_access')
    op.drop_column('users', 'is_pwa_user')
