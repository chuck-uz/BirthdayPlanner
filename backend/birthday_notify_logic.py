"""Создание BirthdayEvent, рассылка подписчикам, тексты сообщений — общее для планировщика и POST подписки."""

from __future__ import annotations

import datetime as dt
import html
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from birthday_utils import days_until_next_birthday, next_birthday_date
from config import get_settings
from database import async_session_maker
from models import BirthdayEvent, Subscription, User
from telegram_service import telegram_send_message

logger = logging.getLogger(__name__)


def target_display_name(user: User) -> str:
    n = (user.full_name or "").strip()
    return n if n else f"Участник #{user.id}"


def message_gift_group_ready(target_name: str, invite_link: str) -> str:
    safe = html.escape(target_name)
    return (
        f"Группа для обсуждения подарка для <b>{safe}</b> готова! Присоединяйтесь:\n"
        f"{html.escape(invite_link)}"
    )


def _birthday_date_in_year(birth: dt.date, year: int) -> dt.date:
    """Календарный день рождения в указанном году (29 фев → 28 фев в невисокосные годы)."""
    try:
        return dt.date(year, birth.month, birth.day)
    except ValueError:
        return dt.date(year, 2, 28)


def subscription_confirmation_text(target: User) -> str:
    safe = html.escape(target_display_name(target))
    bd = target.birth_date
    if bd is None:
        return f"✅ Вы подписались на уведомления о дне рождения: <b>{safe}</b>."
    today = dt.date.today()
    celebration_this_year = _birthday_date_in_year(bd, today.year)
    d = html.escape(celebration_this_year.strftime("%d.%m.%Y"))
    return (
        f"✅ Вы подписались на уведомления о дне рождения: <b>{safe}</b>, "
        f"который будет <b>{d}</b>."
    )


async def get_birthday_event(
    session: AsyncSession,
    target_user_id: int,
    celebration_date: dt.date,
) -> BirthdayEvent | None:
    row = await session.execute(
        select(BirthdayEvent).where(
            BirthdayEvent.target_user_id == target_user_id,
            BirthdayEvent.celebration_date == celebration_date,
        ),
    )
    return row.scalar_one_or_none()


async def _load_subscriber_recipients(
    session: AsyncSession,
    target: User,
) -> list[User]:
    subs_rows = (
        await session.execute(
            select(Subscription, User)
            .join(User, Subscription.subscriber_id == User.id)
            .where(Subscription.target_user_id == target.id),
        )
    ).all()
    out: list[User] = []
    for _sub, subscriber in subs_rows:
        if subscriber.id == target.id:
            continue
        out.append(subscriber)
    return out


async def create_birthday_event_and_notify_subscribers(
    session: AsyncSession,
    target: User,
    *,
    today: dt.date | None = None,
    trigger_subscriber: User | None = None,
) -> BirthdayEvent | None:
    """
    Если событие на ближайшую дату ДР уже есть — вернуть его без рассылки.
    Группу боты создавать не умеют (Bot API это не поддерживает), поэтому её создаёт
    человек: подписчик, инициировавший событие, получает в личку просьбу создать группу
    и прислать ссылку — остальные подписчики узнают о ней уже готовой.
    """
    today = today or dt.date.today()
    assert target.birth_date is not None
    celebration = next_birthday_date(target.birth_date, today)

    existing = await get_birthday_event(session, target.id, celebration)
    if existing is not None:
        return existing

    if trigger_subscriber is not None:
        from birthday_admin_flow import ensure_admin_prompt_for_birthday

        await ensure_admin_prompt_for_birthday(
            session,
            target,
            today=today,
            trigger_subscriber=trigger_subscriber,
        )
        return None

    # Ежедневная задача без инициатора-подписчика: создать группу автоматически нельзя,
    # а просить некого. Событие останется без группы до следующей подписки.
    logger.info(
        "birthday event for target_user_id=%s has no subscriber to ask for a group; "
        "nothing sent automatically.",
        target.id,
    )
    return None


async def send_event_summary_to_telegram_user(
    telegram_user_id: int,
    target: User,
    event: BirthdayEvent,
) -> None:
    """Одному подписчику: только если есть рабочая ссылка (без текста «не удалось создать группу»)."""
    assert target.birth_date is not None
    name = target_display_name(target)
    if not event.invite_link or event.used_dm_fallback:
        return
    await telegram_send_message(telegram_user_id, message_gift_group_ready(name, event.invite_link))


async def run_subscribe_telegram_followup(
    session: AsyncSession,
    subscriber: User,
    target: User,
    *,
    was_new_subscription: bool,
) -> None:
    """После подписки: подтверждение в бот; дальше — окно BIRTHDAY_NOTIFY_DAYS_BEFORE: событие/ссылка
    или просьба подписчику создать группу самому."""
    if not was_new_subscription:
        return

    await telegram_send_message(subscriber.telegram_id, subscription_confirmation_text(target))

    settings = get_settings()
    window = settings.birthday_notify_days_before

    assert target.birth_date is not None
    today = dt.date.today()
    days = days_until_next_birthday(target.birth_date, today)
    if days < 0:
        return

    celebration = next_birthday_date(target.birth_date, today)
    event = await get_birthday_event(session, target.id, celebration)
    if event is not None:
        await send_event_summary_to_telegram_user(subscriber.telegram_id, target, event)
        return

    if days > window:
        return

    await create_birthday_event_and_notify_subscribers(
        session,
        target,
        today=today,
        trigger_subscriber=subscriber,
    )


async def run_subscribe_followup_task(subscriber_id: int, target_user_id: int) -> None:
    """Фоновая обёртка: открывает собственную сессию, не блокирует HTTP-ответ подписки.

    Запускается после коммита подписки (BackgroundTasks), поэтому строки уже в БД.
    """
    try:
        async with async_session_maker() as session:
            subscriber = await session.get(User, subscriber_id)
            target = await session.get(User, target_user_id)
            if subscriber is None or target is None:
                return
            await run_subscribe_telegram_followup(
                session,
                subscriber,
                target,
                was_new_subscription=True,
            )
            await session.commit()
    except Exception:
        logger.exception(
            "subscribe_followup_task failed subscriber_id=%s target_user_id=%s",
            subscriber_id,
            target_user_id,
        )
