"""Tests for primary-deck provisioning and lesson-progress accounting.

Requires DATABASE_URL pointing at a Postgres scratch database with the
current migrations applied. Skipped when the DB is unreachable.
"""

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from reshith.db import models
from reshith.exercises.vocab_id import vocab_id
from reshith.services import lesson_progress, primary_deck
from reshith.services.auth import hash_password

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://reshith:reshith@localhost:5432/reshith",
)


@pytest_asyncio.fixture
async def session():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        async with engine.connect() as conn:
            await conn.close()
    except Exception as e:
        pytest.skip(f"Postgres not reachable: {e}")
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s
        await s.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    user = models.User(
        email=f"t-{uuid.uuid4()}@test.local",
        username=f"t-{uuid.uuid4().hex[:8]}",
        display_name="Tester",
        password_hash=hash_password("pw-12345678"),
    )
    session.add(user)
    await session.flush()
    yield user
    # Cleanup cascades via FK.
    await session.execute(delete(models.User).where(models.User.id == user.id))
    await session.commit()


async def test_primary_deck_auto_provisioned(session, test_user):
    deck = await primary_deck.get_or_create_primary_deck(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW,
    )
    assert deck.is_primary is True
    assert deck.language == models.LanguageCode.BIBLICAL_HEBREW
    # Second call returns the same row.
    deck2 = await primary_deck.get_or_create_primary_deck(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW,
    )
    assert deck.id == deck2.id


async def test_ensure_cards_is_idempotent(session, test_user):
    deck = await primary_deck.get_or_create_primary_deck(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW,
    )
    seeds = [
        primary_deck.VocabSeed(lemma="טֶסְט", definition="test", lesson=1),
        primary_deck.VocabSeed(lemma="עוֹד", definition="more", lesson=1),
    ]
    await primary_deck.ensure_cards_for_vocab(session, deck, seeds)
    # Second call must not insert duplicates.
    await primary_deck.ensure_cards_for_vocab(session, deck, seeds)
    count = (
        await session.execute(
            select(models.Card).where(models.Card.deck_id == deck.id)
        )
    ).scalars().all()
    assert len(count) == 2
    # IDs are deterministic.
    expected_id = vocab_id("hbo", "טֶסְט")
    assert any(c.id == expected_id for c in count)


async def test_lesson_progress_auto_creates_at_lesson_1(session, test_user):
    info = await lesson_progress.get_progress(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW,
    )
    assert info.current_lesson == 1
    assert info.total_lessons >= 1
    # No reviews yet → 0 mastered.
    assert info.vocab_mastered == 0
    # All lesson-1 vocab counts as "due" since no SRS rows exist.
    assert info.due_count == info.vocab_total


async def test_advance_lesson_increments(session, test_user):
    info = await lesson_progress.advance_lesson(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW,
    )
    assert info.current_lesson == 2


async def test_advance_lesson_capped_at_total(session, test_user):
    db_lang = models.LanguageCode.BIBLICAL_HEBREW
    for _ in range(20):
        info = await lesson_progress.advance_lesson(session, test_user.id, db_lang)
    assert info.current_lesson == info.total_lessons


async def test_set_current_lesson_clamps_to_one(session, test_user):
    info = await lesson_progress.set_current_lesson(
        session, test_user.id, models.LanguageCode.BIBLICAL_HEBREW, 0,
    )
    assert info.current_lesson == 1
