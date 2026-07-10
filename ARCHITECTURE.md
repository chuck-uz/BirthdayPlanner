# BirthdayPlanner — Architecture

Technical documentation for developers. It explains how BirthdayPlanner is
structured, how each subsystem works, and the design decisions behind it. For
product/usage docs see [README.md](README.md); for the dev workflow see
[CONTRIBUTING.md](CONTRIBUTING.md).

- **Shape:** a self-hosted web app — async FastAPI backend, React SPA, PostgreSQL, a Telegram bot.
- **Size:** ~3.5k lines of Python across the backend, ~3.6k lines of TypeScript/React on the frontend.
- **Philosophy:** *keep the surprise*. The birthday person must never see the
  gift coordination — subscriptions, the secret chat, or who is in it. Almost
  all coordination happens over a Telegram bot; the web app is the profile,
  wishlist, and admin surface.

---

## 1. High-level pipeline

```
                 Browser (React SPA, served by Nginx)
                          │  same-origin /api/*  (cookie: JWT, HttpOnly)
                          ▼
        ┌────────────────────────────────────────────────────────┐
        │                  FastAPI (async, uvicorn)                │
        │  routers: auth · users · wishlists · admin · webhook     │
        │  deps: get_current_user (JWT) · get_current_admin        │
        └───────┬─────────────────────┬───────────────────┬───────┘
                │                     │                   │
                ▼                     ▼                   ▼
        PostgreSQL              storage/image_store   Telegram Bot API
        (SQLAlchemy 2.0         (avatars, wishlist    (httpx): send /
         async, Alembic)         photos on disk)       edit / webhook
                ▲                                          │
                │                                          ▼
        APScheduler (09:00, tz) ──► birthday flow ──► secret group chat
                                                          ▲
                              Telegram webhook (callback_query /
                              my_chat_member / message)
```

The unit of work is a **birthday event**: for each upcoming birthday with
subscribers, the system drives a one-time flow that ends in a `BirthdayEvent`
row (group created and invite broadcast). Everything is idempotent and keyed by
`(target_user, celebration_date)`.

---

## 2. Tech stack

