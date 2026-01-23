"""Add product_submissions table and contributor tracking

Revision ID: 5e8b994d5c59
Revises: 302c68bf1f95
Create Date: 2026-01-22 22:24:52.331302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e8b994d5c59'
down_revision: Union[str, None] = '302c68bf1f95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create product_submissions table
    op.create_table(
        'product_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(50), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # pending, processing, approved, rejected, duplicate

        # AI-extracted fields (populated after processing)
        sa.Column('extracted_title', sa.String(255), nullable=True),
        sa.Column('extracted_old_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('extracted_new_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('extracted_discount_percent', sa.Integer(), nullable=True),
        sa.Column('extracted_valid_until', sa.Date(), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),

        # Duplicate detection
        sa.Column('potential_duplicate_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('duplicate_similarity', sa.Float(), nullable=True),

        # Admin review
        sa.Column('reviewed_by', sa.String(50), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(255), nullable=True),

        # Result tracking
        sa.Column('resulting_product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='SET NULL'), nullable=True),
        sa.Column('credits_awarded', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes for common queries
    op.create_index('ix_product_submissions_user_id', 'product_submissions', ['user_id'])
    op.create_index('ix_product_submissions_business_id', 'product_submissions', ['business_id'])
    op.create_index('ix_product_submissions_status', 'product_submissions', ['status'])
    op.create_index('ix_product_submissions_created_at', 'product_submissions', ['created_at'])

    # Add contributed_by field to products table (links to user who submitted)
    op.add_column('products', sa.Column('contributed_by', sa.String(50), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_products_contributed_by', 'products', ['contributed_by'])

    # Add feedback tracking fields to users table
    op.add_column('users', sa.Column('feedback_submitted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('last_feedback_prompt_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove feedback tracking fields from users
    op.drop_column('users', 'last_feedback_prompt_at')
    op.drop_column('users', 'feedback_submitted_at')

    # Remove contributed_by from products
    op.drop_index('ix_products_contributed_by', table_name='products')
    op.drop_column('products', 'contributed_by')

    # Drop product_submissions table
    op.drop_index('ix_product_submissions_created_at', table_name='product_submissions')
    op.drop_index('ix_product_submissions_status', table_name='product_submissions')
    op.drop_index('ix_product_submissions_business_id', table_name='product_submissions')
    op.drop_index('ix_product_submissions_user_id', table_name='product_submissions')
    op.drop_table('product_submissions')
