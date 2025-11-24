"""add_product_engagement_tables

Revision ID: 54ddaa720251
Revises: 432f3f76bd81
Create Date: 2025-11-24 01:07:27.092968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54ddaa720251'
down_revision: Union[str, None] = '432f3f76bd81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create product_comments table
    op.create_table(
        'product_comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_product_comments_product_id', 'product_comments', ['product_id'])
    op.create_index('idx_product_comments_user_id', 'product_comments', ['user_id'])
    op.create_index('idx_product_comments_created_at', 'product_comments', ['created_at'])

    # Create product_votes table
    op.create_table(
        'product_votes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('vote_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'user_id', name='uq_product_user_vote')
    )
    op.create_index('idx_product_votes_product_id', 'product_votes', ['product_id'])
    op.create_index('idx_product_votes_user_id', 'product_votes', ['user_id'])

    # Create user_engagements table
    op.create_table(
        'user_engagements',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('activity_type', sa.String(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('credits_earned', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_engagements_user_id', 'user_engagements', ['user_id'])
    op.create_index('idx_user_engagements_created_at', 'user_engagements', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_user_engagements_created_at', table_name='user_engagements')
    op.drop_index('idx_user_engagements_user_id', table_name='user_engagements')
    op.drop_table('user_engagements')

    op.drop_index('idx_product_votes_user_id', table_name='product_votes')
    op.drop_index('idx_product_votes_product_id', table_name='product_votes')
    op.drop_table('product_votes')

    op.drop_index('idx_product_comments_created_at', table_name='product_comments')
    op.drop_index('idx_product_comments_user_id', table_name='product_comments')
    op.drop_index('idx_product_comments_product_id', table_name='product_comments')
    op.drop_table('product_comments')
