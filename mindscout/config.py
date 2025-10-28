"""Configuration management for Mind Scout."""

import os
from pathlib import Path

# Base directory for Mind Scout data
DATA_DIR = Path(os.getenv("MINDSCOUT_DATA_DIR", Path.home() / ".mindscout"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database location
DB_PATH = DATA_DIR / "mindscout.db"

# arXiv RSS feeds by category
ARXIV_FEEDS = {
    "cs.AI": "http://export.arxiv.org/rss/cs.AI",  # Artificial Intelligence
    "cs.LG": "http://export.arxiv.org/rss/cs.LG",  # Machine Learning
    "cs.CL": "http://export.arxiv.org/rss/cs.CL",  # Computation and Language
    "cs.CV": "http://export.arxiv.org/rss/cs.CV",  # Computer Vision
}

# Default categories to fetch (user can customize later)
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
