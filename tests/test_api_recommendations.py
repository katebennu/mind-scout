"""Tests for recommendations API endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from mindscout.database import get_session, Article, UserProfile
from mindscout.vectorstore import VectorStore


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_articles_with_profile(tmp_path, monkeypatch):
    """Create sample articles and user profile."""
    # Use temporary database
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    session = get_session()

    # Create user profile
    profile = UserProfile(
        interests=["transformers", "natural language processing"],
        skill_level="intermediate",
        preferred_sources=["arxiv"],
        daily_reading_goal=5
    )
    session.add(profile)
    session.commit()

    # Create sample articles
    articles = [
        Article(
            source_id="test-rec-1",
            title="Attention Is All You Need",
            authors="Vaswani et al.",
            abstract="We propose a new architecture based solely on attention mechanisms, dispensing with recurrence.",
            url="https://example.com/1",
            source="arxiv",
            published_date=datetime(2024, 1, 15),
            fetched_date=datetime(2024, 1, 20),
            categories="cs.CL",
            is_read=False,
            citation_count=50000,
            has_implementation=True,
            github_url="https://github.com/tensorflow/tensor2tensor",
            topics="transformers,attention,nlp"
        ),
        Article(
            source_id="test-rec-2",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors="Devlin et al.",
            abstract="We introduce BERT, designed to pre-train deep bidirectional representations.",
            url="https://example.com/2",
            source="arxiv",
            published_date=datetime(2024, 2, 10),
            fetched_date=datetime(2024, 2, 15),
            categories="cs.CL",
            is_read=False,
            citation_count=30000,
            has_implementation=True,
            topics="transformers,nlp,bert"
        ),
        Article(
            source_id="test-rec-3",
            title="Deep Reinforcement Learning",
            authors="Mnih et al.",
            abstract="We present an agent that learns to play Atari games using deep reinforcement learning.",
            url="https://example.com/3",
            source="arxiv",
            published_date=datetime(2024, 3, 5),
            fetched_date=datetime(2024, 3, 10),
            categories="cs.LG",
            is_read=True,
            rating=5,
            citation_count=10000,
            topics="reinforcement learning,deep learning"
        ),
        Article(
            source_id="test-rec-4",
            title="Old Computer Vision Paper",
            authors="Author D",
            abstract="An old paper about computer vision from many years ago.",
            url="https://example.com/4",
            source="semanticscholar",
            published_date=datetime(2020, 1, 1),
            fetched_date=datetime(2024, 1, 10),
            categories="cs.CV",
            is_read=False,
            citation_count=100,
            topics="computer vision"
        )
    ]

    for article in articles:
        session.add(article)
    session.commit()

    # Index articles in vector store for semantic recommendations
    vector_store = VectorStore()
    try:
        for article in articles:
            vector_store.add_article(article)
    finally:
        vector_store.close()

    yield {"articles": articles, "profile": profile}

    session.close()


class TestGetRecommendations:
    """Test GET /api/recommendations endpoint."""

    def test_get_recommendations_default(self, client, sample_articles_with_profile):
        """Test getting recommendations with default parameters."""
        response = client.get("/api/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check response structure
        rec = data[0]
        assert "article" in rec
        assert "score" in rec
        assert "reasons" in rec
        assert isinstance(rec["score"], float)
        assert isinstance(rec["reasons"], list)

    def test_get_recommendations_limit(self, client, sample_articles_with_profile):
        """Test recommendations respect limit parameter."""
        response = client.get("/api/recommendations?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 2

    def test_get_recommendations_prefer_interests(self, client, sample_articles_with_profile):
        """Test that recommendations prefer articles matching user interests."""
        response = client.get("/api/recommendations?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        # Top recommendations should be transformer papers (matching interests)
        top_titles = [r["article"]["title"].lower() for r in data[:2]]
        transformer_related = sum(
            1 for title in top_titles
            if "transformer" in title or "bert" in title or "attention" in title
        )
        assert transformer_related > 0

    def test_get_recommendations_reasons(self, client, sample_articles_with_profile):
        """Test that recommendations include reasons."""
        response = client.get("/api/recommendations?limit=5")
        assert response.status_code == 200

        data = response.json()
        for rec in data:
            assert len(rec["reasons"]) > 0
            # Reasons should be descriptive strings
            for reason in rec["reasons"]:
                assert isinstance(reason, str)
                assert len(reason) > 0

    def test_get_recommendations_scores_ordered(self, client, sample_articles_with_profile):
        """Test that recommendations are ordered by score."""
        response = client.get("/api/recommendations?limit=10")
        assert response.status_code == 200

        data = response.json()
        if len(data) > 1:
            scores = [r["score"] for r in data]
            assert scores == sorted(scores, reverse=True)

    def test_get_recommendations_min_score(self, client, sample_articles_with_profile):
        """Test minimum score filtering."""
        response = client.get("/api/recommendations?min_score=0.5&limit=10")
        assert response.status_code == 200

        data = response.json()
        # All recommendations should have score >= 0.5
        for rec in data:
            assert rec["score"] >= 0.5

    def test_get_recommendations_days_back(self, client, sample_articles_with_profile):
        """Test filtering by days back."""
        # Only recent articles (exclude the old 2020 paper)
        response = client.get("/api/recommendations?days_back=365&limit=10")
        assert response.status_code == 200

        data = response.json()
        # Should not include the 2020 paper
        titles = [r["article"]["title"] for r in data]
        assert "Old Computer Vision Paper" not in titles


class TestGetSimilarArticles:
    """Test GET /api/recommendations/{article_id}/similar endpoint."""

    def test_get_similar_articles(self, client, sample_articles_with_profile):
        """Test getting similar articles."""
        # Get articles similar to the first transformer paper
        response = client.get("/api/recommendations/1/similar?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check response structure
        rec = data[0]
        assert "article" in rec
        assert "score" in rec
        assert "reasons" in rec

        # Reason should mention similarity percentage
        assert any("similar" in reason.lower() for reason in rec["reasons"])

    def test_get_similar_articles_excludes_self(self, client, sample_articles_with_profile):
        """Test that similar articles don't include the source article."""
        response = client.get("/api/recommendations/1/similar?limit=10")
        assert response.status_code == 200

        data = response.json()
        # Should not include article 1 itself
        article_ids = [r["article"]["id"] for r in data]
        assert 1 not in article_ids

    def test_get_similar_articles_min_similarity(self, client, sample_articles_with_profile):
        """Test minimum similarity filtering."""
        response = client.get("/api/recommendations/1/similar?min_similarity=0.5&limit=10")
        assert response.status_code == 200

        data = response.json()
        # All results should have score >= 0.5
        for rec in data:
            assert rec["score"] >= 0.5

    def test_get_similar_articles_ordered(self, client, sample_articles_with_profile):
        """Test that similar articles are ordered by similarity."""
        response = client.get("/api/recommendations/1/similar?limit=10")
        assert response.status_code == 200

        data = response.json()
        if len(data) > 1:
            scores = [r["score"] for r in data]
            assert scores == sorted(scores, reverse=True)


class TestSemanticRecommendations:
    """Test GET /api/recommendations/semantic endpoint."""

    def test_semantic_recommendations_default(self, client, sample_articles_with_profile):
        """Test semantic recommendations with default parameters."""
        response = client.get("/api/recommendations/semantic")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_semantic_recommendations_use_interests(self, client, sample_articles_with_profile):
        """Test semantic recommendations based on interests."""
        response = client.get("/api/recommendations/semantic?use_interests=true&use_reading_history=false&limit=5")
        assert response.status_code == 200

        data = response.json()
        if len(data) > 0:
            # Should prioritize transformer papers (matching interests)
            assert "article" in data[0]
            assert "score" in data[0]

    def test_semantic_recommendations_use_reading_history(self, client, sample_articles_with_profile):
        """Test semantic recommendations based on reading history."""
        response = client.get("/api/recommendations/semantic?use_interests=false&use_reading_history=true&limit=5")
        assert response.status_code == 200

        data = response.json()
        # Should work even with reading history only
        assert isinstance(data, list)

    def test_semantic_recommendations_limit(self, client, sample_articles_with_profile):
        """Test that semantic recommendations respect limit."""
        response = client.get("/api/recommendations/semantic?limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 2
