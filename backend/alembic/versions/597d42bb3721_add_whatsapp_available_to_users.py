"""add_whatsapp_available_to_users

Revision ID: 597d42bb3721
Revises: 41d2c4106ed6
Create Date: 2025-11-24 10:39:25.729361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '597d42bb3721'
down_revision: Union[str, None] = '41d2c4106ed6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add whatsapp_available column with default True
    op.add_column('users', sa.Column('whatsapp_available', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    # Remove whatsapp_available column
    op.drop_column('users', 'whatsapp_available')
