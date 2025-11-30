"""Content processing logic for Mind Scout."""

import json
from datetime import datetime
from typing import Optional

from mindscout.database import Article, Notification, UserProfile, get_session
from mindscout.processors.llm import LLMClient


class ContentProcessor:
    """Processes articles using LLM for summarization and topic extraction."""

    def __init__(self, llm_client: Optional[LLMClient] = None, lazy_init: bool = False):
        """Initialize content processor.

        Args:
            llm_client: LLM client instance. If None, creates a new one when needed.
            lazy_init: If True, don't initialize LLM client until needed.
        """
        if lazy_init:
            self.llm = None
            self._llm_client_provided = llm_client
        else:
            self.llm = llm_client or LLMClient()
            self._llm_client_provided = None

    def _ensure_llm(self):
        """Ensure LLM client is initialized."""
        if self.llm is None:
            self.llm = self._llm_client_provided or LLMClient()

    def process_article(self, article: Article, force: bool = False) -> bool:
        """Process a single article.

        Args:
            article: Article to process
            force: If True, reprocess even if already processed

        Returns:
            True if processing succeeded, False otherwise
        """
        # Skip if already processed (unless forcing)
        if article.processed and not force:
            return False

        # Ensure LLM is initialized
        self._ensure_llm()

        try:
            # Commented out to save token usage; can be re-enabled if needed
            # TODO: Remove or uncomment depending on whether abstract summarization is needed in the future
            # Generate summary from abstract
            # if article.abstract:
            #     article.summary = self.llm.summarize(article.abstract, max_sentences=2)
            #     article.summary = article.abstract
            # else:
            #     article.summary = None

            # Extract topics
            topics = self.llm.extract_topics(
                title=article.title,
                abstract=article.abstract or "",
                max_topics=5,
            )
            article.topics = json.dumps(topics)

            # Note: Embeddings are generated and stored in ChromaDB via VectorStore.index_articles()
            # which uses SentenceTransformer for real semantic embeddings

            # Mark as processed
            article.processed = True
            article.processing_date = datetime.utcnow()

            return True

        except Exception as e:
            print(f"Error processing article {article.id}: {e}")
            return False

    def process_batch(
        self,
        limit: Optional[int] = None,
        force: bool = False,
        only_unprocessed: bool = True,
        batch_size: int = 10,
    ) -> tuple[int, int]:
        """Process multiple articles using multi-article prompts.

        This method batches articles together in single LLM calls for efficiency.
        Reduces API calls by ~5-10x compared to processing one at a time.

        Args:
            limit: Maximum number of articles to process. If None, processes all.
            force: If True, reprocess even if already processed
            only_unprocessed: If True, only process unprocessed articles
            batch_size: Number of articles to process per LLM call (default 10)

        Returns:
            Tuple of (processed_count, failed_count)
        """
        session = get_session()
        processed_count = 0
        failed_count = 0

        try:
            # Ensure LLM is initialized
            self._ensure_llm()

            # Build query
            query = session.query(Article)

            if only_unprocessed and not force:
                query = query.filter(Article.processed == False)  # noqa: E712

            if limit:
                query = query.limit(limit)

            articles = query.all()

            # Process in batches
            for i in range(0, len(articles), batch_size):
                batch = articles[i : i + batch_size]

                # Prepare batch data for LLM
                batch_data = [
                    {
                        "id": str(article.id),
                        "title": article.title,
                        "abstract": article.abstract or "",
                    }
                    for article in batch
                ]

                # Extract topics for all articles in batch with single API call
                topics_map = self.llm.extract_topics_batch(batch_data, max_topics=5)

                # Update articles with results
                for article in batch:
                    article_id = str(article.id)
                    if article_id in topics_map and topics_map[article_id]:
                        article.topics = json.dumps(topics_map[article_id])
                        article.processed = True
                        article.processing_date = datetime.utcnow()
                        processed_count += 1

                        # Create interest-based notification
                        self._create_interest_notification(article, session)
                    else:
                        # Fall back to individual processing if batch failed
                        success = self.process_article(article, force=force)
                        if success:
                            processed_count += 1
                            self._create_interest_notification(article, session)
                        else:
                            failed_count += 1

                # Commit after each batch
                session.commit()

        except Exception as e:
            session.rollback()
            print(f"Batch processing error: {e}")
        finally:
            session.close()

        return processed_count, failed_count

    def process_batch_legacy(
        self,
        limit: Optional[int] = None,
        force: bool = False,
        only_unprocessed: bool = True,
    ) -> tuple[int, int]:
        """Process articles one at a time (legacy method).

        Use process_batch() instead for better efficiency.

        Args:
            limit: Maximum number of articles to process
            force: If True, reprocess even if already processed
            only_unprocessed: If True, only process unprocessed articles

        Returns:
            Tuple of (processed_count, failed_count)
        """
        session = get_session()
        processed_count = 0
        failed_count = 0

        try:
            query = session.query(Article)

            if only_unprocessed and not force:
                query = query.filter(Article.processed == False)  # noqa: E712

            if limit:
                query = query.limit(limit)

            articles = query.all()

            for article in articles:
                success = self.process_article(article, force=force)
                if success:
                    processed_count += 1
                    self._create_interest_notification(article, session)
                else:
                    if not (article.processed and not force):
                        failed_count += 1

                session.commit()

        except Exception as e:
            session.rollback()
            print(f"Batch processing error: {e}")
        finally:
            session.close()

        return processed_count, failed_count

    def create_async_batch(self, limit: Optional[int] = None) -> str:
        """Create an async batch for processing (50% cheaper).

        Uses Anthropic's Message Batches API. Results available within 24 hours.
        Ideal for scheduled background jobs where immediate results aren't needed.

        Args:
            limit: Maximum number of articles to include in batch

        Returns:
            Batch ID for checking status and retrieving results later
        """
        session = get_session()

        try:
            self._ensure_llm()

            # Get unprocessed articles
            query = session.query(Article).filter(Article.processed == False)  # noqa: E712

            if limit:
                query = query.limit(limit)

            articles = query.all()

            if not articles:
                raise ValueError("No unprocessed articles found")

            # Prepare batch data
            batch_data = [
                {
                    "id": str(article.id),
                    "title": article.title,
                    "abstract": article.abstract or "",
                }
                for article in articles
            ]

            # Create async batch
            batch_id = self.llm.create_topic_extraction_batch(batch_data)
            return batch_id

        finally:
            session.close()

    def apply_batch_results(self, batch_id: str) -> tuple[int, int]:
        """Apply results from a completed async batch to articles.

        Args:
            batch_id: The batch ID from create_async_batch

        Returns:
            Tuple of (updated_count, failed_count)
        """
        session = get_session()
        updated_count = 0
        failed_count = 0

        try:
            self._ensure_llm()

            # Get batch results
            results = self.llm.get_batch_results(batch_id)

            for article_id, topics in results.items():
                article = session.query(Article).filter_by(id=int(article_id)).first()
                if not article:
                    failed_count += 1
                    continue

                if topics:
                    article.topics = json.dumps(topics)
                    article.processed = True
                    article.processing_date = datetime.utcnow()
                    updated_count += 1

                    # Create notification if matches interests
                    self._create_interest_notification(article, session)
                else:
                    failed_count += 1

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"Error applying batch results: {e}")
        finally:
            session.close()

        return updated_count, failed_count

    def get_processing_stats(self) -> dict:
        """Get statistics about processed articles.

        Returns:
            Dictionary with processing statistics
        """
        session = get_session()

        try:
            total = session.query(Article).count()
            processed = session.query(Article).filter(Article.processed).count()  # noqa: E712
            unprocessed = total - processed

            # Get topics distribution
            all_topics = []
            for article in session.query(Article).filter(Article.topics.isnot(None)).all():
                try:
                    topics = json.loads(article.topics)
                    all_topics.extend(topics)
                except json.JSONDecodeError:
                    pass

            # Count topic frequencies
            from collections import Counter

            topic_counts = Counter(all_topics)
            top_topics = topic_counts.most_common(10)

            return {
                "total_articles": total,
                "processed": processed,
                "unprocessed": unprocessed,
                "processing_rate": (processed / total * 100) if total > 0 else 0,
                "top_topics": top_topics,
            }

        finally:
            session.close()

    def _create_interest_notification(self, article: Article, session) -> bool:
        """Create notification if article topics match user interests.

        Args:
            article: Article that was just processed
            session: Database session to use

        Returns:
            True if notification was created, False otherwise
        """
        # Get user profile
        profile = session.query(UserProfile).first()
        if not profile or not profile.interests:
            return False

        # Parse user interests
        user_interests = {i.strip().lower() for i in profile.interests.split(",") if i.strip()}
        if not user_interests:
            return False

        # Parse article topics
        try:
            article_topics = json.loads(article.topics) if article.topics else []
        except json.JSONDecodeError:
            return False

        article_topics_lower = {t.lower() for t in article_topics}

        # Check for any overlap between interests and topics
        matching_topics = user_interests & article_topics_lower
        if not matching_topics:
            return False

        # Check if notification already exists for this article
        existing = (
            session.query(Notification)
            .filter_by(article_id=article.id, type="interest_match")
            .first()
        )
        if existing:
            return False

        # Create interest-match notification
        notification = Notification(article_id=article.id, type="interest_match")
        session.add(notification)
        return True

    def get_articles_by_topic(self, topic: str, limit: int = 10) -> list[Article]:
        """Find articles matching a specific topic.

        Args:
            topic: Topic to search for
            limit: Maximum number of results

        Returns:
            List of matching articles
        """
        session = get_session()

        try:
            articles = []
            query = session.query(Article).filter(Article.topics.isnot(None))

            for article in query.all():
                try:
                    topics = json.loads(article.topics)
                    # Case-insensitive partial match
                    if any(topic.lower() in t.lower() for t in topics):
                        articles.append(article)
                        if len(articles) >= limit:
                            break
                except json.JSONDecodeError:
                    pass

            return articles

        finally:
            session.close()
