"""Search API endpoints."""

import logging
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.database import get_db
from app.models.project import Project
from app.services.llm import get_embedding_provider, get_vector_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{project_id}/search", response_model=SearchResponse)
async def search_code(project_id: str, request: SearchRequest, db: Session = Depends(get_db)):
    """
    Semantic code search.

    Embeds the query and searches Qdrant for similar code chunks.
    Falls back to empty results if services are unavailable.
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    start_time = time.time()

    # Get providers
    embedding_provider = get_embedding_provider()
    vector_service = get_vector_service()

    # Check if services are available
    embedding_healthy = await embedding_provider.health_check()
    vector_healthy = await vector_service.health_check()

    if not embedding_healthy or not vector_healthy:
        logger.warning(
            f"Search services unavailable (embedding: {embedding_healthy}, "
            f"vector: {vector_healthy})"
        )
        return SearchResponse(
            query=request.query,
            results=[],
            total_results=0,
            search_time_ms=int((time.time() - start_time) * 1000),
        )

    try:
        # Generate query embedding
        query_embedding = await embedding_provider.embed_single(request.query)

        # Build filters from request
        filters = None
        if request.filters:
            filters = {}
            if request.filters.languages:
                filters["languages"] = request.filters.languages
            if request.filters.chunk_types:
                filters["chunk_types"] = request.filters.chunk_types

        # Search Qdrant
        chunks = await vector_service.search(
            query_vector=query_embedding,
            project_id=project_id,
            limit=request.limit,
            filters=filters,
        )

        # Convert to SearchResult objects
        results = []
        for chunk in chunks:
            result = SearchResult(
                score=chunk.score or 0.0,
                file_path=chunk.file_path,
                chunk_type=chunk.chunk_type,
                name=_extract_name_from_path(chunk.file_path),
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                language=chunk.language or "text",
                context=None,  # Could add module/imports context later
            )
            results.append(result)

        search_time_ms = int((time.time() - start_time) * 1000)

        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time_ms,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return SearchResponse(
            query=request.query,
            results=[],
            total_results=0,
            search_time_ms=int((time.time() - start_time) * 1000),
        )


def _extract_name_from_path(file_path: str) -> str:
    """Extract a display name from a file path."""
    # Get just the filename without extension
    parts = file_path.split("/")
    filename = parts[-1] if parts else file_path

    # Remove common extensions
    for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs"]:
        if filename.endswith(ext):
            return filename[:-len(ext)]

    return filename
