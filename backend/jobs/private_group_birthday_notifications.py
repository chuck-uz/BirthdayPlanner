"""Ежедневный запуск flow "создать чат" по ДР участников приватных групп."""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from birthday_utils import days_until_next_birthday
from database import async_session_maker
from group_birthday_notify_logic import plan_group_birthday_prompt, send_group_birthday_prompt
from models import Group, UserGroup
from services.private_groups import group_subscribers_for

logger = logging.getLogger(__name__)


async def run_private_group_birthday_notifications(today: dt.date | None = None) -> None:
    today = today or dt.date.today()

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
            if birthday_user.birth_date is None or birthday_user.is_blocked:
                continue
            if days_until_next_birthday(birthday_user.birth_date, today) != group.notify_lead_days:
                continue
            try:
                async with async_session_maker() as session:
                    has_subscribers = bool(
                        await group_subscribers_for(
                            session, group_id=group.id, target_user_id=birthday_user.id
                        ),
                    )
                    candidate = plan_group_birthday_prompt(
                        group=group,
                        memberships=memberships,
                        birthday_user=birthday_user,
                        today=today,
                        has_subscribers=has_subscribers,
                    )
                    if candidate is not None:
                        await send_group_birthday_prompt(session, candidate)
                    await session.commit()
            except Exception:
                logger.exception(
                    "private_group_birthday_prompt failed group_id=%s user_id=%s",
                    group.id,
                    birthday_user.id,
                )
