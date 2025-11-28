"""Background job definitions for Mind Scout."""

import logging
from datetime import datetime

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
        logger.warning(
            "No user interests configured - skipping arXiv and Semantic Scholar fetch"
        )

    # 1. Refresh RSS feeds (always - user explicitly subscribed)
    try:
        from mindscout.fetchers.rss import RSSFetcher

        rss_fetcher = RSSFetcher()
        rss_result = rss_fetcher.refresh_all_feeds()
        results["rss"]["feeds"] = rss_result.get("feeds_checked", 0)
        results["rss"]["articles"] = rss_result.get("new_count", 0)
        logger.info(
            f"RSS: {results['rss']['articles']} new from {results['rss']['feeds']} feeds"
        )
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

    # 4. Process new articles (limit 50)
    try:
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor()
        processed, failed = processor.process_batch(limit=50)
        results["processed"] = processed
        results["failed"] = failed
        logger.info(f"Processed: {processed} articles ({failed} failed)")
    except Exception as e:
        logger.error(f"Processing failed: {e}")

    total_fetched = (
        results["rss"]["articles"]
        + results["arxiv"]["articles"]
        + results["semanticscholar"]["articles"]
    )
    logger.info(
        f"Daily job complete: {total_fetched} fetched, {results['processed']} processed"
    )

    return results
