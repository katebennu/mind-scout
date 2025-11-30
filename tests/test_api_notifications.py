"""Tests for notifications API endpoints."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from mindscout.database import Article, Notification, RSSFeed, get_session


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_notifications(isolated_test_db):
    """Create sample notifications with articles and feeds."""
    session = get_session()

    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml", title="Test Feed", category="tech_blog", is_active=True
    )
    session.add(feed)
    session.flush()

    # Create articles
    articles = [
        Article(
            source_id="test-1",
            title="Article 1",
            authors="Author A",
            abstract="Test abstract 1",
            url="https://example.com/1",
            source="rss",
            source_name="Test Feed",
            published_date=datetime(2024, 1, 15),
            fetched_date=datetime(2024, 1, 20),
        ),
        Article(
            source_id="test-2",
            title="Article 2",
            authors="Author B",
            abstract="Test abstract 2",
            url="https://example.com/2",
            source="rss",
            source_name="Test Feed",
            published_date=datetime(2024, 1, 16),
            fetched_date=datetime(2024, 1, 21),
        ),
        Article(
            source_id="test-3",
            title="Article 3",
            authors="Author C",
            abstract="Test abstract 3",
            url="https://example.com/3",
            source="rss",
            source_name="Test Feed",
            published_date=datetime(2024, 1, 17),
            fetched_date=datetime(2024, 1, 22),
        ),
    ]

    for article in articles:
        session.add(article)
    session.flush()

    # Create notifications
    notifications = [
        Notification(
            article_id=1,
            feed_id=feed.id,
            type="new_article",
            is_read=False,
            created_date=datetime(2024, 1, 20, 10, 0),
        ),
        Notification(
            article_id=2,
            feed_id=feed.id,
            type="new_article",
            is_read=True,
            created_date=datetime(2024, 1, 21, 10, 0),
            read_date=datetime(2024, 1, 21, 12, 0),
        ),
        Notification(
            article_id=3,
            feed_id=feed.id,
            type="new_article",
            is_read=False,
            created_date=datetime(2024, 1, 22, 10, 0),
        ),
    ]

    for notif in notifications:
        session.add(notif)
    session.commit()

    yield {"feed": feed, "articles": articles, "notifications": notifications}

    session.close()


class TestListNotifications:
    """Test GET /api/notifications endpoint."""

    def test_list_notifications_empty(self, client, isolated_test_db):
        """Test listing notifications when none exist."""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_notifications(self, client, sample_notifications):
        """Test listing all notifications."""
        response = client.get("/api/notifications")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3

        # Check structure
        first = data[0]
        assert "id" in first
        assert "article" in first
        assert "feed" in first
        assert "type" in first
        assert "is_read" in first
        assert "created_date" in first

        # Check article info
        assert "title" in first["article"]
        assert "source" in first["article"]
        assert "url" in first["article"]

    def test_list_notifications_unread_only(self, client, sample_notifications):
        """Test filtering unread notifications."""
        response = client.get("/api/notifications?unread_only=true")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert all(not n["is_read"] for n in data)

    def test_list_notifications_with_limit(self, client, sample_notifications):
        """Test limiting notifications."""
        response = client.get("/api/notifications?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2


class TestNotificationCount:
    """Test GET /api/notifications/count endpoint."""

    def test_notification_count_empty(self, client, isolated_test_db):
        """Test count when no notifications exist."""
        response = client.get("/api/notifications/count")
        assert response.status_code == 200

        data = response.json()
        assert data["unread"] == 0
        assert data["total"] == 0

    def test_notification_count(self, client, sample_notifications):
        """Test notification count."""
        response = client.get("/api/notifications/count")
        assert response.status_code == 200

        data = response.json()
        assert data["unread"] == 2
        assert data["total"] == 3


class TestMarkNotificationRead:
    """Test POST /api/notifications/{id}/read endpoint."""

    def test_mark_notification_read(self, client, sample_notifications):
        """Test marking a notification as read."""
        response = client.post("/api/notifications/1/read")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["is_read"] is True

        # Verify count changed
        count_response = client.get("/api/notifications/count")
        assert count_response.json()["unread"] == 1

    def test_mark_notification_read_not_found(self, client, sample_notifications):
        """Test marking non-existent notification as read."""
        response = client.post("/api/notifications/999/read")
        assert response.status_code == 404


class TestMarkAllNotificationsRead:
    """Test POST /api/notifications/read-all endpoint."""

    def test_mark_all_read(self, client, sample_notifications):
        """Test marking all notifications as read."""
        response = client.post("/api/notifications/read-all")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify all are read
        count_response = client.get("/api/notifications/count")
        assert count_response.json()["unread"] == 0


class TestDeleteNotification:
    """Test DELETE /api/notifications/{id} endpoint."""

    def test_delete_notification(self, client, sample_notifications):
        """Test deleting a notification."""
        response = client.delete("/api/notifications/1")
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify count changed
        count_response = client.get("/api/notifications/count")
        assert count_response.json()["total"] == 2

    def test_delete_notification_not_found(self, client, sample_notifications):
        """Test deleting non-existent notification."""
        response = client.delete("/api/notifications/999")
        assert response.status_code == 404


class TestClearNotifications:
    """Test DELETE /api/notifications endpoint."""

    def test_clear_read_notifications(self, client, sample_notifications):
        """Test clearing read notifications only."""
        response = client.delete("/api/notifications?read_only=true")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 1  # Only 1 read notification

        # Verify only unread remain
        count_response = client.get("/api/notifications/count")
        assert count_response.json()["total"] == 2
        assert count_response.json()["unread"] == 2

    def test_clear_all_notifications(self, client, sample_notifications):
        """Test clearing all notifications."""
        response = client.delete("/api/notifications?read_only=false")
        assert response.status_code == 200

        data = response.json()
        assert data["deleted_count"] == 3

        # Verify none remain
        count_response = client.get("/api/notifications/count")
        assert count_response.json()["total"] == 0
