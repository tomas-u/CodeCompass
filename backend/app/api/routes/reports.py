"""Reports API endpoints."""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from uuid import uuid4

from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ReportType,
    ReportContent,
    ReportSection,
)
from app.mock_data import get_mock_project, MOCK_ARCHITECTURE_REPORT

router = APIRouter()


@router.get("/{project_id}/reports", response_model=ReportListResponse)
async def list_reports(project_id: str):
    """List all reports for a project."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items = [
        ReportListItem(
            id=str(uuid4()),
            type=ReportType.summary,
            title="Project Summary",
            generated_at=datetime.utcnow()
        ),
        ReportListItem(
            id=str(uuid4()),
            type=ReportType.architecture,
            title="Architecture Overview",
            generated_at=datetime.utcnow()
        ),
        ReportListItem(
            id=str(uuid4()),
            type=ReportType.dependencies,
            title="Dependency Analysis",
            generated_at=datetime.utcnow()
        ),
    ]

    return ReportListResponse(items=items)


@router.get("/{project_id}/reports/{report_type}", response_model=ReportResponse)
async def get_report(project_id: str, report_type: ReportType):
    """Get specific report."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Mock report content
    content = ReportContent(
        format="markdown",
        body=MOCK_ARCHITECTURE_REPORT,
        sections=[
            ReportSection(
                id="tech-stack",
                title="Technology Stack",
                content="..."
            ),
            ReportSection(
                id="architecture-pattern",
                title="Architecture Pattern",
                content="This project follows a **layered architecture**..."
            )
        ]
    )

    return ReportResponse(
        id=str(uuid4()),
        type=report_type,
        title=f"{report_type.value.title()} Report",
        content=content,
        metadata={
            "languages": ["python", "typescript"],
            "frameworks": ["fastapi", "react"],
            "patterns_detected": ["mvc", "repository"]
        },
        generated_at=datetime.utcnow()
    )
