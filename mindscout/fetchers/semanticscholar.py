"""Semantic Scholar API fetcher with citation data."""

import time
from datetime import datetime
from typing import List, Dict, Optional
import requests

from mindscout.fetchers.base import BaseFetcher


class SemanticScholarFetcher(BaseFetcher):
    """Fetcher for Semantic Scholar API with citation counts."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        """Initialize Semantic Scholar fetcher."""
        super().__init__("semanticscholar")
        self.session = requests.Session()
        # Add headers for better rate limiting
        self.session.headers.update({
            "User-Agent": "MindScout/0.2 (Research Assistant; mailto:user@example.com)"
        })

    def fetch(
        self,
        query: str,
        fields: Optional[List[str]] = None,
        limit: int = 100,
        sort: str = "citationCount:desc",
        year: Optional[str] = None,
        venue: Optional[List[str]] = None,
        min_citations: Optional[int] = None,
    ) -> List[Dict]:
        """Fetch papers from Semantic Scholar.

        Args:
            query: Search query string
            fields: List of fields to return (default: all useful fields)
            limit: Maximum number of results (default: 100, max: 100 per request)
            sort: Sort order - "citationCount:desc", "citationCount:asc",
                  "publicationDate:desc", "publicationDate:asc"
            year: Filter by year (e.g., "2024" or "2020-2024")
            venue: Filter by publication venue
            min_citations: Minimum citation count filter

            Returns:
            List of article dictionaries
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "authors",
                "year",
                "citationCount",
                "influentialCitationCount",
                "publicationDate",
                "url",
                "venue",
                "fieldsOfStudy",
            ]

        articles = []
        offset = 0
        batch_size = min(limit, 100)  # API limit is 100 per request

        while len(articles) < limit:
            params = {
                "query": query,
                "fields": ",".join(fields),
                "offset": offset,
                "limit": batch_size,
            }

            if sort:
                params["sort"] = sort
            if year:
                params["year"] = year
            if venue:
                params["venue"] = ",".join(venue)
            if min_citations:
                params["minCitationCount"] = min_citations

            try:
                response = self.session.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                # Check if we got results
                if "data" not in data or not data["data"]:
                    break

                # Parse results
                for paper in data["data"]:
                    article = self._parse_paper(paper)
                    if article:
                        articles.append(article)

                # Check if there are more results
                total = data.get("total", 0)
                if offset + batch_size >= total or len(data["data"]) < batch_size:
                    break

                offset += batch_size

                # Rate limiting - be nice to the API
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching from Semantic Scholar: {e}")
                break

            if len(articles) >= limit:
                break

        return articles[:limit]

    def _parse_paper(self, paper: Dict) -> Optional[Dict]:
        """Parse a paper from Semantic Scholar API response.

        Args:
            paper: Paper data from API

        Returns:
            Normalized article dictionary or None if invalid
        """
        try:
            # Extract paper ID
            paper_id = paper.get("paperId")
            if not paper_id:
                return None

            # Get title
            title = paper.get("title", "").strip()
            if not title:
                return None

            # Get authors
            authors = []
            for author in paper.get("authors", []):
                name = author.get("name")
                if name:
                    authors.append(name)
            authors_str = ", ".join(authors) if authors else "Unknown"

            # Get abstract
            abstract = paper.get("abstract", "")

            # Get publication date
            pub_date = None
            if paper.get("publicationDate"):
                try:
                    pub_date = datetime.fromisoformat(paper["publicationDate"])
                except (ValueError, TypeError):
                    # Try year only
                    year = paper.get("year")
                    if year:
                        try:
                            pub_date = datetime(year, 1, 1)
                        except (ValueError, TypeError):
                            pass

            # Get URL
            url = paper.get("url", f"https://www.semanticscholar.org/paper/{paper_id}")

            # Get venue/conference
            venue = paper.get("venue", "")

            # Get fields of study (as categories)
            fields_of_study = paper.get("fieldsOfStudy", [])
            categories = ",".join(fields_of_study[:3]) if fields_of_study else ""

            # Get citation metrics
            citation_count = paper.get("citationCount", 0)
            influential_citations = paper.get("influentialCitationCount", 0)

            # Create normalized article
            article = {
                "source_id": paper_id,
                "source": "semanticscholar",
                "title": title,
                "authors": authors_str,
                "abstract": abstract or "",
                "url": url,
                "published_date": pub_date,
                "categories": categories,
                "citation_count": citation_count,
                "influential_citations": influential_citations,
            }

            return self.normalize_article(article)

        except Exception as e:
            print(f"Error parsing paper: {e}")
            return None

    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """Get paper details by arXiv ID to enrich existing papers.

        Args:
            arxiv_id: arXiv ID (e.g., "2301.12345")

        Returns:
            Article dictionary with citation data or None
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/paper/arXiv:{arxiv_id}",
                params={"fields": "paperId,citationCount,influentialCitationCount"},
                timeout=10
            )
            response.raise_for_status()
            paper = response.json()

            if "paperId" in paper:
                return {
                    "source_id": paper["paperId"],
                    "citation_count": paper.get("citationCount", 0),
                    "influential_citations": paper.get("influentialCitationCount", 0),
                }

        except requests.exceptions.RequestException:
            pass

        return None


def enrich_arxiv_papers_with_citations(limit: int = 100) -> int:
    """Enrich existing arXiv papers with citation data from Semantic Scholar.

    Args:
        limit: Maximum number of papers to enrich

    Returns:
        Number of papers updated
    """
    from mindscout.database import get_session, Article

    fetcher = SemanticScholarFetcher()
    session = get_session()
    updated = 0

    try:
        # Get arXiv papers without citation data
        papers = session.query(Article).filter(
            Article.source == "arxiv",
            Article.citation_count == None  # noqa: E711
        ).limit(limit).all()

        for paper in papers:
            # Extract arXiv ID from source_id
            arxiv_id = paper.source_id

            # Get citation data
            citation_data = fetcher.get_paper_by_arxiv_id(arxiv_id)

            if citation_data:
                paper.citation_count = citation_data["citation_count"]
                paper.influential_citations = citation_data["influential_citations"]
                updated += 1

            # Rate limiting
            time.sleep(1)

        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Error enriching papers: {e}")
    finally:
        session.close()

    return updated
