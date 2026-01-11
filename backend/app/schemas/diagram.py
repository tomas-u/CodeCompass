"""Diagram schemas."""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class DiagramType(str, Enum):
    """Diagram type."""
    architecture = "architecture"
    dependency = "dependency"
    directory = "directory"
    class_diagram = "class"
    sequence = "sequence"


class DiagramResponse(BaseModel):
    """Diagram response."""
    id: str
    type: DiagramType
    title: str
    mermaid_code: str
    metadata: Optional[Dict] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class DiagramListItem(BaseModel):
    """Diagram list item."""
    id: str
    type: DiagramType
    title: str
    preview_available: bool = True


class DiagramListResponse(BaseModel):
    """Diagram list response."""
    items: List[DiagramListItem]
