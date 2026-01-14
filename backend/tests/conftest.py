"""Global pytest fixtures for CodeCompass tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType
from tests.fixtures import (
    create_test_project,
    create_test_project_with_stats,
    get_sample_repo_path,
    create_test_settings,
    create_test_stats,
)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing."""
    # Import models to register them with Base before creating tables
    from app.models import project  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db(test_db_session):
    """Override get_db dependency with test database."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield test_db_session
    app.dependency_overrides.clear()


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI test client with test database."""
    # Mock init_db to prevent startup event from using production database
    with patch("app.main.init_db"):
        with TestClient(app) as test_client:
            yield test_client


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def temp_repo_dir():
    """Create temporary directory for test repositories."""
    temp_dir = tempfile.mkdtemp(prefix="codecompass_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def sample_python_repo():
    """
    Get path to python_simple sample repository from Story #49 fixtures.

    Returns permanent sample repo instead of creating temp directories.
    Sample repo includes: main.py, utils.py, requirements.txt, .gitignore
    """
    return get_sample_repo_path('python_simple')


@pytest.fixture(scope="function")
def sample_javascript_repo():
    """
    Get path to javascript_simple sample repository from Story #49 fixtures.

    Sample repo includes: index.js, utils.js, package.json, .gitignore
    """
    return get_sample_repo_path('javascript_simple')


@pytest.fixture(scope="function")
def sample_mixed_repo():
    """
    Get path to mixed_language sample repository from Story #49 fixtures.

    Sample repo includes:
    - Python files: api.py, models.py, helpers.py
    - JavaScript files: client.js, ui.js, config.js
    - .gitignore with combined patterns
    """
    return get_sample_repo_path('mixed_language')


# ============================================================================
# Data Factories
# ============================================================================

@pytest.fixture
def project_factory(test_db_session):
    """
    Factory for creating test projects using Story #49 fixtures.

    This fixture wraps create_test_project() and handles database persistence.
    Uses the comprehensive factory from tests.fixtures for consistent test data.
    """
    def _create_project(**kwargs):
        # Use Story #49 factory to create project with sensible defaults
        project = create_test_project(**kwargs)

        # Add to test database session
        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)
        return project

    return _create_project


@pytest.fixture
def db_initialized(test_db_session, project_factory):
    """
    Ensure database is initialized (tables created).
    This fixture ensures database setup runs but doesn't leave any projects.
    """
    # Create and immediately delete a dummy project to ensure tables exist
    # This is needed because FastAPI TestClient has issues with database overrides
    dummy = project_factory(name="_dummy_for_init_")
    test_db_session.delete(dummy)
    test_db_session.commit()
    return test_db_session
