"""Ensure pg_trgm extension is enabled

Revision ID: fc14aa07c34f
Revises: 12581959c664
Create Date: 2025-12-09 09:53:25.567373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc14aa07c34f'
down_revision: Union[str, None] = '12581959c664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram similarity search
    # This provides the similarity() function for fuzzy text matching
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')


def downgrade() -> None:
    # Don't drop the extension on downgrade as other things may depend on it
    pass
