"""Unit tests for database models."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.project import Project
from app.schemas.project import ProjectStatus, SourceType


class TestProjectModel:
    """Test Project model."""

    def test_project_creation(self, test_db_session):
        """Test creating a Project model instance."""
        project_id = str(uuid4())
        project = Project(
            id=project_id,
            name="Test Project",
            description="A test project",
            source_type=SourceType.local_path,
            source="/path/to/project",
            branch="main",
            status=ProjectStatus.pending
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        assert project.id == project_id
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.source_type == SourceType.local_path
        assert project.source == "/path/to/project"
        assert project.branch == "main"
        assert project.status == ProjectStatus.pending
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_default_values(self, test_db_session):
        """Test Project model default values."""
        project = Project(
            id=str(uuid4()),
            name="Default Test",
            source_type=SourceType.git_url,
            source="https://github.com/test/repo.git"
            # branch and status not provided - should use defaults
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # Check defaults
        assert project.branch == "main"
        assert project.status == ProjectStatus.pending
        assert project.description is None
        assert project.settings is None
        assert project.stats is None
        assert project.local_path is None
        assert project.last_analyzed_at is None

    def test_project_to_dict(self, test_db_session):
        """Test Project.to_dict() serialization."""
        project_id = str(uuid4())
        now = datetime.utcnow()

        project = Project(
            id=project_id,
            name="Serialization Test",
            description="Testing to_dict",
            source_type=SourceType.local_path,
            source="/test/path",
            branch="develop",
            local_path="/clone/path",
            status=ProjectStatus.ready,
            settings={"key": "value"},
            stats={"files": 10, "lines_of_code": 100}
        )
        project.last_analyzed_at = now

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # Convert to dict
        data = project.to_dict()

        # Verify all fields
        assert data["id"] == project_id
        assert data["name"] == "Serialization Test"
        assert data["description"] == "Testing to_dict"
        assert data["source_type"] == SourceType.local_path
        assert data["source"] == "/test/path"
        assert data["branch"] == "develop"
        assert data["local_path"] == "/clone/path"
        assert data["status"] == ProjectStatus.ready
        assert data["settings"] == {"key": "value"}
        assert data["stats"] == {"files": 10, "lines_of_code": 100}
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        assert data["last_analyzed_at"] == now

    def test_project_enum_conversions(self, test_db_session):
        """Test enum conversions for ProjectStatus and SourceType."""
        project = Project(
            id=str(uuid4()),
            name="Enum Test",
            source_type=SourceType.git_url,
            source="https://example.com/repo.git",
            status=ProjectStatus.analyzing
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # Enums should be properly stored and retrieved
        assert project.source_type == SourceType.git_url
        assert project.status == ProjectStatus.analyzing

        # Can be compared with enum values
        assert project.source_type in [SourceType.git_url, SourceType.local_path]
        assert project.status in [
            ProjectStatus.pending,
            ProjectStatus.cloning,
            ProjectStatus.scanning,
            ProjectStatus.analyzing,
            ProjectStatus.ready,
            ProjectStatus.failed
        ]

    def test_project_status_transitions(self, test_db_session):
        """Test updating project status."""
        project = Project(
            id=str(uuid4()),
            name="Status Test",
            source_type=SourceType.local_path,
            source="/test",
            status=ProjectStatus.pending
        )

        test_db_session.add(project)
        test_db_session.commit()

        # Update status
        project.status = ProjectStatus.cloning
        test_db_session.commit()
        test_db_session.refresh(project)
        assert project.status == ProjectStatus.cloning

        # Update to analyzing
        project.status = ProjectStatus.analyzing
        test_db_session.commit()
        test_db_session.refresh(project)
        assert project.status == ProjectStatus.analyzing

        # Update to ready
        project.status = ProjectStatus.ready
        test_db_session.commit()
        test_db_session.refresh(project)
        assert project.status == ProjectStatus.ready

    def test_project_json_fields(self, test_db_session):
        """Test JSON fields (settings and stats)."""
        complex_settings = {
            "ignore_patterns": ["*.log", "node_modules"],
            "analyze_languages": ["python", "javascript"],
            "max_file_size": 10
        }

        complex_stats = {
            "files": 100,
            "lines_of_code": 5000,
            "languages": {
                "Python": {"files": 50, "lines": 3000},
                "JavaScript": {"files": 50, "lines": 2000}
            }
        }

        project = Project(
            id=str(uuid4()),
            name="JSON Test",
            source_type=SourceType.local_path,
            source="/test",
            settings=complex_settings,
            stats=complex_stats
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # JSON fields should be properly stored and retrieved
        assert project.settings == complex_settings
        assert project.stats == complex_stats
        assert project.stats["files"] == 100
        assert project.stats["languages"]["Python"]["lines"] == 3000

    def test_project_repr(self, test_db_session):
        """Test Project __repr__ method."""
        project_id = str(uuid4())
        project = Project(
            id=project_id,
            name="Repr Test",
            source_type=SourceType.local_path,
            source="/test",
            status=ProjectStatus.ready
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        repr_str = repr(project)

        assert "Project" in repr_str
        assert project_id in repr_str
        assert "Repr Test" in repr_str
        assert "ready" in repr_str

    def test_project_timestamps(self, test_db_session):
        """Test project timestamps are set correctly."""
        project = Project(
            id=str(uuid4()),
            name="Timestamp Test",
            source_type=SourceType.local_path,
            source="/test"
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # Timestamps should be set
        assert project.created_at is not None
        assert project.updated_at is not None
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

        # last_analyzed_at should be None initially
        assert project.last_analyzed_at is None

        # Set last_analyzed_at
        now = datetime.utcnow()
        project.last_analyzed_at = now
        test_db_session.commit()
        test_db_session.refresh(project)

        assert project.last_analyzed_at == now

    def test_project_nullable_fields(self, test_db_session):
        """Test nullable fields can be None."""
        project = Project(
            id=str(uuid4()),
            name="Nullable Test",
            source_type=SourceType.git_url,
            source="https://example.com/repo.git",
            # Optional fields not provided
        )

        test_db_session.add(project)
        test_db_session.commit()
        test_db_session.refresh(project)

        # Nullable fields should be None
        assert project.description is None
        assert project.local_path is None
        assert project.settings is None
        assert project.stats is None
        assert project.last_analyzed_at is None
