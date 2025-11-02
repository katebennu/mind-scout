"""Search API endpoints."""

from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from mindscout.vectorstore import VectorStore
from backend.api.articles import ArticleResponse

router = APIRouter()


class SearchResult(BaseModel):
    article: ArticleResponse
    relevance: float


@router.get("", response_model=List[SearchResult])
def semantic_search(
    q: str = Query(..., min_length=3, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """Perform semantic search for articles."""
    vector_store = VectorStore()

    try:
        results = vector_store.semantic_search(
            query=q,
            n_results=limit
        )

        return [
            SearchResult(
                article=ArticleResponse.from_orm(result["article"]),
                relevance=result["relevance"]
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
