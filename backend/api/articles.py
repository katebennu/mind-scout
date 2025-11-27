"""Articles API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from mindscout.database import get_session, Article

router = APIRouter()


# Pydantic models for request/response
class ArticleResponse(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    abstract: Optional[str]
    url: str
    source: str
    source_name: Optional[str]
    published_date: Optional[datetime]
    fetched_date: datetime
    categories: Optional[str]
    is_read: bool
    rating: Optional[int]
    citation_count: Optional[int]
    has_implementation: bool
    github_url: Optional[str]
    topics: Optional[str]
    summary: Optional[str]

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    page: int
    page_size: int


class MarkReadRequest(BaseModel):
    is_read: bool


class RateArticleRequest(BaseModel):
    rating: int  # 1-5


@router.get("", response_model=ArticleListResponse)
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    source: Optional[str] = None,
    sort_by: str = Query("fetched_date", regex="^(fetched_date|published_date|rating)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """List articles with pagination and filters."""
    session = get_session()

    try:
        # Base query
        query = session.query(Article)

        # Apply filters
        if unread_only:
            query = query.filter(Article.is_read == False)

        if source:
            query = query.filter(Article.source == source)

        # Count total before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Article, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        articles = query.offset(offset).limit(page_size).all()

        return ArticleListResponse(
            articles=[ArticleResponse.model_validate(a) for a in articles],
            total=total,
            page=page,
            page_size=page_size
        )

    finally:
        session.close()


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int):
    """Get a single article by ID."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return ArticleResponse.model_validate(article)

    finally:
        session.close()


@router.post("/{article_id}/read")
def mark_read(article_id: int, request: MarkReadRequest):
    """Mark article as read or unread."""
    session = get_session()

    try:
        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article.is_read = request.is_read
        session.commit()

        return {"success": True, "is_read": article.is_read}

    finally:
        session.close()


@router.post("/{article_id}/rate")
def rate_article(article_id: int, request: RateArticleRequest):
    """Rate an article (1-5 stars)."""
    session = get_session()

    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        article = session.query(Article).filter_by(id=article_id).first()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article.rating = request.rating
        article.rated_date = datetime.utcnow()
        article.is_read = True  # Auto-mark as read when rated
        session.commit()

        return {"success": True, "rating": article.rating}

    finally:
        session.close()
