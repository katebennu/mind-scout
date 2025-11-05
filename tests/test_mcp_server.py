"""Tests for MCP server tools."""

import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
import pytest
import importlib.util

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mindscout.database import get_session, Article, UserProfile

# Import the MCP server module (handling the hyphenated name)
spec = importlib.util.spec_from_file_location(
    "mcp_server",
    Path(__file__).parent.parent / "mcp-server" / "server.py"
)
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    session = get_session()

    # Clear existing data
    session.query(Article).delete()
    session.query(UserProfile).delete()

    articles = [
        Article(
            source_id="arxiv_001",
            source="arxiv",
            title="Attention Is All You Need",
            authors="Vaswani et al.",
            abstract="We propose a new simple network architecture, the Transformer.",
            url="https://arxiv.org/abs/1706.03762",
            published_date=datetime(2017, 6, 12),
            citation_count=50000,
            is_read=False,
            rating=None
        ),
        Article(
            source_id="arxiv_002",
            source="arxiv",
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            authors="Devlin et al.",
            abstract="We introduce BERT, a new language representation model.",
            url="https://arxiv.org/abs/1810.04805",
            published_date=datetime(2018, 10, 11),
            citation_count=40000,
            is_read=True,
            rating=5
        ),
        Article(
            source_id="ss_001",
            source="semanticscholar",
            title="GPT-3: Language Models are Few-Shot Learners",
            authors="Brown et al.",
            abstract="We show that scaling up language models greatly improves task-agnostic performance.",
            url="https://arxiv.org/abs/2005.14165",
            published_date=datetime(2020, 5, 28),
            citation_count=30000,
            is_read=False,
            rating=None
        )
    ]

    for article in articles:
        session.add(article)

    session.commit()

    # Get the IDs after commit
    article_ids = [a.id for a in articles]

    yield article_ids

    # Cleanup
    session.query(Article).delete()
    session.query(UserProfile).delete()
    session.commit()
    session.close()


@pytest.fixture
def sample_profile():
    """Create sample user profile for testing."""
    session = get_session()

    profile = UserProfile(
        interests=["transformers", "natural language processing"],
        skill_level="intermediate",
        preferred_sources=["arxiv"],
        daily_reading_goal=5
    )

    session.add(profile)
    session.commit()

    yield profile

    session.query(UserProfile).delete()
    session.commit()
    session.close()


class TestSearchPapers:
    """Tests for mcp_server.search_papers tool."""

    def test_mcp_server.search_papers_basic(self, sample_articles):
        """Test basic semantic search functionality."""
        # Mock VectorStore
        with patch('mcp_server.VectorStore') as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance

            # Mock search results
            session = get_session()
            article = session.query(Article).first()
            session.close()

            mock_instance.semantic_search.return_value = [
                {
                    "article": article,
                    "relevance": 0.85
                }
            ]

            results = mcp_server.mcp_server.search_papers(query="transformers", limit=5)

            assert len(results) == 1
            assert results[0]["title"] == article.title
            assert results[0]["relevance_score"] == 85.0
            mock_instance.close.assert_called_once()

    def test_mcp_server.search_papers_empty_results(self):
        """Test search with no results."""
        with patch('mcp_server.VectorStore') as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance
            mock_instance.semantic_search.return_value = []

            results = mcp_server.mcp_server.search_papers(query="nonexistent topic", limit=10)

            assert results == []
            mock_instance.close.assert_called_once()

    def test_mcp_server.search_papers_limit(self, sample_articles):
        """Test that limit parameter works correctly."""
        with patch('mcp_server.VectorStore') as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance

            mock_instance.semantic_search.return_value = []

            mcp_server.mcp_server.search_papers(query="test", limit=3)

            mock_instance.semantic_search.assert_called_once_with(query="test", n_results=3)


class TestGetRecommendations:
    """Tests for mcp_server.get_recommendations tool."""

    def test_mcp_server.get_recommendations_basic(self, sample_articles, sample_profile):
        """Test getting recommendations."""
