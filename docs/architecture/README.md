# Architecture Documentation System

## 📐 Overview

MindScout uses an automated system to keep architecture diagrams synchronized with code changes. This ensures documentation never gets stale!

## 🎯 Quick Start (First Time)

```bash
# 1. Install the git hook (one-time setup)
./scripts/setup_git_hooks.sh

# 2. Optional: Install diagram validator
npm install -g @mermaid-js/mermaid-cli

# 3. You're done! The system will remind you to update diagrams.
```

## 📁 Files

| File | Purpose |
|------|---------|
| `ARCHITECTURE_DIAGRAM.md` | **The diagrams** - 15 Mermaid diagrams (renders on GitHub) |
| `ARCHITECTURE.md` | Text-based architecture documentation |
| `ARCHITECTURE_MAINTENANCE.md` | **User guide** - How to update diagrams |
| `.claude/instructions.md` | **AI guide** - Instructions for Claude Code |
| `scripts/check_architecture_docs.sh` | **Checker** - Validates diagram updates |
| `scripts/setup_git_hooks.sh` | **Installer** - Sets up git hooks |

## 🔄 How It Works

### Automatic Reminders

When you commit changes to architecture-sensitive files:

```bash
# You modify backend code
vim backend/api/articles.py

# You commit
git add backend/
git commit -m "feat: add bulk import"

# The hook reminds you:
# ⚠️  Architecture Documentation Check
# You've modified: backend/api/
# ❌ ARCHITECTURE_DIAGRAM.md was NOT updated
# Continue without updating? (y/N)
```

### What Triggers the Check?

Changes to these files trigger a reminder:

- `backend/main.py` or `backend/api/`
- `mcp-server/server.py`
- `mindscout/database.py`
- `mindscout/vectorstore.py`
- `mindscout/recommender.py`
- `mindscout/fetchers/`
- `requirements.txt`
- `Dockerfile`
- `cloudbuild.yaml`

## 📊 Available Diagrams

All diagrams are in `ARCHITECTURE_DIAGRAM.md`:

1. **System Overview** - Complete system architecture
2. **Paper Fetching Flow** - How papers are fetched and stored
3. **Semantic Search Flow** - Vector search process
4. **Recommendation Engine** - How recommendations work
5. **MCP Server Integration** - Claude Desktop integration
6. **Database Schema (ERD)** - All tables and relationships
7. **API Endpoints** - REST API architecture
8. **MCP Tools Mindmap** - All 9 MCP tools
9. **GCP Deployment** - Production cloud architecture
10. **CI/CD Pipeline** - Deployment automation
11. **User Journey** - Complete data flow
12. **Component Interactions** - How components connect
13. **Test Coverage** - Coverage pie chart
14. **Technology Stack** - All frameworks and tools
15. More specialized diagrams...

## ✏️ Updating Diagrams

### Step-by-Step

1. **Make your code changes**
2. **Open ARCHITECTURE_DIAGRAM.md**
3. **Find the relevant diagram section**
4. **Update the Mermaid code**
5. **Preview** (VS Code with Mermaid extension or https://mermaid.live)
6. **Commit together** with your code changes

### Example: Adding an API Endpoint

```mermaid
# Before
graph LR
    C1[GET /api/articles]
    C2[GET /api/articles/:id]

# After (add your new endpoint)
graph LR
    C1[GET /api/articles]
    C2[GET /api/articles/:id]
    C3[POST /api/articles/export]  # NEW!
```

Full guide: See `ARCHITECTURE_MAINTENANCE.md`

## 🛠️ Tools

### Preview Diagrams

```bash
# Option 1: VS Code (with Mermaid extension)
code ARCHITECTURE_DIAGRAM.md
# Press Cmd+Shift+V

# Option 2: Online
open https://mermaid.live
# Paste your diagram code

# Option 3: Export to image
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png
```

### Validate Syntax

```bash
# Automatic (if mermaid-cli installed)
git commit  # Hook validates automatically

# Manual
mmdc -i ARCHITECTURE_DIAGRAM.md -o /tmp/test.png
```

## 🎨 Diagram Style Guide

### Colors (Consistent Across All Diagrams)

```
User Interfaces:     #e1f5ff (Light Blue)
Application Layer:   #fff4e1 (Light Yellow)
Data/Storage:        #e8f5e9 (Light Green)
External APIs:       #fce4ec (Light Red)
Monitoring:          #f3e5f5 (Light Purple)
```

### Best Practices

✅ **DO**:
- Update diagrams when you change code
- Keep diagrams simple and focused
- Use consistent colors
- Test rendering before committing
- Commit code + diagrams together

❌ **DON'T**:
- Skip diagram updates (future you will regret it!)
- Make diagrams too detailed
- Forget to preview
- Commit diagrams separately from code

## 📚 Documentation Hierarchy

```
High Level → ARCHITECTURE_DIAGRAM.md (visual)
             ↓
Mid Level  → ARCHITECTURE.md (text descriptions)
             ↓
Details    → Code comments & docstrings
```

## 🤖 For AI Assistants (Claude Code)

See `.claude/instructions.md` for:
- When to update diagrams
- Which diagrams to update
- Mermaid syntax quick reference
- Common patterns
- Validation steps

## 🆘 Troubleshooting

### Diagram not rendering on GitHub?

1. Check code block: ` ```mermaid ` (not ` ```markdown `)
2. Validate syntax at https://mermaid.live
3. Hard refresh browser (GitHub caches)

### Hook not working?

```bash
# Reinstall hook
./scripts/setup_git_hooks.sh

# Check if executable
ls -la .git/hooks/pre-commit

# Make executable if needed
chmod +x .git/hooks/pre-commit
```

### Want to skip the hook once?

```bash
# Not recommended, but if you must:
git commit --no-verify
```

## 📖 Learn More

- **Mermaid Documentation**: https://mermaid.js.org/intro/
- **Mermaid Live Editor**: https://mermaid.live
- **GitHub Mermaid Support**: https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/

## 🎯 Goals

1. **Never have stale diagrams** - Automation reminds you
2. **Easy to update** - Clear instructions and examples
3. **Beautiful on GitHub** - Mermaid renders automatically
4. **Validate before commit** - Catch syntax errors early
5. **Single source of truth** - One diagram file

## 💡 Pro Tips

1. **Update as you go**: Don't save diagram updates for the end
2. **Use Mermaid Live**: Fastest way to preview and debug
3. **Keep it high-level**: Show component interactions, not implementation
4. **Commit message**: Mention which diagrams you updated
5. **Review PRs**: Check if diagrams match code changes

---

**Remember**: Good documentation is code that explains itself. Keep diagrams updated and your team (and future you) will thank you! 🙌
