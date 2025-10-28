"""LLM client wrapper for Anthropic Claude."""

import os
from typing import Optional
from anthropic import Anthropic


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
