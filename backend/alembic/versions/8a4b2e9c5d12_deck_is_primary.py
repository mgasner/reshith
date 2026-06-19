"""deck is_primary flag with partial unique index per (owner, language)

Revision ID: 8a4b2e9c5d12
Revises: 7f3a1c4b2d10
Create Date: 2026-06-18 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8a4b2e9c5d12'
down_revision: Union[str, None] = '7f3a1c4b2d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'decks',
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_index(
        'uq_decks_primary_per_user_lang',
        'decks',
        ['owner_id', 'language'],
        unique=True,
        postgresql_where=sa.text('is_primary'),
    )
    # Backfill: mark each user's oldest deck per language as primary so existing
    # users have something to save to.
    op.execute(
        """
        UPDATE decks SET is_primary = true WHERE id IN (
            SELECT DISTINCT ON (owner_id, language) id
            FROM decks
            ORDER BY owner_id, language, created_at ASC
        )
        """
    )


def downgrade() -> None:
    op.drop_index('uq_decks_primary_per_user_lang', table_name='decks')
    op.drop_column('decks', 'is_primary')
