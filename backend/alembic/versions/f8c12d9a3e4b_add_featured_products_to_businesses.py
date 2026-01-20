"""Add featured_products to businesses

Revision ID: f8c12d9a3e4b
Revises: e9932b8e83a7
Create Date: 2026-01-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8c12d9a3e4b'
down_revision: Union[str, None] = 'e9932b8e83a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('businesses', sa.Column('featured_products', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('businesses', 'featured_products')
