.PHONY: test coverage coverage-html coverage-report install-dev clean lint format help

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-dev:  ## Install development dependencies
	pip install -e ".[dev]"

test:  ## Run tests
	ANTHROPIC_API_KEY=test-key pytest -v

coverage:  ## Run tests with coverage report in terminal
	ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=term-missing

coverage-html:  ## Generate HTML coverage report
	ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html"

coverage-report:  ## Show coverage report from last run
	coverage report

coverage-xml:  ## Generate XML coverage report (for CI)
	ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=xml

lint:  ## Run linters (ruff)
	ruff check mindscout backend mcp-server

format:  ## Format code with black
	black mindscout backend mcp-server tests

format-check:  ## Check if code is formatted
	black --check mindscout backend mcp-server tests

clean:  ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf mindscout.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

# API commands
api:  ## Start the FastAPI server
	python -m uvicorn backend.main:app --reload --port 8000

frontend:  ## Start the frontend dev server
	cd frontend && npm run dev

# Database commands
db-init:  ## Initialize the database
	mindscout profile list

# MCP commands
mcp-test:  ## Test MCP server
	python mcp-server/server.py

mcp-install:  ## Install MCP server in Claude Desktop
	@echo "MCP server path: $(PWD)/mcp-server/server.py"
	@echo "Python path: $(shell which python)"
	@echo ""
	@echo "Add this to Claude Desktop config:"
	@echo '{'
	@echo '  "mcpServers": {'
	@echo '    "mindscout": {'
	@echo '      "command": "$(shell which python)",'
	@echo '      "args": ["$(PWD)/mcp-server/server.py"]'
	@echo '    }'
	@echo '  }'
	@echo '}'
