"""Code chunk database model for tracking indexed chunks."""

import enum

from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.sql import func

from app.database import Base


class ChunkType(str, enum.Enum):
    """Type of code chunk."""
    file = "file"      # Whole file as single chunk
    segment = "segment"  # Part of a file (line-based split)


class CodeChunk(Base):
    """
    CodeChunk model - tracks metadata for code chunks stored in Qdrant.

    The actual embeddings and content are stored in Qdrant,
    this table provides fast lookups and project-level queries.
    """

    __tablename__ = "code_chunks"

    # Primary key (matches Qdrant point ID)
    id = Column(String, primary_key=True, index=True)

    # Foreign key to project
    project_id = Column(String, nullable=False, index=True)

    # File information
    file_path = Column(String, nullable=False, index=True)
    language = Column(String, nullable=True)

    # Chunk information
    chunk_type = Column(SQLEnum(ChunkType), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)

    # Content hash for detecting changes
    content_hash = Column(String, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    def __repr__(self):
        return f"<CodeChunk(id={self.id}, project_id={self.project_id}, file_path={self.file_path})>"
