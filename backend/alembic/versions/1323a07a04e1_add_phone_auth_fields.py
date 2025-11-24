"""add_phone_auth_fields

Revision ID: 1323a07a04e1
Revises: 144e87ad4d89
Create Date: 2025-11-23 22:36:09.974750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1323a07a04e1'
down_revision: Union[str, None] = '144e87ad4d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add phone_verified and registration_method to users table
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('registration_method', sa.String(), nullable=True))

    # Make phone unique
    op.create_unique_constraint('uq_users_phone', 'users', ['phone'])

    # Create otp_codes table
    op.create_table(
        'otp_codes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_otp_codes_phone', 'otp_codes', ['phone'])
    op.create_index('idx_otp_phone_expires', 'otp_codes', ['phone', 'expires_at'])

    # Set defaults for existing users
    op.execute("UPDATE users SET phone_verified = false WHERE phone_verified IS NULL")
    op.execute("UPDATE users SET registration_method = 'email' WHERE registration_method IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('users', 'phone_verified', nullable=False, server_default=sa.false())
    op.alter_column('users', 'registration_method', nullable=False, server_default='email')


def downgrade() -> None:
    # Drop otp_codes table
    op.drop_index('idx_otp_phone_expires', 'otp_codes')
    op.drop_index('idx_otp_codes_phone', 'otp_codes')
    op.drop_table('otp_codes')

    # Remove phone unique constraint
    op.drop_constraint('uq_users_phone', 'users', type_='unique')

    # Remove new columns from users
    op.drop_column('users', 'registration_method')
    op.drop_column('users', 'phone_verified')
