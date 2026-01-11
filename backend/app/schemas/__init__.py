"""Pydantic schemas for request/response validation."""

from .project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStats,
)
from .analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisProgress,
    AnalysisStep,
)
from .report import (
    ReportResponse,
    ReportListResponse,
    ReportContent,
)
from .diagram import (
    DiagramResponse,
    DiagramListResponse,
)
from .chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatSessionListResponse,
)
from .search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from .files import (
    FileTreeResponse,
    FileContentResponse,
    FileNode,
)
from .settings import (
    SettingsResponse,
    SettingsUpdate,
    ProvidersResponse,
)

__all__ = [
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    "ProjectStats",
    # Analysis
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisProgress",
    "AnalysisStep",
    # Report
    "ReportResponse",
    "ReportListResponse",
    "ReportContent",
    # Diagram
    "DiagramResponse",
    "DiagramListResponse",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatSessionResponse",
    "ChatSessionListResponse",
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    # Files
    "FileTreeResponse",
    "FileContentResponse",
    "FileNode",
    # Settings
    "SettingsResponse",
    "SettingsUpdate",
    "ProvidersResponse",
]
