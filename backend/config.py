from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


@lru_cache
def get_settings() -> Settings:
    return Settings()
