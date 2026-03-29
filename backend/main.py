"""BirthdayPlanner API entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

import models  # noqa: F401
from avatar_storage import ensure_avatars_dir
from config import get_settings
from database import Base, engine
from jobs.scheduler import shutdown_scheduler, start_scheduler
from routers.telegram_auth import router as telegram_auth_router
from routers.telegram_webhook import router as telegram_webhook_router
from routers.users import router as users_router
from routers.wishlists import router as wishlists_router
from wishlist_storage import ensure_wishlist_dir
from telegram_service import telegram_set_webhook

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_avatars_dir()
    ensure_wishlist_dir()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if "postgresql" in settings.database_url.lower():
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE admin_birthday_prompts "
                        "ADD COLUMN IF NOT EXISTS prompt_recipient_telegram_id BIGINT",
                    ),
                )
            except Exception:
                logger.warning(
                    "Could not add prompt_recipient_telegram_id column (migrate manually if needed)",
                    exc_info=True,
                )
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_path VARCHAR(512)",
                    ),
                )
            except Exception:
                logger.warning(
                    "Could not add users.avatar_path column (migrate manually if needed)",
                    exc_info=True,
                )
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_bot_active BOOLEAN NOT NULL DEFAULT false",
                    ),
                )
            except Exception:
                logger.warning(
                    "Could not add users.is_bot_active column (migrate manually if needed)",
                    exc_info=True,
                )
            for stmt in (
                "ALTER TABLE wishlists ADD COLUMN IF NOT EXISTS description TEXT",
                "ALTER TABLE wishlists ADD COLUMN IF NOT EXISTS link_url VARCHAR(2048)",
                "ALTER TABLE wishlists ADD COLUMN IF NOT EXISTS photo_path VARCHAR(512)",
            ):
                try:
                    await conn.execute(text(stmt))
                except Exception:
                    logger.warning(
                        "Could not migrate wishlists column: %s",
                        stmt.split()[-1],
                        exc_info=True,
                    )
    start_scheduler()
    base = (settings.telegram_webhook_base_url or "").strip().rstrip("/")
    if base:
        webhook_url = f"{base}/api/telegram/webhook"
        await telegram_set_webhook(webhook_url, secret_token=settings.telegram_webhook_secret)
    yield
    shutdown_scheduler()
    await engine.dispose()


app = FastAPI(title="BirthdayPlanner API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Порт по умолчанию 80 (Docker: 80→5173): Origin без :80
        "http://127.0.0.1",
        "http://localhost",
        # Локальный npm run dev на нестандартном порту
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_auth_router)
app.include_router(telegram_webhook_router)
app.include_router(users_router)
app.include_router(wishlists_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
