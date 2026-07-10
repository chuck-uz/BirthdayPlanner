"""In-memory SQLite для сервисных тестов (не требует настоящего Postgres)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  — регистрирует все модели в Base.metadata
from database import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def make_user(db_session: AsyncSession):
    from models import User

    _next_id = iter(range(1, 100_000))

    async def _make(*, telegram_id: int | None = None, full_name: str = "Test User", **kwargs) -> User:
        tg_id = telegram_id if telegram_id is not None else next(_next_id)
        user = User(telegram_id=tg_id, full_name=full_name, **kwargs)
        db_session.add(user)
        await db_session.flush()
        return user

    return _make
