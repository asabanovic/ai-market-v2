"""Add social media and contact fields to businesses

Revision ID: 302c68bf1f95
Revises: f8c12d9a3e4b
Create Date: 2026-01-19 23:54:03.474649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '302c68bf1f95'
down_revision: Union[str, None] = 'f8c12d9a3e4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add social media and contact fields to businesses table
    op.add_column('businesses', sa.Column('website_url', sa.String(length=500), nullable=True))
    op.add_column('businesses', sa.Column('facebook_url', sa.String(length=500), nullable=True))
    op.add_column('businesses', sa.Column('instagram_url', sa.String(length=500), nullable=True))
    op.add_column('businesses', sa.Column('viber_contact', sa.String(length=100), nullable=True))
    op.add_column('businesses', sa.Column('contact_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('businesses', 'contact_email')
    op.drop_column('businesses', 'viber_contact')
    op.drop_column('businesses', 'instagram_url')
    op.drop_column('businesses', 'facebook_url')
    op.drop_column('businesses', 'website_url')
