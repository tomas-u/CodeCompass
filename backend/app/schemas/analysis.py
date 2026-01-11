"""Analysis schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Analysis status."""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(str, Enum):
    """Step status."""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class AnalysisStep(BaseModel):
    """Analysis step details."""
    name: str
    status: StepStatus
    progress_percent: Optional[int] = None
    duration_ms: Optional[int] = None
    details: Optional[Dict] = None


class AnalysisProgress(BaseModel):
    """Analysis progress."""
    current_step: str
    steps: List[AnalysisStep]
    overall_percent: int
    estimated_remaining_seconds: Optional[int] = None


class AnalysisOptions(BaseModel):
    """Analysis options."""
    generate_reports: bool = True
    generate_diagrams: bool = True
    build_embeddings: bool = True


class AnalysisCreate(BaseModel):
    """Create analysis request."""
    force: bool = False
    options: Optional[AnalysisOptions] = None


class AnalysisResponse(BaseModel):
    """Analysis response."""
    id: str
    project_id: str
    status: AnalysisStatus
    progress: Optional[AnalysisProgress] = None
    stats: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisStartResponse(BaseModel):
    """Analysis start response."""
    analysis_id: str
    status: AnalysisStatus
    message: str
    estimated_duration_seconds: Optional[int] = None


class AnalysisCancelResponse(BaseModel):
    """Analysis cancel response."""
    message: str
    analysis_id: str
