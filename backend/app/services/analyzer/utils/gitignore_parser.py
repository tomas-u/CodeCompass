"""Gitignore pattern parsing and matching utilities."""

from pathlib import Path
from typing import List, Optional
import logging
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

logger = logging.getLogger(__name__)


# Default patterns to always ignore
DEFAULT_IGNORE_PATTERNS = [
    # Version control
    ".git/",
    ".svn/",
    ".hg/",

    # Dependencies
    "node_modules/",
    "bower_components/",
    "vendor/",
    "packages/",

    # Python
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "venv/",
    ".venv/",
    "env/",
    ".env/",
    "ENV/",
    "*.egg-info/",
    "dist/",
    "build/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".tox/",
    "*.so",

    # JavaScript/Node
    ".next/",
    ".nuxt/",
    "out/",
    ".cache/",
    "*.min.js",
    "*.bundle.js",

    # IDE
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
    ".DS_Store",

    # Build outputs
    "*.log",
    "*.pid",
    "*.seed",
    "*.pid.lock",

    # OS
    "Thumbs.db",
    "desktop.ini",

    # Misc
    "tmp/",
    "temp/",
    ".tmp/",
]


class GitignoreParser:
    """Parse .gitignore files and match paths against patterns."""

    def __init__(self, use_defaults: bool = True):
        """
        Initialize gitignore parser.

        Args:
            use_defaults: Whether to include default ignore patterns
        """
        self.patterns: List[str] = []
        if use_defaults:
            self.patterns.extend(DEFAULT_IGNORE_PATTERNS)

        self.pathspec: Optional[PathSpec] = None

    def parse_gitignore(self, repo_path: str) -> None:
        """
        Parse .gitignore file from repository root.

        Args:
            repo_path: Path to repository
        """
        gitignore_path = Path(repo_path) / ".gitignore"

        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith('#'):
                            self.patterns.append(line)

                logger.info(f"Loaded {len(self.patterns)} patterns from .gitignore")
            except Exception as e:
                logger.warning(f"Error reading .gitignore: {e}")
        else:
            logger.info("No .gitignore found, using default patterns only")

        # Build PathSpec from patterns
        self._build_pathspec()

    def _build_pathspec(self) -> None:
        """Build PathSpec object from patterns."""
        try:
            self.pathspec = PathSpec.from_lines(
                GitWildMatchPattern,
                self.patterns
            )
        except Exception as e:
            logger.error(f"Error building PathSpec: {e}")
            self.pathspec = None

    def should_ignore(self, file_path: str, repo_path: str) -> bool:
        """
        Check if file should be ignored.

        Args:
            file_path: Absolute or relative file path
            repo_path: Repository root path

        Returns:
            True if file should be ignored, False otherwise
        """
        if self.pathspec is None:
            return False

        try:
            # Convert to relative path from repo root
            file_path_obj = Path(file_path)
            repo_path_obj = Path(repo_path)

            # Always try to compute relative path from repo root
            # This handles both absolute and relative paths that include the repo path
            try:
                relative_path = file_path_obj.relative_to(repo_path_obj)
            except ValueError:
                # Path doesn't start with repo_path, use as-is
                # This can happen for paths already relative to repo root
                relative_path = file_path_obj

            # Convert to POSIX path for matching
            posix_path = relative_path.as_posix()

            # Match against patterns
            return self.pathspec.match_file(posix_path)

        except ValueError:
            # Path is outside repo
            return False
        except Exception as e:
            logger.warning(f"Error checking ignore for {file_path}: {e}")
            return False

    def should_ignore_dir(self, dir_path: str, repo_path: str) -> bool:
        """
        Check if directory should be ignored.

        Args:
            dir_path: Directory path
            repo_path: Repository root path

        Returns:
            True if directory should be ignored, False otherwise
        """
        # For directories, add trailing slash for proper matching
        if not dir_path.endswith('/'):
            dir_path = dir_path + '/'

        return self.should_ignore(dir_path, repo_path)

    def add_pattern(self, pattern: str) -> None:
        """
        Add custom ignore pattern.

        Args:
            pattern: Gitignore-style pattern
        """
        self.patterns.append(pattern)
        self._build_pathspec()

    def add_patterns(self, patterns: List[str]) -> None:
        """
        Add multiple custom ignore patterns.

        Args:
            patterns: List of gitignore-style patterns
        """
        self.patterns.extend(patterns)
        self._build_pathspec()

    def clear_patterns(self) -> None:
        """Clear all patterns."""
        self.patterns = []
        self.pathspec = None

    def get_patterns(self) -> List[str]:
        """
        Get current patterns.

        Returns:
            List of patterns
        """
        return self.patterns.copy()
