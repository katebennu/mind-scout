"""arXiv RSS feed fetcher."""

from datetime import datetime
from typing import List, Dict
import feedparser
from mindscout.config import ARXIV_FEEDS, DEFAULT_CATEGORIES
from mindscout.database import Article, get_session


def parse_arxiv_id(link: str) -> str:
    """Extract arXiv ID from link.

    Example: http://arxiv.org/abs/2401.12345v1 -> 2401.12345
    """
    parts = link.split("/")
    arxiv_id = parts[-1]
    # Remove version suffix if present
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    return arxiv_id


def fetch_arxiv_category(category: str) -> List[Dict]:
    """Fetch articles from a single arXiv category.

    Args:
        category: arXiv category code (e.g., 'cs.AI')

    Returns:
        List of article dictionaries
    """
    feed_url = ARXIV_FEEDS.get(category)
    if not feed_url:
        raise ValueError(f"Unknown category: {category}")

    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed.entries:
        # Extract arXiv ID
        arxiv_id = parse_arxiv_id(entry.link)

        # Parse authors
        authors = ", ".join(author.get("name", "") for author in entry.get("authors", []))

        # Parse published date
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])

        article = {
            "source_id": arxiv_id,
            "source": "arxiv",
            "title": entry.title,
            "authors": authors,
            "abstract": entry.summary,
            "url": entry.link,
            "published_date": published,
            "categories": category,
        }
        articles.append(article)

    return articles


def fetch_arxiv(categories: List[str] = None) -> int:
    """Fetch articles from arXiv and store in database.

    Args:
        categories: List of category codes to fetch. If None, uses DEFAULT_CATEGORIES.

    Returns:
        Number of new articles added
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    session = get_session()
    new_count = 0

    try:
        for category in categories:
            articles = fetch_arxiv_category(category)

            for article_data in articles:
                # Check if article already exists
                existing = session.query(Article).filter_by(
                    source_id=article_data["source_id"]
                ).first()

                if existing:
                    continue

                # Create new article
                article = Article(**article_data)
                session.add(article)
                new_count += 1

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

    return new_count
