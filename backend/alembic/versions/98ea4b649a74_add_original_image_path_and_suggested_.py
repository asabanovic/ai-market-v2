"""Add original_image_path and suggested_images to products

Revision ID: 98ea4b649a74
Revises: a1b2c3d4e5f6
Create Date: 2025-12-03 23:48:41.422902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98ea4b649a74'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('original_image_path', sa.String(), nullable=True))
    op.add_column('products', sa.Column('suggested_images', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'suggested_images')
    op.drop_column('products', 'original_image_path')
