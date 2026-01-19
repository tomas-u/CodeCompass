"""Chat database models for persistent conversation history."""

from sqlalchemy import Column, String, DateTime, JSON, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MessageRole(str, enum.Enum):
    """Role of the message sender."""
    user = "user"
    assistant = "assistant"
    system = "system"


class ChatSession(Base):
    """
    Chat session model - represents a conversation thread for a project.

    Each project can have multiple chat sessions, allowing users to
    organize different topics or start fresh conversations while
    preserving history.
    """

    __tablename__ = "chat_sessions"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Foreign key to project
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)

    # Session metadata
    title = Column(String, nullable=True)  # Auto-generated from first message or user-set
    is_active = Column(Boolean, nullable=False, default=True)  # Current active session

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, project_id={self.project_id}, title={self.title})>"

    def to_dict(self, include_messages: bool = False):
        """Convert model to dictionary for API responses."""
        result = {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        return result


class ChatMessage(Base):
    """
    Chat message model - represents a single message in a conversation.

    Messages can be from the user, assistant, or system (for context/intro).
    Assistant messages include source citations from RAG retrieval.
    """

    __tablename__ = "chat_messages"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Foreign key to session
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)

    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # Source citations (for assistant messages from RAG)
    # Format: [{"file_path": str, "start_line": int, "end_line": int, "snippet": str, "relevance_score": float}]
    sources = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, role={self.role}, content={content_preview})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at,
        }
