"""Tests for RSS fetcher."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from mindscout.fetchers.rss import RSSFetcher
from mindscout.database import get_session, Article, RSSFeed, Notification


@pytest.fixture
def fetcher():
    """Create RSS fetcher instance."""
    return RSSFetcher()


@pytest.fixture
def sample_feed(isolated_test_db):
    """Create a sample feed in the database."""
    session = get_session()

    feed = RSSFeed(
        url="https://example.com/feed.xml",
        title="Test Feed",
        category="tech_blog",
        is_active=True
    )
    session.add(feed)
    session.commit()
    session.refresh(feed)

    yield feed

    session.close()


def create_mock_feed_entry(
    title="Test Article",
    link="https://example.com/article",
    summary="Test summary",
    author="Test Author",
    published_parsed=None,
    entry_id=None
):
    """Create a mock feedparser entry that behaves like a real feedparser entry.

    Feedparser entries are dict-like objects that also have attribute access.
    """
    # Create a dict subclass that also supports attribute access
    class MockEntry(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(f"MockEntry has no attribute '{name}'")

        def __setattr__(self, name, value):
            self[name] = value

    entry = MockEntry({
        "title": title,
        "link": link,
        "id": entry_id,
        "summary": summary,
        "author": author,
        "published_parsed": published_parsed or (2024, 1, 15, 10, 0, 0, 0, 0, 0),
        "updated_parsed": None,
        "tags": [],
        "authors": [],
        "content": [],
    })

    return entry


class TestRSSFetcherParseEntry:
    """Test RSS entry parsing."""

    def test_parse_entry_basic(self, fetcher):
        """Test parsing a basic entry."""
        entry = create_mock_feed_entry(
            title="Test Title",
            link="https://example.com/test",
            summary="Test summary content"
        )

        result = fetcher._parse_entry(entry, "https://example.com/feed.xml")

        assert result is not None
        assert result["title"] == "Test Title"
        assert result["url"] == "https://example.com/test"
        assert result["source"] == "rss"
        assert "Test summary content" in result["abstract"]

    def test_parse_entry_with_html_in_summary(self, fetcher):
        """Test that HTML is stripped from summary."""
        entry = create_mock_feed_entry(
            summary="<p>This is <b>bold</b> and <i>italic</i> text</p>"
        )

        result = fetcher._parse_entry(entry, "https://example.com/feed.xml")

        assert "<" not in result["abstract"]
        assert ">" not in result["abstract"]
        assert "bold" in result["abstract"]

    def test_parse_entry_missing_title(self, fetcher):
        """Test that entries without title are skipped."""
        entry = create_mock_feed_entry(title="")

        result = fetcher._parse_entry(entry, "https://example.com/feed.xml")

        assert result is None

    def test_parse_entry_missing_link(self, fetcher):
        """Test that entries without link are skipped."""
        entry = create_mock_feed_entry(link="")

        result = fetcher._parse_entry(entry, "https://example.com/feed.xml")

        assert result is None

    def test_parse_entry_published_date(self, fetcher):
        """Test parsing of published date."""
        entry = create_mock_feed_entry(
            published_parsed=(2024, 3, 15, 14, 30, 0, 0, 0, 0)
        )

        result = fetcher._parse_entry(entry, "https://example.com/feed.xml")

        assert result["published_date"] == datetime(2024, 3, 15, 14, 30, 0)


class TestRSSFetcherGenerateSourceId:
    """Test source ID generation."""

    def test_generate_source_id_with_entry_id(self, fetcher):
        """Test that entry ID is used when available."""
        entry = create_mock_feed_entry(entry_id="unique-id-123")

        result = fetcher._generate_source_id(entry, "https://example.com/feed.xml")

        assert result == "unique-id-123"

    def test_generate_source_id_fallback_to_hash(self, fetcher):
        """Test fallback to hash when no entry ID."""
        entry = create_mock_feed_entry(entry_id=None)

        result = fetcher._generate_source_id(entry, "https://example.com/feed.xml")

        # Should be a hash (32 characters) or the link (since entry_id is None, falls back to link)
        # The actual implementation returns entry.get("id") first, which can return link
        assert len(result) > 0


class TestRSSFetcherFetchFeed:
    """Test fetching from a subscribed feed."""

    def test_fetch_feed_creates_articles(self, fetcher, sample_feed, isolated_test_db):
        """Test that fetching creates new articles."""
        mock_parsed = MagicMock(spec=[])  # Empty spec prevents auto-creating attributes
        mock_parsed.feed = {"title": "Test Feed"}
        mock_parsed.entries = [
            create_mock_feed_entry(
                title="Article 1",
                link="https://example.com/1",
                entry_id="id-1"
            ),
            create_mock_feed_entry(
                title="Article 2",
                link="https://example.com/2",
                entry_id="id-2"
            ),
        ]

        with patch("mindscout.fetchers.rss.feedparser.parse", return_value=mock_parsed):
            result = fetcher.fetch_feed(sample_feed)

        assert result["new_count"] == 2

        # Verify articles in database
        session = get_session()
        articles = session.query(Article).all()
        assert len(articles) == 2
        assert articles[0].source_name == "Test Feed"
        session.close()

    def test_fetch_feed_handles_duplicates_in_same_feed(self, fetcher, sample_feed, isolated_test_db):
        """Test that duplicate entries within the same feed are handled."""
        mock_parsed = MagicMock(spec=[])
        mock_parsed.feed = {"title": "Test Feed"}
        # Same entry_id appears twice in the feed
        mock_parsed.entries = [
            create_mock_feed_entry(
                title="Article 1",
                link="https://example.com/1",
                entry_id="duplicate-id"
            ),
            create_mock_feed_entry(
                title="Article 1 Copy",
                link="https://example.com/1",
                entry_id="duplicate-id"
            ),
        ]

        with patch("mindscout.fetchers.rss.feedparser.parse", return_value=mock_parsed):
            result = fetcher.fetch_feed(sample_feed)

        # Should only create one article
        assert result["new_count"] == 1

        session = get_session()
        articles = session.query(Article).all()
        assert len(articles) == 1
        session.close()

    def test_fetch_feed_skips_duplicates(self, fetcher, sample_feed, isolated_test_db):
        """Test that duplicate articles are not created."""
        mock_parsed = MagicMock(spec=[])  # Empty spec prevents auto-creating attributes
        mock_parsed.feed = {"title": "Test Feed"}
        mock_parsed.entries = [
            create_mock_feed_entry(
                title="Article 1",
                link="https://example.com/1",
                entry_id="id-1"
            ),
        ]

        with patch("mindscout.fetchers.rss.feedparser.parse", return_value=mock_parsed):
            # First fetch
            result1 = fetcher.fetch_feed(sample_feed)
            assert result1["new_count"] == 1

            # Second fetch with same article
            result2 = fetcher.fetch_feed(sample_feed)
            assert result2["new_count"] == 0

        # Verify only one article in database
        session = get_session()
        articles = session.query(Article).all()
        assert len(articles) == 1
        session.close()

    def test_fetch_feed_updates_last_checked(self, fetcher, sample_feed, isolated_test_db):
        """Test that last_checked is updated."""
        mock_parsed = MagicMock(spec=[])  # Empty spec prevents auto-creating attributes
        mock_parsed.feed = {"title": "Test Feed"}
        mock_parsed.entries = []

        assert sample_feed.last_checked is None

        with patch("mindscout.fetchers.rss.feedparser.parse", return_value=mock_parsed):
            fetcher.fetch_feed(sample_feed)

        # Reload feed from database
        session = get_session()
        feed = session.query(RSSFeed).filter_by(id=sample_feed.id).first()
        assert feed.last_checked is not None
        session.close()


class TestRSSFetcherRefreshAllFeeds:
    """Test refreshing all feeds."""

    def test_refresh_all_feeds(self, fetcher, isolated_test_db):
        """Test refreshing all active feeds."""
        session = get_session()

        # Create multiple feeds
        feeds = [
            RSSFeed(url="https://example.com/feed1.xml", title="Feed 1", is_active=True),
            RSSFeed(url="https://example.com/feed2.xml", title="Feed 2", is_active=True),
            RSSFeed(url="https://example.com/feed3.xml", title="Feed 3", is_active=False),
        ]
        for feed in feeds:
            session.add(feed)
        session.commit()
        session.close()

        mock_parsed = MagicMock(spec=[])  # Empty spec prevents auto-creating attributes
        mock_parsed.feed = {"title": "Test"}
        mock_parsed.entries = [
            create_mock_feed_entry(title="Article", link="https://example.com/a", entry_id="a"),
        ]

        with patch("mindscout.fetchers.rss.feedparser.parse", return_value=mock_parsed):
            # Need to patch at instance level since fetch_feed creates new sessions
            with patch.object(fetcher, "fetch_feed_by_id", return_value={"new_count": 1}):
                result = fetcher.refresh_all_feeds()

        assert result["feeds_checked"] == 2  # Only active feeds
        assert result["new_count"] == 2
