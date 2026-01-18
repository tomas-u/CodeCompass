"""Chat API endpoints."""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionListItem,
    ChatMessage,
    ChatResponseContent,
    ChatSource,
    MessageRole,
    TokenUsage,
)
from app.mock_data import MOCK_CHAT_SESSIONS
from app.database import get_db
from app.models.project import Project
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def stream_chat_response(project_id: str, project_name: str, message: str, max_chunks: int):
    """Generate SSE stream for chat response."""
    rag_service = get_rag_service()

    async for event in rag_service.chat_with_context_stream(
        query=message,
        project_id=project_id,
        project_name=project_name,
        max_chunks=max_chunks,
    ):
        event_type = event.get("type", "unknown")
        event_data = json.dumps(event)
        yield f"event: {event_type}\ndata: {event_data}\n\n"


@router.post("/{project_id}/chat")
async def chat(project_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send chat message with RAG-powered response.

    Uses the RAG service to retrieve relevant code context and generate
    context-aware responses.

    If stream=true in options, returns Server-Sent Events (SSE) stream.
    Otherwise returns complete ChatResponse.
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine options
    max_chunks = 5
    include_sources = True
    stream = False
    if request.options:
        max_chunks = request.options.max_context_chunks
        include_sources = request.options.include_sources
        stream = request.options.stream

    # Handle streaming response
    if stream:
        return StreamingResponse(
            stream_chat_response(
                project_id=project_id,
                project_name=project.name,
                message=request.message,
                max_chunks=max_chunks,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering in nginx
            },
        )

    # Non-streaming response (existing behavior)
    session_id = request.session_id or str(uuid4())
    message_id = str(uuid4())

    # Get RAG service
    rag_service = get_rag_service()

    # Use RAG service to generate response
    rag_response = await rag_service.chat_with_context(
        query=request.message,
        project_id=project_id,
        project_name=project.name,
        max_chunks=max_chunks,
        include_sources=include_sources,
    )

    # Convert RAG sources to ChatSource objects
    sources = []
    if include_sources and rag_response.sources:
        for chunk in rag_response.sources:
            # Create a snippet (first 200 chars of content)
            snippet = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content

            source = ChatSource(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                snippet=snippet,
                relevance_score=chunk.score or 0.0,
            )
            sources.append(source)

    response_content = ChatResponseContent(
        content=rag_response.content,
        format="markdown",
        sources=sources,
        tokens_used=TokenUsage(
            prompt=rag_response.prompt_tokens,
            completion=rag_response.completion_tokens,
        )
    )

    return ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=response_content,
        created_at=datetime.utcnow()
    )


@router.get("/{project_id}/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(project_id: str, db: Session = Depends(get_db)):
    """List chat sessions."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    items = [
        ChatSessionListItem(
            id=session_id,
            title=session["title"],
            message_count=len(session["messages"]),
            created_at=session["created_at"],
            last_message_at=session["messages"][-1]["created_at"]
        )
        for session_id, session in MOCK_CHAT_SESSIONS.items()
    ]

    return ChatSessionListResponse(items=items)


@router.get("/{project_id}/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(project_id: str, session_id: str, db: Session = Depends(get_db)):
    """Get chat session history."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    session = MOCK_CHAT_SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = [
        ChatMessage(
            id=msg["id"],
            role=MessageRole(msg["role"]),
            content=msg["content"],
            sources=[
                ChatSource(**src)
                for src in msg.get("sources", [])
            ] if msg.get("sources") else None,
            created_at=msg["created_at"]
        )
        for msg in session["messages"]
    ]

    return ChatSessionResponse(
        id=session_id,
        title=session["title"],
        messages=messages,
        created_at=session["created_at"]
    )


@router.delete("/{project_id}/chat/sessions/{session_id}")
async def delete_chat_session(project_id: str, session_id: str, db: Session = Depends(get_db)):
    """Delete chat session."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Session deleted successfully", "session_id": session_id}
