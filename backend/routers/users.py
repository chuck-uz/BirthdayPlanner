from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from birthday_utils import days_until_next_birthday
from database import get_db
from deps import get_current_user
from models import User, Wishlist
from schemas.user import (
    UpcomingBirthdayOut,
    UserMeOut,
    UserProfileUpdate,
    UserPublicProfileOut,
    build_user_me_out,
)
from schemas.wishlist import WishlistCreate, WishlistItemOut

router = APIRouter(prefix="/api/users", tags=["users"])


def _public_profile_from_user(user: User) -> UserPublicProfileOut:
    wishlists = sorted(user.wishlists, key=lambda w: w.created_at, reverse=True)
    return UserPublicProfileOut(
        id=user.id,
        full_name=user.full_name,
        birth_date=user.birth_date,
        wishlists=[WishlistItemOut.model_validate(w) for w in wishlists],
    )


@router.get("/me", response_model=UserMeOut)
async def get_me(user: User = Depends(get_current_user)) -> UserMeOut:
    return build_user_me_out(user)


@router.get("/me/wishlists", response_model=list[WishlistItemOut])
async def list_my_wishlists(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> list[WishlistItemOut]:
    result = await session.execute(
        select(Wishlist)
        .where(Wishlist.user_id == user.id)
        .order_by(Wishlist.created_at.desc()),
    )
    rows = result.scalars().all()
    return [WishlistItemOut.model_validate(w) for w in rows]


@router.post("/me/wishlists", response_model=WishlistItemOut)
async def create_my_wishlist(
    body: WishlistCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> WishlistItemOut:
    if not body.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_title")
    w = Wishlist(user_id=user.id, title=body.title.strip())
    session.add(w)
    await session.flush()
    await session.refresh(w)
    return WishlistItemOut.model_validate(w)


@router.delete("/me/wishlists/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_wishlist(
    wishlist_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> Response:
    result = await session.execute(
        select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user.id),
    )
    w = result.scalar_one_or_none()
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await session.delete(w)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/birthdays/upcoming", response_model=list[UpcomingBirthdayOut])
async def upcoming_birthdays(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user),
) -> list[UpcomingBirthdayOut]:
    """Все пользователи с указанной датой рождения, по возрастанию дней до следующего ДР."""
    result = await session.execute(select(User).where(User.birth_date.is_not(None)))
    rows = result.scalars().all()
    items: list[UpcomingBirthdayOut] = []
    for u in rows:
        assert u.birth_date is not None
        d = days_until_next_birthday(u.birth_date)
        items.append(
            UpcomingBirthdayOut(
                user_id=u.id,
                full_name=u.full_name,
                birth_date=u.birth_date,
                days_until=d,
            )
        )
    items.sort(key=lambda x: (x.days_until, x.user_id))
    return items


@router.patch("/me", response_model=UserMeOut)
async def patch_me(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
) -> UserMeOut:
    user.full_name = body.full_name
    user.birth_date = body.birth_date
    return build_user_me_out(user)


@router.get("/{user_id}", response_model=UserPublicProfileOut)
async def get_user_public_profile(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: User = Depends(get_current_user),
) -> UserPublicProfileOut:
    """Профиль именинника и вишлист (для авторизованных пользователей)."""
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.wishlists)),
    )
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    return _public_profile_from_user(u)
