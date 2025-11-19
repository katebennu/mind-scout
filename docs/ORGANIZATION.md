# Repository Organization Guide

## 📁 Proposed Structure

```
mindscout/
├── .github/                    # GitHub-specific files
│   ├── workflows/              # GitHub Actions
│   └── ISSUE_TEMPLATE/         # Issue templates
│
├── .claude/                    # Claude Code configuration
│   └── instructions.md         # AI assistant instructions
│
├── backend/                    # FastAPI backend
│   ├── api/                    # API routes
│   ├── main.py                 # Application entry
│   └── __init__.py
│
├── frontend/                   # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
│
├── mcp-server/                 # MCP integration
│   └── server.py
│
├── mindscout/                  # Core Python library
│   ├── fetchers/
│   ├── processors/
│   ├── database.py
│   └── ...
│
├── tests/                      # Test suite
│   ├── test_*.py
│   └── fixtures/
│
├── scripts/                    # Utility scripts
│   ├── deploy_gcp.sh
│   ├── setup_git_hooks.sh
│   └── check_architecture_docs.sh
│
├── docs/                       # 📚 All documentation
│   ├── README.md               # Docs index
│   ├── architecture/           # Architecture docs
│   │   ├── diagrams.md         # Mermaid diagrams
│   │   ├── overview.md         # Text overview
│   │   └── maintenance.md      # How to maintain
│   ├── deployment/             # Deployment guides
│   │   ├── gcp.md              # GCP deployment
│   │   ├── local.md            # Local development
│   │   └── quickstart.md       # Quick start
│   ├── development/            # Development docs
│   │   ├── testing.md          # Testing guide
│   │   ├── contributing.md     # Contribution guide
│   │   └── setup.md            # Dev environment
│   └── api/                    # API documentation
│       ├── rest-api.md         # REST API reference
│       └── mcp-tools.md        # MCP tools reference
│
├── config/                     # Configuration files
│   ├── .dockerignore
│   ├── .gcloudignore
│   └── nginx.conf              # Production nginx config
│
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local dev environment
├── cloudbuild.yaml             # GCP Cloud Build
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Python project config
├── Makefile                    # Build commands
├── LICENSE                     # License file
└── README.md                   # Main README (keep concise!)
```

## 🎯 Reorganization Plan

### Phase 1: Move Documentation (Immediate)

**Current scattered docs** → **Organized in `docs/`**

```bash
# Architecture docs
docs/architecture/
  ├── diagrams.md          ← ARCHITECTURE_DIAGRAM.md
  ├── overview.md          ← ARCHITECTURE.md
  └── maintenance.md       ← ARCHITECTURE_MAINTENANCE.md

# Deployment docs
docs/deployment/
  ├── gcp.md              ← DEPLOYMENT_GCP.md
  ├── general.md          ← DEPLOYMENT.md
  └── quickstart.md       ← GCP_QUICKSTART.md

# Development docs
docs/development/
  ├── testing.md          ← TESTING.md
  ├── structure.md        ← STRUCTURE.md
  └── status.md           ← STATUS.md

# Project planning
docs/
  └── project-plan.md     ← PROJECT_PLAN.md
```

### Phase 2: Move Config Files

**Root clutter** → **`config/` directory**

```bash
config/
  ├── .dockerignore       ← .dockerignore
  ├── .gcloudignore       ← .gcloudignore
  └── docker/             # Docker-related configs
      ├── Dockerfile      ← Dockerfile
      └── docker-compose.yml
```

### Phase 3: Update Root README

**Make it concise and guide to subdirectories**

## 📋 Migration Commands

### Create New Structure

