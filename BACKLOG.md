# Mind Scout - Feature Backlog

A prioritized list of features, improvements, and ideas for Mind Scout.

**Legend:**
- `[P0]` - High priority / Next up
- `[P1]` - Medium priority / Soon
- `[P2]` - Low priority / Nice to have
- `[P3]` - Ideas / Future consideration

---

## Core Features

### Fetch & Process Pipeline
- [ ] `[P0]` Unified fetch-and-process flow (fetch new articles, then process with LLM)
  - Trigger from UI (button/manual)
  - Trigger as scheduled background task (cron/scheduler)
  - Progress tracking and status reporting
  - Configurable schedule (hourly, daily, etc.)

### Content Sources
- [ ] `[P1]` Papers with Code integration (GitHub links, implementation status)
- [ ] `[P1]` Hugging Face daily papers integration
- [ ] `[P2]` YouTube AI channels (Yannic Kilcher, Two Minute Papers, etc.)
- [ ] `[P2]` AI podcast feeds (Lex Fridman, TWIML, Latent Space)
- [ ] `[P3]` Twitter/X integration for AI researchers
- [ ] `[P3]` Conference paper tracking (NeurIPS, ICML, ICLR, ACL)

### Recommendations
- [ ] `[P1]` Weekly/daily digest generation (email or in-app)
- [ ] `[P2]` Trending topics detection across sources
- [ ] `[P2]` "More like this" one-click recommendations
- [ ] `[P2]` Collaborative filtering (if multi-user support added)
- [ ] `[P3]` Reading time estimates based on paper length

### Organization
- [ ] `[P1]` Reading lists / collections (group papers by project/topic)
- [ ] `[P1]` Tags system (user-defined tags beyond auto-extracted topics)
- [ ] `[P2]` Notes/annotations on articles
- [ ] `[P2]` Export functionality (PDF, CSV, Markdown, BibTeX)
- [ ] `[P3]` Integration with Zotero/Mendeley

---

## Technical Improvements

### Performance & Scalability
- [ ] `[P0]` Test coverage improvements (fix failing tests, add new tests)
- [ ] `[P1]` Convert remaining sync endpoints to async
- [ ] `[P1]` Background task queue for long-running operations (Celery/ARQ)
- [ ] `[P2]` Redis caching for API responses
- [ ] `[P2]` Database connection pooling optimization
- [ ] `[P3]` PostgreSQL migration for production deployment

### Code Quality
- [ ] `[P0]` Fix Pydantic deprecation warnings (use ConfigDict)
- [ ] `[P0]` Fix SQLAlchemy deprecation warning (declarative_base)
- [ ] `[P1]` Add type hints throughout codebase
- [ ] `[P1]` API input validation improvements
- [ ] `[P2]` OpenTelemetry integration for observability
- [ ] `[P2]` Structured JSON logging

### Infrastructure
- [ ] `[P1]` Docker containerization
- [ ] `[P1]` docker-compose for local development
- [ ] `[P2]` CI/CD pipeline (GitHub Actions)
- [ ] `[P2]` Kubernetes/GKE deployment (see microservices plan)
- [ ] `[P3]` Terraform infrastructure as code

---

## Frontend / UI

### Web Interface
- [ ] `[P1]` Dark mode toggle
- [ ] `[P1]` Mobile responsive improvements
- [ ] `[P2]` Keyboard shortcuts for power users
- [ ] `[P2]` Infinite scroll for article list
- [ ] `[P2]` Article preview modal (quick view without leaving list)
- [ ] `[P3]` PWA support for offline reading

### Visualizations
- [ ] `[P2]` Reading analytics dashboard (charts, trends)
- [ ] `[P2]` Topic cloud visualization
- [ ] `[P2]` Citation network graph
- [ ] `[P3]` Paper similarity map (t-SNE/UMAP visualization)

---

## Integrations

