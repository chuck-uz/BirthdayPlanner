"""Ручное создание группы админом: запрос в ЛС, callback-кнопки, привязка чата по my_chat_member."""

from __future__ import annotations

import asyncio
import datetime as dt
import html
import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin_broadcast_flow import try_handle_admin_broadcast_callback
from birthday_notify_logic import (
    _load_subscriber_recipients,
    get_birthday_event,
    message_gift_group_ready,
    target_display_name,
)
from birthday_utils import days_until_next_birthday, next_birthday_date
from config import get_settings
from models import AdminBirthdayPrompt, BirthdayEvent, User
from telegram_service import (
    get_bot_telegram_user_id,
    telegram_answer_callback_query,
    telegram_edit_message_text,
    telegram_edit_message_reply_markup,
    telegram_export_chat_invite_link,
    telegram_send_message,
    telegram_send_message_message_id,
)

logger = logging.getLogger(__name__)

STATE_PROMPT_SENT = "prompt_sent"
STATE_CREATE_SELECTED = "create_selected"
STATE_AWAIT_LINK = "await_link"
STATE_LINK_RECEIVED = "link_received"
STATE_SKIPPED = "skipped"
STATE_COMPLETED = "completed"

# callback_data ≤ 64 байт
CB_CREATE_PREFIX = "bd_c:"
CB_SKIP_PREFIX = "bd_s:"
CB_BROADCAST_LINK_PREFIX = "bd_g:"


def _ru_days_word(n: int) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return "день"
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "дня"
    return "дней"


def _ru_people_word(n: int) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return "человек"
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "человека"
    return "человек"


def _admin_prompt_text(
    target_name: str,
    days_until_birthday: int,
    subscriber_count: int,
    *,
    await_link: bool,
) -> str:
    safe = html.escape(target_name)
    d = max(0, abs(days_until_birthday))
    if await_link:
        return (
            f"🔔 <b>Новое событие!</b> Через {d} {_ru_days_word(d)} день рождения у <b>{safe}</b>.\n"
            f"Подписано друзей: {subscriber_count} {_ru_people_word(subscriber_count)}.\n\n"
            "Ожидаю ссылку на группу для обсуждения подарка. "
            "Пришлите URL в ЛС (лучше ответом на это сообщение)."
        )
    return (
        f"🔔 <b>Новое событие!</b> Через {d} {_ru_days_word(d)} день рождения у <b>{safe}</b>.\n"
        f"Подписано друзей: {subscriber_count} {_ru_people_word(subscriber_count)}.\n\n"
        "Желаете создать группу для обсуждения подарка?"
    )


def _instruction_text(subscriber_count: int) -> str:
    return (
        "Пожалуйста, создайте группу, добавьте меня туда и сделайте администратором. "
        f"Я сам разошлю ссылку всем {subscriber_count} друзьям."
    )


def _operator_telegram_id(prompt: AdminBirthdayPrompt, admin_id: int | None) -> int | None:
    if prompt.prompt_recipient_telegram_id is not None:
        return int(prompt.prompt_recipient_telegram_id)
    if admin_id is not None:
        return int(admin_id)
    return None


def _callback_operator_allowed(from_id: int, prompt: AdminBirthdayPrompt, admin_id: int | None) -> bool:
    if prompt.prompt_recipient_telegram_id is not None:
        return from_id == int(prompt.prompt_recipient_telegram_id)
    if admin_id is not None:
        return from_id == int(admin_id)
    return False


def _inline_keyboard_prompt(prompt_id: int) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Создать группу", "callback_data": f"{CB_CREATE_PREFIX}{prompt_id}"},
                {"text": "❌ Пропустить", "callback_data": f"{CB_SKIP_PREFIX}{prompt_id}"},
            ],
        ],
    }


def _extract_group_link(text: str) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    m = re.search(r"(https?://[^\s]+|t\.me/[^\s]+)", s, flags=re.I)
    if not m:
        return None
    u = m.group(1)
    if u.lower().startswith("t.me/"):
        u = "https://" + u
    if not u.lower().startswith(("http://", "https://")):
        return None
    return u


def _broadcast_keyboard(prompt_id: int) -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "🎁 Разослать подписчикам", "callback_data": f"{CB_BROADCAST_LINK_PREFIX}{prompt_id}"},
            ]
        ],
    }


