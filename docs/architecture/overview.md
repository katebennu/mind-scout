# MindScout Architecture

## Current Architecture (Local Development)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           MindScout System                                │
└──────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐     │
│  │   Web UI     │        │  CLI Tools   │        │ Claude.app   │     │
│  │  (React +    │        │  (Terminal)  │        │  (Desktop)   │     │
│  │   Vite)      │        │              │        │              │     │
│  │              │        │              │        │              │     │
│  │ Port: 3000   │        │ mindscout    │        │   + MCP      │     │
│  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘     │
│         │                       │                       │              │
└─────────┼───────────────────────┼───────────────────────┼──────────────┘
          │                       │                       │
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Application Layer                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────┐              ┌─────────────────────────┐   │
│  │   FastAPI Backend      │              │   MCP Server            │   │
│  │   (REST API)           │              │   (stdio protocol)      │   │
│  │                        │              │                         │   │
│  │  Endpoints:            │              │  Tools:                 │   │
│  │  • /api/articles       │              │  • search_papers        │   │
│  │  • /api/profile        │              │  • get_article          │   │
│  │  • /api/search         │              │  • list_articles        │   │
│  │  • /api/recommendations│              │  • rate_article         │   │
│  │                        │              │  • mark_article_read    │   │
│  │  Port: 8000            │              │  • get_profile          │   │
│  └───────────┬────────────┘              │  • update_interests     │   │
│              │                           │  • fetch_articles       │   │
│              │                           └────────────┬────────────┘   │
│              │                                        │                │
│              └────────────────┬───────────────────────┘                │
│                               │                                        │
└───────────────────────────────┼────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Core Services Layer                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Database    │  │  VectorStore │  │ Recommender  │  │  Fetchers  │ │
│  │  (SQLite)    │  │  (ChromaDB)  │  │   Engine     │  │            │ │
│  │              │  │              │  │              │  │  • arXiv   │ │
│  │ Tables:      │  │ Embeddings:  │  │ Algorithms:  │  │  • S2      │ │
│  │ • articles   │  │ • Article    │  │ • Interest   │  │            │ │
│  │ • user_      │  │   vectors    │  │   matching   │  │            │ │
│  │   profile    │  │ • Semantic   │  │ • Citation   │  │            │ │
│  │              │  │   search     │  │   scoring    │  │            │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Services                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Anthropic    │  │   arXiv      │  │  Semantic    │                 │
│  │   Claude     │  │    API       │  │  Scholar     │                 │
│  │     API      │  │              │  │     API      │                 │
│  │              │  │ Papers:      │  │              │                 │
│  │ • LLM for    │  │ • RSS feeds  │  │ • Citations  │                 │
│  │   summaries  │  │ • Metadata   │  │ • Search     │                 │
│  │ • Processing │  │ • PDFs       │  │ • Metadata   │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Paper Fetching Flow

```
┌─────────┐
│  User   │
│ Request │
└────┬────┘
     │
     ▼
┌─────────────────┐
│ CLI / MCP Tool  │
│ fetch_articles  │
└────┬────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│         Fetcher Selection             │
│  if source == "arxiv"                │
│    → ArxivFetcher                    │
│  elif source == "semanticscholar"   │
│    → SemanticScholarFetcher          │
└────┬─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      External API Call               │
│  • Build query parameters            │
│  • Handle rate limiting              │
│  • Retry on failure                  │
│  • Parse response                    │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Data Normalization              │
│  • Extract metadata                  │
│  • Format dates                      │
│  • Clean text                        │
│  • Generate source_id                │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Database Storage                │
│  • Check for duplicates (source_id)  │
│  • Insert new articles               │
│  • Update existing if needed         │
│  • Return count of new articles      │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│    Vector Embedding (Optional)       │
│  • Generate embedding for abstract   │
│  • Store in ChromaDB                 │
│  • Enable semantic search            │
└─────────────────────────────────────┘
```

### 2. Semantic Search Flow

