"""Global pytest fixtures for CodeCompass tests."""

import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database for testing."""
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
def sample_python_repo(temp_repo_dir):
    """Create minimal Python repository for testing."""
    repo_path = temp_repo_dir / "python_sample"
    repo_path.mkdir()

    # Create main.py with imports
    (repo_path / "main.py").write_text("""import os
from utils import helper

def main():
    print("Hello, World!")
    result = helper()
    return result

if __name__ == "__main__":
    main()
""")

    # Create utils.py with functions
    (repo_path / "utils.py").write_text("""def helper():
    return "Helper function"

def calculate(a, b):
    return a + b

def process_data(data):
    return [x * 2 for x in data]
""")

    # Create requirements.txt
    (repo_path / "requirements.txt").write_text("""fastapi==0.128.0
pytest==9.0.2
sqlalchemy==2.0.37
""")

    # Create .gitignore
    (repo_path / ".gitignore").write_text("""__pycache__/
*.pyc
venv/
.env
""")

    return repo_path


# ============================================================================
# Data Factories
# ============================================================================

@pytest.fixture
def project_factory(test_db_session):
    """Factory for creating test projects."""
    def _create_project(
        name="Test Project",
        source_type=SourceType.local_path,
        source="/tmp/test",
        status=ProjectStatus.pending,
        **kwargs
    ):
        from uuid import uuid4
        project = Project(
            id=str(uuid4()),
            name=name,
            source_type=source_type,
            source=source,
            branch=kwargs.get("branch", "main"),
            local_path=kwargs.get("local_path", source),
            status=status,
            settings=kwargs.get("settings"),
            stats=kwargs.get("stats"),
        )
        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)
        return project

    return _create_project
