"""Generic RSS feed fetcher with notification support."""

import hashlib
from datetime import datetime
from typing import List, Dict, Optional
import feedparser
import requests

from mindscout.fetchers.base import BaseFetcher
from mindscout.database import Article, RSSFeed, Notification, get_session


class RSSFetcher(BaseFetcher):
    """Generic RSS/Atom feed fetcher that creates notifications for new articles."""

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
        """Fetch new articles from a subscribed feed and create notifications.

        Args:
            feed: RSSFeed database object

        Returns:
            Dictionary with counts: {"new_count": int, "notifications_count": int}
        """
        session = get_session()
        new_count = 0
        notifications_count = 0

        try:
            # Parse the feed
            parsed = feedparser.parse(feed.url)

            # Update feed metadata
            feed.last_checked = datetime.utcnow()
            if hasattr(parsed, "etag"):
                feed.last_etag = parsed.etag
            if hasattr(parsed, "modified"):
                feed.last_modified = parsed.modified

            # Update feed title if we got one
            if parsed.feed.get("title") and not feed.title:
                feed.title = parsed.feed.title

            new_article_ids = []

            # Use feed title as source_name
            source_name = feed.title or parsed.feed.get("title") or "RSS Feed"

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
                session.flush()  # Get the article ID

                new_article_ids.append(article.id)
                new_count += 1

            # Create notifications for new articles
            for article_id in new_article_ids:
                notification = Notification(
                    article_id=article_id,
                    feed_id=feed.id,
                    type="new_article"
                )
                session.add(notification)
                notifications_count += 1

            session.commit()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        return {
            "new_count": new_count,
            "notifications_count": notifications_count
        }

    def refresh_all_feeds(self) -> Dict:
        """Refresh all active feed subscriptions.

        Returns:
            Dictionary with total counts
        """
        session = get_session()
        total_new = 0
        total_notifications = 0
        feeds_checked = 0

        try:
            feeds = session.query(RSSFeed).filter(RSSFeed.is_active == True).all()

            for feed in feeds:
                try:
                    result = self.fetch_feed(feed)
                    total_new += result["new_count"]
                    total_notifications += result["notifications_count"]
                    feeds_checked += 1
                except Exception as e:
                    # Log error but continue with other feeds
                    print(f"Error fetching feed {feed.url}: {e}")
                    continue

        finally:
            session.close()

        return {
            "feeds_checked": feeds_checked,
            "new_count": total_new,
            "notifications_count": total_notifications
        }
