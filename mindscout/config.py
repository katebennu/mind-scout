"""Configuration management for Mind Scout."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="MINDSCOUT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    data_dir: Path = Field(
        default=Path.home() / ".mindscout", description="Base directory for Mind Scout data"
    )

    # Database
    database_url: Optional[str] = Field(
        default=None, description="Database URL (defaults to SQLite in data_dir)"
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key for Claude"
    )

    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Maximum requests per minute")
    rate_limit_process: int = Field(
        default=10, description="Maximum process requests per minute (LLM calls)"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Scheduler
    scheduler_enabled: bool = Field(
        default=True, description="Enable background scheduler for daily fetch/process"
    )
    scheduler_hour: int = Field(default=6, description="Hour to run daily job (0-23)")
    scheduler_minute: int = Field(default=0, description="Minute to run daily job (0-59)")

    # Phoenix Observability
    phoenix_enabled: bool = Field(
        default=True, description="Enable Phoenix tracing for LLM observability"
    )
    phoenix_api_key: Optional[str] = Field(
        default=None, description="Phoenix API key for cloud dashboard"
    )
    phoenix_collector_endpoint: str = Field(
        default="https://app.phoenix.arize.com", description="Phoenix collector endpoint"
    )
    phoenix_project_name: str = Field(default="mind-scout", description="Phoenix project name")

    @property
    def db_path(self) -> Path:
        """Get database path."""
        return self.data_dir / "mindscout.db"

    @property
    def chroma_path(self) -> Path:
        """Get ChromaDB path."""
        return self.data_dir / "chroma"

    @property
    def effective_database_url(self) -> str:
        """Get effective database URL."""
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.db_path}"

    def setup_directories(self):
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.setup_directories()
    return settings


# Legacy compatibility - these will be deprecated
_settings = get_settings()
DATA_DIR = _settings.data_dir
DB_PATH = _settings.db_path

# arXiv RSS feeds by category
ARXIV_FEEDS = {
    "cs.AI": "http://export.arxiv.org/rss/cs.AI",  # Artificial Intelligence
    "cs.LG": "http://export.arxiv.org/rss/cs.LG",  # Machine Learning
    "cs.CL": "http://export.arxiv.org/rss/cs.CL",  # Computation and Language
    "cs.CV": "http://export.arxiv.org/rss/cs.CV",  # Computer Vision
}

# Default categories to fetch (user can customize later)
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]

# Curated RSS feeds for subscription suggestions
# Note: Some major AI company blogs don't have working RSS feeds (OpenAI, Anthropic, Meta AI, DeepMind)
CURATED_FEEDS = [
    # Tech Blogs
    {
        "url": "https://blog.google/technology/ai/rss/",
        "title": "Google AI Blog",
        "category": "tech_blog",
        "description": "AI research and product updates from Google",
    },
    {
        "url": "https://huggingface.co/blog/feed.xml",
        "title": "Hugging Face Blog",
        "category": "tech_blog",
        "description": "Open-source ML tools and research",
    },
    {
        "url": "https://lilianweng.github.io/index.xml",
        "title": "Lil'Log (Lilian Weng)",
        "category": "tech_blog",
        "description": "In-depth ML tutorials and explanations",
    },
    {
        "url": "https://pytorch.org/blog/feed.xml",
        "title": "PyTorch Blog",
        "category": "tech_blog",
        "description": "PyTorch updates, tutorials, and best practices",
    },
    # News & Analysis
    {
        "url": "https://www.technologyreview.com/feed/",
        "title": "MIT Technology Review",
        "category": "news",
        "description": "Technology news and analysis",
    },
    {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "title": "Wired AI",
        "category": "news",
        "description": "AI coverage from Wired magazine",
    },
    {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "title": "TechCrunch AI",
        "category": "news",
        "description": "AI startup and industry news",
    },
    # Podcasts
    {
        "url": "https://lexfridman.com/feed/podcast/",
        "title": "Lex Fridman Podcast",
        "category": "podcast",
        "description": "In-depth conversations about AI, science, and technology",
    },
    {
        "url": "https://feeds.megaphone.fm/MLN2155636147",
        "title": "The TWIML AI Podcast",
        "category": "podcast",
        "description": "This Week in Machine Learning & AI",
    },
    {
        "url": "https://anchor.fm/s/1e4a0eac/podcast/rss",
        "title": "Machine Learning Street Talk",
        "category": "podcast",
        "description": "Technical ML discussions with researchers",
    },
    {
        "url": "https://feeds.simplecast.com/JGE3yC0V",
        "title": "Latent Space",
        "category": "podcast",
        "description": "AI engineering and research insights",
    },
    # Newsletters/Substacks
    {
        "url": "https://www.aisnakeoil.com/feed",
        "title": "AI Snake Oil",
        "category": "newsletter",
        "description": "Critical analysis of AI hype and reality",
    },
    {
        "url": "https://newsletter.ruder.io/feed",
        "title": "Sebastian Ruder's NLP Newsletter",
        "category": "newsletter",
        "description": "NLP research highlights and analysis",
    },
    # arXiv Categories (already in ARXIV_FEEDS but included for discoverability)
    {
        "url": "http://export.arxiv.org/rss/cs.AI",
        "title": "arXiv cs.AI",
        "category": "papers",
        "description": "New papers in Artificial Intelligence",
    },
    {
        "url": "http://export.arxiv.org/rss/cs.LG",
        "title": "arXiv cs.LG",
        "category": "papers",
        "description": "New papers in Machine Learning",
    },
    {
        "url": "http://export.arxiv.org/rss/cs.CL",
        "title": "arXiv cs.CL",
        "category": "papers",
        "description": "New papers in Computation and Language (NLP)",
    },
    {
        "url": "http://export.arxiv.org/rss/cs.CV",
        "title": "arXiv cs.CV",
        "category": "papers",
        "description": "New papers in Computer Vision",
    },
]
