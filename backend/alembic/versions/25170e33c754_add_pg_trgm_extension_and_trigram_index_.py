"""Add pg_trgm extension and trigram index for hybrid search

Revision ID: 25170e33c754
Revises: 98ea4b649a74
Create Date: 2025-12-09 07:06:36.600085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25170e33c754'
down_revision: Union[str, None] = '98ea4b649a74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create GIN index on product title for fast trigram lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS products_title_trgm_idx
        ON products USING gin (lower(title) gin_trgm_ops)
    """)

    # Also create index on enriched_description for broader matching
    op.execute("""
        CREATE INDEX IF NOT EXISTS products_enriched_desc_trgm_idx
        ON products USING gin (lower(enriched_description) gin_trgm_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS products_enriched_desc_trgm_idx")
    op.execute("DROP INDEX IF EXISTS products_title_trgm_idx")
    # Note: Not dropping pg_trgm extension as it may be used by other things
