"""Integration tests for the createDeckFromPassage resolver.

Requires a Postgres scratch database (TEST_DATABASE_URL) with current
migrations applied; skipped when the DB is unreachable, matching the
convention in test_primary_deck.py.
"""

import os
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from reshith.api import resolvers
from reshith.api.types import CreateDeckFromPassageInput
from reshith.db import models
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
    await session.execute(delete(models.User).where(models.User.id == user.id))
    await session.commit()


def _info(session, user_id):
    return SimpleNamespace(context={"db": session, "current_user_id": user_id})


async def test_create_deck_from_passage_persists_cards(session, test_user):
    result = await resolvers.mutate_create_deck_from_passage(
        _info(session, test_user.id),
        CreateDeckFromPassageInput(reference="John 1:1"),
    )
    assert result.reference == "John 1:1"
    assert result.card_count > 0
    assert result.deck.language.name == "NT_GREEK"
    # First deck in a language becomes primary automatically.
    assert result.deck.is_primary is True

    count = await session.execute(
        select(func.count()).where(models.Card.deck_id == result.deck.id)
    )
    assert (count.scalar() or 0) == result.card_count


async def test_create_deck_from_passage_decks_are_independent(session, test_user):
    # Overlapping vocabulary (λόγος appears in both John 1:1 and 1:1-2) must
    # produce independent card rows per deck, not collide on a shared id.
    r1 = await resolvers.mutate_create_deck_from_passage(
        _info(session, test_user.id),
        CreateDeckFromPassageInput(reference="John 1:1"),
    )
    r2 = await resolvers.mutate_create_deck_from_passage(
        _info(session, test_user.id),
        CreateDeckFromPassageInput(reference="John 1:1-2"),
    )
    assert r1.deck.id != r2.deck.id
    # The longer passage is a superset, so it has at least as many cards.
    assert r2.card_count >= r1.card_count

    logos = "\u03bb\u03cc\u03b3\u03bf\u03c2"  # λόγος
    for deck_id in (r1.deck.id, r2.deck.id):
        got = await session.execute(
            select(models.Card).where(
                models.Card.deck_id == deck_id, models.Card.front == logos
            )
        )
        # Present exactly once in each deck.
        assert len(got.scalars().all()) == 1


async def test_create_deck_from_passage_rejects_bad_reference(session, test_user):
    with pytest.raises(Exception, match="Unknown book|parse"):
        await resolvers.mutate_create_deck_from_passage(
            _info(session, test_user.id),
            CreateDeckFromPassageInput(reference="Frobnicate 1"),
        )
