"""Chat API endpoints."""

from fastapi import APIRouter, HTTPException
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
from app.mock_data import get_mock_project, MOCK_CHAT_SESSIONS

router = APIRouter()


@router.post("/{project_id}/chat", response_model=ChatResponse)
async def chat(project_id: str, request: ChatRequest):
    """Send chat message."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate or use existing session
    session_id = request.session_id or str(uuid4())
    message_id = str(uuid4())

    # Mock response
    response_content = ChatResponseContent(
        content=f"""Based on the code analysis, here's what I found:

The codebase uses a **layered architecture pattern** with clear separation between API routes, services, and models.

Key components:
- **API Layer**: Handles HTTP requests/responses
- **Service Layer**: Contains business logic
- **Data Layer**: Database models and operations

For your specific question about "{request.message}", you can find the relevant code in the following files:""",
        format="markdown",
        sources=[
            ChatSource(
                file_path="src/services/auth_service.py",
                start_line=15,
                end_line=45,
                snippet="class AuthService:\n    async def login...",
                relevance_score=0.95
            )
        ] if request.options and request.options.include_sources else [],
        tokens_used=TokenUsage(prompt=1500, completion=350)
    )

    return ChatResponse(
        session_id=session_id,
        message_id=message_id,
        response=response_content,
        created_at=datetime.utcnow()
    )


@router.get("/{project_id}/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(project_id: str):
    """List chat sessions."""
    project = get_mock_project(project_id)

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
async def get_chat_session(project_id: str, session_id: str):
    """Get chat session history."""
    project = get_mock_project(project_id)

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
async def delete_chat_session(project_id: str, session_id: str):
    """Delete chat session."""
    project = get_mock_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Session deleted successfully", "session_id": session_id}