async def _get_admin_prompt(
    session: AsyncSession,
    target_user_id: int,
    celebration_date: dt.date,
) -> AdminBirthdayPrompt | None:
    row = await session.execute(
        select(AdminBirthdayPrompt).where(
            AdminBirthdayPrompt.target_user_id == target_user_id,
            AdminBirthdayPrompt.celebration_date == celebration_date,
        ),
    )
    return row.scalar_one_or_none()


async def ensure_admin_prompt_for_birthday(
    session: AsyncSession,
    target: User,
    *,
    today: dt.date | None = None,
    trigger_subscriber: User | None = None,
    relax_days_limit: bool = False,
) -> None:
    """Создать/обновить админ-подсказку на ручной поток: «ожидаю ссылку»."""
    settings = get_settings()
    admin_id = settings.telegram_admin_id
    await_link_mode = admin_id is not None
    if admin_id is not None:
        recipient_tid = int(admin_id)
    elif trigger_subscriber is not None:
        recipient_tid = int(trigger_subscriber.telegram_id)
    else:
        return

    today = today or dt.date.today()
    assert target.birth_date is not None
    celebration = next_birthday_date(target.birth_date, today)

    if await get_birthday_event(session, target.id, celebration) is not None:
        logger.debug(
            "admin_prompt skip: BirthdayEvent exists target_id=%s celebration=%s",
            target.id,
            celebration,
        )
        return

    existing = await _get_admin_prompt(session, target.id, celebration)
    if existing is not None:
        if (
            existing.prompt_recipient_telegram_id is None
            or int(existing.prompt_recipient_telegram_id) == recipient_tid
        ):
            name = target_display_name(target)
            recipients = await _load_subscriber_recipients(session, target)
            if (
                trigger_subscriber is not None
                and trigger_subscriber.id != target.id
                and not any(r.id == trigger_subscriber.id for r in recipients)
            ):
                recipients.append(trigger_subscriber)
            if not recipients:
                logger.warning("admin_prompt resend skipped: no recipients target_id=%s", target.id)
                return
            days_left = days_until_next_birthday(target.birth_date, today)
            count = len(recipients)

            if await_link_mode:
                # Конвертируем старое сообщение с кнопками в «ожидаю ссылку».
                if existing.state == STATE_PROMPT_SENT and existing.admin_prompt_message_id is not None:
                    await telegram_edit_message_text(
                        recipient_tid,
                        int(existing.admin_prompt_message_id),
                        _admin_prompt_text(name, days_left, count, await_link=True),
                        parse_mode="HTML",
                        reply_markup={"inline_keyboard": []},
                    )
                    existing.state = STATE_AWAIT_LINK
                    await session.flush()
                    return

                if (
                    existing.state == STATE_AWAIT_LINK
                    and existing.admin_prompt_message_id is None
                ):
                    mid = await telegram_send_message_message_id(
                        recipient_tid,
                        _admin_prompt_text(name, days_left, count, await_link=True),
                        reply_markup=None,
                    )
                    existing.admin_prompt_message_id = mid
                    await session.flush()
                    if mid is None:
                        logger.error(
                            "admin_prompt resend failed Telegram chat_id=%s target_id=%s",
                            recipient_tid,
                            target.id,
                        )
                    return

            else:
                # Легаси-режим: показываем кнопки «создать группу/пропустить» только когда
                # TELEGRAM_ADMIN_ID не задан (т.е. ответственный — сам подписчик).
                if (
                    existing.state == STATE_PROMPT_SENT
                    and existing.admin_prompt_message_id is None
                ):
                    mid = await telegram_send_message_message_id(
                        recipient_tid,
                        _admin_prompt_text(name, days_left, count, await_link=False),
                        reply_markup=_inline_keyboard_prompt(existing.id),
                    )
                    existing.admin_prompt_message_id = mid
                    await session.flush()
                    if mid is None:
                        logger.error(
                            "admin_prompt resend failed Telegram chat_id=%s target_id=%s",
                            recipient_tid,
                            target.id,
                        )
                    return
        logger.debug(
            "admin_prompt skip: prompt row exists state=%s target_id=%s",
            existing.state,
            target.id,
        )
        return

    await session.flush()

    recipients = await _load_subscriber_recipients(session, target)
    if (
        trigger_subscriber is not None
        and trigger_subscriber.id != target.id
        and not any(r.id == trigger_subscriber.id for r in recipients)
    ):
        recipients.append(trigger_subscriber)

    if not recipients:
        logger.warning(
            "admin_prompt skip: zero subscribers target_id=%s celebration=%s",
            target.id,
            celebration,
        )
        return

    lead = settings.birthday_notify_days_before
    days_left = days_until_next_birthday(target.birth_date, today)
    if not relax_days_limit and days_left > lead:
        logger.debug(
            "admin_prompt skip: days_left=%s > lead=%s target_id=%s",
            days_left,
            lead,
            target.id,
        )
        return

    name = target_display_name(target)
    count = len(recipients)
    text = _admin_prompt_text(name, days_left, count, await_link=await_link_mode)

    row = AdminBirthdayPrompt(
        target_user_id=target.id,
        celebration_date=celebration,
        state=STATE_AWAIT_LINK if await_link_mode else STATE_PROMPT_SENT,
        prompt_recipient_telegram_id=recipient_tid,
    )
    session.add(row)
    await session.flush()

    mid = await telegram_send_message_message_id(
        recipient_tid,
        text,
        reply_markup=None if await_link_mode else _inline_keyboard_prompt(row.id),
    )
    row.admin_prompt_message_id = mid
    await session.flush()
    if mid is None:
        logger.error(
            "admin_prompt sendMessage failed chat_id=%s target_id=%s — проверьте /start у бота и BOT_TOKEN",
            recipient_tid,
            target.id,
        )


