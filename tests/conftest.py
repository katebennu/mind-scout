"""Pytest configuration and shared fixtures for test isolation."""

import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Automatically isolate each test with its own database.

    This fixture runs automatically for every test, ensuring:
    1. Each test gets a fresh temporary database
    2. The production database is never touched
    3. Database state doesn't leak between tests
    """
    # Set environment variable BEFORE any database imports
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    # Patch the config module
    from mindscout import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "mindscout.db")

    # Re-initialize the database module with the new path
    from mindscout import database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create a new engine pointing to the test database
    test_engine = create_engine(f"sqlite:///{tmp_path / 'mindscout.db'}")
    test_session_factory = sessionmaker(bind=test_engine)

    # Patch the database module's engine and Session
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "Session", test_session_factory)

    # Initialize the test database schema
    database.init_db()

    yield tmp_path

    # Cleanup happens automatically when tmp_path is removed


@pytest.fixture
def db_session(isolated_test_db):
    """Get a database session for the isolated test database."""
    from mindscout.database import get_session
    session = get_session()
    yield session
    session.close()
