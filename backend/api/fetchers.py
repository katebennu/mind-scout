"""Paper fetcher API endpoints for arXiv and Semantic Scholar."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mindscout.config import ARXIV_FEEDS, DEFAULT_CATEGORIES

router = APIRouter()


class ArxivFetchRequest(BaseModel):
    query: Optional[str] = None  # Keywords to search in all fields
    categories: Optional[List[str]] = None
    author: Optional[str] = None
    title: Optional[str] = None
    max_results: Optional[int] = 100


class SemanticScholarFetchRequest(BaseModel):
    query: str
    limit: Optional[int] = 50
    year: Optional[str] = None
    min_citations: Optional[int] = None


class FetchResponse(BaseModel):
    success: bool
    new_articles: int
    message: str


class CategoryResponse(BaseModel):
    code: str
    name: str
    url: str


@router.get("/arxiv/categories", response_model=List[CategoryResponse])
def get_arxiv_categories():
    """Get available arXiv categories."""
    category_names = {
        "cs.AI": "Artificial Intelligence",
        "cs.LG": "Machine Learning",
        "cs.CL": "Computation and Language",
        "cs.CV": "Computer Vision",
    }

    return [
        CategoryResponse(
            code=code,
            name=category_names.get(code, code),
            url=url
        )
        for code, url in ARXIV_FEEDS.items()
    ]


@router.post("/arxiv", response_model=FetchResponse)
def fetch_arxiv(request: ArxivFetchRequest = None):
    """Fetch new papers from arXiv using the arXiv API.

    Args:
        request: Optional request body with query, categories, author, title, and max_results.
                 If not provided, fetches default categories.
    """
    from mindscout.fetchers.arxiv_advanced import ArxivAdvancedFetcher

    query = None
    categories = None
    author = None
    title = None
    max_results = 100

    if request:
        query = request.query.strip() if request.query else None
        author = request.author.strip() if request.author else None
        title = request.title.strip() if request.title else None

        if request.categories:
            # Validate categories
            invalid = [c for c in request.categories if c not in ARXIV_FEEDS]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid categories: {', '.join(invalid)}"
                )
            categories = request.categories

        if request.max_results:
            max_results = min(request.max_results, 500)  # Cap at 500

    # If no search criteria provided, use default categories
    if not query and not categories and not author and not title:
        categories = DEFAULT_CATEGORIES

    try:
        fetcher = ArxivAdvancedFetcher()

        # Determine sort - use relevance if keyword search, otherwise submittedDate
        sort_by = "relevance" if query else "submittedDate"

        new_count = fetcher.fetch_and_store(
            keywords=query,
            categories=categories,
            author=author,
            title=title,
            max_results=max_results,
            sort_by=sort_by,
            sort_order="descending",
        )

        # Build description message
        parts = []
        if query:
            parts.append(f"query: '{query}'")
        if categories:
            parts.append(f"categories: {', '.join(categories)}")
        if author:
            parts.append(f"author: '{author}'")
        if title:
            parts.append(f"title: '{title}'")

        desc = ", ".join(parts) if parts else "default categories"
        return FetchResponse(
            success=True,
            new_articles=new_count,
            message=f"Fetched {new_count} new papers from arXiv ({desc})"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semanticscholar", response_model=FetchResponse)
def fetch_semantic_scholar(request: SemanticScholarFetchRequest):
    """Fetch papers from Semantic Scholar by search query.

    Args:
        request: Search parameters including query, limit, year filter,
                 and minimum citation count.
    """
    from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    try:
        fetcher = SemanticScholarFetcher()

        # Fetch papers
        articles = fetcher.fetch(
            query=request.query.strip(),
            limit=min(request.limit or 50, 100),  # Cap at 100
            year=request.year,
            min_citations=request.min_citations,
        )

        # Store in database
        new_count = fetcher.store_articles(articles)
        fetcher.close()

        return FetchResponse(
            success=True,
            new_articles=new_count,
            message=f"Fetched {new_count} new papers from Semantic Scholar for '{request.query}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=FetchResponse)
def process_unprocessed():
    """Process unprocessed articles with LLM to extract topics/summaries."""
    from mindscout.processors.content import ContentProcessor

    try:
        processor = ContentProcessor()
        result = processor.process_all(limit=50)

        return FetchResponse(
            success=True,
            new_articles=result["processed"],
            message=f"Processed {result['processed']} articles ({result['failed']} failed)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
