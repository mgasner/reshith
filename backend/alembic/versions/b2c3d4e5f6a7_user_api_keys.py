"""user_api_keys (and merge of pre-existing branch heads)

Adds the per-user encrypted LLM provider credentials table. Mirrors the
shape of ``user_srs_settings``: one row per user, ``user_id`` is a unique
FK with cascade delete. Both key columns are nullable so a user can
configure only one provider.

Also acts as a merge point for the two pre-existing branch heads
``a1b2c3d4e5f6`` (srs config) and ``8a4b2e9c5d12`` (deck is_primary), which
diverged from ``7f3a1c4b2d10``. Listing both in ``down_revision`` collapses
them into a single linear history without a no-op merge migration.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6, 8a4b2e9c5d12
Create Date: 2026-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f6", "8a4b2e9c5d12")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("openai_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("anthropic_api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("preferred_provider", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_api_keys")
