"""Обработка /start в личке: отмечаем, что пользователь активировал бота."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User

logger = logging.getLogger(__name__)


async def handle_telegram_message_for_bot_activity(session: AsyncSession, message: dict) -> None:
    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        return
    text = message.get("text")
    if not isinstance(text, str) or not text.strip().startswith("/start"):
        return
    from_user = message.get("from") or {}
    tid = from_user.get("id")
    if not isinstance(tid, int):
        return
    result = await session.execute(select(User).where(User.telegram_id == tid))
    user = result.scalar_one_or_none()
    if user is None:
        return
    if not user.is_bot_active:
        user.is_bot_active = True
        logger.info("is_bot_active set for user_id=%s telegram_id=%s", user.id, tid)
