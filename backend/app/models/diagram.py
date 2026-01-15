"""Diagram database model."""

from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.schemas.diagram import DiagramType


class Diagram(Base):
    """Diagram model - stores generated Mermaid diagrams for a project."""

    __tablename__ = "diagrams"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Foreign key to project
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)

    # Diagram type
    type = Column(SQLEnum(DiagramType), nullable=False)

    # Diagram content
    title = Column(String, nullable=False)
    mermaid_code = Column(Text, nullable=False)

    # Metadata for interactivity (node positions, colors, file mappings)
    # Note: 'metadata' is reserved by SQLAlchemy, so we use 'diagram_metadata'
    diagram_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<Diagram(id={self.id}, type={self.type}, project_id={self.project_id})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "title": self.title,
            "mermaid_code": self.mermaid_code,
            "metadata": self.diagram_metadata,
            "created_at": self.created_at,
        }
