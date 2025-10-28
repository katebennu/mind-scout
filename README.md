# Mind Scout

Your AI research assistant that helps you stay on top of advances in AI.

Mind Scout uses agentic workflows to discover, process, and recommend AI research papers and articles tailored to your interests and reading history.

## Features

### Phase 1: Content Discovery ✅
- 📚 **Fetch articles** from arXiv across multiple AI categories
- 💾 **Local storage** with SQLite for all your articles
- 📖 **Track reading status** - mark articles as read/unread
- 🎨 **Beautiful CLI** with rich formatting and tables
- 📊 **Statistics** about your collection

### Phase 2: AI-Powered Analysis ✅ NEW!
- 🤖 **Smart summarization** with Claude 3.5 Haiku
- 🏷️ **Automatic topic extraction** from papers
- 🔍 **Topic-based search** to find relevant articles
- 📈 **Processing analytics** and progress tracking
- 💾 **Vector embeddings** (foundation for Phase 5 semantic search)

## Installation

```bash
# Clone the repository
cd mind-scout

# Install in development mode
pip install -e .

# (Optional) If upgrading from Phase 1, migrate database
python migrate_db_phase2.py
```

### Phase 2 Setup (Optional)

To use AI-powered features, you need an Anthropic API key:

1. Get a key from https://console.anthropic.com/
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Quick Start

### Basic Usage (Phase 1)

```bash
# Fetch latest articles from arXiv
mindscout fetch

# Fetch from specific categories
mindscout fetch -c cs.CV -c cs.AI

# List unread articles
mindscout list --unread

# Show details of a specific article
mindscout show 1

# Mark article as read
mindscout read 1

# View your statistics
mindscout stats
```

### AI-Powered Features (Phase 2)

```bash
# Process articles with Claude (requires API key)
mindscout process --limit 10

# View discovered topics
mindscout topics

# Find articles by topic
mindscout find-by-topic "transformer"

# Check processing progress
mindscout processing-stats
```

## Commands

### `mindscout fetch`
Fetch new articles from arXiv RSS feeds.

Options:
- `-c, --categories`: Specify categories to fetch (can be used multiple times)

Example:
```bash
mindscout fetch -c cs.AI -c cs.CV
```

### `mindscout list`
List articles in your database.

Options:
- `-u, --unread`: Show only unread articles
- `-n, --limit`: Number of articles to show (default: 10)
- `-s, --source`: Filter by source (e.g., arxiv)

Example:
```bash
mindscout list --unread --limit 20
```

### `mindscout show <article_id>`
Display full details of a specific article including abstract.

Example:
```bash
mindscout show 5
```

### `mindscout read <article_id>`
Mark an article as read.

### `mindscout unread <article_id>`
Mark an article as unread.

### `mindscout stats`
Show statistics about your article collection.

### `mindscout process` (Phase 2)
Process articles with LLM for summarization and topic extraction.

Options:
- `--limit N`: Process at most N articles
- `--force`: Reprocess already processed articles

Example:
```bash
mindscout process --limit 10
```

### `mindscout topics` (Phase 2)
Show all discovered topics from processed articles.

### `mindscout find-by-topic <topic>` (Phase 2)
Find articles matching a specific topic.

Options:
- `--limit N`: Number of results to show (default: 10)

Example:
```bash
mindscout find-by-topic "reinforcement learning"
```

### `mindscout processing-stats` (Phase 2)
Show processing progress and statistics.

## Configuration

Mind Scout stores data in `~/.mindscout/` by default. You can change this by setting the `MINDSCOUT_DATA_DIR` environment variable:

```bash
export MINDSCOUT_DATA_DIR=/path/to/your/data
```

### arXiv Categories

Currently supported categories:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CL` - Computation and Language (NLP)
- `cs.CV` - Computer Vision

## Roadmap

### Phase 1: Content Discovery ✅ COMPLETE
- ✅ arXiv RSS integration
- ✅ SQLite storage
- ✅ CLI interface
- ✅ Read tracking

### Phase 2: Content Processing Agent ✅ COMPLETE
- ✅ LLM-based summarization (Claude 3.5 Haiku)
- ✅ Automatic topic extraction and tagging
- ✅ Vector embeddings for semantic search (placeholder)
- ✅ Topic-based article search

### Phase 3: Memory System (Next)
- User profile and interests
- Basic recommendations
- Learning from feedback

### Phase 4: Multi-Agent Coordination
- Multiple content sources (Twitter, Hugging Face, etc.)
- Parallel fetching
- Deduplication

### Phase 5: Smart Recommendations
- Semantic similarity search
- LLM-powered relevance scoring
- Adaptive learning

### Phase 6: Web UI & Polish
- React-based web interface
- Daily digest emails
- Export functionality

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black mindscout

# Lint
ruff check mindscout
```

## License

MIT

## Contributing

This is a hobby project, but contributions are welcome! Feel free to open issues or submit pull requests.
