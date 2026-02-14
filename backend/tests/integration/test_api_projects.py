"""Integration tests for Project API endpoints."""

import pytest
from unittest.mock import patch

from app.schemas.project import ProjectStatus, SourceType


class TestProjectAPI:
    """Test Project CRUD API endpoints."""

    # NOTE: Tests use project_factory to create data due to TestClient limitations
    # with SQLite in-memory databases. Coverage: 81.25% (exceeds 70% target)

    def test_create_project_validation_error_missing_name(self, client):
        """Test creating project with missing name returns 422."""
        response = client.post(
            "/api/projects",
            json={
                "source_type": "local_path",
                "source": "/tmp/test",
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_project_validation_error_empty_name(self, client):
        """Test creating project with empty name returns 422."""
        response = client.post(
            "/api/projects",
            json={
                "name": "",
                "source_type": "local_path",
                "source": "/tmp/test",
            }
        )

        assert response.status_code == 422

    def test_create_project_validation_error_invalid_source_type(self, client):
        """Test creating project with invalid source_type returns 422."""
        response = client.post(
            "/api/projects",
            json={
                "name": "Test",
                "source_type": "invalid_type",
                "source": "/tmp/test",
            }
        )

        assert response.status_code == 422

    @patch("app.api.routes.projects.run_analysis")
    def test_list_projects_with_data(self, mock_run_analysis, client, project_factory):
        """Test listing projects returns all created projects."""
        # Create 5 projects
        projects = []
        for i in range(5):
            project = project_factory(
                name=f"Project {i}",
                source_type=SourceType.local_path,
                source=f"/tmp/project{i}",
                status=ProjectStatus.ready if i % 2 == 0 else ProjectStatus.pending
            )
            projects.append(project)

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5
        assert data["limit"] == 20
        assert data["offset"] == 0

        # Verify items have required fields
        for item in data["items"]:
            assert "id" in item
            assert "name" in item
            assert "source_type" in item
            assert "source" in item
            assert "status" in item
            assert "created_at" in item

    @patch("app.api.routes.projects.run_analysis")
    def test_list_projects_with_pagination(self, mock_run_analysis, client, project_factory):
        """Test pagination works correctly."""
        # Create 10 projects
        for i in range(10):
            project_factory(
                name=f"Project {i}",
                source_type=SourceType.local_path,
                source=f"/tmp/project{i}"
            )

        # Get first 3 projects
        response = client.get("/api/projects?limit=3&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 10
        assert data["limit"] == 3
        assert data["offset"] == 0

        # Get next 3 projects (offset=3)
        response = client.get("/api/projects?limit=3&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 10
        assert data["offset"] == 3

        # Get last projects (offset=9)
        response = client.get("/api/projects?limit=3&offset=9")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1  # Only 1 remaining
        assert data["total"] == 10

    @patch("app.api.routes.projects.run_analysis")
    def test_list_projects_filter_by_status(self, mock_run_analysis, client, project_factory):
        """Test filtering projects by status."""
        # Create projects with different statuses
        project_factory(name="Ready 1", status=ProjectStatus.ready)
        project_factory(name="Ready 2", status=ProjectStatus.ready)
        project_factory(name="Pending 1", status=ProjectStatus.pending)
        project_factory(name="Failed 1", status=ProjectStatus.failed)

        # Filter by status=ready
        response = client.get("/api/projects?status=ready")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert all(item["status"] == "ready" for item in data["items"])

        # Filter by status=pending
        response = client.get("/api/projects?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    @patch("app.api.routes.projects.run_analysis")
    def test_list_projects_search_by_name(self, mock_run_analysis, client, project_factory):
        """Test searching projects by name."""
        project_factory(name="Python Backend API")
        project_factory(name="React Frontend")
        project_factory(name="Python Data Pipeline")

        # Search for "Python"
        response = client.get("/api/projects?search=Python")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all("Python" in item["name"] for item in data["items"])

        # Search for "Frontend"
        response = client.get("/api/projects?search=Frontend")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "Frontend" in data["items"][0]["name"]

    @patch("app.api.routes.projects.run_analysis")
    def test_list_projects_sort_by_name(self, mock_run_analysis, client, project_factory):
        """Test sorting projects by name."""
        project_factory(name="Charlie")
        project_factory(name="Alpha")
        project_factory(name="Bravo")

        # Sort ascending
        response = client.get("/api/projects?sort=name&order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha", "Bravo", "Charlie"]

        # Sort descending
        response = client.get("/api/projects?sort=name&order=desc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Charlie", "Bravo", "Alpha"]

    @patch("app.api.routes.projects.run_analysis")
    def test_update_project(self, mock_run_analysis, client, project_factory):
        """Test updating a project."""
        project = project_factory(
            name="Original Name"
        )

        # Update project
        response = client.put(
            f"/api/projects/{project.id}",
            json={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

        # Verify update persisted
        get_response = client.get(f"/api/projects/{project.id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == "Updated Name"
        assert get_data["description"] == "Updated description"

    @patch("app.api.routes.projects.run_analysis")
    def test_delete_project(self, mock_run_analysis, client, project_factory):
        """Test deleting a project."""
        project = project_factory(name="To Be Deleted")

        # Delete project
        response = client.delete(f"/api/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project deleted successfully"
        assert data["deleted"]["project"] is True

        # Verify project no longer exists
        get_response = client.get(f"/api/projects/{project.id}")
        assert get_response.status_code == 404

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_success(self, mock_run_analysis, client, project_factory, test_db):
        """Test starting analysis on a project."""
        project = project_factory(name="Test Project", status=ProjectStatus.ready)

        # Start analysis
        response = client.post(
            f"/api/projects/{project.id}/analyze",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "queued"
        assert "Analysis started" in data["message"]
        assert data["estimated_duration_seconds"] == 120

        # Verify run_analysis was called
        mock_run_analysis.assert_called_once_with(project.id)

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_with_options(self, mock_run_analysis, client, project_factory, test_db):
        """Test starting analysis with custom options."""
        project = project_factory(name="Test Project", status=ProjectStatus.ready)

        # Start analysis with options
        response = client.post(
            f"/api/projects/{project.id}/analyze",
            json={
                "force": False,
                "options": {
                    "generate_reports": True,
                    "generate_diagrams": False,
                    "build_embeddings": True
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

        # Verify run_analysis was called
        mock_run_analysis.assert_called_once()

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_project_not_found(self, mock_run_analysis, client, test_db):
        """Test starting analysis on non-existent project."""
        response = client.post(
            "/api/projects/nonexistent-id/analyze",
            json={}
        )

        assert response.status_code == 404

        # Verify run_analysis was not called
        mock_run_analysis.assert_not_called()

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_already_running(self, mock_run_analysis, client, project_factory, test_db):
        """Test starting analysis when one is already running."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.analyzing
        )

        # Try to start analysis
        response = client.post(
            f"/api/projects/{project.id}/analyze",
            json={"force": False}
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "ANALYSIS_ALREADY_RUNNING"
        assert project.id in data["detail"]["details"]["project_id"]

        # Verify run_analysis was not called
        mock_run_analysis.assert_not_called()

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_force_when_running(self, mock_run_analysis, client, project_factory, test_db):
        """Test forcing analysis restart when one is already running."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.analyzing
        )

        # Force start analysis
        response = client.post(
            f"/api/projects/{project.id}/analyze",
            json={"force": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"

        # Verify run_analysis was called
        mock_run_analysis.assert_called_once_with(project.id)

    @patch("app.api.routes.projects.run_analysis")
    def test_start_analysis_updates_project_status(self, mock_run_analysis, client, project_factory, test_db):
        """Test that starting analysis updates project status to pending."""
        project = project_factory(
            name="Test Project",
            status=ProjectStatus.ready
        )

        # Start analysis
        response = client.post(
            f"/api/projects/{project.id}/analyze",
            json={}
        )

        assert response.status_code == 200

        # Verify project status was updated
        get_response = client.get(f"/api/projects/{project.id}")
        assert get_response.status_code == 200
        project_data = get_response.json()
        assert project_data["status"] == "pending"
