# Mind Scout - Project Plan

## Project Vision

Mind Scout is an AI research assistant that helps you stay on top of advances in AI through agentic workflows. It discovers, processes, and recommends AI research papers and articles tailored to your interests and reading history.

This is a hobby/portfolio project designed to showcase modern AI engineering practices, agentic architecture, and full-stack development skills.

## Core Architecture

### High-Level Components

1. **Content Discovery Agent** - Scrapes/fetches AI news from multiple sources
2. **Content Processor** - Extracts key information, summarizes, categorizes
3. **User Profile & Memory System** - Tracks reading history, interests, skill level
4. **Recommendation Engine** - Matches new content against user profile
5. **Interface Layer** - CLI and/or web UI for interaction

### Tech Stack

- **Language**: Python 3.9+
- **Database**: SQLite (Phase 1-3) → PostgreSQL (optional later)
- **Vector DB**: ChromaDB or Qdrant (Phase 5)
- **LLM**: Anthropic Claude or OpenAI GPT (Phase 2+)
- **Orchestration**: LangGraph or simple Python classes
- **CLI**: Click + Rich
- **Web**: FastAPI + React (Phase 6, optional)
- **Package Management**: pyproject.toml

## Phase Breakdown

---

### ✅ Phase 1: Basic Content Fetcher (4-6 hours) - COMPLETED

**Goal**: Establish foundation with single source integration

**Features**:
- [x] Project structure and package setup
- [x] SQLite database with Article model
- [x] arXiv RSS fetcher (cs.AI, cs.LG, cs.CL, cs.CV)
- [x] CLI with commands: fetch, list, show, read, unread, stats
- [x] Beautiful terminal output with Rich
- [x] Read/unread tracking

**Database Schema**:
```python
Article:
  - id (primary key)
  - source_id (unique, e.g., arXiv ID)
  - source (platform: arxiv, twitter, etc.)
  - title
  - authors
  - abstract
  - url
  - published_date
  - fetched_date
  - categories
  - is_read
```

**Portfolio Value**:
- API integration
- Database design with SQLAlchemy ORM
- CLI development
- Project structure and modularity

**Deliverables**:
- ✅ Working CLI tool
- ✅ 436 articles fetched
- ✅ Clean, documented codebase
- ✅ README and DEMO documentation

---

### 🔜 Phase 2: Content Processing Agent (6-8 hours)

**Goal**: Add intelligence with LLM-based content analysis

**Features**:
- [ ] LLM integration (Claude or GPT-4)
- [ ] Automatic summarization of abstracts
- [ ] Topic/keyword extraction
- [ ] Generate vector embeddings for articles
- [ ] Store embeddings in database
- [ ] New CLI command: `mindscout process` to analyze articles

**Database Changes**:
```python
Article (additions):
  - summary (LLM-generated, shorter than abstract)
  - topics (JSON or comma-separated tags)
  - embedding (vector representation)
  - processed (boolean flag)
  - processing_date
```

**New Components**:
```
mindscout/
└── processors/
    ├── __init__.py
    ├── llm.py          # LLM client wrapper
    └── content.py      # Content processing logic
```

**CLI Commands**:
```bash
mindscout process              # Process unprocessed articles
mindscout process --reprocess  # Reprocess all articles
mindscout topics               # List all discovered topics
```

**Portfolio Value**:
- LLM integration and prompt engineering
- Vector embeddings
- Batch processing
- API cost management

**Estimated Time**: 6-8 hours

---

### Phase 3: Multi-Source Integration (10-15 hours)

**Goal**: Add multiple high-quality AI research sources with citation data

**Features**:
- [ ] Semantic Scholar integration (citation counts & sorting!)
- [ ] Papers with Code integration (implementation links)
- [ ] Hugging Face daily papers integration
- [ ] Base fetcher class for consistency
- [ ] Multi-source coordination and deduplication
- [ ] Source-specific metadata (citations, GitHub links, etc.)

