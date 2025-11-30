"""Background job definitions for Mind Scout."""

import logging
from datetime import datetime

from mindscout.database import Article, PendingBatch, get_db_session

logger = logging.getLogger(__name__)


def get_user_interests() -> list[str]:
    """Get user interests from profile, return empty list if none."""
    from mindscout.profile import ProfileManager

    pm = ProfileManager()
    profile = pm.get_profile()
    if profile and profile.interests:
        # interests stored as comma-separated string
        return [i.strip() for i in profile.interests.split(",") if i.strip()]
    return []


async def fetch_and_process_job() -> dict:
    """Daily job to fetch new articles based on user interests.

    Fetches from:
    - RSS feeds (always - user explicitly subscribed)
    - arXiv (based on user interests)
    - Semantic Scholar (based on user interests)

    Then processes up to 50 new articles with LLM.

    Returns:
        Dictionary with fetch and process results
    """
    logger.info(f"Starting daily fetch & process job at {datetime.now()}")

    results = {
        "rss": {"feeds": 0, "articles": 0},
        "arxiv": {"articles": 0},
        "semanticscholar": {"articles": 0},
        "processed": 0,
        "failed": 0,
    }

    # Get user interests for targeted fetching
    interests = get_user_interests()
    if not interests:
        logger.warning("No user interests configured - skipping arXiv and Semantic Scholar fetch")

    # 1. Refresh RSS feeds (always - user explicitly subscribed)
    try:
        from mindscout.fetchers.rss import RSSFetcher

        rss_fetcher = RSSFetcher()
        rss_result = rss_fetcher.refresh_all_feeds()
        results["rss"]["feeds"] = rss_result.get("feeds_checked", 0)
        results["rss"]["articles"] = rss_result.get("new_count", 0)
        logger.info(f"RSS: {results['rss']['articles']} new from {results['rss']['feeds']} feeds")
    except Exception as e:
        logger.error(f"RSS fetch failed: {e}")

    # 2. Fetch arXiv based on user interests
    if interests:
        try:
            from mindscout.fetchers.arxiv_advanced import ArxivAdvancedFetcher

            fetcher = ArxivAdvancedFetcher()
            # Search for each interest keyword (top 5)
            for interest in interests[:5]:
                count = fetcher.fetch_and_store(
                    keywords=interest,
                    max_results=20,
                    sort_by="submittedDate",
                    sort_order="descending",
                )
                results["arxiv"]["articles"] += count
            logger.info(
                f"arXiv: {results['arxiv']['articles']} new articles "
                f"for interests: {interests[:5]}"
            )
        except Exception as e:
            logger.error(f"arXiv fetch failed: {e}")

    # 3. Fetch Semantic Scholar based on user interests
    if interests:
        try:
            from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

            ss_fetcher = SemanticScholarFetcher()
            # Search for combined interests (top 3 as OR query)
            query = " OR ".join(interests[:3])
            articles = ss_fetcher.fetch(query=query, limit=50, year="2024-2025")
            ss_count = ss_fetcher.store_articles(articles)
            ss_fetcher.close()
            results["semanticscholar"]["articles"] = ss_count
            logger.info(f"Semantic Scholar: {ss_count} new articles for: {query}")
        except Exception as e:
            logger.error(f"Semantic Scholar fetch failed: {e}")

    # 4. Create async batch for processing (50% cheaper)
    try:
        from mindscout.processors.content import ContentProcessor

        # Check how many unprocessed articles we have
        with get_db_session() as session:
            unprocessed_count = (
                session.query(Article).filter(Article.processed == False).count()  # noqa: E712
            )

        if unprocessed_count > 0:
            processor = ContentProcessor()
            batch_id = processor.create_async_batch(limit=100)

            # Store pending batch in database
            with get_db_session() as session:
                pending = PendingBatch(
                    batch_id=batch_id,
                    article_count=min(unprocessed_count, 100),
                    status="pending",
                )
                session.add(pending)

            results["batch_id"] = batch_id
            results["batch_articles"] = min(unprocessed_count, 100)
            logger.info(
                f"Created async batch {batch_id} for {min(unprocessed_count, 100)} articles"
            )
        else:
            logger.info("No unprocessed articles - skipping batch creation")
            results["batch_id"] = None
            results["batch_articles"] = 0

    except Exception as e:
        logger.error(f"Batch creation failed: {e}")
        results["batch_id"] = None
        results["batch_articles"] = 0

    total_fetched = (
        results["rss"]["articles"]
        + results["arxiv"]["articles"]
        + results["semanticscholar"]["articles"]
    )
    logger.info(
        f"Daily job complete: {total_fetched} fetched, "
        f"batch created for {results.get('batch_articles', 0)} articles"
    )

    return results


async def check_pending_batches_job() -> dict:
    """Check pending batches and apply results when complete.

    This job runs periodically to check if any async batches have completed
    and applies their results to the database.

    Returns:
        Dictionary with batch processing results
    """
    from mindscout.processors.content import ContentProcessor
    from mindscout.processors.llm import LLMClient

    logger.info("Checking pending batches...")

    results = {
        "checked": 0,
        "completed": 0,
        "still_pending": 0,
        "failed": 0,
        "articles_updated": 0,
    }

    try:
        llm = LLMClient()
        processor = ContentProcessor()
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return results

    # Get all pending batches
    with get_db_session() as session:
        pending_batches = (
            session.query(PendingBatch)
            .filter(PendingBatch.status.in_(["pending", "processing"]))
            .all()
        )

        for batch in pending_batches:
            results["checked"] += 1

            try:
                status = llm.get_batch_status(batch.batch_id)
                logger.info(
                    f"Batch {batch.batch_id}: status={status['status']}, "
                    f"succeeded={status['counts']['succeeded']}"
                )

                if status["status"] == "ended":
                    # Batch complete - apply results
                    updated, failed = processor.apply_batch_results(batch.batch_id)
                    results["articles_updated"] += updated

                    batch.status = "completed"
                    batch.completed_date = datetime.utcnow()
                    results["completed"] += 1

                    logger.info(
                        f"Batch {batch.batch_id} completed: "
                        f"{updated} articles updated, {failed} failed"
                    )

                elif status["status"] in ["failed", "expired", "canceled"]:
                    batch.status = "failed"
                    batch.error_message = f"Batch {status['status']}"
                    batch.completed_date = datetime.utcnow()
                    results["failed"] += 1

                    logger.warning(f"Batch {batch.batch_id} {status['status']}")

                else:
                    # Still processing
                    batch.status = "processing"
                    results["still_pending"] += 1

            except Exception as e:
                logger.error(f"Error checking batch {batch.batch_id}: {e}")
                batch.error_message = str(e)
                results["failed"] += 1

    logger.info(
        f"Batch check complete: {results['completed']} completed, "
        f"{results['still_pending']} pending, {results['failed']} failed"
    )

    return results
