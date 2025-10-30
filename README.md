# Mind Scout

Your AI research assistant that helps you stay on top of advances in AI.

Mind Scout uses agentic workflows to discover, process, and recommend AI research papers and articles tailored to your interests and reading history.

## Features

### 📚 Multi-Source Content Discovery
- **arXiv integration** - Fetch latest papers across AI categories (cs.AI, cs.LG, cs.CV, cs.CL)
- **Semantic Scholar** - Access citation data and find most-cited papers
- **Advanced search** - Filter by date, author, keywords, citations, and more
- **Beautiful CLI** - Rich terminal formatting with tables and panels

### 🤖 AI-Powered Intelligence
- **Smart summarization** - Claude 3.5 Haiku generates concise summaries
- **Automatic topic extraction** - AI identifies key topics and themes
- **Topic-based search** - Find papers by research area
- **Vector embeddings** - Foundation for semantic similarity (Phase 5)

### 🎯 Personalized Recommendations
- **User profiles** - Set your interests, skill level, and preferences
- **Smart recommendations** - Multi-factor scoring algorithm:
  - Topic matching with your interests (40%)
  - Citation impact and influence (25%)
  - Source preferences (15%)
  - Publication recency (10%)
  - Code availability bonus (10%)
- **Explainable AI** - See why each paper is recommended
- **Article ratings** - Rate papers 1-5 stars to improve recommendations

### 📊 Reading Analytics
- **Reading insights** - Track your reading habits and progress
- **Rating distribution** - See your rating patterns
- **Source breakdown** - Understand where you read from most
- **Daily goals** - Set and track reading targets

## Installation

```bash
# Clone the repository
cd mind-scout

# Install in development mode
pip install -e .

# Run migrations (if upgrading from earlier version)
python migrations/migrate_db_phase2.py
python migrations/migrate_db_phase3.py
python migrations/migrate_db_phase4.py
```

### Optional: AI Features Setup

To use AI-powered features (summarization, topic extraction), you need an Anthropic API key:

1. Get a key from https://console.anthropic.com/
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Quick Start

### 1. Set Up Your Profile

Tell Mind Scout what you're interested in:

```bash
# Set your research interests
mindscout profile set-interests "transformers, reinforcement learning, computer vision"

# Set your skill level
mindscout profile set-skill advanced

# View your profile
mindscout profile show
```

### 2. Discover Papers

Fetch papers from multiple sources:

```bash
# Quick fetch from arXiv (latest papers)
mindscout fetch -c cs.AI -c cs.LG

# Advanced search: Papers from last 30 days
mindscout search -k "large language models" --last-days 30

# Find high-impact papers (Semantic Scholar)
mindscout search --source semanticscholar -q "diffusion models" --min-citations 100 -n 20

# Filter by year and citations
mindscout search --source semanticscholar -q "GPT" --year 2024
```

### 3. Get Personalized Recommendations

Let Mind Scout suggest papers based on your interests:

```bash
# Get top 10 recommendations
mindscout recommend

# Get recommendations with detailed explanations
mindscout recommend --explain

# Include papers from last 60 days
mindscout recommend -d 60 -n 15
```

### 4. Read and Rate Papers

Track what you've read and rate papers:

```bash
# List unread articles
mindscout list --unread -n 20

# View article details (with citations if available)
mindscout show 5

# Mark as read
mindscout read 5

# Rate the paper (1-5 stars)
mindscout rate 5 4
```

### 5. Process with AI (Optional)

Use Claude to extract insights:

```bash
# Process articles for topic extraction
mindscout process --limit 10

# View discovered topics
mindscout topics

# Find articles by topic
mindscout find-by-topic "attention mechanism"
```

### 6. Track Your Progress

View your reading analytics:

```bash
# See your reading insights
mindscout insights

# View collection statistics
mindscout stats
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

### `mindscout search`
Universal search command supporting multiple sources (arXiv and Semantic Scholar).

Common Options:
- `--source`: Choose source - `arxiv` (default) or `semanticscholar`
- `-n, --max-results`: Maximum results (default: 100)
- `-q, --query`: Search query (required for Semantic Scholar)

**arXiv Options:**
- `-k, --keywords`: Keywords to search for
- `-c, --categories`: Filter by categories
- `-a, --author`: Search by author name
- `-t, --title`: Search in titles
- `--last-days N`: Fetch papers from last N days
- `--from-date YYYY-MM-DD`: Start date
- `--to-date YYYY-MM-DD`: End date
- `--sort-by`: Sort by `submittedDate`, `lastUpdatedDate`, or `relevance`
- `--sort-order`: `ascending` or `descending`

**Semantic Scholar Options:**
- `-q, --query`: Search query (required)
- `--ss-sort`: Sort order - `citationCount:desc` (default), `citationCount:asc`, `publicationDate:desc`, `publicationDate:asc`
- `--year YEAR`: Filter by year (e.g., "2024" or "2020-2024")
- `--min-citations N`: Minimum citation count

Examples:
```bash
# arXiv: Papers from last month about transformers
mindscout search -k "transformer" --last-days 30

