"""Unit tests for ReportGenerator service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.report_generator import ReportGenerator
from app.schemas.report import ReportType
from app.schemas.project import ProjectStatus


class TestReportGeneratorInit:
    """Tests for ReportGenerator initialization."""

    def test_init_with_db_session(self, test_db_session):
        """Test that ReportGenerator initializes with database session."""
        generator = ReportGenerator(test_db_session)
        assert generator.db is test_db_session
        assert generator._llm_provider is None
        assert generator._embedding_provider is None
        assert generator._vector_service is None


class TestParseSections:
    """Tests for _parse_sections method."""

    def test_parse_simple_sections(self, test_db_session):
        """Test parsing markdown with simple sections."""
        generator = ReportGenerator(test_db_session)

        content = """## 1. Overview
This is the overview section.
It has multiple lines.

## 2. Details
Here are the details.

## 3. Summary
Final summary."""

        sections = generator._parse_sections(content)

        assert len(sections) == 3
        assert sections[0]["title"] == "Overview"
        assert sections[0]["id"] == "overview"
        assert "overview section" in sections[0]["content"]
        assert sections[1]["title"] == "Details"
        assert sections[2]["title"] == "Summary"

    def test_parse_sections_without_numbers(self, test_db_session):
        """Test parsing sections without numbered prefixes."""
        generator = ReportGenerator(test_db_session)

        content = """## Executive Summary
Brief overview here.

## Technical Details
Technical content here."""

        sections = generator._parse_sections(content)

        assert len(sections) == 2
        assert sections[0]["title"] == "Executive Summary"
        assert sections[0]["id"] == "executive-summary"
        assert sections[1]["title"] == "Technical Details"

    def test_parse_empty_content(self, test_db_session):
        """Test parsing empty content returns empty list."""
        generator = ReportGenerator(test_db_session)
        sections = generator._parse_sections("")
        assert sections == []

    def test_parse_no_sections(self, test_db_session):
        """Test parsing content without sections."""
        generator = ReportGenerator(test_db_session)
        content = "Just some text without any sections."
        sections = generator._parse_sections(content)
        assert sections == []

    def test_parse_sections_with_code_blocks(self, test_db_session):
        """Test parsing sections containing code blocks."""
        generator = ReportGenerator(test_db_session)

        content = """## 1. Code Example
Here is some code:
```python
def hello():
    print("Hello")
```

