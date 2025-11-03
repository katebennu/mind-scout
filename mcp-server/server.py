#!/usr/bin/env python3
"""Mind Scout MCP Server

Provides AI assistants with tools to interact with the Mind Scout research library.

This MCP server enables Claude Desktop (and other MCP-compatible AI assistants) to:
- Search your research library with semantic search
- Fetch new papers from arXiv and Semantic Scholar
- Get personalized recommendations
- Rate and track reading progress
- Manage your profile and interests

Tools (9 total):

Search & Discovery:
- search_papers: Semantic search through research papers using natural language
- get_recommendations: Get personalized paper recommendations based on interests
- fetch_articles: Fetch new papers from arXiv or Semantic Scholar and add to library

Library Management:
- list_articles: Browse articles with pagination and filters (unread, source, sort)
- get_article: Retrieve detailed information about a specific article

Reading & Rating:
- rate_article: Rate a paper from 1-5 stars
- mark_article_read: Mark paper as read or unread

Profile & Settings:
- get_profile: View user profile, interests, and comprehensive reading statistics
- update_interests: Update research interests to improve recommendations

Usage:
    Once installed in Claude Desktop, simply ask questions like:
    - "Fetch new transformer papers from arXiv"
    - "Search my library for papers about diffusion models"
    - "What are my top 5 recommendations?"
    - "Show my reading statistics"
"""

import sys
from pathlib import Path
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

# Add parent directory to path to import mindscout modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from mindscout.database import get_session, Article, UserProfile
from mindscout.vectorstore import VectorStore
from mindscout.recommender import RecommendationEngine
from mindscout.fetchers.arxiv import fetch_arxiv
from mindscout.fetchers.semanticscholar import SemanticScholarFetcher

# Initialize MCP server
mcp = FastMCP("Mind Scout")


@mcp.tool()
def search_papers(query: str, limit: int = 10) -> list[dict]:
    """Search research papers using semantic search with natural language queries.

    Args:
        query: Natural language search query (e.g., "attention mechanisms in transformers")
        limit: Maximum number of results to return (default: 10)

    Returns:
        List of papers with relevance scores, sorted by relevance
    """
    vector_store = VectorStore()

    try:
        # Perform semantic search
        results = vector_store.semantic_search(query=query, n_results=limit)

        papers = []
        for result in results:
            article = result["article"]
            papers.append({
                "id": article.id,
                "title": article.title,
                "authors": article.authors,
                "abstract": article.abstract,
                "url": article.url,
                "source": article.source,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "citation_count": article.citation_count,
                "relevance_score": round(result["relevance"] * 100, 1),
                "is_read": article.is_read,
                "rating": article.rating
            })

        return papers

    finally:
        vector_store.close()


@mcp.tool()
def get_recommendations(limit: int = 10) -> list[dict]:
    """Get personalized paper recommendations based on your interests and reading history.

    Args:
        limit: Maximum number of recommendations (default: 10)

    Returns:
        List of recommended papers with match scores and reasons
    """
    engine = RecommendationEngine()

    try:
        # Get recommendations
        recommendations = engine.get_recommendations(limit=limit, unread_only=True)

        results = []
        for rec in recommendations:
            article = rec["article"]
            results.append({
                "id": article.id,
                "title": article.title,
                "authors": article.authors,
                "abstract": article.abstract,
                "url": article.url,
                "source": article.source,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "citation_count": article.citation_count,
                "match_score": round(rec["score"] * 100, 1),
                "reasons": rec["reasons"],
                "is_read": article.is_read,
                "rating": article.rating
            })

        return results

    finally:
        engine.close()


@mcp.tool()
def get_article(article_id: int) -> dict:
    """Get detailed information about a specific article.

    Args:
        article_id: The unique ID of the article

    Returns:
        Complete article details including metadata and reading status
    """
    session = get_session()

    try:
        article = session.query(Article).filter(Article.id == article_id).first()

        if not article:
            return {"error": f"Article {article_id} not found"}

        return {
            "id": article.id,
            "title": article.title,
            "authors": article.authors,
            "abstract": article.abstract,
            "url": article.url,
            "source": article.source,
            "source_id": article.source_id,
            "published_date": article.published_date.isoformat() if article.published_date else None,
            "citation_count": article.citation_count,
            "is_read": article.is_read,
            "rating": article.rating,
            "fetched_date": article.fetched_date.isoformat() if article.fetched_date else None
        }

    finally:
        session.close()


