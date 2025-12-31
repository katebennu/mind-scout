"""Tests for MCP server tools."""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Skip all tests if mcp module is not available
pytest.importorskip("mcp", reason="MCP module not installed")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mindscout.database import Article, UserProfile, get_session  # noqa: E402


@pytest.fixture
def mcp_server(isolated_test_db):
    """Import the MCP server module after database is initialized."""
    spec = importlib.util.spec_from_file_location(
        "mcp_server", Path(__file__).parent.parent / "mcp-server" / "server.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sample_articles(isolated_test_db):
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
            rating=None,
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
            rating=5,
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
            rating=None,
        ),
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
def sample_profile(isolated_test_db):
    """Create sample user profile for testing."""
    session = get_session()

    # Interests and sources are stored as comma-separated strings
    profile = UserProfile(
        interests="transformers,natural language processing",
        skill_level="intermediate",
        preferred_sources="arxiv",
        daily_reading_goal=5,
    )

    session.add(profile)
    session.commit()

    yield profile

    session.query(UserProfile).delete()
    session.commit()
    session.close()


class TestSearchPapers:
    """Tests for search_papers tool."""

    def test_search_papers_basic(self, mcp_server, sample_articles):
        """Test basic semantic search functionality."""
        # Get sample article
        session = get_session()
        article = session.query(Article).first()
        session.close()

        # Mock VectorStore at the location where it's used in the MCP server
        with patch.object(mcp_server, "VectorStore") as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance

            mock_instance.semantic_search.return_value = [{"article": article, "relevance": 0.85}]

            results = mcp_server.search_papers(query="transformers", limit=5)

            assert len(results) == 1
            assert results[0]["title"] == article.title
            assert results[0]["relevance_score"] == 85.0
            mock_instance.close.assert_called_once()

    def test_search_papers_empty_results(self, mcp_server):
        """Test search with no results."""
        with patch.object(mcp_server, "VectorStore") as mock_vs:
            mock_instance = MagicMock()
            mock_vs.return_value = mock_instance
            mock_instance.semantic_search.return_value = []

            results = mcp_server.search_papers(query="nonexistent topic", limit=10)

            assert results == []
            mock_instance.close.assert_called_once()


class TestGetArticle:
    """Tests for get_article tool."""

    def test_get_article_success(self, mcp_server, sample_articles):
        """Test getting a specific article."""
        article_id = sample_articles[0]
        result = mcp_server.get_article(article_id=article_id)

        assert result["id"] == article_id
        assert "title" in result
        assert "authors" in result
        assert "abstract" in result
        assert "url" in result

    def test_get_article_not_found(self, mcp_server):
        """Test getting a non-existent article."""
        result = mcp_server.get_article(article_id=99999)

        assert "error" in result
        assert "not found" in result["error"]


class TestListArticles:
    """Tests for list_articles tool."""

    def test_list_articles_basic(self, mcp_server, sample_articles):
        """Test listing articles with default parameters."""
        result = mcp_server.list_articles()

        assert "articles" in result
        assert "total" in result
        assert result["total"] == 3
        assert len(result["articles"]) == 3
        assert result["page"] == 1

    def test_list_articles_pagination(self, mcp_server, sample_articles):
        """Test pagination."""
        result = mcp_server.list_articles(page=1, page_size=2)

        assert len(result["articles"]) == 2
        assert result["total"] == 3
        assert result["total_pages"] == 2

    def test_list_articles_unread_only(self, mcp_server, sample_articles):
        """Test filtering by unread status."""
        result = mcp_server.list_articles(unread_only=True)

        assert result["total"] == 2  # Two unread articles
        for article in result["articles"]:
            assert not article["is_read"]

    def test_list_articles_filter_by_source(self, mcp_server, sample_articles):
        """Test filtering by source."""
        result = mcp_server.list_articles(source="arxiv")

        assert result["total"] == 2  # Two arxiv articles
        for article in result["articles"]:
            assert article["source"] == "arxiv"


