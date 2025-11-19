"""Tests for profile API endpoints."""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app
from mindscout.database import get_session, Article, UserProfile


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def clean_db(tmp_path, monkeypatch):
    """Setup clean database."""
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))
    yield
    session = get_session()
    session.close()


@pytest.fixture
def sample_profile(tmp_path, monkeypatch):
    """Create sample user profile."""
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    session = get_session()

    profile = UserProfile(
        interests=["machine learning", "computer vision"],
        skill_level="advanced",
        preferred_sources=["arxiv", "semanticscholar"],
        daily_reading_goal=10
    )
    session.add(profile)
    session.commit()

    yield profile

    session.close()


@pytest.fixture
def sample_articles_for_stats(tmp_path, monkeypatch):
    """Create sample articles for statistics tests."""
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    session = get_session()

    # Create profile
    profile = UserProfile(
        interests=["ai"],
        skill_level="intermediate",
        daily_reading_goal=5
    )
    session.add(profile)

    # Create articles with different read/rating states
    articles = [
        Article(
            source_id="test-prof-1",
            title="Read Article 1",
            url="https://example.com/1",
            source="arxiv",
            fetched_date=datetime.now(),
            is_read=True,
            rating=5
        ),
        Article(
            source_id="test-prof-2",
            title="Read Article 2",
            url="https://example.com/2",
            source="arxiv",
            fetched_date=datetime.now(),
            is_read=True,
            rating=4
        ),
        Article(
            source_id="test-prof-3",
            title="Unread Article 1",
            url="https://example.com/3",
            source="semanticscholar",
            fetched_date=datetime.now(),
            is_read=False
        ),
        Article(
            source_id="test-prof-4",
            title="Unread Article 2",
            url="https://example.com/4",
            source="semanticscholar",
            fetched_date=datetime.now(),
            is_read=False
        ),
        Article(
            source_id="test-prof-5",
            title="Read No Rating",
            url="https://example.com/5",
            source="arxiv",
            fetched_date=datetime.now(),
            is_read=True
        )
    ]

    for article in articles:
        session.add(article)
    session.commit()

    yield {"profile": profile, "articles": articles}

    session.close()


class TestGetProfile:
    """Test GET /api/profile endpoint."""

    def test_get_profile_existing(self, client, sample_profile):
        """Test getting existing profile."""
        response = client.get("/api/profile")
        assert response.status_code == 200

        data = response.json()
        assert data["interests"] == ["machine learning", "computer vision"]
        assert data["skill_level"] == "advanced"
        assert data["preferred_sources"] == ["arxiv", "semanticscholar"]
        assert data["daily_reading_goal"] == 10

    def test_get_profile_creates_default(self, client, clean_db):
        """Test that getting profile creates default if none exists."""
        response = client.get("/api/profile")
        assert response.status_code == 200

        data = response.json()
        # Should have default values
        assert isinstance(data["interests"], list)
        assert data["skill_level"] in ["beginner", "intermediate", "advanced"]
        assert isinstance(data["daily_reading_goal"], int)


