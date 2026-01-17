"""Add deleted_at soft delete field to users

Revision ID: 200c8d216efe
Revises: e6f7g8h9i0j1
Create Date: 2026-01-17 12:45:10.166182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '200c8d216efe'
down_revision: Union[str, None] = 'e6f7g8h9i0j1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column for soft delete functionality
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
