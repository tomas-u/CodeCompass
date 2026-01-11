"""Files API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.schemas.files import (
    FileTreeResponse,
    FileContentResponse,
    FileNode,
    FileTreeStats,
)
from app.mock_data import get_mock_project, MOCK_FILE_TREE, MOCK_FILE_CONTENT

router = APIRouter()


@router.get("/{project_id}/files", response_model=FileTreeResponse)
async def get_file_tree(
    project_id: str,
    depth: int = Query(default=None, ge=1),
    include_hidden: bool = False
):
    """Get file tree structure."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert dict to FileNode
    root = FileNode(**MOCK_FILE_TREE)

    stats = FileTreeStats(
        total_files=150,
        total_directories=25
    )

    return FileTreeResponse(root=root, stats=stats)


@router.get("/{project_id}/files/{file_path:path}", response_model=FileContentResponse)
async def get_file_content(project_id: str, file_path: str):
    """Get file content."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Mock file content
    return FileContentResponse(
        path=file_path,
        name=file_path.split("/")[-1],
        language="python",
        content=MOCK_FILE_CONTENT,
        lines=len(MOCK_FILE_CONTENT.split("\n")),
        size_bytes=len(MOCK_FILE_CONTENT),
        encoding="utf-8",
        last_modified=datetime.utcnow()
    )
