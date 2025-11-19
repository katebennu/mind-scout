#!/bin/bash

# Setup Git Hooks for Architecture Documentation
# This script installs a pre-commit hook that reminds developers to update architecture diagrams

set -e

echo "🔧 Setting up Git hooks for architecture documentation..."
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository root"
    echo "   Please run this from the project root directory"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for MindScout
# Checks for architecture documentation updates

# Run architecture documentation checker
./scripts/check_architecture_docs.sh
EOF

# Make hook executable
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed!"
echo ""
echo "The hook will:"
echo "  • Detect changes to architecture-sensitive files"
echo "  • Remind you to update ARCHITECTURE_DIAGRAM.md"
echo "  • Validate Mermaid syntax (if mermaid-cli installed)"
echo ""
echo "To install Mermaid validation (optional):"
echo "  npm install -g @mermaid-js/mermaid-cli"
echo ""
echo "To bypass the hook (not recommended):"
echo "  git commit --no-verify"
echo ""
echo "✨ All set! Your architecture docs will stay in sync."
