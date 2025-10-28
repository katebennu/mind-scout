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

### Phase 2: AI-Powered Analysis ✅
- 🤖 **Smart summarization** with Claude 3.5 Haiku
- 🏷️ **Automatic topic extraction** from papers
- 🔍 **Topic-based search** to find relevant articles
- 📈 **Processing analytics** and progress tracking
- 💾 **Vector embeddings** (foundation for Phase 5 semantic search)

### Phase 3: Multi-Source Integration ✅ NEW!
- 📊 **Semantic Scholar** - Citation counts and metrics
- 🎯 **Citation-based search** - Find most cited papers
- 📚 **Multiple academic sources** in one place
- 🔢 **Impact tracking** with influential citation metrics

## Installation

```bash
# Clone the repository
cd mind-scout

# Install in development mode
pip install -e .

# (Optional) If upgrading from Phase 1, migrate database
python migrate_db_phase2.py

# (Optional) If upgrading to Phase 3, migrate database
python migrate_db_phase3.py
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

### Multi-Source Search (Phase 3)

```bash
# Fetch most cited papers from Semantic Scholar
mindscout fetch-semantic-scholar "large language models" -n 20

# Filter by year and minimum citations
mindscout fetch-semantic-scholar "transformers" --year 2024 --min-citations 100

# Sort by publication date instead of citations
mindscout fetch-semantic-scholar "GPT-4" --sort publicationDate:desc

# View citation data for articles
mindscout show 1  # Shows citation counts if available
```

## Commands

### `mindscout fetch`
Fetch latest articles from arXiv RSS feeds (simple, fast).

Options:
- `-c, --categories`: Specify categories to fetch (can be used multiple times)

Example:
```bash
mindscout fetch -c cs.AI -c cs.CV
```

### `mindscout search` (Advanced)
Search arXiv with advanced filters using the arXiv API.

Options:
- `-k, --keywords`: Keywords to search for
- `-c, --categories`: Filter by categories
- `-a, --author`: Search by author name
- `-t, --title`: Search in titles
- `--last-days N`: Fetch papers from last N days
- `--from-date YYYY-MM-DD`: Start date
- `--to-date YYYY-MM-DD`: End date
- `-n, --max-results`: Maximum results (default: 100)
- `--sort-by`: Sort by `submittedDate`, `lastUpdatedDate`, or `relevance`
- `--sort-order`: `ascending` or `descending`

Examples:
```bash
# Papers from last month about transformers
mindscout search -k "transformer" --last-days 30

# Papers by specific author from last year
mindscout search -a "Hinton" --last-days 365 -n 20

# Papers in specific categories with keywords
mindscout search -k "reinforcement learning" -c cs.AI cs.LG -n 50

# Papers from a date range sorted by relevance
mindscout search -k "diffusion" --from-date 2025-01-01 --to-date 2025-10-01 --sort-by relevance
```

**Note:** arXiv doesn't support sorting by citations. Use `--sort-by relevance` for most relevant papers based on search terms.

### `mindscout fetch-semantic-scholar` (Phase 3)
Fetch papers from Semantic Scholar with citation data and metrics.

Options:
- `-n, --max-results`: Maximum results (default: 50)
- `--sort`: Sort order - `citationCount:desc` (default), `citationCount:asc`, `publicationDate:desc`, `publicationDate:asc`
- `--year YEAR`: Filter by year (e.g., "2024" or "2020-2024")
- `--min-citations N`: Minimum citation count filter

Examples:
```bash
# Most cited papers about transformers
mindscout fetch-semantic-scholar "transformers" -n 20

# Recent papers from 2024 with at least 50 citations
mindscout fetch-semantic-scholar "large language models" --year 2024 --min-citations 50

# Papers sorted by publication date
mindscout fetch-semantic-scholar "neural networks" --sort publicationDate:desc -n 10
```

**Note:** This command provides the citation-based search that arXiv doesn't support. Great for finding high-impact papers!

### `mindscout list`
List articles in your database.

Options:
- `-u, --unread`: Show only unread articles
- `-n, --limit`: Number of articles to show (default: 10)
- `-s, --source`: Filter by source (e.g., arxiv, semanticscholar)

Example:
```bash
mindscout list --unread --limit 20
mindscout list -s semanticscholar  # Show only Semantic Scholar articles
```

### `mindscout show <article_id>`
Display full details of a specific article including abstract, and citation data if available (Phase 3).

Example:
```bash
mindscout show 5
```

### `mindscout read <article_id>`
Mark an article as read.

### `mindscout unread <article_id>`
Mark an article as unread.

### `mindscout stats`
Show statistics about your article collection, including source breakdown (arXiv, Semantic Scholar, etc.).

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

### `mindscout clear`
Clear all articles from the database.

Options:
- `--force`: Skip confirmation prompt

Example:
```bash
# With confirmation
mindscout clear

# Skip confirmation
mindscout clear --force
```

**Warning:** This permanently deletes all articles. Use with caution!

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

### Phase 3: Multi-Source Integration 🚧 IN PROGRESS
- ✅ Semantic Scholar integration with citation data
- ✅ Citation-based search and sorting
- 🚧 Papers with Code (implementation links)
- 🚧 Hugging Face (community engagement metrics)
- ⏳ Cross-source deduplication

### Phase 4: User Profile & Recommendations (Next)
- User profile and interests
- Basic recommendations
- Learning from feedback

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
