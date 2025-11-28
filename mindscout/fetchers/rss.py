"""Generic RSS feed fetcher."""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
import requests

from mindscout.fetchers.base import BaseFetcher
from mindscout.database import Article, RSSFeed, get_db_session

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """Generic RSS/Atom feed fetcher."""

    def __init__(self):
        super().__init__("rss")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MindScout/0.6 (RSS Reader)"
        })

    def fetch(self, url: str, **kwargs) -> List[Dict]:
        """Fetch articles from an RSS feed URL.

        Args:
            url: RSS feed URL

        Returns:
            List of article dictionaries
        """
        feed = feedparser.parse(url)
        articles = []

        for entry in feed.entries:
            article = self._parse_entry(entry, url)
            if article:
                articles.append(article)

        return articles

    def _parse_entry(self, entry: Dict, feed_url: str) -> Optional[Dict]:
        """Parse a feed entry into an article dictionary.

        Args:
            entry: feedparser entry object
            feed_url: URL of the source feed

        Returns:
            Article dictionary or None if parsing fails
        """
        # Generate a unique source_id from the entry
        source_id = self._generate_source_id(entry, feed_url)

        # Get title (required)
        title = entry.get("title", "").strip()
        if not title:
            return None

        # Get URL (required)
        url = entry.get("link", "")
        if not url:
            return None

        # Parse authors
        authors = ""
        if "authors" in entry:
            authors = ", ".join(
                author.get("name", "") for author in entry.authors
            )
        elif "author" in entry:
            authors = entry.author

        # Parse content/summary
        abstract = ""
        if "summary" in entry:
            abstract = entry.summary
        elif "content" in entry and entry.content:
            abstract = entry.content[0].get("value", "")

        # Strip HTML tags from abstract (simple approach)
        import re
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        # Parse published date
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        # Parse categories/tags
        categories = ""
        if "tags" in entry:
            categories = ", ".join(
                tag.get("term", "") for tag in entry.tags if tag.get("term")
            )

        return {
            "source_id": source_id,
            "source": "rss",
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "url": url,
            "published_date": published,
            "categories": categories,
        }

    def _generate_source_id(self, entry: Dict, feed_url: str) -> str:
        """Generate a unique source ID for an entry.

        Uses entry ID if available, otherwise generates hash from URL + title.

        Args:
            entry: feedparser entry object
            feed_url: URL of the source feed

        Returns:
            Unique source ID string
        """
        # Try to use entry's id field first
        if entry.get("id"):
            return entry.id

        # Fall back to hashing URL + title
        content = f"{entry.get('link', '')}{entry.get('title', '')}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def fetch_feed(self, feed: RSSFeed) -> Dict:
        """Fetch new articles from a subscribed feed.

        Notifications are NOT created here - they are created by the content
        processor when articles match user interests.

        Args:
            feed: RSSFeed database object

        Returns:
            Dictionary with counts: {"new_count": int}
        """
        new_count = 0

        with get_db_session() as session:
            # Get the feed object in this session
            db_feed = session.query(RSSFeed).filter_by(id=feed.id).first()
            if not db_feed:
                logger.error(f"Feed with id {feed.id} not found")
                raise ValueError(f"Feed with id {feed.id} not found")

            logger.info(f"Fetching RSS feed: {db_feed.title or db_feed.url}")

            # Parse the feed
            parsed = feedparser.parse(feed.url)

            # Update feed metadata
            db_feed.last_checked = datetime.utcnow()
            if hasattr(parsed, "etag"):
                db_feed.last_etag = parsed.etag
            if hasattr(parsed, "modified"):
                db_feed.last_modified = parsed.modified

            # Update feed title if we got one
            if parsed.feed.get("title") and not db_feed.title:
                db_feed.title = parsed.feed.title

            # Use feed title as source_name
            source_name = db_feed.title or parsed.feed.get("title") or "RSS Feed"

            for entry in parsed.entries:
                article_data = self._parse_entry(entry, feed.url)
                if not article_data:
                    continue

                # Add source_name from feed
                article_data["source_name"] = source_name

                # Check if article already exists
                existing = session.query(Article).filter_by(
                    source_id=article_data["source_id"]
                ).first()

                if existing:
                    continue

                # Create new article
                article = Article(**article_data)
                session.add(article)
                new_count += 1

        logger.info(f"Fetched {new_count} new articles from {source_name}")
        return {
            "new_count": new_count,
        }

    def refresh_all_feeds(self) -> Dict:
        """Refresh all active feed subscriptions.

        Returns:
            Dictionary with total counts
        """
        total_new = 0
        feeds_checked = 0

        with get_db_session() as session:
            feeds = session.query(RSSFeed).filter(RSSFeed.is_active == True).all()

        for feed in feeds:
            try:
                result = self.fetch_feed(feed)
                total_new += result["new_count"]
                feeds_checked += 1
            except Exception as e:
                logger.error(f"Error fetching feed {feed.url}: {e}")
                continue

        logger.info(f"Refreshed {feeds_checked} feeds, found {total_new} new articles")
        return {
            "feeds_checked": feeds_checked,
            "new_count": total_new,
        }
