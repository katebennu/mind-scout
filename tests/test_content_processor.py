"""Tests for content processor."""

import json
import pytest
from unittest.mock import patch, MagicMock

from mindscout.database import get_session, Article, UserProfile, Notification


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    mock = MagicMock()
    mock.extract_topics.return_value = ["machine learning", "neural networks", "deep learning"]
    mock.extract_topics_batch.return_value = {
        "1": ["topic1", "topic2"],
        "2": ["topic3", "topic4"],
    }
    mock.summarize.return_value = "A summary of the article"
    return mock


@pytest.fixture
def sample_articles(isolated_test_db):
    """Create sample articles in the database."""
    session = get_session()

    articles = [
        Article(
            id=1,
            source_id="test-1",
            title="Article 1",
            abstract="Abstract about machine learning",
            url="https://example.com/1",
            source="test",
            processed=False,
        ),
        Article(
            id=2,
            source_id="test-2",
            title="Article 2",
            abstract="Abstract about neural networks",
            url="https://example.com/2",
            source="test",
            processed=False,
        ),
        Article(
            id=3,
            source_id="test-3",
            title="Already Processed",
            abstract="Already processed article",
            url="https://example.com/3",
            source="test",
            processed=True,
            topics='["existing topic"]',
        ),
    ]

    for article in articles:
        session.add(article)
    session.commit()

    yield articles

    session.close()


@pytest.fixture
def sample_profile(isolated_test_db):
    """Create a sample user profile."""
    session = get_session()

    profile = UserProfile(
        interests="machine learning, neural networks",
        skill_level="intermediate",
    )
    session.add(profile)
    session.commit()

    yield profile

    session.close()


class TestContentProcessorInit:
    """Test ContentProcessor initialization."""

    def test_init_with_llm_client(self, mock_llm, isolated_test_db):
        """Test initialization with provided LLM client."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)

        assert processor.llm == mock_llm

    def test_init_lazy(self, isolated_test_db):
        """Test lazy initialization."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(lazy_init=True)

        assert processor.llm is None

    def test_ensure_llm_initializes(self, mock_llm, isolated_test_db):
        """Test that _ensure_llm initializes when needed."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm, lazy_init=True)
        assert processor.llm is None

        processor._ensure_llm()
        assert processor.llm == mock_llm


class TestProcessArticle:
    """Test ContentProcessor.process_article method."""

    def test_process_article_success(self, mock_llm, sample_articles, isolated_test_db):
        """Test successful article processing."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        article = sample_articles[0]

        result = processor.process_article(article)

        assert result is True
        assert article.processed is True
        assert article.topics is not None
        topics = json.loads(article.topics)
        assert "machine learning" in topics

    def test_process_article_skips_processed(self, mock_llm, sample_articles, isolated_test_db):
        """Test that processed articles are skipped."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        article = sample_articles[2]  # Already processed

        result = processor.process_article(article)

        assert result is False
        mock_llm.extract_topics.assert_not_called()

    def test_process_article_force_reprocess(self, mock_llm, sample_articles, isolated_test_db):
        """Test forcing reprocessing of already processed article."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        article = sample_articles[2]  # Already processed

        result = processor.process_article(article, force=True)

        assert result is True
        mock_llm.extract_topics.assert_called_once()

    def test_process_article_handles_error(self, mock_llm, sample_articles, isolated_test_db):
        """Test that errors are handled gracefully."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.extract_topics.side_effect = Exception("API Error")
        processor = ContentProcessor(llm_client=mock_llm)
        article = sample_articles[0]

        result = processor.process_article(article)

        assert result is False
        assert article.processed is False


class TestProcessBatch:
    """Test ContentProcessor.process_batch method."""

    def test_process_batch_success(self, mock_llm, sample_articles, isolated_test_db):
        """Test successful batch processing."""
        from mindscout.processors.content import ContentProcessor

        # Update mock to return topics for our article IDs
        mock_llm.extract_topics_batch.return_value = {
            "1": ["topic1", "topic2"],
            "2": ["topic3", "topic4"],
        }

        processor = ContentProcessor(llm_client=mock_llm)

        processed, failed = processor.process_batch(only_unprocessed=True)

        # Should process 2 unprocessed articles
        assert processed == 2
        assert failed == 0

    def test_process_batch_with_limit(self, mock_llm, sample_articles, isolated_test_db):
        """Test batch processing with limit."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.extract_topics_batch.return_value = {"1": ["topic1"]}
        processor = ContentProcessor(llm_client=mock_llm)

        processed, failed = processor.process_batch(limit=1)

        assert processed == 1

    def test_process_batch_fallback_on_empty_result(
        self, mock_llm, sample_articles, isolated_test_db
    ):
        """Test fallback to individual processing when batch returns empty."""
        from mindscout.processors.content import ContentProcessor

        # Batch returns empty for article 1, should fall back to individual processing
        mock_llm.extract_topics_batch.return_value = {
            "1": [],  # Empty - will trigger fallback
            "2": ["topic3"],
        }

        processor = ContentProcessor(llm_client=mock_llm)
        processed, failed = processor.process_batch(batch_size=10)

        # Article 2 from batch, article 1 from fallback (which succeeds due to extract_topics mock)
        assert processed >= 1


