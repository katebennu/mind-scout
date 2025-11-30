"""Tests for scheduler jobs and batch processing."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from mindscout.database import Article, PendingBatch, get_db_session, get_session


@pytest.fixture
def sample_unprocessed_articles(isolated_test_db):
    """Create sample unprocessed articles."""
    session = get_session()

    articles = [
        Article(
            source_id=f"test-article-{i}",
            title=f"Test Article {i}",
            authors="Test Author",
            abstract=f"Abstract for article {i}",
            url=f"https://example.com/{i}",
            source="arxiv",
            processed=False,
        )
        for i in range(5)
    ]

    for article in articles:
        session.add(article)
    session.commit()

    yield articles

    session.close()


class TestPendingBatchModel:
    """Test PendingBatch database model."""

    def test_create_pending_batch(self, isolated_test_db):
        """Test creating a pending batch record."""
        with get_db_session() as session:
            batch = PendingBatch(
                batch_id="msgbatch_test123",
                article_count=10,
                status="pending",
            )
            session.add(batch)

        # Verify it was saved
        with get_db_session() as session:
            saved = session.query(PendingBatch).filter_by(batch_id="msgbatch_test123").first()
            assert saved is not None
            assert saved.article_count == 10
            assert saved.status == "pending"
            assert saved.created_date is not None

    def test_update_batch_status(self, isolated_test_db):
        """Test updating batch status."""
        with get_db_session() as session:
            batch = PendingBatch(
                batch_id="msgbatch_test456",
                article_count=5,
                status="pending",
            )
            session.add(batch)

        # Update status
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id="msgbatch_test456").first()
            batch.status = "completed"
            batch.completed_date = datetime.utcnow()

        # Verify update
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id="msgbatch_test456").first()
            assert batch.status == "completed"
            assert batch.completed_date is not None

    def test_batch_id_unique_constraint(self, isolated_test_db):
        """Test that batch_id must be unique."""
        with get_db_session() as session:
            batch1 = PendingBatch(batch_id="msgbatch_dup", article_count=1)
            session.add(batch1)

        with pytest.raises(Exception):  # noqa: B017 - IntegrityError
            with get_db_session() as session:
                batch2 = PendingBatch(batch_id="msgbatch_dup", article_count=2)
                session.add(batch2)


class TestFetchAndProcessJob:
    """Test the daily fetch and process job."""

    @pytest.mark.asyncio
    async def test_fetch_and_process_creates_batch(
        self, isolated_test_db, sample_unprocessed_articles
    ):
        """Test that job creates an async batch for unprocessed articles."""
        from backend.scheduler.jobs import fetch_and_process_job

        mock_batch_id = "msgbatch_test789"

        # Create mock processor
        mock_processor = MagicMock()
        mock_processor.create_async_batch.return_value = mock_batch_id

        with patch("backend.scheduler.jobs.get_user_interests", return_value=[]):
            with patch(
                "mindscout.processors.content.ContentProcessor", return_value=mock_processor
            ):
                result = await fetch_and_process_job()

        assert result["batch_id"] == mock_batch_id
        assert result["batch_articles"] == 5

        # Verify batch was stored in database
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id=mock_batch_id).first()
            assert batch is not None
            assert batch.status == "pending"

    @pytest.mark.asyncio
    async def test_fetch_and_process_no_unprocessed_articles(self, isolated_test_db):
        """Test job handles case with no unprocessed articles."""
        from backend.scheduler.jobs import fetch_and_process_job

        with patch("backend.scheduler.jobs.get_user_interests", return_value=[]):
            result = await fetch_and_process_job()

        assert result["batch_id"] is None
        assert result["batch_articles"] == 0


class TestCheckPendingBatchesJob:
    """Test the batch checking job."""

    @pytest.mark.asyncio
    async def test_check_pending_batches_completes_batch(
        self, isolated_test_db, sample_unprocessed_articles
    ):
        """Test that completed batches are processed."""
        from backend.scheduler.jobs import check_pending_batches_job

        # Create a pending batch
        with get_db_session() as session:
            batch = PendingBatch(
                batch_id="msgbatch_complete",
                article_count=5,
                status="pending",
            )
            session.add(batch)

        # Mock LLM client and processor
        mock_llm = MagicMock()
        mock_llm.get_batch_status.return_value = {
            "status": "ended",
            "counts": {"succeeded": 5, "processing": 0, "errored": 0, "canceled": 0, "expired": 0},
        }

        mock_processor = MagicMock()
        mock_processor.apply_batch_results.return_value = (5, 0)

        with patch("mindscout.processors.llm.LLMClient", return_value=mock_llm):
            with patch(
                "mindscout.processors.content.ContentProcessor", return_value=mock_processor
            ):
                result = await check_pending_batches_job()

        assert result["checked"] == 1
        assert result["completed"] == 1
        assert result["articles_updated"] == 5

        # Verify batch status updated
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id="msgbatch_complete").first()
            assert batch.status == "completed"
            assert batch.completed_date is not None

    @pytest.mark.asyncio
    async def test_check_pending_batches_still_processing(self, isolated_test_db):
        """Test handling of batches still processing."""
        from backend.scheduler.jobs import check_pending_batches_job

        # Create a pending batch
        with get_db_session() as session:
            batch = PendingBatch(
                batch_id="msgbatch_processing",
                article_count=10,
                status="pending",
            )
            session.add(batch)

        mock_llm = MagicMock()
        mock_llm.get_batch_status.return_value = {
            "status": "in_progress",
            "counts": {"succeeded": 3, "processing": 7, "errored": 0, "canceled": 0, "expired": 0},
        }

        with patch("mindscout.processors.llm.LLMClient", return_value=mock_llm):
            with patch("mindscout.processors.content.ContentProcessor"):
                result = await check_pending_batches_job()

        assert result["checked"] == 1
        assert result["still_pending"] == 1
        assert result["completed"] == 0

        # Verify batch status updated to processing
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id="msgbatch_processing").first()
            assert batch.status == "processing"

    @pytest.mark.asyncio
    async def test_check_pending_batches_handles_failure(self, isolated_test_db):
        """Test handling of failed batches."""
        from backend.scheduler.jobs import check_pending_batches_job

        # Create a pending batch
        with get_db_session() as session:
            batch = PendingBatch(
                batch_id="msgbatch_failed",
                article_count=5,
                status="pending",
            )
            session.add(batch)

        mock_llm = MagicMock()
        mock_llm.get_batch_status.return_value = {
            "status": "expired",
            "counts": {"succeeded": 0, "processing": 0, "errored": 0, "canceled": 0, "expired": 5},
        }

        with patch("mindscout.processors.llm.LLMClient", return_value=mock_llm):
            with patch("mindscout.processors.content.ContentProcessor"):
                result = await check_pending_batches_job()

        assert result["checked"] == 1
        assert result["failed"] == 1

        # Verify batch marked as failed
        with get_db_session() as session:
            batch = session.query(PendingBatch).filter_by(batch_id="msgbatch_failed").first()
            assert batch.status == "failed"
            assert "expired" in batch.error_message

    @pytest.mark.asyncio
    async def test_check_pending_batches_no_pending(self, isolated_test_db):
        """Test with no pending batches."""
        from backend.scheduler.jobs import check_pending_batches_job

        # Job initializes LLM client even if no batches, so we need to mock it
        with patch("mindscout.processors.llm.LLMClient"):
            with patch("mindscout.processors.content.ContentProcessor"):
                result = await check_pending_batches_job()

        assert result["checked"] == 0
        assert result["completed"] == 0
