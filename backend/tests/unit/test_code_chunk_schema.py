"""Unit tests for code chunk schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.code_chunk import (
    ChunkType,
    ChunkCreate,
    ChunkData,
    ChunkResponse,
    ChunkWithContent,
    ChunkSearchResult,
)


class TestChunkType:
    """Tests for ChunkType enum."""

    def test_chunk_type_values(self):
        """Test ChunkType enum values."""
        assert ChunkType.file.value == "file"
        assert ChunkType.segment.value == "segment"

    def test_chunk_type_from_string(self):
        """Test creating ChunkType from string."""
        assert ChunkType("file") == ChunkType.file
        assert ChunkType("segment") == ChunkType.segment


class TestChunkCreate:
    """Tests for ChunkCreate schema."""

    def test_chunk_create_valid(self):
        """Test creating a valid ChunkCreate."""
        chunk = ChunkCreate(
            id="chunk-1",
            project_id="proj-1",
            file_path="src/main.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=50,
            language="python",
            content="def main(): pass",
            content_hash="abc123",
        )

        assert chunk.id == "chunk-1"
        assert chunk.project_id == "proj-1"
        assert chunk.file_path == "src/main.py"
        assert chunk.chunk_type == ChunkType.file
        assert chunk.start_line == 1
        assert chunk.end_line == 50
        assert chunk.language == "python"
        assert chunk.content == "def main(): pass"
        assert chunk.content_hash == "abc123"

    def test_chunk_create_optional_language(self):
        """Test ChunkCreate with optional language."""
        chunk = ChunkCreate(
            id="1",
            project_id="proj",
            file_path="file.txt",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="text",
            content_hash="hash",
        )

        assert chunk.language is None

    def test_chunk_create_missing_required(self):
        """Test ChunkCreate with missing required fields."""
        with pytest.raises(ValidationError):
            ChunkCreate(
                id="1",
                # missing project_id
                file_path="file.py",
                chunk_type=ChunkType.file,
                start_line=1,
                end_line=10,
                content="code",
                content_hash="hash",
            )


class TestChunkData:
    """Tests for ChunkData schema."""

    def test_chunk_data_valid(self):
        """Test creating a valid ChunkData."""
        chunk = ChunkData(
            id="chunk-1",
            project_id="proj-1",
            file_path="main.py",
            chunk_type=ChunkType.segment,
            start_line=10,
            end_line=30,
            language="python",
            content="class MyClass: pass",
            content_hash="def456",
        )

        assert chunk.chunk_type == ChunkType.segment
        assert chunk.start_line == 10
        assert chunk.end_line == 30

    def test_chunk_data_serialization(self):
        """Test ChunkData serialization."""
        chunk = ChunkData(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=5,
            content="code",
            content_hash="hash",
        )

        data = chunk.model_dump()
        assert data["chunk_type"] == ChunkType.file


class TestChunkResponse:
    """Tests for ChunkResponse schema."""

    def test_chunk_response_valid(self):
        """Test creating a valid ChunkResponse."""
        now = datetime.utcnow()
        chunk = ChunkResponse(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content_hash="hash",
            created_at=now,
        )

        assert chunk.created_at == now
        assert chunk.language is None  # Optional

    def test_chunk_response_with_language(self):
        """Test ChunkResponse with language."""
        chunk = ChunkResponse(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            language="python",
            content_hash="hash",
            created_at=datetime.utcnow(),
        )

        assert chunk.language == "python"


class TestChunkWithContent:
    """Tests for ChunkWithContent schema."""

    def test_chunk_with_content_valid(self):
        """Test creating a valid ChunkWithContent."""
        chunk = ChunkWithContent(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="def func(): pass",
            score=0.85,
        )

        assert chunk.content == "def func(): pass"
        assert chunk.score == 0.85

    def test_chunk_with_content_optional_score(self):
        """Test ChunkWithContent with optional score."""
        chunk = ChunkWithContent(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="code",
        )

        assert chunk.score is None

    def test_chunk_with_content_string_chunk_type(self):
        """Test ChunkWithContent accepts string chunk type."""
        chunk = ChunkWithContent(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type="file",  # String instead of enum
            start_line=1,
            end_line=10,
            content="code",
        )

        assert chunk.chunk_type == ChunkType.file


class TestChunkSearchResult:
    """Tests for ChunkSearchResult schema."""

    def test_chunk_search_result_valid(self):
        """Test creating a valid ChunkSearchResult."""
        chunk = ChunkWithContent(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="code",
        )

        result = ChunkSearchResult(
            chunk=chunk,
            score=0.92,
        )

        assert result.chunk.id == "1"
        assert result.score == 0.92

    def test_chunk_search_result_score_range(self):
        """Test ChunkSearchResult accepts various score values."""
        chunk = ChunkWithContent(
            id="1",
            project_id="proj",
            file_path="file.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="code",
        )

        # Score can be any float
        result = ChunkSearchResult(chunk=chunk, score=0.0)
        assert result.score == 0.0

        result = ChunkSearchResult(chunk=chunk, score=1.0)
        assert result.score == 1.0

        result = ChunkSearchResult(chunk=chunk, score=0.5)
        assert result.score == 0.5