class TestProcessBatchLegacy:
    """Test ContentProcessor.process_batch_legacy method."""

    def test_process_batch_legacy(self, mock_llm, sample_articles, isolated_test_db):
        """Test legacy batch processing."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)

        processed, failed = processor.process_batch_legacy(only_unprocessed=True)

        assert processed == 2
        assert failed == 0
        # Should call extract_topics for each article
        assert mock_llm.extract_topics.call_count == 2


class TestCreateAsyncBatch:
    """Test ContentProcessor.create_async_batch method."""

    def test_create_async_batch_success(self, mock_llm, sample_articles, isolated_test_db):
        """Test creating async batch."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.create_topic_extraction_batch.return_value = "batch_123"
        processor = ContentProcessor(llm_client=mock_llm)

        batch_id = processor.create_async_batch()

        assert batch_id == "batch_123"
        mock_llm.create_topic_extraction_batch.assert_called_once()
        # Should include unprocessed articles
        call_args = mock_llm.create_topic_extraction_batch.call_args[0][0]
        assert len(call_args) == 2  # 2 unprocessed articles

    def test_create_async_batch_with_limit(self, mock_llm, sample_articles, isolated_test_db):
        """Test creating async batch with limit."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.create_topic_extraction_batch.return_value = "batch_456"
        processor = ContentProcessor(llm_client=mock_llm)

        batch_id = processor.create_async_batch(limit=1)

        assert batch_id == "batch_456"
        call_args = mock_llm.create_topic_extraction_batch.call_args[0][0]
        assert len(call_args) == 1

    def test_create_async_batch_no_articles(self, mock_llm, isolated_test_db):
        """Test creating batch with no unprocessed articles raises error."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)

        with pytest.raises(ValueError, match="No unprocessed articles"):
            processor.create_async_batch()


class TestApplyBatchResults:
    """Test ContentProcessor.apply_batch_results method."""

    def test_apply_batch_results_success(self, mock_llm, sample_articles, isolated_test_db):
        """Test applying batch results."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.get_batch_results.return_value = {
            "1": ["topic1", "topic2"],
            "2": ["topic3"],
        }
        processor = ContentProcessor(llm_client=mock_llm)

        updated, failed = processor.apply_batch_results("batch_123")

        assert updated == 2
        assert failed == 0

        # Verify articles were updated
        session = get_session()
        article1 = session.query(Article).filter_by(id=1).first()
        assert article1.processed is True
        assert "topic1" in article1.topics
        session.close()

    def test_apply_batch_results_missing_article(self, mock_llm, sample_articles, isolated_test_db):
        """Test handling of missing articles."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.get_batch_results.return_value = {
            "1": ["topic1"],
            "999": ["topic2"],  # Non-existent article
        }
        processor = ContentProcessor(llm_client=mock_llm)

        updated, failed = processor.apply_batch_results("batch_123")

        assert updated == 1
        assert failed == 1

    def test_apply_batch_results_empty_topics(self, mock_llm, sample_articles, isolated_test_db):
        """Test handling of empty topics."""
        from mindscout.processors.content import ContentProcessor

        mock_llm.get_batch_results.return_value = {
            "1": ["topic1"],
            "2": [],  # Empty topics
        }
        processor = ContentProcessor(llm_client=mock_llm)

        updated, failed = processor.apply_batch_results("batch_123")

        assert updated == 1
        assert failed == 1


class TestGetProcessingStats:
    """Test ContentProcessor.get_processing_stats method."""

    def test_get_processing_stats(self, mock_llm, sample_articles, isolated_test_db):
        """Test getting processing statistics."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)

        stats = processor.get_processing_stats()

        assert stats["total_articles"] == 3
        assert stats["processed"] == 1
        assert stats["unprocessed"] == 2
        assert "processing_rate" in stats
        assert "top_topics" in stats

    def test_get_processing_stats_empty_db(self, mock_llm, isolated_test_db):
        """Test stats with empty database."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)

        stats = processor.get_processing_stats()

        assert stats["total_articles"] == 0
        assert stats["processing_rate"] == 0


