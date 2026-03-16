"""Seed data for development."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.db.models import User
from reshith.db.session import async_session_maker
from reshith.services.auth import hash_password

logger = logging.getLogger(__name__)

DEV_USERNAME = "dev"
DEV_PASSWORD = "password"
DEV_EMAIL = "dev@reshith.local"
DEV_DISPLAY_NAME = "Dev User"


async def seed_dev_data() -> None:
    async with async_session_maker() as session:
        await _ensure_dev_user(session)
        await session.commit()


async def _ensure_dev_user(session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.username == DEV_USERNAME))
    if result.scalar_one_or_none() is not None:
        return

    user = User(
        email=DEV_EMAIL,
        username=DEV_USERNAME,
        display_name=DEV_DISPLAY_NAME,
        password_hash=hash_password(DEV_PASSWORD),
    )
    session.add(user)
    logger.info("Created dev user '%s' (password: '%s')", DEV_USERNAME, DEV_PASSWORD)
