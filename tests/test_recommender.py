"""Tests for recommendation engine."""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from mindscout.database import get_session, Article, UserProfile


@pytest.fixture
def sample_articles(isolated_test_db):
    """Create sample articles for testing."""
    session = get_session()

    now = datetime.utcnow()
    articles = [
        Article(
            id=1,
            source_id="rec-test-1",
            title="Machine Learning Survey",
            abstract="A survey of machine learning techniques",
            url="https://example.com/1",
            source="arxiv",
            topics='["machine learning", "survey", "neural networks"]',
            categories="cs.LG, cs.AI",
            fetched_date=now - timedelta(days=5),
            published_date=now - timedelta(days=10),
            citation_count=150,
            processed=True,
            is_read=False,
        ),
        Article(
            id=2,
            source_id="rec-test-2",
            title="Deep Learning Tutorial",
            abstract="Introduction to deep learning",
            url="https://example.com/2",
            source="arxiv",
            topics='["deep learning", "tutorial", "neural networks"]',
            fetched_date=now - timedelta(days=3),
            published_date=now - timedelta(days=7),
            citation_count=500,
            processed=True,
            is_read=False,
        ),
        Article(
            id=3,
            source_id="rec-test-3",
            title="Advanced Transformer Architecture",
            abstract="Novel transformer architecture for NLP",
            url="https://example.com/3",
            source="semanticscholar",
            topics='["transformers", "NLP", "attention"]',
            fetched_date=now - timedelta(days=1),
            published_date=now - timedelta(days=30),
            citation_count=20,
            processed=True,
            is_read=False,
            has_implementation=True,
            github_url="https://github.com/example/transformer",
        ),
        Article(
            id=4,
            source_id="rec-test-4",
            title="Old Article",
            abstract="An old article",
            url="https://example.com/4",
            source="arxiv",
            topics='["machine learning"]',
            fetched_date=now - timedelta(days=100),
            published_date=now - timedelta(days=120),
            processed=True,
            is_read=True,  # Already read
        ),
        Article(
            id=5,
            source_id="rec-test-5",
            title="Recent Paper",
            abstract="Recent research paper",
            url="https://example.com/5",
            source="arxiv",
            topics='["reinforcement learning"]',
            fetched_date=now - timedelta(days=1),
            published_date=now - timedelta(days=2),
            processed=True,
            is_read=False,
        ),
    ]

    for article in articles:
        session.add(article)
    session.commit()

    yield articles

    session.close()


@pytest.fixture
def sample_profile(isolated_test_db):
    """Create sample user profile."""
    session = get_session()

    profile = UserProfile(
        interests="machine learning, neural networks, deep learning",
        skill_level="intermediate",
        preferred_sources="arxiv",
    )
    session.add(profile)
    session.commit()

    yield profile

    session.close()


