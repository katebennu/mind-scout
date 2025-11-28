"""LLM client wrapper for Anthropic Claude."""

import json
import logging
import os
import time
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for Anthropic Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        """Initialize the LLM client.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
            model: Model to use. Default is Claude 3.5 Haiku (fast and cost-effective).
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Claude.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def summarize(self, text: str, max_sentences: int = 2) -> str:
        """Summarize text using Claude.

        Args:
            text: Text to summarize (e.g., article abstract)
            max_sentences: Maximum sentences in summary

        Returns:
            Summary text
        """
        system = (
            "You are a technical summarizer for AI research papers. "
            "Create concise, accurate summaries that capture the key contribution."
        )

        prompt = f"""Summarize the following research abstract in {max_sentences} clear, technical sentences.
Focus on the main contribution and findings.

Abstract:
{text}

Summary:"""

        return self.generate(prompt, system=system, max_tokens=300, temperature=0.5)

    def extract_topics(self, title: str, abstract: str, max_topics: int = 5) -> list[str]:
        """Extract key topics/keywords from an article.

        Args:
            title: Article title
            abstract: Article abstract
            max_topics: Maximum number of topics to extract

        Returns:
            List of topic strings
        """
        system = (
            "You are an AI research topic classifier. "
            "Extract key technical topics and concepts from research papers."
        )

        prompt = f"""Extract up to {max_topics} key technical topics from this research paper.
Return only the topics as a comma-separated list, nothing else.

Title: {title}

Abstract: {abstract}

Topics:"""

        response = self.generate(prompt, system=system, max_tokens=200, temperature=0.3)

        # Parse comma-separated topics
        topics = [topic.strip() for topic in response.split(",")]
        # Clean up and limit
        topics = [t for t in topics if t and len(t) > 2][:max_topics]
        return topics

    def generate_embedding(self, text: str) -> list[float]:
        """Generate text embedding using Claude.

        Note: For Phase 2, we'll use a simple approach with Anthropic's API.
        In Phase 5, we may switch to a dedicated embedding model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        # For now, we'll use a simple hash-based approach
        # In Phase 5, we'll integrate a proper embedding model (Voyage AI, OpenAI, etc.)
        import hashlib
        import numpy as np

        # Simple hash-based embedding (768 dimensions)
        # This is a placeholder - will be replaced in Phase 5 with proper embeddings
        hash_obj = hashlib.sha256(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Generate pseudo-random but deterministic embedding
        np.random.seed(hash_int % (2**32))
        embedding = np.random.randn(768).tolist()

        return embedding

    def extract_topics_batch(
        self, articles: list[dict], max_topics: int = 5
    ) -> dict[str, list[str]]:
        """Extract topics for multiple articles in a single API call.

        This is more cost-effective than calling extract_topics for each article
        individually. Reduces API calls by ~5-10x.

        Args:
            articles: List of dicts with 'id', 'title', and 'abstract' keys
            max_topics: Maximum topics per article

        Returns:
            Dict mapping article ID to list of topics
        """
        if not articles:
            return {}

        # Build prompt for all articles
        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"""
Article {i} (ID: {article['id']}):
Title: {article['title']}
Abstract: {article.get('abstract', '')}

"""

        system = (
            "You are an AI research topic classifier. "
            "Extract key technical topics and concepts from research papers. "
            "Return results as valid JSON."
        )

        prompt = f"""Extract up to {max_topics} key technical topics for each of the following articles.

Return a JSON object where keys are article IDs and values are arrays of topic strings.
Return ONLY valid JSON, no other text.

{articles_text}

JSON response:"""

        try:
            response = self.generate(prompt, system=system, max_tokens=1000, temperature=0.3)

            # Parse JSON response
            # Clean up response - sometimes model adds markdown code blocks
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            result = json.loads(response.strip())

            # Ensure all IDs are strings and topics are lists
            return {
                str(k): [t.strip() for t in v if t and len(t.strip()) > 2][:max_topics]
                for k, v in result.items()
            }

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Batch topic extraction failed: {e}")
            # Fall back to empty dict - caller should handle gracefully
            return {}

    def create_topic_extraction_batch(
        self, articles: list[dict], max_topics: int = 5
    ) -> str:
        """Create an async batch for topic extraction (50% cheaper).

        Uses Anthropic's Message Batches API for cost-effective processing.
        Results are available within 24 hours.

        Args:
            articles: List of dicts with 'id', 'title', and 'abstract' keys
            max_topics: Maximum topics per article

        Returns:
            Batch ID for retrieving results later
        """
        if not articles:
            raise ValueError("No articles provided")

        system = (
            "You are an AI research topic classifier. "
            "Extract key technical topics and concepts from research papers."
        )

        requests = []
        for article in articles:
            prompt = f"""Extract up to {max_topics} key technical topics from this research paper.
Return only the topics as a comma-separated list, nothing else.

Title: {article['title']}

Abstract: {article.get('abstract', '')}

Topics:"""

            requests.append({
                "custom_id": str(article["id"]),
                "params": {
                    "model": self.model,
                    "max_tokens": 200,
                    "temperature": 0.3,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            })

        batch = self.client.messages.batches.create(requests=requests)
        logger.info(f"Created batch {batch.id} with {len(requests)} requests")
        return batch.id

    def get_batch_status(self, batch_id: str) -> dict:
        """Get the status of a message batch.

        Args:
            batch_id: The batch ID returned from create_topic_extraction_batch

        Returns:
            Dict with 'status' and 'counts' keys
        """
        batch = self.client.messages.batches.retrieve(batch_id)
        return {
            "id": batch.id,
            "status": batch.processing_status,
            "created_at": batch.created_at,
            "ended_at": batch.ended_at,
            "counts": {
                "processing": batch.request_counts.processing,
                "succeeded": batch.request_counts.succeeded,
                "errored": batch.request_counts.errored,
                "canceled": batch.request_counts.canceled,
                "expired": batch.request_counts.expired,
            },
        }

    def get_batch_results(self, batch_id: str) -> dict[str, list[str]]:
        """Retrieve results from a completed batch.

        Args:
            batch_id: The batch ID

        Returns:
            Dict mapping article ID to list of topics
        """
        results = {}

        for entry in self.client.messages.batches.results(batch_id):
            article_id = entry.custom_id
            if entry.result.type == "succeeded":
                # Parse topics from response
                response_text = entry.result.message.content[0].text
                topics = [t.strip() for t in response_text.split(",")]
                topics = [t for t in topics if t and len(t) > 2][:5]
                results[article_id] = topics
            else:
                logger.warning(f"Batch request {article_id} failed: {entry.result.type}")
                results[article_id] = []

        return results

    def poll_batch_until_complete(
        self, batch_id: str, poll_interval: int = 60, max_wait: int = 86400
    ) -> dict[str, list[str]]:
        """Poll a batch until complete and return results.

        Args:
            batch_id: The batch ID
            poll_interval: Seconds between polls (default 60)
            max_wait: Maximum seconds to wait (default 24 hours)

        Returns:
            Dict mapping article ID to list of topics

        Raises:
            TimeoutError: If batch doesn't complete within max_wait
        """
        start_time = time.time()

        while True:
            status = self.get_batch_status(batch_id)

            if status["status"] == "ended":
                logger.info(f"Batch {batch_id} completed")
                return self.get_batch_results(batch_id)

            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"Batch {batch_id} did not complete within {max_wait}s")

            logger.info(
                f"Batch {batch_id} status: {status['status']}, "
                f"succeeded: {status['counts']['succeeded']}, "
                f"processing: {status['counts']['processing']}"
            )
            time.sleep(poll_interval)
