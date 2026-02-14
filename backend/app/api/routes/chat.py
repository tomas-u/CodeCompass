"""Chat API endpoints with persistent sessions."""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
from typing import Optional

from app.database import get_db, SessionLocal
from app.models.project import Project
from app.models.chat import ChatSession, ChatMessage as ChatMessageModel, MessageRole as DBMessageRole
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
    ChatSessionCreate,
    ChatSessionUpdate,
)
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


def get_project_or_404(project_id: str, db: Session) -> Project:
    """Get project from database or raise 404."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def generate_introduction_message(project: Project) -> str:
    """Generate contextual introduction message for a new chat session."""
    stats = project.stats or {}
    languages = stats.get("languages", {})
    total_files = stats.get("total_files", "several")

    # Determine primary language
    primary_lang = "code"
    if languages:
        # Language values can be dicts like {"files": 10, "lines": 500} or simple counts
        def get_file_count(lang_key):
            val = languages[lang_key]
            if isinstance(val, dict):
                return val.get("files", 0)
            return val
        primary_lang = max(languages.keys(), key=get_file_count)

    intro = f"""Hi! I'm your CodeCompass assistant for **{project.name}**.

I've analyzed this {primary_lang} codebase ({total_files} files) and can help you with:
• Understanding how specific features work
• Finding where code is located
• Explaining dependencies and architecture
• Answering questions about patterns and conventions

