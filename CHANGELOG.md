# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project documentation and presentation: bilingual `README.md` / `README.en.md`,
  `ARCHITECTURE.md`, `CONTRIBUTING.md`, this changelog, `LICENSE` (MIT),
  `.env.example`, and a GitHub Pages landing under `docs/`.
- **Alembic** migrations (async `env.py`, baseline `0001_baseline`); the backend
  container runs `alembic upgrade head` on startup.
- Unified image storage (`storage/image_store.ImageStore`) with EXIF stripping,
  decompression-bomb guard, and resizing for both avatars and wishlist photos.
- Rate limiting (slowapi) on sign-in, subscription, and file uploads.
- `pytest` suite for `auth`, `birthday_utils`, and `redirects` (16 tests).
- `CORS_ALLOW_ORIGINS` environment variable.

### Changed
- The admin DM group flow now persists its pending invite link in the database
  (`admin_birthday_prompts.pending_invite_link`) instead of in-process memory —
  survives restarts and multiple workers.
- Subscription follow-up runs as a background task; `can_receive_bot_messages` is
  read from the cached `is_bot_active` flag instead of a live Telegram call.
- Admin birthdays dashboard: removed N+1 queries (aggregate + batched lookups).
- Telegram webhook returns 500 on handler errors so updates are retried.

### Fixed
- Wired `handle_telegram_admin_birthday_prompt_message` into the webhook (the
  admin's "send the group link in DM" step previously did nothing).
- Removed the dead `createChat` path (bots cannot create groups via the Bot API).
- Daily reminder used a hardcoded `14` days instead of `BIRTHDAY_NOTIFY_DAYS_BEFORE`.

### Removed
- The ad-hoc `create_all` + manual `ALTER TABLE ... IF NOT EXISTS` schema block
  from application startup (replaced by Alembic).
- Duplicated `avatar_storage.py` / `wishlist_storage.py` modules.

## [0.1.0] — Initial

### Added
- Telegram Login authentication with HMAC verification and JWT in an HttpOnly cookie.
- User profiles: name, birth date, avatar (served only to authenticated users).
- Wishlists with title, description, store link, and photo.
- Subscriptions to other users' birthdays and an upcoming-birthdays feed.
- Birthday notification flow with a secret group chat for gift coordination,
  driven over a Telegram bot (webhook: callbacks, `my_chat_member`, messages).
- Admin panel: user management (block/delete), birthdays dashboard, manual
  group-link broadcast, and test-user generation.
- Daily APScheduler job (09:00, configurable timezone).
- Docker Compose stack: PostgreSQL, FastAPI backend, React + Nginx frontend.

[Unreleased]: https://github.com/chuck-uz/BirthdayPlanner/compare/main...HEAD