mcp_server.get_recommendations

        with patch('mcp_server.RecommendationEngine') as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value = mock_instance

            session = get_session()
            article = session.query(Article).filter(Article.is_read == False).first()
            session.close()

            mock_instance.mcp_server.get_recommendations.return_value = [
                {
                    "article": article,
                    "score": 0.92,
                    "reasons": ["Matches interests: transformers", "High citation count"]
                }
            ]

            results = mcp_server.get_recommendations(limit=5)

            assert len(results) == 1
            assert results[0]["title"] == article.title
            assert results[0]["match_score"] == 92.0
            assert len(results[0]["reasons"]) == 2
            mock_instance.close.assert_called_once()

    def test_mcp_server.get_recommendations_empty(self):
        """Test recommendations with no results."""
mcp_server.get_recommendations

        with patch('mcp_server.RecommendationEngine') as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value = mock_instance
            mock_instance.mcp_server.get_recommendations.return_value = []

            results = mcp_server.get_recommendations(limit=10)

            assert results == []


class TestGetArticle:
    """Tests for mcp_server.get_article tool."""

    def test_mcp_server.get_article_success(self, sample_articles):
        """Test getting a specific article."""
mcp_server.get_article

        article_id = sample_articles[0]
        result = mcp_server.get_article(article_id=article_id)

        assert result["id"] == article_id
        assert "title" in result
        assert "authors" in result
        assert "abstract" in result
        assert "url" in result

    def test_mcp_server.get_article_not_found(self):
        """Test getting a non-existent article."""
mcp_server.get_article

        result = mcp_server.get_article(article_id=99999)

        assert "error" in result
        assert "not found" in result["error"]


class TestListArticles:
    """Tests for mcp_server.list_articles tool."""

    def test_mcp_server.list_articles_basic(self, sample_articles):
        """Test listing articles with default parameters."""
mcp_server.list_articles

        result = mcp_server.list_articles()

        assert "articles" in result
        assert "total" in result
        assert result["total"] == 3
        assert len(result["articles"]) == 3
        assert result["page"] == 1

    def test_mcp_server.list_articles_pagination(self, sample_articles):
        """Test pagination."""
mcp_server.list_articles

        result = mcp_server.list_articles(page=1, page_size=2)

        assert len(result["articles"]) == 2
        assert result["total"] == 3
        assert result["total_pages"] == 2

        # Second page
        result2 = mcp_server.list_articles(page=2, page_size=2)
        assert len(result2["articles"]) == 1

    def test_mcp_server.list_articles_unread_only(self, sample_articles):
        """Test filtering by unread status."""
mcp_server.list_articles

        result = mcp_server.list_articles(unread_only=True)

        assert result["total"] == 2  # Two unread articles
        for article in result["articles"]:
            assert article["is_read"] == False

    def test_mcp_server.list_articles_filter_by_source(self, sample_articles):
        """Test filtering by source."""
mcp_server.list_articles

        result = mcp_server.list_articles(source="arxiv")

        assert result["total"] == 2  # Two arxiv articles
        for article in result["articles"]:
            assert article["source"] == "arxiv"

    def test_mcp_server.list_articles_sort_by_citations(self, sample_articles):
        """Test sorting by citation count."""
mcp_server.list_articles

        result = mcp_server.list_articles(sort_by="citations")

        # First article should have highest citations
        assert result["articles"][0]["citation_count"] >= result["articles"][1]["citation_count"]

    def test_mcp_server.list_articles_sort_by_rating(self, sample_articles):
        """Test sorting by rating."""
mcp_server.list_articles

        result = mcp_server.list_articles(sort_by="rating")

        # Articles with ratings should come first
        if result["articles"][0]["rating"] is not None:
            assert result["articles"][0]["rating"] == 5


class TestRateArticle:
    """Tests for mcp_server.rate_article tool."""

    def test_mcp_server.rate_article_success(self, sample_articles):
        """Test rating an article."""
mcp_server.rate_article

        article_id = sample_articles[0]
        result = mcp_server.rate_article(article_id=article_id, rating=4)

        assert result["success"] == True
        assert result["rating"] == 4
        assert "message" in result

        # Verify in database
        session = get_session()
        article = session.query(Article).filter(Article.id == article_id).first()
        assert article.rating == 4
        session.close()

    def test_mcp_server.rate_article_invalid_rating(self, sample_articles):
        """Test rating with invalid value."""
