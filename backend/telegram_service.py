"""Вызовы Telegram Bot API (httpx). Стандартный Bot API не создаёт новые группы без участия пользователя — см. try_create_birthday_group."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
TG_API = "https://api.telegram.org"


async def telegram_api(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = get_settings()
    url = f"{TG_API}/bot{settings.bot_token}/{method}"
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload or {})
        try:
            return response.json()
        except Exception:
            return {"ok": False, "description": response.text[:200]}


async def telegram_user_can_receive_bot_messages(telegram_user_id: int) -> bool:
    """getChat для private chat существует, если пользователь хотя бы раз нажал Start у бота."""
    data = await telegram_api("getChat", {"chat_id": telegram_user_id})
    return bool(data.get("ok"))


_bot_username_cache: str | None = None


async def get_bot_username() -> str | None:
    global _bot_username_cache
    if _bot_username_cache:
        return _bot_username_cache
    data = await telegram_api("getMe")
    if data.get("ok") and isinstance(data.get("result"), dict):
        u = data["result"].get("username")
        if isinstance(u, str) and u.strip():
            _bot_username_cache = u.strip().lstrip("@")
            return _bot_username_cache
    return None


async def telegram_send_message(
    chat_id: int,
    text: str,
    *,
    parse_mode: str | None = "HTML",
    reply_markup: dict[str, Any] | None = None,
) -> bool:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = await telegram_api("sendMessage", payload)
    if not data.get("ok"):
        logger.warning("sendMessage failed chat_id=%s: %s", chat_id, data.get("description"))
    return bool(data.get("ok"))


async def telegram_send_message_message_id(
    chat_id: int,
    text: str,
    *,
    parse_mode: str | None = "HTML",
    reply_markup: dict[str, Any] | None = None,
) -> int | None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = await telegram_api("sendMessage", payload)
    if not data.get("ok"):
        logger.warning("sendMessage failed chat_id=%s: %s", chat_id, data.get("description"))
        return None
    result = data.get("result")
    if isinstance(result, dict):
        mid = result.get("message_id")
        if isinstance(mid, int):
            return mid
    return None


async def telegram_answer_callback_query(
    callback_query_id: str,
    *,
    text: str | None = None,
    show_alert: bool = False,
) -> bool:
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text is not None:
        payload["text"] = text
    if show_alert:
        payload["show_alert"] = True
    data = await telegram_api("answerCallbackQuery", payload)
    return bool(data.get("ok"))


async def telegram_edit_message_reply_markup(
    chat_id: int,
    message_id: int,
    reply_markup: dict[str, Any] | None,
) -> bool:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": reply_markup or {"inline_keyboard": []},
    }
    data = await telegram_api("editMessageReplyMarkup", payload)
    return bool(data.get("ok"))


async def telegram_export_chat_invite_link(chat_id: int) -> str | None:
    data = await telegram_api("exportChatInviteLink", {"chat_id": chat_id})
    if not data.get("ok"):
        logger.warning("exportChatInviteLink failed chat_id=%s: %s", chat_id, data.get("description"))
        return None
    link = data.get("result")
    return link if isinstance(link, str) else None


_bot_id_cache: int | None = None


async def get_bot_telegram_user_id() -> int | None:
    global _bot_id_cache
    if _bot_id_cache is not None:
        return _bot_id_cache
    data = await telegram_api("getMe")
    if not data.get("ok") or not isinstance(data.get("result"), dict):
        return None
    bid = data["result"].get("id")
    if isinstance(bid, int):
        _bot_id_cache = bid
        return bid
    return None


async def telegram_set_webhook(webhook_url: str, *, secret_token: str | None) -> bool:
    payload: dict[str, Any] = {
        "url": webhook_url,
        "allowed_updates": ["callback_query", "my_chat_member", "message"],
    }
    if secret_token:
        payload["secret_token"] = secret_token
    data = await telegram_api("setWebhook", payload)
    if not data.get("ok"):
        logger.warning("setWebhook failed: %s", data.get("description"))
    return bool(data.get("ok"))


async def try_create_birthday_group(title: str) -> tuple[int | None, str | None]:
    """
    Попытка создать супергруппу через Bot API.
    У большинства ботов метод отсутствует или возвращает ошибку — тогда (None, None).
    """
    trimmed = (title or "День рождения 🎁")[:128]
    data = await telegram_api(
        "createChat",
        {
            "title": trimmed,
        },
    )
    if not data.get("ok"):
        return None, None
    result = data.get("result")
    if not isinstance(result, dict):
        return None, None
    chat_id = result.get("id")
    if chat_id is None:
        return None, None
    inv = await telegram_api("exportChatInviteLink", {"chat_id": chat_id})
    if not inv.get("ok"):
        return int(chat_id), None
    link = inv.get("result")
    if not isinstance(link, str):
        return int(chat_id), None
    return int(chat_id), link
