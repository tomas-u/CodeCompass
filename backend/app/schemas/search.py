"""Search schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class SearchFilters(BaseModel):
    """Search filters."""
    languages: Optional[List[str]] = None
    file_patterns: Optional[List[str]] = None
    chunk_types: Optional[List[str]] = None


class SearchRequest(BaseModel):
    """Search request."""
    query: str = Field(..., max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    filters: Optional[SearchFilters] = None


class SearchContext(BaseModel):
    """Search context."""
    module: str
    imports: List[str] = []


class SearchResult(BaseModel):
    """Search result."""
    score: float
    file_path: str
    chunk_type: str
    name: str
    start_line: int
    end_line: int
    content: str
    language: str
    context: Optional[SearchContext] = None


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: int

    class Config:
        from_attributes = True