### Browser Extensions
- [ ] `[P2]` Chrome extension for one-click save from arXiv/Scholar
- [ ] `[P2]` Firefox extension

### Third-Party Apps
- [ ] `[P2]` Notion integration (sync reading list)
- [ ] `[P2]` Obsidian plugin (link papers to notes)
- [ ] `[P3]` Slack/Discord bot for notifications
- [ ] `[P3]` Raycast/Alfred extension

### Export & Sync
- [ ] `[P1]` OPML export for RSS subscriptions
- [ ] `[P2]` Pocket/Instapaper integration
- [ ] `[P2]` ReadWise integration
- [ ] `[P3]` API webhooks for external integrations

---

## AI Enhancements

### LLM Features
- [ ] `[P1]` Paper comparison (compare two papers side-by-side)
- [ ] `[P1]` "Explain like I'm a beginner" mode for complex papers
- [ ] `[P2]` Generate related questions for each paper
- [ ] `[P2]` Auto-generate literature review from reading list
- [ ] `[P3]` Chat with your paper collection (RAG)

### Embedding & Search
- [ ] `[P1]` Upgrade to better embedding model (e.g., Cohere, Voyage)
- [ ] `[P2]` Hybrid search (keyword + semantic)
- [ ] `[P2]` Multi-lingual paper support
- [ ] `[P3]` Image/figure search within papers

---

## User Experience

### Onboarding
- [ ] `[P1]` First-run setup wizard
- [ ] `[P1]` Interest discovery from sample papers
- [ ] `[P2]` Import existing reading history

### Notifications
- [ ] `[P1]` Email digest opt-in
- [ ] `[P2]` Push notifications for high-priority papers
- [ ] `[P2]` Customizable notification preferences

### Accessibility
- [ ] `[P2]` Screen reader improvements
- [ ] `[P2]` High contrast mode
- [ ] `[P3]` Keyboard-only navigation

---

## Multi-User / SaaS (Future)

- [ ] `[P3]` User authentication (OAuth, magic links)
- [ ] `[P3]` Multi-tenant database
- [ ] `[P3]` Team/organization features
- [ ] `[P3]` Shared reading lists
- [ ] `[P3]` Usage analytics and billing

---

## Bug Fixes & Maintenance

- [ ] `[P0]` Fix test fixtures (list serialization for user_profile)
- [ ] `[P1]` Update datetime.utcnow() to timezone-aware
- [ ] `[P1]` Handle RSS feed fetch failures gracefully
- [ ] `[P2]` Improve error messages in API responses
- [ ] `[P2]` Add retry logic for external API failures

---

## Documentation

- [ ] `[P1]` API usage examples in README
- [ ] `[P1]` Contributing guide
- [ ] `[P2]` Architecture decision records (ADRs)
- [ ] `[P2]` Deployment guide
- [ ] `[P3]` Video walkthrough/demo

---

## Recently Completed

- [x] ~~Database session management (context manager)~~
- [x] ~~Error handling in fetchers (structured logging)~~
- [x] ~~Configuration management (pydantic-settings)~~
- [x] ~~API rate limiting (slowapi)~~
- [x] ~~Async database operations (SQLAlchemy async)~~
- [x] ~~RSS feed subscriptions~~
- [x] ~~Notification system for new articles~~
- [x] ~~Material UI frontend migration~~

---

## Notes

### How to Use This Backlog
1. Pick items from `[P0]` first - these are blocking or high-impact
2. `[P1]` items are good for regular development sessions
3. `[P2]` items are for when you have extra time or interest
4. `[P3]` items are "someday/maybe" - review periodically

### Adding New Items
When adding a new item:
1. Add it to the appropriate category
2. Assign a priority based on impact and urgency
3. Keep descriptions concise but clear

### Moving Items
- When starting work: move to a TODO list or issue tracker
- When completed: move to "Recently Completed" section
- Periodically archive old completed items

---

*Last updated: November 28, 2025*
