"""Integration tests for Admin API endpoints."""

import pytest
from datetime import datetime

from app.schemas.project import ProjectStatus, SourceType


class TestAdminAPI:
    """Test Admin API endpoints."""

    def test_clear_database(self, client, project_factory, test_db_session):
        """Test DELETE /api/admin/database/clear clears all data."""
        # Create multiple projects
        project1 = project_factory(name="Project 1")
        project2 = project_factory(name="Project 2")
        project3 = project_factory(name="Project 3")
        test_db_session.commit()

        # Verify projects exist
        from app.models.project import Project
        count_before = test_db_session.query(Project).count()
        assert count_before == 3

        # Clear database
        response = client.delete("/api/admin/database/clear")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["message"] == "Database cleared successfully"
        assert data["tables_cleared"] == ["projects"]
        assert data["records_deleted"]["projects"] == 3
        assert "timestamp" in data

        # Verify timestamp is valid ISO format
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)

        # Verify database is actually cleared
        count_after = test_db_session.query(Project).count()
        assert count_after == 0

    def test_clear_database_empty(self, client, test_db_session):
        """Test DELETE /api/admin/database/clear with empty database."""
        # Verify database is empty
        from app.models.project import Project
        count_before = test_db_session.query(Project).count()
        assert count_before == 0

        # Clear database (no-op)
        response = client.delete("/api/admin/database/clear")

        assert response.status_code == 200
        data = response.json()

        # Should still return success
        assert data["message"] == "Database cleared successfully"
        assert data["records_deleted"]["projects"] == 0

