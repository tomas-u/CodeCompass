"""Diagrams API endpoints."""

from fastapi import APIRouter, HTTPException, Response
from datetime import datetime
from uuid import uuid4

from app.schemas.diagram import (
    DiagramResponse,
    DiagramListResponse,
    DiagramListItem,
    DiagramType,
)
from app.mock_data import get_mock_project, MOCK_DIAGRAMS

router = APIRouter()


@router.get("/{project_id}/diagrams", response_model=DiagramListResponse)
async def list_diagrams(project_id: str):
    """List available diagrams."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items = [
        DiagramListItem(
            id=str(uuid4()),
            type=DiagramType.architecture,
            title="System Architecture",
            preview_available=True
        ),
        DiagramListItem(
            id=str(uuid4()),
            type=DiagramType.dependency,
            title="Module Dependencies",
            preview_available=True
        ),
        DiagramListItem(
            id=str(uuid4()),
            type=DiagramType.directory,
            title="Directory Structure",
            preview_available=True
        ),
    ]

    return DiagramListResponse(items=items)


@router.get("/{project_id}/diagrams/{diagram_type}", response_model=DiagramResponse)
async def get_diagram(project_id: str, diagram_type: DiagramType):
    """Get specific diagram."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get mock diagram
    mermaid_code = MOCK_DIAGRAMS.get(diagram_type.value, "")

    if not mermaid_code:
        raise HTTPException(status_code=404, detail="Diagram not found")

    return DiagramResponse(
        id=str(uuid4()),
        type=diagram_type,
        title=f"{diagram_type.value.title()} Diagram",
        mermaid_code=mermaid_code,
        metadata={
            "nodes": 15,
            "edges": 23,
            "max_depth": 4
        },
        generated_at=datetime.utcnow()
    )


@router.get("/{project_id}/diagrams/{diagram_type}/svg")
async def get_diagram_svg(project_id: str, diagram_type: DiagramType):
    """Get pre-rendered SVG."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Mock SVG response
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
        <text x="200" y="100" text-anchor="middle">Mock SVG Diagram</text>
    </svg>"""

    return Response(content=svg_content, media_type="image/svg+xml")
