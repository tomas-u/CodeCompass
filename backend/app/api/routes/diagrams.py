"""Diagrams API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from app.database import get_db
from app.models.project import Project
from app.models.diagram import Diagram
from app.schemas.project import ProjectStatus
from app.schemas.diagram import (
    DiagramResponse,
    DiagramListResponse,
    DiagramListItem,
    DiagramType,
)
from app.services.diagram_generator import DiagramGenerator
from app.services.analyzer.generic_analyzer import GenericAnalyzer
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_project_or_404(project_id: str, db: Session) -> Project:
    """Get project from database or raise 404."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def generate_dependency_diagram(
    project: Project,
    db: Session,
    path: str = "",
    depth: int = 1
) -> Diagram:
    """Generate dependency diagram for a project.

    Args:
        project: The project to generate diagram for
        db: Database session
        path: Directory path to filter to (empty = root level for drill-down)
        depth: How many directory levels to show
    """
    if not project.local_path or not Path(project.local_path).exists():
        raise HTTPException(
            status_code=400,
            detail="Project has not been analyzed yet. Run analysis first."
        )

    # Run analyzer to get dependency graph
    analyzer = GenericAnalyzer(
        repo_path=project.local_path,
        max_file_size_mb=settings.max_file_size_mb,
        use_gitignore=True
    )
    analyzer.analyze()

    dep_graph = analyzer.get_dependency_graph()
    if not dep_graph:
        raise HTTPException(
            status_code=500,
            detail="Failed to build dependency graph"
        )

    # Generate diagram - use path-based if path is specified or graph is large
    generator = DiagramGenerator()
    node_count = dep_graph.graph.number_of_nodes()

    # Use drill-down mode for large graphs OR when path is specified
    if path or node_count > generator.GROUPING_THRESHOLD:
        diagram_data = generator.generate_dependency_diagram_for_path(
            dep_graph,
            base_path=path,
            depth=depth,
            title=f"Dependencies: {project.name}"
        )
    else:
        # Small graph - show everything
        diagram_data = generator.generate_dependency_diagram(
            dep_graph,
            title=f"Dependencies: {project.name}"
        )

    # For path-based queries, don't cache (dynamic content)
    if path:
        # Return a temporary diagram object without persisting
        return Diagram(
            id=diagram_data["id"],
            project_id=project.id,
            type=DiagramType.dependency,
            title=diagram_data["title"],
            mermaid_code=diagram_data["mermaid_code"],
            diagram_metadata=diagram_data["metadata"]
        )

    # Check if diagram already exists (to preserve ID on updates)
    existing = db.query(Diagram).filter(
        Diagram.project_id == project.id,
        Diagram.type == DiagramType.dependency
    ).first()

    if existing:
        # Update existing diagram (preserve ID for consistency)
        existing.mermaid_code = diagram_data["mermaid_code"]
        existing.diagram_metadata = diagram_data["metadata"]
        existing.title = diagram_data["title"]
        db.commit()
        return existing
    else:
        # Create new diagram
        diagram = Diagram(
            id=diagram_data["id"],
            project_id=project.id,
            type=DiagramType.dependency,
            title=diagram_data["title"],
            mermaid_code=diagram_data["mermaid_code"],
            diagram_metadata=diagram_data["metadata"]
        )
        db.add(diagram)
        db.commit()
        db.refresh(diagram)
        return diagram


def generate_directory_diagram(project: Project, db: Session) -> Diagram:
    """Generate directory structure diagram for a project."""
    if not project.local_path or not Path(project.local_path).exists():
        raise HTTPException(
            status_code=400,
            detail="Project has not been analyzed yet. Run analysis first."
        )

    # Check if diagram already exists (to preserve ID on updates)
    existing = db.query(Diagram).filter(
        Diagram.project_id == project.id,
        Diagram.type == DiagramType.directory
    ).first()

    generator = DiagramGenerator()
    diagram_data = generator.generate_directory_diagram(
        repo_path=project.local_path,
        max_depth=3
    )

    if existing:
        # Update existing diagram (preserve ID for consistency)
        existing.mermaid_code = diagram_data["mermaid_code"]
        existing.diagram_metadata = diagram_data["metadata"]
        existing.title = f"Directory Structure: {project.name}"
        db.commit()
        return existing
    else:
        # Create new diagram
        diagram = Diagram(
            id=diagram_data["id"],
            project_id=project.id,
            type=DiagramType.directory,
            title=f"Directory Structure: {project.name}",
            mermaid_code=diagram_data["mermaid_code"],
            diagram_metadata=diagram_data["metadata"]
        )
        db.add(diagram)
        db.commit()
        db.refresh(diagram)
        return diagram


@router.get("/{project_id}/diagrams", response_model=DiagramListResponse)
async def list_diagrams(project_id: str, db: Session = Depends(get_db)):
    """
    List available diagrams for a project.

    Returns the list of diagram types that can be generated.
    """
    project = get_project_or_404(project_id, db)

    # Check if project has been analyzed
    has_analysis = project.status == ProjectStatus.ready and project.local_path

    items = []

    # Dependency diagram - available if project is analyzed
    items.append(DiagramListItem(
        id=str(uuid4()),
        type=DiagramType.dependency,
        title="Module Dependencies",
        preview_available=has_analysis
    ))

    # Directory diagram - available if project has local path
    items.append(DiagramListItem(
        id=str(uuid4()),
        type=DiagramType.directory,
        title="Directory Structure",
        preview_available=has_analysis
    ))

    # Architecture diagram - placeholder for future
    items.append(DiagramListItem(
        id=str(uuid4()),
        type=DiagramType.architecture,
        title="System Architecture",
        preview_available=False  # Not yet implemented
    ))

    return DiagramListResponse(items=items)


