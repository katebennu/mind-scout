"""LLM evaluation using Phoenix Evals."""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result from an evaluation."""

    score: float
    label: str
    explanation: Optional[str] = None


class TopicEvaluator:
    """Evaluator for topic extraction quality."""

    def __init__(self, model: str = "claude-3-5-haiku-20241022"):
        """Initialize the topic evaluator.

        Args:
            model: Anthropic model to use for evaluation
        """
        from phoenix.evals import LLM, create_classifier

        self.llm = LLM(provider="anthropic", model=model)

        self.evaluator = create_classifier(
            name="topic_relevance",
            prompt_template="""Evaluate if the extracted topics are relevant and accurate for this research paper.

Title: {title}
Abstract: {abstract}
Extracted Topics: {topics}

Rate the topics as:
- "excellent": All topics are relevant, specific, and capture key themes
- "good": Most topics are relevant but some may be too generic or miss key themes
- "poor": Topics are irrelevant, too generic, or miss the main themes

Respond with exactly one word: excellent, good, or poor.""",
            llm=self.llm,
            choices={"excellent": 1.0, "good": 0.5, "poor": 0.0},
        )

    def evaluate(self, title: str, abstract: str, topics: list[str]) -> EvalResult:
        """Evaluate extracted topics for a single article.

        Args:
            title: Article title
            abstract: Article abstract
            topics: List of extracted topics

        Returns:
            EvalResult with score, label, and explanation
        """
        results = self.evaluator.evaluate(
            {"title": title, "abstract": abstract, "topics": ", ".join(topics)}
        )

        # Results is a list of Score objects
        if results:
            score_obj = results[0]
            return EvalResult(
                score=score_obj.score, label=score_obj.label, explanation=score_obj.explanation
            )

        return EvalResult(score=0.0, label="unknown", explanation=None)

    def evaluate_batch(self, articles: list[dict], concurrency: int = 5) -> list[EvalResult]:
        """Evaluate topics for multiple articles.

        Args:
            articles: List of dicts with 'title', 'abstract', 'topics' keys
            concurrency: Number of concurrent evaluation calls

        Returns:
            List of EvalResult objects
        """
        eval_results = []

        for article in articles:
            topics = article["topics"]
            if isinstance(topics, list):
                topics = ", ".join(topics)

            result = self.evaluate(
                title=article["title"],
                abstract=article["abstract"],
                topics=topics.split(", ") if isinstance(topics, str) else topics,
            )
            eval_results.append(result)

        return eval_results