## 2. Another Section
More content here."""

        sections = generator._parse_sections(content)

        assert len(sections) == 2
        assert "```python" in sections[0]["content"]
        assert "def hello():" in sections[0]["content"]


class TestSlugify:
    """Tests for _slugify method."""

    def test_slugify_simple(self, test_db_session):
        """Test basic slugify functionality."""
        generator = ReportGenerator(test_db_session)

        assert generator._slugify("Hello World") == "hello-world"
        assert generator._slugify("Overview") == "overview"
        assert generator._slugify("Tech Stack") == "tech-stack"

    def test_slugify_with_numbers(self, test_db_session):
        """Test slugify with numbers."""
        generator = ReportGenerator(test_db_session)

        assert generator._slugify("1. Introduction") == "1-introduction"
        assert generator._slugify("Section 2") == "section-2"

    def test_slugify_special_characters(self, test_db_session):
        """Test slugify removes special characters."""
        generator = ReportGenerator(test_db_session)

        assert generator._slugify("Hello! World?") == "hello-world"
        assert generator._slugify("Code & Architecture") == "code-architecture"

    def test_slugify_preserves_hyphens(self, test_db_session):
        """Test slugify with existing hyphens."""
        generator = ReportGenerator(test_db_session)

        # Multiple consecutive hyphens become one
        assert generator._slugify("A - B") == "a-b"


class TestExtractMetadata:
    """Tests for _extract_metadata method."""

    def test_extract_languages(self, test_db_session, project_factory):
        """Test extracting languages from project stats."""
        project = project_factory(
            name="test-project",
            stats={"languages": {"Python": {"files": 10}, "JavaScript": {"files": 5}}},
        )

        generator = ReportGenerator(test_db_session)
        content = "This is a basic report."

        metadata = generator._extract_metadata(project, content)

        assert "Python" in metadata["languages"]
        assert "JavaScript" in metadata["languages"]

    def test_extract_frameworks(self, test_db_session, project_factory):
        """Test extracting frameworks from content."""
        project = project_factory(name="test-project", stats={})

        generator = ReportGenerator(test_db_session)
        content = """
        This project uses FastAPI for the backend.
        The frontend is built with React.
        """

        metadata = generator._extract_metadata(project, content)

        assert "fastapi" in metadata["frameworks"]
        assert "react" in metadata["frameworks"]

    def test_extract_patterns(self, test_db_session, project_factory):
        """Test extracting architecture patterns from content."""
        project = project_factory(name="test-project", stats={})

        generator = ReportGenerator(test_db_session)
        content = """
        This codebase follows the MVC pattern.
        It uses a repository pattern for data access.
        """

        metadata = generator._extract_metadata(project, content)

        assert "mvc" in metadata["patterns_detected"]
        assert "repository" in metadata["patterns_detected"]

    def test_extract_empty_stats(self, test_db_session, project_factory):
        """Test extracting metadata with empty stats."""
        project = project_factory(name="test-project", stats=None)

        generator = ReportGenerator(test_db_session)
        content = "Basic content."

        metadata = generator._extract_metadata(project, content)

        assert metadata["languages"] == []


class TestBuildSummaryPrompt:
    """Tests for _build_summary_prompt method."""

    def test_build_prompt_with_stats(self, test_db_session, project_factory):
        """Test building summary prompt with full stats."""
        project = project_factory(
            name="MyProject",
            description="A test project",
            stats={
                "files": 50,
                "lines_of_code": 5000,
                "directories": 10,
                "languages": {"Python": {"files": 30}, "JavaScript": {"files": 20}},
            },
        )

        generator = ReportGenerator(test_db_session)
        prompt = generator._build_summary_prompt(project)

        assert "MyProject" in prompt
        assert "A test project" in prompt
        assert "50" in prompt  # files
        assert "5000" in prompt  # LOC
        assert "Python" in prompt
        assert "JavaScript" in prompt

    def test_build_prompt_without_description(self, test_db_session, project_factory):
        """Test building prompt without description."""
        project = project_factory(name="MyProject", description=None, stats={})

        generator = ReportGenerator(test_db_session)
        prompt = generator._build_summary_prompt(project)

        assert "No description provided" in prompt

    def test_build_prompt_without_languages(self, test_db_session, project_factory):
        """Test building prompt without language breakdown."""
        project = project_factory(name="MyProject", stats={})

        generator = ReportGenerator(test_db_session)
        prompt = generator._build_summary_prompt(project)

        assert "No language breakdown available" in prompt


class TestBuildDependenciesPrompt:
    """Tests for _build_dependencies_prompt method."""

    def test_build_prompt_with_dependency_graph(self, test_db_session, project_factory):
        """Test building dependencies prompt with graph data."""
        project = project_factory(
            name="MyProject",
            stats={
                "files": 30,
                "lines_of_code": 3000,
                "languages": {"Python": {"files": 30}},
                "dependency_graph": {
                    "nodes": 15,
                    "edges": 25,
                    "max_depth": 4,
                },
            },
        )

        generator = ReportGenerator(test_db_session)
        prompt = generator._build_dependencies_prompt(project)

        assert "MyProject" in prompt
        assert "15" in prompt  # nodes
        assert "25" in prompt  # edges

    def test_build_prompt_without_dependency_graph(self, test_db_session, project_factory):
        """Test building dependencies prompt without graph data."""
        project = project_factory(name="MyProject", stats={"files": 10})

        generator = ReportGenerator(test_db_session)
        prompt = generator._build_dependencies_prompt(project)

        assert "Dependency graph data not available" in prompt


class TestSaveReport:
    """Tests for _save_report method."""

    def test_save_new_report(self, test_db_session, project_factory):
        """Test saving a new report."""
        project = project_factory(name="test-project")

        generator = ReportGenerator(test_db_session)
        report = generator._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Test Summary",
            content="Test content",
            sections=[{"id": "overview", "title": "Overview", "content": "Content"}],
            metadata={"languages": ["Python"]},
            model_used="test-model",
            generation_time_ms=1000,
        )

        assert report.id is not None
        assert report.project_id == project.id
        assert report.type == "summary"
        assert report.title == "Test Summary"
        assert report.content == "Test content"
        assert len(report.sections) == 1

    def test_update_existing_report(self, test_db_session, project_factory):
        """Test updating an existing report."""
        project = project_factory(name="test-project")

        generator = ReportGenerator(test_db_session)

        # Create initial report
        report1 = generator._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Initial Title",
            content="Initial content",
            sections=[],
            metadata={},
            model_used="model-v1",
            generation_time_ms=500,
        )
        original_id = report1.id

        # Update the report
        report2 = generator._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Updated Title",
            content="Updated content",
            sections=[{"id": "new", "title": "New", "content": "New content"}],
            metadata={"languages": ["Python"]},
            model_used="model-v2",
            generation_time_ms=600,
        )

        # Should update existing, not create new
        assert report2.id == original_id
        assert report2.title == "Updated Title"
        assert report2.content == "Updated content"
        assert report2.model_used == "model-v2"

    def test_save_different_report_types(self, test_db_session, project_factory):
        """Test saving reports of different types."""
        project = project_factory(name="test-project")

        generator = ReportGenerator(test_db_session)

        # Save summary report
        summary = generator._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Summary",
            content="Summary content",
            sections=[],
            metadata={},
            model_used="test-model",
            generation_time_ms=100,
        )

        # Save architecture report
        arch = generator._save_report(
            project_id=project.id,
            report_type=ReportType.architecture,
            title="Architecture",
            content="Architecture content",
            sections=[],
            metadata={},
            model_used="test-model",
            generation_time_ms=200,
        )

        # Both should exist with different IDs
        assert summary.id != arch.id
        assert summary.type == "summary"
        assert arch.type == "architecture"


class TestGenerateReport:
    """Tests for generate_report method with mocked LLM."""

    @pytest.mark.asyncio
    async def test_generate_report_project_not_found(self, test_db_session):
        """Test generating report for non-existent project."""
        generator = ReportGenerator(test_db_session)

        with pytest.raises(ValueError, match="Project not found"):
            await generator.generate_report("nonexistent-id", ReportType.summary)

    @pytest.mark.asyncio
    async def test_generate_report_project_not_ready(self, test_db_session, project_factory):
        """Test generating report for project that's not ready."""
        project = project_factory(name="test-project", status=ProjectStatus.pending)

        generator = ReportGenerator(test_db_session)

        with pytest.raises(ValueError, match="not ready"):
            await generator.generate_report(project.id, ReportType.summary)

    @pytest.mark.asyncio
    async def test_generate_report_returns_existing(self, test_db_session, project_factory):
        """Test that existing report is returned without force."""
        project = project_factory(name="test-project", status=ProjectStatus.ready)

        generator = ReportGenerator(test_db_session)

        # Create existing report
        existing_report = generator._save_report(
            project_id=project.id,
            report_type=ReportType.summary,
            title="Existing Summary",
            content="Existing content",
            sections=[],
            metadata={},
            model_used="old-model",
            generation_time_ms=100,
        )

        # Should return existing without generating
        report = await generator.generate_report(project.id, ReportType.summary, force=False)
        assert report.id == existing_report.id
        assert report.content == "Existing content"

    @pytest.mark.asyncio
    async def test_generate_report_llm_unavailable(self, test_db_session, project_factory):
        """Test error when LLM is unavailable."""
        project = project_factory(name="test-project", status=ProjectStatus.ready)

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider to be unhealthy
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=False)
        generator._llm_provider = mock_provider

        with pytest.raises(RuntimeError, match="LLM provider is not available"):
            await generator.generate_report(project.id, ReportType.summary, force=True)

    @pytest.mark.asyncio
    async def test_generate_summary_report_success(self, test_db_session, project_factory):
        """Test successful summary report generation."""
        project = project_factory(
            name="test-project",
            status=ProjectStatus.ready,
            stats={"files": 10, "lines_of_code": 1000, "languages": {"Python": {"files": 10}}},
        )

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider
        mock_response = MagicMock()
        mock_response.content = """## 1. Overview
This is a Python project with 10 files.

## 2. Quick Stats
| Metric | Value |
|--------|-------|
| Files | 10 |

## 3. Getting Started
Run pip install -r requirements.txt."""
        mock_response.model = "test-model-v1"

        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.chat = AsyncMock(return_value=mock_response)
        generator._llm_provider = mock_provider

        report = await generator.generate_report(project.id, ReportType.summary, force=True)

        assert report is not None
        assert report.project_id == project.id
        assert report.type == "summary"
        assert report.title == "Project Summary"
        assert "Python project" in report.content
        assert len(report.sections) >= 2

    @pytest.mark.asyncio
    async def test_generate_architecture_report_success(self, test_db_session, project_factory):
        """Test successful architecture report generation."""
        project = project_factory(
            name="test-project",
            status=ProjectStatus.ready,
            stats={
                "files": 20,
                "lines_of_code": 2000,
                "directories": 5,
                "languages": {"Python": {"files": 15, "lines": 1500}, "JavaScript": {"files": 5, "lines": 500}},
            },
        )

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider
        mock_response = MagicMock()
        mock_response.content = """## 1. Executive Summary
This is a full-stack web application using FastAPI and React.

## 2. Technology Stack
- Python with FastAPI
- JavaScript with React

## 3. Architecture Pattern
The codebase follows an MVC pattern.

## 4. Key Components
Main modules include api, services, and models.

## 5. Data Flow
Requests flow through the API layer.

## 6. Dependencies
External: FastAPI, SQLAlchemy

## 7. Recommendations
Consider adding more tests."""
        mock_response.model = "test-model"

        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.chat = AsyncMock(return_value=mock_response)
        generator._llm_provider = mock_provider

        # Mock embedding and vector services
        mock_embedding = AsyncMock()
        mock_embedding.health_check = AsyncMock(return_value=False)
        generator._embedding_provider = mock_embedding

        mock_vector = AsyncMock()
        mock_vector.health_check = AsyncMock(return_value=False)
        generator._vector_service = mock_vector

        report = await generator.generate_report(project.id, ReportType.architecture, force=True)

        assert report is not None
        assert report.type == "architecture"
        assert report.title == "Architecture Overview"
        assert "full-stack web application" in report.content
        assert "fastapi" in report.report_metadata.get("frameworks", [])

    @pytest.mark.asyncio
    async def test_generate_dependencies_report_success(self, test_db_session, project_factory):
        """Test successful dependencies report generation."""
        project = project_factory(
            name="test-project",
            status=ProjectStatus.ready,
            stats={
                "files": 15,
                "lines_of_code": 1500,
                "languages": {"Python": {"files": 15}},
                "dependency_graph": {"nodes": 10, "edges": 15, "max_depth": 3},
            },
        )

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider
        mock_response = MagicMock()
        mock_response.content = """## 1. Overview
The project has a well-structured dependency graph.

## 2. External Dependencies
Uses FastAPI, SQLAlchemy, Pydantic.

## 3. Internal Dependencies
Modules are properly organized.

## 4. Dependency Graph Summary
10 modules with 15 connections.

## 5. Potential Issues
No circular dependencies detected.

## 6. Recommendations
Consider reducing coupling in service layer."""
        mock_response.model = "test-model"

        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.chat = AsyncMock(return_value=mock_response)
        generator._llm_provider = mock_provider

        report = await generator.generate_report(project.id, ReportType.dependencies, force=True)

        assert report is not None
        assert report.type == "dependencies"
        assert report.title == "Dependency Analysis"

    @pytest.mark.asyncio
    async def test_generate_unsupported_report_type(self, test_db_session, project_factory):
        """Test error for unsupported report type."""
        project = project_factory(name="test-project", status=ProjectStatus.ready)

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        generator._llm_provider = mock_provider

        # Create a fake enum value
        with pytest.raises(ValueError, match="Unsupported report type"):
            # Use a mock that looks like a ReportType but isn't one of the handled values
            fake_type = MagicMock()
            fake_type.value = "unknown"
            await generator.generate_report(project.id, fake_type, force=True)