class TestUpdateProfile:
    """Test PUT /api/profile endpoint."""

    def test_update_profile_full(self, client, clean_db):
        """Test updating all profile fields."""
        profile_data = {
            "interests": ["nlp", "transformers", "llm"],
            "skill_level": "expert",
            "preferred_sources": ["arxiv"],
            "daily_reading_goal": 15
        }

        response = client.put("/api/profile", json=profile_data)
        assert response.status_code == 200

        data = response.json()
        assert data["interests"] == ["nlp", "transformers", "llm"]
        assert data["skill_level"] == "expert"
        assert data["preferred_sources"] == ["arxiv"]
        assert data["daily_reading_goal"] == 15

    def test_update_profile_partial(self, client, sample_profile):
        """Test updating only some fields."""
        update_data = {
            "interests": ["deep learning"],
            "skill_level": "advanced",
            "preferred_sources": ["arxiv", "semanticscholar"],
            "daily_reading_goal": 10
        }

        response = client.put("/api/profile", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["interests"] == ["deep learning"]
        # Other fields should remain
        assert data["daily_reading_goal"] == 10

    def test_update_profile_interests_only(self, client, sample_profile):
        """Test updating just interests."""
        # Need to provide all required fields
        update_data = {
            "interests": ["new interest"],
            "skill_level": "advanced",
            "preferred_sources": ["arxiv", "semanticscholar"],
            "daily_reading_goal": 10
        }

        response = client.put("/api/profile", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["interests"] == ["new interest"]

    def test_update_profile_invalid_skill_level(self, client, clean_db):
        """Test updating with invalid skill level."""
        profile_data = {
            "interests": ["ai"],
            "skill_level": "invalid_level",
            "preferred_sources": ["arxiv"],
            "daily_reading_goal": 5
        }

        response = client.put("/api/profile", json=profile_data)
        # Should return validation error
        assert response.status_code == 422


class TestGetProfileStats:
    """Test GET /api/profile/stats endpoint."""

    def test_get_stats_with_data(self, client, sample_articles_for_stats):
        """Test getting statistics with data."""
        response = client.get("/api/profile/stats")
        assert response.status_code == 200

        data = response.json()

        # Check total articles
        assert data["total_articles"] == 5

        # Check read articles
        assert data["read_articles"] == 3  # 2 rated + 1 read without rating
        assert data["read_percentage"] > 0

        # Check rated articles
        assert data["rated_articles"] == 2

        # Check average rating
        assert data["average_rating"] == 4.5  # (5 + 4) / 2

        # Check articles by source
        assert "articles_by_source" in data
        assert data["articles_by_source"]["arxiv"] == 3
        assert data["articles_by_source"]["semanticscholar"] == 2

    def test_get_stats_empty_db(self, client, clean_db):
        """Test getting statistics with no articles."""
        # Create empty profile
        session = get_session()
        profile = UserProfile(
            interests=["ai"],
            skill_level="beginner",
            daily_reading_goal=5
        )
        session.add(profile)
        session.commit()
        session.close()

        response = client.get("/api/profile/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_articles"] == 0
        assert data["read_articles"] == 0
        assert data["read_percentage"] == 0
        assert data["rated_articles"] == 0
        assert data["average_rating"] is None
        assert data["articles_by_source"] == {}

    def test_get_stats_creates_profile_if_missing(self, client, clean_db):
        """Test that stats endpoint creates profile if none exists."""
        response = client.get("/api/profile/stats")
        assert response.status_code == 200

        # Should return valid stats structure
        data = response.json()
        assert "total_articles" in data
        assert "read_articles" in data
        assert "read_percentage" in data


class TestGetProfileInsights:
    """Test GET /api/profile/insights endpoint."""

    def test_get_insights_with_data(self, client, sample_articles_for_stats):
        """Test getting insights with data."""
        response = client.get("/api/profile/insights")
        assert response.status_code == 200

        data = response.json()

        # Check reading progress
        assert "reading_progress" in data
        progress = data["reading_progress"]
        assert progress["total_articles"] == 5
        assert progress["read_articles"] == 3
        assert progress["unread_articles"] == 2

        # Check rating distribution
        assert "rating_distribution" in data
        ratings = data["rating_distribution"]
        assert ratings["5"] == 1
        assert ratings["4"] == 1

        # Check source breakdown
        assert "source_breakdown" in data
        sources = data["source_breakdown"]
        assert sources["arxiv"] == 3
        assert sources["semanticscholar"] == 2

        # Check daily progress
        assert "daily_progress" in data
        daily = data["daily_progress"]
        assert daily["goal"] == 5
        assert daily["read_today"] >= 0
        assert "days_to_catch_up" in daily

    def test_get_insights_empty_db(self, client, clean_db):
        """Test getting insights with no articles."""
        # Create empty profile
        session = get_session()
        profile = UserProfile(
            interests=["ai"],
            skill_level="beginner",
            daily_reading_goal=5
        )
        session.add(profile)
        session.commit()
        session.close()

        response = client.get("/api/profile/insights")
        assert response.status_code == 200

        data = response.json()
        assert data["reading_progress"]["total_articles"] == 0
        assert data["rating_distribution"] == {}
        assert data["source_breakdown"] == {}

    def test_get_insights_calculates_daily_progress(self, client, sample_articles_for_stats):
        """Test that daily progress is calculated correctly."""
        response = client.get("/api/profile/insights")
        assert response.status_code == 200

        data = response.json()
        daily = data["daily_progress"]

        assert "goal" in daily
        assert "read_today" in daily
        assert "percentage" in daily
        assert daily["percentage"] >= 0
        assert daily["percentage"] <= 100
