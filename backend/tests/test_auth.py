import hashlib
import hmac
import time

import pytest

from auth import (
    TelegramAuthError,
    create_access_token,
    decode_access_token,
    verify_telegram_login_hash,
)
from config import Settings

BOT_TOKEN = "123456:test-bot-token"


def _sign(auth_data: dict[str, str], bot_token: str = BOT_TOKEN) -> dict[str, str]:
    pairs = [f"{k}={v}" for k, v in sorted(auth_data.items()) if k != "hash"]
    check_string = "\n".join(pairs)
    secret = hashlib.sha256(bot_token.encode()).digest()
    digest = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return {**auth_data, "hash": digest}


def test_valid_login_hash_passes():
    data = _sign({"id": "42", "first_name": "Ann", "auth_date": str(int(time.time()))})
    # Не бросает исключение → подпись валидна.
    verify_telegram_login_hash(data, bot_token=BOT_TOKEN, max_age_seconds=86400)


def test_tampered_payload_is_rejected():
    data = _sign({"id": "42", "auth_date": str(int(time.time()))})
    data["id"] = "43"  # подменили после подписи
    with pytest.raises(TelegramAuthError):
        verify_telegram_login_hash(data, bot_token=BOT_TOKEN, max_age_seconds=86400)


def test_expired_auth_date_is_rejected():
    old = str(int(time.time()) - 100_000)
    data = _sign({"id": "42", "auth_date": old})
    with pytest.raises(TelegramAuthError):
        verify_telegram_login_hash(data, bot_token=BOT_TOKEN, max_age_seconds=86400)


def test_missing_hash_is_rejected():
    with pytest.raises(TelegramAuthError):
        verify_telegram_login_hash({"id": "42", "auth_date": "1"}, bot_token=BOT_TOKEN, max_age_seconds=1)


def _settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./x.db",
        BOT_TOKEN=BOT_TOKEN,
        JWT_SECRET_KEY="unit-test-secret",
    )


def test_jwt_roundtrip():
    settings = _settings()
    token = create_access_token("42", settings=settings, extra_claims={"telegram_id": 99})
    payload = decode_access_token(token, settings=settings)
    assert payload["sub"] == "42"
    assert payload["telegram_id"] == 99


def test_jwt_wrong_secret_rejected():
    token = create_access_token("42", settings=_settings())
    other = Settings(
        DATABASE_URL="sqlite+aiosqlite:///./x.db",
        BOT_TOKEN=BOT_TOKEN,
        JWT_SECRET_KEY="a-different-secret",
    )
    with pytest.raises(TelegramAuthError):
        decode_access_token(token, settings=other)
