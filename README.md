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
- **Semantic search** - Natural language queries to find relevant papers
- **Similarity matching** - Find papers similar to ones you like

### 🎯 Personalized Recommendations
- **User profiles** - Set your interests, skill level, and preferences
- **Smart recommendations** - Multi-factor scoring algorithm:
  - Topic matching with your interests (35%)
  - Citation impact and influence (20%)
  - Skill level matching (15%)
  - Source preferences (10%)
  - Publication recency (10%)
  - Code availability bonus (10%)
- **Skill-adaptive filtering** - Recommendations tailored to your experience:
  - **Beginner**: Surveys, tutorials, well-established papers with implementations
  - **Intermediate**: Balanced mix of foundational and recent research
  - **Advanced**: Cutting-edge research, high-impact papers, novel contributions
- **Semantic recommendations** - Find papers using vector similarity:
  - Match papers to your interests semantically
  - Discover papers similar to ones you rated highly
- **Explainable AI** - See why each paper is recommended
- **Article ratings** - Rate papers 1-5 stars to improve recommendations

### 📊 Reading Analytics
- **Reading insights** - Track your reading habits and progress
- **Rating distribution** - See your rating patterns
- **Source breakdown** - Understand where you read from most
- **Daily goals** - Set and track reading targets

### 🌐 Web API & Frontend
- **FastAPI backend** - Production-ready REST API with 11 endpoints
- **React web UI** - Modern, responsive interface with Tailwind CSS
- **OpenAPI docs** - Auto-generated API documentation at `/docs`
- **CORS-enabled** - Ready for web and mobile frontends
- **Pagination & filtering** - Efficient data retrieval
- **Type-safe** - Pydantic models for request/response validation

### 🔌 MCP Server (New!)
- **Claude Desktop integration** - Access Mind Scout directly from Claude
- **9 AI tools** - Search, fetch, recommend, rate, and manage your library via AI
- **Natural language** - "Fetch new transformer papers from arXiv" just works
- **Fetch integration** - Ask Claude to fetch papers from arXiv or Semantic Scholar
- **Secure & local** - Runs on your machine, no data sent externally
- **Model Context Protocol** - Industry-standard AI integration (OpenAI, Google, Anthropic)

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

# For semantic search features, index your articles
mindscout index
```

### Optional: AI Features Setup

To use AI-powered features (summarization, topic extraction), you need an Anthropic API key:

1. Get a key from https://console.anthropic.com/
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Optional: Web API Setup

To run the web API server:

```bash
# Start the FastAPI server
python -m uvicorn backend.main:app --reload --port 8000

# API will be available at:
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/api/health
```

The API provides full access to all Mind Scout features via REST endpoints. See [API Documentation](#web-api-reference) below for details.

### Optional: MCP Server Setup (Claude Desktop)

To use Mind Scout with Claude Desktop or other MCP-compatible AI assistants:

```bash
# Install MCP SDK
pip install "mcp[cli]>=1.2.0"

# Add to Claude Desktop config file:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "mindscout": {
      "command": "python",
      "args": ["/path/to/agento/mcp-server/server.py"]
    }
  }
}

# Restart Claude Desktop
```

Once configured, you can ask Claude to search your library, get recommendations, rate papers, and more using natural language. See [mcp-server/README.md](mcp-server/README.md) for full documentation.

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

### 6. Use Semantic Search

Find papers using natural language and similarity:

```bash
# Index articles for semantic search (run once, or after fetching new papers)
mindscout index

# Search using natural language
mindscout semantic-search "attention mechanisms in transformers" -n 10

# Find papers similar to one you liked
mindscout similar 42 -n 5
```

### 7. Track Your Progress

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

### `mindscout index`
Index articles in the vector database for semantic search.

Options:
- `-n, --limit`: Index only N articles (useful for testing)
- `-f, --force`: Re-index articles that are already indexed

Examples:
```bash
# Index all articles
mindscout index

# Index only 50 articles (for testing)
mindscout index -n 50

# Re-index all articles
mindscout index --force
```

**Note:** Run this after fetching new articles to enable semantic search on them. Initial indexing may take a few minutes depending on the number of articles.

### `mindscout similar <article_id>`
Find articles semantically similar to a given article.

Options:
- `-n, --limit`: Number of similar articles to show (default: 10)
- `--min-similarity`: Minimum similarity score 0-1 (default: 0.3)

Examples:
```bash
# Find 5 articles similar to article 42
mindscout similar 42 -n 5

