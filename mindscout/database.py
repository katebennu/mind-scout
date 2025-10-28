"""Database models and operations for Mind Scout."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from mindscout.config import DB_PATH

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
    # Vector embedding (JSON array stored as text)
    embedding = Column(Text)
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

    def __repr__(self):
        return f"<Article {self.source_id}: {self.title[:50]}>"


# Database engine and session
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)


def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    return Session()
