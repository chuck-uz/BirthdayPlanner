"""Интерактивный flow "создать чат в Telegram" для дней рождения внутри приватных групп.

Уведомление админов ролевое и не зависит от подписчиков — админы узнают о ДР каждого
участника через настроенное группой число дней. А вот интерактивный промпт "создать
чат" (с кнопками) уходит им, только если у именинника есть хотя бы один подписчик —
иначе создавать чат не для кого. Исключение: если именинник — единственный админ
группы, промпт уходит всем остальным участникам всегда, независимо от подписчиков
(резервный путь, когда обычного пути "спросить админа" не существует).

Промпт уходит всем получателям одновременно; кто первый нажал «Создать чат» и добавил
бота в свежесозданную Telegram-группу — тот и закрывает событие (my_chat_member).
Готовая ссылка-приглашение рассылается подписчикам именинника, которые сейчас состоят
в этой же группе.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import html
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from birthday_utils import days_until_next_birthday, next_birthday_date
from models import (
    Group,
    GroupBirthdayEvent,
    GroupBirthdayPrompt,
    GroupBirthdayPromptRecipient,
    GroupRole,
    User,
    UserGroup,
)
from services.private_groups import group_subscribers_for
from telegram_service import (
    get_bot_telegram_user_id,
    telegram_answer_callback_query,
    telegram_edit_message_reply_markup,
    telegram_edit_message_text,
    telegram_export_chat_invite_link,
    telegram_send_message,
    telegram_send_message_message_id,
)

logger = logging.getLogger(__name__)

CB_CREATE_PREFIX = "gbp_c:"
CB_SKIP_PREFIX = "gbp_s:"


def _display_name(user: User) -> str:
    return (user.full_name or "").strip() or f"Участник #{user.id}"


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
        return "человеку"
    if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return "человекам"
    return "людям"


@dataclass(frozen=True)
class GroupBirthdayCandidate:
    group_id: int
    group_name: str
    birthday_user_id: int
    birthday_user_name: str
    celebration_date: dt.date
    days_left: int
    recipient_user_ids: tuple[int, ...]


def plan_group_birthday_prompt(
    *,
    group: Group,
    memberships: list[UserGroup],
    birthday_user: User,
    today: dt.date,
    has_subscribers: bool,
) -> GroupBirthdayCandidate | None:
    """Выбирает получателей интерактивного промпта "создать чат" для одного именинника."""
    if birthday_user.birth_date is None or birthday_user.is_blocked:
        return None
    birthday_membership = next((m for m in memberships if m.user_id == birthday_user.id), None)
    if birthday_membership is None:
        return None

    days_left = days_until_next_birthday(birthday_user.birth_date, today)
    if days_left != group.notify_lead_days:
        return None

    celebration = next_birthday_date(birthday_user.birth_date, today)
    name = _display_name(birthday_user)

    admins = [m for m in memberships if m.role == GroupRole.admin.value]
    other_admins = [m for m in admins if m.user_id != birthday_user.id]

    if other_admins:
        if not has_subscribers:
            return None
        recipients = tuple(m.user_id for m in other_admins)
    else:
        # Единственный админ группы — сам именинник: спрашиваем всех остальных, всегда.
        recipients = tuple(m.user_id for m in memberships if m.user_id != birthday_user.id)
        if not recipients:
            return None

    return GroupBirthdayCandidate(
        group_id=group.id,
        group_name=group.name,
        birthday_user_id=birthday_user.id,
        birthday_user_name=name,
        celebration_date=celebration,
        days_left=days_left,
        recipient_user_ids=recipients,
    )


def _prompt_text(candidate: GroupBirthdayCandidate) -> str:
    d = candidate.days_left
    safe_name = html.escape(candidate.birthday_user_name)
    safe_group = html.escape(candidate.group_name)
    return (
        f"🎂 В группе <b>{safe_group}</b> через {d} {_ru_days_word(d)} "
        f"день рождения у <b>{safe_name}</b>.\n"
        "Желаете создать чат в Telegram для обсуждения подарка?"
    )


def _instruction_text(subscriber_count: int) -> str:
    if subscriber_count == 0:
        return (
            "Пожалуйста, создайте группу в Telegram, добавьте меня туда и сделайте "
            "администратором. Подписчиков на этот ДР пока нет — ссылку разослать будет некому, "
            "но чат создастся."
        )
    return (
        "Пожалуйста, создайте группу в Telegram, добавьте меня туда и сделайте "
        f"администратором. Я разошлю ссылку {subscriber_count} {_ru_people_word(subscriber_count)}, "
        "кто подписан на этот ДР."
    )


def _prompt_keyboard(prompt_id: int) -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Создать чат", "callback_data": f"{CB_CREATE_PREFIX}{prompt_id}"},
                {"text": "❌ Пропустить", "callback_data": f"{CB_SKIP_PREFIX}{prompt_id}"},
            ],
        ],
    }


async def _existing_prompt(
    session: AsyncSession, *, group_id: int, target_user_id: int, celebration_date: dt.date
) -> GroupBirthdayPrompt | None:
    result = await session.execute(
        select(GroupBirthdayPrompt).where(
            GroupBirthdayPrompt.group_id == group_id,
            GroupBirthdayPrompt.target_user_id == target_user_id,
            GroupBirthdayPrompt.celebration_date == celebration_date,
        ),
    )
    return result.scalar_one_or_none()


async def _event_exists(
    session: AsyncSession, *, group_id: int, target_user_id: int, celebration_date: dt.date
) -> bool:
    result = await session.execute(
        select(GroupBirthdayEvent.id).where(
            GroupBirthdayEvent.group_id == group_id,
            GroupBirthdayEvent.target_user_id == target_user_id,
            GroupBirthdayEvent.celebration_date == celebration_date,
        ),
    )
    return result.scalar_one_or_none() is not None


async def send_group_birthday_prompt(session: AsyncSession, candidate: GroupBirthdayCandidate) -> None:
    """Идемпотентно создаёт промпт и рассылает его всем получателям одновременно."""
    if await _existing_prompt(
        session,
        group_id=candidate.group_id,
        target_user_id=candidate.birthday_user_id,
        celebration_date=candidate.celebration_date,
    ):
        return
    if await _event_exists(
        session,
        group_id=candidate.group_id,
        target_user_id=candidate.birthday_user_id,
        celebration_date=candidate.celebration_date,
    ):
        return

    result = await session.execute(select(User).where(User.id.in_(candidate.recipient_user_ids)))
    recipients = [u for u in result.scalars().all() if not u.is_blocked and u.is_bot_active]
    if not recipients:
        return

    prompt = GroupBirthdayPrompt(
        group_id=candidate.group_id,
        target_user_id=candidate.birthday_user_id,
        celebration_date=candidate.celebration_date,
    )
    session.add(prompt)
    await session.flush()

    text = _prompt_text(candidate)
    keyboard = _prompt_keyboard(prompt.id)
    for recipient in recipients:
        mid = await telegram_send_message_message_id(recipient.telegram_id, text, reply_markup=keyboard)
        session.add(
            GroupBirthdayPromptRecipient(
                prompt_id=prompt.id, user_id=recipient.id, telegram_message_id=mid
            ),
        )
        await asyncio.sleep(0.05)
    await session.flush()


async def handle_group_birthday_callback_query(session: AsyncSession, cq: dict) -> bool:
    """Обрабатывает нажатие «Создать чат» / «Пропустить». True — если это был наш callback."""
    data = str(cq.get("data") or "")
    if data.startswith(CB_CREATE_PREFIX):
        action, raw_id = "create", data[len(CB_CREATE_PREFIX) :]
    elif data.startswith(CB_SKIP_PREFIX):
        action, raw_id = "skip", data[len(CB_SKIP_PREFIX) :]
    else:
        return False

    raw_qid = cq.get("id")
    qid = str(raw_qid) if raw_qid is not None else ""
    if not qid or not raw_id.isdigit():
        return True

    prompt_id = int(raw_id)
    from_user = cq.get("from") or {}
    from_tid = int(from_user.get("id") or 0)

    prompt = await session.get(GroupBirthdayPrompt, prompt_id)
    if prompt is None:
        await telegram_answer_callback_query(qid, text="Запрос устарел.", show_alert=True)
        return True

    user_row = await session.execute(select(User).where(User.telegram_id == from_tid))
    user = user_row.scalar_one_or_none()
    if user is None:
        await telegram_answer_callback_query(qid, text="Нет доступа.", show_alert=True)
        return True

    recipient_row = await session.execute(
        select(GroupBirthdayPromptRecipient).where(
            GroupBirthdayPromptRecipient.prompt_id == prompt_id,
            GroupBirthdayPromptRecipient.user_id == user.id,
        ),
    )
    recipient = recipient_row.scalar_one_or_none()
    if recipient is None:
        await telegram_answer_callback_query(qid, text="Нет доступа.", show_alert=True)
        return True

    if action == "skip":
        recipient.skipped = True
        await session.flush()
        await telegram_answer_callback_query(qid, text="Пропущено.")
        if recipient.telegram_message_id is not None:
            await telegram_edit_message_reply_markup(from_tid, recipient.telegram_message_id, None)
        return True

    # action == "create"
    if prompt.state != "open":
        if prompt.claimed_by_user_id == user.id:
            await telegram_answer_callback_query(
                qid, text="Вы уже создаёте чат — добавьте бота в группу.", show_alert=False
            )
        else:
            await telegram_answer_callback_query(qid, text="Уже занято другим участником.", show_alert=True)
        return True

    target = await session.get(User, prompt.target_user_id)
    if target is None or target.birth_date is None:
        await telegram_answer_callback_query(qid, text="Именинник не найден.", show_alert=True)
        return True

    subscribers = await group_subscribers_for(
        session, group_id=prompt.group_id, target_user_id=prompt.target_user_id
    )
    count = len(subscribers)

    prompt.state = "claimed"
    prompt.claimed_by_user_id = user.id
    await session.flush()

    all_recipients_row = await session.execute(
        select(GroupBirthdayPromptRecipient).where(GroupBirthdayPromptRecipient.prompt_id == prompt_id),
    )
    claimer_name = html.escape(_display_name(user))
    for r in all_recipients_row.scalars().all():
        if r.telegram_message_id is None:
            continue
        r_user = await session.get(User, r.user_id)
        if r_user is None:
            continue
        if r.user_id == user.id:
            await telegram_edit_message_text(
                r_user.telegram_id, r.telegram_message_id, _instruction_text(count), reply_markup=None
            )
        else:
            await telegram_edit_message_text(
                r_user.telegram_id,
                r.telegram_message_id,
                f"Уже занято: чат создаёт {claimer_name}.",
                reply_markup=None,
            )

    await telegram_answer_callback_query(qid, text="Создайте группу и добавьте бота.")
    return True


async def handle_group_birthday_my_chat_member(session: AsyncSession, upd: dict) -> None:
    """Бот добавлен в новую Telegram-группу — экспортирует ссылку и рассылает подписчикам."""
    chat = upd.get("chat") or {}
    if chat.get("type") not in ("group", "supergroup"):
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
    if new_cm.get("status") not in active or old_cm.get("status") in active:
        return

    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    from_user = upd.get("from") or {}
    from_tid = int(from_user.get("id") or 0)
    if not from_tid:
        return

    user_row = await session.execute(select(User).where(User.telegram_id == from_tid))
    user = user_row.scalar_one_or_none()
    if user is None:
        return

    prompt_row = await session.execute(
        select(GroupBirthdayPrompt)
        .where(
            GroupBirthdayPrompt.state == "claimed",
            GroupBirthdayPrompt.claimed_by_user_id == user.id,
        )
        .order_by(GroupBirthdayPrompt.created_at.asc())
        .limit(1),
    )
    prompt = prompt_row.scalar_one_or_none()
    if prompt is None:
        logger.info("group_birthday my_chat_member: no claimed prompt for user_id=%s", user.id)
        return

    if await _event_exists(
        session,
        group_id=prompt.group_id,
        target_user_id=prompt.target_user_id,
        celebration_date=prompt.celebration_date,
    ):
        prompt.state = "completed"
        await session.flush()
        return

    link = await telegram_export_chat_invite_link(chat_id)
    if not link:
        await telegram_send_message(
            from_tid,
            "Не удалось получить ссылку-приглашение. Проверьте, что бот в группе и имеет права администратора.",
            parse_mode=None,
        )
        return

    session.add(
        GroupBirthdayEvent(
            group_id=prompt.group_id,
            target_user_id=prompt.target_user_id,
            celebration_date=prompt.celebration_date,
            telegram_chat_id=chat_id,
            invite_link=link,
        ),
    )
    prompt.state = "completed"
    await session.flush()

    subscribers = await group_subscribers_for(
        session, group_id=prompt.group_id, target_user_id=prompt.target_user_id
    )
    target = await session.get(User, prompt.target_user_id)
    name = html.escape(_display_name(target)) if target is not None else "именинника"
    safe_link = html.escape(link, quote=True)
    text = (
        f"🎁 Секретный чат для обсуждения подарка для <b>{name}</b> готов!\n"
        f'<a href="{safe_link}">{safe_link}</a>'
    )
    reply_markup = {"inline_keyboard": [[{"text": "Присоединиться к чату", "url": link}]]}

    sent = 0
    for sub in subscribers:
        if sub.is_blocked or not sub.is_bot_active:
            continue
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

    if sent:
        await telegram_send_message(from_tid, f"Готово: ссылка разослана {sent} подписчикам.", parse_mode=None)
    else:
        await telegram_send_message(
            from_tid,
            "Готово: чат создан, но подписчиков не оказалось — ссылку никто не получил.",
            parse_mode=None,
        )
