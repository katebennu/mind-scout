"""Base fetcher class for all content sources."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from mindscout.database import Article, get_db_session

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for content fetchers."""

    def __init__(self, source_name: str):
        """Initialize fetcher.

        Args:
            source_name: Name of the source (e.g., 'arxiv', 'semanticscholar')
        """
        self.source_name = source_name

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict]:
        """Fetch articles from the source.

        Returns:
            List of article dictionaries with standardized fields
        """
        pass

    def store_articles(self, articles: List[Dict]) -> int:
        """Store articles in database.

        Args:
            articles: List of article dictionaries

        Returns:
            Number of new articles added
        """
        new_count = 0

        with get_db_session() as session:
            for article_data in articles:
                # Check if already exists
                existing = session.query(Article).filter_by(
                    source_id=article_data["source_id"],
                    source=article_data["source"]
                ).first()

                if existing:
                    # Update existing article with new metadata if available
                    self._update_article(existing, article_data)
                    continue

                # Create new article
                article = Article(**article_data)
                session.add(article)
                new_count += 1

        logger.info(f"Stored {new_count} new articles from {self.source_name}")
        return new_count

    def _update_article(self, existing: Article, new_data: Dict):
        """Update existing article with new metadata.

        Args:
            existing: Existing Article object
            new_data: New article data dictionary
        """
        # Update citation count if provided
        if 'citation_count' in new_data and new_data['citation_count'] is not None:
            existing.citation_count = new_data['citation_count']

        # Update influential citations if provided
        if 'influential_citations' in new_data and new_data['influential_citations'] is not None:
            existing.influential_citations = new_data['influential_citations']

        # Update GitHub URL if provided
        if 'github_url' in new_data and new_data['github_url']:
            existing.github_url = new_data['github_url']
            existing.has_implementation = True

        # Update Papers with Code URL if provided
        if 'paper_url_pwc' in new_data and new_data['paper_url_pwc']:
            existing.paper_url_pwc = new_data['paper_url_pwc']

        # Update Hugging Face upvotes if provided
        if 'hf_upvotes' in new_data and new_data['hf_upvotes'] is not None:
            existing.hf_upvotes = new_data['hf_upvotes']

    def fetch_and_store(self, **kwargs) -> int:
        """Fetch articles and store them in database.

        Args:
            **kwargs: Arguments to pass to fetch method

        Returns:
            Number of new articles added
        """
        articles = self.fetch(**kwargs)
        return self.store_articles(articles)

    @staticmethod
    def normalize_article(article_data: Dict) -> Dict:
        """Normalize article data to standard format.

        Args:
            article_data: Raw article data

        Returns:
            Normalized article dictionary with standard fields
        """
        # Standard fields that all articles must have
        required_fields = ['source_id', 'source', 'title', 'url']

        for field in required_fields:
            if field not in article_data:
                raise ValueError(f"Missing required field: {field}")

        # Optional fields with defaults
        normalized = {
            'authors': article_data.get('authors', ''),
            'abstract': article_data.get('abstract', ''),
            'published_date': article_data.get('published_date'),
            'categories': article_data.get('categories', ''),
            'citation_count': article_data.get('citation_count'),
            'influential_citations': article_data.get('influential_citations'),
            'github_url': article_data.get('github_url'),
            'has_implementation': article_data.get('has_implementation', False),
            'paper_url_pwc': article_data.get('paper_url_pwc'),
            'hf_upvotes': article_data.get('hf_upvotes'),
        }

        # Add required fields
        for field in required_fields:
            normalized[field] = article_data[field]

        return normalized
