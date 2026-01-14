"""Language detection utilities based on file extensions."""

from typing import Optional, Set
from pathlib import Path


# Map file extensions to language names
LANGUAGE_MAP = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    ".pyw": "Python",

    # JavaScript/TypeScript
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",

    # Web
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",

    # Java/JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",

    # C/C++
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".hxx": "C++",

    # C#/.NET
    ".cs": "C#",
    ".csx": "C#",
    ".fs": "F#",
    ".fsx": "F#",
    ".vb": "Visual Basic",

    # Go
    ".go": "Go",

    # Rust
    ".rs": "Rust",

    # Ruby
    ".rb": "Ruby",
    ".rake": "Ruby",

    # PHP
    ".php": "PHP",
    ".phtml": "PHP",

    # Swift
    ".swift": "Swift",

    # R
    ".r": "R",
    ".R": "R",

    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",

    # Other
    ".sql": "SQL",
    ".pl": "Perl",
    ".lua": "Lua",
    ".dart": "Dart",
    ".elm": "Elm",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".ml": "OCaml",
    ".hs": "Haskell",
}

# Map language names to Tree-sitter grammar identifiers
GRAMMAR_MAP = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "TSX": "tsx",
    # Add more as Tree-sitter grammars are installed
}

# Languages supported by Tree-sitter parsers
SUPPORTED_LANGUAGES = {
    "Python",
    "JavaScript",
    "TypeScript",
    "TSX",
}


class LanguageDetector:
    """Detect programming language from file extension."""

    def __init__(self):
        """Initialize language detector."""
        self.language_map = LANGUAGE_MAP
        self.grammar_map = GRAMMAR_MAP
        self.supported_languages = SUPPORTED_LANGUAGES

    def detect_language(self, file_path: str) -> Optional[str]:
        """
        Detect language from file extension.

        Args:
            file_path: Path to file

        Returns:
            Language name or None if unknown
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Special case for .tsx files
        if extension == ".tsx":
            return "TSX"

        return self.language_map.get(extension)

    def is_supported_language(self, language: str) -> bool:
        """
        Check if language has Tree-sitter grammar available.

        Args:
            language: Language name

        Returns:
            True if supported, False otherwise
        """
        return language in self.supported_languages

    def get_grammar_name(self, language: str) -> Optional[str]:
        """
        Get Tree-sitter grammar name for language.

        Args:
            language: Language name

        Returns:
            Grammar name or None if not supported
        """
        return self.grammar_map.get(language)

    def get_supported_extensions(self) -> Set[str]:
        """
        Get all supported file extensions.

        Returns:
            Set of file extensions (e.g., {'.py', '.js'})
        """
        return set(self.language_map.keys())

    def is_code_file(self, file_path: str) -> bool:
        """
        Check if file is a recognized code file.

        Args:
            file_path: Path to file

        Returns:
            True if code file, False otherwise
        """
        language = self.detect_language(file_path)
        return language is not None