**New Database Columns** (extend Article table):
```python
Article (additions):
  - citation_count (INTEGER)         # From Semantic Scholar
  - influential_citations (INTEGER)  # From Semantic Scholar
  - github_url (VARCHAR)             # From Papers with Code
  - has_implementation (BOOLEAN)     # Has code available
  - paper_url_pwc (VARCHAR)          # Papers with Code URL
  - hf_upvotes (INTEGER)             # Hugging Face community votes
```

**New Fetchers**:
```
mindscout/
└── fetchers/
    ├── base.py              # Base fetcher class
    ├── arxiv.py             # Existing
    ├── arxiv_advanced.py    # Existing
    ├── semanticscholar.py   # NEW - With citations!
    ├── paperswithcode.py    # NEW - With implementations
    └── huggingface.py       # NEW - Community papers
```

**CLI Commands**:
```bash
# Fetch from specific sources
mindscout fetch-semantic-scholar -k "transformers" -n 50 --sort-citations
mindscout fetch-papers-with-code -k "diffusion"
mindscout fetch-huggingface --daily

# List by citations
mindscout list --sort-by citations --limit 20

# Show with enhanced metadata
mindscout show 123  # Now includes citations, GitHub links
```

**Portfolio Value**:
- Multi-source integration
- API integration variety
- Data enrichment
- Citation tracking
- Code-paper linking

**Estimated Time**: 10-15 hours

---

### Phase 4: User Profile & Recommendations (8-10 hours)

**Goal**: Personalized recommendations based on reading history

**Features**:
- [ ] User profile configuration
- [ ] Interest tracking (topics user cares about)
- [ ] Skill level tracking (beginner/intermediate/advanced)
- [ ] Reading history analytics
- [ ] Basic recommendation algorithm
- [ ] Feedback mechanism (thumbs up/down)

**New Database Tables**:
```python
UserProfile:
  - interests, skill_level, preferred_sources

ReadingHistory:
  - article_id, read_date, rating

Recommendation:
  - article_id, score, reason
```

**Estimated Time**: 8-10 hours

---

### Phase 5: Smart Recommendations (8-12 hours)

**Goal**: Advanced recommendation engine with semantic search

**Features**:
- [ ] Vector database integration (ChromaDB/Qdrant)
- [ ] Semantic similarity search
- [ ] LLM-powered relevance scoring
- [ ] Learning from user feedback
- [ ] Explanation generation (why this recommendation?)
- [ ] Weekly digest generation
- [ ] Trending topics detection

**Vector DB Integration**:
```python
# Store embeddings in ChromaDB/Qdrant
# Support queries like:
- "Find papers similar to this one"
- "Papers about diffusion models"
- "Latest advances in RL"
```

**Enhanced Recommendation Engine**:
```python
SmartRecommender:
  - Semantic search via vector DB
  - LLM scoring for relevance
  - Feedback-based learning
  - Diversity in recommendations
  - Novelty detection
  - Explanation generation
```

**CLI Commands**:
```bash
mindscout recommend --explain           # Show why each is recommended
mindscout similar <article_id>          # Find similar articles
mindscout search "diffusion models"     # Semantic search
mindscout digest --weekly               # Generate weekly digest
mindscout trending                      # Show trending topics
```

**Portfolio Value**:
- Vector databases
- RAG pattern implementation
- Advanced recommendation systems
- ML feedback loops

**Estimated Time**: 8-12 hours

---

### Phase 6: Web UI & Polish (10-15 hours) - OPTIONAL

**Goal**: Professional web interface and production features

**Features**:
- [ ] FastAPI backend
- [ ] React frontend
- [ ] User authentication
- [ ] Visual article cards
- [ ] Interactive recommendation feed
- [ ] Email digest service
- [ ] Export functionality (PDF, CSV, Markdown)
- [ ] Dark mode
- [ ] Mobile responsive

**Tech Stack**:
- Backend: FastAPI
- Frontend: React + Vite
- UI: Tailwind CSS or Material-UI
- State: React Query
- Email: SendGrid or AWS SES

