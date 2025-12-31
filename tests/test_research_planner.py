"""Tests for ResearchPlannerAgent."""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from mindscout.database import Article, get_session
from mindscout.research_planner import (
    ResearchPlannerAgent,
    _cleanup_expired_plans,
    _pending_plans,
)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for analysis."""
    return json.dumps(
        {
            "candidates": [
                {
                    "index": 0,
                    "relevance_score": 9,
                    "difficulty": "intermediate",
                    "rationale": "Foundational paper on the topic.",
                    "suggested_order": 1,
                },
                {
                    "index": 1,
                    "relevance_score": 7,
                    "difficulty": "advanced",
                    "rationale": "More advanced concepts.",
                    "suggested_order": 2,
                },
            ],
            "recommendation": "Start with paper 0, then move to paper 1.",
        }
    )


@pytest.fixture
def mock_reading_plan_response():
    """Mock LLM response for reading plan."""
    return json.dumps(
        {
            "summary": "A comprehensive learning path for understanding the topic.",
            "path": [
                {
                    "order": 1,
                    "title": "First Paper",
                    "authors": "Author A",
                    "rationale": "Start here for fundamentals.",
                    "estimated_time": "2-3 hours",
                },
                {
                    "order": 2,
                    "title": "Second Paper",
                    "authors": "Author B",
                    "rationale": "Build on previous knowledge.",
                    "estimated_time": "3-4 hours",
                },
            ],
        }
    )


@pytest.fixture
def mock_papers():
    """Mock paper data from Semantic Scholar."""
    return [
        {
            "title": "Introduction to RLHF",
            "authors": "Author A, Author B",
            "year": 2023,
            "citation_count": 150,
            "abstract": "This paper introduces RLHF techniques for language models.",
            "url": "https://example.com/paper1",
            "source_id": "ss_001",
        },
        {
            "title": "Advanced RLHF Methods",
            "authors": "Author C",
            "year": 2024,
            "citation_count": 50,
            "abstract": "We present advanced methods for RLHF optimization.",
            "url": "https://example.com/paper2",
            "source_id": "ss_002",
        },
    ]


@pytest.fixture(autouse=True)
def clear_pending_plans():
    """Clear pending plans before and after each test."""
    _pending_plans.clear()
    yield
    _pending_plans.clear()


class TestResearchPlannerAgentInit:
    """Test ResearchPlannerAgent initialization."""

    def test_init(self, isolated_test_db):
        """Test basic initialization."""
        with patch("mindscout.research_planner.LLMClient"):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                assert agent.llm is not None
                assert agent.ss_fetcher is not None
                agent.close()

    def test_close(self, isolated_test_db):
        """Test closing resources."""
        with patch("mindscout.research_planner.LLMClient"):
            mock_fetcher = MagicMock()
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                agent.close()
                mock_fetcher.close.assert_called_once()


class TestPlanMethod:
    """Test ResearchPlannerAgent.plan method."""

    def test_plan_success(self, isolated_test_db, mock_papers, mock_llm_response):
        """Test successful planning."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                result = agent.plan(goal="RLHF", skill_level="intermediate")

                assert result["success"]
                assert "plan_id" in result
                assert result["goal"] == "RLHF"
                assert result["skill_level"] == "intermediate"
                assert len(result["candidates"]) == 2
                assert result["plan_id"] in _pending_plans

                agent.close()

    def test_plan_no_papers_found(self, isolated_test_db):
        """Test planning when no papers are found."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = []

        with patch("mindscout.research_planner.LLMClient"):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                result = agent.plan(goal="nonexistent topic")

                assert not result["success"]
                assert result["error"] == "no_papers_found"

                agent.close()

    def test_plan_search_failed(self, isolated_test_db):
        """Test planning when search fails."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch.side_effect = Exception("API error")

        with patch("mindscout.research_planner.LLMClient"):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                result = agent.plan(goal="RLHF")

                assert not result["success"]
                assert result["error"] == "search_failed"

                agent.close()

    def test_plan_candidates_sorted_by_relevance(
        self, isolated_test_db, mock_papers, mock_llm_response
    ):
        """Test that candidates are sorted by relevance score."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                result = agent.plan(goal="RLHF")

                scores = [c["relevance_score"] for c in result["candidates"]]
                assert scores == sorted(scores, reverse=True)

                agent.close()

    def test_plan_stores_pending_plan(self, isolated_test_db, mock_papers, mock_llm_response):
        """Test that plan is stored for later execution."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()
                result = agent.plan(goal="RLHF", skill_level="beginner")

                plan_id = result["plan_id"]
                assert plan_id in _pending_plans
                stored_plan = _pending_plans[plan_id]
                assert stored_plan["goal"] == "RLHF"
                assert stored_plan["skill_level"] == "beginner"
                assert stored_plan["papers"] == mock_papers
                assert "expires" in stored_plan

                agent.close()


