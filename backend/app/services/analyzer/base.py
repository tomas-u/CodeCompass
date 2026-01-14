"""Base analyzer abstract class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Abstract base class for code analyzers."""

    def __init__(self, repo_path: str):
        """
        Initialize analyzer.

        Args:
            repo_path: Path to repository to analyze
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self.stats = {
            "files": 0,
            "directories": 0,
            "lines_of_code": 0,
            "languages": {}
        }

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Run full repository analysis.

        Returns:
            Dictionary containing analysis results with structure:
            {
                "files": int,
                "directories": int,
                "lines_of_code": int,
                "languages": {
                    "Python": {"files": int, "lines": int},
                    "JavaScript": {"files": int, "lines": int},
                    ...
                }
            }
        """
        pass

    @abstractmethod
    def analyze_file(self, file_path: str, language: str) -> Dict[str, Any]:
        """
        Analyze a single file.

        Args:
            file_path: Path to file
            language: Detected language name

        Returns:
            Dictionary containing file metrics:
            {
                "lines": int,
                "imports": List[str],  # Optional
                ...
            }
        """
        pass

    def _update_stats(self, language: str, file_stats: Dict[str, Any]) -> None:
        """
        Update aggregate statistics.

        Args:
            language: Language name
            file_stats: File analysis results
        """
        # Initialize language entry if needed
        if language not in self.stats["languages"]:
            self.stats["languages"][language] = {
                "files": 0,
                "lines": 0
            }

        # Update counts
        self.stats["files"] += 1
        lines = file_stats.get("lines", 0)
        self.stats["lines_of_code"] += lines
        self.stats["languages"][language]["files"] += 1
        self.stats["languages"][language]["lines"] += lines

    def _count_lines(self, file_path: str) -> int:
        """
        Count non-empty lines in file.

        Args:
            file_path: Path to file

        Returns:
            Number of non-empty lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f.readlines()]
                # Count non-empty lines
                return sum(1 for line in lines if line)
        except Exception as e:
            logger.warning(f"Error counting lines in {file_path}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current analysis statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats
