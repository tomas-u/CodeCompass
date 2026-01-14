"""Unit tests for TreeSitterManager."""

import pytest
from pathlib import Path

from app.services.analyzer.utils.tree_sitter_utils import TreeSitterManager


class TestTreeSitterManager:
    """Test TreeSitterManager methods."""

    def test_initialization_loads_grammars(self):
        """Test TreeSitterManager initializes and loads grammars."""
        manager = TreeSitterManager()

        # Should have loaded 4 grammars
        assert len(manager.languages) == 4
        assert "python" in manager.languages
        assert "javascript" in manager.languages
        assert "typescript" in manager.languages
        assert "tsx" in manager.languages

        # Parsers should be empty initially (lazy loading)
        assert len(manager.parsers) == 0

    def test_get_parser_python(self):
        """Test get_parser creates parser for Python."""
        manager = TreeSitterManager()

        parser = manager.get_parser("python")

        assert parser is not None
        assert "python" in manager.parsers

    def test_get_parser_javascript(self):
        """Test get_parser creates parser for JavaScript."""
        manager = TreeSitterManager()

        parser = manager.get_parser("javascript")

        assert parser is not None
        assert "javascript" in manager.parsers

    def test_get_parser_typescript(self):
        """Test get_parser creates parser for TypeScript."""
        manager = TreeSitterManager()

        parser = manager.get_parser("typescript")

        assert parser is not None
        assert "typescript" in manager.parsers

    def test_get_parser_tsx(self):
        """Test get_parser creates parser for TSX."""
        manager = TreeSitterManager()

        parser = manager.get_parser("tsx")

        assert parser is not None
        assert "tsx" in manager.parsers

    def test_get_parser_caching(self):
        """Test get_parser returns cached parser on second call."""
        manager = TreeSitterManager()

        # First call creates parser
        parser1 = manager.get_parser("python")
        assert len(manager.parsers) == 1

        # Second call returns cached parser
        parser2 = manager.get_parser("python")
        assert parser1 is parser2  # Same object
        assert len(manager.parsers) == 1  # No new parser created

    def test_get_parser_case_insensitive(self):
        """Test get_parser handles case-insensitive language names."""
        manager = TreeSitterManager()

        parser1 = manager.get_parser("Python")
        parser2 = manager.get_parser("PYTHON")
        parser3 = manager.get_parser("python")

        # All should return the same cached parser
        assert parser1 is not None
        assert parser1 is parser2
        assert parser2 is parser3

    def test_get_parser_unsupported_language(self):
        """Test get_parser returns None for unsupported language."""
        manager = TreeSitterManager()

        parser = manager.get_parser("java")

        assert parser is None
        assert "java" not in manager.parsers

    def test_parse_file_python(self, temp_repo_dir):
        """Test parse_file with valid Python file."""
        manager = TreeSitterManager()

        # Create Python file
        py_file = temp_repo_dir / "test.py"
        py_file.write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

        tree = manager.parse_file(str(py_file), "python")

        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "module"

    def test_parse_file_javascript(self, temp_repo_dir):
        """Test parse_file with valid JavaScript file."""
        manager = TreeSitterManager()

        # Create JavaScript file
        js_file = temp_repo_dir / "test.js"
        js_file.write_text("""
function hello() {
    console.log("Hello, World!");
}

hello();
""")

        tree = manager.parse_file(str(js_file), "javascript")

        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "program"

    def test_parse_file_missing_file(self):
        """Test parse_file handles missing file gracefully."""
        manager = TreeSitterManager()

        tree = manager.parse_file("/nonexistent/file.py", "python")

        assert tree is None

    def test_parse_file_unsupported_language(self, temp_repo_dir):
        """Test parse_file returns None for unsupported language."""
        manager = TreeSitterManager()

        # Create file
        file_path = temp_repo_dir / "test.java"
        file_path.write_text("public class Test {}")

        tree = manager.parse_file(str(file_path), "java")

        assert tree is None

    def test_parse_code_python(self):
        """Test parse_code with Python source bytes."""
        manager = TreeSitterManager()

        source_code = b"""
def add(a, b):
    return a + b

result = add(2, 3)
"""

        tree = manager.parse_code(source_code, "python")

        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "module"

    def test_parse_code_javascript(self):
        """Test parse_code with JavaScript source bytes."""
        manager = TreeSitterManager()

        source_code = b"""
const add = (a, b) => a + b;
const result = add(2, 3);
"""

        tree = manager.parse_code(source_code, "javascript")

        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "program"

    def test_parse_code_empty(self):
        """Test parse_code with empty source."""
        manager = TreeSitterManager()

        tree = manager.parse_code(b"", "python")

        assert tree is not None
        assert tree.root_node is not None

    def test_parse_code_unsupported_language(self):
        """Test parse_code returns None for unsupported language."""
        manager = TreeSitterManager()

        source_code = b"public class Test {}"

        tree = manager.parse_code(source_code, "java")

        assert tree is None

    def test_is_language_supported(self):
        """Test is_language_supported for supported languages."""
        manager = TreeSitterManager()

        # Supported languages
        assert manager.is_language_supported("python") is True
        assert manager.is_language_supported("javascript") is True
        assert manager.is_language_supported("typescript") is True
        assert manager.is_language_supported("tsx") is True

        # Case insensitive
        assert manager.is_language_supported("Python") is True
        assert manager.is_language_supported("JAVASCRIPT") is True

    def test_is_language_not_supported(self):
        """Test is_language_supported returns False for unsupported languages."""
        manager = TreeSitterManager()

        assert manager.is_language_supported("java") is False
        assert manager.is_language_supported("go") is False
        assert manager.is_language_supported("rust") is False
        assert manager.is_language_supported("unknown") is False

    def test_get_supported_languages(self):
        """Test get_supported_languages returns list of 4 languages."""
        manager = TreeSitterManager()

        languages = manager.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) == 4
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "tsx" in languages

    def test_parse_file_with_syntax_errors(self, temp_repo_dir):
        """Test parse_file handles files with syntax errors."""
        manager = TreeSitterManager()

        # Create file with syntax errors
        py_file = temp_repo_dir / "broken.py"
        py_file.write_text("""
def broken_function(
    # Missing closing parenthesis and body

if True
    # Missing colon
""")

        # Should not crash, Tree-sitter is error-tolerant
        tree = manager.parse_file(str(py_file), "python")

        # Tree-sitter still returns a tree even with errors
        assert tree is not None
        assert tree.root_node is not None

    def test_parse_code_with_syntax_errors(self):
        """Test parse_code handles syntax errors gracefully."""
        manager = TreeSitterManager()

        source_code = b"""
def broken(
    # Missing closing parenthesis
"""

        # Tree-sitter is error-tolerant
        tree = manager.parse_code(source_code, "python")

        assert tree is not None
        assert tree.root_node is not None
