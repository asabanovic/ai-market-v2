"""add_cascade_delete_to_product_foreign_keys

Revision ID: cc6ff6f0bb1b
Revises: 597d42bb3721
Create Date: 2025-12-02 15:28:52.214367

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc6ff6f0bb1b'
down_revision: Union[str, None] = '597d42bb3721'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add CASCADE delete to all foreign keys referencing products.id

    # product_embeddings.product_id
    op.drop_constraint('product_embeddings_product_id_fkey', 'product_embeddings', type_='foreignkey')
    op.create_foreign_key('product_embeddings_product_id_fkey', 'product_embeddings', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # favorites.product_id
    op.drop_constraint('favorites_product_id_fkey', 'favorites', type_='foreignkey')
    op.create_foreign_key('favorites_product_id_fkey', 'favorites', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # shopping_list_items.product_id
    op.drop_constraint('shopping_list_items_product_id_fkey', 'shopping_list_items', type_='foreignkey')
    op.create_foreign_key('shopping_list_items_product_id_fkey', 'shopping_list_items', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # shopping_list_items.business_id (also add cascade for business deletion)
    op.drop_constraint('shopping_list_items_business_id_fkey', 'shopping_list_items', type_='foreignkey')
    op.create_foreign_key('shopping_list_items_business_id_fkey', 'shopping_list_items', 'businesses', ['business_id'], ['id'], ondelete='CASCADE')

    # product_comments.product_id
    op.drop_constraint('product_comments_product_id_fkey', 'product_comments', type_='foreignkey')
    op.create_foreign_key('product_comments_product_id_fkey', 'product_comments', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # product_votes.product_id
    op.drop_constraint('product_votes_product_id_fkey', 'product_votes', type_='foreignkey')
    op.create_foreign_key('product_votes_product_id_fkey', 'product_votes', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    # user_engagements.product_id
    op.drop_constraint('user_engagements_product_id_fkey', 'user_engagements', type_='foreignkey')
    op.create_foreign_key('user_engagements_product_id_fkey', 'user_engagements', 'products', ['product_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Remove CASCADE delete, restore original foreign keys

    # product_embeddings.product_id
    op.drop_constraint('product_embeddings_product_id_fkey', 'product_embeddings', type_='foreignkey')
    op.create_foreign_key('product_embeddings_product_id_fkey', 'product_embeddings', 'products', ['product_id'], ['id'])

    # favorites.product_id
    op.drop_constraint('favorites_product_id_fkey', 'favorites', type_='foreignkey')
    op.create_foreign_key('favorites_product_id_fkey', 'favorites', 'products', ['product_id'], ['id'])

    # shopping_list_items.product_id
    op.drop_constraint('shopping_list_items_product_id_fkey', 'shopping_list_items', type_='foreignkey')
    op.create_foreign_key('shopping_list_items_product_id_fkey', 'shopping_list_items', 'products', ['product_id'], ['id'])

    # shopping_list_items.business_id
    op.drop_constraint('shopping_list_items_business_id_fkey', 'shopping_list_items', type_='foreignkey')
    op.create_foreign_key('shopping_list_items_business_id_fkey', 'shopping_list_items', 'businesses', ['business_id'], ['id'])

    # product_comments.product_id
    op.drop_constraint('product_comments_product_id_fkey', 'product_comments', type_='foreignkey')
    op.create_foreign_key('product_comments_product_id_fkey', 'product_comments', 'products', ['product_id'], ['id'])

    # product_votes.product_id
    op.drop_constraint('product_votes_product_id_fkey', 'product_votes', type_='foreignkey')
    op.create_foreign_key('product_votes_product_id_fkey', 'product_votes', 'products', ['product_id'], ['id'])

    # user_engagements.product_id
    op.drop_constraint('user_engagements_product_id_fkey', 'user_engagements', type_='foreignkey')
    op.create_foreign_key('user_engagements_product_id_fkey', 'user_engagements', 'products', ['product_id'], ['id'])