# Find similar articles with at least 50% similarity
mindscout similar 42 --min-similarity 0.5
```

### `mindscout semantic-search <query>`
Search for articles using natural language queries. Uses semantic similarity to find relevant papers even if they don't contain exact keywords.

Options:
- `-n, --limit`: Number of results to show (default: 10)

Examples:
```bash
# Search for papers about attention mechanisms
mindscout semantic-search "attention mechanisms in transformers"

# Find papers about a specific topic
mindscout semantic-search "diffusion models for image generation" -n 20

# Use natural language descriptions
mindscout semantic-search "how to train large language models efficiently"
```

**Note:** Semantic search finds papers based on meaning, not just keywords. This is more powerful than traditional keyword search.

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

### Phase 5: Smart Recommendations ✅ COMPLETE
- ✅ Vector database integration (ChromaDB)
- ✅ Semantic similarity search
- ✅ Natural language article search
- ✅ Find similar papers by ID
- ✅ Semantic recommendations based on interests and reading history
- ⏳ LLM-powered relevance scoring - deferred
- ⏳ Adaptive learning from feedback - deferred
- ⏳ Weekly digest generation - deferred

### Phase 6: Web UI & Polish (Backend Complete) ✅
- ✅ FastAPI backend with 11 REST endpoints
- ✅ OpenAPI documentation
- ✅ Pagination, filtering, and sorting
- ✅ Full CRUD operations for all features
- ✅ Type-safe with Pydantic models
- ⏳ React-based web interface - planned
- ⏳ Daily digest emails - planned
- ⏳ Export functionality - planned

## Project Structure

```
mind-scout/
├── mindscout/              # Main package (core logic)
│   ├── cli.py             # Command-line interface
│   ├── database.py        # SQLAlchemy models
│   ├── profile.py         # User profile management
│   ├── recommender.py     # Recommendation engine
│   ├── vectorstore.py     # Vector database for semantic search
│   ├── fetchers/          # Content fetchers (arXiv, Semantic Scholar)
│   └── processors/        # AI processors (LLM, embeddings)
├── backend/               # Web API (NEW - Phase 6)
│   ├── api/
│   │   ├── articles.py    # Article endpoints
│   │   ├── recommendations.py
│   │   ├── profile.py
│   │   └── search.py
│   └── main.py            # FastAPI application
├── migrations/            # Database migrations
├── tests/                 # Test suite
└── pyproject.toml         # Package configuration
```

See [STRUCTURE.md](STRUCTURE.md) for detailed architecture documentation.

## Web API Reference

Mind Scout provides a complete REST API for integration with web and mobile applications.

### Starting the API Server

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### API Endpoints

#### Articles

**List Articles**
```
GET /api/articles?page=1&page_size=20&unread_only=false&source=arxiv&sort_by=fetched_date&sort_order=desc
```

**Get Article**
```
GET /api/articles/{id}
```

**Mark as Read**
```
POST /api/articles/{id}/read
Body: {"is_read": true}
```

**Rate Article**
```
POST /api/articles/{id}/rate
Body: {"rating": 5}
```

#### Recommendations

**Get Recommendations**
```
GET /api/recommendations?limit=10&days_back=30&min_score=0.1
```

**Find Similar Articles**
```
GET /api/recommendations/{id}/similar?limit=10&min_similarity=0.3
```

**Semantic Recommendations**
```
GET /api/recommendations/semantic?limit=10&use_interests=true&use_reading_history=true
```

#### Profile

**Get Profile**
```
GET /api/profile
```

**Update Profile**
```
PUT /api/profile
Body: {
  "interests": ["transformers", "RL"],
  "skill_level": "advanced",
  "preferred_sources": ["arxiv", "semanticscholar"],
  "daily_reading_goal": 10
}
```

**Get Statistics**
```
GET /api/profile/stats
```

#### Search

**Semantic Search**
```
GET /api/search?q=attention mechanisms&limit=10
```

**Search Stats**
```
GET /api/search/stats
```

### Response Format

All endpoints return JSON. Example article response:

```json
{
  "id": 42,
  "title": "Attention is All You Need",
  "authors": "Vaswani et al.",
  "abstract": "...",
  "url": "https://arxiv.org/abs/1706.03762",
  "source": "arxiv",
  "published_date": "2017-06-12T00:00:00",
  "is_read": false,
  "rating": null,
  "citation_count": 50000,
  "has_implementation": true,
  "topics": "[\"Transformers\", \"Attention Mechanisms\"]"
}
```

### Error Responses

- `404` - Resource not found
- `400` - Invalid request (validation error)
- `500` - Internal server error

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

# Run API server (development mode)
uvicorn backend.main:app --reload
```

## License

MIT

## Contributing

This is a hobby project, but contributions are welcome! Feel free to open issues or submit pull requests.
