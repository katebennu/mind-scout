"""Advanced arXiv API fetcher with search and filtering capabilities."""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import urllib.parse
import xml.etree.ElementTree as ET
import requests

from mindscout.database import Article, get_session


class ArxivAdvancedFetcher:
    """Advanced arXiv fetcher using the arXiv API for complex queries."""

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        """Initialize the advanced fetcher."""
        self.session = requests.Session()

    def build_query(
        self,
        keywords: Optional[str] = None,
        categories: Optional[List[str]] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> str:
        """Build a search query for the arXiv API.

        Args:
            keywords: Keywords to search in all fields
            categories: List of arXiv categories (e.g., ['cs.AI', 'cs.LG'])
            author: Author name to search for
            title: Title keywords to search for
            from_date: Start date for submission date filter
            to_date: End date for submission date filter

        Returns:
            URL-encoded query string
        """
        query_parts = []

        if keywords:
            query_parts.append(f"all:{keywords}")

        if categories:
            cat_query = "+OR+".join(f"cat:{cat}" for cat in categories)
            if len(categories) > 1:
                cat_query = f"({cat_query})"
            query_parts.append(cat_query)

        if author:
            query_parts.append(f"au:{author}")

        if title:
            query_parts.append(f"ti:{title}")

        # Combine query parts with AND
        query = "+AND+".join(query_parts) if query_parts else "all:*"

        # Add date range if specified
        if from_date or to_date:
            from_str = from_date.strftime("%Y%m%d0000") if from_date else "19910101000"
            to_str = to_date.strftime("%Y%m%d2359") if to_date else datetime.now().strftime("%Y%m%d2359")
            query += f"+AND+submittedDate:[{from_str}+TO+{to_str}]"

        return query

    def search(
        self,
        keywords: Optional[str] = None,
        categories: Optional[List[str]] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        max_results: int = 100,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[Dict]:
        """Search arXiv using the API.

        Args:
            keywords: Keywords to search in all fields
            categories: List of arXiv categories
            author: Author name
            title: Title keywords
            from_date: Start date for filtering
            to_date: End date for filtering
            max_results: Maximum number of results (default: 100)
            sort_by: Sort field - "submittedDate", "lastUpdatedDate", or "relevance"
            sort_order: "ascending" or "descending"

        Returns:
            List of article dictionaries
        """
        query = self.build_query(keywords, categories, author, title, from_date, to_date)

        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        # Retry logic for rate limiting
        max_retries = 3
        retry_delay = 5  # Start with 5 seconds

        for retry in range(max_retries):
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                # Parse XML response
                articles = self._parse_feed(response.text)

                # Be nice to arXiv API - rate limit
                time.sleep(3)

                return articles

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit hit
                    if retry < max_retries - 1:
                        wait_time = retry_delay * (2 ** retry)  # Exponential backoff
                        print(f"arXiv rate limit hit. Waiting {wait_time}s before retry {retry + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(
                            "arXiv rate limit exceeded. Please wait a few minutes and try again. "
                            "arXiv allows about 1 request per 3 seconds."
                        )
                else:
                    raise

        return []

    def _parse_feed(self, xml_text: str) -> List[Dict]:
        """Parse arXiv API XML response.

        Args:
            xml_text: XML response from arXiv API

        Returns:
            List of article dictionaries
        """
        articles = []

        # Parse XML with namespaces
        root = ET.fromstring(xml_text)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        # Find all entry elements
        for entry in root.findall("atom:entry", ns):
            # Extract arXiv ID from the ID URL
            id_url = entry.find("atom:id", ns).text
            arxiv_id = id_url.split("/abs/")[-1]
            if "v" in arxiv_id:
                arxiv_id = arxiv_id.split("v")[0]

            # Get title
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")

            # Get authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                authors.append(name)
            authors_str = ", ".join(authors)

            # Get abstract
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")

            # Get published date
            published_str = entry.find("atom:published", ns).text
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))

            # Get categories
            categories = []
            for category in entry.findall("atom:category", ns):
                categories.append(category.get("term"))
            categories_str = ",".join(categories[:3])  # Limit to first 3

            # Get PDF link
            pdf_link = None
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_link = link.get("href")
                    break
            if not pdf_link:
                pdf_link = f"https://arxiv.org/abs/{arxiv_id}"

            article = {
                "source_id": arxiv_id,
                "source": "arxiv",
                "title": title,
                "authors": authors_str,
                "abstract": abstract,
                "url": pdf_link,
                "published_date": published,
                "categories": categories_str,
            }

            articles.append(article)

        return articles

    def fetch_and_store(
        self,
        keywords: Optional[str] = None,
        categories: Optional[List[str]] = None,
        author: Optional[str] = None,
        title: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        max_results: int = 100,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> int:
        """Search arXiv and store results in database.

        Args:
            keywords: Keywords to search
            categories: List of categories
            author: Author name
            title: Title keywords
            from_date: Start date
            to_date: End date
            max_results: Maximum results
            sort_by: Sort field
            sort_order: Sort order

        Returns:
            Number of new articles added
        """
        articles = self.search(
            keywords=keywords,
            categories=categories,
            author=author,
            title=title,
            from_date=from_date,
            to_date=to_date,
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        session = get_session()
        new_count = 0

        try:
            for article_data in articles:
                # Check if already exists
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


def fetch_last_month(categories: Optional[List[str]] = None, max_results: int = 100) -> int:
    """Convenience function to fetch papers from the last month.

    Args:
        categories: List of categories (default: cs.AI, cs.LG, cs.CL)
        max_results: Maximum results

    Returns:
        Number of new articles added
    """
    if categories is None:
        categories = ["cs.AI", "cs.LG", "cs.CL"]

    fetcher = ArxivAdvancedFetcher()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=30)

    return fetcher.fetch_and_store(
        categories=categories,
        from_date=from_date,
        to_date=to_date,
        max_results=max_results,
        sort_by="submittedDate",
        sort_order="descending",
    )


def fetch_by_keyword(keyword: str, max_results: int = 50, categories: Optional[List[str]] = None) -> int:
    """Fetch papers matching a keyword.

    Args:
        keyword: Keyword to search for
        max_results: Maximum results
        categories: Optional list of categories to filter by

    Returns:
        Number of new articles added
    """
    fetcher = ArxivAdvancedFetcher()
    return fetcher.fetch_and_store(
        keywords=keyword,
        categories=categories,
        max_results=max_results,
        sort_by="relevance",
    )
