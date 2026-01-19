"""Project schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    """Project source type."""
    git_url = "git_url"
    local_path = "local_path"


class ProjectStatus(str, Enum):
    """Project status."""
    pending = "pending"
    cloning = "cloning"
    scanning = "scanning"
    analyzing = "analyzing"
    embedding = "embedding"  # Generating embeddings for RAG
    ready = "ready"
    failed = "failed"


class ProjectSettings(BaseModel):
    """Project settings."""
    ignore_patterns: List[str] = Field(default_factory=lambda: ["*.log", "node_modules"])
    analyze_languages: List[str] = Field(default_factory=lambda: ["python", "javascript", "typescript"])


class LanguageStats(BaseModel):
    """Language statistics."""
    files: int
    lines: int


class ProjectStats(BaseModel):
    """Project statistics."""
    files: int = 0
    directories: int = 0
    lines_of_code: int = 0
    languages: Dict[str, LanguageStats] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1, max_length=100)
    source_type: SourceType
    source: str = Field(..., min_length=1, max_length=500)
    branch: str = Field(default="main", max_length=100)
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None


class ProjectUpdate(BaseModel):
    """Update project request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None


class ProjectResponse(BaseModel):
    """Project response."""
    id: str
    name: str
    description: Optional[str] = None
    source_type: SourceType
    source: str
    branch: str
    local_path: Optional[str] = None
    status: ProjectStatus
    settings: Optional[ProjectSettings] = None
    stats: Optional[ProjectStats] = None
    created_at: datetime
    updated_at: datetime
    last_analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    """Project list item."""
    id: str
    name: str
    source_type: SourceType
    source: str
    status: ProjectStatus
    stats: Optional[ProjectStats] = None
    last_analyzed_at: Optional[datetime] = None
    created_at: datetime


class ProjectListResponse(BaseModel):
    """Project list response."""
    items: List[ProjectListItem]
    total: int
    limit: int
    offset: int
