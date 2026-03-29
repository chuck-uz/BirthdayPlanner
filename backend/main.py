"""BirthdayPlanner API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

import models  # noqa: F401
from database import Base, engine
from routers.telegram_auth import router as telegram_auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="BirthdayPlanner API", version="0.1.0", lifespan=lifespan)
app.include_router(telegram_auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
