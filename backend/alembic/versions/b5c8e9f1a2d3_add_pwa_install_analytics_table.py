"""Add PWA install analytics table

Revision ID: b5c8e9f1a2d3
Revises: edf83469ae72
Create Date: 2026-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c8e9f1a2d3'
down_revision: Union[str, None] = 'edf83469ae72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('pwa_install_analytics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('session_id', sa.String(length=64), nullable=True),
    sa.Column('event', sa.String(length=50), nullable=False),
    sa.Column('page_url', sa.String(length=500), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('platform', sa.String(length=50), nullable=True),
    sa.Column('browser', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pwa_analytics_event', 'pwa_install_analytics', ['event'], unique=False)
    op.create_index('idx_pwa_analytics_created', 'pwa_install_analytics', ['created_at'], unique=False)
    op.create_index('idx_pwa_analytics_session', 'pwa_install_analytics', ['session_id'], unique=False)
    op.create_index('idx_pwa_analytics_user', 'pwa_install_analytics', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_pwa_analytics_user', table_name='pwa_install_analytics')
    op.drop_index('idx_pwa_analytics_session', table_name='pwa_install_analytics')
    op.drop_index('idx_pwa_analytics_created', table_name='pwa_install_analytics')
    op.drop_index('idx_pwa_analytics_event', table_name='pwa_install_analytics')
    op.drop_table('pwa_install_analytics')
