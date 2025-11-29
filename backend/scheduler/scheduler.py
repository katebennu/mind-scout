"""APScheduler configuration for background jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from mindscout.config import get_settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Start the background scheduler."""
    settings = get_settings()

    if not settings.scheduler_enabled:
        logger.info("Scheduler is disabled via configuration")
        return

    from backend.scheduler.jobs import fetch_and_process_job, check_pending_batches_job

    # Run daily at configured time - fetches articles and creates async batch
    scheduler.add_job(
        fetch_and_process_job,
        CronTrigger(hour=settings.scheduler_hour, minute=settings.scheduler_minute),
        id="daily_fetch_process",
        name="Daily fetch and create batch",
        replace_existing=True,
    )

    # Check pending batches every 15 minutes
    scheduler.add_job(
        check_pending_batches_job,
        IntervalTrigger(minutes=15),
        id="check_pending_batches",
        name="Check pending batches",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started - daily job at "
        f"{settings.scheduler_hour:02d}:{settings.scheduler_minute:02d}, "
        f"batch check every 15 min"
    )


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")
