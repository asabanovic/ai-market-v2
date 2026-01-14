"""Add discount_starts column to products table

Revision ID: e6f7g8h9i0j1
Revises: d5f9e2a3b4c6
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e6f7g8h9i0j1'
down_revision = 'd5f9e2a3b4c6'
branch_labels = None
depends_on = None


def upgrade():
    # Add discount_starts column to products table
    # NULL means discount is immediately active (existing behavior)
    op.add_column('products', sa.Column('discount_starts', sa.Date(), nullable=True))

    # Create index for efficient filtering by discount_starts
    op.create_index('idx_products_discount_starts', 'products', ['discount_starts'], unique=False)


def downgrade():
    # Drop index
    op.drop_index('idx_products_discount_starts', table_name='products')

    # Drop column
    op.drop_column('products', 'discount_starts')
