"""Входящие обновления Telegram: callback_query (кнопки админа), my_chat_member (бот добавлен в группу)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException, Request

from birthday_admin_flow import handle_telegram_callback_query, handle_telegram_my_chat_member
from telegram_bot_start_handler import handle_telegram_message_for_bot_activity
from config import get_settings
from database import async_session_maker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict[str, bool]:
    settings = get_settings()
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="forbidden")

    body = await request.json()
    try:
        async with async_session_maker() as session:
            if "callback_query" in body:
                await handle_telegram_callback_query(session, body["callback_query"])
            elif "my_chat_member" in body:
                await handle_telegram_my_chat_member(session, body["my_chat_member"])
            elif "message" in body:
                await handle_telegram_message_for_bot_activity(session, body["message"])
            await session.commit()
    except Exception:
        logger.exception("telegram_webhook handler failed update_id=%s", body.get("update_id"))

    return {"ok": True}
