"""Research Planning Agent for discovering and planning new reading material.

This module provides an LLM-powered agent that searches external sources
(Semantic Scholar, arXiv) for papers relevant to a learning goal, analyzes
them, and helps users build a reading plan.
"""

import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from mindscout.fetchers.semanticscholar import SemanticScholarFetcher
from mindscout.processors.llm import LLMClient

logger = logging.getLogger(__name__)

# In-memory storage for pending plans (could be Redis in production)
_pending_plans: dict[str, dict] = {}


def _cleanup_expired_plans():
    """Remove expired plans from storage."""
    now = datetime.now(UTC)
    expired = [pid for pid, plan in _pending_plans.items() if plan["expires"] < now]
    for pid in expired:
        del _pending_plans[pid]


class ResearchPlannerAgent:
    """Agent that helps discover and plan new reading material.

    Two-step workflow:
    1. plan() - Search external sources, analyze with LLM, return candidates
    2. execute() - Fetch selected papers, create reading plan
    """

    def __init__(self):
        self.llm = LLMClient()
        self.ss_fetcher = SemanticScholarFetcher()

    def close(self):
        """Clean up resources."""
        self.ss_fetcher.close()

    def plan(
        self,
        goal: str,
        skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate",
        max_candidates: int = 10,
    ) -> dict:
        """Search for papers and analyze their relevance to a learning goal.

        Args:
            goal: What the user wants to learn (e.g., "RLHF", "transformers")
            skill_level: User's current level in this area
            max_candidates: Maximum number of candidates to return

        Returns:
            Dictionary with plan_id, candidates, and LLM analysis
        """
        _cleanup_expired_plans()

        # 1. Search Semantic Scholar for papers
        try:
            papers = self.ss_fetcher.fetch(
                query=goal,
                limit=max_candidates,
                min_citations=5,  # Filter for quality
            )
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return {
                "success": False,
                "error": "search_failed",
                "message": f"Failed to search for papers: {str(e)}",
            }

        if not papers:
            return {
                "success": False,
                "error": "no_papers_found",
                "message": f"No papers found for '{goal}'. Try a different search term.",
            }

        # 2. Use LLM to analyze relevance and difficulty
        analysis = self._analyze_candidates(goal, skill_level, papers)

        if not analysis.get("success"):
            return analysis

        # 3. Store plan for later execution
        plan_id = str(uuid.uuid4())[:8]
        _pending_plans[plan_id] = {
            "goal": goal,
            "skill_level": skill_level,
            "papers": papers,
            "analysis": analysis,
            "expires": datetime.now(UTC) + timedelta(hours=1),
        }

        # 4. Return candidates with analysis
        candidates = []
        for i, paper in enumerate(papers):
            paper_analysis = next(
                (a for a in analysis.get("candidates", []) if a.get("index") == i),
                {},
            )
            candidates.append(
                {
                    "index": i,
                    "title": paper.get("title", "Unknown"),
                    "authors": paper.get("authors", "Unknown"),
                    "year": paper.get("year"),
                    "citation_count": paper.get("citation_count", 0),
                    "abstract": paper.get("abstract", "")[:300]
                    + ("..." if len(paper.get("abstract", "")) > 300 else ""),
                    "url": paper.get("url", ""),
                    "relevance_score": paper_analysis.get("relevance_score", 5),
                    "difficulty": paper_analysis.get("difficulty", "intermediate"),
                    "rationale": paper_analysis.get("rationale", ""),
                    "suggested_order": paper_analysis.get("suggested_order"),
                }
            )

        # Sort by relevance score
        candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "success": True,
            "plan_id": plan_id,
            "goal": goal,
            "skill_level": skill_level,
            "total_found": len(candidates),
            "candidates": candidates,
            "recommendation": analysis.get("recommendation", ""),
            "expires_in": "1 hour",
        }

    def execute(self, plan_id: str, selected_indices: list[int]) -> dict:
        """Fetch selected papers and create a reading plan.

        Args:
            plan_id: The plan ID from a previous plan() call
            selected_indices: Indices of papers to download (0-based)

        Returns:
            Dictionary with fetched papers and ordered reading plan
        """
        _cleanup_expired_plans()

        # 1. Retrieve the pending plan
        if plan_id not in _pending_plans:
            return {
                "success": False,
                "error": "plan_not_found",
                "message": f"Plan '{plan_id}' not found or expired. Please run plan_research again.",
            }

        plan = _pending_plans[plan_id]
        papers = plan["papers"]
        goal = plan["goal"]
        skill_level = plan["skill_level"]

        # 2. Validate indices
        valid_indices = [i for i in selected_indices if 0 <= i < len(papers)]
        if not valid_indices:
            return {
                "success": False,
                "error": "invalid_indices",
                "message": f"No valid paper indices provided. Valid range: 0-{len(papers)-1}",
            }

        # 3. Get selected papers
        selected_papers = [papers[i] for i in valid_indices]

        # 4. Save papers to database
        try:
            # Add rate limit delay
            time.sleep(1)
            new_count = self.ss_fetcher.save_to_db(selected_papers)
        except Exception as e:
            logger.error(f"Error saving papers: {e}")
            return {
                "success": False,
                "error": "save_failed",
                "message": f"Failed to save papers: {str(e)}",
            }

        # 5. Create reading plan using LLM
        reading_plan = self._create_reading_plan(goal, skill_level, selected_papers)

        # 6. Clean up the pending plan
        del _pending_plans[plan_id]

        return {
            "success": True,
            "goal": goal,
            "papers_added": new_count,
            "duplicates_skipped": len(selected_papers) - new_count,
            "reading_plan": reading_plan,
        }

    def _analyze_candidates(
        self,
        goal: str,
        skill_level: str,
        papers: list[dict],
    ) -> dict:
        """Use LLM to analyze paper relevance and difficulty."""
        # Format papers for the prompt
        paper_list = []
        for i, paper in enumerate(papers):
            paper_list.append(
                f"""Paper {i}:
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'Unknown')}
Citations: {paper.get('citation_count', 0)}
Abstract: {paper.get('abstract', '')[:400]}
"""
            )

        papers_text = "\n---\n".join(paper_list)

        system_prompt = """You are an expert research advisor helping someone plan their learning.
Analyze the papers and assess their value for the learning goal.
Always return valid JSON matching the specified format."""

        user_prompt = f"""Learning Goal: {goal}
User's Skill Level: {skill_level}

Papers found:

{papers_text}

For each paper, assess:
1. Relevance to learning goal (1-10)
2. Difficulty level (beginner/intermediate/advanced)
3. Why it would be valuable (1-2 sentences)
4. Suggested reading order if selected (1 = read first)

Return JSON:
{{
    "candidates": [
        {{
            "index": 0,
            "relevance_score": 8,
            "difficulty": "intermediate",
            "rationale": "This paper provides...",
            "suggested_order": 1
        }}
    ],
    "recommendation": "For a solid understanding of {goal}, I recommend..."
}}"""

        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=2000,
                temperature=0.3,
            )

            # Parse JSON from response
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            result = json.loads(json_str.strip())
            result["success"] = True
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Return basic analysis without LLM insights
            return {
                "success": True,
                "candidates": [
                    {"index": i, "relevance_score": 5, "difficulty": "intermediate"}
                    for i in range(len(papers))
                ],
                "recommendation": f"Found {len(papers)} papers related to {goal}.",
            }
        except Exception as e:
            logger.error(f"Error analyzing candidates: {e}")
            return {
                "success": False,
                "error": "analysis_failed",
                "message": str(e),
            }

    def _create_reading_plan(
        self,
        goal: str,
        skill_level: str,
        papers: list[dict],
    ) -> dict:
        """Create an ordered reading plan for selected papers."""
        if len(papers) == 1:
            # Single paper, no need for ordering
            paper = papers[0]
            return {
                "summary": f"Read '{paper.get('title')}' to learn about {goal}.",
                "path": [
                    {
                        "order": 1,
                        "title": paper.get("title"),
                        "authors": paper.get("authors"),
                        "rationale": "Start with this paper.",
                        "estimated_time": "2-3 hours",
                    }
                ],
            }

        # Format papers for LLM
        paper_list = []
        for i, paper in enumerate(papers):
            paper_list.append(
                f"""Paper {i + 1}:
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Year: {paper.get('year', 'Unknown')}
Citations: {paper.get('citation_count', 0)}
Abstract: {paper.get('abstract', '')[:300]}
"""
            )

        papers_text = "\n---\n".join(paper_list)

        system_prompt = """You are an expert research advisor creating a reading plan.
Order the papers for optimal learning progression.
Return valid JSON only."""

        user_prompt = f"""Goal: Learn about {goal}
Skill Level: {skill_level}

Papers to order:

{papers_text}

Create a reading plan. Return JSON:
{{
    "summary": "Brief overview of what this path will teach",
    "path": [
        {{
            "order": 1,
            "title": "Paper title",
            "authors": "Authors",
            "rationale": "Why read this first",
            "estimated_time": "X hours"
        }}
    ]
}}"""

        try:
            response = self.llm.generate(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=1500,
                temperature=0.3,
            )

            # Parse JSON
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())

        except Exception as e:
            logger.error(f"Error creating reading plan: {e}")
            # Return basic order
            return {
                "summary": f"Read these {len(papers)} papers to learn about {goal}.",
                "path": [
                    {
                        "order": i + 1,
                        "title": p.get("title"),
                        "authors": p.get("authors"),
                        "rationale": "Suggested reading",
                        "estimated_time": "2-3 hours",
                    }
                    for i, p in enumerate(papers)
                ],
            }
