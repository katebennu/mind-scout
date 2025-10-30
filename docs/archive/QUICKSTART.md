# Mind Scout - Quick Start Guide

## 🚀 Getting Back Up to Speed

When you return to this project, here's everything you need to know in 2 minutes:

---

## Current State

**Phase**: 1/6 Complete ✅
**Articles in DB**: 436
**Status**: Ready for Phase 2

---

## Essential Commands

```bash
# View latest articles
mindscout list --unread --limit 10

# Read an article
mindscout show 5

# Mark as read
mindscout read 5

# Check stats
mindscout stats

# Fetch new articles (use test script due to cosmetic CLI bug)
python test_fetch.py
```

---

## Project Files

| File | Purpose |
|------|---------|
| `PROJECT_PLAN.md` | Full 6-phase roadmap with detailed specs |
| `STATUS.md` | Current state, schema, dependencies, known issues |
| `README.md` | User documentation and CLI guide |
| `DEMO.md` | Feature walkthrough and demo script |
| `QUICKSTART.md` | This file - quick reference |

---

## Starting Phase 2

### What Phase 2 Adds
- LLM integration for summarization
- Topic extraction
- Vector embeddings
- Article processing pipeline

### Before You Start
1. Choose LLM provider:
   - **Anthropic Claude** (Recommended): Best quality, good pricing
   - **OpenAI GPT-4o**: Alternative option
   - **Claude Haiku**: Cheapest for bulk processing

2. Get API key:
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   # OR
   export OPENAI_API_KEY="your-key-here"
   ```

3. Review Phase 2 plan:
   ```bash
   # See PROJECT_PLAN.md lines 100-180 for full details
   ```

### Step-by-Step Phase 2

1. **Install LLM library**
   ```bash
   # Add to pyproject.toml dependencies
   pip install anthropic  # or openai
   ```

2. **Update database schema**
   ```python
   # Add to Article model in database.py:
   summary = Column(Text)           # LLM summary
   topics = Column(Text)            # JSON array
   embedding = Column(Text)         # Vector embedding
   processed = Column(Boolean)      # Processing flag
   processing_date = Column(DateTime)
   ```

3. **Create processors module**
   ```
   mindscout/
   └── processors/
       ├── __init__.py
       ├── llm.py       # LLM client
       └── content.py   # Processing logic
   ```

4. **Add CLI command**
   ```python
   @main.command()
   def process():
       """Process unprocessed articles."""
       # Implementation
   ```

5. **Test and iterate**

---

## Architecture Reminder

```
Mind Scout = Content Discovery + Processing + Memory + Recommendations

Phase 1: ✅ Content Discovery (arXiv)
Phase 2: 🔜 Processing (LLM)
Phase 3: ⏳ Memory (User profile)
Phase 4: ⏳ Multi-agent (Multiple sources)
Phase 5: ⏳ Recommendations (Smart matching)
Phase 6: ⏳ Web UI (Optional polish)
```

---

## Key Design Decisions

### Why These Choices?

| Choice | Rationale |
|--------|-----------|
| SQLite | Simple, portable, perfect for single-user |
| Click + Rich | Modern CLI with great UX |
| Modular structure | Each phase extends cleanly |
| arXiv first | Free API, no rate limits, high-quality content |
| LLM in Phase 2 | Core value-add, enables all later features |

---

## Time Estimates

| Phase | Estimated Time | Status |
|-------|---------------|--------|
| 1: Basic Fetcher | 4-6 hours | ✅ Done (actual: ~5 hours) |
| 2: LLM Processing | 6-8 hours | 🔜 Next |
| 3: User Profile | 8-10 hours | ⏳ Planned |
| 4: Multi-Agent | 6-8 hours | ⏳ Planned |
| 5: Smart Recs | 8-12 hours | ⏳ Planned |
| 6: Web UI | 10-15 hours | ⏳ Optional |
| **Total** | **42-59 hours** | **~10% complete** |

---

## Common Issues & Solutions

### Issue: CLI fetch shows error
**Solution**: It's cosmetic, use `python test_fetch.py`

### Issue: DB location unclear
**Solution**: `~/.mindscout/mindscout.db`

### Issue: Want to reset DB
**Solution**: `rm ~/.mindscout/mindscout.db && mindscout stats`

---

## Development Workflow

```bash
# 1. Start new feature branch
git checkout -b phase-2-content-processing

# 2. Make changes, test frequently
mindscout <command>

# 3. Commit often
git commit -m "Add LLM summarization"

# 4. Complete phase
git checkout main
git merge phase-2-content-processing
git tag v0.2.0
```

---

## Testing Checklist

Before considering a phase "done":

- [ ] All features work via CLI
- [ ] No crashes or unhandled errors
- [ ] Database migrations successful
- [ ] Documentation updated
- [ ] Demo script works
- [ ] Status.md reflects changes

---

## Portfolio Story

**The Pitch**:
"Mind Scout is an AI research assistant that helps you stay current with AI advances. It uses agentic workflows to discover, analyze, and recommend papers based on your interests. Built in Python with LLMs, vector search, and a beautiful CLI."

**What It Shows**:
- Modern AI engineering (RAG, agents, LLMs)
- System design (modular, scalable)
- Full-stack skills (backend → frontend)
- Product thinking (real problem, phased approach)
- Code quality (clean, documented, tested)

---

## Useful Snippets

### Check article count
```python
from mindscout.database import get_session, Article
print(get_session().query(Article).count())
```

### Fetch from specific category
```python
from mindscout.fetchers.arxiv import fetch_arxiv
fetch_arxiv(["cs.CV"])
```

### View recent articles
```python
from mindscout.database import get_session, Article
session = get_session()
for a in session.query(Article).order_by(Article.id.desc()).limit(5):
    print(f"{a.id}: {a.title}")
```

---

## Next Session Checklist

When you sit down to work on Phase 2:

- [ ] Read PROJECT_PLAN.md Phase 2 section
- [ ] Decide: Anthropic or OpenAI?
- [ ] Get API key
- [ ] Update pyproject.toml with LLM library
- [ ] Create processors/ directory
- [ ] Update database schema
- [ ] Start with simple summarization test
- [ ] Build from there!

---

## Questions? Check These Files

- **How to use?** → README.md
- **What's the plan?** → PROJECT_PLAN.md
- **What's working?** → STATUS.md
- **What's next?** → PROJECT_PLAN.md (Phase 2 section)
- **Quick demo?** → DEMO.md

---

**Ready to build Phase 2? Let's make this AI assistant intelligent! 🧠**

Run `mindscout stats` to see your current collection and dive in!
