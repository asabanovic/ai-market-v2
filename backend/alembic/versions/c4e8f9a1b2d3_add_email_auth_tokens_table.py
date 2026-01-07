"""Add email_auth_tokens table for magic link authentication

Revision ID: c4e8f9a1b2d3
Revises: b5c8e9f1a2d3
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4e8f9a1b2d3'
down_revision = 'b5c8e9f1a2d3'
branch_labels = None
depends_on = None


def upgrade():
    # Create email_auth_tokens table for magic link authentication
    op.create_table(
        'email_auth_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('email_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes for efficient lookups
    op.create_index('idx_email_auth_token', 'email_auth_tokens', ['token'])
    op.create_index('idx_email_auth_user', 'email_auth_tokens', ['user_id'])
    op.create_index('idx_email_auth_expires', 'email_auth_tokens', ['expires_at'])


def downgrade():
    op.drop_index('idx_email_auth_expires')
    op.drop_index('idx_email_auth_user')
    op.drop_index('idx_email_auth_token')
    op.drop_table('email_auth_tokens')
