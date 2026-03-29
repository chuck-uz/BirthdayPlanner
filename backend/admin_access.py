"""Доступ к панели администратора: тот же Telegram ID, что и TELEGRAM_ADMIN_ID (бот)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from config import get_settings
from deps import get_current_user
from models import User


def user_is_app_admin(user: User) -> bool:
    aid = get_settings().telegram_admin_id
    return aid is not None and int(user.telegram_id) == int(aid)


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user_is_app_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin_required",
        )
    return user
