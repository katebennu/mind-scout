.PHONY: test coverage coverage-html coverage-report install-dev clean lint format help api frontend db-init mcp-test mcp-install venv setup db-migrate db-upgrade

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

setup: venv  ## Create venv and install all dependencies
	$(PIP) install -e ".[dev]"
	@echo ""
	@echo "Virtual environment created. Activate with:"
	@echo "  source $(VENV)/bin/activate"

install-dev:  ## Install development dependencies (in current env)
	pip install -e ".[dev]"

test:  ## Run tests (requires PostgreSQL - use: docker compose up -d postgres)
	TEST_DATABASE_URL=postgresql://mindscout:mindscout@localhost:5432/mindscout_test \
	ANTHROPIC_API_KEY=test-key pytest -v

coverage:  ## Run tests with coverage report in terminal
	TEST_DATABASE_URL=postgresql://mindscout:mindscout@localhost:5432/mindscout_test \
	ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=term-missing

coverage-html:  ## Generate HTML coverage report
	TEST_DATABASE_URL=postgresql://mindscout:mindscout@localhost:5432/mindscout_test \
	ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html"

coverage-report:  ## Show coverage report from last run
	coverage report

coverage-xml:  ## Generate XML coverage report (for CI)
	TEST_DATABASE_URL=postgresql://mindscout:mindscout@localhost:5432/mindscout_test \
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
db-init:  ## Initialize the database (legacy - creates tables directly)
	mindscout profile list

db-migrate:  ## Create a new migration (usage: make db-migrate msg="description")
	alembic revision --autogenerate -m "$(msg)"

db-upgrade:  ## Run database migrations
	alembic upgrade head

db-downgrade:  ## Rollback last migration
	alembic downgrade -1

db-history:  ## Show migration history
	alembic history

postgres-up:  ## Start PostgreSQL container
	docker compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@echo "PostgreSQL is running on localhost:5432"
	@echo "Connection: postgresql://mindscout:mindscout@localhost:5432/mindscout"

postgres-down:  ## Stop PostgreSQL container
	docker compose down

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