What would you like to know?"""

    return intro


def get_or_create_active_session(
    project_id: str,
    db: Session,
    session_id: Optional[str] = None
) -> tuple[ChatSession, bool]:
    """
    Get existing session or create new one.

    Returns:
        Tuple of (session, is_new_session)
    """
    if session_id:
        # Try to get specific session
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.project_id == project_id
        ).first()
        if session:
            return session, False

    # Look for active session for this project
    active_session = db.query(ChatSession).filter(
        ChatSession.project_id == project_id,
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).first()

    if active_session:
        return active_session, False

    # Create new session
    new_session = ChatSession(
        id=str(uuid4()),
        project_id=project_id,
        is_active=True
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session, True


async def stream_chat_response(
    project_id: str,
    project_name: str,
    message: str,
    max_chunks: int,
    session_id: str,
    assistant_message_id: str,
):
    """Generate SSE stream for chat response and persist the result."""
    rag_service = get_rag_service()
    accumulated_content = ""
    sources_data = None

    try:
        async for event in rag_service.chat_with_context_stream(
            query=message,
            project_id=project_id,
            project_name=project_name,
            max_chunks=max_chunks,
        ):
            event_type = event.get("type", "unknown")

            # Accumulate content from tokens
            if event_type == "token" and "content" in event:
                accumulated_content += event["content"]
            elif event_type == "sources" and "sources" in event:
                sources_data = []
                for src in event["sources"]:
                    snippet = src.get("content", "")
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    sources_data.append({
                        "file_path": src.get("file_path", ""),
                        "start_line": src.get("start_line", 0),
                        "end_line": src.get("end_line", 0),
                        "snippet": snippet,
                        "relevance_score": src.get("score", 0.0),
                    })

            event_data = json.dumps(event)
            yield f"event: {event_type}\ndata: {event_data}\n\n"
    finally:
        # Persist the assistant response after streaming completes
        if accumulated_content:
            try:
                db = SessionLocal()
                try:
                    assistant_message = ChatMessageModel(
                        id=assistant_message_id,
                        session_id=session_id,
                        role=DBMessageRole.assistant,
                        content=accumulated_content,
                        sources=sources_data,
                    )
                    db.add(assistant_message)

                    # Update session timestamp
                    session = db.query(ChatSession).filter(
                        ChatSession.id == session_id
                    ).first()
                    if session:
                        session.updated_at = datetime.utcnow()

                    db.commit()
                    logger.debug(f"Persisted streaming response to session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to persist streaming response: {e}")
                    db.rollback()
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Failed to create DB session for persistence: {e}")


@router.post("/{project_id}/chat")
async def chat(project_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send chat message with RAG-powered response.

    Uses the RAG service to retrieve relevant code context and generate
    context-aware responses. Messages are persisted to the database.

    If stream=true in options, returns Server-Sent Events (SSE) stream.
    Otherwise returns complete ChatResponse.
    """
    project = get_project_or_404(project_id, db)

    # Determine options
    max_chunks = 5
    include_sources = True
    stream = False
    if request.options:
        max_chunks = request.options.max_context_chunks
        include_sources = request.options.include_sources
        stream = request.options.stream

    # Handle streaming response with persistence
    if stream:
        # Get or create session before streaming starts
        session, is_new_session = get_or_create_active_session(
            project_id, db, request.session_id
        )

        # If new session, add introduction message and set title
        if is_new_session:
            intro_content = generate_introduction_message(project)
            intro_message = ChatMessageModel(
                id=str(uuid4()),
                session_id=session.id,
                role=DBMessageRole.assistant,
                content=intro_content,
                sources=None,
            )
            db.add(intro_message)
            session.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            db.commit()

        # Save user message before streaming
        user_message = ChatMessageModel(
            id=str(uuid4()),
            session_id=session.id,
            role=DBMessageRole.user,
            content=request.message,
        )
        db.add(user_message)
        db.commit()

        assistant_message_id = str(uuid4())

        # Include session_id in the stream so frontend can track it
        async def stream_with_session_info():
            # Send session info as first event
            yield f"event: session\ndata: {json.dumps({'session_id': session.id})}\n\n"
            async for chunk in stream_chat_response(
                project_id=project_id,
                project_name=project.name,
                message=request.message,
                max_chunks=max_chunks,
                session_id=session.id,
                assistant_message_id=assistant_message_id,
            ):
                yield chunk

        return StreamingResponse(
            stream_with_session_info(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Get or create session
    session, is_new_session = get_or_create_active_session(
        project_id, db, request.session_id
    )

    # If new session, add introduction message
    if is_new_session:
        intro_content = generate_introduction_message(project)
        intro_message = ChatMessageModel(
            id=str(uuid4()),
            session_id=session.id,
            role=DBMessageRole.assistant,
            content=intro_content,
            sources=None
        )
        db.add(intro_message)

        # Generate session title from first user message
        session.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        db.commit()

    # Save user message
    user_message = ChatMessageModel(
        id=str(uuid4()),
        session_id=session.id,
        role=DBMessageRole.user,
        content=request.message
    )
    db.add(user_message)
    db.commit()

    # Get RAG service and generate response
    rag_service = get_rag_service()
    message_id = str(uuid4())

    try:
        rag_response = await rag_service.chat_with_context(
            query=request.message,
            project_id=project_id,
            project_name=project.name,
            max_chunks=max_chunks,
            include_sources=include_sources,
        )

        response_content = rag_response.content

        # Convert RAG sources to storable format
        sources_data = None
        sources = []
        if include_sources and rag_response.sources:
            sources_data = []
            for chunk in rag_response.sources:
                snippet = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                source_dict = {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "snippet": snippet,
                    "relevance_score": chunk.score or 0.0,
                }
                sources_data.append(source_dict)
                sources.append(ChatSource(**source_dict))

        prompt_tokens = rag_response.prompt_tokens
        completion_tokens = rag_response.completion_tokens

    except Exception as e:
        logger.warning(f"RAG service error, using fallback: {e}")
        response_content = f"""I apologize, but I'm currently unable to access the code analysis for this project.

This could be because:
- The project hasn't been fully analyzed yet
- The embedding service is not running
- The vector database is not available

Please ensure the project has been analyzed and try again.

Your question: "{request.message[:100]}..." """
        sources_data = None
        sources = []
        prompt_tokens = 0
        completion_tokens = 0

    # Save assistant message
    assistant_message = ChatMessageModel(
        id=message_id,
        session_id=session.id,
        role=DBMessageRole.assistant,
        content=response_content,
        sources=sources_data
    )
    db.add(assistant_message)

    # Update session timestamp
    session.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        session_id=session.id,
        message_id=message_id,
        response=ChatResponseContent(
            content=response_content,
            format="markdown",
            sources=sources,
            tokens_used=TokenUsage(prompt=prompt_tokens, completion=completion_tokens)
        ),
        created_at=datetime.utcnow()
    )


@router.post("/{project_id}/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    project_id: str,
    request: ChatSessionCreate = None,
    db: Session = Depends(get_db)
):
    """
    Create a new chat session for a project.

    Optionally accepts a custom title. The new session becomes active,
    and other sessions are deactivated.
    """
    project = get_project_or_404(project_id, db)

    # Deactivate other sessions for this project
    db.query(ChatSession).filter(
        ChatSession.project_id == project_id,
        ChatSession.is_active == True
    ).update({"is_active": False})

    # Create new session
    session = ChatSession(
        id=str(uuid4()),
        project_id=project_id,
        title=request.title if request else None,
        is_active=True
    )
    db.add(session)
    db.commit()

    # Add introduction message
    intro_content = generate_introduction_message(project)
    intro_message = ChatMessageModel(
        id=str(uuid4()),
        session_id=session.id,
        role=DBMessageRole.assistant,
        content=intro_content,
        sources=None
    )
    db.add(intro_message)
    db.commit()
    db.refresh(session)

    # Return session with messages
    messages = [
        ChatMessage(
            id=msg.id,
            role=MessageRole(msg.role.value),
            content=msg.content,
            sources=None,
            created_at=msg.created_at
        )
        for msg in session.messages
    ]

    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        messages=messages,
        created_at=session.created_at
    )


