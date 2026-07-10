from __future__ import annotations

import json
from typing import Literal, cast
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import TelegramAuthError, create_access_token, verify_telegram_login_hash
from config import Settings, get_settings
from database import get_db
from models import User
from ratelimit import limiter
from redirects import resolve_post_login_redirect

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _query_params_as_str_dict(request: Request) -> dict[str, str]:
    return {k: str(v) for k, v in request.query_params.multi_items()}


def _same_site_cookie(value: str) -> Literal["lax", "strict", "none"]:
    normalized = value.lower()
    if normalized in ("lax", "strict", "none"):
        return cast(Literal["lax", "strict", "none"], normalized)
    return "lax"


_SKIP_TELEGRAM_VERIFY = frozenset({"next", "popup"})


def _popup_success_response(
    redirect_url: str,
    token: str,
    settings: Settings,
) -> HTMLResponse:
    """После входа: редирект в этом же окне (popup). Cookie уже в ответе. Без postMessage — иначе Firefox/
    Telegram (чужой opener / неверный targetOrigin) сыплют ошибки в консоль; родитель подхватит сессию
    по focus/visibility (см. AuthContext)."""
    redirect_js = json.dumps(redirect_url, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Вход выполнен</title></head>
<body style="font-family:system-ui,sans-serif;padding:1.5rem;text-align:center;background:#fafafa">
<p style="margin:0;font-size:14px;color:#333">Переход в приложение…</p>
<script>
(function() {{
  var url = {redirect_js};
  window.location.replace(url);
}})();
</script>
</body></html>"""
    response = HTMLResponse(content=html, status_code=status.HTTP_200_OK)
    _attach_auth_cookie(response, token, settings)
    return response


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


@router.get("/telegram", response_model=None)
@limiter.limit("30/minute")
async def telegram_login(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse | HTMLResponse:
    settings = get_settings()
    raw_all = _query_params_as_str_dict(request)
    raw = {k: v for k, v in raw_all.items() if k not in _SKIP_TELEGRAM_VERIFY}

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

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, full_name=None, birth_date=None)
        session.add(user)
        await session.flush()

    token = create_access_token(
        str(user.id),
        settings=settings,
        extra_claims={"telegram_id": telegram_id},
    )

    redirect_url = resolve_post_login_redirect(
        raw_all.get("next"),
        settings.frontend_default_url,
    )
    popup = (raw_all.get("popup") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if popup:
        return _popup_success_response(redirect_url, token, settings)

    redirect = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    _attach_auth_cookie(redirect, token, settings)
    return redirect


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