async def handle_telegram_callback_query(session: AsyncSession, cq: dict[str, Any]) -> None:
    if await try_handle_admin_broadcast_callback(session, cq):
        return

    settings = get_settings()
    admin_id = settings.telegram_admin_id

    data = str(cq.get("data") or "")
    raw_qid = cq.get("id")
    qid = str(raw_qid) if raw_qid is not None else ""
    if not qid:
        return

    m_send = re.match(rf"^{re.escape(CB_BROADCAST_LINK_PREFIX)}(\d+)$", data)
    if m_send:
        sid = int(m_send.group(1))
        prompt = await session.get(AdminBirthdayPrompt, sid)
        if prompt is None:
            await telegram_answer_callback_query(qid, text="Запрос устарел.", show_alert=True)
            return
        from_user = cq.get("from") or {}
        from_tid = int(from_user.get("id") or 0)
        if not _callback_operator_allowed(from_tid, prompt, admin_id):
            await telegram_answer_callback_query(qid, text="Нет доступа.", show_alert=True)
            return
        if prompt.state != STATE_LINK_RECEIVED:
            await telegram_answer_callback_query(qid, text="Сначала пришлите ссылку.", show_alert=True)
            return

        link = prompt.pending_invite_link
        if not link:
            await telegram_answer_callback_query(qid, text="Ссылка потерялась (перезапустите сценарий).", show_alert=True)
            return
        prompt.pending_invite_link = None

        target = await session.get(User, prompt.target_user_id)
        if target is None or target.birth_date is None:
            await telegram_answer_callback_query(qid, text="Именинник не найден.", show_alert=True)
            return

        celebration = prompt.celebration_date
        if await get_birthday_event(session, target.id, celebration) is not None:
            prompt.state = STATE_COMPLETED
            await session.flush()
            await telegram_answer_callback_query(qid, text="Уже обработано.", show_alert=False)
            return

        recipients = await _load_subscriber_recipients(session, target)
        recipients = [r for r in recipients if not bool(getattr(r, "is_blocked", False))]
        name = target_display_name(target)
        safe_link = html.escape(link, quote=True)
        text = (
            f"🎁 Секретный чат для обсуждения подарка для <b>{html.escape(name)}</b> готов!\n"
            f"Присоединяйтесь: <a href=\"{safe_link}\">{safe_link}</a>"
        )
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Присоединиться к чату", "url": link}],
            ]
        }

        sent = 0
        for sub in recipients:
            ok = await telegram_send_message(
                sub.telegram_id,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=False,
            )
            if ok:
                sent += 1
            await asyncio.sleep(0.05)

        session.add(
            BirthdayEvent(
                target_user_id=target.id,
                celebration_date=celebration,
                telegram_chat_id=None,
                invite_link=link,
                used_dm_fallback=False,
            ),
        )
        prompt.state = STATE_COMPLETED
        await session.flush()

        message = cq.get("message") or {}
        chat = message.get("chat") or {}
        msg_chat_id = chat.get("id")
        msg_id = message.get("message_id")
        if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
            await telegram_edit_message_reply_markup(msg_chat_id, msg_id, {"inline_keyboard": []})

        await telegram_answer_callback_query(qid, text=f"✅ Ссылка разослана {sent} пользователям.", show_alert=False)
        return

    m = re.match(r"^bd_([cs]):(\d+)$", data)
    if not m:
        await telegram_answer_callback_query(qid, text="Неизвестная команда.", show_alert=True)
        return

    action, sid = m.group(1), int(m.group(2))
    prompt = await session.get(AdminBirthdayPrompt, sid)
    if prompt is None or prompt.state != STATE_PROMPT_SENT:
        await telegram_answer_callback_query(qid, text="Запрос устарел или уже обработан.", show_alert=True)
        return

    from_user = cq.get("from") or {}
    from_tid = int(from_user.get("id") or 0)
    if not _callback_operator_allowed(from_tid, prompt, admin_id):
        await telegram_answer_callback_query(qid, text="Нет доступа.", show_alert=True)
        return

    target = await session.get(User, prompt.target_user_id)
    if target is None:
        await telegram_answer_callback_query(qid, text="Именинник не найден.", show_alert=True)
        return

    recipients = await _load_subscriber_recipients(session, target)
    count = len(recipients)

    message = cq.get("message") or {}
    chat = message.get("chat") or {}
    msg_chat_id = chat.get("id")
    msg_id = message.get("message_id")

    # В TELEGRAM_ADMIN_ID-режиме мы больше не используем кнопки создания группы.
    # Если старое сообщение ещё с кнопками — конвертируем в режим «ожидаю ссылку».
    if admin_id is not None and prompt.state == STATE_PROMPT_SENT:
        days_left = days_until_next_birthday(target.birth_date, dt.date.today())
        text = _admin_prompt_text(
            target_display_name(target),
            days_left,
            count,
            await_link=True,
        )
        prompt.state = STATE_AWAIT_LINK
        await session.flush()
        await telegram_answer_callback_query(qid, text="Кнопки отключены. Пришлите ссылку на группу.", show_alert=True)
        if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
            await telegram_edit_message_text(
                msg_chat_id,
                msg_id,
                text,
                parse_mode="HTML",
                reply_markup={"inline_keyboard": []},
            )
        return

    op_chat = _operator_telegram_id(prompt, admin_id)

    if action == "s":
        prompt.state = STATE_SKIPPED
        await telegram_answer_callback_query(qid, text="Пропущено.")
        if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
            await telegram_edit_message_reply_markup(msg_chat_id, msg_id, {"inline_keyboard": []})
        if op_chat is not None:
            await telegram_send_message(
                op_chat,
                "Вы пропустили создание группы для этого дня рождения. Подписчикам ссылка не отправляется.",
                parse_mode=None,
            )
        await session.flush()
        return

    # create
    prompt.state = STATE_CREATE_SELECTED
    await telegram_answer_callback_query(qid, text="Создайте группу и добавьте бота.")
    if isinstance(msg_chat_id, int) and isinstance(msg_id, int):
        await telegram_edit_message_reply_markup(msg_chat_id, msg_id, {"inline_keyboard": []})
    if op_chat is not None:
        await telegram_send_message(op_chat, _instruction_text(count), parse_mode=None)
    await session.flush()


