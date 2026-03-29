from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from schemas.wishlist import WishlistItemOut, build_wishlist_item_out


class AdminUserListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    full_name: str | None
    birth_date: dt.date | None
    is_blocked: bool
    is_test: bool
    is_profile_complete: bool
    has_avatar: bool
    is_bot_active: bool
    created_at: dt.datetime


class AdminUserDetailOut(BaseModel):
    id: int
    telegram_id: int
    full_name: str | None
    birth_date: dt.date | None
    is_blocked: bool
    is_test: bool
    is_profile_complete: bool
    has_avatar: bool
    is_bot_active: bool
    created_at: dt.datetime
    wishlists: list[WishlistItemOut]
    subscribers_count: int
    subscribing_count: int


def build_admin_user_detail(
    user: object,
    *,
    subscribers_count: int,
    subscribing_count: int,
) -> AdminUserDetailOut:
    wishlists = sorted(getattr(user, "wishlists", []), key=lambda w: w.created_at, reverse=True)
    name_ok = bool(user.full_name and str(user.full_name).strip())
    ap = getattr(user, "avatar_path", None)
    has_avatar = bool(ap and str(ap).strip())
    return AdminUserDetailOut(
        id=user.id,
        telegram_id=user.telegram_id,
        full_name=user.full_name,
        birth_date=user.birth_date,
        is_blocked=bool(getattr(user, "is_blocked", False)),
        is_test=bool(getattr(user, "is_test", False)),
        is_profile_complete=name_ok and user.birth_date is not None,
        has_avatar=has_avatar,
        is_bot_active=bool(getattr(user, "is_bot_active", False)),
        created_at=user.created_at,
        wishlists=[build_wishlist_item_out(w) for w in wishlists],
        subscribers_count=subscribers_count,
        subscribing_count=subscribing_count,
    )


class AdminCreateTestUsersIn(BaseModel):
    """Создание одного или нескольких тестовых пользователей (только админ API)."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(default=1, ge=1, le=20)


class AdminDeleteAllTestUsersOut(BaseModel):
    deleted_count: int


class AdminBirthdayDashboardItemOut(BaseModel):
    id: int
    full_name: str | None
    birth_date: dt.date
    subscribers_count: int
    days_until_birthday: int
    celebration_date: dt.date
    status: str
    is_sent: bool


class AdminBroadcastLinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_user_id: int = Field(..., ge=1)
    group_link: str = Field(..., min_length=10, max_length=2048)

    @field_validator("group_link")
    @classmethod
    def validate_group_link(cls, v: str) -> str:
        link = v.strip()
        if not link.startswith("https://t.me/"):
            raise ValueError("Ссылка должна начинаться с https://t.me/")
        return link


class AdminBroadcastLinkOut(BaseModel):
    target_user_id: int
    sent_count: int
    skipped_count: int
    celebration_date: dt.date


class AdminUserPatch(BaseModel):
    """Частичное обновление пользователя администратором."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    birth_date: dt.date | None = None
    is_blocked: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> AdminUserPatch:
        if self.full_name is None and self.birth_date is None and self.is_blocked is None:
            raise ValueError("Нужно указать хотя бы одно поле")
        return self

    @field_validator("full_name", mode="before")
    @classmethod
    def collapse_full_name(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str):
            s = " ".join(v.split()).strip()
            return s or None
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_two_words(cls, v: str | None) -> str | None:
        if v is None:
            return None
        parts = [p for p in v.split(" ") if p]
        if len(parts) < 2:
            raise ValueError("ФИО: минимум два слова (фамилия и имя)")
        if len(v) < 4:
            raise ValueError("ФИО слишком короткое")
        return v

    @field_validator("birth_date")
    @classmethod
    def birth_date_plausible(cls, v: dt.date | None) -> dt.date | None:
        if v is None:
            return None
        today = dt.date.today()
        if v > today:
            raise ValueError("Дата рождения не может быть в будущем")
        oldest = today.replace(year=today.year - 120)
        if v < oldest:
            raise ValueError("Некорректная дата рождения")
        return v