**API Endpoints**:
```
GET  /api/articles              # List articles
GET  /api/articles/:id          # Get article details
POST /api/articles/:id/read     # Mark as read
GET  /api/recommendations       # Get recommendations
POST /api/feedback              # Submit feedback
GET  /api/profile               # Get user profile
PUT  /api/profile               # Update profile
GET  /api/search                # Semantic search
```

**Portfolio Value**:
- Full-stack development
- REST API design
- Modern frontend skills
- Production deployment

**Estimated Time**: 10-15 hours

---

## Implementation Guidelines

### Best Practices

1. **Modularity**: Each phase should be self-contained and functional
2. **Testing**: Write tests for core functionality
3. **Documentation**: Update README after each phase
4. **Git**: Commit frequently with clear messages
5. **Error Handling**: Graceful degradation, never crash
6. **Logging**: Comprehensive logging for debugging

### Development Workflow

```bash
# Start new phase
git checkout -b phase-X-description

# Develop features
# ... code, test, iterate ...

# Complete phase
git commit -m "Complete Phase X: description"
git checkout main
git merge phase-X-description

# Tag release
git tag v0.X.0
```

### Testing Strategy

- Unit tests for core logic (fetchers, processors)
- Integration tests for database operations
- End-to-end tests for CLI commands
- Manual testing for UX

### Cost Management

**LLM API Costs** (Phase 2+):
- Use cheaper models for bulk processing (Claude Haiku, GPT-3.5)
- Cache results to avoid reprocessing
- Batch API calls when possible
- Set monthly budget limits

**Estimated Costs** (processing 1000 articles):
- Summarization: ~$1-5 with Haiku/GPT-3.5
- Embeddings: ~$0.10-1 with text-embedding-3-small
- Recommendations: Minimal (mostly vector search)

---

## Success Metrics

### Technical Metrics
- [ ] All phases complete and functional
- [ ] Clean, well-documented code
- [ ] Comprehensive README
- [ ] Working demo

### Portfolio Metrics
- [ ] Demonstrates modern AI engineering
- [ ] Shows full-stack capabilities (if Phase 6)
- [ ] Production-quality code
- [ ] Deployable system

### Personal Metrics
- [ ] Actually use the tool daily
- [ ] Learn something new from recommendations
- [ ] Save time staying current with AI research

---

## Current Status

**Phase**: 1 of 6
**Progress**: Phase 1 ✅ Complete
**Next**: Phase 2 - Content Processing Agent
**Timeline**: ~4-6 hours invested, ~38-56 hours remaining

**Last Updated**: October 27, 2025

---

## Notes & Ideas

### Future Enhancements (Beyond Phase 6)
- Browser extension for one-click saves
- Integration with Zotero/Mendeley
- Podcast and video content (YouTube, podcasts)
- Social features (share recommendations)
- Mobile app
- Slack/Discord bot integration
- Notion/Obsidian sync

### Technical Debt to Address
- [ ] Fix cosmetic CLI error in `mindscout fetch` command
- [ ] Add proper logging instead of print statements
- [ ] Implement retry logic for API failures
- [ ] Add rate limiting for arXiv requests
- [ ] Create proper test suite

### Research Questions
- Best embedding model for academic papers?
- Optimal vector DB for this use case?
- How to handle multimodal content (papers with images)?
- Privacy considerations for user data?

---

## Resources

### Documentation
- arXiv API: https://arxiv.org/help/api
- ChromaDB docs: https://docs.trychroma.com
- LangGraph: https://langchain-ai.github.io/langgraph
- FastAPI: https://fastapi.tiangolo.com

### Inspiration
- Papers With Code: https://paperswithcode.com
- Hugging Face Daily Papers: https://huggingface.co/papers
- AI Alignment Newsletter
- Import AI Newsletter

---

## Contact & Contributions

**Author**: Kate
**Repository**: /Users/kate/projects/agento
**License**: MIT

This is a personal hobby project, but ideas and contributions are welcome!
