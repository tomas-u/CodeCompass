"""Project database model."""

from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base
from app.schemas.project import SourceType, ProjectStatus
import enum


class Project(Base):
    """Project model - represents a code repository being analyzed."""

    __tablename__ = "projects"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Basic info
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)

    # Source information
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source = Column(String, nullable=False)  # Git URL or local path
    branch = Column(String, nullable=False, default="main")
    local_path = Column(String, nullable=True)  # Where repo is cloned

    # Status
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.pending)

    # Settings and stats (stored as JSON)
    settings = Column(JSON, nullable=True)
    stats = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), server_default=func.now())
    last_analyzed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_type": self.source_type,
            "source": self.source,
            "branch": self.branch,
            "local_path": self.local_path,
            "status": self.status,
            "settings": self.settings,
            "stats": self.stats,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_analyzed_at": self.last_analyzed_at,
        }
