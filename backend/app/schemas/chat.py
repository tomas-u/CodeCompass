"""Chat schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role."""
    user = "user"
    assistant = "assistant"


class ChatSource(BaseModel):
    """Chat source reference."""
    file_path: str
    start_line: int
    end_line: int
    snippet: str
    relevance_score: float


class ChatOptions(BaseModel):
    """Chat options."""
    include_sources: bool = True
    max_context_chunks: int = 5
    stream: bool = False


class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., max_length=10000)
    session_id: Optional[str] = None
    options: Optional[ChatOptions] = None


class TokenUsage(BaseModel):
    """Token usage."""
    prompt: int
    completion: int


class ChatResponseContent(BaseModel):
    """Chat response content."""
    content: str
    format: str = "markdown"
    sources: List[ChatSource] = []
    tokens_used: Optional[TokenUsage] = None


class ChatResponse(BaseModel):
    """Chat response."""
    session_id: str
    message_id: str
    response: ChatResponseContent
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Chat message."""
    id: str
    role: MessageRole
    content: str
    sources: Optional[List[ChatSource]] = None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    id: str
    title: Optional[str] = None
    messages: List[ChatMessage]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionListItem(BaseModel):
    """Chat session list item."""
    id: str
    title: Optional[str] = None
    message_count: int
    created_at: datetime
    last_message_at: datetime


class ChatSessionListResponse(BaseModel):
    """Chat session list response."""
    items: List[ChatSessionListItem]
