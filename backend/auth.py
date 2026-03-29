from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from jose import jwt
from jose.exceptions import JWTError

from config import Settings, get_settings


class TelegramAuthError(Exception):
    """Invalid Telegram Login Widget payload."""


def build_telegram_data_check_string(auth_data: dict[str, str]) -> str:
    """Sorted key=value lines excluding hash (Telegram Login Widget spec)."""
    pairs = [f"{k}={v}" for k, v in sorted(auth_data.items()) if k != "hash"]
    return "\n".join(pairs)


def verify_telegram_login_hash(
    auth_data: dict[str, str],
    *,
    bot_token: str,
    max_age_seconds: int,
) -> None:
    """
    Validate HMAC-SHA256 signature and auth_date freshness.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    received_hash = auth_data.get("hash")
    if not received_hash:
        raise TelegramAuthError("missing hash")

    auth_date_raw = auth_data.get("auth_date")
    if auth_date_raw is None:
        raise TelegramAuthError("missing auth_date")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise TelegramAuthError("invalid auth_date") from exc

    if int(time.time()) - auth_date > max_age_seconds:
        raise TelegramAuthError("auth_date expired")

    check_string = build_telegram_data_check_string(auth_data)
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed = hmac.new(
        secret_key,
        check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        raise TelegramAuthError("invalid hash")


def create_access_token(
    subject: str,
    *,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    cfg = settings or get_settings()
    now = int(time.time())
    expire = now + cfg.jwt_expire_minutes * 60
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


def decode_access_token(token: str, *, settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    try:
        return jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
    except JWTError as exc:
        raise TelegramAuthError("invalid token") from exc
