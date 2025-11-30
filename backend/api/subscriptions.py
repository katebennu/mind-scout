"""RSS subscription API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mindscout.config import CURATED_FEEDS
from mindscout.database import RSSFeed, get_session

router = APIRouter()


class SubscriptionCreate(BaseModel):
    url: str
    title: Optional[str] = None
    category: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    check_interval: Optional[int] = None


class SubscriptionResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    category: Optional[str]
    is_active: bool
    check_interval: int
    last_checked: Optional[datetime]
    created_date: datetime

    class Config:
        from_attributes = True


class CuratedFeedResponse(BaseModel):
    url: str
    title: str
    category: str
    description: str


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions():
    """List all RSS feed subscriptions."""
    session = get_session()

    try:
        feeds = session.query(RSSFeed).order_by(RSSFeed.created_date.desc()).all()
        return [SubscriptionResponse.model_validate(feed) for feed in feeds]

    finally:
        session.close()


@router.get("/curated", response_model=list[CuratedFeedResponse])
def list_curated_feeds():
    """Get list of curated/suggested RSS feeds."""
    return [
        CuratedFeedResponse(
            url=feed["url"],
            title=feed["title"],
            category=feed["category"],
            description=feed["description"],
        )
        for feed in CURATED_FEEDS
    ]


@router.post("", response_model=SubscriptionResponse)
def create_subscription(request: SubscriptionCreate):
    """Subscribe to a new RSS feed."""
    import feedparser

    session = get_session()

    try:
        # Check if already subscribed
        existing = session.query(RSSFeed).filter(RSSFeed.url == request.url).first()
        if existing:
            raise HTTPException(status_code=400, detail="Already subscribed to this feed")

        # Validate the feed URL by fetching it
        feed = feedparser.parse(request.url)
        if feed.bozo and not feed.entries:
            raise HTTPException(status_code=400, detail="Invalid RSS feed URL or feed is empty")

        # Get title from feed if not provided
        title = request.title
        if not title and feed.feed.get("title"):
            title = feed.feed.title

        # Create subscription
        subscription = RSSFeed(
            url=request.url,
            title=title,
            category=request.category,
            is_active=True,
            check_interval=60,
        )

        session.add(subscription)
        session.commit()
        session.refresh(subscription)

        return SubscriptionResponse.model_validate(subscription)

    finally:
        session.close()


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(subscription_id: int):
    """Get a specific subscription."""
    session = get_session()

    try:
        subscription = session.query(RSSFeed).filter(RSSFeed.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        return SubscriptionResponse.model_validate(subscription)

    finally:
        session.close()


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(subscription_id: int, request: SubscriptionUpdate):
    """Update a subscription."""
    session = get_session()

    try:
        subscription = session.query(RSSFeed).filter(RSSFeed.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        if request.title is not None:
            subscription.title = request.title
        if request.category is not None:
            subscription.category = request.category
        if request.is_active is not None:
            subscription.is_active = request.is_active
        if request.check_interval is not None:
            subscription.check_interval = request.check_interval

        session.commit()
        session.refresh(subscription)

        return SubscriptionResponse.model_validate(subscription)

    finally:
        session.close()


@router.delete("/{subscription_id}")
def delete_subscription(subscription_id: int):
    """Unsubscribe from a feed."""
    session = get_session()

    try:
        subscription = session.query(RSSFeed).filter(RSSFeed.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        session.delete(subscription)
        session.commit()

        return {"success": True, "message": "Subscription deleted"}

    finally:
        session.close()


@router.post("/{subscription_id}/refresh")
def refresh_subscription(subscription_id: int):
    """Manually refresh a subscription and fetch new articles.

    Note: Notifications are created by the content processor when articles
    match user interests, not during feed refresh.
    """
    from mindscout.fetchers.rss import RSSFetcher

    session = get_session()

    try:
        subscription = session.query(RSSFeed).filter(RSSFeed.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        # Fetch new articles
        fetcher = RSSFetcher()
        result = fetcher.fetch_feed(subscription)

        return {
            "success": True,
            "new_articles": result["new_count"],
        }

    finally:
        session.close()


@router.post("/refresh-all")
def refresh_all_subscriptions():
    """Refresh all active subscriptions.

    Note: Notifications are created by the content processor when articles
    match user interests, not during feed refresh.
    """
    from mindscout.fetchers.rss import RSSFetcher

    session = get_session()

    try:
        feeds = session.query(RSSFeed).filter(RSSFeed.is_active).all()

        fetcher = RSSFetcher()
        total_new = 0

        for feed in feeds:
            result = fetcher.fetch_feed(feed)
            total_new += result["new_count"]

        return {
            "success": True,
            "feeds_checked": len(feeds),
            "new_articles": total_new,
        }

    finally:
        session.close()
