"""Git repository operations service."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class GitService:
    """Service for handling git repository operations."""

    def __init__(self, timeout: int = 300):
        """
        Initialize Git service.

        Args:
            timeout: Maximum time in seconds for git operations (default 5 minutes)
        """
        self.timeout = timeout

    def clone_repository(
        self,
        git_url: str,
        local_path: str,
        branch: str = "main",
        max_size_mb: int = 1000
    ) -> Tuple[bool, Optional[str]]:
        """
        Clone a git repository to local path.

        Args:
            git_url: Git repository URL (https or ssh)
            local_path: Local path to clone to
            branch: Branch to checkout (default: main)
            max_size_mb: Maximum repository size in MB (default: 1000)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Create parent directories if needed
            path = Path(local_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing directory if it exists
            if path.exists():
                shutil.rmtree(path)

            # Clone repository with depth 1 (shallow clone)
            logger.info(f"Cloning repository: {git_url} to {local_path}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", branch, git_url, local_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Git clone failed: {error_msg}")

                # Try with 'master' branch if 'main' failed
                if branch == "main" and ("not found" in error_msg.lower() or "remote branch" in error_msg.lower()):
                    logger.info("Retrying with 'master' branch")
                    result = subprocess.run(
                        ["git", "clone", "--depth", "1", "--branch", "master", git_url, local_path],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout
                    )
                    if result.returncode == 0:
                        return (True, None)

                return (False, f"Git clone failed: {error_msg}")

            # Check repository size
            size_mb = self.get_repo_size(local_path)
            if size_mb > max_size_mb:
                shutil.rmtree(path)
                return (False, f"Repository too large: {size_mb:.1f} MB (max: {max_size_mb} MB)")

            # Validate clone
            if not self.validate_repository(local_path):
                return (False, "Invalid repository: .git directory not found")

            logger.info(f"Successfully cloned repository ({size_mb:.1f} MB)")
            return (True, None)

        except subprocess.TimeoutExpired:
            logger.error("Git clone timeout")
            if Path(local_path).exists():
                shutil.rmtree(local_path)
            return (False, f"Clone timeout after {self.timeout} seconds")

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command error: {e}")
            return (False, f"Git error: {str(e)}")

        except OSError as e:
            logger.error(f"File system error: {e}")
            return (False, f"File system error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return (False, f"Unexpected error: {str(e)}")

    def validate_repository(self, local_path: str) -> bool:
        """
        Validate that path is a git repository.

        Args:
            local_path: Path to check

        Returns:
            True if valid repository, False otherwise
        """
        path = Path(local_path)
        if not path.exists():
            return False

        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def get_repo_size(self, local_path: str) -> float:
        """
        Get repository size in MB.

        Args:
            local_path: Path to repository

        Returns:
            Size in MB
        """
        try:
            path = Path(local_path)
            if not path.exists():
                return 0.0

            total_size = 0
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size

            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.error(f"Error calculating size: {e}")
            return 0.0

    def pull_repository(self, local_path: str) -> Tuple[bool, Optional[str]]:
        """
        Pull latest changes from remote.

        Args:
            local_path: Path to repository

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            if not self.validate_repository(local_path):
                return (False, "Not a valid git repository")

            logger.info(f"Pulling repository: {local_path}")
            result = subprocess.run(
                ["git", "-C", local_path, "pull"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Git pull failed: {error_msg}")
                return (False, f"Git pull failed: {error_msg}")

            logger.info("Successfully pulled repository")
            return (True, None)

        except subprocess.TimeoutExpired:
            return (False, f"Pull timeout after {self.timeout} seconds")

        except Exception as e:
            logger.error(f"Error pulling repository: {e}")
            return (False, f"Error: {str(e)}")

    def get_current_branch(self, local_path: str) -> Optional[str]:
        """
        Get current branch name.

        Args:
            local_path: Path to repository

        Returns:
            Branch name or None if error
        """
        try:
            result = subprocess.run(
                ["git", "-C", local_path, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting branch: {e}")
            return None

    def get_commit_hash(self, local_path: str) -> Optional[str]:
        """
        Get current commit hash.

        Args:
            local_path: Path to repository

        Returns:
            Commit hash or None if error
        """
        try:
            result = subprocess.run(
                ["git", "-C", local_path, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Error getting commit hash: {e}")
            return None