class TestRateArticle:
    """Tests for rate_article tool."""

    def test_rate_article_success(self, mcp_server, sample_articles):
        """Test rating an article."""
        article_id = sample_articles[0]
        result = mcp_server.rate_article(article_id=article_id, rating=4)

        assert result["success"]
        assert result["rating"] == 4
        assert "message" in result

        # Verify in database
        session = get_session()
        article = session.query(Article).filter(Article.id == article_id).first()
        assert article.rating == 4
        session.close()

    def test_rate_article_invalid_rating(self, mcp_server, sample_articles):
        """Test rating with invalid value."""
        result = mcp_server.rate_article(article_id=sample_articles[0], rating=6)

        assert "error" in result
        assert "between 1 and 5" in result["error"]

    def test_rate_article_not_found(self, mcp_server):
        """Test rating a non-existent article."""
        result = mcp_server.rate_article(article_id=99999, rating=5)

        assert "error" in result
        assert "not found" in result["error"]


class TestMarkArticleRead:
    """Tests for mark_article_read tool."""

    def test_mark_article_read_success(self, mcp_server, sample_articles):
        """Test marking an article as read."""
        article_id = sample_articles[0]
        result = mcp_server.mark_article_read(article_id=article_id, is_read=True)

        assert result["success"]
        assert result["is_read"]

        # Verify in database
        session = get_session()
        article = session.query(Article).filter(Article.id == article_id).first()
        assert article.is_read
        session.close()

    def test_mark_article_unread(self, mcp_server, sample_articles):
        """Test marking an article as unread."""
        article_id = sample_articles[1]  # This one is already read
        result = mcp_server.mark_article_read(article_id=article_id, is_read=False)

        assert result["success"]
        assert not result["is_read"]


class TestGetProfile:
    """Tests for get_profile tool."""

    def test_get_profile_with_existing(self, mcp_server, sample_articles, sample_profile):
        """Test getting existing profile with statistics."""
        result = mcp_server.get_profile()

        assert "interests" in result
        assert "transformers" in result["interests"]
        assert "statistics" in result
        assert result["statistics"]["total_articles"] == 3
        assert result["statistics"]["read_articles"] == 1
        assert result["statistics"]["read_percentage"] == 33.3

    def test_get_profile_without_existing(self, mcp_server, sample_articles):
        """Test getting profile when none exists."""
        result = mcp_server.get_profile()

        assert "interests" in result
        assert isinstance(result["interests"], list)
        assert "statistics" in result


class TestUpdateInterests:
    """Tests for update_interests tool."""

    def test_update_interests_new_profile(self, mcp_server):
        """Test updating interests for new profile."""
        interests = ["machine learning", "computer vision"]
        result = mcp_server.update_interests(interests=interests)

        assert result["success"]
        assert result["interests"] == interests

        # Verify in database (stored as comma-separated string)
        session = get_session()
        profile = session.query(UserProfile).first()
        assert profile.interests == "machine learning,computer vision"
        session.close()

    def test_update_interests_existing_profile(self, mcp_server, sample_profile):
        """Test updating interests for existing profile."""
        new_interests = ["reinforcement learning", "robotics"]
        result = mcp_server.update_interests(interests=new_interests)

        assert result["success"]
        assert result["interests"] == new_interests


class TestFetchArticles:
    """Tests for fetch_articles tool."""

    def test_fetch_articles_arxiv(self, mcp_server):
        """Test fetching from arXiv."""
        with patch.object(mcp_server, "fetch_arxiv") as mock_fetch:
            mock_fetch.return_value = 5

            result = mcp_server.fetch_articles(source="arxiv", categories=["cs.AI"], limit=20)

            assert result["success"]
            assert result["source"] == "arxiv"
            assert result["new_articles"] == 5
            assert "cs.AI" in result["categories"]
            mock_fetch.assert_called_once()

    def test_fetch_articles_semanticscholar_success(self, mcp_server):
        """Test fetching from Semantic Scholar."""
        with patch.object(mcp_server, "SemanticScholarFetcher") as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher

            mock_fetcher.fetch.return_value = [{"title": "Test Paper"}] * 3
            mock_fetcher.save_to_db.return_value = 2

            result = mcp_server.fetch_articles(
                source="semanticscholar", query="transformers", limit=10
            )

            assert result["success"]
            assert result["source"] == "semanticscholar"
            assert result["fetched"] == 3
            assert result["new_articles"] == 2
            assert result["duplicates"] == 1
            mock_fetcher.close.assert_called_once()

    def test_fetch_articles_semanticscholar_no_query(self, mcp_server):
        """Test Semantic Scholar without query."""
        result = mcp_server.fetch_articles(source="semanticscholar", limit=10)

        assert "error" in result
        assert "required" in result["error"]

    def test_fetch_articles_invalid_source(self, mcp_server):
        """Test with invalid source."""
        result = mcp_server.fetch_articles(source="invalid", limit=10)

        assert "error" in result
        assert "Unknown source" in result["error"]


