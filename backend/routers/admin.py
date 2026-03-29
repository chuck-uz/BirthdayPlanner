from __future__ import annotations

import datetime as dt
import random
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from admin_access import get_current_admin
from database import get_db
from models import Subscription, User, Wishlist
from schemas.admin import (
    AdminCreateTestUsersIn,
    AdminUserDetailOut,
    AdminUserListItemOut,
    AdminUserPatch,
    build_admin_user_detail,
)
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
