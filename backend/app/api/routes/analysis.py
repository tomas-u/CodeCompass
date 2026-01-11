"""Analysis API endpoints."""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4

from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisStartResponse,
    AnalysisCancelResponse,
    AnalysisStatus,
    AnalysisProgress,
    AnalysisStep,
    StepStatus,
)
from app.mock_data import get_mock_project

router = APIRouter()

# In-memory storage for analyses
MOCK_ANALYSES = {}


@router.post("/{project_id}/analyze", response_model=AnalysisStartResponse, status_code=202)
async def start_analysis(project_id: str, options: AnalysisCreate = None):
    """Start code analysis."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create analysis
    analysis_id = str(uuid4())
    analysis = {
        "id": analysis_id,
        "project_id": project_id,
        "status": AnalysisStatus.queued,
        "progress": None,
        "stats": None,
        "error": None,
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.utcnow(),
    }

    MOCK_ANALYSES[analysis_id] = analysis

    return AnalysisStartResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.queued,
        message="Analysis started",
        estimated_duration_seconds=120
    )


@router.get("/{project_id}/analysis", response_model=AnalysisResponse)
async def get_analysis_status(project_id: str):
    """Get latest analysis status."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return mock analysis in progress
    analysis_id = str(uuid4())

    # Mock progress
    progress = AnalysisProgress(
        current_step="analyzing",
        steps=[
            AnalysisStep(
                name="cloning",
                status=StepStatus.completed,
                duration_ms=5000
            ),
            AnalysisStep(
                name="scanning",
                status=StepStatus.completed,
                duration_ms=2000,
                details={"files_found": 150}
            ),
            AnalysisStep(
                name="analyzing",
                status=StepStatus.running,
                progress_percent=67,
                details={
                    "current_file": "src/services/auth.ts",
                    "files_processed": 100,
                    "files_total": 150
                }
            ),
            AnalysisStep(
                name="generating_reports",
                status=StepStatus.pending
            ),
            AnalysisStep(
                name="building_index",
                status=StepStatus.pending
            ),
        ],
        overall_percent=45,
        estimated_remaining_seconds=90
    )

    return AnalysisResponse(
        id=analysis_id,
        project_id=project_id,
        status=AnalysisStatus.running,
        progress=progress,
        stats=None,
        error=None,
        started_at=datetime.utcnow(),
        completed_at=None,
        created_at=datetime.utcnow()
    )


@router.delete("/{project_id}/analysis", response_model=AnalysisCancelResponse)
async def cancel_analysis(project_id: str):
    """Cancel ongoing analysis."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis_id = str(uuid4())

    return AnalysisCancelResponse(
        message="Analysis cancelled",
        analysis_id=analysis_id
    )
