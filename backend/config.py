from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )

    bot_token: str = Field(..., min_length=1, alias="BOT_TOKEN")
    jwt_secret_key: str = Field(..., min_length=1, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, alias="JWT_EXPIRE_MINUTES")

    telegram_auth_max_age_seconds: int = Field(
        default=86400,
        alias="TELEGRAM_AUTH_MAX_AGE_SECONDS",
    )

    jwt_cookie_name: str = Field(default="access_token", alias="JWT_COOKIE_NAME")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="lax", alias="COOKIE_SAMESITE")

    # Разрешённые Origin для CORS (через запятую или JSON-массив в CORS_ALLOW_ORIGINS).
    # NoDecode: иначе pydantic-settings пытается json.loads до валидатора и падает на
    # обычной строке вида https://example.com (типично для DockHost/env без JSON).
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://127.0.0.1",
            "http://localhost",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5173",
            "http://localhost:5174",
        ],
        alias="CORS_ALLOW_ORIGINS",
    )

    # Редирект после Telegram Login, если параметр next потерян или не прошёл проверку
    frontend_default_url: str = Field(
        default="http://127.0.0.1/",
        alias="FRONTEND_DEFAULT_URL",
    )

    # За сколько дней до ДР запускать рассылку подписчикам (и попытку «группы»)
    birthday_notify_days_before: int = Field(default=14, alias="BIRTHDAY_NOTIFY_DAYS_BEFORE", ge=1, le=90)

    # Часовой пояс ежедневной проверки (09:00)
    scheduler_timezone: str = Field(default="Europe/Moscow", alias="SCHEDULER_TIMEZONE")

    # Telegram user id админа: кнопки бота + веб-панель /admin (PATCH блокировка, список пользователей)
    telegram_admin_id: int | None = Field(default=None, alias="TELEGRAM_ADMIN_ID")

    # Вебхук: секрет в заголовке X-Telegram-Bot-Api-Secret-Token (рекомендуется в проде)
    telegram_webhook_secret: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET")

    # Публичный HTTPS URL без хвоста, например https://example.com — при старте вызовется setWebhook на …/api/telegram/webhook
    telegram_webhook_base_url: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_BASE_URL")

    @field_validator("telegram_admin_id", mode="before")
    @classmethod
    def _admin_id_empty_as_none(cls, v: object) -> object:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, v: object) -> object:
        """Строка через запятую, JSON-массив или уже list."""
        if isinstance(v, str):
            raw = v.strip()
            if not raw:
                return []
            if raw.startswith("["):
                import json

                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
