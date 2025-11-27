"""Notification API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mindscout.database import get_session, Notification, Article, RSSFeed

router = APIRouter()


class ArticleSummary(BaseModel):
    id: int
    title: str
    source: str
    url: str
    published_date: Optional[datetime]

    class Config:
        from_attributes = True


class FeedSummary(BaseModel):
    id: int
    title: Optional[str]
    url: str

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    article: ArticleSummary
    feed: Optional[FeedSummary]
    type: str
    is_read: bool
    created_date: datetime
    read_date: Optional[datetime]


class NotificationCountResponse(BaseModel):
    unread: int
    total: int


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """List notifications, newest first."""
    session = get_session()

    try:
        query = session.query(Notification).order_by(Notification.created_date.desc())

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = query.offset(offset).limit(limit).all()

        results = []
        for notif in notifications:
            article = session.query(Article).filter(Article.id == notif.article_id).first()
            feed = session.query(RSSFeed).filter(RSSFeed.id == notif.feed_id).first() if notif.feed_id else None

            if article:
                results.append(NotificationResponse(
                    id=notif.id,
                    article=ArticleSummary(
                        id=article.id,
                        title=article.title,
                        source=article.source,
                        url=article.url,
                        published_date=article.published_date
                    ),
                    feed=FeedSummary(
                        id=feed.id,
                        title=feed.title,
                        url=feed.url
                    ) if feed else None,
                    type=notif.type,
                    is_read=notif.is_read,
                    created_date=notif.created_date,
                    read_date=notif.read_date
                ))

        return results

    finally:
        session.close()


@router.get("/count", response_model=NotificationCountResponse)
def get_notification_count():
    """Get count of unread and total notifications."""
    session = get_session()

    try:
        unread = session.query(Notification).filter(Notification.is_read == False).count()
        total = session.query(Notification).count()

        return NotificationCountResponse(unread=unread, total=total)

    finally:
        session.close()


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int):
    """Mark a notification as read."""
    session = get_session()

    try:
        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.is_read = True
        notification.read_date = datetime.utcnow()
        session.commit()

        return {"success": True, "is_read": True}

    finally:
        session.close()


@router.post("/read-all")
def mark_all_notifications_read():
    """Mark all notifications as read."""
    session = get_session()

    try:
        session.query(Notification).filter(
            Notification.is_read == False
        ).update({
            Notification.is_read: True,
            Notification.read_date: datetime.utcnow()
        })
        session.commit()

        return {"success": True, "message": "All notifications marked as read"}

    finally:
        session.close()


@router.delete("/{notification_id}")
def delete_notification(notification_id: int):
    """Delete a notification."""
    session = get_session()

    try:
        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        session.delete(notification)
        session.commit()

        return {"success": True, "message": "Notification deleted"}

    finally:
        session.close()


@router.delete("")
def clear_all_notifications(read_only: bool = True):
    """Clear notifications. By default, only clears read notifications."""
    session = get_session()

    try:
        query = session.query(Notification)
        if read_only:
            query = query.filter(Notification.is_read == True)

        deleted_count = query.delete()
        session.commit()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} notifications"
        }

    finally:
        session.close()
