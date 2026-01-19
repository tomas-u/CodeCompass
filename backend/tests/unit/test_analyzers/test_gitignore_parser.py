"""Unit tests for GitignoreParser."""

import pytest
from pathlib import Path

from app.services.analyzer.utils.gitignore_parser import (
    GitignoreParser,
    DEFAULT_IGNORE_PATTERNS
)


class TestGitignoreParser:
    """Test GitignoreParser methods."""

    def test_default_ignore_patterns(self):
        """Test parser initializes with default ignore patterns."""
        parser = GitignoreParser(use_defaults=True)

        patterns = parser.get_patterns()

        # Should have default patterns
        assert len(patterns) > 0
        assert "node_modules/" in patterns
        assert "venv/" in patterns
        assert "__pycache__/" in patterns
        assert ".git/" in patterns

    def test_no_default_patterns(self):
        """Test parser can be initialized without defaults."""
        parser = GitignoreParser(use_defaults=False)

        patterns = parser.get_patterns()

        # Should have no patterns
        assert len(patterns) == 0

    def test_parse_gitignore_file(self, temp_repo_dir):
        """Test parsing custom .gitignore file."""
        # Create .gitignore file
        gitignore_path = temp_repo_dir / ".gitignore"
        gitignore_path.write_text("""
# Comment line
*.log
temp/
build/**
!important.log
""")

        parser = GitignoreParser(use_defaults=False)
        parser.parse_gitignore(str(temp_repo_dir))

        patterns = parser.get_patterns()

        # Should parse non-comment lines
        assert "*.log" in patterns
        assert "temp/" in patterns
        assert "build/**" in patterns
        assert "!important.log" in patterns

        # Should skip comments and empty lines
        assert "# Comment line" not in patterns

    def test_parse_gitignore_missing_file(self, temp_repo_dir):
        """Test graceful handling of missing .gitignore file."""
        parser = GitignoreParser(use_defaults=False)

        # Should not raise exception
        parser.parse_gitignore(str(temp_repo_dir))

        # Should have no patterns
        assert len(parser.get_patterns()) == 0

    def test_should_ignore_node_modules(self, temp_repo_dir):
        """Test pattern matching: node_modules/ matches any path."""
        parser = GitignoreParser(use_defaults=True)
        parser.parse_gitignore(str(temp_repo_dir))

        # Should match node_modules in any location
        assert parser.should_ignore("node_modules/package.json", str(temp_repo_dir)) is True
        assert parser.should_ignore("src/node_modules/lib.js", str(temp_repo_dir)) is True
        assert parser.should_ignore("foo/bar/node_modules/index.js", str(temp_repo_dir)) is True

    def test_should_ignore_glob_pattern(self, temp_repo_dir):
        """Test glob pattern matching with **."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("*.log")
        parser.add_pattern("build/**")

        # Glob patterns should match
        assert parser.should_ignore("error.log", str(temp_repo_dir)) is True
        assert parser.should_ignore("logs/error.log", str(temp_repo_dir)) is True
        assert parser.should_ignore("build/output.js", str(temp_repo_dir)) is True
        assert parser.should_ignore("build/dist/bundle.js", str(temp_repo_dir)) is True

    def test_should_ignore_relative_paths(self, temp_repo_dir):
        """Test relative path matching."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("temp/")

        # Relative paths
        assert parser.should_ignore("temp/file.txt", str(temp_repo_dir)) is True
        assert parser.should_ignore("src/temp/data.json", str(temp_repo_dir)) is True

    def test_should_ignore_absolute_paths(self, temp_repo_dir):
        """Test absolute path conversion to relative."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("*.pyc")

        # Create absolute path within repo
        abs_path = temp_repo_dir / "src" / "module.pyc"

        assert parser.should_ignore(str(abs_path), str(temp_repo_dir)) is True

    def test_should_not_ignore_non_matching(self, temp_repo_dir):
        """Test files not matching patterns are not ignored."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("*.log")
        parser.add_pattern("temp/")

        # Should not ignore
        assert parser.should_ignore("src/main.py", str(temp_repo_dir)) is False
        assert parser.should_ignore("data/config.json", str(temp_repo_dir)) is False
        assert parser.should_ignore("README.md", str(temp_repo_dir)) is False

    def test_add_pattern(self, temp_repo_dir):
        """Test add_pattern adds single pattern."""
        parser = GitignoreParser(use_defaults=False)

        assert len(parser.get_patterns()) == 0

        parser.add_pattern("*.tmp")

        patterns = parser.get_patterns()
        assert len(patterns) == 1
        assert "*.tmp" in patterns

        # Should rebuild pathspec
        assert parser.pathspec is not None

    def test_add_patterns(self, temp_repo_dir):
        """Test add_patterns adds multiple patterns."""
        parser = GitignoreParser(use_defaults=False)

        parser.add_patterns(["*.log", "*.tmp", "cache/"])

        patterns = parser.get_patterns()
        assert len(patterns) == 3
        assert "*.log" in patterns
        assert "*.tmp" in patterns
        assert "cache/" in patterns

    def test_clear_patterns(self):
        """Test clear_patterns resets state."""
        parser = GitignoreParser(use_defaults=True)

        # Should have default patterns
        assert len(parser.get_patterns()) > 0
        assert parser.pathspec is None  # Not built yet

        # Clear patterns
        parser.clear_patterns()

        # Should be empty
        assert len(parser.get_patterns()) == 0
        assert parser.pathspec is None

    def test_get_patterns_returns_copy(self):
        """Test get_patterns returns a copy (not reference)."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("*.log")

        patterns1 = parser.get_patterns()
        patterns2 = parser.get_patterns()

        # Should be equal but not same object
        assert patterns1 == patterns2
        assert patterns1 is not patterns2

        # Modifying returned list should not affect parser
        patterns1.append("*.tmp")
        assert "*.tmp" not in parser.get_patterns()

    def test_default_ignore_patterns_constant(self):
        """Test DEFAULT_IGNORE_PATTERNS has expected entries."""
        # Verify it's a list
        assert isinstance(DEFAULT_IGNORE_PATTERNS, list)
        assert len(DEFAULT_IGNORE_PATTERNS) >= 40  # Has 44 patterns

        # Key patterns should be present
        assert "node_modules/" in DEFAULT_IGNORE_PATTERNS
        assert "__pycache__/" in DEFAULT_IGNORE_PATTERNS
        assert "venv/" in DEFAULT_IGNORE_PATTERNS
        assert ".git/" in DEFAULT_IGNORE_PATTERNS
        assert "*.pyc" in DEFAULT_IGNORE_PATTERNS

    def test_should_ignore_outside_repo(self, temp_repo_dir):
        """Test should_ignore handles paths outside repo gracefully."""
        parser = GitignoreParser(use_defaults=False)
        parser.add_pattern("*.log")

        # Paths outside the repo still get pattern-matched against the full path
        # When relative_to fails, the path is used as-is for matching
        outside_path = "/completely/different/path/file.log"
        # *.log pattern matches the filename in the path
        assert parser.should_ignore(outside_path, str(temp_repo_dir)) is True

        # Non-matching extension returns False
        outside_txt = "/completely/different/path/file.txt"
        assert parser.should_ignore(outside_txt, str(temp_repo_dir)) is False

    def test_parse_gitignore_with_encoding_issues(self, temp_repo_dir):
        """Test parse_gitignore handles encoding issues gracefully."""
        # Create .gitignore with potential encoding issues
        gitignore_path = temp_repo_dir / ".gitignore"
        gitignore_path.write_text("*.log\ntemp/\n", encoding='utf-8')

        parser = GitignoreParser(use_defaults=False)

        # Should not raise exception
        parser.parse_gitignore(str(temp_repo_dir))

        patterns = parser.get_patterns()
        assert "*.log" in patterns
        assert "temp/" in patterns