```
┌─────────┐
│  User   │
│  Query  │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│      VectorStore.semantic_search     │
│  Input: "transformers for NLP"       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Query Embedding                 │
│  • sentence-transformers             │
│  • Convert text → 384-dim vector     │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│    ChromaDB Vector Search            │
│  • Cosine similarity                 │
│  • Find top K similar embeddings     │
│  • Return article IDs + scores       │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│    Article Retrieval                 │
│  • Fetch full articles from DB       │
│  • Attach relevance scores           │
│  • Sort by relevance                 │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│    Return Results                    │
│  [{                                  │
│    article: {...},                   │
│    relevance: 0.87                   │
│  }]                                  │
└─────────────────────────────────────┘
```

### 3. Recommendation Flow

```
┌─────────┐
│  User   │
│ Profile │
└────┬────┘
     │
     ▼
┌─────────────────────────────────────┐
│   RecommendationEngine               │
│   get_recommendations()              │
└────┬────────────────────────────────┘
     │
     ├─────────────────┐
     ▼                 ▼
┌─────────────┐  ┌──────────────┐
│ Get User    │  │ Get Unread   │
│ Interests   │  │ Articles     │
│             │  │              │
│ • Topics    │  │ • Filter     │
│ • Skill     │  │   is_read=0  │
│   level     │  │ • Limit 100  │
└────┬────────┘  └──────┬───────┘
     │                  │
     └────────┬─────────┘
              ▼
┌─────────────────────────────────────┐
│      Scoring Algorithm               │
│                                      │
│  For each article:                   │
│    score = 0                         │
│                                      │
│    • Topic match: +20 per match      │
│    • Citation count: +10 if > 100    │
│    • Recent: +5 if < 30 days         │
│    • Source preference: +5           │
│                                      │
│    If semantic_search enabled:       │
│      • Similarity: +15 if > 0.7      │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Ranking & Filtering             │
│  • Sort by score (descending)        │
│  • Apply threshold (score >= 10)     │
│  • Limit to top N (default: 10)      │
│  • Attach reasons for recommendation │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│      Return Recommendations          │
│  [{                                  │
│    article: {...},                   │
│    score: 35,                        │
│    reasons: [                        │
│      "Matches: transformers",        │
│      "High citations: 250",          │
│      "Published this week"           │
│    ]                                 │
│  }]                                  │
└─────────────────────────────────────┘
```

### 4. MCP Integration Flow

```
┌─────────────────┐
│  Claude.app     │
│  (Desktop)      │
└────┬────────────┘
     │ stdio
     ▼
┌─────────────────────────────────────┐
│      MCP Server (FastMCP)            │
│                                      │
│  Server initialized with 9 tools     │
│  Connected to local database         │
└────┬────────────────────────────────┘
     │
     │ User: "Show me recent AI papers"
     │
     ▼
┌─────────────────────────────────────┐
│  Claude decides to use:              │
│  search_papers(                      │
│    query="recent AI papers",         │
│    limit=10                          │
│  )                                   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  MCP Tool Execution                  │
│  • Call VectorStore.semantic_search  │
│  • Retrieve articles from DB         │
│  • Format results as JSON            │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  Return to Claude                    │
│  Claude receives structured data     │
│  Formats natural language response   │
└────┬────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  User sees formatted response:       │
│                                      │
│  "I found 10 recent AI papers:       │
│   1. 'Attention Is All You Need'...  │
│   2. 'BERT: Pre-training...'...      │
│   ..."                               │
└─────────────────────────────────────┘
```

## Component Details

### Backend API (FastAPI)

**File**: `backend/main.py`

```python
Endpoints:
  GET  /api/articles              # List articles with pagination
  GET  /api/articles/{id}         # Get specific article
  POST /api/articles/search       # Semantic search
  GET  /api/recommendations       # Personalized recommendations
  GET  /api/profile               # User profile & stats
  PUT  /api/profile               # Update profile
  POST /api/profile/interests     # Update interests
```

**Technologies**:
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)
- CORS middleware (frontend access)

### MCP Server

**File**: `mcp-server/server.py`

```python
Tools (9 total):
  search_papers()           # Semantic search
  get_article()            # Get by ID
  list_articles()          # Browse with filters
  rate_article()           # Rate 1-5 stars
  mark_article_read()      # Update read status
  get_profile()            # View profile & stats
  update_interests()       # Update interests
  fetch_articles()         # Fetch from arXiv/S2
  get_recommendations()    # (implied, not shown)
```

