"""add_shopping_list_history_and_price_tracking

Revision ID: 144e87ad4d89
Revises: 7f3a9b2c4d5e
Create Date: 2025-11-18 18:45:58.811630

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '144e87ad4d89'
down_revision: Union[str, None] = '7f3a9b2c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Check if product_price_history table exists
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name='product_price_history'
    """))

    if not result.fetchone():
        # Create product price history table
        op.create_table('product_price_history',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('base_price', sa.Float(), nullable=False),
            sa.Column('discount_price', sa.Float(), nullable=True),
            sa.Column('recorded_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_price_history_product_id', 'product_price_history', ['product_id'], unique=False)
        op.create_index('idx_price_history_recorded_at', 'product_price_history', ['recorded_at'], unique=False)

    # Check if purchased_at column exists in shopping_list_items
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='shopping_list_items' AND column_name='purchased_at'
    """))
    if not result.fetchone():
        op.add_column('shopping_list_items', sa.Column('purchased_at', sa.DateTime(), nullable=True))
        op.create_index('idx_shopping_list_items_purchased', 'shopping_list_items', ['purchased_at'], unique=False)

    # Check if completed_at column exists in shopping_lists
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='shopping_lists' AND column_name='completed_at'
    """))
    if not result.fetchone():
        op.add_column('shopping_lists', sa.Column('completed_at', sa.DateTime(), nullable=True))
        op.create_index('idx_shopping_lists_completed', 'shopping_lists', ['completed_at'], unique=False)


def downgrade() -> None:
    # Remove indexes and columns from shopping_lists
    op.drop_index('idx_shopping_lists_completed', table_name='shopping_lists')
    op.drop_column('shopping_lists', 'completed_at')

    # Remove indexes and columns from shopping_list_items
    op.drop_index('idx_shopping_list_items_purchased', table_name='shopping_list_items')
    op.drop_column('shopping_list_items', 'purchased_at')

    # Drop product price history table
    op.drop_index('idx_price_history_recorded_at', table_name='product_price_history')
    op.drop_index('idx_price_history_product_id', table_name='product_price_history')
    op.drop_table('product_price_history')
