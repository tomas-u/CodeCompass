"""Projects API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from uuid import uuid4

from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectListItem,
    ProjectStatus,
)
from app.database import get_db
from app.models.project import Project
from app.services.mock_analysis import simulate_analysis

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new project and start analysis."""
    # Generate new project ID
    project_id = str(uuid4())

    # Create project model
    db_project = Project(
        id=project_id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        source=project.source,
        branch=project.branch or "main",
        local_path=f"/app/repos/{project_id}",
        status=ProjectStatus.pending,
        settings=project.settings.dict() if project.settings else None,
        stats=None,
        last_analyzed_at=None,
    )

    # Save to database
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Trigger mock analysis in background
    background_tasks.add_task(simulate_analysis, project_id)

    return ProjectResponse(**db_project.to_dict())


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = Query(default="created_at", pattern="^(created_at|updated_at|name)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """List all projects."""
    # Build query
    query = db.query(Project)

    # Apply filters
    if status:
        query = query.filter(Project.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Project.name.ilike(search_pattern)) |
            (Project.description.ilike(search_pattern))
        )

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(Project, sort)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    projects = query.offset(offset).limit(limit).all()

    # Convert to list items
    items = [
        ProjectListItem(
            id=p.id,
            name=p.name,
            source_type=p.source_type,
            source=p.source,
            status=p.status,
            stats=p.stats,
            last_analyzed_at=p.last_analyzed_at,
            created_at=p.created_at,
        )
        for p in projects
    ]

    return ProjectListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project with ID '{project_id}' not found",
                "details": {"project_id": project_id}
            }
        )

    return ProjectResponse(**project.to_dict())


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Update project."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    if update.name:
        project.name = update.name
    if update.description is not None:
        project.description = update.description
    if update.settings:
        project.settings = update.settings.dict()

    project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(project)

    return ProjectResponse(**project.to_dict())


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    delete_files: bool = Query(default=True),
    db: Session = Depends(get_db)
):
    """Delete project."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete from database
    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully",
        "deleted": {
            "project": True,
            "analyses": 0,  # TODO: Count actual related records when implemented
            "reports": 0,
            "diagrams": 0,
            "chat_sessions": 0,
            "vector_embeddings": 0,
            "files": delete_files
        }
    }
