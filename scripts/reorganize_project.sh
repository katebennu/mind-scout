#!/bin/bash

# MindScout Project Reorganization Script
# Moves documentation and config files into organized subdirectories

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MindScout Project Reorganization${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Confirm before proceeding
echo -e "${YELLOW}This will reorganize your project structure:${NC}"
echo ""
echo "  • Move docs to docs/ subdirectories"
echo "  • Move config files to config/"
echo "  • Update file references"
echo "  • Keep root directory clean"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Cancelled.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Starting reorganization...${NC}"
echo ""

# Create directory structure
echo -e "${BLUE}📁 Creating directory structure...${NC}"
mkdir -p docs/{architecture,deployment,development,api}
mkdir -p config
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Move architecture documentation
echo -e "${BLUE}📐 Moving architecture documentation...${NC}"
if [ -f "ARCHITECTURE_DIAGRAM.md" ]; then
    git mv ARCHITECTURE_DIAGRAM.md docs/architecture/diagrams.md 2>/dev/null || \
        mv ARCHITECTURE_DIAGRAM.md docs/architecture/diagrams.md
    echo "  ✓ Moved diagrams.md"
fi

if [ -f "ARCHITECTURE.md" ]; then
    git mv ARCHITECTURE.md docs/architecture/overview.md 2>/dev/null || \
        mv ARCHITECTURE.md docs/architecture/overview.md
    echo "  ✓ Moved overview.md"
fi

if [ -f "ARCHITECTURE_MAINTENANCE.md" ]; then
    git mv ARCHITECTURE_MAINTENANCE.md docs/architecture/maintenance.md 2>/dev/null || \
        mv ARCHITECTURE_MAINTENANCE.md docs/architecture/maintenance.md
    echo "  ✓ Moved maintenance.md"
fi

if [ -f "docs/ARCHITECTURE_README.md" ]; then
    git mv docs/ARCHITECTURE_README.md docs/architecture/README.md 2>/dev/null || \
        mv docs/ARCHITECTURE_README.md docs/architecture/README.md
    echo "  ✓ Moved architecture README.md"
fi

echo -e "${GREEN}✓ Architecture docs moved${NC}"
echo ""

# Move deployment documentation
echo -e "${BLUE}☁️  Moving deployment documentation...${NC}"
if [ -f "DEPLOYMENT_GCP.md" ]; then
    git mv DEPLOYMENT_GCP.md docs/deployment/gcp.md 2>/dev/null || \
        mv DEPLOYMENT_GCP.md docs/deployment/gcp.md
    echo "  ✓ Moved gcp.md"
fi

if [ -f "DEPLOYMENT.md" ]; then
    git mv DEPLOYMENT.md docs/deployment/general.md 2>/dev/null || \
        mv DEPLOYMENT.md docs/deployment/general.md
    echo "  ✓ Moved general.md"
fi

if [ -f "GCP_QUICKSTART.md" ]; then
    git mv GCP_QUICKSTART.md docs/deployment/quickstart.md 2>/dev/null || \
        mv GCP_QUICKSTART.md docs/deployment/quickstart.md
    echo "  ✓ Moved quickstart.md"
fi

echo -e "${GREEN}✓ Deployment docs moved${NC}"
echo ""

# Move development documentation
echo -e "${BLUE}🔧 Moving development documentation...${NC}"
if [ -f "TESTING.md" ]; then
    git mv TESTING.md docs/development/testing.md 2>/dev/null || \
        mv TESTING.md docs/development/testing.md
    echo "  ✓ Moved testing.md"
fi

if [ -f "STRUCTURE.md" ]; then
    git mv STRUCTURE.md docs/development/structure.md 2>/dev/null || \
        mv STRUCTURE.md docs/development/structure.md
    echo "  ✓ Moved structure.md"
fi

if [ -f "STATUS.md" ]; then
    git mv STATUS.md docs/development/status.md 2>/dev/null || \
        mv STATUS.md docs/development/status.md
    echo "  ✓ Moved status.md"
fi

echo -e "${GREEN}✓ Development docs moved${NC}"
echo ""

# Move project planning
echo -e "${BLUE}📋 Moving project planning...${NC}"
if [ -f "PROJECT_PLAN.md" ]; then
    git mv PROJECT_PLAN.md docs/project-plan.md 2>/dev/null || \
        mv PROJECT_PLAN.md docs/project-plan.md
    echo "  ✓ Moved project-plan.md"
fi

if [ -f "docs/ORGANIZATION.md" ]; then
    # Keep ORGANIZATION.md in docs root
    echo "  ✓ ORGANIZATION.md already in place"
fi

echo -e "${GREEN}✓ Project docs moved${NC}"
echo ""

# Move configuration files (optional - keep in root for now)
echo -e "${BLUE}⚙️  Configuration files...${NC}"
echo "  ℹ️  Keeping .dockerignore and .gcloudignore in root (Docker/GCloud expect them there)"
echo -e "${GREEN}✓ Config files verified${NC}"
echo ""

# Create docs index
echo -e "${BLUE}📚 Creating documentation index...${NC}"
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
│   ├── diagrams.md     # Mermaid architecture diagrams
│   ├── overview.md     # Detailed text description
│   ├── maintenance.md  # How to keep docs updated
│   └── README.md       # Architecture documentation index
├── deployment/         # Deployment guides
│   ├── gcp.md         # Comprehensive GCP guide
│   ├── general.md     # Other deployment options
│   └── quickstart.md  # Deploy in 30 minutes
├── development/        # Development workflow
│   ├── testing.md     # Testing and coverage
│   ├── structure.md   # Project structure
│   └── status.md      # Current status
├── api/               # API reference (coming soon)
└── project-plan.md    # Original project planning
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
→ Read the main [README](../README.md)

**...run tests**
→ See [Testing Guide](development/testing.md)

**...update architecture docs**
→ Follow [Maintenance Guide](architecture/maintenance.md)

## Documentation Standards

- **Architecture docs**: Keep diagrams in sync with code changes
- **API docs**: Update when endpoints change
- **Deployment docs**: Test on clean environment before updating
- **Development docs**: Update when workflow changes

See [Maintaining Diagrams](architecture/maintenance.md) for automation.

---

**Need help?** Check the [main README](../README.md) or [open an issue](https://github.com/yourusername/mindscout/issues).
EOF

echo "  ✓ Created docs/README.md"
echo -e "${GREEN}✓ Documentation index created${NC}"
echo ""

# Update references in scripts
echo -e "${BLUE}🔗 Updating file references...${NC}"

# Update git hook script
if [ -f "scripts/check_architecture_docs.sh" ]; then
    # Create backup
    cp scripts/check_architecture_docs.sh scripts/check_architecture_docs.sh.bak

    # Update paths
    sed -i.tmp 's|ARCHITECTURE_DIAGRAM\.md|docs/architecture/diagrams.md|g' scripts/check_architecture_docs.sh
    rm -f scripts/check_architecture_docs.sh.tmp

    echo "  ✓ Updated check_architecture_docs.sh"
fi

# Update Claude instructions
if [ -f ".claude/instructions.md" ]; then
    # Create backup
    cp .claude/instructions.md .claude/instructions.md.bak

    # Update paths
    sed -i.tmp 's|ARCHITECTURE_DIAGRAM\.md|docs/architecture/diagrams.md|g' .claude/instructions.md
    sed -i.tmp 's|ARCHITECTURE_MAINTENANCE\.md|docs/architecture/maintenance.md|g' .claude/instructions.md
    sed -i.tmp 's|ARCHITECTURE\.md|docs/architecture/overview.md|g' .claude/instructions.md
    rm -f .claude/instructions.md.tmp

    echo "  ✓ Updated .claude/instructions.md"
fi

echo -e "${GREEN}✓ References updated${NC}"
echo ""

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Reorganization complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Moved files:"
echo "  📐 Architecture docs → docs/architecture/"
echo "  ☁️  Deployment docs  → docs/deployment/"
echo "  🔧 Development docs → docs/development/"
echo "  📋 Planning docs    → docs/"
echo ""

echo "Updated references in:"
echo "  • scripts/check_architecture_docs.sh"
echo "  • .claude/instructions.md"
echo ""

echo "Next steps:"
echo "  1. Review the new structure:"
echo "     tree docs/"
echo ""
echo "  2. Check docs index:"
echo "     cat docs/README.md"
echo ""
echo "  3. Test that links work:"
echo "     (Open in GitHub or VS Code preview)"
echo ""
echo "  4. Commit changes:"
echo "     git status"
echo "     git add ."
echo "     git commit -m \"docs: reorganize project structure\""
echo ""

echo -e "${YELLOW}⚠️  Backup files created (.bak) - delete if everything works!${NC}"
echo ""
