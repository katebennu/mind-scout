"""Recommendation engine for personalized article suggestions."""

import json
from datetime import datetime, timedelta

from mindscout.database import Article, get_session
from mindscout.profile import ProfileManager


class RecommendationEngine:
    """Generate personalized article recommendations."""

    def __init__(self):
        """Initialize recommendation engine."""
        self.session = get_session()
        self.profile_manager = ProfileManager()

    def get_recommendations(
        self,
        limit: int = 10,
        days_back: int = 30,
        min_score: float = 0.1,
        unread_only: bool = True,
    ) -> list[dict]:
        """Get personalized article recommendations.

        Args:
            limit: Maximum number of recommendations
            days_back: Only consider articles from last N days
            min_score: Minimum recommendation score (0-1)
            unread_only: Only recommend unread articles

        Returns:
            List of article dictionaries with scores and reasons
        """
        profile = self.profile_manager.get_or_create_profile()
        interests = self.profile_manager.get_interests()

        # Build query for candidate articles
        query = self.session.query(Article)

        # Filter by date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(Article.fetched_date >= cutoff_date)

        # Filter by read status
        if unread_only:
            query = query.filter(not Article.is_read)

        # Get all candidates
        candidates = query.all()

        # Score each article
        scored_articles = []
        for article in candidates:
            score, reasons = self._score_article(article, interests, profile)

            if score >= min_score:
                scored_articles.append(
                    {
                        "article": article,
                        "score": score,
                        "reasons": reasons,
                    }
                )

        # Sort by score (descending) and limit
        scored_articles.sort(key=lambda x: x["score"], reverse=True)

        return scored_articles[:limit]

    def _score_article(
        self, article: Article, interests: list[str], profile
    ) -> tuple[float, list[str]]:
        """Score an article based on user profile.

        Args:
            article: Article to score
            interests: User interests
            profile: User profile

        Returns:
            Tuple of (score, reasons) where score is 0-1 and reasons is a list of strings
        """
        score = 0.0
        reasons = []

        # 1. Topic matching (35% weight)
        topic_score = self._score_topics(article, interests)
        if topic_score > 0:
            score += topic_score * 0.35
            reasons.append(f"Matches your interests ({topic_score:.0%})")

        # 2. Citation count (20% weight)
        citation_score = self._score_citations(article)
        if citation_score > 0:
            score += citation_score * 0.20
            reasons.append(f"High impact ({int(article.citation_count or 0)} citations)")

        # 3. Skill level match (15% weight)
        skill_score = self._score_skill_match(article, profile)
        if skill_score > 0.6:  # Only mention if notably relevant
            score += skill_score * 0.15
            if profile.skill_level:
                if profile.skill_level.lower() == "beginner" and skill_score > 0.8:
                    reasons.append("Good for beginners")
                elif profile.skill_level.lower() == "advanced" and skill_score > 0.8:
                    reasons.append("Cutting-edge research")
        else:
            score += skill_score * 0.15

        # 4. Source preference (10% weight)
        source_score = self._score_source(article, profile)
        if source_score > 0:
            score += source_score * 0.10
            if source_score == 1.0:
                reasons.append("From preferred source")

        # 5. Recency (10% weight)
        recency_score = self._score_recency(article)
        score += recency_score * 0.10
        if recency_score > 0.8:
            reasons.append("Recently published")

        # 6. Has implementation (10% weight)
        if article.has_implementation and article.github_url:
            score += 0.10
            reasons.append("Has code implementation")

        return min(score, 1.0), reasons

    def _score_topics(self, article: Article, interests: list[str]) -> float:
        """Score article based on topic matching.

        Returns:
            Score between 0 and 1
        """
        if not interests or not article.topics:
            return 0.0

        try:
            # Parse article topics
            article_topics = json.loads(article.topics) if article.topics else []
        except (json.JSONDecodeError, TypeError):
            # Fallback to categories if topics not available
            if article.categories:
                article_topics = [c.strip() for c in article.categories.split(",")]
            else:
                return 0.0

        # Convert to lowercase for matching
        article_topics_lower = [t.lower() for t in article_topics]
        interests_lower = [i.lower() for i in interests]

        # Count matches
        matches = sum(
            1
            for interest in interests_lower
            if any(interest in topic or topic in interest for topic in article_topics_lower)
        )

        # Normalize by number of interests
        return min(matches / len(interests), 1.0) if interests else 0.0

    def _score_citations(self, article: Article) -> float:
        """Score article based on citation count.

        Returns:
            Score between 0 and 1
        """
        if not article.citation_count:
            return 0.0

        # Logarithmic scaling: 10 citations = 0.5, 100 = 0.75, 1000 = 1.0
        import math

        score = math.log10(max(article.citation_count, 1)) / 3.0
        return min(score, 1.0)

    def _score_source(self, article: Article, profile) -> float:
        """Score article based on source preference.

        Returns:
            Score between 0 and 1
        """
        if not profile.preferred_sources:
            return 0.5  # Neutral if no preference

        preferred = profile.preferred_sources.split(",")
        return 1.0 if article.source in preferred else 0.0

    def _score_recency(self, article: Article) -> float:
        """Score article based on how recent it is.

        Returns:
            Score between 0 and 1
        """
        if not article.published_date:
            return 0.5  # Neutral if no date

        # Days old
        age_days = (datetime.utcnow() - article.published_date).days

        # Score: 1.0 for today, 0.5 for 30 days, 0.0 for 90+ days
        if age_days < 7:
            return 1.0
        elif age_days < 30:
            return 0.8
        elif age_days < 60:
            return 0.5
        elif age_days < 90:
            return 0.3
        else:
            return 0.1

    def _score_skill_match(self, article: Article, profile) -> float:
        """Score article based on skill level match.

        Uses heuristics to estimate paper difficulty and match to user skill level:
        - Beginner: Prefers surveys, tutorials, well-cited foundational papers
        - Intermediate: No strong preference (neutral scoring)
        - Advanced: Prefers recent, cutting-edge, high-impact research

        Args:
            article: Article to score
            profile: User profile

        Returns:
            Score between 0 and 1
        """
        if not profile.skill_level:
            return 0.5  # Neutral if not set

        skill = profile.skill_level.lower()

        # Keywords indicating beginner-friendly content
        beginner_keywords = [
            "survey",
            "review",
            "introduction",
            "tutorial",
            "overview",
            "primer",
            "guide",
            "fundamentals",
            "basics",
            "introduction to",
        ]

        # Combine title and abstract for keyword matching
        text = f"{article.title} {article.abstract or ''}".lower()

        # Calculate paper age
        age_days = None
        if article.published_date:
            age_days = (datetime.utcnow() - article.published_date).days

        # Beginner: Prefer educational content and well-established papers
        if skill == "beginner":
            # Check for beginner-friendly keywords
            if any(keyword in text for keyword in beginner_keywords):
                return 1.0  # Perfect match for tutorials/surveys

            # Prefer well-cited papers (established, likely well-explained)
            if article.citation_count:
                if article.citation_count > 500:
                    return 0.9  # Very well established
                elif article.citation_count > 100:
                    return 0.8  # Well established
                elif article.citation_count > 50:
                    return 0.6

            # Boost papers with implementations (hands-on learning)
            if article.has_implementation:
                return 0.7

            # Slightly penalize very recent papers (less likely to be foundational)
            if age_days and age_days < 90:
                return 0.4

            return 0.5  # Neutral for other papers

        # Intermediate: No strong bias, slight preference for balance
        elif skill == "intermediate":
            # Slight boost for papers 1-2 years old (current but not bleeding edge)
            if age_days:
                if 180 < age_days < 730:  # 6 months to 2 years
                    return 0.7

            # Moderate citation count is good
            if article.citation_count:
                if 50 < article.citation_count < 500:
                    return 0.6

            return 0.5  # Neutral default

        # Advanced: Prefer cutting-edge, high-impact research
        elif skill == "advanced":
            # Strong preference for very recent papers
            if age_days:
                if age_days < 90:
                    return 1.0  # Last 3 months
                elif age_days < 180:
                    return 0.9  # Last 6 months
                elif age_days < 365:
                    return 0.7  # Last year

            # High citation count indicates important work
            if article.citation_count:
                if article.citation_count > 1000:
                    return 1.0  # Seminal paper
                elif article.citation_count > 500:
                    return 0.9  # High impact

            # Penalize tutorials/surveys (advanced users want novel research)
            if any(keyword in text for keyword in beginner_keywords):
                return 0.2

            return 0.5  # Neutral for moderate papers

        return 0.5  # Default neutral

    def explain_recommendation(self, article: Article) -> dict:
        """Explain why an article is recommended.

        Args:
            article: Article to explain

        Returns:
            Dictionary with detailed scoring breakdown
        """
        profile = self.profile_manager.get_or_create_profile()
        interests = self.profile_manager.get_interests()

        score, reasons = self._score_article(article, interests, profile)

        return {
            "article_id": article.id,
            "title": article.title,
            "overall_score": score,
            "reasons": reasons,
            "details": {
                "topic_match": self._score_topics(article, interests),
                "citation_score": self._score_citations(article),
                "skill_level_match": self._score_skill_match(article, profile),
                "source_preference": self._score_source(article, profile),
                "recency": self._score_recency(article),
                "has_code": article.has_implementation,
            },
        }

    def get_semantic_recommendations(
        self,
        limit: int = 10,
        use_interests: bool = True,
        use_reading_history: bool = True,
    ) -> list[dict]:
        """Get recommendations using semantic similarity.

        Args:
            limit: Maximum number of recommendations
            use_interests: Use user interests for semantic search
            use_reading_history: Use highly-rated articles for similarity

        Returns:
            List of semantically similar articles
        """
        from mindscout.vectorstore import VectorStore

        vector_store = VectorStore()
        recommendations = []

        try:
            # Strategy 1: Search by user interests
            if use_interests:
                interests = self.profile_manager.get_interests()
                if interests:
                    # Create a query from interests
                    query = " ".join(interests)
                    results = vector_store.semantic_search(query, n_results=limit)

                    for result in results:
                        article = result["article"]
                        # Skip read articles
                        if not article.is_read:
                            recommendations.append(
                                {
                                    "article": article,
                                    "score": result["relevance"],
                                    "reasons": [
                                        f"Semantically matches your interests ({result['relevance']:.0%})"
                                    ],
                                    "method": "interest_search",
                                }
                            )

            # Strategy 2: Find papers similar to highly-rated ones
            if use_reading_history:
                # Get user's highly rated articles (4-5 stars)
                high_rated = self.session.query(Article).filter(Article.rating >= 4).limit(3).all()

                for rated_article in high_rated:
                    similar = vector_store.find_similar(
                        rated_article.id, n_results=5, min_similarity=0.5
                    )

                    for sim in similar:
                        article = sim["article"]
                        if not article.is_read:
                            recommendations.append(
                                {
                                    "article": article,
                                    "score": sim["similarity"],
                                    "reasons": [
                                        f"Similar to '{rated_article.title[:50]}...' ({sim['similarity']:.0%})"
                                    ],
                                    "method": "similar_to_liked",
                                }
                            )

            # Remove duplicates and sort by score
            seen_ids = set()
            unique_recs = []
            for rec in sorted(recommendations, key=lambda x: x["score"], reverse=True):
                if rec["article"].id not in seen_ids:
                    seen_ids.add(rec["article"].id)
                    unique_recs.append(rec)

            return unique_recs[:limit]

        finally:
            vector_store.close()

    def close(self):
        """Close database sessions."""
        self.session.close()
        self.profile_manager.close()
