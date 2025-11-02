"""Profile API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from mindscout.profile import ProfileManager

router = APIRouter()


class ProfileResponse(BaseModel):
    interests: List[str]
    skill_level: str
    preferred_sources: List[str]
    daily_reading_goal: int
    created_date: Optional[datetime]
    updated_date: Optional[datetime]


class UpdateProfileRequest(BaseModel):
    interests: Optional[List[str]] = None
    skill_level: Optional[str] = None
    preferred_sources: Optional[List[str]] = None
    daily_reading_goal: Optional[int] = None


class StatsResponse(BaseModel):
    total_articles: int
    read_articles: int
    unread_articles: int
    read_percentage: float
    rated_articles: int
    average_rating: Optional[float]
    articles_by_source: dict
    recent_activity: dict


@router.get("", response_model=ProfileResponse)
def get_profile():
    """Get user profile."""
    manager = ProfileManager()

    try:
        profile = manager.get_or_create_profile()
        interests = manager.get_interests()
        sources = manager.get_preferred_sources()

        return ProfileResponse(
            interests=interests,
            skill_level=profile.skill_level or "intermediate",
            preferred_sources=sources,
            daily_reading_goal=profile.daily_reading_goal or 5,
            created_date=profile.created_date,
            updated_date=profile.updated_date
        )

    finally:
        manager.close()


@router.put("", response_model=ProfileResponse)
def update_profile(request: UpdateProfileRequest):
    """Update user profile."""
    manager = ProfileManager()

    try:
        if request.interests is not None:
            manager.set_interests(request.interests)

        if request.skill_level is not None:
            manager.set_skill_level(request.skill_level)

        if request.preferred_sources is not None:
            manager.set_preferred_sources(request.preferred_sources)

        if request.daily_reading_goal is not None:
            manager.set_daily_reading_goal(request.daily_reading_goal)

        # Return updated profile
        profile = manager.get_or_create_profile()
        interests = manager.get_interests()
        sources = manager.get_preferred_sources()

        return ProfileResponse(
            interests=interests,
            skill_level=profile.skill_level or "intermediate",
            preferred_sources=sources,
            daily_reading_goal=profile.daily_reading_goal or 5,
            created_date=profile.created_date,
            updated_date=profile.updated_date
        )

    finally:
        manager.close()


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get reading statistics."""
    from mindscout.database import get_session, Article
    from sqlalchemy import func

    session = get_session()

    try:
        # Total articles
        total = session.query(Article).count()

        # Read/unread counts
        read_count = session.query(Article).filter(Article.is_read == True).count()
        unread_count = total - read_count
        read_pct = (read_count / total * 100) if total > 0 else 0

        # Rated articles
        rated_count = session.query(Article).filter(Article.rating.isnot(None)).count()

        # Average rating
        avg_rating = session.query(func.avg(Article.rating)).filter(
            Article.rating.isnot(None)
        ).scalar()

        # Articles by source
        by_source = {}
        source_counts = session.query(
            Article.source,
            func.count(Article.id)
        ).group_by(Article.source).all()

        for source, count in source_counts:
            by_source[source] = count

        # Recent activity (last 7 days)
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)

        recent_fetched = session.query(Article).filter(
            Article.fetched_date >= recent_date
        ).count()

        recent_read = session.query(Article).filter(
            Article.is_read == True,
            Article.fetched_date >= recent_date
        ).count()

        return StatsResponse(
            total_articles=total,
            read_articles=read_count,
            unread_articles=unread_count,
            read_percentage=round(read_pct, 1),
            rated_articles=rated_count,
            average_rating=round(avg_rating, 2) if avg_rating else None,
            articles_by_source=by_source,
            recent_activity={
                "fetched_last_7_days": recent_fetched,
                "read_last_7_days": recent_read
            }
        )

    finally:
        session.close()
