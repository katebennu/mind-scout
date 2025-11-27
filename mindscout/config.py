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

# Curated RSS feeds for subscription suggestions
# Note: Some major AI company blogs don't have working RSS feeds (OpenAI, Anthropic, Meta AI, DeepMind)
CURATED_FEEDS = [
    # Tech Blogs
    {
        "url": "https://blog.google/technology/ai/rss/",
        "title": "Google AI Blog",
        "category": "tech_blog",
        "description": "AI research and product updates from Google"
    },
    {
        "url": "https://huggingface.co/blog/feed.xml",
        "title": "Hugging Face Blog",
        "category": "tech_blog",
        "description": "Open-source ML tools and research"
    },
    {
        "url": "https://lilianweng.github.io/index.xml",
        "title": "Lil'Log (Lilian Weng)",
        "category": "tech_blog",
        "description": "In-depth ML tutorials and explanations"
    },
    {
        "url": "https://pytorch.org/blog/feed.xml",
        "title": "PyTorch Blog",
        "category": "tech_blog",
        "description": "PyTorch updates, tutorials, and best practices"
    },
    # News & Analysis
    {
        "url": "https://www.technologyreview.com/feed/",
        "title": "MIT Technology Review",
        "category": "news",
        "description": "Technology news and analysis"
    },
    {
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "title": "Wired AI",
        "category": "news",
        "description": "AI coverage from Wired magazine"
    },
    {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "title": "TechCrunch AI",
        "category": "news",
        "description": "AI startup and industry news"
    },
    # Podcasts
    {
        "url": "https://lexfridman.com/feed/podcast/",
        "title": "Lex Fridman Podcast",
        "category": "podcast",
        "description": "In-depth conversations about AI, science, and technology"
    },
    {
        "url": "https://feeds.megaphone.fm/MLN2155636147",
        "title": "The TWIML AI Podcast",
        "category": "podcast",
        "description": "This Week in Machine Learning & AI"
    },
    {
        "url": "https://anchor.fm/s/1e4a0eac/podcast/rss",
        "title": "Machine Learning Street Talk",
        "category": "podcast",
        "description": "Technical ML discussions with researchers"
    },
    {
        "url": "https://feeds.simplecast.com/JGE3yC0V",
        "title": "Latent Space",
        "category": "podcast",
        "description": "AI engineering and research insights"
    },
    # Newsletters/Substacks
    {
        "url": "https://www.aisnakeoil.com/feed",
        "title": "AI Snake Oil",
        "category": "newsletter",
        "description": "Critical analysis of AI hype and reality"
    },
    {
        "url": "https://newsletter.ruder.io/feed",
        "title": "Sebastian Ruder's NLP Newsletter",
        "category": "newsletter",
        "description": "NLP research highlights and analysis"
    },
    # arXiv Categories (already in ARXIV_FEEDS but included for discoverability)
    {
        "url": "http://export.arxiv.org/rss/cs.AI",
        "title": "arXiv cs.AI",
        "category": "papers",
        "description": "New papers in Artificial Intelligence"
    },
    {
        "url": "http://export.arxiv.org/rss/cs.LG",
        "title": "arXiv cs.LG",
        "category": "papers",
        "description": "New papers in Machine Learning"
    },
    {
        "url": "http://export.arxiv.org/rss/cs.CL",
        "title": "arXiv cs.CL",
        "category": "papers",
        "description": "New papers in Computation and Language (NLP)"
    },
    {
        "url": "http://export.arxiv.org/rss/cs.CV",
        "title": "arXiv cs.CV",
        "category": "papers",
        "description": "New papers in Computer Vision"
    },
]
