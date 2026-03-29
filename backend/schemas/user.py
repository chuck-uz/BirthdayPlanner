from __future__ import annotations

import datetime as dt
from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import User


class UserMeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    full_name: str | None
    birth_date: dt.date | None
    is_profile_complete: bool


def build_user_me_out(user: User) -> UserMeOut:
    name_ok = bool(user.full_name and user.full_name.strip())
    return UserMeOut(
        id=user.id,
        telegram_id=user.telegram_id,
        full_name=user.full_name,
        birth_date=user.birth_date,
        is_profile_complete=name_ok and user.birth_date is not None,
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
