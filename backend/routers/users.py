from __future__ import annotations

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from deps import get_current_user
from models import User, Wishlist
from pydantic import ValidationError
from schemas.group_subscription import GroupSubscriptionStateOut
from schemas.user import (
    TelegramDeliveryOut,
    UserMeOut,
    UserProfileUpdate,
    UserPublicProfileOut,
    build_user_me_out,
)
from schemas.wishlist import WishlistItemOut, build_wishlist_item_out, parse_optional_link_url
from ratelimit import limiter
from services.private_groups import (
    PrivateGroupError,
    subscribe_to_member,
    subscription_state,
    unsubscribe_from_member,
)
from storage.image_store import ImageStore, avatar_store, wishlist_store
from telegram_service import get_bot_username, telegram_user_can_receive_bot_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


def _public_profile_from_user(user: User) -> UserPublicProfileOut:
    wishlists = sorted(user.wishlists, key=lambda w: w.created_at, reverse=True)
    return UserPublicProfileOut(
        id=user.id,
        full_name=user.full_name,
        birth_date=user.birth_date,
        wishlists=[build_wishlist_item_out(w) for w in wishlists],
    )


@router.get("/me", response_model=UserMeOut)
async def get_me(user: User = Depends(get_current_user)) -> UserMeOut:
    return build_user_me_out(user)


@router.get("/me/telegram-delivery", response_model=TelegramDeliveryOut)
async def my_telegram_delivery(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> TelegramDeliveryOut:
    can = await telegram_user_can_receive_bot_messages(user.telegram_id)
    if can and not user.is_bot_active:
        user.is_bot_active = True
    bot = await get_bot_username()
    return TelegramDeliveryOut(can_receive_bot_messages=can, bot_username=bot)


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
    return [build_wishlist_item_out(w) for w in rows]


def _normalize_description(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    return s or None


@router.post("/me/wishlists", response_model=WishlistItemOut)
@limiter.limit("30/minute")
async def create_my_wishlist(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
    title: str = Form(...),
    description: str | None = Form(None),
    link_url: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> WishlistItemOut:
    t = title.strip()
    if not t:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_title")
    try:
        link = parse_optional_link_url(link_url)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_link_url",
        ) from None
    desc = _normalize_description(description)
    photo_rel: str | None = None
    if file is not None and (file.filename or "").strip():
        photo_rel = await wishlist_store.store_upload(file)
    w = Wishlist(
        user_id=user.id,
        title=t,
        description=desc,
        link_url=link,
        photo_path=photo_rel,
    )
    session.add(w)
    await session.flush()
    await session.refresh(w)
    return build_wishlist_item_out(w)


@router.patch("/me/wishlists/{wishlist_id}", response_model=WishlistItemOut)
async def patch_my_wishlist(
    wishlist_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
    title: str = Form(...),
    description: str | None = Form(None),
    link_url: str | None = Form(None),
    file: UploadFile | None = File(None),
    clear_photo: bool = Form(False),
) -> WishlistItemOut:
    result = await session.execute(
        select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user.id),
    )
    w = result.scalar_one_or_none()
    if w is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    t = title.strip()
    if not t:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_title")
    try:
        link = parse_optional_link_url(link_url)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_link_url",
        ) from None
    w.title = t
    w.description = _normalize_description(description)
    w.link_url = link
    if clear_photo:
        wishlist_store.delete_if_exists(w.photo_path)
        w.photo_path = None
    if file is not None and (file.filename or "").strip():
        old_photo = w.photo_path
        w.photo_path = await wishlist_store.store_upload(file)
        wishlist_store.delete_if_exists(old_photo)
    await session.flush()
    await session.refresh(w)
    return build_wishlist_item_out(w)


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
    wishlist_store.delete_if_exists(w.photo_path)
    await session.delete(w)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{target_user_id}/group-subscription", response_model=GroupSubscriptionStateOut)
async def get_group_subscription_status(
    target_user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupSubscriptionStateOut:
    subscribed, can_subscribe = await subscription_state(
        session, subscriber_id=user.id, target_user_id=target_user_id
    )
    return GroupSubscriptionStateOut(subscribed=subscribed, can_subscribe=can_subscribe)


@router.post("/{target_user_id}/group-subscription", response_model=GroupSubscriptionStateOut)
@limiter.limit("30/minute")
async def create_group_subscription(
    request: Request,
    target_user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> GroupSubscriptionStateOut:
    if target_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot_subscribe_to_self")
    try:
        await subscribe_to_member(session, subscriber=user, target_user_id=target_user_id)
    except PrivateGroupError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.code == "no_shared_group" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=exc.code) from exc
    return GroupSubscriptionStateOut(subscribed=True, can_subscribe=True)


@router.delete("/{target_user_id}/group-subscription", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_subscription(
    target_user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> Response:
    await unsubscribe_from_member(session, subscriber=user, target_user_id=target_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/me", response_model=UserMeOut)
async def patch_me(
    body: UserProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
) -> UserMeOut:
    user.full_name = body.full_name
    user.birth_date = body.birth_date
    await session.flush()
    return build_user_me_out(user)


@router.patch("/me/avatar", response_model=UserMeOut)
@limiter.limit("15/minute")
async def patch_my_avatar(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> UserMeOut:
    old_path = user.avatar_path
    rel = await avatar_store.store_upload(file)
    user.avatar_path = rel
    await session.flush()
    if old_path and old_path != rel:
        avatar_store.delete_if_exists(old_path)
    return build_user_me_out(user)


@router.get("/{user_id}/avatar")
async def get_user_avatar(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    viewer: User = Depends(get_current_user),
) -> FileResponse:
    target = await session.get(User, user_id)
    if target is None or not (target.avatar_path and str(target.avatar_path).strip()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found")
    if target.is_blocked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found")
    try:
        path = avatar_store.filesystem_path(target.avatar_path)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found") from None
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found")
    return FileResponse(
        path,
        media_type=ImageStore.media_type(target.avatar_path),
        filename=path.name,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/{user_id}", response_model=UserPublicProfileOut)
async def get_user_public_profile(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    viewer: User = Depends(get_current_user),
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
    if bool(getattr(u, "is_blocked", False)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    return _public_profile_from_user(u)
