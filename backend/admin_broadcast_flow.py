"""Админ: /admin_broadcast — рассылка ссылки на группу подписчикам именинника (FSM в памяти)."""

from __future__ import annotations

import asyncio
import datetime as dt
import html
import logging
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from birthday_notify_logic import _load_subscriber_recipients, target_display_name
from birthday_utils import days_until_next_birthday
from config import get_settings
from models import Subscription, User
from telegram_service import (
    telegram_answer_callback_query,
    telegram_edit_message_text,
    telegram_send_message,
)

logger = logging.getLogger(__name__)

# callback_data ≤ 64 байт
CB_LINK_PREFIX = "ab_l:"
CB_CANCEL = "ab_x"

# admin telegram_id -> target_user_id (ожидание ссылки)
_pending_broadcast: dict[int, int] = {}


def _admin_telegram_id() -> int | None:
    return get_settings().telegram_admin_id


def _is_admin_tid(from_tid: int) -> bool:
    aid = _admin_telegram_id()
    return aid is not None and from_tid == aid


def _command_matches(text: str, cmd: str) -> bool:
    if not text or not text.strip():
        return False
    first = text.strip().split()[0]
    return first == f"/{cmd}" or first.startswith(f"/{cmd}@")


def _extract_url(text: str) -> str | None:
    s = text.strip()
    m = re.search(r"(https?://[^\s]+|t\.me/[^\s]+)", s, re.I)
    if m:
        u = m.group(1)
        if u.lower().startswith("t.me/"):
            u = "https://" + u
        return u
    if "http" in s.lower() or "t.me" in s.lower():
        return s.split()[0] if s.split() else None
    return None


def _cancel_keyboard() -> dict[str, Any]:
    return {"inline_keyboard": [[{"text": "Отмена", "callback_data": CB_CANCEL}]]}


def _link_button_keyboard(url: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "Присоединиться к чату", "url": url}],
        ],
    }


async def _subscriber_count(session: AsyncSession, target_user_id: int) -> int:
    r = await session.execute(
        select(func.count()).select_from(Subscription).where(Subscription.target_user_id == target_user_id),
    )
    return int(r.scalar_one() or 0)


async def _upcoming_birthday_users(session: AsyncSession, *, days: int) -> list[tuple[User, int, int]]:
    """Список (User, days_until, subscriber_count) для ДР в ближайшие `days` дней."""
    today = dt.date.today()
    rows = await session.execute(select(User).where(User.birth_date.isnot(None), User.is_blocked.is_(False)))
    users = list(rows.scalars().all())
    out: list[tuple[User, int, int]] = []
    for u in users:
        assert u.birth_date is not None
        d = days_until_next_birthday(u.birth_date, today)
        if 0 <= d <= days:
            cnt = await _subscriber_count(session, u.id)
            out.append((u, d, cnt))
    out.sort(key=lambda x: (x[1], target_display_name(x[0]).lower()))
    return out


async def _send_broadcast_list(admin_chat_id: int, session: AsyncSession, *, days: int) -> None:
    rows = await _upcoming_birthday_users(session, days=days)
    if not rows:
        await telegram_send_message(
            admin_chat_id,
            f"Нет именинников с датой рождения в ближайшие {days} дней.",
            parse_mode=None,
        )
        return

    header = (
        f"<b>Именинники в ближайшие {days} дней</b>\n"
        "Под каждым — кнопка «Разослать ссылку» подписчикам (не имениннику)."
    )
    await telegram_send_message(admin_chat_id, header, parse_mode="HTML")

    for u, d_left, sub_cnt in rows:
        name = html.escape(target_display_name(u))
        d_word = "день" if d_left % 10 == 1 and d_left % 100 != 11 else "дня" if 2 <= d_left % 10 <= 4 and (d_left % 100 < 10 or d_left % 100 >= 20) else "дней"
        text = (
            f"🎂 <b>{name}</b>\n"
            f"До дня рождения: {d_left} {d_word}\n"
            f"Подписчиков: {sub_cnt}"
        )
        kb = {
            "inline_keyboard": [
                [{"text": "Разослать ссылку", "callback_data": f"{CB_LINK_PREFIX}{u.id}"}],
            ],
        }
        await telegram_send_message(admin_chat_id, text, parse_mode="HTML", reply_markup=kb)


