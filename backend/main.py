"""BirthdayPlanner API entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import models  # noqa: F401
from config import get_settings
from database import engine
from jobs.scheduler import shutdown_scheduler, start_scheduler
from ratelimit import limiter
from routers.telegram_auth import router as telegram_auth_router
from routers.telegram_webhook import router as telegram_webhook_router
from routers.admin import router as admin_router
from routers.users import router as users_router
from routers.wishlists import router as wishlists_router
from storage.image_store import avatar_store, wishlist_store
from telegram_service import telegram_set_webhook

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    avatar_store.ensure_dir()
    wishlist_store.ensure_dir()
    # Схема БД управляется Alembic (`alembic upgrade head`, см. backend/migrations).
    # Приложение больше не создаёт/меняет таблицы при старте.
    start_scheduler()
    base = (settings.telegram_webhook_base_url or "").strip().rstrip("/")
    if base:
        webhook_url = f"{base}/api/telegram/webhook"
        await telegram_set_webhook(webhook_url, secret_token=settings.telegram_webhook_secret)
    yield
    shutdown_scheduler()
    await engine.dispose()


app = FastAPI(title="BirthdayPlanner API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_auth_router)
app.include_router(telegram_webhook_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(wishlists_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
