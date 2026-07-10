# Contributing / Development guide

How to build, run, and extend BirthdayPlanner. For the system design read
[ARCHITECTURE.md](ARCHITECTURE.md); for product usage read [README.md](README.md).

## Prerequisites

- Docker + Docker Compose (the easiest path), **or** Python 3.12+ and Node 20+ for local dev.
- A Telegram bot from [@BotFather](https://t.me/BotFather) — you need `BOT_TOKEN`.
- Copy `.env.example` to `.env` and fill it in.

## Project layout

```
backend/            FastAPI app (see ARCHITECTURE.md §3 for the module map)
  migrations/       Alembic (env.py, versions/)
  storage/          image storage (avatars, wishlist photos)
  jobs/             APScheduler + daily birthday job
  routers/          HTTP endpoints
  schemas/          Pydantic request/response models
  tests/            pytest
  requirements.txt          runtime deps
  requirements-dev.txt      + pytest
  entrypoint.sh             runs `alembic upgrade head`, then uvicorn
frontend/           React 19 + Vite + Tailwind SPA
  src/pages,components,contexts,lib,types
  nginx-docker.conf         SPA + /api proxy for the production image
Dockerfile          multi-stage: backend, frontend-development, frontend-production
docker-compose.yml  db + backend + frontend
```

## Run with Docker (recommended)

```sh
cp .env.example .env        # fill BOT_TOKEN, JWT_SECRET_KEY, DB_*
docker compose up --build
```

- Frontend: **http://127.0.0.1/** (port 80 → Vite 5173 in the dev image)
- Backend: **http://127.0.0.1:8000** (OpenAPI docs at `/docs`)
- Postgres: `localhost:5432`

The backend container runs `alembic upgrade head` before starting uvicorn.

## Run locally without Docker

```sh
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/birthday_planner"
export BOT_TOKEN="..." JWT_SECRET_KEY="dev-secret"
alembic upgrade head
uvicorn main:app --reload

# frontend
cd frontend
npm install
npm run dev            # http://127.0.0.1:5173, proxies /api to :8000
```

The Vite dev server proxies `/api` to the backend so the HttpOnly cookie is
same-origin (see `frontend/vite.config.ts`).

## Database migrations

Schema is managed by **Alembic** — never edit tables by hand and never rely on
`create_all`.

```sh
cd backend
alembic revision --autogenerate -m "short description"   # after changing models.py
# review the generated file in migrations/versions/, then:
alembic upgrade head
alembic downgrade -1                                       # roll back one step
```

`env.py` reads `DATABASE_URL` and the models' metadata from the app, so no extra
wiring is needed. On a DB created by the old `create_all`, run `alembic stamp
head` once — see [backend/migrations/README.md](backend/migrations/README.md).

## Tests

```sh
cd backend
pip install -r requirements-dev.txt
pytest
```

Current tests cover the pure modules (`auth`, `birthday_utils`, `redirects`).
When adding logic, prefer functions that don't depend on global singletons so
they stay unit-testable; inject the session and settings instead.

## Conventions

- **Backend:** type hints everywhere, `from __future__ import annotations`,
  async endpoints, Pydantic for all request/response bodies. Escape user input
  in any Telegram HTML (`html.escape`). Put abuse-prone endpoints behind
  `@limiter.limit(...)`.
- **Frontend:** function components + hooks, `@/` path alias, Tailwind classes,
  API calls through `src/lib/api.ts` (the shared axios instance).
- **Commits:** short imperative subject; this repo does **not** add a
  `Co-Authored-By` trailer. After a change that alters behavior, add an entry to
  [CHANGELOG.md](CHANGELOG.md).

## Release / deploy notes

- Set `COOKIE_SECURE=true`, a real `CORS_ALLOW_ORIGINS`, `TELEGRAM_WEBHOOK_SECRET`,
  and `TELEGRAM_WEBHOOK_BASE_URL` for production.
- Register the site domain with the bot: [@BotFather](https://t.me/BotFather) → `/setdomain`.
- Run the app with a single worker (or externalize the scheduler) to avoid
  duplicate daily broadcasts — see [ARCHITECTURE.md](ARCHITECTURE.md) §8.