@router.get("/{project_id}/diagrams/{diagram_type}", response_model=DiagramResponse)
async def get_diagram(
    project_id: str,
    diagram_type: DiagramType,
    regenerate: bool = False,
    path: str = "",
    depth: int = 1,
    db: Session = Depends(get_db)
):
    """
    Get a specific diagram for a project.

    Args:
        project_id: Project ID
        diagram_type: Type of diagram to get
        regenerate: If True, regenerate even if cached
        path: For dependency diagrams, filter to this directory path (enables drill-down)
        depth: For dependency diagrams, how many directory levels to show
    """
    project = get_project_or_404(project_id, db)

    # For path-based queries, always generate fresh (don't use cache)
    use_cache = not regenerate and not path

    # Check for cached diagram (unless regenerate requested or path specified)
    if use_cache:
        cached = db.query(Diagram).filter(
            Diagram.project_id == project_id,
            Diagram.type == diagram_type
        ).first()

        if cached:
            return DiagramResponse(
                id=cached.id,
                type=cached.type,
                title=cached.title,
                mermaid_code=cached.mermaid_code,
                metadata=cached.diagram_metadata,
                generated_at=cached.created_at
            )

    # Generate diagram based on type
    if diagram_type == DiagramType.dependency:
        diagram = generate_dependency_diagram(project, db, path=path, depth=depth)
    elif diagram_type == DiagramType.directory:
        diagram = generate_directory_diagram(project, db)
    elif diagram_type == DiagramType.architecture:
        # Architecture diagram not yet implemented
        raise HTTPException(
            status_code=501,
            detail="Architecture diagram generation not yet implemented"
        )
    elif diagram_type == DiagramType.class_diagram:
        raise HTTPException(
            status_code=501,
            detail="Class diagram generation not yet implemented"
        )
    elif diagram_type == DiagramType.sequence:
        raise HTTPException(
            status_code=501,
            detail="Sequence diagram generation not yet implemented"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown diagram type: {diagram_type}")

    return DiagramResponse(
        id=diagram.id,
        type=diagram.type,
        title=diagram.title,
        mermaid_code=diagram.mermaid_code,
        metadata=diagram.diagram_metadata,
        generated_at=diagram.created_at or datetime.utcnow()
    )


@router.get("/{project_id}/diagrams/{diagram_type}/svg")
async def get_diagram_svg(
    project_id: str,
    diagram_type: DiagramType,
    db: Session = Depends(get_db)
):
    """
    Get pre-rendered SVG for a diagram.

    Note: SVG rendering requires server-side Mermaid CLI or external service.
    Currently returns a placeholder indicating client-side rendering is needed.
    """
    project = get_project_or_404(project_id, db)

    # Get the diagram first
    diagram = db.query(Diagram).filter(
        Diagram.project_id == project_id,
        Diagram.type == diagram_type
    ).first()

    if not diagram:
        # Try to generate it
        try:
            if diagram_type == DiagramType.dependency:
                diagram = generate_dependency_diagram(project, db)
            elif diagram_type == DiagramType.directory:
                diagram = generate_directory_diagram(project, db)
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Diagram not found and cannot be generated"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate diagram: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate diagram")

    # Note: Server-side SVG rendering requires mermaid-cli (mmdc)
    # For now, return a placeholder suggesting client-side rendering
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200">
        <rect width="600" height="200" fill="#f5f5f5"/>
        <text x="300" y="80" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
            SVG rendering requires client-side Mermaid.js
        </text>
        <text x="300" y="110" text-anchor="middle" font-family="Arial" font-size="12" fill="#999">
            Use GET /diagrams/{diagram_type} for Mermaid code
        </text>
        <text x="300" y="140" text-anchor="middle" font-family="Arial" font-size="10" fill="#ccc">
            Diagram: {diagram.title}
        </text>
    </svg>"""

    return Response(content=svg_content, media_type="image/svg+xml")


@router.post("/{project_id}/diagrams/generate")
async def regenerate_all_diagrams(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Regenerate all diagrams for a project.

    Useful after re-analysis or code changes.
    """
    project = get_project_or_404(project_id, db)

    if project.status != ProjectStatus.ready:
        raise HTTPException(
            status_code=400,
            detail="Project must be in 'ready' status to generate diagrams"
        )

    generated = []
    errors = []

    # Generate dependency diagram
    try:
        diagram = generate_dependency_diagram(project, db)
        generated.append({
            "type": "dependency",
            "id": diagram.id,
            "title": diagram.title
        })
    except Exception as e:
        logger.error(f"Failed to generate dependency diagram: {e}")
        errors.append({"type": "dependency", "error": str(e)})

    # Generate directory diagram
    try:
        diagram = generate_directory_diagram(project, db)
        generated.append({
            "type": "directory",
            "id": diagram.id,
            "title": diagram.title
        })
    except Exception as e:
        logger.error(f"Failed to generate directory diagram: {e}")
        errors.append({"type": "directory", "error": str(e)})

    return {
        "message": f"Generated {len(generated)} diagrams",
        "generated": generated,
        "errors": errors if errors else None
    }
