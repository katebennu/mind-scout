# Mind Scout Tests

This directory will contain tests for Mind Scout.

## Planned Test Coverage

### Unit Tests

**Fetchers** (`test_fetchers.py`)
- arXiv RSS parsing
- Semantic Scholar API integration
- Advanced arXiv search query building
- Article normalization

**Processors** (`test_processors.py`)
- LLM client initialization
- Topic extraction
- Summarization
- Embedding generation

**Recommendation Engine** (`test_recommender.py`)
- Topic matching algorithm
- Citation scoring
- Multi-factor scoring
- Explanation generation

**Profile Management** (`test_profile.py`)
- Interest management
- Skill level setting
- Profile retrieval

### Integration Tests

**Database** (`test_database.py`)
- Article storage and retrieval
- Duplicate handling
- Profile creation
- Rating storage

**CLI** (`test_cli.py`)
- Command parsing
- Output formatting
- Error handling

### End-to-End Tests

**Workflows** (`test_workflows.py`)
- Fetch → Process → Recommend workflow
- Search → Rate → Insights workflow
- Profile setup → Recommendation workflow

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=mindscout

# Run specific test file
pytest tests/test_recommender.py

# Run specific test
pytest tests/test_recommender.py::test_topic_matching
```

## Writing Tests

Example test structure:

```python
import pytest
from mindscout.recommender import RecommendationEngine

def test_topic_matching():
    """Test that topic matching works correctly."""
    engine = RecommendationEngine()
    # Test implementation
    assert True

@pytest.fixture
def sample_article():
    """Fixture providing a sample article."""
    return {
        "source_id": "test123",
        "title": "Test Paper",
        "abstract": "Test abstract",
        # ...
    }
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Key workflows covered
- **E2E Tests**: Happy path scenarios

## TODO

- [ ] Set up pytest configuration
- [ ] Add test fixtures for articles and profiles
- [ ] Implement fetcher tests
- [ ] Implement processor tests
- [ ] Implement recommender tests
- [ ] Implement database tests
- [ ] Add CI/CD with GitHub Actions
- [ ] Set up test database separate from production
