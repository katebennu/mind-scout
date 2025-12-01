"""Pytest configuration and shared fixtures for test isolation."""

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_test_database_url() -> tuple[str, str]:
    """Get PostgreSQL database URLs for testing.

    Returns sync and async database URLs based on TEST_DATABASE_URL env var.
    Defaults to local PostgreSQL if not set.

    Returns:
        Tuple of (sync_url, async_url)
    """
    test_db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://mindscout:mindscout@localhost:5432/mindscout_test",
    )

    if test_db_url.startswith("postgresql+asyncpg://"):
        sync_url = test_db_url.replace("postgresql+asyncpg://", "postgresql://")
        async_url = test_db_url
    else:
        sync_url = test_db_url
        async_url = test_db_url.replace("postgresql://", "postgresql+asyncpg://")

    return sync_url, async_url


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Automatically isolate each test with its own database.

    This fixture runs automatically for every test, ensuring:
    1. Each test gets a clean database state
    2. The production database is never touched
    3. Database state doesn't leak between tests

    Requires PostgreSQL to be running. For local development:
        docker compose up -d postgres

    For CI, GitHub Actions provides a PostgreSQL service container.
    """
    # Set environment variable BEFORE any database imports
    monkeypatch.setenv("MINDSCOUT_DATA_DIR", str(tmp_path))

    # Patch the config module
    from mindscout import config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    # Re-initialize the database module with test database
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from mindscout import database

    sync_url, _ = get_test_database_url()

    test_engine = create_engine(sync_url)

    # Clean up existing tables before each test
    with test_engine.connect() as conn:
        # Drop all tables in reverse order of dependencies
        conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS pending_batches CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS rss_feeds CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS user_profile CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS articles CASCADE"))
        conn.commit()

    test_session_factory = sessionmaker(bind=test_engine)

    # Patch the database module's sync engine and Session
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "Session", test_session_factory)

    # Reset the lazy-initialized async globals so they get recreated
    # with the test database URL in the correct event loop
    monkeypatch.setattr(database, "_async_engine", None)
    monkeypatch.setattr(database, "_async_session_local", None)

    # Patch the settings to use test database URL
    from mindscout.config import get_settings

    test_settings = get_settings()
    monkeypatch.setattr(test_settings, "database_url", sync_url)

    # Initialize the test database schema
    database.init_db()

    yield tmp_path

    # Reset async globals at end of test to avoid event loop issues
    database._async_engine = None
    database._async_session_local = None


@pytest.fixture
def db_session(isolated_test_db):
    """Get a database session for the isolated test database."""
    from mindscout.database import get_session

    session = get_session()
    yield session
    session.close()


@pytest.fixture
def test_app(isolated_test_db):
    """Create a FastAPI test app with overridden database dependency.

    This fixture creates a fresh async engine for each test to avoid
    event loop conflicts with TestClient.
    """
    from backend.main import app
    from mindscout.database import get_async_db

    sync_url, async_url = get_test_database_url()

    # Create a fresh async engine for this test
    test_async_engine = create_async_engine(async_url, echo=False)
    test_async_session_factory = async_sessionmaker(
        bind=test_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_async_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_db] = override_get_async_db

    yield app

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    """Create test client with overridden database dependency."""
    from fastapi.testclient import TestClient

    return TestClient(test_app)