# arXiv: Papers by specific author
mindscout search -a "Hinton" --last-days 365 -n 20

# Semantic Scholar: Most cited papers
mindscout search --source semanticscholar -q "large language models" -n 20

# Semantic Scholar: Filter by year and citations
mindscout search --source semanticscholar -q "transformers" --year 2024 --min-citations 100

# Semantic Scholar: Sort by recent papers
mindscout search --source semanticscholar -q "diffusion models" --ss-sort publicationDate:desc
```

**Note:** This unified command replaces the old `fetch-semantic-scholar` command. arXiv doesn't support citation-based sorting, but Semantic Scholar does!

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
Display full details of a specific article including abstract and citation data if available.

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

### `mindscout process`
Process articles with LLM for summarization and topic extraction (requires Anthropic API key).

Options:
- `--limit N`: Process at most N articles
- `--force`: Reprocess already processed articles

Example:
```bash
mindscout process --limit 10
```

### `mindscout topics`
Show all discovered topics from processed articles.

### `mindscout find-by-topic <topic>`
Find articles matching a specific topic.

Options:
- `--limit N`: Number of results to show (default: 10)

Example:
```bash
mindscout find-by-topic "reinforcement learning"
```

### `mindscout processing-stats`
Show processing progress and statistics.

### `mindscout profile`
Manage your user profile and preferences.

Subcommands:
- `show` - Display your current profile
- `set-interests <topics>` - Set interests (comma-separated)
- `add-interests <topics>` - Add interests without removing existing
- `set-skill <level>` - Set skill level (beginner/intermediate/advanced)
- `set-sources <sources>` - Set preferred sources (comma-separated)
- `set-goal <number>` - Set daily reading goal

Examples:
```bash
# View profile
mindscout profile show

# Set interests
mindscout profile set-interests "transformers, RL, NLP"

# Add more interests
mindscout profile add-interests "computer vision, GANs"

# Set skill level
mindscout profile set-skill advanced

# Set daily goal
mindscout profile set-goal 10
```

### `mindscout recommend`
Get personalized article recommendations based on your profile.

Options:
- `-n, --limit`: Number of recommendations (default: 10)
- `-d, --days`: Look back N days (default: 30)
- `--include-read`: Include already-read articles
- `--explain`: Show detailed explanation for top recommendation

Examples:
```bash
# Get top 10 recommendations
mindscout recommend

# Get 20 recommendations from last 60 days
mindscout recommend -n 20 -d 60

# Get recommendations with explanation
mindscout recommend --explain
```

### `mindscout rate <article_id> <rating>`
Rate an article from 1-5 stars.

Example:
```bash
# Rate article 42 as 5 stars
mindscout rate 42 5
```

### `mindscout insights`
Show reading insights and analytics including:
- Total articles, read count, and read percentage
- Articles rated and rating distribution
- Source breakdown for read articles
- Daily reading goal progress

Example:
```bash
mindscout insights
```

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

### Phase 3: Multi-Source Integration ✅ COMPLETE
- ✅ Semantic Scholar integration with citation data
- ✅ Citation-based search and sorting
- ✅ Unified search command across sources
- ⏳ Papers with Code (implementation links) - deferred
- ⏳ Hugging Face (community engagement metrics) - deferred

### Phase 4: User Profile & Recommendations ✅ COMPLETE
- ✅ User profile with interests and preferences
- ✅ Multi-factor recommendation algorithm
- ✅ Article rating system (1-5 stars)
- ✅ Reading insights and analytics
- ✅ Explainable recommendations

### Phase 5: Smart Recommendations (Next)
- Vector database integration (ChromaDB/Qdrant)
- Semantic similarity search
- LLM-powered relevance scoring
- Adaptive learning from feedback
- Weekly digest generation

### Phase 6: Web UI & Polish
- FastAPI backend
- React-based web interface
- Daily digest emails
- Export functionality

## Project Structure

```
mind-scout/
├── mindscout/              # Main package
│   ├── cli.py             # Command-line interface
│   ├── database.py        # SQLAlchemy models
│   ├── profile.py         # User profile management
│   ├── recommender.py     # Recommendation engine
│   ├── fetchers/          # Content fetchers (arXiv, Semantic Scholar)
│   └── processors/        # AI processors (LLM, embeddings)
├── migrations/            # Database migrations
├── tests/                 # Test suite
└── pyproject.toml         # Package configuration
```

See [STRUCTURE.md](STRUCTURE.md) for detailed architecture documentation.

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
