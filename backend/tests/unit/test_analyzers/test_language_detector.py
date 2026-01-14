"""Unit tests for LanguageDetector."""

import pytest
from app.services.analyzer.utils.language_detector import (
    LanguageDetector,
    LANGUAGE_MAP,
    GRAMMAR_MAP,
    SUPPORTED_LANGUAGES
)


class TestLanguageDetector:
    """Test LanguageDetector methods."""

    def test_detect_language_python(self):
        """Test detection of Python files."""
        detector = LanguageDetector()

        assert detector.detect_language("script.py") == "Python"
        assert detector.detect_language("module.pyi") == "Python"
        assert detector.detect_language("app.pyw") == "Python"
        assert detector.detect_language("/path/to/file.py") == "Python"

    def test_detect_language_javascript(self):
        """Test detection of JavaScript files."""
        detector = LanguageDetector()

        assert detector.detect_language("app.js") == "JavaScript"
        assert detector.detect_language("component.jsx") == "JavaScript"
        assert detector.detect_language("module.mjs") == "JavaScript"
        assert detector.detect_language("script.cjs") == "JavaScript"

    def test_detect_language_typescript(self):
        """Test detection of TypeScript files."""
        detector = LanguageDetector()

        assert detector.detect_language("app.ts") == "TypeScript"
        assert detector.detect_language("module.mts") == "TypeScript"
        assert detector.detect_language("config.cts") == "TypeScript"

    def test_detect_language_tsx_special_case(self):
        """Test special case: .tsx → TSX (not TypeScript)."""
        detector = LanguageDetector()

        # .tsx should return "TSX", not "TypeScript"
        assert detector.detect_language("component.tsx") == "TSX"
        assert detector.detect_language("/src/Component.tsx") == "TSX"

    def test_detect_language_various_extensions(self):
        """Test detection of various language extensions."""
        detector = LanguageDetector()

        assert detector.detect_language("Main.java") == "Java"
        assert detector.detect_language("main.go") == "Go"
        assert detector.detect_language("lib.rs") == "Rust"
        assert detector.detect_language("app.rb") == "Ruby"
        assert detector.detect_language("script.php") == "PHP"
        assert detector.detect_language("App.swift") == "Swift"
        assert detector.detect_language("main.cpp") == "C++"
        assert detector.detect_language("program.cs") == "C#"

    def test_detect_language_unknown_extension(self):
        """Test unknown extension returns None."""
        detector = LanguageDetector()

        assert detector.detect_language("data.json") is None
        assert detector.detect_language("README.md") is None
        assert detector.detect_language("config.yaml") is None
        assert detector.detect_language("file.txt") is None
        assert detector.detect_language("unknown.xyz") is None

    def test_detect_language_case_insensitive(self):
        """Test detection is case-insensitive for extensions."""
        detector = LanguageDetector()

        # Extensions should be lowercased
        assert detector.detect_language("script.PY") == "Python"
        assert detector.detect_language("app.JS") == "JavaScript"
        assert detector.detect_language("MODULE.TS") == "TypeScript"

    def test_is_supported_language(self):
        """Test is_supported_language for Tree-sitter grammars."""
        detector = LanguageDetector()

        # Supported languages (have Tree-sitter grammars)
        assert detector.is_supported_language("Python") is True
        assert detector.is_supported_language("JavaScript") is True
        assert detector.is_supported_language("TypeScript") is True
        assert detector.is_supported_language("TSX") is True

        # Unsupported languages (no Tree-sitter grammar yet)
        assert detector.is_supported_language("Java") is False
        assert detector.is_supported_language("Go") is False
        assert detector.is_supported_language("Ruby") is False
        assert detector.is_supported_language("UnknownLanguage") is False

    def test_get_grammar_name(self):
        """Test get_grammar_name returns correct Tree-sitter grammar identifier."""
        detector = LanguageDetector()

        assert detector.get_grammar_name("Python") == "python"
        assert detector.get_grammar_name("JavaScript") == "javascript"
        assert detector.get_grammar_name("TypeScript") == "typescript"
        assert detector.get_grammar_name("TSX") == "tsx"

        # Unsupported language returns None
        assert detector.get_grammar_name("Java") is None
        assert detector.get_grammar_name("Go") is None

    def test_get_supported_extensions(self):
        """Test get_supported_extensions returns all 40+ extensions."""
        detector = LanguageDetector()

        extensions = detector.get_supported_extensions()

        # Should be a set
        assert isinstance(extensions, set)

        # Should have 40+ extensions
        assert len(extensions) >= 60  # Actually has more than 60

        # Check some key extensions are present
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".ts" in extensions
        assert ".tsx" in extensions
        assert ".java" in extensions
        assert ".go" in extensions
        assert ".rs" in extensions

    def test_is_code_file_recognized(self):
        """Test is_code_file identifies recognized code files."""
        detector = LanguageDetector()

        # Code files
        assert detector.is_code_file("app.py") is True
        assert detector.is_code_file("index.js") is True
        assert detector.is_code_file("main.go") is True
        assert detector.is_code_file("lib.rs") is True
        assert detector.is_code_file("component.tsx") is True

    def test_is_code_file_unrecognized(self):
        """Test is_code_file returns False for unrecognized files."""
        detector = LanguageDetector()

        # Non-code files
        assert detector.is_code_file("README.md") is False
        assert detector.is_code_file("data.json") is False
        assert detector.is_code_file("config.yaml") is False
        assert detector.is_code_file("image.png") is False
        assert detector.is_code_file("document.pdf") is False

    def test_language_map_consistency(self):
        """Test LANGUAGE_MAP is consistent and comprehensive."""
        # Verify LANGUAGE_MAP is not empty
        assert len(LANGUAGE_MAP) > 0

        # Verify all extensions start with "."
        for ext in LANGUAGE_MAP.keys():
            assert ext.startswith("."), f"Extension {ext} should start with '.'"

        # Verify all values are non-empty strings
        for lang in LANGUAGE_MAP.values():
            assert isinstance(lang, str)
            assert len(lang) > 0

    def test_grammar_map_consistency(self):
        """Test GRAMMAR_MAP has entries for supported languages."""
        # All SUPPORTED_LANGUAGES should have grammar mappings
        for lang in SUPPORTED_LANGUAGES:
            assert lang in GRAMMAR_MAP, f"Language {lang} missing from GRAMMAR_MAP"

        # All grammar names should be lowercase
        for grammar_name in GRAMMAR_MAP.values():
            assert grammar_name.islower(), f"Grammar name {grammar_name} should be lowercase"

    def test_detector_initialization(self):
        """Test LanguageDetector initializes with correct maps."""
        detector = LanguageDetector()

        assert detector.language_map == LANGUAGE_MAP
        assert detector.grammar_map == GRAMMAR_MAP
        assert detector.supported_languages == SUPPORTED_LANGUAGES
