"""Unit tests for GitService."""

import pytest
from unittest.mock import MagicMock, patch, call
from subprocess import TimeoutExpired
from pathlib import Path

from app.services.git_service import GitService


class TestGitService:
    """Test GitService methods."""

    def test_init_default_timeout(self):
        """Test GitService initialization with default timeout."""
        service = GitService()
        assert service.timeout == 300

    def test_init_custom_timeout(self):
        """Test GitService initialization with custom timeout."""
        service = GitService(timeout=600)
        assert service.timeout == 600

    @patch("app.services.git_service.subprocess.run")
    @patch("app.services.git_service.shutil.rmtree")
    def test_clone_repository_success(self, mock_rmtree, mock_run, temp_repo_dir):
        """Test successful repository cloning."""
        local_path = str(temp_repo_dir / "cloned")

        # Mock successful git clone
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        # Create .git directory to pass validation
        git_dir = temp_repo_dir / "cloned" / ".git"
        git_dir.mkdir(parents=True)

        service = GitService(timeout=300)
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=local_path,
            branch="main",
            max_size_mb=1000
        )

        assert success is True
        assert error is None
        mock_run.assert_called_once()

        # Verify git clone command
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "clone" in args
        assert "--depth" in args
        assert "1" in args
        assert "--branch" in args
        assert "main" in args
        assert "https://github.com/test/repo.git" in args

    @patch("app.services.git_service.subprocess.run")
    @patch.object(GitService, "validate_repository")
    def test_clone_repository_with_main_branch(self, mock_validate, mock_run, temp_repo_dir):
        """Test cloning with main branch (default)."""
        local_path = str(temp_repo_dir / "cloned")

        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        mock_validate.return_value = True  # Mock validation to pass

        service = GitService()
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=local_path
        )

        assert success is True
        # Verify main branch was used
        args = mock_run.call_args[0][0]
        assert "main" in args

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_with_master_fallback(self, mock_run, temp_repo_dir):
        """Test fallback to master branch when main fails."""
        local_path = str(temp_repo_dir / "cloned")

        # First call fails (main branch not found)
        # Second call succeeds (master branch)
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="remote branch main not found", stdout=""),
            MagicMock(returncode=0, stderr="", stdout="")
        ]

        # Create .git directory for validation
        git_dir = temp_repo_dir / "cloned" / ".git"
        git_dir.mkdir(parents=True)

        service = GitService()
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=local_path,
            branch="main"
        )

        assert success is True
        assert error is None
        assert mock_run.call_count == 2

        # Verify second call used master
        second_call_args = mock_run.call_args_list[1][0][0]
        assert "master" in second_call_args

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_failure_invalid_url(self, mock_run, temp_repo_dir):
        """Test clone failure with invalid URL."""
        local_path = str(temp_repo_dir / "cloned")

        mock_run.return_value = MagicMock(
            returncode=128,
            stderr="fatal: repository 'https://invalid.git' not found",
            stdout=""
        )

        service = GitService()
        success, error = service.clone_repository(
            git_url="https://invalid.git",
            local_path=local_path
        )

        assert success is False
        assert error is not None
        assert "Git clone failed" in error
        assert "not found" in error

    @patch("app.services.git_service.subprocess.run")
    def test_clone_repository_timeout(self, mock_run, temp_repo_dir):
        """Test clone timeout handling."""
        local_path = str(temp_repo_dir / "cloned")

        mock_run.side_effect = TimeoutExpired(cmd="git", timeout=300)

        service = GitService(timeout=300)
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=local_path
        )

        assert success is False
        assert error is not None
        assert "timeout" in error.lower()
        assert "300" in error

    @patch("app.services.git_service.shutil.rmtree")
    @patch("app.services.git_service.subprocess.run")
    @patch.object(GitService, "validate_repository")
    @patch.object(GitService, "get_repo_size")
    def test_clone_repository_exceeds_size_limit(self, mock_get_size, mock_validate, mock_run, mock_rmtree, temp_repo_dir):
        """Test repository size limit enforcement."""
        local_path = str(temp_repo_dir / "cloned")

        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        mock_validate.return_value = True  # Pass validation
        mock_get_size.return_value = 15.0  # Mock size as 15 MB

        service = GitService()
        success, error = service.clone_repository(
            git_url="https://github.com/test/repo.git",
            local_path=local_path,
            max_size_mb=10  # Set limit to 10 MB
        )

        assert success is False
        assert error is not None
        assert "too large" in error.lower()
        assert "10" in error
        # Verify rmtree was called to clean up the oversized repo
        mock_rmtree.assert_called()

    def test_validate_repository_valid(self, temp_repo_dir):
        """Test validation of valid repository."""
        repo_path = temp_repo_dir / "valid_repo"
        git_dir = repo_path / ".git"
        git_dir.mkdir(parents=True)

        service = GitService()
        is_valid = service.validate_repository(str(repo_path))

        assert is_valid is True

    def test_validate_repository_invalid_no_git_dir(self, temp_repo_dir):
        """Test validation fails when .git directory missing."""
        repo_path = temp_repo_dir / "invalid_repo"
        repo_path.mkdir()

        service = GitService()
        is_valid = service.validate_repository(str(repo_path))

        assert is_valid is False

    def test_validate_repository_path_not_exists(self, temp_repo_dir):
        """Test validation fails when path doesn't exist."""
        non_existent = temp_repo_dir / "nonexistent"

        service = GitService()
        is_valid = service.validate_repository(str(non_existent))

        assert is_valid is False

    def test_get_repo_size(self, temp_repo_dir):
        """Test repository size calculation."""
        repo_path = temp_repo_dir / "test_repo"
        repo_path.mkdir()

        # Create some files with known sizes
        (repo_path / "file1.txt").write_text("x" * 1024)  # 1 KB
        (repo_path / "file2.txt").write_text("y" * 2048)  # 2 KB

        service = GitService()
        size_mb = service.get_repo_size(str(repo_path))

        # Should be approximately 3 KB = 0.003 MB
        assert size_mb > 0
        assert size_mb < 0.01  # Less than 0.01 MB

    def test_get_repo_size_nonexistent_path(self, temp_repo_dir):
        """Test size calculation for nonexistent path."""
        non_existent = temp_repo_dir / "nonexistent"

        service = GitService()
        size_mb = service.get_repo_size(str(non_existent))

        assert size_mb == 0.0

    @patch("app.services.git_service.subprocess.run")
    def test_pull_repository_success(self, mock_run, temp_repo_dir):
        """Test successful git pull."""
        repo_path = temp_repo_dir / "test_repo"
        git_dir = repo_path / ".git"
        git_dir.mkdir(parents=True)

        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="Already up to date.")

        service = GitService()
        success, error = service.pull_repository(str(repo_path))

        assert success is True
        assert error is None
        mock_run.assert_called_once()

        # Verify git pull command
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "-C" in args
        assert "pull" in args

    @patch("app.services.git_service.subprocess.run")
    def test_pull_repository_failure(self, mock_run, temp_repo_dir):
        """Test git pull failure."""
        repo_path = temp_repo_dir / "test_repo"
        git_dir = repo_path / ".git"
        git_dir.mkdir(parents=True)

        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="fatal: unable to access repository",
            stdout=""
        )

        service = GitService()
        success, error = service.pull_repository(str(repo_path))

        assert success is False
        assert error is not None
        assert "Git pull failed" in error

    def test_pull_repository_invalid_repo(self, temp_repo_dir):
        """Test pull on invalid repository."""
        repo_path = temp_repo_dir / "not_a_repo"
        repo_path.mkdir()

        service = GitService()
        success, error = service.pull_repository(str(repo_path))

        assert success is False
        assert error is not None
        assert "not a valid git repository" in error.lower()

    @patch("app.services.git_service.subprocess.run")
    def test_get_current_branch(self, mock_run, temp_repo_dir):
        """Test getting current branch name."""
        repo_path = temp_repo_dir / "test_repo"

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main\n",
            stderr=""
        )

        service = GitService()
        branch = service.get_current_branch(str(repo_path))

        assert branch == "main"

        # Verify command
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "rev-parse" in args
        assert "--abbrev-ref" in args
        assert "HEAD" in args

    @patch("app.services.git_service.subprocess.run")
    def test_get_current_branch_failure(self, mock_run, temp_repo_dir):
        """Test get branch failure."""
        repo_path = temp_repo_dir / "test_repo"

        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal")

        service = GitService()
        branch = service.get_current_branch(str(repo_path))

        assert branch is None

    @patch("app.services.git_service.subprocess.run")
    def test_get_commit_hash(self, mock_run, temp_repo_dir):
        """Test getting current commit hash."""
        repo_path = temp_repo_dir / "test_repo"

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def456\n",
            stderr=""
        )

        service = GitService()
        commit_hash = service.get_commit_hash(str(repo_path))

        assert commit_hash == "abc123def456"

        # Verify command
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "rev-parse" in args
        assert "HEAD" in args

    @patch("app.services.git_service.subprocess.run")
    def test_get_commit_hash_failure(self, mock_run, temp_repo_dir):
        """Test get commit hash failure."""
        repo_path = temp_repo_dir / "test_repo"

        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal")

        service = GitService()
        commit_hash = service.get_commit_hash(str(repo_path))

        assert commit_hash is None

    @patch("app.services.git_service.subprocess.run")
    def test_pull_repository_timeout(self, mock_run, temp_repo_dir):
        """Test pull timeout handling."""
        repo_path = temp_repo_dir / "test_repo"
        git_dir = repo_path / ".git"
        git_dir.mkdir(parents=True)

        mock_run.side_effect = TimeoutExpired(cmd="git", timeout=300)

        service = GitService(timeout=300)
        success, error = service.pull_repository(str(repo_path))

        assert success is False
        assert error is not None
        assert "timeout" in error.lower()

    @patch("app.services.git_service.subprocess.run")
    def test_get_repo_size_with_error(self, mock_run, temp_repo_dir):
        """Test get_repo_size handles errors gracefully."""
        # Create a path that will cause an error during size calculation
        service = GitService()

        # Test with permission denied simulation by mocking Path.rglob
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.side_effect = PermissionError("Access denied")
            size = service.get_repo_size(str(temp_repo_dir))
            assert size == 0.0

    @patch("app.services.git_service.subprocess.run")
    def test_get_current_branch_exception(self, mock_run):
        """Test get_current_branch handles exceptions."""
        mock_run.side_effect = Exception("Unexpected error")

        service = GitService()
        branch = service.get_current_branch("/some/path")

        assert branch is None

    @patch("app.services.git_service.subprocess.run")
    def test_get_commit_hash_exception(self, mock_run):
        """Test get_commit_hash handles exceptions."""
        mock_run.side_effect = Exception("Unexpected error")

        service = GitService()
        commit = service.get_commit_hash("/some/path")

        assert commit is None

    @patch("app.services.git_service.subprocess.run")
    def test_pull_repository_generic_exception(self, mock_run, temp_repo_dir):
        """Test pull handles generic exceptions."""
        repo_path = temp_repo_dir / "test_repo"
        git_dir = repo_path / ".git"
        git_dir.mkdir(parents=True)

        mock_run.side_effect = Exception("Unexpected error")

        service = GitService()
        success, error = service.pull_repository(str(repo_path))

        assert success is False
        assert error is not None
        assert "Error" in error
