"""add_notifications_table

Revision ID: 41d2c4106ed6
Revises: dd6d2044bc58
Create Date: 2025-11-24 09:19:41.647951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41d2c4106ed6'
down_revision: Union[str, None] = 'dd6d2044bc58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('notification_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('action_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_notifications_user_read', table_name='notifications')
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')

    # Drop table
    op.drop_table('notifications')