class TestExecuteMethod:
    """Test ResearchPlannerAgent.execute method."""

    def test_execute_success(
        self, isolated_test_db, mock_papers, mock_llm_response, mock_reading_plan_response
    ):
        """Test successful execution."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = [mock_llm_response, mock_reading_plan_response]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers
        mock_fetcher.save_to_db.return_value = 2

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()

                # First create a plan
                plan_result = agent.plan(goal="RLHF")
                plan_id = plan_result["plan_id"]

                # Then execute it
                result = agent.execute(plan_id=plan_id, selected_indices=[0, 1])

                assert result["success"]
                assert result["papers_added"] == 2
                assert "reading_plan" in result
                assert plan_id not in _pending_plans  # Plan should be cleaned up

                agent.close()

    def test_execute_plan_not_found(self, isolated_test_db):
        """Test execution with non-existent plan."""
        with patch("mindscout.research_planner.LLMClient"):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent.execute(plan_id="nonexistent", selected_indices=[0])

                assert not result["success"]
                assert result["error"] == "plan_not_found"

                agent.close()

    def test_execute_invalid_indices(self, isolated_test_db, mock_papers, mock_llm_response):
        """Test execution with invalid indices."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()

                plan_result = agent.plan(goal="RLHF")
                plan_id = plan_result["plan_id"]

                # Try to execute with invalid indices
                result = agent.execute(plan_id=plan_id, selected_indices=[99, 100])

                assert not result["success"]
                assert result["error"] == "invalid_indices"

                agent.close()

    def test_execute_partial_valid_indices(
        self, isolated_test_db, mock_papers, mock_llm_response, mock_reading_plan_response
    ):
        """Test execution with some valid and some invalid indices."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = [mock_llm_response, mock_reading_plan_response]

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers
        mock_fetcher.save_to_db.return_value = 1

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()

                plan_result = agent.plan(goal="RLHF")
                plan_id = plan_result["plan_id"]

                # Mix of valid (0) and invalid (99) indices
                result = agent.execute(plan_id=plan_id, selected_indices=[0, 99])

                assert result["success"]
                assert result["papers_added"] == 1

                agent.close()

    def test_execute_save_failed(self, isolated_test_db, mock_papers, mock_llm_response):
        """Test execution when save fails."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        mock_fetcher = MagicMock()
        mock_fetcher.fetch.return_value = mock_papers
        mock_fetcher.save_to_db.side_effect = Exception("Database error")

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.research_planner.SemanticScholarFetcher",
                return_value=mock_fetcher,
            ):
                agent = ResearchPlannerAgent()

                plan_result = agent.plan(goal="RLHF")
                plan_id = plan_result["plan_id"]

                result = agent.execute(plan_id=plan_id, selected_indices=[0])

                assert not result["success"]
                assert result["error"] == "save_failed"

                agent.close()