**Technologies**:
- FastMCP (MCP framework)
- stdio communication
- Integrated with mindscout core

### Database (SQLite)

**File**: `mindscout/database.py`

```sql
Table: articles
  - id: Integer (PK)
  - source_id: String (unique)
  - source: String (arxiv, semanticscholar, rss)
  - title: String
  - authors: Text
  - abstract: Text
  - url: String
  - published_date: DateTime
  - fetched_date: DateTime
  - categories: String
  - citation_count: Integer
  - is_read: Boolean
  - rating: Integer (1-5)
  - embedding: Text (JSON)
  - source_name: String

Table: user_profile
  - id: Integer (PK)
  - interests: Text (comma-separated)
  - skill_level: String
  - preferred_sources: Text
  - daily_reading_goal: Integer

Table: rss_feeds
  - id: Integer (PK)
  - url: String (unique)
  - title: String
  - category: String
  - is_active: Boolean
  - check_interval: Integer
  - last_checked: DateTime

Table: notifications
  - id: Integer (PK)
  - article_id: Integer (FK)
  - feed_id: Integer (FK)
  - type: String (new_article, interest_match)
  - is_read: Boolean
  - created_date: DateTime
```

### Vector Store (ChromaDB)

**File**: `mindscout/vectorstore.py`

```python
Collection: "articles"
  - Embeddings: 384-dimensional vectors
  - Metadata: article_id, title, source
  - Model: all-MiniLM-L6-v2
  - Distance: Cosine similarity
```

### Fetchers

**Files**:
- `mindscout/fetchers/arxiv.py`
- `mindscout/fetchers/semanticscholar.py`

```python
ArxivFetcher:
  - arXiv API integration
  - Categories: cs.AI, cs.LG, cs.CV, cs.CL
  - Metadata extraction
  - Rate limiting with exponential backoff

SemanticScholarFetcher:
  - REST API integration
  - Citation data
  - Rate limiting with exponential backoff
  - Retry logic (3 attempts)

RSSFetcher:
  - Generic RSS/Atom feed parsing
  - Subscription management
  - Curated tech blog feeds
```

## Testing Architecture

```
┌─────────────────────────────────────┐
│         Test Suite                   │
├─────────────────────────────────────┤
│                                      │
│  tests/                              │
│  ├── test_fetch.py                   │
│  │   • Test arXiv fetching           │
│  │   • Test S2 fetching              │
│  │   • Mock API responses            │
│  │                                   │
│  ├── test_process.py                 │
│  │   • Test content processing       │
│  │   • Test LLM integration          │
│  │                                   │
│  └── test_mcp_server.py              │
│      • 21 tests (100% passing)       │
│      • Mock VectorStore              │
│      • Test all 9 MCP tools          │
│      • Database fixtures             │
│                                      │
│  Coverage: 14.09% total              │
│  MCP Server: 86.30%                  │
└─────────────────────────────────────┘
```

## File Structure

```
mindscout/
├── backend/                 # FastAPI REST API
│   ├── main.py             # App entry point
│   └── api/                # API routes
│       ├── articles.py     # Article endpoints
│       ├── profile.py      # Profile endpoints
│       ├── recommendations.py
│       └── search.py       # Search endpoints
│
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── services/       # API client
│   └── package.json
│
├── mcp-server/             # MCP integration
│   └── server.py           # 9 MCP tools
│
├── mindscout/              # Core Python library
│   ├── database.py         # SQLAlchemy models
│   ├── vectorstore.py      # ChromaDB integration
│   ├── recommender.py      # Recommendation engine
│   ├── fetchers/
│   │   ├── arxiv.py        # arXiv fetcher
│   │   ├── arxiv_advanced.py  # arXiv API fetcher
│   │   ├── semanticscholar.py  # S2 fetcher
│   │   ├── rss.py          # RSS/Atom fetcher
│   │   └── base.py         # Base fetcher class
│   └── processors/
│       ├── content.py      # Content processing
│       └── llm.py          # LLM integration
│
├── tests/                  # Test suite
│   ├── test_fetch.py
│   ├── test_process.py
│   └── test_mcp_server.py
│
├── scripts/                # Deployment scripts
│   └── deploy_gcp.sh
│
├── Dockerfile              # Container image
├── cloudbuild.yaml         # GCP CI/CD
├── requirements.txt        # Python deps
└── pyproject.toml          # Project config
```

