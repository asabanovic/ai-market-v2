"""Add receipts and receipt_items tables

Revision ID: dbd1b1b035d4
Revises: 5e8b994d5c59
Create Date: 2026-01-24 20:23:33.989162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dbd1b1b035d4'
down_revision: Union[str, None] = '5e8b994d5c59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create receipts table
    op.create_table('receipts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(length=50), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('receipt_image_url', sa.String(length=500), nullable=False),
    sa.Column('store_name', sa.String(length=255), nullable=True),
    sa.Column('store_address', sa.String(length=500), nullable=True),
    sa.Column('jib', sa.String(length=50), nullable=True),
    sa.Column('pib', sa.String(length=50), nullable=True),
    sa.Column('ibfm', sa.String(length=100), nullable=True),
    sa.Column('receipt_serial_number', sa.String(length=100), nullable=True),
    sa.Column('receipt_date', sa.DateTime(), nullable=True),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('processing_status', sa.String(length=20), nullable=False),
    sa.Column('processing_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('processed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_receipt_duplicate_check', 'receipts', ['user_id', 'jib', 'receipt_serial_number', 'receipt_date'], unique=False)
    op.create_index(op.f('ix_receipts_business_id'), 'receipts', ['business_id'], unique=False)
    op.create_index(op.f('ix_receipts_created_at'), 'receipts', ['created_at'], unique=False)
    op.create_index(op.f('ix_receipts_ibfm'), 'receipts', ['ibfm'], unique=False)
    op.create_index(op.f('ix_receipts_jib'), 'receipts', ['jib'], unique=False)
    op.create_index(op.f('ix_receipts_pib'), 'receipts', ['pib'], unique=False)
    op.create_index(op.f('ix_receipts_processing_status'), 'receipts', ['processing_status'], unique=False)
    op.create_index(op.f('ix_receipts_receipt_date'), 'receipts', ['receipt_date'], unique=False)
    op.create_index(op.f('ix_receipts_receipt_serial_number'), 'receipts', ['receipt_serial_number'], unique=False)
    op.create_index(op.f('ix_receipts_user_id'), 'receipts', ['user_id'], unique=False)

    # Create receipt_items table
    op.create_table('receipt_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('receipt_id', sa.Integer(), nullable=False),
    sa.Column('raw_name', sa.Text(), nullable=False),
    sa.Column('parsed_name', sa.String(length=255), nullable=True),
    sa.Column('brand', sa.String(length=100), nullable=True),
    sa.Column('product_type', sa.String(length=100), nullable=True),
    sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('pack_size', sa.String(length=50), nullable=True),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('line_total', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('size_value', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('size_unit', sa.String(length=10), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['receipt_id'], ['receipts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receipt_items_receipt_id'), 'receipt_items', ['receipt_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_receipt_items_receipt_id'), table_name='receipt_items')
    op.drop_table('receipt_items')
    op.drop_index(op.f('ix_receipts_user_id'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_receipt_serial_number'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_receipt_date'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_processing_status'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_pib'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_jib'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_ibfm'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_created_at'), table_name='receipts')
    op.drop_index(op.f('ix_receipts_business_id'), table_name='receipts')
    op.drop_index('ix_receipt_duplicate_check', table_name='receipts')
    op.drop_table('receipts')