class TestRecommendationEngineInit:
    """Test RecommendationEngine initialization."""

    def test_init(self, isolated_test_db):
        """Test basic initialization."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        assert engine.session is not None
        assert engine.profile_manager is not None

        engine.close()


class TestGetRecommendations:
    """Test RecommendationEngine.get_recommendations method."""

    def test_get_recommendations_basic(self, sample_articles, sample_profile, isolated_test_db):
        """Test basic recommendations."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        recs = engine.get_recommendations(limit=5)

        assert len(recs) > 0
        assert all("article" in rec for rec in recs)
        assert all("score" in rec for rec in recs)
        assert all("reasons" in rec for rec in recs)

        engine.close()

    def test_get_recommendations_respects_limit(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that limit is respected."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        recs = engine.get_recommendations(limit=2)

        assert len(recs) <= 2

        engine.close()

    def test_get_recommendations_excludes_read(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that read articles are excluded."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        recs = engine.get_recommendations(unread_only=True)

        article_ids = [rec["article"].id for rec in recs]
        assert 4 not in article_ids  # Article 4 is read

        engine.close()

    def test_get_recommendations_includes_read_when_disabled(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that read articles are included when filter is disabled."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        recs = engine.get_recommendations(unread_only=False, days_back=150)

        article_ids = [rec["article"].id for rec in recs]
        assert 4 in article_ids  # Article 4 should be included

        engine.close()

    def test_get_recommendations_sorted_by_score(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that recommendations are sorted by score."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        recs = engine.get_recommendations(limit=5)

        if len(recs) > 1:
            scores = [rec["score"] for rec in recs]
            assert scores == sorted(scores, reverse=True)

        engine.close()


class TestScoreTopics:
    """Test topic scoring."""

    def test_score_topics_with_matches(self, sample_articles, isolated_test_db):
        """Test topic scoring with matching interests."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[0]
        interests = ["machine learning", "neural networks"]

        score = engine._score_topics(article, interests)

        assert score > 0
        assert score <= 1.0

        engine.close()

    def test_score_topics_no_interests(self, sample_articles, isolated_test_db):
        """Test topic scoring without interests."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[0]
        score = engine._score_topics(article, [])

        assert score == 0.0

        engine.close()

    def test_score_topics_no_topics(self, isolated_test_db):
        """Test topic scoring without article topics."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        article = Article(
            source_id="no-topics",
            title="No Topics",
            url="https://example.com/no-topics",
            source="test",
            topics=None,
        )
        session.add(article)
        session.commit()

        engine = RecommendationEngine()
        score = engine._score_topics(article, ["machine learning"])

        assert score == 0.0

        session.close()
        engine.close()

    def test_score_topics_falls_back_to_categories(self, isolated_test_db):
        """Test fallback to categories when topics are invalid JSON."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        article = Article(
            source_id="category-test",
            title="Category Test",
            url="https://example.com/cat",
            source="test",
            topics="invalid json",
            categories="machine learning, AI",
        )
        session.add(article)
        session.commit()

        engine = RecommendationEngine()
        score = engine._score_topics(article, ["machine learning"])

        assert score > 0

        session.close()
        engine.close()


class TestScoreCitations:
    """Test citation scoring."""

    def test_score_citations_high_count(self, sample_articles, isolated_test_db):
        """Test citation scoring with high count."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[1]  # 500 citations
        score = engine._score_citations(article)

        assert score > 0.5

        engine.close()

    def test_score_citations_no_count(self, isolated_test_db):
        """Test citation scoring without citations."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        article = Article(
            source_id="no-citations",
            title="No Citations",
            url="https://example.com/no-cit",
            source="test",
            citation_count=None,
        )
        session.add(article)
        session.commit()

        engine = RecommendationEngine()
        score = engine._score_citations(article)

        assert score == 0.0

        session.close()
        engine.close()


class TestScoreSource:
    """Test source preference scoring."""

    def test_score_source_preferred(self, sample_articles, sample_profile, isolated_test_db):
        """Test scoring for preferred source."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[0]  # arxiv
        profile = sample_profile

        score = engine._score_source(article, profile)

        assert score == 1.0

        engine.close()

    def test_score_source_not_preferred(self, sample_articles, sample_profile, isolated_test_db):
        """Test scoring for non-preferred source."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[2]  # semanticscholar
        profile = sample_profile

        score = engine._score_source(article, profile)

        assert score == 0.0

        engine.close()

    def test_score_source_no_preference(self, sample_articles, isolated_test_db):
        """Test scoring when no source preference set."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        profile = UserProfile(interests="machine learning")
        session.add(profile)
        session.commit()

        engine = RecommendationEngine()
        article = sample_articles[0]

        score = engine._score_source(article, profile)

        assert score == 0.5  # Neutral

        session.close()
        engine.close()


class TestScoreRecency:
    """Test recency scoring."""

    def test_score_recency_recent(self, sample_articles, isolated_test_db):
        """Test scoring for recent article."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[4]  # 2 days old
        score = engine._score_recency(article)

        assert score == 1.0

        engine.close()

    def test_score_recency_old(self, sample_articles, isolated_test_db):
        """Test scoring for old article."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[3]  # 120 days old
        score = engine._score_recency(article)

        assert score <= 0.3

        engine.close()

    def test_score_recency_no_date(self, isolated_test_db):
        """Test scoring without published date."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        article = Article(
            source_id="no-date",
            title="No Date",
            url="https://example.com/no-date",
            source="test",
            published_date=None,
        )
        session.add(article)
        session.commit()

        engine = RecommendationEngine()
        score = engine._score_recency(article)

        assert score == 0.5  # Neutral

        session.close()
        engine.close()


class TestScoreSkillMatch:
    """Test skill level matching."""

    def test_score_skill_beginner_survey(self, sample_articles, isolated_test_db):
        """Test beginner preference for surveys."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        profile = UserProfile(interests="machine learning", skill_level="beginner")
        session.add(profile)
        session.commit()

        engine = RecommendationEngine()

        article = sample_articles[0]  # "Machine Learning Survey"
        score = engine._score_skill_match(article, profile)

        assert score == 1.0  # Perfect match for survey

        session.close()
        engine.close()

    def test_score_skill_advanced_recent(self, sample_articles, isolated_test_db):
        """Test advanced preference for recent papers."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        profile = UserProfile(interests="machine learning", skill_level="advanced")
        session.add(profile)
        session.commit()

        engine = RecommendationEngine()

        article = sample_articles[4]  # 2 days old
        score = engine._score_skill_match(article, profile)

        assert score >= 0.9  # High score for recent paper

        session.close()
        engine.close()

    def test_score_skill_no_skill_set(self, sample_articles, isolated_test_db):
        """Test scoring when skill level not set."""
        from mindscout.recommender import RecommendationEngine

        session = get_session()
        profile = UserProfile(interests="machine learning")
        session.add(profile)
        session.commit()

        engine = RecommendationEngine()

        article = sample_articles[0]
        score = engine._score_skill_match(article, profile)

        assert score == 0.5  # Neutral

        session.close()
        engine.close()


class TestExplainRecommendation:
    """Test recommendation explanation."""

    def test_explain_recommendation(self, sample_articles, sample_profile, isolated_test_db):
        """Test explaining a recommendation."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()

        article = sample_articles[0]
        explanation = engine.explain_recommendation(article)

        assert explanation["article_id"] == article.id
        assert "overall_score" in explanation
        assert "reasons" in explanation
        assert "details" in explanation
        assert "topic_match" in explanation["details"]
        assert "citation_score" in explanation["details"]

        engine.close()


class TestGetSemanticRecommendations:
    """Test semantic recommendations."""

    def test_semantic_recommendations_with_interests(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test semantic recommendations using interests."""
        from mindscout.recommender import RecommendationEngine

        # Mock VectorStore at the module level where it's imported
        mock_vector_store = MagicMock()
        mock_vector_store.semantic_search.return_value = [
            {"article": sample_articles[0], "relevance": 0.9}
        ]

        with patch("mindscout.vectorstore.VectorStore", return_value=mock_vector_store):
            engine = RecommendationEngine()
            recs = engine.get_semantic_recommendations(
                limit=5, use_interests=True, use_reading_history=False
            )

            assert len(recs) >= 0  # May be empty if no unread articles

            engine.close()

    def test_semantic_recommendations_deduplicates(
        self, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that duplicate articles are removed."""
        from mindscout.recommender import RecommendationEngine

        mock_vector_store = MagicMock()
        # Return same article multiple times
        mock_vector_store.semantic_search.return_value = [
            {"article": sample_articles[0], "relevance": 0.9},
            {"article": sample_articles[0], "relevance": 0.8},
        ]
        mock_vector_store.find_similar.return_value = []

        with patch("mindscout.vectorstore.VectorStore", return_value=mock_vector_store):
            engine = RecommendationEngine()
            recs = engine.get_semantic_recommendations(
                limit=5, use_interests=True, use_reading_history=False
            )

            # Should only have one instance of the article
            article_ids = [rec["article"].id for rec in recs]
            assert len(article_ids) == len(set(article_ids))

            engine.close()


class TestClose:
    """Test closing the engine."""

    def test_close(self, isolated_test_db):
        """Test closing database sessions."""
        from mindscout.recommender import RecommendationEngine

        engine = RecommendationEngine()
        engine.close()

        # Should not raise an error
        assert True
