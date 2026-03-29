from __future__ import annotations

from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import TelegramAuthError, create_access_token, verify_telegram_login_hash
from config import Settings, get_settings
from database import get_db
from deps import get_current_user
from models import User
from redirects import safe_browser_redirect

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


def _attach_auth_cookie(response: Response, token: str, settings: Settings) -> None:
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


@router.get("/telegram")
async def telegram_login(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse | RedirectResponse:
    settings = get_settings()
    raw_all = _query_params_as_str_dict(request)
    next_url = safe_browser_redirect(raw_all.get("next"))
    raw = {k: v for k, v in raw_all.items() if k != "next"}

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

    if next_url:
        redirect = RedirectResponse(url=next_url, status_code=status.HTTP_302_FOUND)
        _attach_auth_cookie(redirect, token, settings)
        return redirect

    body = {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "telegram_id": telegram_id,
    }
    response = JSONResponse(content=body, status_code=status.HTTP_200_OK)
    _attach_auth_cookie(response, token, settings)
    return response


@router.get("/me")
async def auth_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
    }


@router.post("/logout")
async def auth_logout(response: Response) -> dict:
    settings = get_settings()
    response.delete_cookie(
        key=settings.jwt_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        samesite=_same_site_cookie(settings.cookie_samesite),
        httponly=True,
    )
    return {"ok": True}
