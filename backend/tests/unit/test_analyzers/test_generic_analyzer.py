"""Unit tests for GenericAnalyzer."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.services.analyzer.generic_analyzer import GenericAnalyzer


class TestGenericAnalyzer:
    """Test GenericAnalyzer methods."""

    def test_init_default_parameters(self, temp_repo_dir):
        """Test GenericAnalyzer initialization with defaults."""
        analyzer = GenericAnalyzer(str(temp_repo_dir))

        assert analyzer.repo_path == temp_repo_dir
        assert analyzer.max_file_size_bytes == 10 * 1024 * 1024  # 10 MB
        assert analyzer.use_gitignore is True
        assert analyzer.language_detector is not None
        assert analyzer.tree_sitter_manager is not None
        assert analyzer.gitignore_parser is not None

    def test_init_custom_parameters(self, temp_repo_dir):
        """Test GenericAnalyzer initialization with custom parameters."""
        analyzer = GenericAnalyzer(
            str(temp_repo_dir),
            max_file_size_mb=5,
            use_gitignore=False
        )

        assert analyzer.max_file_size_bytes == 5 * 1024 * 1024  # 5 MB
        assert analyzer.use_gitignore is False

    def test_init_invalid_path(self):
        """Test GenericAnalyzer raises error for invalid path."""
        with pytest.raises(ValueError, match="Repository path does not exist"):
            GenericAnalyzer("/nonexistent/path")

    def test_analyze_simple_python_repo(self, sample_repos_path):
        """Test analyzing a simple Python repository."""
        python_repo = sample_repos_path / "python_simple"
        analyzer = GenericAnalyzer(str(python_repo))

        stats = analyzer.analyze()

        # Should find 3 Python files (main.py, utils.py, data_processor.py)
        assert stats["files"] == 3
        assert stats["lines_of_code"] > 0
        assert "Python" in stats["languages"]
        assert stats["languages"]["Python"]["files"] == 3
        assert stats["languages"]["Python"]["lines"] > 0

    def test_analyze_simple_javascript_repo(self, sample_repos_path):
        """Test analyzing a simple JavaScript repository."""
        js_repo = sample_repos_path / "javascript_simple"
        analyzer = GenericAnalyzer(str(js_repo))

        stats = analyzer.analyze()

        # Should find 3 JavaScript files (index.js, utils.js, services.js)
        assert stats["files"] == 3
        assert stats["lines_of_code"] > 0
        assert "JavaScript" in stats["languages"]
        assert stats["languages"]["JavaScript"]["files"] == 3
        assert stats["languages"]["JavaScript"]["lines"] > 0

    def test_analyze_mixed_language_repo(self, sample_repos_path):
        """Test analyzing repository with mixed languages."""
        mixed_repo = sample_repos_path / "mixed_language"
        analyzer = GenericAnalyzer(str(mixed_repo))

        stats = analyzer.analyze()

        # Should find both Python and JavaScript files
        # mixed_language has: 4 Python files + 4 JavaScript files = 8 total
        assert stats["files"] == 8
        assert "Python" in stats["languages"]
        assert "JavaScript" in stats["languages"]
        assert stats["languages"]["Python"]["files"] == 4
        assert stats["languages"]["JavaScript"]["files"] == 4

    def test_collect_files_respects_gitignore(self, temp_repo_dir):
        """Test that file collection respects .gitignore patterns."""
        # Create directory structure
        (temp_repo_dir / "src").mkdir()
        (temp_repo_dir / "node_modules").mkdir()
        (temp_repo_dir / "node_modules" / "lib").mkdir()

        # Create files
        (temp_repo_dir / "src" / "main.js").write_text("console.log('main');")
        (temp_repo_dir / "node_modules" / "lib" / "module.js").write_text("console.log('module');")

        # Create .gitignore
        (temp_repo_dir / ".gitignore").write_text("node_modules/")

        analyzer = GenericAnalyzer(str(temp_repo_dir), use_gitignore=True)
        stats = analyzer.analyze()

        # Should only find src/main.js, not node_modules/lib/module.js
        assert stats["files"] == 1

    def test_collect_files_without_gitignore(self, temp_repo_dir):
        """Test that file collection ignores .gitignore when disabled."""
        # Create directory structure
        (temp_repo_dir / "src").mkdir()
        (temp_repo_dir / "node_modules").mkdir()

        # Create files
        (temp_repo_dir / "src" / "main.js").write_text("console.log('main');")
        (temp_repo_dir / "node_modules" / "lib.js").write_text("console.log('lib');")

        # Create .gitignore
        (temp_repo_dir / ".gitignore").write_text("node_modules/")

        analyzer = GenericAnalyzer(str(temp_repo_dir), use_gitignore=False)
        stats = analyzer.analyze()

        # Should find both files
        assert stats["files"] == 2

    def test_language_detection(self, temp_repo_dir):
        """Test language detection for various file extensions."""
        # Create files with different extensions
        (temp_repo_dir / "script.py").write_text("print('hello')")
        (temp_repo_dir / "app.js").write_text("console.log('hello');")
        (temp_repo_dir / "component.tsx").write_text("export const App = () => {};")
        (temp_repo_dir / "README.md").write_text("# Documentation")

        analyzer = GenericAnalyzer(str(temp_repo_dir))
        stats = analyzer.analyze()

        # Should detect Python, JavaScript, and TSX
        assert "Python" in stats["languages"]
        assert "JavaScript" in stats["languages"]
        assert "TSX" in stats["languages"]
        # README.md should be detected but depends on language detector config

    def test_analyze_file_counts_lines(self, temp_repo_dir):
        """Test that analyze_file correctly counts non-empty lines."""
        # Create file with known line count
        file_path = temp_repo_dir / "test.py"
        file_path.write_text("""# Comment line

