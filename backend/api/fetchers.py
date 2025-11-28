"""Paper fetcher API endpoints for arXiv and Semantic Scholar."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from mindscout.config import ARXIV_FEEDS, DEFAULT_CATEGORIES, get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

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
@limiter.limit(f"{settings.rate_limit_requests}/minute")
def fetch_arxiv(request: Request, body: ArxivFetchRequest = None):
    """Fetch new papers from arXiv using the arXiv API.

    Args:
        body: Optional request body with query, categories, author, title, and max_results.
              If not provided, fetches default categories.
    """
    from mindscout.fetchers.arxiv_advanced import ArxivAdvancedFetcher

    query = None
    categories = None
    author = None
    title = None
    max_results = 100

    if body:
        query = body.query.strip() if body.query else None
        author = body.author.strip() if body.author else None
        title = body.title.strip() if body.title else None

        if body.categories:
            # Validate categories
            invalid = [c for c in body.categories if c not in ARXIV_FEEDS]
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid categories: {', '.join(invalid)}"
                )
            categories = body.categories

        if body.max_results:
            max_results = min(body.max_results, 500)  # Cap at 500

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
@limiter.limit(f"{settings.rate_limit_requests}/minute")
def fetch_semantic_scholar(request: Request, body: SemanticScholarFetchRequest):
    """Fetch papers from Semantic Scholar by search query.

    Args:
        body: Search parameters including query, limit, year filter,
              and minimum citation count.
    """
    from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    try:
        fetcher = SemanticScholarFetcher()

        # Fetch papers
        articles = fetcher.fetch(
            query=body.query.strip(),
            limit=min(body.limit or 50, 100),  # Cap at 100
            year=body.year,
            min_citations=body.min_citations,
        )

        # Store in database
        new_count = fetcher.store_articles(articles)
        fetcher.close()

        return FetchResponse(
            success=True,
            new_articles=new_count,
            message=f"Fetched {new_count} new papers from Semantic Scholar for '{body.query}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=FetchResponse)
@limiter.limit(f"{settings.rate_limit_process}/minute")
def process_unprocessed(request: Request):
    """Process unprocessed articles with LLM to extract topics/summaries."""
    from mindscout.processors.content import ContentProcessor

    try:
        processor = ContentProcessor()
        processed, failed = processor.process_batch(limit=50)

        return FetchResponse(
            success=True,
            new_articles=processed,
            message=f"Processed {processed} articles ({failed} failed)"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-daily-job", response_model=FetchResponse)
@limiter.limit(f"{settings.rate_limit_process}/minute")
async def run_daily_job(request: Request):
    """Manually trigger the daily fetch & process job.

    This runs the same job that the scheduler runs daily:
    - Fetches RSS feeds
    - Fetches arXiv papers based on user interests
    - Fetches Semantic Scholar papers based on user interests
    - Processes up to 50 new articles with LLM
    """
    from backend.scheduler.jobs import fetch_and_process_job

    try:
        results = await fetch_and_process_job()
        total = (
            results["rss"]["articles"]
            + results["arxiv"]["articles"]
            + results["semanticscholar"]["articles"]
        )

        return FetchResponse(
            success=True,
            new_articles=total,
            message=(
                f"Fetched {total} articles "
                f"(RSS: {results['rss']['articles']}, "
                f"arXiv: {results['arxiv']['articles']}, "
                f"S2: {results['semanticscholar']['articles']}), "
                f"processed {results['processed']} ({results['failed']} failed)"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
