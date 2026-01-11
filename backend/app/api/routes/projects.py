"""Projects API endpoints."""

from fastapi import APIRouter, HTTPException, Query
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
from app.mock_data import MOCK_PROJECTS, get_mock_project, get_all_mock_projects

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate):
    """Create a new project."""
    # Generate new project ID
    project_id = str(uuid4())

    # Create project data
    new_project = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "source_type": project.source_type,
        "source": project.source,
        "branch": project.branch,
        "local_path": f"/app/repos/{project_id}",
        "status": ProjectStatus.pending,
        "settings": project.settings.dict() if project.settings else None,
        "stats": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_analyzed_at": None,
    }

    # Store in mock data (for session)
    MOCK_PROJECTS[project_id] = new_project

    return ProjectResponse(**new_project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = Query(default="created_at", pattern="^(created_at|updated_at|name)$"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all projects."""
    projects = get_all_mock_projects()

    # Apply filters
    if status:
        projects = [p for p in projects if p.get("status") == status]

    if search:
        search_lower = search.lower()
        projects = [
            p for p in projects
            if search_lower in p.get("name", "").lower()
            or search_lower in p.get("description", "").lower()
        ]

    # Sort
    reverse = order == "desc"
    projects = sorted(projects, key=lambda x: x.get(sort, ""), reverse=reverse)

    # Paginate
    total = len(projects)
    projects = projects[offset:offset + limit]

    # Convert to list items
    items = [
        ProjectListItem(
            id=p["id"],
            name=p["name"],
            source_type=p["source_type"],
            status=p["status"],
            stats=p.get("stats"),
            last_analyzed_at=p.get("last_analyzed_at"),
            created_at=p["created_at"],
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
async def get_project(project_id: str):
    """Get project by ID."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PROJECT_NOT_FOUND",
                "message": f"Project with ID '{project_id}' not found",
                "details": {"project_id": project_id}
            }
        )

    return ProjectResponse(**project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate):
    """Update project."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    if update.name:
        project["name"] = update.name
    if update.description is not None:
        project["description"] = update.description
    if update.settings:
        project["settings"] = update.settings.dict()

    project["updated_at"] = datetime.utcnow().isoformat()

    return ProjectResponse(**project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    delete_files: bool = Query(default=True)
):
    """Delete project."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Remove from mock data
    del MOCK_PROJECTS[project_id]

    return {
        "message": "Project deleted successfully",
        "deleted": {
            "project": True,
            "analyses": 3,
            "reports": 4,
            "diagrams": 5,
            "chat_sessions": 2,
            "vector_embeddings": 1500,
            "files": delete_files
        }
    }
