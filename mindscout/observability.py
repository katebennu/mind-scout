"""Phoenix observability and tracing setup."""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_tracer_provider = None
_initialized = False


def init_phoenix(project_name: Optional[str] = None) -> Optional[object]:
    """Initialize Phoenix tracing for LLM observability.

    Args:
        project_name: Name for the Phoenix project (defaults to config value)

    Returns:
        TracerProvider if successful, None otherwise
    """
    global _tracer_provider, _initialized

    # Only attempt initialization once
    if _initialized:
        return _tracer_provider

    _initialized = True

    from mindscout.config import get_settings

    settings = get_settings()

    if not settings.phoenix_enabled:
        logger.info("Phoenix tracing disabled via config")
        return None

    # Get API key from config or environment
    api_key = settings.phoenix_api_key or os.getenv("PHOENIX_API_KEY")
    if not api_key:
        logger.info("Phoenix API key not found, tracing disabled")
        return None

    project = project_name or settings.phoenix_project_name

    try:
        from phoenix.otel import register

        # Set environment variables for Phoenix cloud
        os.environ["PHOENIX_API_KEY"] = api_key
        os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = settings.phoenix_collector_endpoint
        os.environ["PHOENIX_CLIENT_HEADERS"] = f"api_key={api_key}"

        _tracer_provider = register(
            project_name=project, auto_instrument=True  # Auto-instruments Anthropic SDK
        )

        logger.info(
            f"Phoenix tracing initialized - project: {project}, "
            f"endpoint: {settings.phoenix_collector_endpoint}"
        )
        return _tracer_provider

    except ImportError as e:
        logger.warning(f"Phoenix packages not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix: {e}")
        return None


def get_tracer_provider():
    """Get the current tracer provider."""
    return _tracer_provider


def is_tracing_enabled() -> bool:
    """Check if tracing is enabled and initialized."""
    return _tracer_provider is not None
