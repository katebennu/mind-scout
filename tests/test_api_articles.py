"""Tests for articles API endpoints."""

from datetime import datetime

import pytest

from mindscout.database import Article, get_session


@pytest.fixture
def sample_articles(isolated_test_db):
    """Create sample articles in test database."""
    session = get_session()

    # Create sample articles
    articles = [
        Article(
            source_id="test-arxiv-1",
            title="Test Article 1",
            authors="Author A, Author B",
            abstract="This is a test abstract about transformers.",
            url="https://example.com/1",
            source="arxiv",
            source_name="arXiv cs.AI",
            published_date=datetime(2024, 1, 15),
            fetched_date=datetime(2024, 1, 20),
            categories="cs.AI",
            is_read=False,
            citation_count=10,
            has_implementation=True,
            github_url="https://github.com/test/1",
        ),
        Article(
            source_id="test-ss-2",
            title="Test Article 2",
            authors="Author C",
            abstract="Another test abstract about reinforcement learning.",
            url="https://example.com/2",
            source="semanticscholar",
            source_name="semanticscholar",
            published_date=datetime(2024, 2, 10),
            fetched_date=datetime(2024, 2, 15),
            categories="cs.LG",
            is_read=True,
            rating=5,
            citation_count=50,
            has_implementation=False,
        ),
        Article(
            source_id="test-arxiv-3",
            title="Test Article 3",
            authors="Author D, Author E",
            abstract="Third test abstract about computer vision.",
            url="https://example.com/3",
            source="arxiv",
            source_name="arXiv cs.AI",
            published_date=datetime(2024, 3, 5),
            fetched_date=datetime(2024, 3, 10),
            categories="cs.CV",
            is_read=False,
            citation_count=25,
            has_implementation=True,
            github_url="https://github.com/test/3",
        ),
    ]

    for article in articles:
        session.add(article)
    session.commit()

    yield articles

    session.close()


class TestListSources:
    """Test GET /api/articles/sources endpoint."""

    def test_list_sources(self, client, sample_articles):
        """Test listing distinct sources."""
        response = client.get("/api/articles/sources")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2  # arxiv and semanticscholar

        # Check structure
        for source in data:
            assert "source" in source
            assert "source_name" in source
            assert "count" in source

    def test_list_sources_empty(self, client, isolated_test_db):
        """Test listing sources when no articles exist."""
        response = client.get("/api/articles/sources")
        assert response.status_code == 200
        assert response.json() == []


class TestListArticles:
    """Test GET /api/articles endpoint."""

    def test_list_articles_default(self, client, sample_articles):
        """Test listing articles with default parameters."""
        response = client.get("/api/articles")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert len(data["articles"]) == 3

    def test_list_articles_pagination(self, client, sample_articles):
        """Test pagination."""
        response = client.get("/api/articles?page=1&page_size=2")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["articles"]) == 2

    def test_list_articles_unread_only(self, client, sample_articles):
        """Test filtering unread articles."""
        response = client.get("/api/articles?unread_only=true")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2  # Only 2 unread articles
        assert all(not article["is_read"] for article in data["articles"])

    def test_list_articles_filter_by_source(self, client, sample_articles):
        """Test filtering by source."""
        response = client.get("/api/articles?source=arxiv")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 2  # Only 2 arxiv articles
        assert all(article["source"] == "arxiv" for article in data["articles"])

    def test_list_articles_filter_by_source_name(self, client, sample_articles):
        """Test filtering by source_name."""
        response = client.get("/api/articles?source_name=semanticscholar")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 1
        assert data["articles"][0]["source_name"] == "semanticscholar"

    def test_list_articles_sort_by_rating(self, client, sample_articles):
        """Test sorting by rating."""
        response = client.get("/api/articles?sort_by=rating&sort_order=desc")
        assert response.status_code == 200

        data = response.json()
        assert response.status_code == 200
        # First article should be the one with rating
        assert data["articles"][0]["rating"] == 5


class TestGetArticle:
    """Test GET /api/articles/{article_id} endpoint."""

    def test_get_article_success(self, client, sample_articles):
        """Test getting a single article."""
        response = client.get("/api/articles/1")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Article 1"
        assert data["authors"] == "Author A, Author B"
        assert data["source"] == "arxiv"

    def test_get_article_not_found(self, client, sample_articles):
        """Test getting non-existent article."""
        response = client.get("/api/articles/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestMarkArticleRead:
    """Test POST /api/articles/{article_id}/read endpoint."""

    def test_mark_article_read(self, client, sample_articles):
        """Test marking article as read."""
        response = client.post("/api/articles/1/read", json={"is_read": True})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["is_read"] is True

        # Verify article is marked as read
        get_response = client.get("/api/articles/1")
        assert get_response.json()["is_read"] is True

    def test_mark_article_unread(self, client, sample_articles):
        """Test marking article as unread."""
        response = client.post("/api/articles/2/read", json={"is_read": False})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["is_read"] is False

    def test_mark_read_not_found(self, client, sample_articles):
        """Test marking non-existent article as read."""
        response = client.post("/api/articles/999/read", json={"is_read": True})
        assert response.status_code == 404


class TestRateArticle:
    """Test POST /api/articles/{article_id}/rate endpoint."""

    def test_rate_article_success(self, client, sample_articles):
        """Test rating an article."""
        response = client.post("/api/articles/1/rate", json={"rating": 4})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["rating"] == 4

        # Verify article is rated and marked as read
        get_response = client.get("/api/articles/1")
        article = get_response.json()
        assert article["rating"] == 4
        assert article["is_read"] is True

    def test_rate_article_invalid_rating_too_low(self, client, sample_articles):
        """Test rating with value < 1."""
        response = client.post("/api/articles/1/rate", json={"rating": 0})
        assert response.status_code == 400
        assert "between 1 and 5" in response.json()["detail"]

    def test_rate_article_invalid_rating_too_high(self, client, sample_articles):
        """Test rating with value > 5."""
        response = client.post("/api/articles/1/rate", json={"rating": 6})
        assert response.status_code == 400
        assert "between 1 and 5" in response.json()["detail"]

    def test_rate_article_not_found(self, client, sample_articles):
        """Test rating non-existent article."""
        response = client.post("/api/articles/999/rate", json={"rating": 5})
        assert response.status_code == 404