class TestGenerateAllReports:
    """Tests for generate_all_reports method."""

    @pytest.mark.asyncio
    async def test_generate_all_reports_success(self, test_db_session, project_factory):
        """Test generating all report types."""
        project = project_factory(
            name="test-project",
            status=ProjectStatus.ready,
            stats={"files": 10, "lines_of_code": 1000, "languages": {"Python": {"files": 10}}},
        )

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider
        mock_response = MagicMock()
        mock_response.content = "## 1. Overview\nTest content."
        mock_response.model = "test-model"

        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.chat = AsyncMock(return_value=mock_response)
        generator._llm_provider = mock_provider

        # Mock embedding and vector services
        mock_embedding = AsyncMock()
        mock_embedding.health_check = AsyncMock(return_value=False)
        generator._embedding_provider = mock_embedding

        mock_vector = AsyncMock()
        mock_vector.health_check = AsyncMock(return_value=False)
        generator._vector_service = mock_vector

        reports = await generator.generate_all_reports(project.id, force=True)

        # Should generate 3 reports: summary, architecture, dependencies
        assert len(reports) == 3
        report_types = {r.type for r in reports}
        assert "summary" in report_types
        assert "architecture" in report_types
        assert "dependencies" in report_types

    @pytest.mark.asyncio
    async def test_generate_all_reports_partial_failure(self, test_db_session, project_factory):
        """Test that partial failures don't stop other reports."""
        project = project_factory(
            name="test-project",
            status=ProjectStatus.ready,
            stats={"files": 10},
        )

        generator = ReportGenerator(test_db_session)

        # Mock LLM provider to fail sometimes
        call_count = 0

        async def mock_chat(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("LLM error")
            response = MagicMock()
            response.content = "## 1. Overview\nTest content."
            response.model = "test-model"
            return response

        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.chat = mock_chat
        generator._llm_provider = mock_provider

        # Mock embedding and vector services
        mock_embedding = AsyncMock()
        mock_embedding.health_check = AsyncMock(return_value=False)
        generator._embedding_provider = mock_embedding

        mock_vector = AsyncMock()
        mock_vector.health_check = AsyncMock(return_value=False)
        generator._vector_service = mock_vector

        reports = await generator.generate_all_reports(project.id, force=True)

        # Should have 2 successful reports (one failed)
        assert len(reports) == 2
