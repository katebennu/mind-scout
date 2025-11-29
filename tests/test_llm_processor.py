"""Tests for LLM processor."""

import pytest
from unittest.mock import patch, MagicMock


class TestLLMClientInit:
    """Test LLMClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")

            assert client.api_key == "test-key"
            assert client.model == "claude-3-5-haiku-20241022"
            mock_anthropic.assert_called_once_with(api_key="test-key")

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-test-key")

        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            from mindscout.processors.llm import LLMClient

            client = LLMClient()

            assert client.api_key == "env-test-key"
            mock_anthropic.assert_called_once_with(api_key="env-test-key")

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key", model="claude-3-opus-20240229")

            assert client.model == "claude-3-opus-20240229"

    def test_init_without_api_key_raises(self, monkeypatch):
        """Test that initialization without API key raises ValueError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from mindscout.processors.llm import LLMClient

        with pytest.raises(ValueError, match="Anthropic API key not found"):
            LLMClient()


class TestLLMClientGenerate:
    """Test LLMClient.generate method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock LLM client."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Generated response")]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            yield client, mock_anthropic.return_value

    def test_generate_basic(self, mock_client):
        """Test basic text generation."""
        client, mock_anthropic = mock_client

        result = client.generate("Test prompt")

        assert result == "Generated response"
        mock_anthropic.messages.create.assert_called_once()
        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert call_kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]
        assert call_kwargs["model"] == "claude-3-5-haiku-20241022"

    def test_generate_with_system_prompt(self, mock_client):
        """Test generation with system prompt."""
        client, mock_anthropic = mock_client

        client.generate("Test prompt", system="You are helpful")

        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are helpful"

    def test_generate_with_custom_params(self, mock_client):
        """Test generation with custom parameters."""
        client, mock_anthropic = mock_client

        client.generate("Test prompt", max_tokens=500, temperature=0.9)

        call_kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["temperature"] == 0.9


class TestLLMClientSummarize:
    """Test LLMClient.summarize method."""

    def test_summarize(self):
        """Test summarize method."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Summary of the text")]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.summarize("Long abstract text here")

            assert result == "Summary of the text"
            call_kwargs = mock_anthropic.return_value.messages.create.call_args.kwargs
            assert "2" in call_kwargs["messages"][0]["content"]  # max_sentences default

    def test_summarize_custom_sentences(self):
        """Test summarize with custom sentence count."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Short summary")]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            client.summarize("Text", max_sentences=5)

            call_kwargs = mock_anthropic.return_value.messages.create.call_args.kwargs
            assert "5" in call_kwargs["messages"][0]["content"]


class TestLLMClientExtractTopics:
    """Test LLMClient.extract_topics method."""

    def test_extract_topics(self):
        """Test topic extraction."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text="machine learning, neural networks, deep learning")
            ]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.extract_topics("Test Title", "Test abstract about ML")

            assert result == ["machine learning", "neural networks", "deep learning"]

    def test_extract_topics_filters_short(self):
        """Test that short topics are filtered out."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="AI, ml, deep learning, NLP")]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.extract_topics("Title", "Abstract")

            # "ml" should be filtered out (< 3 chars)
            assert "ml" not in result
            assert "deep learning" in result

    def test_extract_topics_limits_count(self):
        """Test that topics are limited to max_topics."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text="one, two, three, four, five, six, seven")
            ]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.extract_topics("Title", "Abstract", max_topics=3)

            assert len(result) == 3