| Concern | Choice | Why |
|---|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com/) (async) + uvicorn | Async I/O for DB + Telegram, typed, OpenAPI for free |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) async (`asyncpg`) | Modern typed mappings, async sessions |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) (async env) | Versioned schema, autogenerate from models |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) + pydantic-settings | Request/response schemas, env config |
| Auth | Telegram Login Widget + JWT ([python-jose](https://github.com/mpdavis/python-jose)) | Passwordless; HMAC-verified; HttpOnly cookie |
| Bot | Telegram Bot API over [httpx](https://www.python-httpx.org/) | No heavyweight framework; thin wrapper |
| Scheduling | [APScheduler](https://apscheduler.readthedocs.io/) (AsyncIO) | Daily cron job inside the app process |
| Images | [Pillow](https://python-pillow.org/) | Re-encode, strip EXIF, resize, bomb guard |
| Rate limiting | [slowapi](https://github.com/laurentS/slowapi) | Per-IP limits on abuse-prone endpoints |
| Frontend | [React 19](https://react.dev/) + [Vite](https://vite.dev/) + [Tailwind](https://tailwindcss.com/) + React Router | SPA, fast dev, utility CSS |
| HTTP client | [axios](https://axios-http.com/) (`withCredentials`) | Sends the session cookie on same-origin `/api` |
| Runtime | Docker Compose: Postgres 17 + backend + frontend (Nginx) | One-command self-host |

---

## 3. Backend layout

```
backend/
  main.py                     app factory, lifespan, CORS, router wiring, limiter
  config.py                   Settings (pydantic-settings, env-driven, lru_cache)
  database.py                 async engine + session maker, get_db dependency
  models.py                   SQLAlchemy models (5 tables)
  deps.py                     get_current_user (JWT → User, block check)
  auth.py                     Telegram HMAC verify, JWT encode/decode
  admin_access.py             is_app_admin, get_current_admin dependency
  redirects.py                post-login open-redirect allowlist
  birthday_utils.py           next_birthday_date / days_until (leap-year safe)
  birthday_notify_logic.py    subscribe follow-up, event creation, subscriber broadcast
  birthday_admin_flow.py      DM group flow: prompts, callback buttons, my_chat_member
  admin_broadcast_flow.py     admin broadcast callback handling
  telegram_service.py         Telegram Bot API calls (httpx)
  telegram_bot_start_handler.py  /start → mark is_bot_active
  ratelimit.py                shared slowapi Limiter
  jobs/
    scheduler.py              APScheduler start/stop (09:00 daily)
    birthday_notifications.py daily reminder job
  storage/
    image_store.py            ImageStore (avatars + wishlist photos)
  routers/
    telegram_auth.py          GET /api/auth/telegram, POST /api/auth/logout
    telegram_webhook.py       POST /api/telegram/webhook
    users.py                  profile, wishlist CRUD, subscriptions, avatars
    wishlists.py              JWT-gated wishlist photo delivery
    admin.py                  users admin, birthdays dashboard, broadcast
  schemas/                    Pydantic request/response models
  migrations/                 Alembic (env.py, versions/0001_baseline.py)
  tests/                      pytest (auth, birthday_utils, redirects)
```

The design intent (post-refactor) is a move toward layers: routers validate and
map, business logic lives in the `birthday_*` / `storage` modules, and DB access
goes through SQLAlchemy sessions injected via `get_db`. Configuration and the
Telegram client are the main remaining global singletons.

---

## 4. Data model

Five tables (`backend/models.py`), all keyed to `users`:

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Accounts (one per Telegram user, plus synthetic test users) | `telegram_id` (unique), `full_name`, `birth_date`, `avatar_path`, `is_bot_active`, `is_blocked`, `is_test` |
| `wishlists` | Gift items owned by a user | `user_id` (FK, cascade), `title`, `description`, `link_url`, `photo_path` |
| `subscriptions` | "subscriber wants notifications about target's birthday" | `subscriber_id`, `target_user_id`, unique together |
| `admin_birthday_prompts` | State machine for the manual group flow | `target_user_id`, `celebration_date`, `state`, `prompt_recipient_telegram_id`, `admin_prompt_message_id`, `pending_invite_link` |
| `birthday_events` | Terminal record: this birthday cycle is done | `target_user_id`, `celebration_date` (unique together), `telegram_chat_id`, `invite_link` |

The unique constraint `(target_user_id, celebration_date)` on both
`admin_birthday_prompts` and `birthday_events` is what makes the whole flow
idempotent — a birthday is processed at most once per year.

---

## 5. Authentication

1. The frontend renders the official **Telegram Login Widget**; on success it
   redirects to `GET /api/auth/telegram` with the signed payload.
2. `auth.verify_telegram_login_hash` recomputes the **HMAC-SHA256** over the
   sorted `key=value` data-check-string using `sha256(BOT_TOKEN)` as the key and
   compares it in constant time; it also rejects a stale `auth_date`.
3. On success the user is upserted by `telegram_id`, a short **JWT** (`sub` =
   user id) is issued and set as an **HttpOnly, SameSite cookie** (`Secure` in
   production via `COOKIE_SECURE`).
4. Every protected request goes through `deps.get_current_user`: it reads the
   cookie (or `Authorization: Bearer`), decodes the JWT, loads the user, and
   **rejects blocked accounts** with 403.

Admin access (`admin_access`) is simply "the JWT user's `telegram_id` equals
`TELEGRAM_ADMIN_ID`". Post-login redirects are constrained by an allowlist
(`redirects.py`) to prevent open redirects.

---

## 6. The birthday notification flow

The heart of the product. Two entry points converge on the same state machine:

- **On new subscription** (`POST /api/users/{id}/subscription`) — scheduled as a
  `BackgroundTask` so the HTTP response isn't blocked by Telegram calls.
- **Daily** (`jobs/birthday_notifications.run_daily_birthday_reminders`) — for
  everyone whose birthday is exactly `BIRTHDAY_NOTIFY_DAYS_BEFORE` away.

When `TELEGRAM_ADMIN_ID` is set, the flow is admin-operated over DM
(`birthday_admin_flow`). `admin_birthday_prompts.state` walks:

```
prompt_sent ──► (admin-mode) await_link ──► link_received ──► completed
      │                                          ▲
      └► create_selected ──(bot added to group, my_chat_member)──► completed
      └► skipped
```

1. Bot DMs the operator: "birthday of X in N days, K subscribers — send a group
   link" (or, in legacy no-admin mode, buttons *Create / Skip*).
2. Operator replies with a `t.me/...` URL → `handle_telegram_admin_birthday_prompt_message`
   stores it in `pending_invite_link` and shows a **"Broadcast to subscribers"** button.
3. Pressing it messages every subscriber (except the birthday person and blocked
   users) with the invite and writes a terminal `BirthdayEvent`.
4. Alternatively, the operator creates a group and adds the bot; the
   `my_chat_member` webhook exports the invite link and broadcasts it.

All prompt/event state lives in PostgreSQL (the pending link too), so the flow
survives restarts and multiple workers. The birthday person is never a recipient.

> A group cannot be created by a bot via the Bot API — a human always creates it
> and the bot only obtains the invite link. This is why the flow is
> operator-driven rather than fully automatic.

---

## 7. Telegram integration

- **`telegram_service`** — a thin async wrapper over the Bot API (`sendMessage`,
  `editMessageText`, `answerCallbackQuery`, `exportChatInviteLink`, `getChat`,
  `getMe`, `setWebhook`). `getMe`/bot id are cached.
- **Webhook** (`routers/telegram_webhook`) — verified by the
  `X-Telegram-Bot-Api-Secret-Token` header, routes `callback_query`,
  `my_chat_member`, and `message` updates. On a handler error it returns **500**
  so Telegram retries delivery instead of dropping the update.
- **Delivery capability** — whether the bot can DM a user is cached in
  `users.is_bot_active` (set when the user presses `/start`), so hot paths don't
  make a live `getChat` per request.

Outgoing messages use HTML parse mode with `html.escape` on all user-supplied
names and links (XSS/markup-injection safe).

---

## 8. Scheduler

`jobs/scheduler` starts an `AsyncIOScheduler` in the FastAPI lifespan with a
single cron job at **09:00** in `SCHEDULER_TIMEZONE`. The job selects users whose
birthday is `BIRTHDAY_NOTIFY_DAYS_BEFORE` away and drives the flow above, each
target in its own session/transaction so one failure doesn't abort the batch.

> Scaling note: the scheduler currently starts inside every worker process, so
> run the app with a single worker, or move the scheduler to a dedicated process
> / guard it with a Postgres advisory lock.

---

## 9. File storage

`storage/image_store.ImageStore` is the single implementation for both avatars
and wishlist photos:

- validates the upload by **magic bytes** (JPEG/PNG) and a size cap;
- re-encodes through Pillow — **strips EXIF**, guards against
  **decompression bombs** (`Image.MAX_IMAGE_PIXELS`), and resizes to a max side;
- writes a UUID-named file under `uploads/{avatars,wishlist}/`;
- resolves stored paths with **path-traversal protection**.

Files are never exposed as public static — they are served by JWT-gated
endpoints (`/api/users/{id}/avatar`, `/api/wishlists/{id}/photo`) that also hide
blocked users' media, with `Cache-Control` headers.

---

## 10. Migrations

Schema is owned by **Alembic** (`backend/migrations`). The async `env.py` pulls
`DATABASE_URL` and metadata from the app; the container runs `alembic upgrade
head` on startup via `entrypoint.sh`. A hand-written baseline
(`0001_baseline.py`) matches the models exactly (verified by autogenerate
producing no drift). Adopting Alembic on a pre-existing DB requires a one-time
`alembic stamp head` — see [backend/migrations/README.md](backend/migrations/README.md).

---

## 11. Frontend

React 19 SPA (Vite + Tailwind, React Router). `AuthContext` fetches
`/api/users/me` on mount and on window focus/visibility (throttled), keeping the
session in sync. `axios` is configured `withCredentials` so the HttpOnly cookie
rides along on same-origin `/api` calls; a response interceptor centralizes
401/403 (blocked) handling. Pages: home (upcoming birthdays), profile & settings,
wishlist editing, another user's public profile, and the admin dashboard/user
views. In production Nginx serves the built SPA and proxies `/api/` to the
backend.

---

## 12. Key decisions

- **Passwordless via Telegram** — the audience already uses Telegram; the same
  identity drives the bot that delivers every notification.
- **Bot-first coordination** — the surprise only works if the birthday person
  can't see it, so the secret chat and broadcasts live entirely in Telegram, not
  in the web UI.
- **Idempotency by unique key** — `(target, celebration_date)` guarantees a
  birthday is handled once, whether triggered by a subscription or the daily job.
- **State in the database, not memory** — the whole DM flow (including the
  pending invite link) persists in Postgres, so restarts and extra workers don't
  lose in-flight coordination.
- **No public media** — avatars and wishlist photos are always authorization-gated.
