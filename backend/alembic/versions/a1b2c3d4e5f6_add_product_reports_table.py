"""add_product_reports_table

Revision ID: a1b2c3d4e5f6
Revises: cc6ff6f0bb1b
Create Date: 2025-12-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cc6ff6f0bb1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create product_reports table
    op.create_table(
        'product_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),  # Optional explanation
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),  # pending, reviewed, resolved, dismissed
        sa.Column('admin_notes', sa.Text(), nullable=True),  # Admin can add notes
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_product_reports_product_id', 'product_reports', ['product_id'])
    op.create_index('idx_product_reports_user_id', 'product_reports', ['user_id'])
    op.create_index('idx_product_reports_status', 'product_reports', ['status'])
    op.create_index('idx_product_reports_created_at', 'product_reports', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_product_reports_created_at')
    op.drop_index('idx_product_reports_status')
    op.drop_index('idx_product_reports_user_id')
    op.drop_index('idx_product_reports_product_id')
    op.drop_table('product_reports')
