"""Add product embeddings for semantic search

Revision ID: 7f3a9b2c4d5e
Revises: e620e8e8e940
Create Date: 2025-11-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f3a9b2c4d5e'
down_revision: Union[str, None] = 'e620e8e8e940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add content_hash and enriched_description to products table (if they don't exist)
    conn = op.get_bind()

    # Check if content_hash column exists
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='products' AND column_name='content_hash'
    """))
    if not result.fetchone():
        op.add_column('products', sa.Column('content_hash', sa.String(), nullable=True))

    # Check if enriched_description column exists
    result = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='products' AND column_name='enriched_description'
    """))
    if not result.fetchone():
        op.add_column('products', sa.Column('enriched_description', sa.Text(), nullable=True))

    # Check if product_embeddings table exists
    result = conn.execute(sa.text("""
        SELECT table_name FROM information_schema.tables
        WHERE table_name='product_embeddings'
    """))

    if not result.fetchone():
        # Create product_embeddings table
        op.create_table('product_embeddings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=False),
            sa.Column('embedding_text', sa.Text(), nullable=True),
            sa.Column('model_version', sa.String(), nullable=True),
            sa.Column('content_hash', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('product_id', name='uq_product_embedding')
        )

        # Create index on product_id for faster lookups
        op.create_index('idx_product_embeddings_product_id', 'product_embeddings', ['product_id'], unique=False)

        # Note: The embedding column will be converted to vector(1536) type after table creation
        # This requires pgvector extension to be loaded
        op.execute('ALTER TABLE product_embeddings ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)')

        # Create index for vector similarity search (using cosine distance)
        op.execute('CREATE INDEX idx_product_embeddings_vector ON product_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')


def downgrade() -> None:
    # Drop indexes
    op.execute('DROP INDEX IF EXISTS idx_product_embeddings_vector')
    op.drop_index('idx_product_embeddings_product_id', table_name='product_embeddings')

    # Drop product_embeddings table
    op.drop_table('product_embeddings')

    # Remove columns from products table
    op.drop_column('products', 'enriched_description')
    op.drop_column('products', 'content_hash')

    # Note: We don't drop the vector extension in downgrade as it might be used elsewhere
