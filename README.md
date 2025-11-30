# Mind Scout

Your AI research assistant that helps you stay on top of advances in AI.

Mind Scout uses agentic workflows to discover, process, and recommend AI research papers and articles tailored to your interests and reading history.

## Features

### 📚 Multi-Source Content Discovery
- **arXiv integration** - Fetch latest papers across AI categories (cs.AI, cs.LG, cs.CV, cs.CL)
- **Semantic Scholar** - Access citation data and find most-cited papers
- **Advanced search** - Filter by date, author, keywords, citations, and more
- **Beautiful CLI** - Rich terminal formatting with tables and panels

### 📡 RSS Subscriptions
- **Subscribe to any RSS feed** - Tech blogs, newsletters, podcasts
- **Automatic notifications** - Get notified of new articles
- **Feed management** - Add, refresh, and manage subscriptions via UI or API

### 🤖 AI-Powered Intelligence
- **Smart summarization** - Claude 3.5 Haiku generates concise summaries
- **Automatic topic extraction** - AI identifies key topics and themes
- **Topic-based search** - Find papers by research area
- **Semantic search** - Natural language queries to find relevant papers
- **Similarity matching** - Find papers similar to ones you like

### 🔭 LLM Observability & Evaluation
- **Phoenix tracing** - Full observability for all LLM calls via Arize Phoenix
- **Cloud dashboard** - Monitor latency, token usage, and costs in real-time
- **Topic evaluation** - Evaluate quality of AI-extracted topics with LLM-as-judge
- **OpenTelemetry** - Industry-standard tracing with automatic Anthropic instrumentation

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
- **React web UI** - Modern, responsive interface with Material UI
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
# Install in development mode
pip install -e .

# Set up AI features (optional but recommended)
export ANTHROPIC_API_KEY='your-api-key-here'  # Get from https://console.anthropic.com/
```

## Quick Start

### Option 1: Web UI (Recommended)

Run both the backend API and React frontend:

```bash
# Terminal 1: Start the backend API
make api
# Or: python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start the React frontend
make frontend
# Or: cd frontend && npm run dev

# Open in browser (Vite typically uses port 5173)
open http://localhost:5173
```

The web UI provides a beautiful Material UI interface for browsing papers, getting recommendations, and tracking your reading.

**API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs.

### Option 2: Claude Desktop Integration (MCP)

Use Mind Scout directly from Claude Desktop using natural language:

```bash
# 1. Add to Claude Desktop config:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "mindscout": {
      "command": "python",
      "args": ["/absolute/path/to/mind-scout/mcp-server/server.py"]
    }
  }
}

# 2. Restart Claude Desktop

# 3. Ask Claude things like:
# - "Search my library for transformer papers"
# - "Get me 10 paper recommendations"
# - "Fetch new papers from arXiv about reinforcement learning"
# - "Rate that paper 5 stars"
```

**Full MCP documentation**: See [mcp-server/README.md](mcp-server/README.md)

### Option 3: CLI Interface

For power users who prefer the terminal:

```bash
# Set up your profile
mindscout profile set-interests "transformers, reinforcement learning"
mindscout profile set-skill advanced

# Fetch papers
mindscout fetch -c cs.AI -c cs.LG

# Get recommendations
mindscout recommend -n 10 --explain

# Search semantically
mindscout semantic-search "attention mechanisms in transformers"
```

**Full CLI reference**: See the [Commands](#commands) section below or visit the [documentation](docs/README.md).

## CLI Commands Reference

The CLI provides powerful commands for power users. Here are the most commonly used:

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `mindscout fetch` | Fetch papers from arXiv | `mindscout fetch -c cs.AI -c cs.LG` |
| `mindscout search` | Search arXiv or Semantic Scholar | `mindscout search -k "transformers" --last-days 30` |
| `mindscout list` | List articles | `mindscout list --unread -n 20` |
| `mindscout recommend` | Get personalized recommendations | `mindscout recommend -n 10 --explain` |

### Profile & Reading

| Command | Description | Example |
|---------|-------------|---------|
| `mindscout profile` | Manage profile and interests | `mindscout profile set-interests "NLP, RL"` |
| `mindscout read <id>` | Mark article as read | `mindscout read 42` |
| `mindscout rate <id> <1-5>` | Rate an article | `mindscout rate 42 5` |
| `mindscout insights` | View reading analytics | `mindscout insights` |

### Semantic Search

| Command | Description | Example |
|---------|-------------|---------|
| `mindscout index` | Index articles for search | `mindscout index` |
| `mindscout semantic-search` | Natural language search | `mindscout semantic-search "attention in transformers"` |
| `mindscout similar <id>` | Find similar papers | `mindscout similar 42 -n 5` |

### AI Processing

| Command | Description | Example |
|---------|-------------|---------|
| `mindscout process` | Extract topics with AI | `mindscout process --limit 10` |
| `mindscout topics` | View discovered topics | `mindscout topics` |
| `mindscout find-by-topic` | Search by topic | `mindscout find-by-topic "transformers"` |
| `mindscout evaluate` | Evaluate topic extraction quality | `mindscout evaluate -n 10 -v` |

For detailed command options and examples, run `mindscout <command> --help` or see the [full documentation](docs/README.md).

## Configuration

Create a `.env` file in the project root:

```bash
# Required for AI features
ANTHROPIC_API_KEY=your-anthropic-key

# Optional: Phoenix observability (get key from https://app.phoenix.arize.com)
MINDSCOUT_PHOENIX_API_KEY=your-phoenix-key
MINDSCOUT_PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/your-space
```

Other settings:
- **Data directory**: `~/.mindscout/` (set `MINDSCOUT_DATA_DIR` to change)
- **arXiv categories**: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`
- **Phoenix tracing**: Enabled by default when API key is set (disable with `MINDSCOUT_PHOENIX_ENABLED=false`)

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
- ✅ React-based web interface with Material UI
- ⏳ Daily digest emails - planned
- ⏳ Export functionality - planned

## Documentation

- **[Documentation Hub](docs/README.md)** - Complete documentation index
- **[Architecture](docs/architecture/diagrams.md)** - System design and diagrams
- **[Project Structure](docs/development/structure.md)** - Code organization
- **[Testing Guide](docs/development/testing.md)** - Running tests and coverage
- **[Development Status](docs/development/status.md)** - Current status and roadmap

## Web API

Mind Scout provides a complete REST API with 11 endpoints for articles, recommendations, profile, and search.

**Quick Start:**
```bash
make api  # Start the API server
open http://localhost:8000/docs  # View interactive API documentation
```

**Key Endpoints:**
- `GET /api/articles` - List and filter articles
- `GET /api/recommendations` - Get personalized recommendations
- `GET /api/search` - Semantic search
- `GET /api/profile` - User profile and stats

Full API documentation is available at `http://localhost:8000/docs` when the server is running.

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
