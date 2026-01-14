"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.project import (
    SourceType,
    ProjectStatus,
    ProjectSettings,
    LanguageStats,
    ProjectStats,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListItem,
    ProjectListResponse
)


class TestProjectSchemas:
    """Test Project Pydantic schemas."""

    def test_project_create_valid(self):
        """Test ProjectCreate with valid data."""
        data = {
            "name": "Test Project",
            "source_type": "local_path",
            "source": "/path/to/project",
            "branch": "main",
            "description": "Test description"
        }

        project = ProjectCreate(**data)

        assert project.name == "Test Project"
        assert project.source_type == SourceType.local_path
        assert project.source == "/path/to/project"
        assert project.branch == "main"
        assert project.description == "Test description"

    def test_project_create_defaults(self):
        """Test ProjectCreate default values."""
        data = {
            "name": "Test Project",
            "source_type": "git_url",
            "source": "https://github.com/test/repo.git"
            # branch not provided - should default to "main"
        }

        project = ProjectCreate(**data)

        assert project.branch == "main"
        assert project.description is None
        assert project.settings is None

    def test_project_create_missing_required_field(self):
        """Test ProjectCreate validation fails when required field is missing."""
        # Missing 'name'
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                source_type="local_path",
                source="/path"
            )

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["loc"][0] == "name" for error in errors)

    def test_project_create_empty_name(self):
        """Test ProjectCreate validation fails with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="",  # Empty string - violates min_length=1
                source_type="local_path",
                source="/path"
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "name" for error in errors)

    def test_project_create_name_too_long(self):
        """Test ProjectCreate validation fails when name exceeds max_length."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="x" * 101,  # 101 characters - exceeds max_length=100
                source_type="local_path",
                source="/path"
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "name" for error in errors)

    def test_project_create_invalid_source_type(self):
        """Test ProjectCreate validation fails with invalid source_type."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                name="Test",
                source_type="invalid_type",  # Not a valid SourceType
                source="/path"
            )

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "source_type" for error in errors)

    def test_project_update_partial(self):
        """Test ProjectUpdate allows partial updates."""
        # Only update name
        update = ProjectUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None
        assert update.settings is None

        # Only update description
        update = ProjectUpdate(description="Updated description")
        assert update.name is None
        assert update.description == "Updated description"

    def test_project_update_empty_name_validation(self):
        """Test ProjectUpdate validation fails with empty name."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectUpdate(name="")  # Empty string violates min_length=1

        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "name" for error in errors)

    def test_project_response_serialization(self):
        """Test ProjectResponse schema serialization."""
        data = {
            "id": "test-id",
            "name": "Test Project",
            "description": "Test description",
            "source_type": SourceType.local_path,
            "source": "/path",
            "branch": "main",
            "local_path": "/clone/path",
            "status": ProjectStatus.ready,
            "settings": None,
            "stats": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_analyzed_at": None
        }

        response = ProjectResponse(**data)

        assert response.id == "test-id"
        assert response.name == "Test Project"
        assert response.status == ProjectStatus.ready
        assert isinstance(response.created_at, datetime)

    def test_project_settings_defaults(self):
        """Test ProjectSettings default values."""
        settings = ProjectSettings()

        assert settings.ignore_patterns == ["*.log", "node_modules"]
        assert settings.analyze_languages == ["python", "javascript", "typescript"]

    def test_project_settings_custom(self):
        """Test ProjectSettings with custom values."""
        settings = ProjectSettings(
            ignore_patterns=["*.tmp", "cache/"],
            analyze_languages=["python", "rust"]
        )

        assert settings.ignore_patterns == ["*.tmp", "cache/"]
        assert settings.analyze_languages == ["python", "rust"]

    def test_language_stats(self):
        """Test LanguageStats schema."""
        stats = LanguageStats(files=10, lines=500)

        assert stats.files == 10
        assert stats.lines == 500

    def test_project_stats_defaults(self):
        """Test ProjectStats default values."""
        stats = ProjectStats()

        assert stats.files == 0
        assert stats.directories == 0
        assert stats.lines_of_code == 0
        assert stats.languages == {}

    def test_project_stats_with_languages(self):
        """Test ProjectStats with language data."""
        stats = ProjectStats(
            files=100,
            directories=10,
            lines_of_code=5000,
            languages={
                "Python": LanguageStats(files=50, lines=3000),
                "JavaScript": LanguageStats(files=50, lines=2000)
            }
        )

        assert stats.files == 100
        assert stats.lines_of_code == 5000
        assert "Python" in stats.languages
        assert stats.languages["Python"].lines == 3000

    def test_project_list_item(self):
        """Test ProjectListItem schema."""
        item = ProjectListItem(
            id="test-id",
            name="Test Project",
            source_type=SourceType.git_url,
            source="https://github.com/test/repo.git",
            status=ProjectStatus.ready,
            stats=None,
            last_analyzed_at=None,
            created_at=datetime.utcnow()
        )

        assert item.id == "test-id"
        assert item.name == "Test Project"
        assert item.status == ProjectStatus.ready

    def test_project_list_response(self):
        """Test ProjectListResponse schema."""
        items = [
            ProjectListItem(
                id=f"id-{i}",
                name=f"Project {i}",
                source_type=SourceType.local_path,
                source=f"/path/{i}",
                status=ProjectStatus.ready,
                stats=None,
                last_analyzed_at=None,
                created_at=datetime.utcnow()
            )
            for i in range(3)
        ]

        response = ProjectListResponse(
            items=items,
            total=10,
            limit=3,
            offset=0
        )

        assert len(response.items) == 3
        assert response.total == 10
        assert response.limit == 3
        assert response.offset == 0

    def test_source_type_enum(self):
        """Test SourceType enum values."""
        assert SourceType.git_url.value == "git_url"
        assert SourceType.local_path.value == "local_path"

        # Can create from string
        assert SourceType("git_url") == SourceType.git_url
        assert SourceType("local_path") == SourceType.local_path

    def test_project_status_enum(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.pending.value == "pending"
        assert ProjectStatus.cloning.value == "cloning"
        assert ProjectStatus.scanning.value == "scanning"
        assert ProjectStatus.analyzing.value == "analyzing"
        assert ProjectStatus.ready.value == "ready"
        assert ProjectStatus.failed.value == "failed"

        # Can create from string
        assert ProjectStatus("ready") == ProjectStatus.ready

    def test_project_create_with_settings(self):
        """Test ProjectCreate with custom settings."""
        settings = ProjectSettings(
            ignore_patterns=["*.log"],
            analyze_languages=["python"]
        )

        project = ProjectCreate(
            name="Test",
            source_type=SourceType.local_path,
            source="/path",
            settings=settings
        )

        assert project.settings is not None
        assert project.settings.ignore_patterns == ["*.log"]
        assert project.settings.analyze_languages == ["python"]

    def test_project_response_with_stats(self):
        """Test ProjectResponse with stats."""
        stats = ProjectStats(
            files=50,
            lines_of_code=2500,
            languages={
                "Python": LanguageStats(files=50, lines=2500)
            }
        )

        response = ProjectResponse(
            id="test-id",
            name="Test",
            source_type=SourceType.local_path,
            source="/path",
            branch="main",
            status=ProjectStatus.ready,
            stats=stats,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        assert response.stats is not None
        assert response.stats.files == 50
        assert response.stats.languages["Python"].lines == 2500

    def test_schema_validation_messages(self):
        """Test validation error messages are descriptive."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectCreate(
                # Missing all required fields
            )

        errors = exc_info.value.errors()

        # Should have errors for missing required fields
        assert len(errors) >= 2  # At least name and source_type

        # Check that error messages exist
        for error in errors:
            assert "type" in error
            assert "loc" in error
            assert "msg" in error
