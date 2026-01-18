"""Add business_locations table

Revision ID: e9932b8e83a7
Revises: 200c8d216efe
Create Date: 2026-01-18 00:42:01.966894

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9932b8e83a7'
down_revision: Union[str, None] = '200c8d216efe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('business_locations',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('address', sa.String(length=500), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('working_hours', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_business_locations_business', 'business_locations', ['business_id'], unique=False)
    op.create_index('idx_business_locations_city', 'business_locations', ['city'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_business_locations_city', table_name='business_locations')
    op.drop_index('idx_business_locations_business', table_name='business_locations')
    op.drop_table('business_locations')
