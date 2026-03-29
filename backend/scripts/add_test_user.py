"""
Добавить тестового пользователя в БД (синтетический telegram_id).
Запуск из корня репозитория (где .env) или из контейнера backend:

  docker compose exec backend python scripts/add_test_user.py
  cd backend && py scripts/add_test_user.py   # при .env в родителе backend/
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
if (REPO_ROOT / ".env").exists():
    os.chdir(REPO_ROOT)
sys.path.insert(0, str(BACKEND_ROOT))

# Синтетический ID — не совпадает с реальными Telegram
TEST_TELEGRAM_ID = 9_000_000_004
FULL_NAME = "Тестовый Тест"
BIRTH_DATE = dt.date(2004, 4, 3)


async def main() -> None:
    from sqlalchemy import select

    from database import async_session_maker
    from models import User

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == TEST_TELEGRAM_ID))
        user = result.scalar_one_or_none()
        if user:
            user.full_name = FULL_NAME
            user.birth_date = BIRTH_DATE
        else:
            session.add(
                User(
                    telegram_id=TEST_TELEGRAM_ID,
                    full_name=FULL_NAME,
                    birth_date=BIRTH_DATE,
                )
            )
        await session.commit()
    print(f"OK: {FULL_NAME}, дата рождения {BIRTH_DATE.isoformat()}, telegram_id={TEST_TELEGRAM_ID}")


if __name__ == "__main__":
    asyncio.run(main())
