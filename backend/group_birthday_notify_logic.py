"""Telegram-уведомления о ДР внутри приватных групп (по ролям).

Оба случая из спеки — "именинник обычный участник" и "именинник admin,
есть другие админы" — сведены к одному пути: получатели = все admin'ы
группы, кроме самого именинника. Если после вычитания получателей не
осталось (именинник — единственный admin), включается fallback: за
SINGLE_ADMIN_FALLBACK_LEAD_DAYS дней уведомляются все остальные участники.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from birthday_utils import days_until_next_birthday, next_birthday_date
from models import Group, GroupBirthdayNotification, GroupRole, User, UserGroup
from telegram_service import telegram_send_message

NotificationKind = Literal["notify_admins", "notify_members_fallback"]

# Единственный admin группы: за сколько дней предупредить остальных участников (фиксировано спекой).
SINGLE_ADMIN_FALLBACK_LEAD_DAYS = 7


@dataclass(frozen=True)
class GroupBirthdayPlan:
    group_id: int
    group_name: str
    birthday_user_id: int
    birthday_user_name: str
    celebration_date: dt.date
    days_left: int
    notification_kind: NotificationKind
    recipient_user_ids: tuple[int, ...]


def _display_name(user: User) -> str:
    return (user.full_name or "").strip() or f"Участник #{user.id}"


def plan_group_birthday_notifications(
    *,
    group: Group,
    memberships: list[UserGroup],
    birthday_user: User,
    today: dt.date,
    admin_lead_days: int,
) -> list[GroupBirthdayPlan]:
    """Выбирает получателей уведомления для одного именинника в одной группе."""
    if birthday_user.birth_date is None or birthday_user.is_blocked:
        return []

    birthday_membership = next((m for m in memberships if m.user_id == birthday_user.id), None)
    if birthday_membership is None:
        return []

    days_left = days_until_next_birthday(birthday_user.birth_date, today)
    celebration = next_birthday_date(birthday_user.birth_date, today)
    name = _display_name(birthday_user)

    admins = [m for m in memberships if m.role == GroupRole.admin.value]
    other_admins = [m for m in admins if m.user_id != birthday_user.id]

    if other_admins:
        if days_left != admin_lead_days:
            return []
        return [
            GroupBirthdayPlan(
                group_id=group.id,
                group_name=group.name,
                birthday_user_id=birthday_user.id,
                birthday_user_name=name,
                celebration_date=celebration,
                days_left=days_left,
                notification_kind="notify_admins",
                recipient_user_ids=tuple(m.user_id for m in other_admins),
            ),
        ]

    # Именинник — единственный admin группы: fallback всем остальным участникам.
    if days_left != SINGLE_ADMIN_FALLBACK_LEAD_DAYS:
        return []
    other_members = tuple(m.user_id for m in memberships if m.user_id != birthday_user.id)
    if not other_members:
        return []
    return [
        GroupBirthdayPlan(
            group_id=group.id,
            group_name=group.name,
            birthday_user_id=birthday_user.id,
            birthday_user_name=name,
            celebration_date=celebration,
            days_left=days_left,
            notification_kind="notify_members_fallback",
            recipient_user_ids=other_members,
        ),
    ]


def _message_for_plan(plan: GroupBirthdayPlan) -> str:
    if plan.notification_kind == "notify_admins":
        return (
            f"🎂 В группе <b>{plan.group_name}</b> через {plan.days_left} дн. "
            f"день рождения у <b>{plan.birthday_user_name}</b>.\n"
            "Организуйте подарок или создайте чат в Telegram."
        )
    return (
        f"🎂 В группе <b>{plan.group_name}</b> через {plan.days_left} дн. "
        f"день рождения у вашего единственного админа <b>{plan.birthday_user_name}</b>.\n"
        "Помогите организовать поздравление и подарок."
    )


async def _notification_already_sent(session: AsyncSession, plan: GroupBirthdayPlan) -> bool:
    result = await session.execute(
        select(GroupBirthdayNotification.id).where(
            GroupBirthdayNotification.group_id == plan.group_id,
            GroupBirthdayNotification.birthday_user_id == plan.birthday_user_id,
            GroupBirthdayNotification.celebration_date == plan.celebration_date,
            GroupBirthdayNotification.notification_kind == plan.notification_kind,
        ),
    )
    return result.scalar_one_or_none() is not None


async def _mark_notification_sent(session: AsyncSession, plan: GroupBirthdayPlan) -> None:
    session.add(
        GroupBirthdayNotification(
            group_id=plan.group_id,
            birthday_user_id=plan.birthday_user_id,
            celebration_date=plan.celebration_date,
            notification_kind=plan.notification_kind,
        ),
    )
    await session.flush()


async def send_plan(session: AsyncSession, plan: GroupBirthdayPlan) -> None:
    """Отправляет уведомление получателям плана, если ещё не отправлялось (idempotent)."""
    if await _notification_already_sent(session, plan):
        return

    result = await session.execute(select(User).where(User.id.in_(plan.recipient_user_ids)))
    recipients = list(result.scalars().all())
    text = _message_for_plan(plan)

    sent_any = False
    for recipient in recipients:
        if recipient.is_blocked or not recipient.is_bot_active:
            continue
        await telegram_send_message(recipient.telegram_id, text, parse_mode="HTML")
        sent_any = True

    if sent_any:
        await _mark_notification_sent(session, plan)
