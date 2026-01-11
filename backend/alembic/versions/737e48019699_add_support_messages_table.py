"""Add support_messages table

Revision ID: 737e48019699
Revises: 90c1d4c68e12
Create Date: 2026-01-11 19:15:09.892397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '737e48019699'
down_revision: Union[str, None] = '90c1d4c68e12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('support_messages',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('sender_type', sa.String(length=10), nullable=False),
    sa.Column('admin_user_id', sa.String(), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('feedback_id', sa.Integer(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('email_sent', sa.Boolean(), nullable=False),
    sa.Column('email_sent_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['feedback_id'], ['user_feedback.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_support_messages_created', 'support_messages', ['created_at'], unique=False)
    op.create_index('idx_support_messages_feedback', 'support_messages', ['feedback_id'], unique=False)
    op.create_index('idx_support_messages_unread', 'support_messages', ['user_id', 'is_read'], unique=False)
    op.create_index('idx_support_messages_user', 'support_messages', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_support_messages_user', table_name='support_messages')
    op.drop_index('idx_support_messages_unread', table_name='support_messages')
    op.drop_index('idx_support_messages_feedback', table_name='support_messages')
    op.drop_index('idx_support_messages_created', table_name='support_messages')
    op.drop_table('support_messages')
