"""User profile management for personalized recommendations."""

from datetime import datetime
from typing import Optional

from mindscout.database import UserProfile, get_session


class ProfileManager:
    """Manages user profile and preferences."""

    def __init__(self):
        """Initialize profile manager."""
        self.session = get_session()

    def get_or_create_profile(self) -> UserProfile:
        """Get the user profile, creating default if it doesn't exist."""
        profile = self.session.query(UserProfile).first()

        if not profile:
            # Create default profile
            profile = UserProfile(
                interests="",
                skill_level="intermediate",
                preferred_sources="arxiv,semanticscholar",
                daily_reading_goal=5,
            )
            self.session.add(profile)
            self.session.commit()

        return profile

    def get_profile(self) -> Optional[UserProfile]:
        """Get the user profile."""
        return self.session.query(UserProfile).first()

    def set_interests(self, interests: list[str]) -> UserProfile:
        """Set user interests.

        Args:
            interests: List of topics the user is interested in

        Returns:
            Updated profile
        """
        profile = self.get_or_create_profile()
        profile.interests = ",".join(interests)
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def add_interests(self, new_interests: list[str]) -> UserProfile:
        """Add new interests without removing existing ones.

        Args:
            new_interests: List of topics to add

        Returns:
            Updated profile
        """
        profile = self.get_or_create_profile()

        # Get existing interests
        existing = set(profile.interests.split(",")) if profile.interests else set()
        existing.discard("")  # Remove empty string

        # Add new interests
        existing.update(new_interests)

        profile.interests = ",".join(sorted(existing))
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def remove_interests(self, interests_to_remove: list[str]) -> UserProfile:
        """Remove interests from profile.

        Args:
            interests_to_remove: List of topics to remove

        Returns:
            Updated profile
        """
        profile = self.get_or_create_profile()

        # Get existing interests
        existing = set(profile.interests.split(",")) if profile.interests else set()
        existing.discard("")

        # Remove specified interests
        for interest in interests_to_remove:
            existing.discard(interest)

        profile.interests = ",".join(sorted(existing))
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def get_interests(self) -> list[str]:
        """Get list of user interests.

        Returns:
            List of interest topics
        """
        profile = self.get_or_create_profile()
        if not profile.interests:
            return []
        return [i.strip() for i in profile.interests.split(",") if i.strip()]

    def set_skill_level(self, skill_level: str) -> UserProfile:
        """Set user skill level.

        Args:
            skill_level: One of 'beginner', 'intermediate', 'advanced'

        Returns:
            Updated profile
        """
        valid_levels = ["beginner", "intermediate", "advanced"]
        if skill_level not in valid_levels:
            raise ValueError(f"Skill level must be one of: {', '.join(valid_levels)}")

        profile = self.get_or_create_profile()
        profile.skill_level = skill_level
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def set_preferred_sources(self, sources: list[str]) -> UserProfile:
        """Set preferred sources.

        Args:
            sources: List of preferred sources (e.g., ['arxiv', 'semanticscholar'])

        Returns:
            Updated profile
        """
        profile = self.get_or_create_profile()
        profile.preferred_sources = ",".join(sources)
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def set_daily_goal(self, goal: int) -> UserProfile:
        """Set daily reading goal.

        Args:
            goal: Number of papers to read per day

        Returns:
            Updated profile
        """
        if goal < 1:
            raise ValueError("Daily goal must be at least 1")

        profile = self.get_or_create_profile()
        profile.daily_reading_goal = goal
        profile.updated_date = datetime.utcnow()
        self.session.commit()
        return profile

    def get_profile_summary(self) -> dict:
        """Get a summary of the user profile.

        Returns:
            Dictionary with profile information
        """
        profile = self.get_or_create_profile()

        return {
            "interests": self.get_interests(),
            "skill_level": profile.skill_level,
            "preferred_sources": (
                profile.preferred_sources.split(",") if profile.preferred_sources else []
            ),
            "daily_reading_goal": profile.daily_reading_goal,
            "created_date": profile.created_date,
            "updated_date": profile.updated_date,
        }

    def close(self):
        """Close the database session."""
        self.session.close()
