"""Report schemas."""

from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    """Report type."""
    summary = "summary"
    architecture = "architecture"
    developer = "developer"
    dependencies = "dependencies"


class ReportSection(BaseModel):
    """Report section."""
    id: str
    title: str
    content: str


class ReportContent(BaseModel):
    """Report content."""
    format: str = "markdown"
    body: str
    sections: List[ReportSection] = []


class ReportResponse(BaseModel):
    """Report response."""
    id: str
    type: ReportType
    title: str
    content: ReportContent
    metadata: Optional[Dict] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    """Report list item."""
    id: str
    type: ReportType
    title: str
    generated_at: datetime


class ReportListResponse(BaseModel):
    """Report list response."""
    items: List[ReportListItem]
