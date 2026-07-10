"""Выдача фото элементов вишлиста только по JWT (без StaticFiles)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models import User, Wishlist
from storage.image_store import ImageStore, wishlist_store

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
    if owner is not None and owner.is_blocked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    try:
        path = wishlist_store.filesystem_path(item.photo_path)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="wishlist_photo_not_found",
        ) from None
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    return FileResponse(
        path,
        media_type=ImageStore.media_type(item.photo_path),
        filename=path.name,
        headers={"Cache-Control": "private, max-age=3600"},
    )
