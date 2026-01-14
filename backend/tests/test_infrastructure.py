"""Smoke test to verify test infrastructure is working."""

import pytest


def test_pytest_works():
    """Verify pytest is configured correctly."""
    assert True


def test_fixtures_available(temp_repo_dir, sample_python_repo):
    """Verify global fixtures are available."""
    # temp_repo_dir fixture
    assert temp_repo_dir.exists()
    assert temp_repo_dir.is_dir()

    # sample_python_repo fixture
    assert sample_python_repo.exists()
    assert sample_python_repo.is_dir()
    assert (sample_python_repo / "main.py").exists()
    assert (sample_python_repo / "utils.py").exists()
    assert (sample_python_repo / "requirements.txt").exists()


def test_database_fixtures(test_db_session):
    """Verify database fixtures work."""
    from sqlalchemy import text

    assert test_db_session is not None
    # Should be able to use the session
    result = test_db_session.execute(text("SELECT 1"))
    assert result is not None


def test_api_client_fixture(client):
    """Verify FastAPI test client works."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_project_factory(project_factory):
    """Verify project factory fixture works."""
    from app.schemas.project import ProjectStatus, SourceType

    project = project_factory(
        name="Test Project",
        source_type=SourceType.local_path,
        source="/tmp/test",
        status=ProjectStatus.pending
    )

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.status == ProjectStatus.pending
    assert project.source_type == SourceType.local_path