```bash
# Create directory structure
mkdir -p docs/{architecture,deployment,development,api}
mkdir -p config/docker
mkdir -p .github/{workflows,ISSUE_TEMPLATE}

# Move architecture docs
mv ARCHITECTURE_DIAGRAM.md docs/architecture/diagrams.md
mv ARCHITECTURE.md docs/architecture/overview.md
mv ARCHITECTURE_MAINTENANCE.md docs/architecture/maintenance.md

# Move deployment docs
mv DEPLOYMENT_GCP.md docs/deployment/gcp.md
mv DEPLOYMENT.md docs/deployment/general.md
mv GCP_QUICKSTART.md docs/deployment/quickstart.md

# Move development docs
mv TESTING.md docs/development/testing.md
mv STRUCTURE.md docs/development/structure.md
mv STATUS.md docs/development/status.md
mv PROJECT_PLAN.md docs/project-plan.md

# Move config files
mv .dockerignore config/.dockerignore
mv .gcloudignore config/.gcloudignore
# Note: Dockerfile and docker-compose might need path updates

# Update any references in git hooks and scripts
# Update .gitignore if needed

# Create docs index
cat > docs/README.md << 'EOF'
# MindScout Documentation

## 📚 Documentation Index

### Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Local Setup](development/setup.md) - Development environment setup
- [Quick Deploy](deployment/quickstart.md) - Deploy to GCP in 30 minutes

### Architecture
- [Architecture Diagrams](architecture/diagrams.md) - Visual system architecture (Mermaid)
- [Architecture Overview](architecture/overview.md) - Detailed text description
- [Maintaining Diagrams](architecture/maintenance.md) - How to keep docs updated

### Development
- [Testing Guide](development/testing.md) - Running tests and coverage
- [Project Structure](development/structure.md) - Code organization
- [Development Status](development/status.md) - Current status and roadmap
- [Contributing](development/contributing.md) - How to contribute

### Deployment
- [GCP Deployment](deployment/gcp.md) - Comprehensive GCP guide
- [General Deployment](deployment/general.md) - Other deployment options
- [Quick Start](deployment/quickstart.md) - Deploy in 30 minutes

### API Reference
- [REST API](api/rest-api.md) - Backend API documentation
- [MCP Tools](api/mcp-tools.md) - MCP server tools reference

### Planning
- [Project Plan](project-plan.md) - Original project planning document
EOF

# Create docs index
cat > docs/README.md << 'EOF'
# MindScout Documentation

Welcome to the MindScout documentation! 📚

## Quick Links

🚀 **Get Started**: [Quick Start Guide](deployment/quickstart.md)
📐 **Architecture**: [System Diagrams](architecture/diagrams.md)
🧪 **Testing**: [Testing Guide](development/testing.md)
☁️ **Deploy**: [GCP Deployment](deployment/gcp.md)

## Documentation Structure

```
docs/
├── architecture/       # System design and diagrams
├── deployment/         # Deployment guides
├── development/        # Development workflow
├── api/               # API reference
└── project-plan.md    # Project planning
```

## Finding What You Need

### I want to...

**...understand how the system works**
→ Start with [Architecture Overview](architecture/overview.md)

**...see visual diagrams**
→ Check [Architecture Diagrams](architecture/diagrams.md)

**...deploy to production**
→ Follow [GCP Deployment Guide](deployment/gcp.md)

**...set up my dev environment**
→ Read [Development Setup](development/setup.md)

**...run tests**
→ See [Testing Guide](development/testing.md)

**...contribute code**
→ Review [Contributing Guide](development/contributing.md)

**...update architecture docs**
→ Follow [Maintenance Guide](architecture/maintenance.md)

## Documentation Standards

- **Architecture docs**: Keep diagrams in sync with code changes
- **API docs**: Update when endpoints change
- **Deployment docs**: Test on clean environment before updating
- **Development docs**: Update when workflow changes

See [Maintaining Diagrams](architecture/maintenance.md) for automation.
EOF
```

## 🎨 Improved Root README

Create a cleaner, more focused root README:

