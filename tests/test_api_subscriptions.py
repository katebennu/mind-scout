"""Tests for subscriptions API endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from mindscout.database import get_session, RSSFeed, init_db


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Set up test database."""
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    # Re-initialize database with new path
    from mindscout import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "mindscout.db")

    # Reload database module to pick up new path
    from mindscout import database
    database.engine = database.create_engine(f"sqlite:///{tmp_path / 'mindscout.db'}")
    database.Session = database.sessionmaker(bind=database.engine)

    init_db()
    yield tmp_path


@pytest.fixture
def sample_feeds(test_db):
    """Create sample RSS feeds in test database."""
    session = get_session()

    feeds = [
        RSSFeed(
            url="https://example.com/feed1.xml",
            title="Test Feed 1",
            category="tech_blog",
            is_active=True,
            check_interval=60,
            created_date=datetime(2024, 1, 1)
        ),
        RSSFeed(
            url="https://example.com/feed2.xml",
            title="Test Feed 2",
            category="podcast",
            is_active=True,
            check_interval=30,
            last_checked=datetime(2024, 1, 15),
            created_date=datetime(2024, 1, 2)
        ),
        RSSFeed(
            url="https://example.com/feed3.xml",
            title="Inactive Feed",
            category="news",
            is_active=False,
            created_date=datetime(2024, 1, 3)
        ),
    ]

    for feed in feeds:
        session.add(feed)
    session.commit()

    yield feeds

    session.close()


class TestListSubscriptions:
    """Test GET /api/subscriptions endpoint."""

    def test_list_subscriptions_empty(self, client, test_db):
        """Test listing subscriptions when none exist."""
        response = client.get("/api/subscriptions")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_subscriptions(self, client, sample_feeds):
        """Test listing all subscriptions."""
        response = client.get("/api/subscriptions")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3

        # Check first feed (most recent first)
        assert data[0]["title"] == "Inactive Feed"
        assert data[0]["category"] == "news"
        assert data[0]["is_active"] is False


class TestGetCuratedFeeds:
    """Test GET /api/subscriptions/curated endpoint."""

    def test_get_curated_feeds(self, client, test_db):
        """Test getting curated feed suggestions."""
        response = client.get("/api/subscriptions/curated")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        # Check structure
        first_feed = data[0]
        assert "url" in first_feed
        assert "title" in first_feed
        assert "category" in first_feed
        assert "description" in first_feed


class TestCreateSubscription:
    """Test POST /api/subscriptions endpoint."""

    def test_create_subscription_success(self, client, test_db):
        """Test creating a new subscription with valid feed."""
        # Mock feedparser to return valid feed
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [{"title": "Test Entry"}]
        mock_feed.feed.get.return_value = "Mocked Feed Title"

        import feedparser
        with patch.object(feedparser, "parse", return_value=mock_feed):
            response = client.post(
                "/api/subscriptions",
                json={
                    "url": "https://example.com/valid-feed.xml",
                    "title": "My Custom Feed",
                    "category": "tech_blog"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/valid-feed.xml"
        assert data["title"] == "My Custom Feed"
        assert data["category"] == "tech_blog"
        assert data["is_active"] is True

    def test_create_subscription_auto_title(self, client, test_db):
        """Test that feed title is auto-detected if not provided."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [{"title": "Test Entry"}]
        mock_feed.feed.get.return_value = "Auto Detected Title"
        mock_feed.feed.title = "Auto Detected Title"

        import feedparser
        with patch.object(feedparser, "parse", return_value=mock_feed):
            response = client.post(
                "/api/subscriptions",
                json={"url": "https://example.com/auto-title.xml"}
            )

        assert response.status_code == 200
        assert response.json()["title"] == "Auto Detected Title"

    def test_create_subscription_invalid_feed(self, client, test_db):
        """Test creating subscription with invalid feed URL."""
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.entries = []

        import feedparser
        with patch.object(feedparser, "parse", return_value=mock_feed):
            response = client.post(
                "/api/subscriptions",
                json={"url": "https://example.com/invalid.xml"}
            )

        assert response.status_code == 400
        assert "Invalid RSS feed" in response.json()["detail"]

    def test_create_subscription_duplicate(self, client, sample_feeds):
        """Test creating duplicate subscription."""
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [{"title": "Test"}]

        import feedparser
        with patch.object(feedparser, "parse", return_value=mock_feed):
            response = client.post(
                "/api/subscriptions",
                json={"url": "https://example.com/feed1.xml"}  # Already exists
            )

        assert response.status_code == 400
        assert "Already subscribed" in response.json()["detail"]


class TestGetSubscription:
    """Test GET /api/subscriptions/{id} endpoint."""

    def test_get_subscription_success(self, client, sample_feeds):
        """Test getting a specific subscription."""
        response = client.get("/api/subscriptions/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Feed 1"

    def test_get_subscription_not_found(self, client, sample_feeds):
        """Test getting non-existent subscription."""
        response = client.get("/api/subscriptions/999")
        assert response.status_code == 404


class TestUpdateSubscription:
    """Test PUT /api/subscriptions/{id} endpoint."""

    def test_update_subscription_title(self, client, sample_feeds):
        """Test updating subscription title."""
        response = client.put(
            "/api/subscriptions/1",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_subscription_deactivate(self, client, sample_feeds):
        """Test deactivating a subscription."""
        response = client.put(
            "/api/subscriptions/1",
            json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_subscription_not_found(self, client, sample_feeds):
        """Test updating non-existent subscription."""
        response = client.put(
            "/api/subscriptions/999",
            json={"title": "New Title"}
        )
        assert response.status_code == 404


class TestDeleteSubscription:
    """Test DELETE /api/subscriptions/{id} endpoint."""

    def test_delete_subscription_success(self, client, sample_feeds):
        """Test deleting a subscription."""
        response = client.delete("/api/subscriptions/1")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify it's deleted
        get_response = client.get("/api/subscriptions/1")
        assert get_response.status_code == 404

    def test_delete_subscription_not_found(self, client, sample_feeds):
        """Test deleting non-existent subscription."""
        response = client.delete("/api/subscriptions/999")
        assert response.status_code == 404


class TestRefreshSubscription:
    """Test POST /api/subscriptions/{id}/refresh endpoint."""

    def test_refresh_subscription_success(self, client, sample_feeds):
        """Test refreshing a subscription."""
        mock_result = {"new_count": 5, "notifications_count": 5}

        with patch("mindscout.fetchers.rss.RSSFetcher.fetch_feed", return_value=mock_result):
            response = client.post("/api/subscriptions/1/refresh")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_articles"] == 5
        assert data["notifications_created"] == 5

    def test_refresh_subscription_not_found(self, client, sample_feeds):
        """Test refreshing non-existent subscription."""
        response = client.post("/api/subscriptions/999/refresh")
        assert response.status_code == 404


class TestRefreshAllSubscriptions:
    """Test POST /api/subscriptions/refresh-all endpoint."""

    def test_refresh_all_success(self, client, sample_feeds):
        """Test refreshing all subscriptions."""
        mock_result = {"new_count": 3, "notifications_count": 3}

        with patch("mindscout.fetchers.rss.RSSFetcher.fetch_feed", return_value=mock_result):
            response = client.post("/api/subscriptions/refresh-all")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["feeds_checked"] == 2  # Only active feeds
        assert data["new_articles"] == 6  # 3 per feed * 2 active feeds