class TestPlanResearch:
    """Tests for plan_research tool."""

    def test_plan_research_success(self, mcp_server):
        """Test successful research planning."""
        mock_agent = MagicMock()
        mock_agent.plan.return_value = {
            "success": True,
            "plan_id": "abc123",
            "goal": "RLHF",
            "skill_level": "intermediate",
            "candidates": [
                {
                    "index": 0,
                    "title": "Test Paper",
                    "relevance_score": 9,
                    "difficulty": "intermediate",
                    "rationale": "Good paper.",
                }
            ],
            "recommendation": "Start with paper 0.",
        }

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            result = mcp_server.plan_research(
                goal="RLHF", skill_level="intermediate", max_candidates=10
            )

            assert result["success"]
            assert result["plan_id"] == "abc123"
            assert result["goal"] == "RLHF"
            assert len(result["candidates"]) == 1
            mock_agent.plan.assert_called_once_with(
                goal="RLHF",
                skill_level="intermediate",
                max_candidates=10,
            )
            mock_agent.close.assert_called_once()

    def test_plan_research_no_papers_found(self, mcp_server):
        """Test planning when no papers are found."""
        mock_agent = MagicMock()
        mock_agent.plan.return_value = {
            "success": False,
            "error": "no_papers_found",
            "message": "No papers found for 'obscure topic'.",
        }

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            result = mcp_server.plan_research(goal="obscure topic")

            assert not result["success"]
            assert result["error"] == "no_papers_found"
            mock_agent.close.assert_called_once()

    def test_plan_research_default_parameters(self, mcp_server):
        """Test planning with default parameters."""
        mock_agent = MagicMock()
        mock_agent.plan.return_value = {"success": True, "plan_id": "test"}

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            mcp_server.plan_research(goal="transformers")

            mock_agent.plan.assert_called_once_with(
                goal="transformers",
                skill_level="intermediate",
                max_candidates=10,
            )


class TestExecuteResearchPlan:
    """Tests for execute_research_plan tool."""

    def test_execute_research_plan_success(self, mcp_server):
        """Test successful plan execution."""
        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "success": True,
            "goal": "RLHF",
            "papers_added": 2,
            "duplicates_skipped": 0,
            "reading_plan": {
                "summary": "Learning path for RLHF",
                "path": [
                    {
                        "order": 1,
                        "title": "Paper 1",
                        "rationale": "Start here.",
                        "estimated_time": "2 hours",
                    }
                ],
            },
        }

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            result = mcp_server.execute_research_plan(plan_id="abc123", selected_indices=[0, 1])

            assert result["success"]
            assert result["papers_added"] == 2
            assert "reading_plan" in result
            mock_agent.execute.assert_called_once_with(
                plan_id="abc123",
                selected_indices=[0, 1],
            )
            mock_agent.close.assert_called_once()

    def test_execute_research_plan_not_found(self, mcp_server):
        """Test execution with non-existent plan."""
        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "success": False,
            "error": "plan_not_found",
            "message": "Plan 'nonexistent' not found or expired.",
        }

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            result = mcp_server.execute_research_plan(plan_id="nonexistent", selected_indices=[0])

            assert not result["success"]
            assert result["error"] == "plan_not_found"
            mock_agent.close.assert_called_once()

    def test_execute_research_plan_invalid_indices(self, mcp_server):
        """Test execution with invalid indices."""
        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "success": False,
            "error": "invalid_indices",
            "message": "No valid paper indices provided.",
        }

        with patch.object(mcp_server, "ResearchPlannerAgent", return_value=mock_agent):
            result = mcp_server.execute_research_plan(plan_id="abc123", selected_indices=[99, 100])

            assert not result["success"]
            assert result["error"] == "invalid_indices"
