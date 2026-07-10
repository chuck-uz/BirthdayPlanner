<div align="center">

<img src="docs/icon.svg" width="112" alt="BirthdayPlanner logo">

# BirthdayPlanner

**A platform where friends secretly chip in for a birthday gift — Telegram sign-in, the birthday person's wishlist, and a hidden group chat they never see.**

[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/frontend-React%2019-61DAFB)](https://react.dev/)
[![Postgres](https://img.shields.io/badge/db-PostgreSQL%2017-4169E1)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/deploy-Docker%20Compose-2496ED)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[Русская версия](README.md)

</div>

## Why

Organizing a group gift usually means someone starts a chat, tries to remember whose birthday is coming up, guesses what to buy, and makes sure the birthday person doesn't notice. **BirthdayPlanner** does it for you. Everyone signs in with Telegram, fills in their wishlist, and subscribes to friends' birthdays. A few weeks before the date the platform notifies the subscribers, helps spin up a **secret group chat to discuss the gift**, and sends everyone the invite — all without the birthday person knowing.

## Features

- **One-tap Telegram sign-in** — the official Telegram Login Widget, signature verified via HMAC, session stored as a JWT in an HttpOnly cookie. No passwords, no separate signup.
- **Profile & wishlist** — name, birth date, avatar; a list of wanted gifts with title, description, store link, and photo. Images are re-encoded server-side (EXIF stripped) and served only to authenticated users.
- **Subscribe to friends' birthdays** — a feed of upcoming birthdays sorted by days remaining; subscribe to anyone in one click.
- **Secret gift chat** — a configurable number of days before the date, the bot offers the organizer to create a group, add the bot, and broadcast the invite to every subscriber. The birthday person is never in that chat.
- **Private groups** — your own closed groups with `admin`/`member` roles and a revocable invite link (regenerate it any time and the old one stops working instantly). The bot notifies group admins ahead of a member's birthday; if the birthday person has no other admins around, every other member is warned a week out instead.
- **Telegram bot** — confirms subscriptions, walks the organizer through the steps ("create a group → add the bot → done"), tracks who activated the bot, and notifies about new events. Buttons and links go through a secure webhook with a secret token.
- **Daily scheduler** — APScheduler at 09:00 in the configured timezone checks whose birthday is N days away and starts the notification flow. Re-processing a date is impossible (a `BirthdayEvent` with a unique key).
- **Protects the birthday person's privacy** — blocked and "test" profiles are hidden from regular users; avatars and wishlist photos are served only with a valid JWT, never as public static.
- **Self-host ready** — a single `docker compose up`: PostgreSQL, the FastAPI backend, and the React frontend behind Nginx. The DB schema is managed by Alembic migrations.

## Quick start

You need Docker and Docker Compose, plus a [Telegram bot](https://t.me/BotFather) (`BOT_TOKEN`).

```sh
git clone https://github.com/chuck-uz/BirthdayPlanner.git
cd BirthdayPlanner
cp .env.example .env     # fill in BOT_TOKEN, JWT_SECRET_KEY, etc. (see below)
docker compose up --build
```

Open **http://127.0.0.1/** — the frontend runs on port 80, the API is proxied to the backend, PostgreSQL keeps data in a named volume. On startup the container runs migrations automatically (`alembic upgrade head`).

> **Already had a running DB (before switching to Alembic)?** Run once:
> `docker compose run --rm backend alembic stamp head`, otherwise the migration
> will try to create existing tables. See [backend/migrations/README.md](backend/migrations/README.md).

## Configuration

Everything is configured via environment variables (a `.env` file in the repo root, read by both Compose and the backend).

| Variable | Required | Purpose |
|---|:---:|---|
| `BOT_TOKEN` | yes | Bot token from [@BotFather](https://t.me/BotFather). Used for both the Login Widget and the Bot API. |
| `JWT_SECRET_KEY` | yes | Secret for signing session JWTs. A long random string. |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | yes | PostgreSQL credentials (Compose builds `DATABASE_URL` from them). |
| `BIRTHDAY_NOTIFY_DAYS_BEFORE` | no | How many days before the birthday to start the broadcast (default 14). |
| `GROUP_BIRTHDAY_NOTIFY_DAYS_BEFORE` | no | How many days before to notify private group admins (default 7). |
| `SCHEDULER_TIMEZONE` | no | Timezone of the daily 09:00 check (default `Europe/Moscow`). |
| `TELEGRAM_WEBHOOK_BASE_URL` | no | Public HTTPS address — the webhook `…/api/telegram/webhook` is set on startup. |
| `TELEGRAM_WEBHOOK_SECRET` | no | Secret in the webhook header (recommended in production). |
| `CORS_ALLOW_ORIGINS` | no | Allowed origins, comma-separated (default: local dev). |
| `COOKIE_SECURE` | no | `true` for production over HTTPS (cookie sent only over a secure connection). |

For Telegram sign-in, register your site's domain with the bot: [@BotFather](https://t.me/BotFather) → `/setdomain`.

## How it works

```
Telegram Login ──► FastAPI /api/auth/telegram ──► JWT in an HttpOnly cookie
                                                        │
React (Vite + Nginx)  ◄────── /api/* ───────►  FastAPI (async) ──► PostgreSQL (SQLAlchemy 2.0)
                                                        │
                          APScheduler (09:00) ─► birthday flow ─► Telegram Bot API ─► secret chat
                                                        ▲
                        Telegram webhook (callback / my_chat_member / message)
```

- **Auth:** the Telegram signature is verified via HMAC-SHA256, then a short JWT is issued in an HttpOnly cookie; account block is checked on every request.
- **Birthday flow:** subscribe → notify N days ahead → organizer creates a group and sends the link to the bot → the bot broadcasts the invite to subscribers; all state lives in the DB, idempotent.
- **Files:** avatars and wishlist photos are stored outside public static and served only with a JWT, through a single storage module with path-traversal and decompression-bomb protection.

## For developers

In-depth technical docs:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — architecture: backend layers, data model, notification flow, Telegram integration, scheduler, file storage, migrations, key decisions.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — local setup, repo layout, migrations workflow, tests, and conventions.
- **[CHANGELOG.md](CHANGELOG.md)** — change history.

## Local development without Docker

```sh
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn main:app --reload

# frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Backend tests: `cd backend && pytest`.

## Privacy

Data lives only in your PostgreSQL database. The app reaches out only to the Telegram Bot API (for sign-in, the bot, and broadcasts). Avatars and wishlist photos are served exclusively to authenticated users; blocked profiles are hidden. The whole point is to keep gift preparation secret from the birthday person: they see neither the secret chat nor who subscribed to it.

## License

[MIT](LICENSE)
