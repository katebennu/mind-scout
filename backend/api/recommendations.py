"""Recommendations API endpoints."""

from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from mindscout.recommender import RecommendationEngine
from backend.api.articles import ArticleResponse

router = APIRouter()


class RecommendationResponse(BaseModel):
    article: ArticleResponse
    score: float
    reasons: List[str]


@router.get("", response_model=List[RecommendationResponse])
def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    days_back: int = Query(30, ge=1, le=365),
    min_score: float = Query(0.1, ge=0.0, le=1.0)
):
    """Get personalized recommendations."""
    engine = RecommendationEngine()

    try:
        recommendations = engine.get_recommendations(
            limit=limit,
            days_back=days_back,
            min_score=min_score,
            unread_only=True
        )

        return [
            RecommendationResponse(
                article=ArticleResponse.model_validate(rec["article"]),
                score=rec["score"],
                reasons=rec["reasons"]
            )
            for rec in recommendations
        ]

    finally:
        engine.close()


@router.get("/{article_id}/similar", response_model=List[RecommendationResponse])
def get_similar_articles(
    article_id: int,
    limit: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0)
):
    """Get articles similar to a given article."""
    from mindscout.vectorstore import VectorStore

    vector_store = VectorStore()

    try:
        similar = vector_store.find_similar(
            article_id=article_id,
            n_results=limit,
            min_similarity=min_similarity
        )

        return [
            RecommendationResponse(
                article=ArticleResponse.model_validate(sim["article"]),
                score=sim["similarity"],
                reasons=[f"{sim['similarity']:.0%} similar"]
            )
            for sim in similar
        ]

    finally:
        vector_store.close()


@router.get("/semantic", response_model=List[RecommendationResponse])
def semantic_recommendations(
    limit: int = Query(10, ge=1, le=50),
    use_interests: bool = True,
    use_reading_history: bool = True
):
    """Get semantic recommendations based on interests and reading history."""
    engine = RecommendationEngine()

    try:
        recommendations = engine.get_semantic_recommendations(
            limit=limit,
            use_interests=use_interests,
            use_reading_history=use_reading_history
        )

        return [
            RecommendationResponse(
                article=ArticleResponse.model_validate(rec["article"]),
                score=rec["score"],
                reasons=rec["reasons"]
            )
            for rec in recommendations
        ]

    finally:
        engine.close()
