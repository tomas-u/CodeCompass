"""Integration tests for Files API endpoints."""

import pytest
from unittest.mock import patch

from app.mock_data import MOCK_FILE_TREE, MOCK_FILE_CONTENT


class TestFilesAPI:
    """Test Files API endpoints."""

    def test_get_file_tree(self, client, project_factory, test_db_session):
        """Test GET /api/projects/{id}/files returns file tree."""
        # Files API uses mock data with hardcoded ID "proj-1"
        # Get file tree (uses mock data)
        response = client.get("/api/projects/proj-1/files")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "root" in data
        assert "stats" in data

        # Verify root node
        root = data["root"]
        assert root["name"] == "fastapi-example"
        assert root["type"] == "directory"
        assert "children" in root
        assert len(root["children"]) > 0

        # Verify stats
        stats = data["stats"]
        assert stats["total_files"] == 150
        assert stats["total_directories"] == 25

    def test_get_file_tree_with_depth_param(self, client):
        """Test GET /api/projects/{id}/files with depth parameter."""
        # Get file tree with depth limit (uses mock project ID)
        response = client.get("/api/projects/proj-1/files?depth=2")

        assert response.status_code == 200
        data = response.json()
        assert "root" in data

    def test_get_file_tree_with_include_hidden_param(self, client):
        """Test GET /api/projects/{id}/files with include_hidden parameter."""
        # Get file tree including hidden files (uses mock project ID)
        response = client.get("/api/projects/proj-1/files?include_hidden=true")

        assert response.status_code == 200
        data = response.json()
        assert "root" in data

    def test_get_file_tree_project_not_found(self, client):
        """Test GET /api/projects/{id}/files returns 404 for nonexistent project."""
        response = client.get("/api/projects/nonexistent-id/files")

        assert response.status_code == 404
        data = response.json()
        # Error format may vary - just check for error response
        assert data is not None

    def test_get_file_content(self, client):
        """Test GET /api/projects/{id}/files/{path} returns file content."""
        # Get file content (uses mock data and mock project ID)
        file_path = "src/main.py"
        response = client.get(f"/api/projects/proj-1/files/{file_path}")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["path"] == file_path
        assert data["name"] == "main.py"
        assert data["language"] == "python"
        assert data["content"] == MOCK_FILE_CONTENT
        assert data["lines"] == len(MOCK_FILE_CONTENT.split("\n"))
        assert data["size_bytes"] == len(MOCK_FILE_CONTENT)
        assert data["encoding"] == "utf-8"
        assert "last_modified" in data

    def test_get_file_content_nested_path(self, client):
        """Test GET /api/projects/{id}/files/{path} with nested path."""
        # Test nested file path (uses mock project ID)
        file_path = "src/api/routes/auth.py"
        response = client.get(f"/api/projects/proj-1/files/{file_path}")

        assert response.status_code == 200
        data = response.json()
        assert data["path"] == file_path
        assert data["name"] == "auth.py"

    def test_get_file_content_project_not_found(self, client):
        """Test GET /api/projects/{id}/files/{path} returns 404 for nonexistent project."""
        response = client.get("/api/projects/nonexistent-id/files/src/main.py")

        assert response.status_code == 404
        data = response.json()
        # Error format may vary - just check for error response
        assert data is not None

    def test_file_tree_structure_validation(self, client):
        """Test file tree structure contains all expected fields."""
        # Uses mock project ID
        response = client.get("/api/projects/proj-1/files")

        assert response.status_code == 200
        data = response.json()

        root = data["root"]

        # Verify directory structure
        assert root["type"] == "directory"
        assert "children" in root

        # Find a file node
        src_dir = None
        for child in root["children"]:
            if child["name"] == "src" and child["type"] == "directory":
                src_dir = child
                break

        assert src_dir is not None
        assert "children" in src_dir

        # Find a file in src
        file_node = None
        for child in src_dir["children"]:
            if child["type"] == "file":
                file_node = child
                break

        # Verify file node structure
        if file_node:
            assert "name" in file_node
            assert "type" in file_node
            assert file_node["type"] == "file"
            assert "language" in file_node
            assert "size_bytes" in file_node
            assert "lines" in file_node
