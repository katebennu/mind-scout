"""Database models and operations for Mind Scout."""

from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from mindscout.config import get_settings

settings = get_settings()
Base = declarative_base()


class Article(Base):
    """Represents an article/paper from various sources."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    # Unique identifier from source (e.g., arXiv ID)
    source_id = Column(String, unique=True, nullable=False, index=True)
    # Source platform (arxiv, twitter, huggingface, etc.)
    source = Column(String, nullable=False, index=True)
    # Article title
    title = Column(String, nullable=False)
    # Authors
    authors = Column(Text)
    # Abstract/summary
    abstract = Column(Text)
    # Link to article
    url = Column(String, nullable=False)
    # Publication/posted date
    published_date = Column(DateTime)
    # When we fetched it
    fetched_date = Column(DateTime, default=datetime.utcnow)
    # Category/tags (comma-separated for now)
    categories = Column(String)
    # Whether user has read it
    is_read = Column(Boolean, default=False)

    # Phase 2: Content Processing fields
    # LLM-generated summary (shorter than abstract)
    summary = Column(Text)
    # Extracted topics/keywords (JSON array stored as text)
    topics = Column(Text)
    # Whether article has been processed
    processed = Column(Boolean, default=False)
    # When article was processed
    processing_date = Column(DateTime)

    # Phase 3: Multi-Source metadata
    # Citation metrics (from Semantic Scholar)
    citation_count = Column(Integer)
    influential_citations = Column(Integer)
    # Implementation links (from Papers with Code)
    github_url = Column(String)
    has_implementation = Column(Boolean, default=False)
    paper_url_pwc = Column(String)  # Papers with Code URL
    # Community engagement (from Hugging Face)
    hf_upvotes = Column(Integer)

    # Phase 4: User feedback and recommendations
    rating = Column(Integer)  # 1-5 star rating, null if not rated
    rated_date = Column(DateTime)  # When user rated this article

    # Human-readable source name (e.g., "arXiv cs.AI", "Lex Fridman Podcast")
    source_name = Column(String)

    def __repr__(self):
        return f"<Article {self.source_id}: {self.title[:50]}>"


class UserProfile(Base):
    """User profile for personalized recommendations."""

    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True)
    # User preferences
    interests = Column(Text)  # Comma-separated topics of interest
    skill_level = Column(String)  # beginner, intermediate, advanced
    preferred_sources = Column(Text)  # Comma-separated source preferences
    # Reading behavior
    daily_reading_goal = Column(Integer)  # Papers per day
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserProfile skill_level={self.skill_level}>"


class RSSFeed(Base):
    """RSS feed subscription."""

    __tablename__ = "rss_feeds"

    id = Column(Integer, primary_key=True)
    # Feed URL (unique constraint)
    url = Column(String, unique=True, nullable=False, index=True)
    # Feed title (fetched from feed or user-provided)
    title = Column(String)
    # Category for organization (e.g., "tech_blog", "podcast", "news")
    category = Column(String)
    # Whether the feed is actively being checked
    is_active = Column(Boolean, default=True)
    # How often to check (in minutes) - for future background polling
    check_interval = Column(Integer, default=60)
    # Last time feed was checked
    last_checked = Column(DateTime)
    # ETag for efficient HTTP caching
    last_etag = Column(String)
    # Last-Modified header value
    last_modified = Column(String)
    # Metadata
    created_date = Column(DateTime, default=datetime.utcnow)

    # Relationship to notifications
    notifications = relationship("Notification", back_populates="feed")

    def __repr__(self):
        return f"<RSSFeed {self.title or self.url}>"


class PendingBatch(Base):
    """Tracks pending async LLM batches for processing."""

    __tablename__ = "pending_batches"

    id = Column(Integer, primary_key=True)
    # Anthropic batch ID
    batch_id = Column(String, unique=True, nullable=False, index=True)
    # Number of articles in the batch
    article_count = Column(Integer, default=0)
    # Status: pending, processing, completed, failed
    status = Column(String, default="pending")
    # When batch was created
    created_date = Column(DateTime, default=datetime.utcnow)
    # When batch was completed/applied
    completed_date = Column(DateTime)
    # Error message if failed
    error_message = Column(Text)

    def __repr__(self):
        return f"<PendingBatch {self.batch_id} status={self.status}>"


class Notification(Base):
    """User notification for new articles from subscriptions."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    # Link to the article that triggered this notification
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    # Link to the feed this came from
    feed_id = Column(Integer, ForeignKey("rss_feeds.id"), index=True)
    # Type of notification
    type = Column(String, default="new_article")  # new_article, interest_match
    # Whether user has seen/dismissed this notification
    is_read = Column(Boolean, default=False, index=True)
    # When notification was created
    created_date = Column(DateTime, default=datetime.utcnow)
    # When user read/dismissed it
    read_date = Column(DateTime)

    # Relationships
    article = relationship("Article")
    feed = relationship("RSSFeed", back_populates="notifications")

    def __repr__(self):
        return f"<Notification article_id={self.article_id} read={self.is_read}>"


# Synchronous database engine and session (for existing code)
engine = create_engine(settings.effective_database_url)
Session = sessionmaker(bind=engine)

# Async database engine and session (for FastAPI endpoints)
# SQLite async requires aiosqlite: pip install aiosqlite
_async_db_url = settings.effective_database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
async_engine = create_async_engine(_async_db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(engine)


async def init_async_db():
    """Initialize the database schema asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session():
    """Get a database session.

    Note: Prefer using get_db_session() context manager for automatic cleanup.
    This function is kept for backward compatibility.
    """
    return Session()


@contextmanager
def get_db_session():
    """Context manager for database sessions.

    Automatically handles commit on success and rollback on error.

    Usage:
        with get_db_session() as session:
            session.query(Article).all()
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions.

    Automatically handles commit on success and rollback on error.

    Usage:
        async with get_async_db_session() as session:
            result = await session.execute(select(Article))
            articles = result.scalars().all()
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions.

    Usage in FastAPI:
        @router.get("/articles")
        async def get_articles(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Article))
            return result.scalars().all()
    """
    async with get_async_db_session() as session:
        yield session
