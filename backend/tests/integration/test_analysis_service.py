"""Integration tests for Analysis Service."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.models.project import Project as ProjectModel
from app.schemas.project import ProjectStatus, SourceType
from app.services.analysis_service import run_analysis, re_analyze, cancel_analysis


class SessionWrapper:
    """Wrapper to prevent test session from being closed."""
    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        if name == "close":
            return lambda: None  # No-op close
        return getattr(self._session, name)


class TestAnalysisService:
    """Test Analysis Service integration."""

    def _mock_session_local(self, test_db_session, mocker):
        """Helper to mock SessionLocal and prevent session close."""
        # Create wrapper that prevents close
        wrapper = SessionWrapper(test_db_session)
        # Mock SessionLocal to return wrapped session
        mocker.patch(
            "app.services.analysis_service.SessionLocal",
            return_value=wrapper
        )

    @pytest.mark.asyncio
    async def test_run_analysis_local_path_success(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test successful analysis with local path."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Local Path Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.pending
        )

        # Run analysis
        await run_analysis(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify final status
        assert project.status == ProjectStatus.ready
        assert project.last_analyzed_at is not None

        # Verify stats populated
        assert project.stats is not None
        assert project.stats["files"] > 0
        assert project.stats["lines_of_code"] > 0
        assert "languages" in project.stats

    @pytest.mark.asyncio
    async def test_run_analysis_git_url_success(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test successful analysis with Git URL (mocked clone)."""
        self._mock_session_local(test_db_session, mocker)

        # Mock git service clone to return success
        mock_clone = mocker.patch(
            "app.services.analysis_service.GitService.clone_repository",
            return_value=(True, None)
        )

        project = project_factory(
            name="Git URL Test",
            source_type=SourceType.git_url,
            source="https://github.com/test/repo.git",
            branch="main",
            status=ProjectStatus.pending
        )

        # Create mock clone directory with sample content
        clone_dir = Path("./repos") / project.id
        clone_dir.mkdir(parents=True, exist_ok=True)

        # Copy sample repo content to clone directory
        import shutil
        for item in sample_python_repo.iterdir():
            if item.is_file():
                shutil.copy(item, clone_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, clone_dir / item.name, dirs_exist_ok=True)

        try:
            # Run analysis
            await run_analysis(project.id)

            # Verify git clone was called
            assert mock_clone.called
            mock_clone.assert_called_once()

            # Refresh project from database
            test_db_session.refresh(project)

            # Verify final status
            assert project.status == ProjectStatus.ready
            assert project.last_analyzed_at is not None

            # Verify local_path was updated
            assert project.local_path is not None
            assert str(project.id) in project.local_path

            # Verify stats populated
            assert project.stats is not None
            assert project.stats["files"] > 0

        finally:
            # Cleanup
            if clone_dir.exists():
                shutil.rmtree(clone_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_status_transitions(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test status transitions during analysis: pending → scanning → analyzing → ready."""
        # Create wrapper
        wrapper = SessionWrapper(test_db_session)

        # Track status changes
        status_history = []
        original_commit = wrapper.commit

        def track_status(*args, **kwargs):
            # Capture current status (changes happen before commit)
            status_history.append(project.status)
            return original_commit(*args, **kwargs)

        # Mock commit on the wrapper
        wrapper.commit = track_status

        # Mock SessionLocal to return our wrapper
        mocker.patch(
            "app.services.analysis_service.SessionLocal",
            return_value=wrapper
        )

        project = project_factory(
            name="Status Transitions Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.pending
        )

        # Run analysis
        await run_analysis(project.id)

        # Verify status progression
        # For local_path: pending → scanning → analyzing → ready
        assert ProjectStatus.scanning in status_history
        assert ProjectStatus.analyzing in status_history
        assert ProjectStatus.ready in status_history

        # Verify final status
        test_db_session.refresh(project)
        assert project.status == ProjectStatus.ready

    @pytest.mark.asyncio
    async def test_analysis_failure_invalid_path(
        self,
        test_db_session,
        project_factory,
        mocker
    ):
        """Test analysis fails gracefully when local path doesn't exist."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Invalid Path Test",
            source_type=SourceType.local_path,
            source="/nonexistent/path/to/repo",
            status=ProjectStatus.pending
        )

        # Run analysis
        await run_analysis(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify status is failed
        assert project.status == ProjectStatus.failed

        # Stats should be None or empty
        assert project.stats is None or project.stats == {}

    @pytest.mark.asyncio
    async def test_analysis_failure_git_clone(
        self,
        test_db_session,
        project_factory,
        mocker
    ):
        """Test analysis fails gracefully when git clone fails."""
        self._mock_session_local(test_db_session, mocker)

        # Mock git service clone to return failure
        mocker.patch(
            "app.services.analysis_service.GitService.clone_repository",
            return_value=(False, "Repository not found")
        )

        project = project_factory(
            name="Git Clone Failure Test",
            source_type=SourceType.git_url,
            source="https://github.com/invalid/repo.git",
            branch="main",
            status=ProjectStatus.pending
        )

        # Run analysis
        await run_analysis(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify status is failed
        assert project.status == ProjectStatus.failed

        # Stats should be None or empty
        assert project.stats is None or project.stats == {}

    @pytest.mark.asyncio
    async def test_stats_populated_correctly(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test that stats field is populated with correct data after analysis."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Stats Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.pending
        )

        # Run analysis
        await run_analysis(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify stats structure
        assert project.stats is not None
        assert "files" in project.stats
        assert "lines_of_code" in project.stats
        assert "languages" in project.stats

        # Verify stats values are reasonable
        assert project.stats["files"] >= 2  # sample_python_repo has 2 files
        assert project.stats["lines_of_code"] > 0

        # Verify language data
        assert "Python" in project.stats["languages"]
        assert project.stats["languages"]["Python"]["files"] >= 1
        assert project.stats["languages"]["Python"]["lines"] > 0

    @pytest.mark.asyncio
    async def test_project_not_found(self, test_db_session, mocker):
        """Test analysis handles non-existent project gracefully."""
        self._mock_session_local(test_db_session, mocker)

        # Run analysis with non-existent project ID
        await run_analysis("00000000-0000-0000-0000-000000000000")

        # Should not raise exception, just log error and return

    @pytest.mark.asyncio
    async def test_re_analyze(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test re-analyzing an existing project."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Re-analyze Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.ready  # Already analyzed
        )

        # Re-run analysis
        await re_analyze(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify status is ready again
        assert project.status == ProjectStatus.ready
        assert project.stats is not None

    @pytest.mark.asyncio
    async def test_re_analyze_already_analyzing(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test re-analyze doesn't run if project is already being analyzed."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Already Analyzing Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.analyzing  # Currently analyzing
        )

        # Try to re-run analysis
        await re_analyze(project.id)

        # Refresh project from database
        test_db_session.refresh(project)

        # Status should still be analyzing (not changed)
        assert project.status == ProjectStatus.analyzing

    @pytest.mark.asyncio
    async def test_cancel_analysis(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test cancelling an ongoing analysis."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Cancel Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.analyzing
        )

        # Cancel analysis
        result = await cancel_analysis(project.id)

        # Verify cancellation succeeded
        assert result is True

        # Refresh project from database
        test_db_session.refresh(project)

        # Verify status is failed (cancelled)
        assert project.status == ProjectStatus.failed

    @pytest.mark.asyncio
    async def test_cancel_analysis_not_analyzing(
        self,
        test_db_session,
        project_factory,
        sample_python_repo,
        mocker
    ):
        """Test cancel analysis returns False when not analyzing."""
        self._mock_session_local(test_db_session, mocker)

        project = project_factory(
            name="Not Analyzing Cancel Test",
            source_type=SourceType.local_path,
            source=str(sample_python_repo),
            status=ProjectStatus.ready
        )

        # Try to cancel analysis
        result = await cancel_analysis(project.id)

        # Verify cancellation failed (not analyzing)
        assert result is False

        # Refresh project from database
        test_db_session.refresh(project)

        # Status should still be ready
        assert project.status == ProjectStatus.ready
