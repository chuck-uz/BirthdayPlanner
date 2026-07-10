"""Ежедневная рассылка по ДР участников приватных групп."""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import get_settings
from database import async_session_maker
from group_birthday_notify_logic import plan_group_birthday_notifications, send_plan
from models import Group, UserGroup

logger = logging.getLogger(__name__)


async def run_private_group_birthday_notifications(today: dt.date | None = None) -> None:
    today = today or dt.date.today()
    settings = get_settings()
    admin_lead_days = settings.group_birthday_notify_days_before

    async with async_session_maker() as session:
        groups_result = await session.execute(
            select(Group).options(
                selectinload(Group.memberships).selectinload(UserGroup.user),
            ),
        )
        groups = list(groups_result.scalars().unique().all())

    for group in groups:
        memberships = list(group.memberships)
        birthday_users = {m.user_id: m.user for m in memberships if m.user is not None}
        for birthday_user in birthday_users.values():
            plans = plan_group_birthday_notifications(
                group=group,
                memberships=memberships,
                birthday_user=birthday_user,
                today=today,
                admin_lead_days=admin_lead_days,
            )
            for plan in plans:
                try:
                    async with async_session_maker() as session:
                        await send_plan(session, plan)
                        await session.commit()
                except Exception:
                    logger.exception(
                        "private_group_birthday_notify failed group_id=%s user_id=%s kind=%s",
                        plan.group_id,
                        plan.birthday_user_id,
                        plan.notification_kind,
                    )