class TestAnalyzeCandidates:
    """Test _analyze_candidates method."""

    def test_analyze_candidates_success(self, isolated_test_db, mock_papers, mock_llm_response):
        """Test successful candidate analysis."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_llm_response

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._analyze_candidates("RLHF", "intermediate", mock_papers)

                assert result["success"]
                assert len(result["candidates"]) == 2
                assert result["candidates"][0]["relevance_score"] == 9
                assert "recommendation" in result

                agent.close()

    def test_analyze_candidates_json_in_code_block(self, isolated_test_db, mock_papers):
        """Test parsing JSON wrapped in code blocks."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = """```json
{
    "candidates": [{"index": 0, "relevance_score": 8, "difficulty": "intermediate"}],
    "recommendation": "Good paper."
}
```"""

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._analyze_candidates("RLHF", "intermediate", mock_papers)

                assert result["success"]
                assert result["candidates"][0]["relevance_score"] == 8

                agent.close()

    def test_analyze_candidates_invalid_json(self, isolated_test_db, mock_papers):
        """Test fallback when LLM returns invalid JSON."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "This is not valid JSON at all."

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._analyze_candidates("RLHF", "intermediate", mock_papers)

                # Should fall back to basic analysis
                assert result["success"]
                assert len(result["candidates"]) == len(mock_papers)
                assert all(c["relevance_score"] == 5 for c in result["candidates"])

                agent.close()

    def test_analyze_candidates_llm_error(self, isolated_test_db, mock_papers):
        """Test handling LLM errors."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("API error")

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._analyze_candidates("RLHF", "intermediate", mock_papers)

                assert not result["success"]
                assert result["error"] == "analysis_failed"

                agent.close()


class TestCreateReadingPlan:
    """Test _create_reading_plan method."""

    def test_create_reading_plan_single_paper(self, isolated_test_db, mock_papers):
        """Test reading plan for single paper."""
        with patch("mindscout.research_planner.LLMClient"):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._create_reading_plan("RLHF", "intermediate", [mock_papers[0]])

                assert "summary" in result
                assert len(result["path"]) == 1
                assert result["path"][0]["order"] == 1

                agent.close()

    def test_create_reading_plan_multiple_papers(
        self, isolated_test_db, mock_papers, mock_reading_plan_response
    ):
        """Test reading plan for multiple papers."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = mock_reading_plan_response

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._create_reading_plan("RLHF", "intermediate", mock_papers)

                assert "summary" in result
                assert len(result["path"]) == 2
                assert result["path"][0]["order"] == 1
                assert result["path"][1]["order"] == 2

                agent.close()

    def test_create_reading_plan_llm_error_fallback(self, isolated_test_db, mock_papers):
        """Test fallback when LLM fails."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("API error")

        with patch("mindscout.research_planner.LLMClient", return_value=mock_llm):
            with patch("mindscout.research_planner.SemanticScholarFetcher"):
                agent = ResearchPlannerAgent()
                result = agent._create_reading_plan("RLHF", "intermediate", mock_papers)

                # Should return basic ordering
                assert "summary" in result
                assert len(result["path"]) == len(mock_papers)

                agent.close()


class TestCleanupExpiredPlans:
    """Test _cleanup_expired_plans function."""

    def test_cleanup_removes_expired_plans(self, isolated_test_db):
        """Test that expired plans are removed."""
        from mindscout.research_planner import _pending_plans

        # Add an expired plan
        _pending_plans["expired_plan"] = {
            "goal": "test",
            "expires": datetime.now(UTC) - timedelta(hours=2),
        }

        # Add a valid plan
        _pending_plans["valid_plan"] = {
            "goal": "test",
            "expires": datetime.now(UTC) + timedelta(hours=1),
        }

        _cleanup_expired_plans()

        assert "expired_plan" not in _pending_plans
        assert "valid_plan" in _pending_plans

    def test_cleanup_keeps_valid_plans(self, isolated_test_db):
        """Test that valid plans are kept."""
        from mindscout.research_planner import _pending_plans

        _pending_plans["valid_plan"] = {
            "goal": "test",
            "expires": datetime.now(UTC) + timedelta(hours=1),
        }

        _cleanup_expired_plans()

        assert "valid_plan" in _pending_plans
