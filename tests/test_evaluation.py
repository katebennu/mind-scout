"""Tests for Phoenix evaluation module."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass


class TestEvalResult:
    """Test EvalResult dataclass."""

    def test_eval_result_creation(self):
        """Test creating an EvalResult."""
        from mindscout.evaluation import EvalResult

        result = EvalResult(score=1.0, label="excellent", explanation="Great topics")

        assert result.score == 1.0
        assert result.label == "excellent"
        assert result.explanation == "Great topics"

    def test_eval_result_without_explanation(self):
        """Test creating an EvalResult without explanation."""
        from mindscout.evaluation import EvalResult

        result = EvalResult(score=0.5, label="good")

        assert result.score == 0.5
        assert result.label == "good"
        assert result.explanation is None


class TestTopicEvaluator:
    """Test TopicEvaluator class."""

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluator_initialization(self, mock_create_classifier, mock_llm):
        """Test that evaluator initializes correctly."""
        from mindscout.evaluation import TopicEvaluator

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        mock_evaluator = MagicMock()
        mock_create_classifier.return_value = mock_evaluator

        evaluator = TopicEvaluator()

        # Check LLM was created with correct provider
        mock_llm.assert_called_once_with(provider="anthropic", model="claude-3-5-haiku-20241022")

        # Check classifier was created
        mock_create_classifier.assert_called_once()
        call_kwargs = mock_create_classifier.call_args[1]
        assert call_kwargs["name"] == "topic_relevance"
        assert call_kwargs["llm"] == mock_llm_instance
        assert "excellent" in call_kwargs["choices"]
        assert "good" in call_kwargs["choices"]
        assert "poor" in call_kwargs["choices"]

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluator_custom_model(self, mock_create_classifier, mock_llm):
        """Test that evaluator can use custom model."""
        from mindscout.evaluation import TopicEvaluator

        mock_llm.return_value = MagicMock()
        mock_create_classifier.return_value = MagicMock()

        evaluator = TopicEvaluator(model="claude-3-5-sonnet-20241022")

        mock_llm.assert_called_once_with(provider="anthropic", model="claude-3-5-sonnet-20241022")

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluate_returns_result(self, mock_create_classifier, mock_llm):
        """Test that evaluate returns proper result."""
        from mindscout.evaluation import TopicEvaluator, EvalResult

        # Mock the score object returned by Phoenix
        mock_score = MagicMock()
        mock_score.score = 1.0
        mock_score.label = "excellent"
        mock_score.explanation = "Topics are highly relevant"

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = [mock_score]
        mock_create_classifier.return_value = mock_evaluator

        mock_llm.return_value = MagicMock()

        evaluator = TopicEvaluator()
        result = evaluator.evaluate(
            title="Test Paper",
            abstract="This is about machine learning",
            topics=["machine learning", "AI"]
        )

        assert isinstance(result, EvalResult)
        assert result.score == 1.0
        assert result.label == "excellent"
        assert result.explanation == "Topics are highly relevant"

        # Check evaluate was called with correct input
        mock_evaluator.evaluate.assert_called_once()
        call_args = mock_evaluator.evaluate.call_args[0][0]
        assert call_args["title"] == "Test Paper"
        assert call_args["abstract"] == "This is about machine learning"
        assert call_args["topics"] == "machine learning, AI"

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluate_handles_empty_result(self, mock_create_classifier, mock_llm):
        """Test that evaluate handles empty results gracefully."""
        from mindscout.evaluation import TopicEvaluator, EvalResult

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = []  # Empty result
        mock_create_classifier.return_value = mock_evaluator

        mock_llm.return_value = MagicMock()

        evaluator = TopicEvaluator()
        result = evaluator.evaluate(
            title="Test Paper",
            abstract="Abstract",
            topics=["topic1"]
        )

        assert isinstance(result, EvalResult)
        assert result.score == 0.0
        assert result.label == "unknown"
        assert result.explanation is None

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluate_batch(self, mock_create_classifier, mock_llm):
        """Test batch evaluation."""
        from mindscout.evaluation import TopicEvaluator, EvalResult

        # Mock scores for two articles
        mock_score1 = MagicMock()
        mock_score1.score = 1.0
        mock_score1.label = "excellent"
        mock_score1.explanation = "Great"

        mock_score2 = MagicMock()
        mock_score2.score = 0.5
        mock_score2.label = "good"
        mock_score2.explanation = "OK"

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.side_effect = [[mock_score1], [mock_score2]]
        mock_create_classifier.return_value = mock_evaluator

        mock_llm.return_value = MagicMock()

        evaluator = TopicEvaluator()
        articles = [
            {"title": "Paper 1", "abstract": "Abstract 1", "topics": ["topic1"]},
            {"title": "Paper 2", "abstract": "Abstract 2", "topics": ["topic2", "topic3"]}
        ]

        results = evaluator.evaluate_batch(articles)

        assert len(results) == 2
        assert results[0].score == 1.0
        assert results[0].label == "excellent"
        assert results[1].score == 0.5
        assert results[1].label == "good"

    @patch("phoenix.evals.LLM")
    @patch("phoenix.evals.create_classifier")
    def test_evaluate_batch_with_string_topics(self, mock_create_classifier, mock_llm):
        """Test batch evaluation handles string topics."""
        from mindscout.evaluation import TopicEvaluator

        mock_score = MagicMock()
        mock_score.score = 1.0
        mock_score.label = "excellent"
        mock_score.explanation = None

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = [mock_score]
        mock_create_classifier.return_value = mock_evaluator

        mock_llm.return_value = MagicMock()

        evaluator = TopicEvaluator()
        articles = [
            {"title": "Paper", "abstract": "Abstract", "topics": "topic1, topic2"}  # String instead of list
        ]

        results = evaluator.evaluate_batch(articles)

        assert len(results) == 1
        assert results[0].score == 1.0
