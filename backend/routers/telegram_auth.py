from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import TelegramAuthError, create_access_token, verify_telegram_login_hash
from config import get_settings
from database import get_db
from models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _query_params_as_str_dict(request: Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.query_params.multi_items()}


def _full_name_from_telegram(data: dict[str, str]) -> str | None:
    first = (data.get("first_name") or "").strip()
    last = (data.get("last_name") or "").strip()
    username = (data.get("username") or "").strip()
    combined = " ".join(p for p in (first, last) if p).strip()
    if combined:
        return combined
    if username:
        return f"@{username}"
    return None


def _same_site_cookie(value: str) -> Literal["lax", "strict", "none"]:
    normalized = value.lower()
    if normalized in ("lax", "strict", "none"):
        return cast(Literal["lax", "strict", "none"], normalized)
    return "lax"


@router.get("/telegram")
async def telegram_login(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    settings = get_settings()
    raw = _query_params_as_str_dict(request)

    try:
        verify_telegram_login_hash(
            raw,
            bot_token=settings.bot_token,
            max_age_seconds=settings.telegram_auth_max_age_seconds,
        )
    except TelegramAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="telegram_auth_failed",
        ) from exc

    telegram_id_raw = raw.get("id")
    if telegram_id_raw is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing id",
        )
    try:
        telegram_id = int(telegram_id_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid id",
        ) from exc

    full_name = _full_name_from_telegram(raw)

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, full_name=full_name)
        session.add(user)
        await session.flush()
    elif full_name is not None:
        user.full_name = full_name

    token = create_access_token(
        str(user.id),
        settings=settings,
        extra_claims={"telegram_id": telegram_id},
    )

    body = {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "telegram_id": telegram_id,
    }
    response = JSONResponse(content=body, status_code=status.HTTP_200_OK)
    max_age = settings.jwt_expire_minutes * 60
    response.set_cookie(
        key=settings.jwt_cookie_name,
        value=token,
        httponly=True,
        max_age=max_age,
        secure=settings.cookie_secure,
        samesite=_same_site_cookie(settings.cookie_samesite),
        path="/",
    )
    return response