## Deployment Architecture (Proposed GCP)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Google Cloud Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌───────────────┐                    │
│  │   Cloud      │         │  Cloud CDN    │                    │
│  │   Storage    │◄────────┤  (Global)     │◄───── Users       │
│  │  (Frontend)  │         └───────────────┘                    │
│  └──────────────┘                                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │            Cloud Run (Backend API)                │          │
│  │  • Auto-scaling (0-10 instances)                 │          │
│  │  • 512MB RAM, 1 vCPU per instance               │          │
│  │  • HTTPS automatic                               │          │
│  │  • Zero-downtime deployments                     │          │
│  └────────────┬─────────────────────────────────────┘          │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────┐     ┌─────────────────────┐          │
│  │   Cloud SQL          │     │  Secret Manager     │          │
│  │   (PostgreSQL 15)    │     │  • API keys         │          │
│  │   • db-f1-micro      │     │  • DB passwords     │          │
│  │   • 10GB SSD         │     │  • Session secrets  │          │
│  │   • Automated backup │     └─────────────────────┘          │
│  └──────────────────────┘                                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │         Cloud Scheduler (Cron Jobs)               │          │
│  │  • Daily paper fetching (9am UTC)                │          │
│  │  • Weekly cleanup tasks                          │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │         Cloud Build (CI/CD)                       │          │
│  │  • Trigger on git push                           │          │
│  │  • Build Docker image                            │          │
│  │  • Deploy to Cloud Run                           │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │       Cloud Logging & Monitoring                  │          │
│  │  • Centralized logs                              │          │
│  │  • Metrics & dashboards                          │          │
│  │  • Alerts & uptime checks                        │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

         ▲
         │
         │ API requests
         │
    ┌────┴─────┐
    │  Claude  │
    │ Desktop  │  (MCP server runs locally, calls Cloud API)
    └──────────┘
```

## Technology Stack Summary

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Material UI (MUI)
- **State**: React hooks
- **HTTP**: Fetch API

### Backend
- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite → PostgreSQL (prod)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2

### AI/ML
- **LLM**: Anthropic Claude (API)
- **Embeddings**: sentence-transformers
- **Vector DB**: ChromaDB
- **Model**: all-MiniLM-L6-v2

### External APIs
- arXiv API
- Semantic Scholar API
- Anthropic Claude API
- RSS/Atom feeds (various tech blogs)

### Development
- **Testing**: pytest, pytest-cov
- **Linting**: ruff
- **Formatting**: black
- **Type checking**: (future: mypy)

### Deployment (GCP)
- **Container**: Docker (multi-stage)
- **Compute**: Cloud Run (serverless)
- **Database**: Cloud SQL (PostgreSQL)
- **Storage**: Cloud Storage
- **CDN**: Cloud CDN
- **Secrets**: Secret Manager
- **CI/CD**: Cloud Build
- **Monitoring**: Cloud Logging/Monitoring

## Performance Characteristics

### Current (Local)
- **Article fetch**: ~2-5 seconds (20 papers)
- **Semantic search**: ~100-200ms
- **Recommendations**: ~50-100ms
- **Database queries**: <10ms (SQLite)

### Expected (Production GCP)
- **Cold start**: 2-3 seconds (first request)
- **Warm requests**: 50-200ms
- **Database**: 5-20ms (Cloud SQL)
- **Concurrent users**: 80 per instance
- **Max throughput**: ~4000 req/min (10 instances)

## Security Model

### Current
- Local only (no network exposure)
- API key in environment variable
- SQLite file permissions

### Production (GCP)
- HTTPS enforced
- Secrets in Secret Manager
- IAM roles (least privilege)
- VPC for database
- DDoS protection (Cloud Armor)
- Automated security updates
- Audit logging enabled
