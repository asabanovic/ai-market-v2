"""add_custom_code_changed_flag

Revision ID: 432f3f76bd81
Revises: 909352703cce
Create Date: 2025-11-23 23:52:10.185087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '432f3f76bd81'
down_revision: Union[str, None] = '909352703cce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add flag to track if custom code has been changed from auto-generated
    op.add_column('users', sa.Column('custom_code_changed', sa.Boolean(), nullable=True, server_default='false'))

    # Set to false for all existing users
    op.execute("UPDATE users SET custom_code_changed = false WHERE custom_code_changed IS NULL")

    # Make it not nullable
    op.alter_column('users', 'custom_code_changed', nullable=False, server_default='false')


def downgrade() -> None:
    # Drop the column
    op.drop_column('users', 'custom_code_changed')
