"""Search API endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchContext,
)
from app.mock_data import get_mock_project, MOCK_SEARCH_RESULTS

router = APIRouter()


@router.post("/{project_id}/search", response_model=SearchResponse)
async def search_code(project_id: str, request: SearchRequest):
    """Semantic code search."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert mock results to SearchResult objects
    results = [
        SearchResult(
            score=r["score"],
            file_path=r["file_path"],
            chunk_type=r["chunk_type"],
            name=r["name"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            content=r["content"],
            language=r["language"],
            context=SearchContext(**r["context"]) if r.get("context") else None
        )
        for r in MOCK_SEARCH_RESULTS[:request.limit]
    ]

    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        search_time_ms=45
    )
