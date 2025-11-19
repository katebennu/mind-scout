# Architecture Documentation Maintenance Guide

## 🎯 Quick Start

### One-Time Setup

```bash
# Install the git hook (auto-checks for diagram updates)
./scripts/setup_git_hooks.sh

# Optional: Install Mermaid CLI for diagram validation
npm install -g @mermaid-js/mermaid-cli
```

That's it! Now every time you commit architecture-sensitive changes, you'll be reminded to update diagrams.

---

## 📝 When to Update Diagrams

### Always Update When You:

✅ **Add a new component**
- New service, module, or class that interacts with other parts
- Example: Adding a caching layer

✅ **Change data flow**
- How data moves between components
- Example: Adding a message queue between services

✅ **Add/modify API endpoints**
- New REST endpoints
- New MCP tools
- Example: Adding `POST /api/articles/bulk`

✅ **Modify database schema**
- New tables
- New columns with relationships
- Example: Adding `notifications` table

✅ **Change deployment architecture**
- New cloud service
- Different scaling strategy
- Example: Adding Redis to GCP deployment

✅ **Add new dependencies**
- New framework or library that changes how things work
- Example: Switching from SQLite to PostgreSQL

### Maybe Update When You:

⚠️ **Refactor internal logic**
- If the component interface stays the same, diagrams might not need updates
- If relationships change, update diagrams

⚠️ **Add helper functions**
- If they don't change architecture, skip diagram updates
- If they represent a new pattern, consider updating

---

## 🔄 Workflow

### Standard Process

```bash
# 1. Make your code changes
vim backend/main.py

# 2. Before committing, ask yourself:
#    "Did I change how components interact?"

# 3. If yes, update diagrams
vim ARCHITECTURE_DIAGRAM.md

# 4. Stage everything
git add backend/main.py ARCHITECTURE_DIAGRAM.md

# 5. Commit
git commit -m "feat: add bulk article import endpoint

- Added POST /api/articles/bulk endpoint
- Updated API architecture diagram
"
```

### The Hook Will Help

When you commit, if you modified architecture files, you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  Architecture Documentation Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You've modified architecture-sensitive files:

  📝 backend/api/

❌ ARCHITECTURE_DIAGRAM.md was NOT updated

Consider updating the architecture diagrams:

  1. Review .claude/instructions.md for guidance
  2. Update relevant diagrams in ARCHITECTURE_DIAGRAM.md
  3. Stage the changes: git add ARCHITECTURE_DIAGRAM.md

Continue commit without updating diagrams? (y/N)
```

---

## 📊 Which Diagram to Update?

### Quick Reference Table

| You Changed... | Update These Diagrams |
|----------------|----------------------|
| Added new API endpoint | • API Endpoints Architecture<br/>• System Overview (if major) |
| Added new MCP tool | • MCP Tools Mindmap<br/>• MCP Server Integration |
| Changed database schema | • Database Schema (ERD)<br/>• System Overview |
| Modified recommendation logic | • Recommendation Engine Flow |
| Added new fetcher | • Paper Fetching Flow<br/>• System Overview |
| Changed deployment | • GCP Deployment Architecture<br/>• CI/CD Pipeline |
| Added new dependency | • Technology Stack |
| Changed data flow | • Relevant sequence diagram |

---

## ✏️ How to Update Diagrams

### Example 1: Adding a New API Endpoint

**Change**: Added `POST /api/articles/export`

**Update**: API Endpoints Architecture diagram

```mermaid
# Find this section in ARCHITECTURE_DIAGRAM.md
subgraph "Client Requests"
    C1[GET /api/articles]
    C2[GET /api/articles/:id]
    # ADD THIS LINE:
    C6[POST /api/articles/export]
end

subgraph "FastAPI Routes"
    R1[articles.list_articles]
    R2[articles.get_article]
    # ADD THIS LINE:
    R6[articles.export_articles]
end

