"""Reports API endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.report import Report
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportListItem,
    ReportType,
    ReportContent,
    ReportSection,
)
from app.schemas.project import ProjectStatus
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{project_id}/reports", response_model=ReportListResponse)
async def list_reports(project_id: str, db: Session = Depends(get_db)):
    """List all reports for a project."""
    # Check project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get existing reports from database
    reports = db.query(Report).filter(Report.project_id == project_id).all()

    items = []
    for report in reports:
        items.append(
            ReportListItem(
                id=report.id,
                type=ReportType(report.type),
                title=report.title,
                model_used=report.model_used,
                generated_at=report.created_at,
            )
        )

    # If no reports exist but project is ready, show available report types
    if not items and project.status == ProjectStatus.ready:
        # Return placeholder items for available reports
        items = [
            ReportListItem(
                id="not-generated",
                type=ReportType.summary,
                title="Project Summary (Not Generated)",
                generated_at=datetime.utcnow(),
            ),
            ReportListItem(
                id="not-generated",
                type=ReportType.architecture,
                title="Architecture Overview (Not Generated)",
                generated_at=datetime.utcnow(),
            ),
            ReportListItem(
                id="not-generated",
                type=ReportType.dependencies,
                title="Dependency Analysis (Not Generated)",
                generated_at=datetime.utcnow(),
            ),
        ]

    return ReportListResponse(items=items)


@router.get("/{project_id}/reports/{report_type}", response_model=ReportResponse)
async def get_report(
    project_id: str,
    report_type: ReportType,
    generate: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get a specific report.

    Args:
        project_id: Project ID
        report_type: Type of report (summary, architecture, dependencies)
        generate: If True, generate report if it doesn't exist
    """
    # Check project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check project is ready
    if project.status != ProjectStatus.ready:
        raise HTTPException(
            status_code=400,
            detail=f"Project is not ready for reports. Status: {project.status.value}"
        )

    # Check for existing report
    report = db.query(Report).filter(
        Report.project_id == project_id,
        Report.type == report_type.value,
    ).first()

    # Generate if doesn't exist and generation is enabled
    if not report and generate:
        try:
            generator = ReportGenerator(db)
            report = await generator.generate_report(project_id, report_type)
        except RuntimeError as e:
            # LLM not available
            raise HTTPException(
                status_code=503,
                detail=f"Report generation unavailable: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate report: {str(e)}"
            )

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report not found. Set generate=true to create it."
        )

    # Parse sections from stored data
    sections = []
    if report.sections:
        for section in report.sections:
            sections.append(
                ReportSection(
                    id=section.get("id", ""),
                    title=section.get("title", ""),
                    content=section.get("content", ""),
                )
            )

    # Build response
    content = ReportContent(
        format="markdown",
        body=report.content,
        sections=sections,
    )

    return ReportResponse(
        id=report.id,
        type=ReportType(report.type),
        title=report.title,
        content=content,
        metadata=report.report_metadata,
        model_used=report.model_used,
        generated_at=report.created_at,
    )


@router.post("/{project_id}/reports/generate")
async def generate_reports(
    project_id: str,
    report_type: Optional[ReportType] = None,
    force: bool = False,
    db: Session = Depends(get_db),
):
    """
    Generate or regenerate reports for a project.

    Args:
        project_id: Project ID
        report_type: Optional specific report type. If None, generates all types.
        force: Force regeneration even if report exists
    """
    # Check project exists and is ready
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != ProjectStatus.ready:
        raise HTTPException(
            status_code=400,
            detail=f"Project is not ready. Status: {project.status.value}"
        )

    generator = ReportGenerator(db)

    try:
        if report_type:
            # Generate specific report type
            report = await generator.generate_report(project_id, report_type, force=force)
            return {
                "message": f"Generated {report_type.value} report",
                "report_id": report.id,
                "generation_time_ms": report.generation_time_ms,
            }
        else:
            # Generate all reports
            reports = await generator.generate_all_reports(project_id, force=force)
            return {
                "message": f"Generated {len(reports)} reports",
                "reports": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "generation_time_ms": r.generation_time_ms,
                    }
                    for r in reports
                ],
            }
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Report generation unavailable: {str(e)}"
        )
    except Exception as e:
        error_msg = str(e) or f"{type(e).__name__} (no details)"
        logger.error(f"Error generating reports: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate reports: {error_msg}"
        )


@router.delete("/{project_id}/reports/{report_type}")
async def delete_report(
    project_id: str,
    report_type: ReportType,
    db: Session = Depends(get_db),
):
    """Delete a specific report."""
    # Check project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find and delete report
    report = db.query(Report).filter(
        Report.project_id == project_id,
        Report.type == report_type.value,
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"message": f"Deleted {report_type.value} report"}
