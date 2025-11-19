# Testing & Coverage Guide

## Current Coverage

**Total Coverage: 9.11%**

| Module | Coverage | Notes |
|--------|----------|-------|
| mindscout/database.py | 97.87% | ✅ Well tested |
| mindscout/fetchers/arxiv.py | 80.85% | ✅ Good coverage |
| mindscout/processors/content.py | 63.64% | ⚠️ Needs more tests |
| mindscout/processors/llm.py | 58.33% | ⚠️ Needs more tests |
| mindscout/cli.py | 0% | ❌ Not tested |
| backend/* | 0% | ❌ Not tested |
| mcp-server/server.py | 0% | ❌ Not tested |

## Quick Commands

### Using Make (Recommended)

```bash
# Show all available commands
make help

# Run tests
make test

# Run tests with coverage report
make coverage

# Generate HTML coverage report
make coverage-html

# Clean up generated files
make clean

# Format code
make format

# Run linters
make lint
```

### Using pytest directly

```bash
# Run all tests
ANTHROPIC_API_KEY=test-key pytest -v

# Run with coverage
ANTHROPIC_API_KEY=test-key pytest --cov=mindscout --cov=backend --cov-report=term-missing

# Run specific test file
ANTHROPIC_API_KEY=test-key pytest tests/test_fetch.py -v

# Run tests matching a pattern
ANTHROPIC_API_KEY=test-key pytest -k "test_fetch" -v
```

## Coverage Reports

### Terminal Report

```bash
make coverage
```

Shows coverage in your terminal with line numbers of uncovered code.

### HTML Report

```bash
make coverage-html
open htmlcov/index.html
```

Generates an interactive HTML report showing:
- Overall coverage statistics
- Per-file coverage
- Highlighted covered/uncovered lines
- Branch coverage information

### XML Report (for CI/CD)

```bash
make coverage-xml
```

Generates `coverage.xml` for CI/CD tools like GitHub Actions, Jenkins, etc.

## Writing Tests

### Test Structure

```python
# tests/test_mymodule.py
import pytest
from mindscout.mymodule import MyClass

def test_my_function():
    """Test that my_function works correctly."""
    result = MyClass().my_function()
    assert result == expected_value

def test_error_handling():
    """Test that errors are handled correctly."""
    with pytest.raises(ValueError):
        MyClass().my_function(invalid_input)
```

### Test Fixtures

```python
@pytest.fixture
def sample_article():
    """Fixture that provides a sample article for tests."""
    return {
        "title": "Test Paper",
        "authors": "Test Author",
        "abstract": "Test abstract"
    }

def test_with_fixture(sample_article):
    """Test using the fixture."""
    assert sample_article["title"] == "Test Paper"
```

### Mocking External APIs

```python
from unittest.mock import patch, MagicMock

def test_api_call():
    """Test API calls with mocking."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"data": "test"}
        result = fetch_from_api()
        assert result == {"data": "test"}
```

## Coverage Goals

### Short-term Goals

- [ ] **mindscout/cli.py**: Add basic CLI tests (target: 50%+)
- [ ] **backend/**: Add API endpoint tests (target: 70%+)
- [ ] **mindscout/processors/**: Improve to 80%+
- [ ] **mcp-server/**: Add MCP tool tests (target: 60%+)

### Long-term Goals

- [ ] **Overall**: 70%+ coverage
- [ ] **Core modules** (database, fetchers, processors): 85%+
- [ ] **CLI & APIs**: 60%+

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: make coverage-xml
      - uses: codecov/codecov-action@v3
```

## Excluding Code from Coverage

Use `# pragma: no cover` for code that shouldn't be tested:

```python
def debug_only():  # pragma: no cover
    """This function is only for debugging."""
    pass

if __name__ == "__main__":  # pragma: no cover
    main()
```

## Best Practices

### DO:
✅ Test edge cases and error conditions
✅ Use descriptive test names
✅ Keep tests independent
✅ Mock external dependencies (APIs, databases)
✅ Test both success and failure paths

### DON'T:
❌ Test implementation details
❌ Write tests that depend on other tests
❌ Leave API keys in test code
❌ Skip testing error handling
❌ Test external services directly

## Troubleshooting

### Tests fail with "No ANTHROPIC_API_KEY"

**Solution**: Use the Makefile commands which set a test key automatically:
```bash
make test
```

Or set a dummy key manually:
```bash
ANTHROPIC_API_KEY=test-key pytest
```

### Coverage report shows wrong files

**Solution**: Check `pyproject.toml` coverage configuration. Make sure paths are correct.

### Tests are slow

**Solution**:
- Use mocking for API calls
- Use in-memory SQLite for database tests
- Run specific test files instead of all tests

### HTML report doesn't open

**Solution**:
```bash
# Generate report
make coverage-html

# Open manually
open htmlcov/index.html

# Or on Linux
xdg-open htmlcov/index.html
```

## Adding More Tests

### Priority Areas

1. **API Endpoints** (backend/*)
   - Test all REST endpoints
   - Test error responses
   - Test authentication/authorization

2. **MCP Server** (mcp-server/server.py)
   - Test each tool function
   - Test error handling
   - Test rate limiting

3. **CLI Commands** (mindscout/cli.py)
   - Test main commands
   - Test argument parsing
   - Test output formatting

4. **Fetchers** (mindscout/fetchers/*)
   - Test API response parsing
   - Test error handling
   - Test rate limiting

### Example: Testing an API Endpoint

```python
# tests/test_api_articles.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_articles():
    """Test the list articles endpoint."""
    response = client.get("/api/articles?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data

def test_get_article_not_found():
    """Test getting a non-existent article."""
    response = client.get("/api/articles/99999")
    assert response.status_code == 404
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing best practices](https://docs.python-guide.org/writing/tests/)