# ADD THIS CONNECTION:
C6 --> R6 --> DB
```

### Example 2: Adding a Database Table

**Change**: Added `notifications` table

**Update**: Database Schema (ERD)

```mermaid
erDiagram
    ARTICLES {
        int id PK
        ...existing fields...
    }

    %% ADD THIS TABLE:
    NOTIFICATIONS {
        int id PK
        int user_id FK
        int article_id FK
        string type
        boolean read
        datetime created_at
    }

    %% ADD THIS RELATIONSHIP:
    ARTICLES ||--o{ NOTIFICATIONS : "generates"
```

### Example 3: Adding a Cloud Service

**Change**: Added Redis (Memorystore) to GCP

**Update**: GCP Deployment Architecture

```mermaid
subgraph "Data Layer"
    SQL[(Cloud SQL<br/>PostgreSQL)]

    %% ADD REDIS:
    REDIS[(Memorystore<br/>Redis<br/>Caching)]
end

%% ADD CONNECTION:
CR --> REDIS
```

---

## 🛠️ Tools

### Preview Diagrams

**Option 1: VS Code**
```bash
# Install extension
code --install-extension bierner.markdown-mermaid

# Open file
code ARCHITECTURE_DIAGRAM.md
# Press Cmd+Shift+V to preview
```

**Option 2: Online (Mermaid Live)**
```bash
# Copy diagram code
# Paste into: https://mermaid.live
# Edit and preview in real-time
```

**Option 3: CLI (Export)**
```bash
# Export to PNG
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png

# Export to SVG (scalable)
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.svg

# Export to PDF
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.pdf
```

### Validate Syntax

```bash
# Install validator
npm install -g @mermaid-js/mermaid-cli

# Validate (automatically done by git hook if installed)
mmdc -i ARCHITECTURE_DIAGRAM.md -o /tmp/test.png
```

---

## 🎨 Style Guide

### Use Consistent Colors

```mermaid
%% User interfaces
style UI fill:#e1f5ff

%% Application layer
style API fill:#fff4e1

%% Data/services
style DB fill:#e8f5e9

%% External APIs
style EXTERNAL fill:#fce4ec

%% Monitoring
style MONITOR fill:#f3e5f5
```

### Naming Conventions

- **Nodes**: UPPERCASE_WITH_UNDERSCORES
- **Labels**: "Readable Title Case"
- **IDs**: descriptive (e.g., `BACKEND_API` not `A1`)

### Diagram Size

- Keep diagrams focused (one concept per diagram)
- If >20 nodes, consider splitting into multiple diagrams
- Use subgraphs to organize complex diagrams

---

## 📚 Examples

### Good Commit Messages

```
✅ feat: add Redis caching layer

- Added Redis for API response caching
- Updated system overview diagram
- Updated GCP deployment diagram
- Updated tech stack diagram
```

```
✅ refactor: split article API into microservices

- Split monolithic API into article-service and search-service
- Updated API architecture showing new services
- Updated deployment diagram with service mesh
- Updated component interaction matrix
```

### Bad Commit Messages

```
❌ feat: add caching
   (No diagram updates mentioned, readers don't know what changed)
```

```
❌ docs: update diagrams
   (No context - what changed in the code?)
```

---

## 🚨 Common Mistakes

### ❌ Don't Do This

1. **Committing code without updating diagrams**
   ```bash
   # Bad
   git add backend/
   git commit -m "add new feature"
   # (Diagrams are now out of sync!)
   ```

2. **Updating diagrams in a separate commit**
   ```bash
   # Bad
   git commit -m "feat: add feature X"
   git commit -m "docs: update diagrams"
   # (History is split, harder to track what changed)
   ```

3. **Making diagrams too detailed**
   ```mermaid
   # Bad - too much detail
   A --> B[Function calls helper1]
   B --> C[helper1 calls helper2]
   C --> D[helper2 calls helper3]
   # (Lost in implementation details)
   ```

### ✅ Do This Instead

1. **Update diagrams with code**
   ```bash
   # Good
   git add backend/ ARCHITECTURE_DIAGRAM.md
   git commit -m "feat: add feature X

   - Implementation details
   - Updated architecture diagrams
   "
   ```

2. **Keep diagrams at the right level**
   ```mermaid
   # Good - shows component interaction
   API --> CacheLayer
   CacheLayer --> Database
   # (Clear, high-level flow)
   ```

---

## 🤖 Automation

### GitHub Actions (Optional)

Create `.github/workflows/validate-diagrams.yml`:

```yaml
name: Validate Architecture Diagrams

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Mermaid CLI
        run: npm install -g @mermaid-js/mermaid-cli

      - name: Validate diagrams
        run: |
          if [ -f "ARCHITECTURE_DIAGRAM.md" ]; then
            mmdc -i ARCHITECTURE_DIAGRAM.md -o /tmp/test.png
            echo "✅ Diagrams are valid"
          fi

      - name: Check for updates
        run: |
          SENSITIVE_FILES="backend/ mcp-server/ mindscout/database.py"
          if git diff --name-only origin/main | grep -E "$SENSITIVE_FILES"; then
            if ! git diff --name-only origin/main | grep "ARCHITECTURE_DIAGRAM.md"; then
              echo "⚠️ Warning: Architecture files changed but diagrams weren't updated"
              exit 1
            fi
          fi
```

---

## 📖 Resources

- **Claude Instructions**: `.claude/instructions.md` - Detailed guide for AI assistants
- **Mermaid Docs**: https://mermaid.js.org/intro/
- **Mermaid Live**: https://mermaid.live - Interactive editor
- **GitHub Mermaid**: https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/

---

## 🆘 Need Help?

### Diagram Won't Render?

1. **Test on Mermaid Live**: https://mermaid.live
2. **Check common issues**:
   - Missing closing backticks ` ``` `
   - Typos in syntax (e.g., `graph TB` not `graph tb`)
   - Invalid connections (node doesn't exist)
   - Special characters not escaped

### Not Sure Which Diagram to Update?

1. **Check `.claude/instructions.md`** - Has a checklist
2. **Ask yourself**: "How does data flow differently now?"
3. **Start with System Overview** - Shows everything at high level
4. **Then drill down** - Update specific flow diagrams

### Forgot to Update Diagrams?

```bash
# No problem! Add them now
vim ARCHITECTURE_DIAGRAM.md

# Amend previous commit
git add ARCHITECTURE_DIAGRAM.md
git commit --amend --no-edit

# Or create new commit
git add ARCHITECTURE_DIAGRAM.md
git commit -m "docs: update architecture diagrams for previous changes"
```

---

## ✨ Pro Tips

1. **Update as you code**: Don't wait until the end
2. **Keep it simple**: Diagrams should clarify, not confuse
3. **Use subgraphs**: Organize complex diagrams
4. **Test rendering**: Always preview before committing
5. **Commit together**: Code + diagrams in one commit
6. **Write good commits**: Mention what diagrams you updated

---

Remember: **Good documentation saves time**. Future you will thank present you for keeping diagrams up to date! 🙏