@mcp.tool()
def list_articles(
    page: int = 1,
    page_size: int = 10,
    unread_only: bool = False,
    source: Optional[str] = None,
    sort_by: Literal["recent", "rating", "citations"] = "recent"
) -> dict:
    """Browse articles in the library with filtering and pagination.

    Args:
        page: Page number (1-indexed, default: 1)
        page_size: Articles per page (default: 10)
        unread_only: Show only unread articles (default: False)
        source: Filter by source (e.g., "arxiv", "semanticscholar")
        sort_by: Sort order - "recent", "rating", or "citations" (default: "recent")

    Returns:
        Paginated list of articles with total count
    """
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
        if sort_by == "rating":
            query = query.order_by(Article.rating.desc().nullslast(), Article.fetched_date.desc())
        elif sort_by == "citations":
            query = query.order_by(Article.citation_count.desc().nullslast(), Article.fetched_date.desc())
        else:  # recent
            query = query.order_by(Article.fetched_date.desc())

        # Apply pagination
        offset = (page - 1) * page_size
        articles = query.offset(offset).limit(page_size).all()

        return {
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "authors": a.authors,
                    "abstract": a.abstract[:200] + "..." if a.abstract and len(a.abstract) > 200 else a.abstract,
                    "url": a.url,
                    "source": a.source,
                    "published_date": a.published_date.isoformat() if a.published_date else None,
                    "citation_count": a.citation_count,
                    "is_read": a.is_read,
                    "rating": a.rating
                }
                for a in articles
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    finally:
        session.close()


@mcp.tool()
def rate_article(article_id: int, rating: int) -> dict:
    """Rate a research paper from 1 to 5 stars.

    Args:
        article_id: The unique ID of the article
        rating: Rating from 1 (poor) to 5 (excellent)

    Returns:
        Success status and updated article info
    """
    if not 1 <= rating <= 5:
        return {"error": "Rating must be between 1 and 5"}

    session = get_session()

    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"error": f"Article {article_id} not found"}

        article.rating = rating
        session.commit()

        return {
            "success": True,
            "article_id": article_id,
            "title": article.title,
            "rating": rating,
            "message": f"Rated '{article.title}' {rating} stars"
        }

    finally:
        session.close()


@mcp.tool()
def mark_article_read(article_id: int, is_read: bool = True) -> dict:
    """Mark a paper as read or unread.

    Args:
        article_id: The unique ID of the article
        is_read: True to mark as read, False to mark as unread (default: True)

    Returns:
        Success status and updated article info
    """
    session = get_session()

    try:
        article = session.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"error": f"Article {article_id} not found"}

        article.is_read = is_read
        session.commit()

        status = "read" if is_read else "unread"
        return {
            "success": True,
            "article_id": article_id,
            "title": article.title,
            "is_read": is_read,
            "message": f"Marked '{article.title}' as {status}"
        }

    finally:
        session.close()


