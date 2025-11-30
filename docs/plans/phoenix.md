# Phoenix Integration Plan

**Status: ✅ IMPLEMENTED**

## Overview

Integrate Arize Phoenix for LLM observability and evaluation in Mind Scout. Using Phoenix Cloud dashboard for visualization.

## Dependencies to Add

```toml
# In pyproject.toml dependencies
"arize-phoenix>=8.0.0",
"arize-phoenix-evals>=2.0.0",
"openinference-instrumentation-anthropic>=0.1.0",
```

## Configuration

Add to `.env`:
```
PHOENIX_API_KEY=<your-api-key>
PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com
```

Add to `mindscout/config.py`:
```python
# Phoenix Observability
phoenix_api_key: Optional[str] = Field(default=None, description="Phoenix API key")
phoenix_collector_endpoint: str = Field(
    default="https://app.phoenix.arize.com",
    description="Phoenix collector endpoint"
)
phoenix_enabled: bool = Field(default=True, description="Enable Phoenix tracing")
```

## Implementation Steps

### Step 1: Create Phoenix Instrumentation Module

Create `mindscout/observability.py`:

```python
"""Phoenix observability and tracing setup."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_tracer_provider = None

def init_phoenix(project_name: str = "mind-scout") -> Optional[object]:
    """Initialize Phoenix tracing for LLM observability.

    Args:
        project_name: Name for the Phoenix project

    Returns:
        TracerProvider if successful, None otherwise
    """
    global _tracer_provider

    if _tracer_provider is not None:
        return _tracer_provider

    from mindscout.config import get_settings
    settings = get_settings()

    if not settings.phoenix_enabled:
        logger.info("Phoenix tracing disabled")
        return None

    api_key = settings.phoenix_api_key or os.getenv("PHOENIX_API_KEY")
    if not api_key:
        logger.warning("Phoenix API key not found, tracing disabled")
        return None

    try:
        from phoenix.otel import register

        # Set environment variables for Phoenix cloud
        os.environ["PHOENIX_API_KEY"] = api_key
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = settings.phoenix_collector_endpoint
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={api_key}"

        _tracer_provider = register(
            project_name=project_name,
            auto_instrument=True  # Auto-instruments Anthropic SDK
        )

        logger.info(f"Phoenix tracing initialized for project: {project_name}")
        return _tracer_provider

    except Exception as e:
        logger.error(f"Failed to initialize Phoenix: {e}")
        return None


def get_tracer_provider():
    """Get the current tracer provider."""
    return _tracer_provider
```

### Step 2: Initialize Tracing in LLM Client

Update `mindscout/processors/llm.py`:

```python
# At module level, before LLMClient class
from mindscout.observability import init_phoenix

# Initialize Phoenix when module loads
init_phoenix()
```

### Step 3: Initialize Tracing in Backend

Update `backend/main.py` lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Initialize Phoenix tracing
    from mindscout.observability import init_phoenix
    init_phoenix()

    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()
```

### Step 4: Create Evaluation Module

Create `mindscout/evaluation.py`:

```python
"""LLM evaluation using Phoenix Evals."""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result from an evaluation."""
    score: float
    label: str
    explanation: Optional[str] = None


class TopicEvaluator:
    """Evaluator for topic extraction quality."""

    def __init__(self):
        from phoenix.evals import create_classifier
        from phoenix.evals.llm import LLM

        self.llm = LLM(provider="anthropic", model="claude-3-5-haiku-20241022")

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

Provide your rating:""",
            llm=self.llm,
            choices={"excellent": 1.0, "good": 0.5, "poor": 0.0},
        )

    def evaluate(self, title: str, abstract: str, topics: List[str]) -> EvalResult:
        """Evaluate extracted topics for a single article."""
        result = self.evaluator.evaluate({
            "title": title,
            "abstract": abstract,
            "topics": ", ".join(topics)
        })
        return EvalResult(
            score=result.score,
            label=result.label,
            explanation=result.explanation
        )
```

### Step 5: Add Evaluation CLI Command

Add to `mindscout/cli.py`:

```python
@cli.command()
def evaluate():
    """Run evaluations on processed articles."""
    from mindscout.database import get_db_session, Article
    from mindscout.evaluation import TopicEvaluator

    console.print("[bold]Running evaluations on processed articles...[/bold]")

    with get_db_session() as session:
        # Get articles with topics
        articles = session.query(Article).filter(
            Article.topics.isnot(None),
            Article.abstract.isnot(None)
        ).limit(10).all()

        if not articles:
            console.print("[yellow]No processed articles found[/yellow]")
            return

        topic_eval = TopicEvaluator()

        for article in articles:
            console.print(f"\n[bold]{article.title[:60]}...[/bold]")

            # Evaluate topics
            if article.topics:
                topics = article.topics.split(",")
                result = topic_eval.evaluate(article.title, article.abstract, topics)
                console.print(f"  Topics: {result.label} ({result.score:.2f})")
```

## File Changes Summary

| File | Change |
|------|--------|
| `pyproject.toml` | Add Phoenix dependencies |
| `mindscout/config.py` | Add Phoenix config options |
| `mindscout/observability.py` | New file - tracing setup |
| `mindscout/evaluation.py` | New file - evaluators |
| `mindscout/processors/llm.py` | Initialize Phoenix |
| `backend/main.py` | Initialize Phoenix in lifespan |
| `mindscout/cli.py` | Add evaluate command |

## Testing

1. Set `PHOENIX_API_KEY` environment variable
2. Run `mindscout process` to trace LLM calls
3. Check Phoenix Cloud dashboard for traces
4. Run `mindscout evaluate` to run evaluations

## Notes

- Tracing is automatic once initialized - no code changes needed in LLM calls
- Evaluations use Claude Haiku for cost efficiency
- Can disable tracing with `MINDSCOUT_PHOENIX_ENABLED=false`

## Implementation Notes

### Changes Made

1. **Dependencies** (`pyproject.toml`):
   - `arize-phoenix>=8.0.0`
   - `arize-phoenix-evals>=2.0.0`
   - `openinference-instrumentation-anthropic>=0.1.0`

2. **Configuration** (`mindscout/config.py`):
   - Added `phoenix_enabled`, `phoenix_api_key`, `phoenix_collector_endpoint`, `phoenix_project_name` settings

3. **Observability Module** (`mindscout/observability.py`):
   - `init_phoenix()` - Initialize tracing with Phoenix Cloud
   - Auto-instruments Anthropic SDK via OpenTelemetry

4. **Evaluation Module** (`mindscout/evaluation.py`):
   - `TopicEvaluator` class using Phoenix Evals
   - LLM-as-judge for topic extraction quality

5. **Tracing Initialization**:
   - `mindscout/processors/llm.py` - Module-level init
   - `backend/main.py` - FastAPI lifespan init
   - `mindscout/cli.py` - Evaluate command init

6. **CLI Command**:
   - `mindscout evaluate -n <limit> -v` - Run topic quality evaluations on random articles

### Phoenix Cloud Setup

1. Create account at https://app.phoenix.arize.com
2. Create a space (e.g., "mindscout")
3. Generate API key in Settings → API Keys
4. Add to `.env`:
   ```
   MINDSCOUT_PHOENIX_API_KEY=your-key
   MINDSCOUT_PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/your-space
   ```
