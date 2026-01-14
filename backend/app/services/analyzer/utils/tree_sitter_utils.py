"""Tree-sitter utilities for code parsing."""

from typing import Dict, Optional
import logging
from tree_sitter import Language, Parser, Tree

logger = logging.getLogger(__name__)


class TreeSitterManager:
    """Manage Tree-sitter parsers and languages."""

    def __init__(self):
        """Initialize Tree-sitter manager."""
        self.languages: Dict[str, Language] = {}
        self.parsers: Dict[str, Parser] = {}
        self._load_languages()

    def _load_languages(self) -> None:
        """Load Tree-sitter grammars for supported languages."""
        try:
            # Load Python
            import tree_sitter_python
            py_lang = Language(tree_sitter_python.language())
            self.languages["python"] = py_lang
            logger.info("Loaded Python grammar")

            # Load JavaScript
            import tree_sitter_javascript
            js_lang = Language(tree_sitter_javascript.language())
            self.languages["javascript"] = js_lang
            logger.info("Loaded JavaScript grammar")

            # Load TypeScript
            import tree_sitter_typescript
            ts_lang = Language(tree_sitter_typescript.language_typescript())
            self.languages["typescript"] = ts_lang
            logger.info("Loaded TypeScript grammar")

            # Load TSX
            tsx_lang = Language(tree_sitter_typescript.language_tsx())
            self.languages["tsx"] = tsx_lang
            logger.info("Loaded TSX grammar")

        except ImportError as e:
            logger.error(f"Failed to load Tree-sitter grammar: {e}")
        except Exception as e:
            logger.error(f"Error loading grammars: {e}")

    def get_parser(self, language: str) -> Optional[Parser]:
        """
        Get or create parser for language.

        Args:
            language: Language identifier (e.g., 'python', 'javascript')

        Returns:
            Parser instance or None if language not supported
        """
        language = language.lower()

        # Return cached parser if exists
        if language in self.parsers:
            return self.parsers[language]

        # Create new parser if language is available
        if language in self.languages:
            parser = Parser(self.languages[language])
            self.parsers[language] = parser
            return parser

        logger.warning(f"No grammar available for language: {language}")
        return None

    def parse_file(self, file_path: str, language: str) -> Optional[Tree]:
        """
        Parse a file and return syntax tree.

        Args:
            file_path: Path to file
            language: Language identifier

        Returns:
            Tree instance or None if parsing failed
        """
        parser = self.get_parser(language.lower())
        if parser is None:
            return None

        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()

            tree = parser.parse(source_code)
            return tree

        except UnicodeDecodeError:
            logger.warning(f"Cannot decode file as text: {file_path}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
            return None

    def parse_code(self, source_code: bytes, language: str) -> Optional[Tree]:
        """
        Parse source code and return syntax tree.

        Args:
            source_code: Source code as bytes
            language: Language identifier

        Returns:
            Tree instance or None if parsing failed
        """
        parser = self.get_parser(language.lower())
        if parser is None:
            return None

        try:
            tree = parser.parse(source_code)
            return tree
        except Exception as e:
            logger.warning(f"Error parsing code: {e}")
            return None

    def is_language_supported(self, language: str) -> bool:
        """
        Check if language is supported.

        Args:
            language: Language identifier

        Returns:
            True if supported, False otherwise
        """
        return language.lower() in self.languages

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages.

        Returns:
            List of language identifiers
        """
        return list(self.languages.keys())
