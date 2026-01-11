"""File schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """Node type."""
    file = "file"
    directory = "directory"


class FileNode(BaseModel):
    """File tree node."""
    name: str
    type: NodeType
    language: Optional[str] = None
    size_bytes: Optional[int] = None
    lines: Optional[int] = None
    children: Optional[List["FileNode"]] = None


class FileTreeStats(BaseModel):
    """File tree statistics."""
    total_files: int
    total_directories: int


class FileTreeResponse(BaseModel):
    """File tree response."""
    root: FileNode
    stats: FileTreeStats

    class Config:
        from_attributes = True


class FileContentResponse(BaseModel):
    """File content response."""
    path: str
    name: str
    language: str
    content: str
    lines: int
    size_bytes: int
    encoding: str = "utf-8"
    last_modified: datetime

    class Config:
        from_attributes = True
