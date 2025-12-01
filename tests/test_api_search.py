"""Tests for search API endpoints."""

from datetime import datetime

import pytest

from mindscout.database import Article, get_session
from mindscout.vectorstore import VectorStore


@pytest.fixture
def sample_articles_with_embeddings(isolated_test_db):
    """Create sample articles and index them in vector store."""
    session = get_session()

    # Create sample articles with distinct topics
    articles = [
        Article(
            source_id="test-search-1",
            title="Attention Mechanisms in Transformers",
            authors="Author A",
            abstract="This paper explores attention mechanisms in transformer architectures for natural language processing.",
            url="https://example.com/1",
            source="arxiv",
            published_date=datetime(2024, 1, 15),
            fetched_date=datetime(2024, 1, 20),
            categories="cs.CL",
            is_read=False,
            citation_count=100,
            has_implementation=True,
        ),
        Article(
            source_id="test-search-2",
            title="Deep Reinforcement Learning for Robotics",
            authors="Author B",
            abstract="We present a deep reinforcement learning approach for robotic manipulation tasks.",
            url="https://example.com/2",
            source="arxiv",
            published_date=datetime(2024, 2, 10),
            fetched_date=datetime(2024, 2, 15),
            categories="cs.RO",
            is_read=False,
            citation_count=50,
        ),
        Article(
            source_id="test-search-3",
            title="Computer Vision with Convolutional Networks",
            authors="Author C",
            abstract="An analysis of convolutional neural networks for image classification tasks.",
            url="https://example.com/3",
            source="semanticscholar",
            published_date=datetime(2024, 3, 5),
            fetched_date=datetime(2024, 3, 10),
            categories="cs.CV",
            is_read=False,
            citation_count=75,
        ),
    ]

    for article in articles:
        session.add(article)
    session.commit()

    # Index articles in vector store
    vector_store = VectorStore()
    try:
        for article in articles:
            vector_store.add_article(article)
    finally:
        vector_store.close()

    yield articles

    session.close()


class TestSemanticSearch:
    """Test GET /api/search endpoint."""

    def test_search_basic(self, client, sample_articles_with_embeddings):
        """Test basic semantic search."""
        response = client.get("/api/search?q=transformer&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check response structure
        result = data[0]
        assert "article" in result
        assert "relevance" in result
        assert isinstance(result["relevance"], float)
        assert 0 <= result["relevance"] <= 1

        # Check article structure
        article = result["article"]
        assert "id" in article
        assert "title" in article
        assert "authors" in article
        assert "abstract" in article

    def test_search_transformers(self, client, sample_articles_with_embeddings):
        """Test searching for transformers returns relevant results."""
        response = client.get("/api/search?q=attention+transformers&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        # The transformer paper should be most relevant
        top_result = data[0]
        assert (
            "transformer" in top_result["article"]["title"].lower()
            or "attention" in top_result["article"]["title"].lower()
        )

    def test_search_robotics(self, client, sample_articles_with_embeddings):
        """Test searching for robotics returns relevant results."""
        response = client.get("/api/search?q=robotics+manipulation&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        # Should find the robotics paper
        titles = [r["article"]["title"].lower() for r in data]
        assert any("robot" in title for title in titles)

    def test_search_limit(self, client, sample_articles_with_embeddings):
        """Test search respects limit parameter."""
        response = client.get("/api/search?q=machine+learning&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 2

    def test_search_short_query_rejected(self, client, sample_articles_with_embeddings):
        """Test that queries shorter than 3 characters are rejected."""
        response = client.get("/api/search?q=ab&limit=10")
        assert response.status_code == 422  # Validation error

    def test_search_relevance_scores_ordered(self, client, sample_articles_with_embeddings):
        """Test that results are ordered by relevance score."""
        response = client.get("/api/search?q=neural+networks&limit=10")
        assert response.status_code == 200

        data = response.json()
        if len(data) > 1:
            # Check that relevance scores are in descending order
            scores = [r["relevance"] for r in data]
            assert scores == sorted(scores, reverse=True)


class TestSearchStats:
    """Test GET /api/search/stats endpoint."""

    def test_search_stats(self, client, sample_articles_with_embeddings):
        """Test getting vector store statistics."""
        response = client.get("/api/search/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_indexed" in data
        # Check that we have at least the articles we indexed
        assert data["total_indexed"] >= 3

    def test_search_stats_returns_valid_structure(self, client, isolated_test_db):
        """Test stats returns valid structure."""
        response = client.get("/api/search/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_indexed" in data
        assert isinstance(data["total_indexed"], int)
        assert data["total_indexed"] >= 0
