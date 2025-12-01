"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-30

Creates all tables for Mind Scout:
- articles: Research papers and articles from various sources
- user_profile: User preferences and settings
- rss_feeds: RSS feed subscriptions
- pending_batches: Tracks async LLM processing batches
- notifications: User notifications for new articles
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    # Articles table
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("source", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("authors", sa.Text(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("published_date", sa.DateTime(), nullable=True),
        sa.Column("fetched_date", sa.DateTime(), nullable=True),
        sa.Column("categories", sa.String(500), nullable=True),
        sa.Column("is_read", sa.Boolean(), default=False),
        # Phase 2: Content Processing fields
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("topics", sa.Text(), nullable=True),
        sa.Column("processed", sa.Boolean(), default=False),
        sa.Column("processing_date", sa.DateTime(), nullable=True),
        # Phase 3: Multi-Source metadata
        sa.Column("citation_count", sa.Integer(), nullable=True),
        sa.Column("influential_citations", sa.Integer(), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("has_implementation", sa.Boolean(), default=False),
        sa.Column("paper_url_pwc", sa.String(500), nullable=True),
        sa.Column("hf_upvotes", sa.Integer(), nullable=True),
        # Phase 4: User feedback
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("rated_date", sa.DateTime(), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
    )

    # User profile table
    op.create_table(
        "user_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("interests", sa.Text(), nullable=True),
        sa.Column("skill_level", sa.String(50), nullable=True),
        sa.Column("preferred_sources", sa.Text(), nullable=True),
        sa.Column("daily_reading_goal", sa.Integer(), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.Column("updated_date", sa.DateTime(), nullable=True),
    )

    # RSS feeds table
    op.create_table(
        "rss_feeds",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("url", sa.String(1000), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("check_interval", sa.Integer(), default=60),
        sa.Column("last_checked", sa.DateTime(), nullable=True),
        sa.Column("last_etag", sa.String(200), nullable=True),
        sa.Column("last_modified", sa.String(200), nullable=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
    )

    # Pending batches table
    op.create_table(
        "pending_batches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("article_count", sa.Integer(), default=0),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.Column("completed_date", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # Notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "article_id", sa.Integer(), sa.ForeignKey("articles.id"), nullable=False, index=True
        ),
        sa.Column(
            "feed_id", sa.Integer(), sa.ForeignKey("rss_feeds.id"), nullable=True, index=True
        ),
        sa.Column("type", sa.String(50), default="new_article"),
        sa.Column("is_read", sa.Boolean(), default=False, index=True),
        sa.Column("created_date", sa.DateTime(), nullable=True),
        sa.Column("read_date", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("notifications")
    op.drop_table("pending_batches")
    op.drop_table("rss_feeds")
    op.drop_table("user_profile")
    op.drop_table("articles")
