"""Code chunk schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ChunkType(str, Enum):
    """Type of code chunk."""
    file = "file"
    segment = "segment"


class ChunkCreate(BaseModel):
    """Schema for creating a chunk (internal use)."""
    id: str
    project_id: str
    file_path: str
    chunk_type: ChunkType
    start_line: int
    end_line: int
    language: Optional[str] = None
    content: str  # The actual text content
    content_hash: str


class ChunkData(BaseModel):
    """
    Data for a code chunk during processing.

    This is the intermediate representation used during chunking
    before storage in both SQLite and Qdrant.
    """
    id: str
    project_id: str
    file_path: str
    chunk_type: ChunkType
    start_line: int
    end_line: int
    language: Optional[str] = None
    content: str
    content_hash: str


class ChunkResponse(BaseModel):
    """Schema for chunk response."""
    id: str
    project_id: str
    file_path: str
    chunk_type: ChunkType
    start_line: int
    end_line: int
    language: Optional[str] = None
    content_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkWithContent(BaseModel):
    """Chunk with content (retrieved from Qdrant)."""
    id: str
    project_id: str
    file_path: str
    chunk_type: ChunkType
    start_line: int
    end_line: int
    language: Optional[str] = None
    content: str
    score: Optional[float] = None  # Relevance score from search


class ChunkSearchResult(BaseModel):
    """Search result for a chunk."""
    chunk: ChunkWithContent
    score: float
