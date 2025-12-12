"""Add only_discounted to user_searches

Revision ID: 3701202b8202
Revises: 4ea35d773bce
Create Date: 2025-12-12 11:25:20.478603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3701202b8202'
down_revision: Union[str, None] = '4ea35d773bce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_searches', sa.Column('only_discounted', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_searches', 'only_discounted')
