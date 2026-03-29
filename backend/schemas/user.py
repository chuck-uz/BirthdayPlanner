from __future__ import annotations

import datetime as dt
from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import get_settings
from models import User
from schemas.wishlist import WishlistItemOut


class UserPublicProfileOut(BaseModel):
    """Профиль участника для просмотра с вишлистом (без telegram_id)."""

    id: int
    full_name: str | None
    birth_date: dt.date | None
    wishlists: list[WishlistItemOut]


class UpcomingBirthdayOut(BaseModel):
    """Пользователь с заполненной датой рождения для списка на главной."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str | None
    birth_date: dt.date
    days_until: int
    subscribed: bool = False
    has_avatar: bool = False


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    full_name: str | None
    birth_date: dt.date | None
    is_profile_complete: bool
    has_avatar: bool = False
    avatar_url: str | None = None
    is_bot_active: bool = False
    is_admin: bool = False


def build_user_me_out(user: User) -> UserMeOut:
    name_ok = bool(user.full_name and user.full_name.strip())
    ap = getattr(user, "avatar_path", None)
    has_avatar = bool(ap and str(ap).strip())
    settings = get_settings()
    aid = settings.telegram_admin_id
    is_admin = aid is not None and int(user.telegram_id) == int(aid)
    return UserMeOut(
        id=user.id,
        telegram_id=user.telegram_id,
        full_name=user.full_name,
        birth_date=user.birth_date,
        is_profile_complete=name_ok and user.birth_date is not None,
        has_avatar=has_avatar,
        avatar_url=f"/api/users/{user.id}/avatar" if has_avatar else None,
        is_bot_active=bool(getattr(user, "is_bot_active", False)),
        is_admin=is_admin,
    )


class UserProfileUpdate(BaseModel):
    """Полное обновление обязательных полей профиля (завершение регистрации)."""

    full_name: str = Field(..., min_length=1, max_length=512)
    birth_date: dt.date

    @field_validator("full_name", mode="before")
    @classmethod
    def collapse_whitespace(cls, v: object) -> object:
        if isinstance(v, str):
            return " ".join(v.split()).strip()
        return v

    @field_validator("full_name")
    @classmethod
    def fio_at_least_two_words(cls, v: str) -> str:
        parts = [p for p in v.split(" ") if p]
        if len(parts) < 2:
            raise ValueError("Укажите фамилию и имя (минимум два слова)")
        if len(v) < 4:
            raise ValueError("ФИО слишком короткое")
        return v

    @field_validator("birth_date")
    @classmethod
    def birth_date_plausible(cls, v: dt.date) -> dt.date:
        today = dt.date.today()
        if v > today:
            raise ValueError("Дата рождения не может быть в будущем")
        oldest = today.replace(year=today.year - 120)
        if v < oldest:
            raise ValueError("Некорректная дата рождения")
        return v
