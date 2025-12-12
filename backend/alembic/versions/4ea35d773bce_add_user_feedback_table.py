"""Add user_feedback table

Revision ID: 4ea35d773bce
Revises: 18832629398b
Create Date: 2025-12-12 02:56:23.822757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ea35d773bce'
down_revision: Union[str, None] = '18832629398b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_feedback',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('anonymous_id', sa.String(length=100), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('what_to_improve', sa.Text(), nullable=True),
    sa.Column('how_to_help', sa.Text(), nullable=True),
    sa.Column('what_would_make_you_use', sa.Text(), nullable=True),
    sa.Column('comments', sa.Text(), nullable=True),
    sa.Column('trigger_type', sa.String(length=50), nullable=True),
    sa.Column('page_url', sa.String(length=500), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('device_type', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_feedback_created_at', 'user_feedback', ['created_at'], unique=False)
    op.create_index('idx_user_feedback_trigger', 'user_feedback', ['trigger_type'], unique=False)
    op.create_index('idx_user_feedback_user_id', 'user_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_user_feedback_user_id', table_name='user_feedback')
    op.drop_index('idx_user_feedback_trigger', table_name='user_feedback')
    op.drop_index('idx_user_feedback_created_at', table_name='user_feedback')
    op.drop_table('user_feedback')
