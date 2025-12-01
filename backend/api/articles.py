"""Articles API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mindscout.config import get_settings
from mindscout.database import Article, get_async_db

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

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
    articles: list[ArticleResponse]
    total: int
    page: int
    page_size: int


class MarkReadRequest(BaseModel):
    is_read: bool


class RateArticleRequest(BaseModel):
    rating: int  # 1-5


@router.get("/sources")
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def list_sources(request: Request, db: AsyncSession = Depends(get_async_db)):
    """Get list of distinct source names for filtering."""
    stmt = (
        select(Article.source, Article.source_name, func.count(Article.id).label("count"))
        .group_by(Article.source, Article.source_name)
        .order_by(func.count(Article.id).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {"source": r.source, "source_name": r.source_name or r.source, "count": r.count}
        for r in rows
    ]


@router.get("", response_model=ArticleListResponse)
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def list_articles(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    source: Optional[str] = None,
    source_name: Optional[str] = None,
    sort_by: str = Query("fetched_date", pattern="^(fetched_date|published_date|rating)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """List articles with pagination and filters."""
    # Build base query
    stmt = select(Article)

    # Apply filters
    if unread_only:
        stmt = stmt.where(Article.is_read.is_(False))

    if source:
        stmt = stmt.where(Article.source == source)

    if source_name:
        stmt = stmt.where(Article.source_name == source_name)

    # Count total before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply sorting based on sort_by parameter
    if sort_by == "rating":
        # Sort by rating (nulls last for desc)
        if sort_order == "desc":
            stmt = stmt.order_by(Article.rating.desc().nullslast(), Article.id.desc())
        else:
            stmt = stmt.order_by(Article.rating.asc().nullsfirst(), Article.id.asc())
    else:
        # Default: sort by fetched_date, then published_date
        if sort_order == "desc":
            stmt = stmt.order_by(
                Article.fetched_date.desc().nullslast(),
                Article.published_date.desc().nullslast(),
                Article.id.desc(),
            )
        else:
            stmt = stmt.order_by(
                Article.fetched_date.asc().nullsfirst(),
                Article.published_date.asc().nullsfirst(),
                Article.id.asc(),
            )

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    articles = result.scalars().all()

    return ArticleListResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def get_article(request: Request, article_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get a single article by ID."""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleResponse.model_validate(article)


@router.post("/{article_id}/read")
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def mark_read(
    request: Request,
    article_id: int,
    body: MarkReadRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Mark article as read or unread."""
    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_read = body.is_read
    await db.commit()

    return {"success": True, "is_read": article.is_read}


@router.post("/{article_id}/rate")
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def rate_article(
    request: Request,
    article_id: int,
    body: RateArticleRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Rate an article (1-5 stars)."""
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    stmt = select(Article).where(Article.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.rating = body.rating
    article.rated_date = datetime.utcnow()
    article.is_read = True  # Auto-mark as read when rated
    await db.commit()

    return {"success": True, "rating": article.rating}
