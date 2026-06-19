"""srs_config_and_per_user_state

Adds the per-user / per-deck SRS configuration tables required for the
configurable SM-2 algorithm, and extends the ``languagecode`` enum with
``ECCLESIASTICAL_LATIN`` so Ecclesiastical Latin decks can be created.

The ``srs_states`` composite UNIQUE on ``(card_id, user_id)`` is introduced
in the upstream migration ``7f3a1c4b2d10`` and is not duplicated here.

Revision ID: a1b2c3d4e5f6
Revises: 7f3a1c4b2d10
Create Date: 2026-06-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7f3a1c4b2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── languagecode enum: add ECCLESIASTICAL_LATIN ────────────────────────
    # ALTER TYPE ADD VALUE must run outside a transaction.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE languagecode ADD VALUE IF NOT EXISTS 'ECCLESIASTICAL_LATIN'")

    # ── user_srs_settings: one row per user, all columns NOT NULL ─────────
    op.create_table(
        "user_srs_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("initial_ef", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("minimum_ef", sa.Float(), nullable=False, server_default="1.3"),
        sa.Column("graduating_interval_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("easy_interval_days", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("hard_multiplier", sa.Float(), nullable=False, server_default="1.2"),
        sa.Column("easy_bonus", sa.Float(), nullable=False, server_default="1.3"),
        sa.Column("interval_modifier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("maximum_interval_days", sa.Integer(), nullable=False, server_default="36500"),
        sa.Column("lapse_multiplier", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "lapse_minimum_interval_days", sa.Integer(), nullable=False, server_default="1"
        ),
        sa.Column("new_cards_per_day", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("reviews_per_day", sa.Integer(), nullable=False, server_default="200"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # ── deck_srs_settings: one row per deck, every config column NULLABLE ─
    op.create_table(
        "deck_srs_settings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("deck_id", sa.UUID(), nullable=False),
        sa.Column("initial_ef", sa.Float(), nullable=True),
        sa.Column("minimum_ef", sa.Float(), nullable=True),
        sa.Column("graduating_interval_days", sa.Integer(), nullable=True),
        sa.Column("easy_interval_days", sa.Integer(), nullable=True),
        sa.Column("hard_multiplier", sa.Float(), nullable=True),
        sa.Column("easy_bonus", sa.Float(), nullable=True),
        sa.Column("interval_modifier", sa.Float(), nullable=True),
        sa.Column("maximum_interval_days", sa.Integer(), nullable=True),
        sa.Column("lapse_multiplier", sa.Float(), nullable=True),
        sa.Column("lapse_minimum_interval_days", sa.Integer(), nullable=True),
        sa.Column("new_cards_per_day", sa.Integer(), nullable=True),
        sa.Column("reviews_per_day", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["deck_id"], ["decks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_id"),
    )


def downgrade() -> None:
    op.drop_table("deck_srs_settings")
    op.drop_table("user_srs_settings")
    # NOTE: Postgres does not support removing enum values cleanly without
    # recreating the type. ECCLESIASTICAL_LATIN is left in place on downgrade.