@mcp.tool()
def get_profile() -> dict:
    """View user profile, interests, and reading statistics.

    Returns:
        Profile information and comprehensive reading statistics
    """
    session = get_session()

    try:
        # Get or create profile
        profile = session.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                interests=[],
                skill_level="intermediate",
                preferred_sources=[],
                daily_reading_goal=5
            )

        # Calculate statistics
        all_articles = session.query(Article).all()
        total_articles = len(all_articles)
        read_articles = len([a for a in all_articles if a.is_read])
        rated_articles = len([a for a in all_articles if a.rating is not None])

        ratings = [a.rating for a in all_articles if a.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        # Articles by source
        sources = {}
        for article in all_articles:
            sources[article.source] = sources.get(article.source, 0) + 1

        return {
            "interests": profile.interests or [],
            "skill_level": profile.skill_level,
            "preferred_sources": profile.preferred_sources or [],
            "daily_reading_goal": profile.daily_reading_goal,
            "statistics": {
                "total_articles": total_articles,
                "read_articles": read_articles,
                "read_percentage": round(read_articles / total_articles * 100, 1) if total_articles > 0 else 0,
                "rated_articles": rated_articles,
                "average_rating": round(avg_rating, 1) if avg_rating else None,
                "articles_by_source": sources
            }
        }

    finally:
        session.close()


@mcp.tool()
def update_interests(interests: list[str]) -> dict:
    """Update your research interests to improve recommendations.

    Args:
        interests: List of research topics (e.g., ["transformers", "computer vision", "RL"])

    Returns:
        Success status with updated interests
    """
    session = get_session()

    try:
        # Get or create profile
        profile = session.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                interests=interests,
                skill_level="intermediate",
                preferred_sources=[],
                daily_reading_goal=5
            )
            session.add(profile)
        else:
            profile.interests = interests

        session.commit()

        return {
            "success": True,
            "interests": interests,
            "message": f"Updated interests to: {', '.join(interests)}"
        }

    finally:
        session.close()


@mcp.tool()
def fetch_articles(
    source: Literal["arxiv", "semanticscholar"],
    query: Optional[str] = None,
    categories: Optional[list[str]] = None,
    limit: int = 20,
    min_citations: Optional[int] = None,
    year: Optional[str] = None
) -> dict:
    """Fetch new research papers from arXiv or Semantic Scholar and add them to your library.

    Args:
        source: Where to fetch from - "arxiv" or "semanticscholar"
        query: Search query (for Semantic Scholar) or None for latest (arXiv)
        categories: arXiv categories to fetch from (e.g., ["cs.AI", "cs.LG"]). Default: ["cs.AI", "cs.LG", "cs.CV", "cs.CL"]
        limit: Maximum number of papers to fetch (default: 20, max for Semantic Scholar: 100)
        min_citations: Minimum citation count (Semantic Scholar only)
        year: Year filter (e.g., "2024" or "2023-2024") (Semantic Scholar only)

    Returns:
        Summary of fetched articles including count of new articles added

    Examples:
        - Fetch latest AI papers from arXiv: fetch_articles(source="arxiv")
        - Search for transformer papers: fetch_articles(source="semanticscholar", query="transformers")
        - Get highly cited recent papers: fetch_articles(source="semanticscholar", query="diffusion models", min_citations=50, year="2024")
    """
    try:
        if source == "arxiv":
            # Fetch from arXiv RSS feeds
            if categories is None:
                categories = ["cs.AI", "cs.LG", "cs.CV", "cs.CL"]

            new_count = fetch_arxiv(categories=categories)

            return {
                "success": True,
                "source": "arxiv",
                "categories": categories,
                "new_articles": new_count,
                "message": f"Fetched {new_count} new papers from arXiv categories: {', '.join(categories)}"
            }

        elif source == "semanticscholar":
            # Fetch from Semantic Scholar
            if not query:
                return {"error": "query parameter is required for Semantic Scholar searches"}

            fetcher = SemanticScholarFetcher()

            try:
                # Fetch papers
                papers = fetcher.fetch(
                    query=query,
                    limit=min(limit, 100),  # S2 API has max 100 per request
                    min_citations=min_citations,
                    year=year
                )

                # Save to database
                new_count = fetcher.save_to_db(papers)

                return {
                    "success": True,
                    "source": "semanticscholar",
                    "query": query,
                    "fetched": len(papers),
                    "new_articles": new_count,
                    "duplicates": len(papers) - new_count,
                    "message": f"Fetched {len(papers)} papers from Semantic Scholar, {new_count} were new",
                    "filters": {
                        "min_citations": min_citations,
                        "year": year
                    }
                }

            finally:
                fetcher.close()

        else:
            return {"error": f"Unknown source: {source}. Must be 'arxiv' or 'semanticscholar'"}

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to fetch articles: {str(e)}"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
