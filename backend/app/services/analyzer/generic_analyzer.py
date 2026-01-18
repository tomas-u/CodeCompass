"""Generic code analyzer using Tree-sitter."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .base import BaseAnalyzer
from .dependency_graph import DependencyGraph
from .utils.language_detector import LanguageDetector
from .utils.gitignore_parser import GitignoreParser
from .utils.tree_sitter_utils import TreeSitterManager

logger = logging.getLogger(__name__)


class GenericAnalyzer(BaseAnalyzer):
    """Generic analyzer using Tree-sitter for multiple languages."""

    def __init__(
        self,
        repo_path: str,
        max_file_size_mb: int = 10,
        use_gitignore: bool = True
    ):
        """
        Initialize generic analyzer.

        Args:
            repo_path: Path to repository
            max_file_size_mb: Maximum file size to analyze in MB (default: 10)
            use_gitignore: Whether to respect .gitignore patterns (default: True)
        """
        super().__init__(repo_path)

        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.use_gitignore = use_gitignore

        # Initialize utilities
        self.language_detector = LanguageDetector()
        self.tree_sitter_manager = TreeSitterManager()
        self.gitignore_parser = GitignoreParser(use_defaults=True)

        # Parse .gitignore if using
        if self.use_gitignore:
            self.gitignore_parser.parse_gitignore(str(self.repo_path))

        # Dependency graph (built during analysis)
        self._dependency_graph: Optional[DependencyGraph] = None
        self._file_imports: Dict[str, List[str]] = {}
        self._file_languages: Dict[str, str] = {}

    def analyze(self) -> Dict[str, Any]:
        """
        Run full repository analysis.

        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting analysis of {self.repo_path}")

        # Reset stats and dependency tracking
        self.stats = {
            "files": 0,
            "directories": 0,
            "lines_of_code": 0,
            "languages": {}
        }
        self._file_imports = {}
        self._file_languages = {}
        self._dependency_graph = None

        # Collect files to analyze
        files_to_analyze = self._collect_files()
        logger.info(f"Found {len(files_to_analyze)} files to analyze")

        # Analyze each file
        for file_path, language in files_to_analyze:
            try:
                file_stats = self.analyze_file(str(file_path), language)
                self._update_stats(language, file_stats)

                # Track imports for dependency graph
                self._file_imports[str(file_path)] = file_stats.get("imports", [])
                self._file_languages[str(file_path)] = language
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
                continue

        # Build dependency graph from collected imports
        self._build_dependency_graph()

        logger.info(f"Analysis complete: {self.stats['files']} files, "
                   f"{self.stats['lines_of_code']} LOC")

        return self.get_stats()

    def _collect_files(self) -> List[tuple[Path, str]]:
        """
        Collect all files to analyze.

        Returns:
            List of (file_path, language) tuples
        """
        files = []

        for root, dirs, filenames in os.walk(self.repo_path):
            root_path = Path(root)

            # Filter out ignored directories (modify dirs in-place)
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore_dir(root, d)
            ]

            # Count directories
            self.stats["directories"] += len(dirs)

            # Process files in this directory
            for filename in filenames:
                file_path = root_path / filename

                # Check if file should be ignored
                if self._should_ignore_file(file_path):
                    continue

                # Check file size
                try:
                    if file_path.stat().st_size > self.max_file_size_bytes:
                        logger.debug(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue

                # Detect language
                language = self.language_detector.detect_language(str(file_path))
                if language:
                    files.append((file_path, language))

        return files

    def _should_ignore_dir(self, root: str, dirname: str) -> bool:
        """
        Check if directory should be ignored.

        Args:
            root: Parent directory path
            dirname: Directory name

        Returns:
            True if should be ignored
        """
        if not self.use_gitignore:
            return False

        dir_path = Path(root) / dirname
        return self.gitignore_parser.should_ignore_dir(
            str(dir_path),
            str(self.repo_path)
        )

    def _should_ignore_file(self, file_path: Path) -> bool:
        """
        Check if file should be ignored.

        Args:
            file_path: File path

        Returns:
            True if should be ignored
        """
        if not self.use_gitignore:
            return False

        return self.gitignore_parser.should_ignore(
            str(file_path),
            str(self.repo_path)
        )

    def analyze_file(self, file_path: str, language: str) -> Dict[str, Any]:
        """
        Analyze a single file.

        Args:
            file_path: Path to file
            language: Detected language name

        Returns:
            Dictionary with file metrics:
            {
                "lines": int,
                "imports": List[str]
            }
        """
        stats = {
            "lines": 0,
            "imports": []
        }

        # Count lines
        stats["lines"] = self._count_lines(file_path)

        # Try to parse with Tree-sitter if supported
        if self.language_detector.is_supported_language(language):
            grammar_name = self.language_detector.get_grammar_name(language)
            if grammar_name:
                tree = self.tree_sitter_manager.parse_file(file_path, grammar_name)
                if tree:
                    # Extract imports
                    imports = self._extract_imports(tree, language)
                    stats["imports"] = imports

        return stats

    def _extract_imports(self, tree, language: str) -> List[str]:
        """
        Extract import statements from syntax tree.

        Args:
            tree: Tree-sitter syntax tree
            language: Language name

        Returns:
            List of imported module names
        """
        imports = []

        try:
            root_node = tree.root_node

            if language == "Python":
                imports = self._extract_python_imports(root_node)
            elif language in ["JavaScript", "TypeScript", "TSX"]:
                imports = self._extract_javascript_imports(root_node)

        except Exception as e:
            logger.debug(f"Error extracting imports: {e}")

        return imports

    def _extract_python_imports(self, root_node) -> List[str]:
        """Extract Python imports."""
        imports = []

        def traverse(node):
            # import statement: import foo, bar
            if node.type == "import_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(child.text.decode('utf-8'))

            # from statement: from foo import bar
            elif node.type == "import_from_statement":
                for child in node.children:
                    if child.type == "dotted_name":
                        imports.append(child.text.decode('utf-8'))
                        break

            # Recurse
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return list(set(imports))  # Remove duplicates

    def _extract_javascript_imports(self, root_node) -> List[str]:
        """Extract JavaScript/TypeScript imports."""
        imports = []

        def traverse(node):
            # import statement
            if node.type == "import_statement":
                # Look for string literals (module names)
                for child in node.children:
                    if child.type == "string":
                        # Remove quotes
                        import_path = child.text.decode('utf-8').strip('"\'')
                        imports.append(import_path)

            # require() calls (CommonJS)
            elif node.type == "call_expression":
                # Check if it's a require() call
                func = node.child_by_field_name("function")
                if func and func.text == b"require":
                    args = node.child_by_field_name("arguments")
                    if args:
                        for arg in args.children:
                            if arg.type == "string":
                                import_path = arg.text.decode('utf-8').strip('"\'')
                                imports.append(import_path)

            # Recurse
            for child in node.children:
                traverse(child)

        traverse(root_node)
        return list(set(imports))  # Remove duplicates

    def _build_dependency_graph(self) -> None:
        """
        Build dependency graph from collected file imports.

        Groups files by language and builds separate graphs, then combines.
        """
        if not self._file_imports:
            logger.debug("No files to build dependency graph from")
            return

        self._dependency_graph = DependencyGraph(str(self.repo_path))

        # Group imports by language
        imports_by_language: Dict[str, Dict[str, List[str]]] = {}
        for file_path, imports in self._file_imports.items():
            language = self._file_languages.get(file_path, "Unknown")
            if language not in imports_by_language:
                imports_by_language[language] = {}
            imports_by_language[language][file_path] = imports

        # Build graph with the primary language (most files)
        primary_language = max(
            imports_by_language.keys(),
            key=lambda lang: len(imports_by_language[lang]),
            default="Python"
        )

        # Build from all files but use primary language for resolution
        self._dependency_graph.build_from_analysis(
            self._file_imports,
            language=primary_language
        )

        logger.info(
            f"Built dependency graph: {self._dependency_graph.graph.number_of_nodes()} "
            f"modules, {self._dependency_graph.graph.number_of_edges()} dependencies"
        )

    def get_dependency_graph(self) -> Optional[DependencyGraph]:
        """
        Get the dependency graph built during analysis.

        Returns:
            DependencyGraph instance or None if analysis hasn't been run
        """
        return self._dependency_graph

    def get_dependency_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the dependency graph.

        Returns:
            Dictionary with dependency statistics, or empty dict if no graph
        """
        if self._dependency_graph is None:
            return {}

        return self._dependency_graph.get_summary()
