"""Content processing logic for Mind Scout."""

import json
from datetime import datetime
from typing import Optional, List
from mindscout.database import get_session, Article
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
            # Generate summary from abstract
            if article.abstract:
                article.summary = self.llm.summarize(article.abstract, max_sentences=2)
            else:
                article.summary = None

            # Extract topics
            topics = self.llm.extract_topics(
                title=article.title,
                abstract=article.abstract or "",
                max_topics=5,
            )
            article.topics = json.dumps(topics)

            # Generate embedding (using title + abstract)
            embed_text = f"{article.title}\n\n{article.abstract or ''}"
            embedding = self.llm.generate_embedding(embed_text)
            article.embedding = json.dumps(embedding)

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
    ) -> tuple[int, int]:
        """Process multiple articles in batch.

        Args:
            limit: Maximum number of articles to process. If None, processes all.
            force: If True, reprocess even if already processed
            only_unprocessed: If True, only process unprocessed articles

        Returns:
            Tuple of (processed_count, failed_count)
        """
        session = get_session()
        processed_count = 0
        failed_count = 0

        try:
            # Build query
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
                else:
                    if not (article.processed and not force):
                        # Only count as failed if we actually tried to process
                        failed_count += 1

                # Commit after each article to save progress
                session.commit()

        except Exception as e:
            session.rollback()
            print(f"Batch processing error: {e}")
        finally:
            session.close()

        return processed_count, failed_count

    def get_processing_stats(self) -> dict:
        """Get statistics about processed articles.

        Returns:
            Dictionary with processing statistics
        """
        session = get_session()

        try:
            total = session.query(Article).count()
            processed = session.query(Article).filter(Article.processed == True).count()  # noqa: E712
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

    def get_articles_by_topic(self, topic: str, limit: int = 10) -> List[Article]:
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
