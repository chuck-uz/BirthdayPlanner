"""Ежедневная рассылка подписчикам за N дней до ДР. Именинник не получает сообщения."""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from birthday_notify_logic import create_birthday_event_and_notify_subscribers
from birthday_utils import days_until_next_birthday
from config import get_settings
from database import async_session_maker
from models import User

logger = logging.getLogger(__name__)


async def _process_one_target(session: AsyncSession, target: User, today: dt.date) -> None:
    settings = get_settings()
    lead = settings.birthday_notify_days_before
    assert target.birth_date is not None
    if days_until_next_birthday(target.birth_date, today) != lead:
        return
    await create_birthday_event_and_notify_subscribers(session, target, today=today)


async def run_daily_birthday_reminders() -> None:
    today = dt.date.today()
    settings = get_settings()
    lead = settings.birthday_notify_days_before
    logger.info("birthday_reminders: date=%s lead_days=%s", today, lead)

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.birth_date.is_not(None), User.is_blocked.is_(False)),
        )
        targets = list(result.scalars().unique().all())

    for target in targets:
        assert target.birth_date is not None
        if days_until_next_birthday(target.birth_date, today) != lead:
            continue
        try:
            async with async_session_maker() as session:
                await _process_one_target(session, target, today)
                await session.commit()
        except Exception:
            logger.exception("birthday_reminders failed for user_id=%s", target.id)
