# Mind Scout - Project Structure

## Directory Layout

```
mind-scout/
├── mindscout/              # Main package
│   ├── __init__.py
│   ├── cli.py             # Command-line interface (argparse)
│   ├── config.py          # Configuration and constants
│   ├── database.py        # SQLAlchemy models (Article, UserProfile)
│   ├── profile.py         # User profile management
│   ├── recommender.py     # Recommendation engine
│   │
│   ├── fetchers/          # Content fetchers
│   │   ├── __init__.py
│   │   ├── base.py        # BaseFetcher abstract class
│   │   ├── arxiv.py       # Simple arXiv RSS fetcher
│   │   ├── arxiv_advanced.py  # Advanced arXiv API search
│   │   └── semanticscholar.py # Semantic Scholar with citations
│   │
│   └── processors/        # Content processors
│       ├── __init__.py
│       ├── llm.py         # LLM client wrapper (Anthropic Claude)
│       └── content.py     # Content processing logic
│
├── migrations/            # Database migrations
│   ├── README.md
│   ├── migrate_db_phase2.py  # LLM processing fields
│   ├── migrate_db_phase3.py  # Multi-source metadata
│   ├── migrate_db_phase4.py  # User profile and ratings
│   └── cli_old.py        # Old Click-based CLI (archived)
│
├── tests/                 # Test suite (planned)
│   ├── README.md
│   ├── test_fetch.py     # Fetcher tests
│   └── test_process.py   # Processor tests
│
├── pyproject.toml        # Package configuration and dependencies
├── README.md             # Main documentation
├── PROJECT_PLAN.md       # Development roadmap
├── STATUS.md             # Current status and progress
├── STRUCTURE.md          # This file
└── .gitignore

Data directory (not in repo):
~/.mindscout/
└── chroma/               # Vector database for semantic search
```

## Core Components

### CLI (`mindscout/cli.py`)
The main entry point for all user interactions. Built with argparse for reliability and ease of debugging.

**Key Commands:**
- Content: `fetch`, `search`, `list`, `show`
- Processing: `process`, `topics`, `find-by-topic`
- Profile: `profile {show,set-interests,add-interests,set-skill,set-sources,set-goal}`
- Recommendations: `recommend`, `rate`, `insights`
- Utility: `read`, `unread`, `stats`, `clear`

### Database (`mindscout/database.py`)
SQLAlchemy ORM models for data persistence.

**Models:**
- `Article` - Research papers with metadata, citations, ratings
- `UserProfile` - User preferences and settings

### Fetchers (`mindscout/fetchers/`)
Modular content fetchers following the BaseFetcher pattern.

**Implemented:**
- `ArxivFetcher` - Simple RSS-based fetching
- `ArxivAdvancedFetcher` - Advanced API search with filters
- `SemanticScholarFetcher` - Citation data and metrics

**Planned:**
- `PapersWithCodeFetcher` - Implementation links
- `HuggingFaceFetcher` - Community papers

### Processors (`mindscout/processors/`)
AI-powered content analysis using LLMs.

**Features:**
- Summarization (Claude 3.5 Haiku)
- Topic extraction
- Vector embeddings (placeholder for Phase 5)

### Recommendation Engine (`mindscout/recommender.py`)
Personalized paper recommendations with multi-factor scoring.

**Scoring Factors:**
- Topic matching (40%)
- Citation impact (25%)
- Source preference (15%)
- Recency (10%)
- Code availability (10%)

### Profile Management (`mindscout/profile.py`)
User preference management for personalization.

**Features:**
- Interest tracking
- Skill level setting
- Source preferences
- Daily reading goals

## Database Schema

### Articles Table
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    source_id VARCHAR UNIQUE,      -- e.g., arXiv ID
    source VARCHAR,                -- arxiv, semanticscholar
    title VARCHAR,
    authors TEXT,
    abstract TEXT,
    url VARCHAR,
    published_date DATETIME,
    fetched_date DATETIME,
    categories VARCHAR,
    is_read BOOLEAN,

    -- Phase 2: Processing
    summary TEXT,
    topics TEXT,                   -- JSON array
    embedding TEXT,                -- JSON array
    processed BOOLEAN,
    processing_date DATETIME,

    -- Phase 3: Multi-source
    citation_count INTEGER,
    influential_citations INTEGER,
    github_url VARCHAR,
    has_implementation BOOLEAN,
    paper_url_pwc VARCHAR,
    hf_upvotes INTEGER,

    -- Phase 4: Feedback
    rating INTEGER,                -- 1-5 stars
    rated_date DATETIME
);
```

### User Profile Table
```sql
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY,
    interests TEXT,                -- Comma-separated topics
    skill_level VARCHAR,           -- beginner/intermediate/advanced
    preferred_sources TEXT,        -- Comma-separated sources
    daily_reading_goal INTEGER,
    created_date DATETIME,
    updated_date DATETIME
);
```

## Development Workflow

### Adding a New Fetcher
1. Create class in `mindscout/fetchers/` extending `BaseFetcher`
2. Implement `fetch()` method returning normalized articles
3. Add CLI command in `cli.py`
4. Update documentation

### Adding Database Fields
1. Update model in `database.py`
2. Create migration script in `migrations/`
3. Test migration on sample database
4. Update documentation

### Adding CLI Commands
1. Create command function `cmd_name(args)` in `cli.py`
2. Add argument parser in `main()`
3. Set `func` default to command function
4. Update README with examples

## Configuration

**Environment Variables:**
- `ANTHROPIC_API_KEY` - For LLM features (optional)
- `MINDSCOUT_DATA_DIR` - Data directory (default: `~/.mindscout/`)

**Default Settings** (`mindscout/config.py`):
- Database path: `~/.mindscout/mindscout.db`
- Default categories: `cs.AI`, `cs.LG`, `cs.CL`, `cs.CV`
- LLM model: Claude 3.5 Haiku

## Dependencies

**Core:**
- `sqlalchemy` - Database ORM
- `requests` - HTTP client
- `feedparser` - RSS/Atom parsing
- `rich` - Terminal formatting

**AI Features:**
- `anthropic` - Claude API client
- `numpy` - Vector operations

**Development:**
- `pytest` - Testing framework
- `black` - Code formatting
- `ruff` - Linting

## Testing Strategy

**Unit Tests:**
- Fetcher parsing and normalization
- Recommendation scoring algorithms
- Profile management operations

**Integration Tests:**
- Database operations
- CLI command execution
- API interactions

**End-to-End Tests:**
- Complete user workflows
- Multi-step processes

## Future Enhancements

**Phase 5:**
- Vector database (ChromaDB/Qdrant)
- Semantic similarity search
- Advanced recommendations

**Phase 6:**
- FastAPI backend
- React frontend
- Web interface

See `PROJECT_PLAN.md` for detailed roadmap.
