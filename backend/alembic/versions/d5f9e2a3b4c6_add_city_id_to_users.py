"""Add city_id foreign key to users table

Revision ID: d5f9e2a3b4c6
Revises: c4e8f9a1b2d3
Create Date: 2026-01-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'd5f9e2a3b4c6'
down_revision = '737e48019699'
branch_labels = None
depends_on = None


def upgrade():
    # Add city_id column to users table
    op.add_column('users', sa.Column('city_id', sa.Integer(), nullable=True))

    # Create index for city_id
    op.create_index('idx_users_city_id', 'users', ['city_id'], unique=False)

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_city_id',
        'users', 'cities',
        ['city_id'], ['id'],
        ondelete='SET NULL'
    )

    # Populate city_id from existing city string column
    # Match users' city names to cities table
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE users u
        SET city_id = c.id
        FROM cities c
        WHERE u.city = c.name
        AND u.city IS NOT NULL
        AND u.city_id IS NULL
    """))


def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_users_city_id', 'users', type_='foreignkey')

    # Drop index
    op.drop_index('idx_users_city_id', table_name='users')

    # Drop column
    op.drop_column('users', 'city_id')