mcp_server.rate_article

        result = mcp_server.rate_article(article_id=sample_articles[0], rating=6)

        assert "error" in result
        assert "between 1 and 5" in result["error"]

    def test_mcp_server.rate_article_not_found(self):
        """Test rating a non-existent article."""
mcp_server.rate_article

        result = mcp_server.rate_article(article_id=99999, rating=5)

        assert "error" in result
        assert "not found" in result["error"]


class TestMarkArticleRead:
    """Tests for mcp_server.mark_article_read tool."""

    def test_mcp_server.mark_article_read_success(self, sample_articles):
        """Test marking an article as read."""
mcp_server.mark_article_read

        article_id = sample_articles[0]
        result = mcp_server.mark_article_read(article_id=article_id, is_read=True)

        assert result["success"] == True
        assert result["is_read"] == True

        # Verify in database
        session = get_session()
        article = session.query(Article).filter(Article.id == article_id).first()
        assert article.is_read == True
        session.close()

    def test_mark_article_unread(self, sample_articles):
        """Test marking an article as unread."""
mcp_server.mark_article_read

        article_id = sample_articles[1]  # This one is already read
        result = mcp_server.mark_article_read(article_id=article_id, is_read=False)

        assert result["success"] == True
        assert result["is_read"] == False

    def test_mcp_server.mark_article_read_not_found(self):
        """Test marking a non-existent article."""
mcp_server.mark_article_read

        result = mcp_server.mark_article_read(article_id=99999, is_read=True)

        assert "error" in result


class TestGetProfile:
    """Tests for mcp_server.get_profile tool."""

    def test_mcp_server.get_profile_with_existing(self, sample_articles, sample_profile):
        """Test getting existing profile with statistics."""
mcp_server.get_profile

        result = mcp_server.get_profile()

        assert "interests" in result
        assert "transformers" in result["interests"]
        assert "statistics" in result
        assert result["statistics"]["total_articles"] == 3
        assert result["statistics"]["read_articles"] == 1
        assert result["statistics"]["read_percentage"] == 33.3

    def test_mcp_server.get_profile_without_existing(self, sample_articles):
        """Test getting profile when none exists."""
mcp_server.get_profile

        result = mcp_server.get_profile()

        assert "interests" in result
        assert isinstance(result["interests"], list)
        assert "statistics" in result

    def test_mcp_server.get_profile_average_rating(self, sample_articles):
        """Test average rating calculation."""
mcp_server.get_profile

        result = mcp_server.get_profile()

        # Only one article has a rating (5)
        assert result["statistics"]["average_rating"] == 5.0
        assert result["statistics"]["rated_articles"] == 1


class TestUpdateInterests:
    """Tests for mcp_server.update_interests tool."""

    def test_mcp_server.update_interests_new_profile(self):
        """Test updating interests for new profile."""
mcp_server.update_interests

        interests = ["machine learning", "computer vision"]
        result = mcp_server.update_interests(interests=interests)

        assert result["success"] == True
        assert result["interests"] == interests

        # Verify in database
        session = get_session()
        profile = session.query(UserProfile).first()
        assert profile.interests == interests
        session.close()

    def test_mcp_server.update_interests_existing_profile(self, sample_profile):
        """Test updating interests for existing profile."""
mcp_server.update_interests

        new_interests = ["reinforcement learning", "robotics"]
        result = mcp_server.update_interests(interests=new_interests)

        assert result["success"] == True
        assert result["interests"] == new_interests


class TestFetchArticles:
    """Tests for mcp_server.fetch_articles tool."""

    def test_mcp_server.fetch_articles_arxiv(self):
        """Test fetching from arXiv."""
mcp_server.fetch_articles

        with patch('mcp_server.fetch_arxiv') as mock_fetch:
            mock_fetch.return_value = 5

            result = mcp_server.fetch_articles(source="arxiv", categories=["cs.AI"], limit=20)

            assert result["success"] == True
            assert result["source"] == "arxiv"
            assert result["new_articles"] == 5
            assert "cs.AI" in result["categories"]
            mock_fetch.assert_called_once()

    def test_mcp_server.fetch_articles_arxiv_default_categories(self):
        """Test fetching from arXiv with default categories."""
