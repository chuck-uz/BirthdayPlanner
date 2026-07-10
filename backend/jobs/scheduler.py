"""APScheduler: ежедневно в 09:00 по настроенному часовому поясу."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import get_settings
from jobs.private_group_birthday_notifications import run_private_group_birthday_notifications

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    settings = get_settings()
    try:
        tz = ZoneInfo(settings.scheduler_timezone)
    except Exception:
        logger.warning("Invalid SCHEDULER_TIMEZONE=%s, using UTC", settings.scheduler_timezone)
        tz = ZoneInfo("UTC")

    _scheduler = AsyncIOScheduler(timezone=tz)
    _scheduler.add_job(
        run_private_group_birthday_notifications,
        "cron",
        hour=9,
        minute=0,
        id="group_birthday_notify_daily",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started (09:00 %s)", settings.scheduler_timezone)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
