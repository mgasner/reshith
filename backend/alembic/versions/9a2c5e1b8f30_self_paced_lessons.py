"""self-paced lessons: lesson_progress + exercise_attempts

Merges the two parallel heads (``a1b2c3d4e5f6`` per-user SRS config and
``8a4b2e9c5d12`` deck is_primary) and adds the lesson-progress + exercise
attempt tables used by the self-paced lesson study flow.

deck.is_primary and the ECCLESIASTICAL_LATIN enum value are already
present from the parent migrations, so we only add the new tables here.

Revision ID: 9a2c5e1b8f30
Revises: a1b2c3d4e5f6, 8a4b2e9c5d12
Create Date: 2026-06-18 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '9a2c5e1b8f30'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', '8a4b2e9c5d12')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reference the existing enum type — create_type=False keeps Alembic from
# attempting CREATE TYPE during create_table().
LANG_ENUM = postgresql.ENUM(
    'BIBLICAL_HEBREW', 'LATIN', 'ECCLESIASTICAL_LATIN', 'ANCIENT_GREEK',
    'NT_GREEK', 'SANSKRIT', 'PALI', 'BUDDHIST_HYBRID_SANSKRIT', 'ARAMAIC',
    'MIDRASHIC_HEBREW',
    name='languagecode',
    create_type=False,
)


def upgrade() -> None:
    # ── lesson_progress ──────────────────────────────────────────────────────
    op.create_table(
        'lesson_progress',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('language', LANG_ENUM, nullable=False),
        sa.Column(
            'current_lesson',
            sa.Integer(),
            nullable=False,
            server_default=sa.text('1'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'language', name='uq_lesson_progress_user_language'),
    )
    op.create_index(
        'ix_lesson_progress_user_id', 'lesson_progress', ['user_id'], unique=False,
    )

    # ── exercise_attempts ────────────────────────────────────────────────────
    op.create_table(
        'exercise_attempts',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('language', LANG_ENUM, nullable=False),
        sa.Column('exercise_type', sa.String(length=50), nullable=False),
        sa.Column('pattern', sa.String(length=100), nullable=True),
        sa.Column('vocab_id', UUID(as_uuid=True), nullable=True),
        sa.Column('correct', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column(
            'attempted_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_exercise_attempts_user_lang_type',
        'exercise_attempts',
        ['user_id', 'language', 'exercise_type'],
        unique=False,
    )
    op.create_index(
        'ix_exercise_attempts_user_vocab',
        'exercise_attempts',
        ['user_id', 'vocab_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_exercise_attempts_user_vocab', table_name='exercise_attempts')
    op.drop_index('ix_exercise_attempts_user_lang_type', table_name='exercise_attempts')
    op.drop_table('exercise_attempts')

    op.drop_index('ix_lesson_progress_user_id', table_name='lesson_progress')
    op.drop_table('lesson_progress')
