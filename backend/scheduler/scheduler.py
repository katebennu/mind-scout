"""APScheduler configuration for background jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from mindscout.config import get_settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the background scheduler."""
    settings = get_settings()

    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled via configuration")
        return

    from backend.scheduler.jobs import fetch_and_process_job

    # Run daily at configured time
    scheduler.add_job(
        fetch_and_process_job,
        CronTrigger(hour=settings.scheduler_hour, minute=settings.scheduler_minute),
        id="daily_fetch_process",
        name="Daily fetch and process",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started - daily job scheduled for "
        f"{settings.scheduler_hour:02d}:{settings.scheduler_minute:02d}"
    )


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")
