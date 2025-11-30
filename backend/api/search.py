"""Search API endpoints."""

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.api.articles import ArticleResponse
from mindscout.config import get_settings
from mindscout.vectorstore import VectorStore

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


class SearchResult(BaseModel):
    article: ArticleResponse
    relevance: float


@router.get("", response_model=list[SearchResult])
@limiter.limit(f"{settings.rate_limit_requests}/minute")
def semantic_search(
    request: Request,
    q: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Perform semantic search for articles."""
    vector_store = VectorStore()

    try:
        results = vector_store.semantic_search(query=q, n_results=limit)

        return [
            SearchResult(
                article=ArticleResponse.model_validate(result["article"]),
                relevance=result["relevance"],
            )
            for result in results
        ]

    finally:
        vector_store.close()


@router.get("/stats")
def get_search_stats():
    """Get vector store statistics."""
    vector_store = VectorStore()

    try:
        stats = vector_store.get_collection_stats()
        return stats

    finally:
        vector_store.close()