@router.get("/{project_id}/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(project_id: str, db: Session = Depends(get_db)):
    """List all chat sessions for a project."""
    project = get_project_or_404(project_id, db)

    sessions = db.query(ChatSession).filter(
        ChatSession.project_id == project_id
    ).order_by(ChatSession.updated_at.desc()).all()

    items = []
    for session in sessions:
        message_count = len(session.messages)
        last_message = session.messages[-1] if session.messages else None

        items.append(ChatSessionListItem(
            id=session.id,
            title=session.title or "Untitled conversation",
            message_count=message_count,
            created_at=session.created_at,
            last_message_at=last_message.created_at if last_message else session.created_at
        ))

    return ChatSessionListResponse(items=items)


@router.get("/{project_id}/chat/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(project_id: str, session_id: str, db: Session = Depends(get_db)):
    """Get a specific chat session with all messages."""
    project = get_project_or_404(project_id, db)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = [
        ChatMessage(
            id=msg.id,
            role=MessageRole(msg.role.value),
            content=msg.content,
            sources=[ChatSource(**src) for src in msg.sources] if msg.sources else None,
            created_at=msg.created_at
        )
        for msg in session.messages
    ]

    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        messages=messages,
        created_at=session.created_at
    )


@router.patch("/{project_id}/chat/sessions/{session_id}")
async def update_chat_session(
    project_id: str,
    session_id: str,
    request: ChatSessionUpdate,
    db: Session = Depends(get_db)
):
    """Update a chat session (title, active status)."""
    project = get_project_or_404(project_id, db)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.title is not None:
        session.title = request.title

    if request.is_active is not None:
        if request.is_active:
            # Deactivate other sessions first
            db.query(ChatSession).filter(
                ChatSession.project_id == project_id,
                ChatSession.is_active == True,
                ChatSession.id != session_id
            ).update({"is_active": False})
        session.is_active = request.is_active

    db.commit()

    return {"message": "Session updated", "session_id": session_id}


@router.delete("/{project_id}/chat/sessions/{session_id}")
async def delete_chat_session(project_id: str, session_id: str, db: Session = Depends(get_db)):
    """Delete a chat session and all its messages."""
    project = get_project_or_404(project_id, db)

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)  # Cascade deletes messages
    db.commit()

    return {"message": "Session deleted successfully", "session_id": session_id}