mcp_server.fetch_articles

        with patch('mcp_server.fetch_arxiv') as mock_fetch:
            mock_fetch.return_value = 10

            result = mcp_server.fetch_articles(source="arxiv", limit=20)

            assert result["success"] == True
            assert "cs.AI" in result["categories"]
            assert "cs.LG" in result["categories"]

    def test_mcp_server.fetch_articles_semanticscholar_success(self):
        """Test fetching from Semantic Scholar."""
mcp_server.fetch_articles

        with patch('mcp_server.SemanticScholarFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher

            mock_fetcher.fetch.return_value = [{"title": "Test Paper"}] * 3
            mock_fetcher.save_to_db.return_value = 2

            result = mcp_server.fetch_articles(
                source="semanticscholar",
                query="transformers",
                limit=10,
                min_citations=50,
                year="2024"
            )

            assert result["success"] == True
            assert result["source"] == "semanticscholar"
            assert result["fetched"] == 3
            assert result["new_articles"] == 2
            assert result["duplicates"] == 1
            mock_fetcher.close.assert_called_once()

    def test_mcp_server.fetch_articles_semanticscholar_no_query(self):
        """Test Semantic Scholar without query."""
mcp_server.fetch_articles

        result = mcp_server.fetch_articles(source="semanticscholar", limit=10)

        assert "error" in result
        assert "required" in result["error"]

    def test_mcp_server.fetch_articles_semanticscholar_rate_limit(self):
        """Test handling rate limit errors."""
mcp_server.fetch_articles

        with patch('mcp_server.SemanticScholarFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher

            mock_fetcher.fetch.side_effect = Exception("429 Too Many Requests")

            result = mcp_server.fetch_articles(source="semanticscholar", query="test", limit=5)

            assert result["success"] == False
            assert result["error"] == "rate_limit_exceeded"
            assert "wait" in result["message"].lower()

    def test_mcp_server.fetch_articles_invalid_source(self):
        """Test with invalid source."""
mcp_server.fetch_articles

        result = mcp_server.fetch_articles(source="invalid", limit=10)

        assert "error" in result
        assert "Unknown source" in result["error"]

    def test_mcp_server.fetch_articles_semanticscholar_limit_capped(self):
        """Test that limit is capped at 100 for Semantic Scholar."""
mcp_server.fetch_articles

        with patch('mcp_server.SemanticScholarFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            mock_fetcher.fetch.return_value = []
            mock_fetcher.save_to_db.return_value = 0

            mcp_server.fetch_articles(source="semanticscholar", query="test", limit=200)

            # Should be called with 100, not 200
            mock_fetcher.fetch.assert_called_once()
            call_args = mock_fetcher.fetch.call_args
            assert call_args.kwargs["limit"] == 100


class TestMCPServerIntegration:
    """Integration tests for MCP server."""

    def test_workflow_search_rate_read(self, sample_articles):
        """Test complete workflow: search -> rate -> mark read."""
mcp_server.search_papers, mcp_server.rate_article, mcp_server.mark_article_read, mcp_server.get_profile

        # Search for papers
        with patch('mcp_server.VectorStore') as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance

            session = get_session()
            article = session.query(Article).first()
            session.close()

            mock_instance.semantic_search.return_value = [
                {"article": article, "relevance": 0.9}
            ]

            search_results = mcp_server.search_papers(query="transformers", limit=5)
            article_id = search_results[0]["id"]

        # Rate the article
        rate_result = mcp_server.rate_article(article_id=article_id, rating=5)
        assert rate_result["success"] == True

        # Mark as read
        read_result = mcp_server.mark_article_read(article_id=article_id, is_read=True)
        assert read_result["success"] == True

        # Check profile stats
        profile = mcp_server.get_profile()
        assert profile["statistics"]["read_articles"] >= 1
        assert profile["statistics"]["rated_articles"] >= 1