class TestLLMClientGenerateEmbedding:
    """Test LLMClient.generate_embedding method."""

    def test_generate_embedding(self):
        """Test embedding generation."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.generate_embedding("Test text")

            assert isinstance(result, list)
            assert len(result) == 768
            assert all(isinstance(x, float) for x in result)

    def test_generate_embedding_deterministic(self):
        """Test that same text produces same embedding."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result1 = client.generate_embedding("Test text")
            result2 = client.generate_embedding("Test text")

            assert result1 == result2

    def test_generate_embedding_different_for_different_text(self):
        """Test that different text produces different embedding."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result1 = client.generate_embedding("Text one")
            result2 = client.generate_embedding("Text two")

            assert result1 != result2


class TestLLMClientExtractTopicsBatch:
    """Test LLMClient.extract_topics_batch method."""

    def test_extract_topics_batch_empty(self):
        """Test batch extraction with empty list."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.extract_topics_batch([])

            assert result == {}

    def test_extract_topics_batch_success(self):
        """Test successful batch topic extraction."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text='{"1": ["topic1", "topic2"], "2": ["topic3"]}')
            ]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            articles = [
                {"id": 1, "title": "Title 1", "abstract": "Abstract 1"},
                {"id": 2, "title": "Title 2", "abstract": "Abstract 2"},
            ]
            result = client.extract_topics_batch(articles)

            assert "1" in result
            assert "2" in result
            assert result["1"] == ["topic1", "topic2"]
            assert result["2"] == ["topic3"]

    def test_extract_topics_batch_strips_markdown(self):
        """Test that markdown code blocks are stripped."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text='```json\n{"1": ["topic1"]}\n```')
            ]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            articles = [{"id": 1, "title": "Title", "abstract": "Abstract"}]
            result = client.extract_topics_batch(articles)

            assert result["1"] == ["topic1"]

    def test_extract_topics_batch_handles_json_error(self):
        """Test that JSON parse errors are handled gracefully."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="not valid json")]
            mock_anthropic.return_value.messages.create.return_value = mock_response

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            articles = [{"id": 1, "title": "Title", "abstract": "Abstract"}]
            result = client.extract_topics_batch(articles)

            assert result == {}


class TestLLMClientAsyncBatch:
    """Test LLMClient async batch methods."""

    def test_create_topic_extraction_batch_empty_raises(self):
        """Test that empty article list raises ValueError."""
        with patch("mindscout.processors.llm.Anthropic"):
            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")

            with pytest.raises(ValueError, match="No articles provided"):
                client.create_topic_extraction_batch([])

    def test_create_topic_extraction_batch(self):
        """Test creating an async batch."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_batch = MagicMock()
            mock_batch.id = "batch_123"
            mock_anthropic.return_value.messages.batches.create.return_value = mock_batch

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            articles = [
                {"id": 1, "title": "Title 1", "abstract": "Abstract 1"},
                {"id": 2, "title": "Title 2", "abstract": "Abstract 2"},
            ]
            result = client.create_topic_extraction_batch(articles)

            assert result == "batch_123"
            mock_anthropic.return_value.messages.batches.create.assert_called_once()
            call_kwargs = mock_anthropic.return_value.messages.batches.create.call_args.kwargs
            assert len(call_kwargs["requests"]) == 2
            assert call_kwargs["requests"][0]["custom_id"] == "1"
            assert call_kwargs["requests"][1]["custom_id"] == "2"

    def test_get_batch_status(self):
        """Test getting batch status."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            mock_batch = MagicMock()
            mock_batch.id = "batch_123"
            mock_batch.processing_status = "in_progress"
            mock_batch.created_at = "2024-01-01T00:00:00Z"
            mock_batch.ended_at = None
            mock_batch.request_counts.processing = 5
            mock_batch.request_counts.succeeded = 3
            mock_batch.request_counts.errored = 0
            mock_batch.request_counts.canceled = 0
            mock_batch.request_counts.expired = 0
            mock_anthropic.return_value.messages.batches.retrieve.return_value = mock_batch

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.get_batch_status("batch_123")

            assert result["id"] == "batch_123"
            assert result["status"] == "in_progress"
            assert result["counts"]["processing"] == 5
            assert result["counts"]["succeeded"] == 3

    def test_get_batch_results(self):
        """Test retrieving batch results."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            # Create mock result entries
            entry1 = MagicMock()
            entry1.custom_id = "1"
            entry1.result.type = "succeeded"
            entry1.result.message.content = [MagicMock(text="topic1, topic2")]

            entry2 = MagicMock()
            entry2.custom_id = "2"
            entry2.result.type = "succeeded"
            entry2.result.message.content = [MagicMock(text="topic3")]

            mock_anthropic.return_value.messages.batches.results.return_value = [
                entry1,
                entry2,
            ]

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.get_batch_results("batch_123")

            assert result["1"] == ["topic1", "topic2"]
            assert result["2"] == ["topic3"]

    def test_get_batch_results_handles_failures(self):
        """Test that failed entries are handled gracefully."""
        with patch("mindscout.processors.llm.Anthropic") as mock_anthropic:
            entry1 = MagicMock()
            entry1.custom_id = "1"
            entry1.result.type = "succeeded"
            entry1.result.message.content = [MagicMock(text="topic1")]

            entry2 = MagicMock()
            entry2.custom_id = "2"
            entry2.result.type = "errored"

            mock_anthropic.return_value.messages.batches.results.return_value = [
                entry1,
                entry2,
            ]

            from mindscout.processors.llm import LLMClient

            client = LLMClient(api_key="test-key")
            result = client.get_batch_results("batch_123")

            assert result["1"] == ["topic1"]
            assert result["2"] == []