async def handle_telegram_my_chat_member(session: AsyncSession, upd: dict[str, Any]) -> None:
    settings = get_settings()

    chat = upd.get("chat") or {}
    chat_type = chat.get("type")
    if chat_type not in ("group", "supergroup"):
        return

    new_cm = upd.get("new_chat_member") or {}
    old_cm = upd.get("old_chat_member") or {}
    new_user = new_cm.get("user") or {}
    if not new_user.get("is_bot"):
        return

    bot_id = await get_bot_telegram_user_id()
    if bot_id is None or int(new_user.get("id") or 0) != bot_id:
        return

    active = {"member", "administrator", "creator"}
    new_st = new_cm.get("status")
    old_st = old_cm.get("status")
    if new_st not in active or old_st in active:
        return

    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    row = await session.execute(
        select(AdminBirthdayPrompt)
        .where(AdminBirthdayPrompt.state == STATE_CREATE_SELECTED)
        .order_by(AdminBirthdayPrompt.id.asc())
        .limit(1),
    )
    prompt = row.scalar_one_or_none()
    if prompt is None:
        logger.info("my_chat_member: no pending create_selected prompt for chat_id=%s", chat_id)
        return

    target = await session.get(User, prompt.target_user_id)
    if target is None:
        prompt.state = STATE_SKIPPED
        await session.flush()
        return

    celebration = prompt.celebration_date
    if await get_birthday_event(session, target.id, celebration) is not None:
        prompt.state = STATE_COMPLETED
        await session.flush()
        return

    op_chat = _operator_telegram_id(prompt, settings.telegram_admin_id)

    link = await telegram_export_chat_invite_link(chat_id)
    if not link:
        if op_chat is not None:
            await telegram_send_message(
                op_chat,
                "Не удалось получить ссылку-приглашение. Проверьте, что бот в группе и имеет права.",
                parse_mode=None,
            )
        return

    recipients = await _load_subscriber_recipients(session, target)
    name = target_display_name(target)
    for sub in recipients:
        await telegram_send_message(sub.telegram_id, message_gift_group_ready(name, link))

    session.add(
        BirthdayEvent(
            target_user_id=target.id,
            celebration_date=celebration,
            telegram_chat_id=chat_id,
            invite_link=link,
            used_dm_fallback=False,
        ),
    )
    prompt.state = STATE_COMPLETED
    await session.flush()

    if op_chat is not None:
        await telegram_send_message(
            op_chat,
            f"Готово: ссылка разослана {len(recipients)} {_ru_people_word(len(recipients))}.",
            parse_mode=None,
        )