async def try_handle_admin_broadcast_callback(session: AsyncSession, cq: dict[str, Any]) -> bool:
    """Обработать ab_l / ab_x. True — событие обработано."""
    data = str(cq.get("data") or "")
    if data != CB_CANCEL and not re.match(rf"^{re.escape(CB_LINK_PREFIX)}\d+$", data):
        return False

    raw_qid = cq.get("id")
    qid = str(raw_qid) if raw_qid is not None else ""
    if not qid:
        return True

    from_user = cq.get("from") or {}
    admin_tid = int(from_user.get("id") or 0)
    if not _is_admin_tid(admin_tid):
        await telegram_answer_callback_query(qid, text="Нет доступа.", show_alert=True)
        return True

    if data == CB_CANCEL:
        _pending_broadcast.pop(admin_tid, None)
        await telegram_answer_callback_query(qid, text="Отменено.")
        message = cq.get("message") or {}
        chat = message.get("chat") or {}
        msg_chat_id = chat.get("id")
        msg_id = message.get("message_id")
        if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
            await telegram_edit_message_text(
                msg_chat_id,
                msg_id,
                "Режим рассылки отменён.",
                parse_mode=None,
                reply_markup={"inline_keyboard": []},
            )
        else:
            await telegram_send_message(admin_tid, "Режим рассылки отменён.", parse_mode=None)
        return True

    m = re.match(rf"^{re.escape(CB_LINK_PREFIX)}(\d+)$", data)
    if not m:
        return True

    target_uid = int(m.group(1))
    target = await session.get(User, target_uid)
    if target is None:
        await telegram_answer_callback_query(qid, text="Пользователь не найден.", show_alert=True)
        return True

    _pending_broadcast[admin_tid] = target_uid
    name = html.escape(target_display_name(target))
    await telegram_answer_callback_query(qid, text="Пришлите ссылку в личку.")
    message = cq.get("message") or {}
    chat = message.get("chat") or {}
    msg_chat_id = chat.get("id")
    msg_id = message.get("message_id")
    prompt = (
        f"Пришлите ссылку на группу для <b>{name}</b>.\n"
        "Все подписчики (кроме именинника) получат её моментально."
    )
    if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
        await telegram_edit_message_text(
            msg_chat_id,
            msg_id,
            prompt,
            parse_mode="HTML",
            reply_markup=_cancel_keyboard(),
        )
    else:
        await telegram_send_message(
            admin_tid,
            prompt,
            parse_mode="HTML",
            reply_markup=_cancel_keyboard(),
        )
    return True


async def _send_to_subscribers(
    session: AsyncSession,
    target: User,
    link: str,
) -> int:
    recipients = await _load_subscriber_recipients(session, target)
    name = html.escape(target_display_name(target))
    href = html.escape(link, quote=True)
    text = (
        f"🎁 Секретный чат для обсуждения подарка для <b>{name}</b> готов!\n"
        f'<a href="{href}">Присоединиться к чату</a>'
    )
    n = 0
    for sub in recipients:
        if bool(getattr(sub, "is_blocked", False)):
            continue
        ok = await telegram_send_message(
            sub.telegram_id,
            text,
            parse_mode="HTML",
            reply_markup=_link_button_keyboard(link),
            disable_web_page_preview=False,
        )
        if ok:
            n += 1
        await asyncio.sleep(0.05)
    return n


async def handle_telegram_admin_broadcast_message(session: AsyncSession, message: dict[str, Any]) -> None:
    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        return

    from_user = message.get("from") or {}
    from_tid = int(from_user.get("id") or 0)
    if not _is_admin_tid(from_tid):
        return

    text = message.get("text")
    if not isinstance(text, str):
        return

    if _command_matches(text, "admin_broadcast"):
        days = get_settings().birthday_notify_days_before
        await _send_broadcast_list(from_tid, session, days=days)
        return

    if from_tid not in _pending_broadcast:
        return

    if text.strip().startswith("/"):
        return

    url = _extract_url(text)
    if not url:
        await telegram_send_message(
            from_tid,
            "Пришлите ссылку: ссылка должна содержать <code>http</code>, <code>https</code> или <code>t.me</code>.",
            parse_mode="HTML",
        )
        return

    target_uid = _pending_broadcast.get(from_tid)
    if target_uid is None:
        return

    target = await session.get(User, target_uid)
    _pending_broadcast.pop(from_tid, None)

    if target is None:
        await telegram_send_message(from_tid, "Именинник не найден.", parse_mode=None)
        return

    sent = await _send_to_subscribers(session, target, url)
    await telegram_send_message(
        from_tid,
        f"✅ Ссылка разослана {sent} пользователям.",
        parse_mode=None,
    )

