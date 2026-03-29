from __future__ import annotations

import asyncio
import datetime as dt
import html
import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin_access import get_admin_user, get_current_admin
from birthday_utils import days_until_next_birthday, next_birthday_date
from database import get_db
from models import BirthdayEvent, Subscription, User, Wishlist
from schemas.admin import (
    AdminBirthdayDashboardItemOut,
    AdminBroadcastLinkIn,
    AdminBroadcastLinkOut,
    AdminCreateTestUsersIn,
    AdminUserDetailOut,
    AdminUserListItemOut,
    AdminUserPatch,
    build_admin_user_detail,
)
from telegram_service import telegram_send_message
from wishlist_storage import delete_wishlist_file_if_exists

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Синтетические telegram_id для тестовых записей (вне диапазона реальных аккаунтов)
_TEST_TELEGRAM_ID_BASE = 9_000_000_000_000_000


def _random_birth_date() -> dt.date:
    today = dt.date.today()
    delta_days = random.randint(20 * 365 + 30, 50 * 365)
    return today - dt.timedelta(days=delta_days)


async def _next_synthetic_telegram_id(session: AsyncSession) -> int:
    r = await session.execute(
        select(func.max(User.telegram_id)).where(User.telegram_id >= _TEST_TELEGRAM_ID_BASE),
    )
    m = r.scalar_one_or_none()
    if m is None:
        return _TEST_TELEGRAM_ID_BASE
    return int(m) + 1


def _list_item_from_user(u: User) -> AdminUserListItemOut:
    name_ok = bool(u.full_name and str(u.full_name).strip())
    ap = getattr(u, "avatar_path", None)
    has_avatar = bool(ap and str(ap).strip())
    return AdminUserListItemOut(
        id=u.id,
        telegram_id=u.telegram_id,
        full_name=u.full_name,
        birth_date=u.birth_date,
        is_blocked=bool(getattr(u, "is_blocked", False)),
        is_test=bool(getattr(u, "is_test", False)),
        is_profile_complete=name_ok and u.birth_date is not None,
        has_avatar=has_avatar,
        is_bot_active=bool(getattr(u, "is_bot_active", False)),
        created_at=u.created_at,
    )


@router.get("/users", response_model=list[AdminUserListItemOut])
async def admin_list_users(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_admin),
) -> list[AdminUserListItemOut]:
    result = await session.execute(select(User).order_by(User.id.desc()))
    rows = result.scalars().all()
    return [_list_item_from_user(u) for u in rows]


@router.post("/users/test", response_model=list[AdminUserListItemOut])
async def admin_create_test_users(
    body: AdminCreateTestUsersIn,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_admin),
) -> list[AdminUserListItemOut]:
    """Тестовые пользователи: синтетический telegram_id, не входят через Telegram Login."""
    created: list[AdminUserListItemOut] = []
    for _ in range(body.count):
        tid = await _next_synthetic_telegram_id(session)
        u = User(
            telegram_id=tid,
            full_name=f"Тестовый Пользователь {tid % 1_000_000}",
            birth_date=_random_birth_date(),
            is_test=True,
            is_bot_active=False,
            is_blocked=False,
        )
        session.add(u)
        await session.flush()
        created.append(_list_item_from_user(u))
    return created


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
async def admin_get_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_admin),
) -> AdminUserDetailOut:
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.wishlists)),
    )
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    sub_to = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.target_user_id == user_id),
    )
    sub_from = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.subscriber_id == user_id),
    )
    return build_admin_user_detail(
        u,
        subscribers_count=int(sub_to or 0),
        subscribing_count=int(sub_from or 0),
    )


@router.patch("/users/{user_id}", response_model=AdminUserDetailOut)
async def admin_patch_user(
    user_id: int,
    body: AdminUserPatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    admin: User = Depends(get_current_admin),
) -> AdminUserDetailOut:
    if body.is_blocked is True and user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cannot_block_self",
        )
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.wishlists)),
    )
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    if body.full_name is not None:
        u.full_name = body.full_name
    if body.birth_date is not None:
        u.birth_date = body.birth_date
    if body.is_blocked is not None:
        u.is_blocked = body.is_blocked
    await session.flush()
    await session.refresh(u)
    sub_to = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.target_user_id == user_id),
    )
    sub_from = await session.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.subscriber_id == user_id),
    )
    return build_admin_user_detail(
        u,
        subscribers_count=int(sub_to or 0),
        subscribing_count=int(sub_from or 0),
    )


