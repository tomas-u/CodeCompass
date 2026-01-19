"""Report database model."""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class Report(Base):
    """Report model - stores generated analysis reports."""

    __tablename__ = "reports"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Foreign key to project
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)

    # Report type: summary, architecture, dependencies, developer
    type = Column(String, nullable=False, index=True)

    # Report title
    title = Column(String, nullable=False)

    # Report content as markdown
    content = Column(Text, nullable=False)

    # Structured sections (JSON array of {id, title, content})
    sections = Column(JSON, nullable=True)

    # Metadata (languages, frameworks, patterns, etc.)
    report_metadata = Column(JSON, nullable=True)

    # Generation info
    model_used = Column(String, nullable=True)  # LLM model used
    generation_time_ms = Column(String, nullable=True)  # Time taken to generate

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Report(id={self.id}, project_id={self.project_id}, type={self.type})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "sections": self.sections,
            "report_metadata": self.report_metadata,
            "model_used": self.model_used,
            "generation_time_ms": self.generation_time_ms,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
