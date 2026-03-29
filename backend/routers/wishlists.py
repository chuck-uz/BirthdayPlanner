"""Выдача фото элементов вишлиста только по JWT (без StaticFiles)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin_access import user_is_app_admin
from database import get_db
from deps import get_current_user
from models import User, Wishlist
from wishlist_storage import filesystem_path_for_stored, media_type_for_stored

router = APIRouter(prefix="/api/wishlists", tags=["wishlists"])


@router.get("/{item_id}/photo")
async def get_wishlist_item_photo(
    item_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    viewer: User = Depends(get_current_user),
) -> FileResponse:
    result = await session.execute(select(Wishlist).where(Wishlist.id == item_id))
    item = result.scalar_one_or_none()
    if item is None or not (item.photo_path and str(item.photo_path).strip()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    owner = await session.get(User, item.user_id)
    if owner is not None and bool(getattr(owner, "is_blocked", False)) and not user_is_app_admin(viewer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    try:
        path = filesystem_path_for_stored(item.photo_path)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="wishlist_photo_not_found",
        ) from None
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    return FileResponse(
        path,
        media_type=media_type_for_stored(item.photo_path),
        filename=path.name,
    )