```markdown
# MindScout

> An AI-powered research assistant that helps you stay on top of advances in AI

[![Tests](https://img.shields.io/badge/tests-21%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-14%25-yellow)](TESTING.md)
[![MCP](https://img.shields.io/badge/MCP-9%20tools-blue)](mcp-server/)

## ✨ Features

- 🔍 **Semantic Search**: Find papers using natural language
- 📊 **Smart Recommendations**: Personalized based on your interests
- 🤖 **Claude Integration**: MCP server for Claude Desktop
- 🌐 **Web Dashboard**: Browse and manage your library
- 📥 **Auto-Fetch**: Fetch from arXiv and Semantic Scholar
- ⭐ **Rate & Track**: Rate papers and track reading progress

## 🚀 Quick Start

### Option 1: Try Locally (5 minutes)

\`\`\`bash
# Install
pip install -e ".[dev]"

# Fetch some papers
mindscout fetch arxiv

# Start web UI
make frontend &
make api &

# Open http://localhost:3000
\`\`\`

### Option 2: Deploy to GCP (30 minutes)

\`\`\`bash
# One command deployment
./scripts/deploy_gcp.sh
\`\`\`

See [Quick Deploy Guide](docs/deployment/quickstart.md) for details.

## 📚 Documentation

- **[Getting Started](docs/README.md)** - Documentation index
- **[Architecture](docs/architecture/diagrams.md)** - System design
- **[Development](docs/development/testing.md)** - Development guide
- **[Deployment](docs/deployment/gcp.md)** - Production deployment
- **[API Reference](docs/api/)** - API documentation

## 🏗️ Architecture

\`\`\`
Web UI ──────┐
             ├──> FastAPI Backend ──> Database (SQLite/PostgreSQL)
Claude ──────┘         │
                       └──> VectorStore (ChromaDB)
                       └──> Recommender Engine
\`\`\`

See [detailed architecture diagrams](docs/architecture/diagrams.md).

## 🧪 Development

\`\`\`bash
# Run tests
make test

# Run with coverage
make coverage

# Format code
make format

# Lint
make lint
\`\`\`

## 📦 Project Structure

\`\`\`
mindscout/
├── backend/           # FastAPI REST API
├── frontend/          # React web UI
├── mcp-server/        # MCP integration for Claude
├── mindscout/         # Core Python library
├── tests/             # Test suite (86% MCP coverage!)
├── docs/              # 📚 Documentation
└── scripts/           # Deployment & utility scripts
\`\`\`

## 🤝 Contributing

See [Contributing Guide](docs/development/contributing.md).

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [ChromaDB](https://www.trychroma.com/)
- [Anthropic Claude](https://www.anthropic.com/)

---

**[View Full Documentation](docs/README.md)** | **[Report Issue](https://github.com/yourusername/mindscout/issues)**
\`\`\`

## 🔧 Update References

After moving files, update these references:

### 1. Git Hook Script

`scripts/check_architecture_docs.sh`:
```bash
# Change
if echo "$CHANGED_FILES" | grep -q "ARCHITECTURE_DIAGRAM.md"; then

# To
if echo "$CHANGED_FILES" | grep -q "docs/architecture/diagrams.md"; then
```

### 2. Claude Instructions

`.claude/instructions.md`:
```markdown
# Change all references:
ARCHITECTURE_DIAGRAM.md → docs/architecture/diagrams.md
ARCHITECTURE_MAINTENANCE.md → docs/architecture/maintenance.md
```

### 3. Docker/Cloud Build

If you move Dockerfile:
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'config/docker/Dockerfile'  # Update path
```

### 4. .gitignore

```gitignore
# Generated files
.coverage
coverage.xml
htmlcov/

# Build artifacts
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Don't ignore config folder
!config/
```

## 📊 Benefits

### Before
```
mindscout/
├── ARCHITECTURE_DIAGRAM.md
├── ARCHITECTURE_MAINTENANCE.md
├── ARCHITECTURE.md
├── DEPLOYMENT_GCP.md
├── DEPLOYMENT.md
├── GCP_QUICKSTART.md
├── TESTING.md
├── STRUCTURE.md
├── STATUS.md
├── PROJECT_PLAN.md
├── .dockerignore
├── .gcloudignore
└── ... (20+ files in root!)
```

### After
```
mindscout/
├── docs/                  # All documentation
├── config/                # All configuration
├── backend/               # Code
├── frontend/              # Code
├── mindscout/             # Code
├── tests/                 # Code
├── scripts/               # Code
├── README.md              # Clear entry point
├── Dockerfile             # Essential only
└── pyproject.toml         # Essential only
```

## 🎯 Essential Root Files Only

Keep these in root:
- ✅ `README.md` - Main entry point
- ✅ `LICENSE` - Legal requirement
- ✅ `pyproject.toml` - Python project config
- ✅ `requirements.txt` - Dependencies
- ✅ `Makefile` - Build commands
- ✅ `Dockerfile` - Container definition
- ✅ `.gitignore` - Git configuration

Everything else → organized subdirectories!

## 📝 Migration Checklist

- [ ] Create new directory structure
- [ ] Move documentation files
- [ ] Move configuration files
- [ ] Update README.md
- [ ] Create docs/README.md index
- [ ] Update git hooks
- [ ] Update .claude/instructions.md
- [ ] Update any hardcoded paths
- [ ] Test that everything still works
- [ ] Update this guide if needed
- [ ] Commit changes

## 🚀 Quick Migration Script

Want me to create an automated migration script?