async def handle_telegram_admin_birthday_prompt_message(session: AsyncSession, message: dict[str, Any]) -> None:
    """
    Админ присылает URL: бот ждёт «ссылка получена» и показывает кнопку «Разослать подписчикам».

    Важно: мы стараемся сопоставить сообщение с конкретным промптом по `reply_to_message`,
    чтобы не перепутать разные именинников.
    """
    settings = get_settings()
    admin_id = settings.telegram_admin_id
    if admin_id is None:
        return

    chat = message.get("chat") or {}
    if chat.get("type") != "private":
        return

    from_user = message.get("from") or {}
    from_tid = int(from_user.get("id") or 0)
    if from_tid != int(admin_id):
        return

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return
    if text.strip().startswith("/"):
        return

    link = _extract_group_link(text)
    if not link:
        return

    reply_to = message.get("reply_to_message") or {}
    reply_mid = reply_to.get("message_id")

    rows = await session.execute(
        select(AdminBirthdayPrompt)
        .where(
            AdminBirthdayPrompt.state == STATE_AWAIT_LINK,
            AdminBirthdayPrompt.prompt_recipient_telegram_id == from_tid,
            AdminBirthdayPrompt.admin_prompt_message_id.isnot(None),
        )
        .order_by(AdminBirthdayPrompt.created_at.desc())
        .limit(10)
    )
    prompts = rows.scalars().all()
    if not prompts:
        return

    chosen = None
    if isinstance(reply_mid, int):
        for p in prompts:
            if isinstance(p.admin_prompt_message_id, int) and int(p.admin_prompt_message_id) == reply_mid:
                chosen = p
                break
    if chosen is None:
        # Если админ не ответил на конкретное сообщение — берём самый свежий промпт.
        chosen = prompts[0]

    assert chosen is not None
    chosen_target = await session.get(User, chosen.target_user_id)
    if chosen_target is None or chosen_target.birth_date is None:
        return

    chosen.pending_invite_link = link
    chosen.state = STATE_LINK_RECEIVED
    await session.flush()

    days_left = days_until_next_birthday(chosen_target.birth_date, dt.date.today())

    # Обновляем текст в том же сообщении: убираем «кнопки», показываем кнопку отправки после получения ссылки.
    safe_name = target_display_name(chosen_target)
    new_text = (
        f"🔔 <b>Новое событие!</b> Через {days_left} дней день рождения у <b>{html.escape(safe_name)}</b>.\n"
        f"Ссылка получена. Теперь нажмите кнопку для рассылки подписчикам."
    )

    msg_id = None
    # У нас есть message_id текущего сообщения админа, но редактировать нужно промпт, поэтому берём admin_prompt_message_id.
    if isinstance(chosen.admin_prompt_message_id, int):
        msg_id = chosen.admin_prompt_message_id

    if isinstance(chat.get("id"), int) and isinstance(msg_id, int):
        await telegram_edit_message_text(
            int(chat.get("id")),
            msg_id,
            new_text,
            parse_mode="HTML",
            reply_markup=_broadcast_keyboard(chosen.id),
        )
    else:
        await telegram_send_message(
            from_tid,
            new_text,
            parse_mode="HTML",
            reply_markup=_broadcast_keyboard(chosen.id),
        )
