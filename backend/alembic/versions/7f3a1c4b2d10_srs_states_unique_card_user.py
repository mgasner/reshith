"""srs_states unique constraint on (card_id, user_id)

Revision ID: 7f3a1c4b2d10
Revises: c00dfca323c2
Create Date: 2026-06-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7f3a1c4b2d10'
down_revision: Union[str, None] = 'c00dfca323c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the original single-column unique on card_id and replace with a
    # composite unique on (card_id, user_id) so each user can have their own
    # SM-2 state per card.
    op.drop_constraint('srs_states_card_id_key', 'srs_states', type_='unique')
    op.create_unique_constraint(
        'uq_srs_card_user', 'srs_states', ['card_id', 'user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_srs_card_user', 'srs_states', type_='unique')
    op.create_unique_constraint(
        'srs_states_card_id_key', 'srs_states', ['card_id']
    )