@router.delete("/users/{user_id}/wishlists/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user_wishlist(
    user_id: int,
    wishlist_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_admin),
) -> Response:
    result = await session.execute(
        select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id),
    )
    w = result.scalar_one_or_none()
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    delete_wishlist_file_if_exists(w.photo_path)
    await session.delete(w)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/birthdays", response_model=list[AdminBirthdayDashboardItemOut])
async def admin_birthdays_dashboard(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_admin_user),
) -> list[AdminBirthdayDashboardItemOut]:
    today = dt.date.today()
    result = await session.execute(select(User).where(User.birth_date.is_not(None), User.is_blocked.is_(False)))
    users = list(result.scalars().all())
    rows: list[AdminBirthdayDashboardItemOut] = []
    for user in users:
        assert user.birth_date is not None
        celebration = next_birthday_date(user.birth_date, today)
        subs = await session.scalar(
            select(func.count()).select_from(Subscription).where(Subscription.target_user_id == user.id),
        )
        event = await session.scalar(
            select(BirthdayEvent).where(
                BirthdayEvent.target_user_id == user.id,
                BirthdayEvent.celebration_date == celebration,
            ),
        )
        is_sent = event is not None and bool(event.invite_link)
        rows.append(
            AdminBirthdayDashboardItemOut(
                id=user.id,
                full_name=user.full_name,
                birth_date=user.birth_date,
                subscribers_count=int(subs or 0),
                days_until_birthday=days_until_next_birthday(user.birth_date, today),
                celebration_date=celebration,
                status="Отправлено" if is_sent else "Не отправлено",
                is_sent=is_sent,
            ),
        )
    rows.sort(key=lambda x: (x.days_until_birthday, (x.full_name or "").lower(), x.id))
    return rows


@router.post("/broadcast-link", response_model=AdminBroadcastLinkOut)
async def admin_broadcast_group_link(
    body: AdminBroadcastLinkIn,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_admin_user),
) -> AdminBroadcastLinkOut:
    target = await session.get(User, body.target_user_id)
    if target is None or target.birth_date is None or bool(getattr(target, "is_blocked", False)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

    recipients = (
        await session.execute(
            select(User)
            .join(Subscription, Subscription.subscriber_id == User.id)
            .where(Subscription.target_user_id == target.id),
        )
    ).scalars().all()

    sent = 0
    skipped = 0
    safe_name = html.escape((target.full_name or "").strip() or f"Участник #{target.id}")
    text = (
        f"🎁 Секретный чат для обсуждения подарка для <b>{safe_name}</b> готов! "
        f"Присоединяйтесь: <a href=\"{html.escape(body.group_link, quote=True)}\">ссылка на группу</a>"
    )
    reply_markup = {"inline_keyboard": [[{"text": "Присоединиться к чату", "url": body.group_link}]]}

    for sub in recipients:
        if sub.id == target.id or bool(getattr(sub, "is_blocked", False)):
            skipped += 1
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
        else:
            skipped += 1
        await asyncio.sleep(0.05)

    celebration = next_birthday_date(target.birth_date, dt.date.today())
    existing_event = await session.scalar(
        select(BirthdayEvent).where(
            BirthdayEvent.target_user_id == target.id,
            BirthdayEvent.celebration_date == celebration,
        ),
    )
    if existing_event is None:
        session.add(
            BirthdayEvent(
                target_user_id=target.id,
                celebration_date=celebration,
                telegram_chat_id=None,
                invite_link=body.group_link,
                used_dm_fallback=False,
            ),
        )
    else:
        existing_event.invite_link = body.group_link
        existing_event.used_dm_fallback = False
    await session.flush()

    return AdminBroadcastLinkOut(
        target_user_id=target.id,
        sent_count=sent,
        skipped_count=skipped,
        celebration_date=celebration,
    )