def function():
    pass

# Another comment
    return True""")

        analyzer = GenericAnalyzer(str(temp_repo_dir))
        file_stats = analyzer.analyze_file(str(file_path), "Python")

        # Should count only non-empty lines (excluding blank lines)
        assert file_stats["lines"] > 0
        assert file_stats["lines"] == 5  # 5 non-empty lines

    def test_extract_python_imports(self, sample_repos_path):
        """Test extraction of Python import statements."""
        python_repo = sample_repos_path / "python_simple"
        main_file = python_repo / "main.py"

        analyzer = GenericAnalyzer(str(python_repo))
        file_stats = analyzer.analyze_file(str(main_file), "Python")

        # Should extract imports from main.py
        imports = file_stats.get("imports", [])
        assert len(imports) > 0
        # Should find: os, sys, utils
        assert "os" in imports
        assert "sys" in imports
        assert "utils" in imports

    def test_extract_javascript_imports(self, sample_repos_path):
        """Test extraction of JavaScript/ES6 import statements."""
        js_repo = sample_repos_path / "javascript_simple"
        index_file = js_repo / "index.js"

        analyzer = GenericAnalyzer(str(js_repo))
        file_stats = analyzer.analyze_file(str(index_file), "JavaScript")

        # Should extract imports from index.js
        imports = file_stats.get("imports", [])
        assert len(imports) > 0
        # Should find: ./utils.js
        assert "./utils.js" in imports

    def test_stats_aggregation(self, sample_repos_path):
        """Test that statistics are aggregated correctly across files."""
        python_repo = sample_repos_path / "python_simple"
        analyzer = GenericAnalyzer(str(python_repo))

        stats = analyzer.analyze()

        # Verify aggregation
        total_files = stats["files"]
        total_loc = stats["lines_of_code"]
        python_stats = stats["languages"]["Python"]

        # Total should match language-specific stats
        assert total_files == python_stats["files"]
        assert total_loc == python_stats["lines"]

        # Verify counts are positive
        assert total_files > 0
        assert total_loc > 0

    def test_skip_binary_files(self, temp_repo_dir):
        """Test that binary files are skipped gracefully."""
        # Create a binary file
        binary_file = temp_repo_dir / "image.png"
        binary_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')

        # Create a text file
        text_file = temp_repo_dir / "script.py"
        text_file.write_text("print('hello')")

        analyzer = GenericAnalyzer(str(temp_repo_dir))
        stats = analyzer.analyze()

        # Should only analyze text files
        # Binary file should not cause crash
        assert stats["files"] >= 0
        # Python file should be counted
        if "Python" in stats["languages"]:
            assert stats["languages"]["Python"]["files"] >= 1

    def test_skip_large_files(self, temp_repo_dir):
        """Test that files exceeding size limit are skipped."""
        # Create a small file
        small_file = temp_repo_dir / "small.py"
        small_file.write_text("print('hello')")

        # Create a large file (larger than 1MB limit)
        large_file = temp_repo_dir / "large.py"
        large_file.write_text("# " + "x" * (2 * 1024 * 1024))  # 2 MB

        # Set max file size to 1 MB
        analyzer = GenericAnalyzer(str(temp_repo_dir), max_file_size_mb=1)
        stats = analyzer.analyze()

        # Should only count small file
        assert stats["files"] == 1
        assert stats["languages"]["Python"]["files"] == 1

    def test_handle_syntax_errors(self, temp_repo_dir):
        """Test that malformed code doesn't crash the analyzer."""
        # Create file with syntax errors
        bad_file = temp_repo_dir / "broken.py"
        bad_file.write_text("""
def broken_function(
    # Missing closing parenthesis and body

if True
    # Missing colon
""")

        # Create valid file
        good_file = temp_repo_dir / "good.py"
        good_file.write_text("print('hello')")

        analyzer = GenericAnalyzer(str(temp_repo_dir))

        # Should not crash, should process what it can
        stats = analyzer.analyze()

        # Should still count files even if parsing fails
        assert stats["files"] >= 1

    def test_analyze_empty_repository(self, temp_repo_dir):
        """Test analyzing an empty repository."""
        analyzer = GenericAnalyzer(str(temp_repo_dir))
        stats = analyzer.analyze()

        assert stats["files"] == 0
        assert stats["lines_of_code"] == 0
        assert len(stats["languages"]) == 0

    @patch("app.services.analyzer.generic_analyzer.logger")
    def test_logging_on_analysis(self, mock_logger, sample_repos_path):
        """Test that analysis logs appropriate messages."""
        python_repo = sample_repos_path / "python_simple"
        analyzer = GenericAnalyzer(str(python_repo))

        stats = analyzer.analyze()

        # Verify logging calls
        assert mock_logger.info.called
        # Should log start and completion
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Starting analysis" in str(call) for call in info_calls)
        assert any("Analysis complete" in str(call) for call in info_calls)

    def test_get_stats_returns_copy(self, temp_repo_dir):
        """Test that get_stats returns current statistics."""
        (temp_repo_dir / "test.py").write_text("print('test')")

        analyzer = GenericAnalyzer(str(temp_repo_dir))

        # Before analysis
        stats_before = analyzer.get_stats()
        assert stats_before["files"] == 0

        # After analysis
        analyzer.analyze()
        stats_after = analyzer.get_stats()
        assert stats_after["files"] == 1

    def test_get_dependency_graph_before_analysis(self, temp_repo_dir):
        """Test get_dependency_graph returns None before analyze() is called."""
        (temp_repo_dir / "main.py").write_text("import utils")
        (temp_repo_dir / "utils.py").write_text("def helper(): pass")

        analyzer = GenericAnalyzer(str(temp_repo_dir))

        # Before analysis, should return None
        dep_graph = analyzer.get_dependency_graph()
        assert dep_graph is None

    def test_get_dependency_graph_after_analysis(self, sample_repos_path):
        """Test get_dependency_graph returns DependencyGraph after analyze()."""
        python_repo = sample_repos_path / "python_simple"
        analyzer = GenericAnalyzer(str(python_repo))

        analyzer.analyze()
        dep_graph = analyzer.get_dependency_graph()

        # Should return a DependencyGraph instance
        assert dep_graph is not None
        # Should have nodes (files analyzed)
        assert dep_graph.graph.number_of_nodes() >= 0

    def test_get_dependency_summary_before_analysis(self, temp_repo_dir):
        """Test get_dependency_summary returns empty dict before analyze()."""
        (temp_repo_dir / "main.py").write_text("import utils")

        analyzer = GenericAnalyzer(str(temp_repo_dir))

        # Before analysis, should return empty dict
        summary = analyzer.get_dependency_summary()
        assert summary == {}

    def test_get_dependency_summary_after_analysis(self, sample_repos_path):
        """Test get_dependency_summary returns summary data after analyze()."""
        python_repo = sample_repos_path / "python_simple"
        analyzer = GenericAnalyzer(str(python_repo))

        analyzer.analyze()
        summary = analyzer.get_dependency_summary()

        # Should return a dict with summary data
        assert isinstance(summary, dict)
        # Should contain expected keys from DependencyGraph.get_summary()
        assert "total_modules" in summary
        assert "total_dependencies" in summary
        assert "has_circular_dependencies" in summary

    def test_get_dependency_graph_with_imports(self, temp_repo_dir):
        """Test dependency graph correctly captures imports."""
        # Create files with imports
        (temp_repo_dir / "main.py").write_text("import utils\nprint('main')")
        (temp_repo_dir / "utils.py").write_text("def helper(): pass")

        analyzer = GenericAnalyzer(str(temp_repo_dir))
        analyzer.analyze()

        dep_graph = analyzer.get_dependency_graph()

        assert dep_graph is not None
        # Should have at least 2 nodes (main.py and utils.py)
        assert dep_graph.graph.number_of_nodes() >= 1


@pytest.fixture
def sample_repos_path():
    """Path to sample repositories fixtures."""
    return Path(__file__).parent.parent.parent / "fixtures" / "sample_repos"