class TestCreateInterestNotification:
    """Test ContentProcessor._create_interest_notification method."""

    def test_creates_notification_on_match(
        self, mock_llm, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that notification is created when topics match interests."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        session = get_session()

        article = session.query(Article).filter_by(id=1).first()
        article.topics = json.dumps(["machine learning", "AI"])

        result = processor._create_interest_notification(article, session)
        session.commit()

        assert result is True

        # Verify notification was created
        notification = session.query(Notification).filter_by(
            article_id=article.id, type="interest_match"
        ).first()
        assert notification is not None

        session.close()

    def test_no_notification_without_profile(self, mock_llm, sample_articles, isolated_test_db):
        """Test no notification when no profile exists."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        session = get_session()

        article = session.query(Article).filter_by(id=1).first()
        article.topics = json.dumps(["machine learning"])

        result = processor._create_interest_notification(article, session)

        assert result is False
        session.close()

    def test_no_notification_without_match(
        self, mock_llm, sample_articles, sample_profile, isolated_test_db
    ):
        """Test no notification when topics don't match interests."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        session = get_session()

        article = session.query(Article).filter_by(id=1).first()
        article.topics = json.dumps(["quantum computing", "biology"])  # No match

        result = processor._create_interest_notification(article, session)

        assert result is False
        session.close()

    def test_no_duplicate_notification(
        self, mock_llm, sample_articles, sample_profile, isolated_test_db
    ):
        """Test that duplicate notifications are not created."""
        from mindscout.processors.content import ContentProcessor

        processor = ContentProcessor(llm_client=mock_llm)
        session = get_session()

        article = session.query(Article).filter_by(id=1).first()
        article.topics = json.dumps(["machine learning"])

        # Create first notification
        result1 = processor._create_interest_notification(article, session)
        session.commit()
        assert result1 is True

        # Try to create duplicate
        result2 = processor._create_interest_notification(article, session)
        assert result2 is False

        # Verify only one notification exists
        count = session.query(Notification).filter_by(
            article_id=article.id, type="interest_match"
        ).count()
        assert count == 1

        session.close()


class TestGetArticlesByTopic:
    """Test ContentProcessor.get_articles_by_topic method."""

    def test_get_articles_by_topic(self, mock_llm, isolated_test_db):
        """Test finding articles by topic."""
        from mindscout.processors.content import ContentProcessor

        session = get_session()

        # Create articles with topics
        articles = [
            Article(
                source_id="topic-test-1",
                title="ML Article",
                abstract="About ML",
                url="https://example.com/1",
                source="test",
                topics='["machine learning", "AI"]',
            ),
            Article(
                source_id="topic-test-2",
                title="Deep Learning Article",
                abstract="About DL",
                url="https://example.com/2",
                source="test",
                topics='["deep learning", "neural networks"]',
            ),
            Article(
                source_id="topic-test-3",
                title="No Topics",
                abstract="No topics",
                url="https://example.com/3",
                source="test",
                topics=None,
            ),
        ]
        for article in articles:
            session.add(article)
        session.commit()
        session.close()

        processor = ContentProcessor(llm_client=mock_llm)
        results = processor.get_articles_by_topic("learning")

        # Should find both articles with "learning" in topics
        assert len(results) == 2

    def test_get_articles_by_topic_case_insensitive(self, mock_llm, isolated_test_db):
        """Test case-insensitive topic matching."""
        from mindscout.processors.content import ContentProcessor

        session = get_session()
        article = Article(
            source_id="case-test",
            title="Test",
            abstract="Test",
            url="https://example.com/case",
            source="test",
            topics='["Machine Learning"]',
        )
        session.add(article)
        session.commit()
        session.close()

        processor = ContentProcessor(llm_client=mock_llm)

        # Search with different case
        results = processor.get_articles_by_topic("machine learning")

        assert len(results) == 1

    def test_get_articles_by_topic_with_limit(self, mock_llm, isolated_test_db):
        """Test topic search with limit."""
        from mindscout.processors.content import ContentProcessor

        session = get_session()
        for i in range(5):
            article = Article(
                source_id=f"limit-test-{i}",
                title=f"Test {i}",
                abstract=f"Test {i}",
                url=f"https://example.com/limit/{i}",
                source="test",
                topics='["common topic"]',
            )
            session.add(article)
        session.commit()
        session.close()

        processor = ContentProcessor(llm_client=mock_llm)
        results = processor.get_articles_by_topic("common topic", limit=3)

        assert len(results) == 3
