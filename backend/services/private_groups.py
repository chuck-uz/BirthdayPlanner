"""Бизнес-логика приватных групп (invite-ссылки, роли admin/member)."""

from __future__ import annotations

import datetime as dt
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from birthday_utils import days_until_next_birthday
from models import Group, GroupInvite, GroupRole, User, UserGroup


class PrivateGroupError(Exception):
    """Базовая ошибка домена приватных групп."""

    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        self.message = message or code
        super().__init__(self.message)


def generate_invite_token() -> str:
    """Криптостойкий токен для invite-ссылки (URL-safe)."""
    return secrets.token_urlsafe(32)


async def _get_membership(
    session: AsyncSession,
    *,
    group_id: int,
    user_id: int,
) -> UserGroup | None:
    result = await session.execute(
        select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def _require_membership(
    session: AsyncSession,
    *,
    group_id: int,
    user_id: int,
) -> UserGroup:
    membership = await _get_membership(session, group_id=group_id, user_id=user_id)
    if membership is None:
        raise PrivateGroupError("not_a_member", "User is not a member of this group")
    return membership


async def _require_admin_membership(
    session: AsyncSession,
    *,
    group_id: int,
    user_id: int,
) -> UserGroup:
    membership = await _require_membership(session, group_id=group_id, user_id=user_id)
    if membership.role != GroupRole.admin.value:
        raise PrivateGroupError("admin_required", "Admin role required")
    return membership


async def get_active_invite(session: AsyncSession, *, group_id: int) -> GroupInvite | None:
    result = await session.execute(
        select(GroupInvite).where(
            GroupInvite.group_id == group_id,
            GroupInvite.revoked_at.is_(None),
        ),
    )
    return result.scalar_one_or_none()


async def create_group(
    session: AsyncSession,
    *,
    creator: User,
    name: str,
) -> tuple[Group, UserGroup, GroupInvite]:
    """Создаёт группу, первую invite-ссылку и добавляет создателя как admin."""
    trimmed = name.strip()
    if not trimmed:
        raise PrivateGroupError("invalid_name", "Group name is required")

    group = Group(name=trimmed)
    session.add(group)
    await session.flush()

    invite = GroupInvite(group_id=group.id, token=generate_invite_token())
    session.add(invite)

    membership = UserGroup(
        user_id=creator.id,
        group_id=group.id,
        role=GroupRole.admin.value,
    )
    session.add(membership)
    await session.flush()
    return group, membership, invite


async def join_group_by_invite_token(
    session: AsyncSession,
    *,
    user: User,
    invite_token: str,
) -> tuple[Group, UserGroup]:
    """Вступление по активному invite_token; повторный join возвращает существующую связь."""
    token = invite_token.strip()
    if not token:
        raise PrivateGroupError("invalid_token", "Invite token is required")

    result = await session.execute(
        select(GroupInvite).where(
            GroupInvite.token == token,
            GroupInvite.revoked_at.is_(None),
        ),
    )
    invite = result.scalar_one_or_none()
    if invite is None:
        raise PrivateGroupError("group_not_found", "Invalid or expired invite link")

    group = await session.get(Group, invite.group_id)
    if group is None:
        raise PrivateGroupError("group_not_found", "Invalid or expired invite link")

    existing = await _get_membership(session, group_id=group.id, user_id=user.id)
    if existing is not None:
        return group, existing

    membership = UserGroup(
        user_id=user.id,
        group_id=group.id,
        role=GroupRole.member.value,
    )
    session.add(membership)
    await session.flush()
    return group, membership


async def regenerate_invite_token(
    session: AsyncSession,
    *,
    group_id: int,
    actor: User,
) -> GroupInvite:
    """Только admin группы может перевыпустить invite_token; старая ссылка мягко отзывается."""
    await _require_admin_membership(session, group_id=group_id, user_id=actor.id)

    old_invite = await get_active_invite(session, group_id=group_id)
    if old_invite is not None:
        old_invite.revoked_at = dt.datetime.utcnow()

    new_invite = GroupInvite(group_id=group_id, token=generate_invite_token())
    session.add(new_invite)
    await session.flush()
    return new_invite


async def promote_member_to_admin(
    session: AsyncSession,
    *,
    group_id: int,
    actor: User,
    target_user_id: int,
) -> UserGroup:
    """Admin повышает участника той же группы до admin; идемпотентно, если уже admin."""
    await _require_admin_membership(session, group_id=group_id, user_id=actor.id)

    target = await _get_membership(session, group_id=group_id, user_id=target_user_id)
    if target is None:
        raise PrivateGroupError("target_not_member", "Target user is not in this group")
    if target.role != GroupRole.admin.value:
        target.role = GroupRole.admin.value
        await session.flush()
    return target


async def update_group_settings(
    session: AsyncSession,
    *,
    group_id: int,
    actor: User,
    invite_visible_to_members: bool,
) -> Group:
    """Только admin может менять настройки группы (видимость инвайт-ссылки участникам)."""
    await _require_admin_membership(session, group_id=group_id, user_id=actor.id)

    group = await session.get(Group, group_id)
    if group is None:
        raise PrivateGroupError("group_not_found", "Group not found")

    group.invite_visible_to_members = invite_visible_to_members
    await session.flush()
    return group


async def list_user_groups(
    session: AsyncSession,
    *,
    user: User,
) -> list[tuple[Group, UserGroup, int, GroupInvite | None]]:
    """Группы пользователя с числом участников и активной invite-ссылкой."""
    result = await session.execute(
        select(Group, UserGroup)
        .join(UserGroup, UserGroup.group_id == Group.id)
        .where(UserGroup.user_id == user.id)
        .order_by(Group.created_at.desc()),
    )
    rows = result.all()
    out: list[tuple[Group, UserGroup, int, GroupInvite | None]] = []
    for group, membership in rows:
        count_result = await session.scalar(
            select(func.count()).select_from(UserGroup).where(UserGroup.group_id == group.id),
        )
        invite = await get_active_invite(session, group_id=group.id)
        out.append((group, membership, int(count_result or 0), invite))
    return out


async def get_group_detail(
    session: AsyncSession,
    *,
    group_id: int,
    user: User,
) -> tuple[Group, UserGroup, list[UserGroup], GroupInvite | None]:
    """Детали группы для участника (с членами и активной invite-ссылкой)."""
    membership = await _require_membership(session, group_id=group_id, user_id=user.id)

    result = await session.execute(
        select(Group)
        .where(Group.id == group_id)
        .options(selectinload(Group.memberships).selectinload(UserGroup.user)),
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise PrivateGroupError("group_not_found", "Group not found")

    members = sorted(group.memberships, key=lambda m: m.joined_at)
    invite = await get_active_invite(session, group_id=group_id)
    return group, membership, members, invite


async def list_group_birthdays(
    session: AsyncSession,
    *,
    user: User,
    today: dt.date | None = None,
) -> list[tuple[Group, list[tuple[User, int]]]]:
    """Группы пользователя с участниками (кроме него самого) с датой рождения,
    отсортированными по близости; группы без ни одной подходящей даты не включаются,
    сами секции отсортированы по самому близкому ДР внутри группы."""
    today = today or dt.date.today()

    result = await session.execute(
        select(Group)
        .join(UserGroup, UserGroup.group_id == Group.id)
        .where(UserGroup.user_id == user.id)
        .options(selectinload(Group.memberships).selectinload(UserGroup.user)),
    )
    groups = list(result.scalars().unique().all())

    sections: list[tuple[Group, list[tuple[User, int]]]] = []
    for group in groups:
        members: list[tuple[User, int]] = []
        for membership in group.memberships:
            member = membership.user
            if member is None or member.id == user.id:
                continue
            if member.birth_date is None or member.is_blocked:
                continue
            members.append((member, days_until_next_birthday(member.birth_date, today)))
        if not members:
            continue
        members.sort(key=lambda pair: (pair[1], pair[0].id))
        sections.append((group, members))

    sections.sort(key=lambda pair: (pair[1][0][1], pair[0].id))
    return sections
