"""Unit tests for Chunking service."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import tempfile
import os
from pathlib import Path

from app.services.chunking_service import (
    ChunkingService,
    SMALL_FILE_THRESHOLD,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from app.schemas.code_chunk import ChunkType


class TestChunkingService:
    """Tests for ChunkingService."""

    @pytest.fixture
    def chunking_service(self):
        """Create a ChunkingService instance."""
        return ChunkingService(max_file_size_mb=10)

    def test_init(self, chunking_service):
        """Test initialization."""
        assert chunking_service.max_file_size_bytes == 10 * 1024 * 1024

    def test_chunk_small_file(self, chunking_service):
        """Test chunking a small file (< threshold)."""
        # Create content smaller than SMALL_FILE_THRESHOLD
        content = "\n".join([f"line {i}" for i in range(50)])

        chunks = chunking_service.chunk_file(
            file_path="small.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.file
        assert chunks[0].file_path == "small.py"
        assert chunks[0].start_line == 1
        assert chunks[0].end_line == 50
        assert chunks[0].language == "python"
        assert chunks[0].project_id == "proj-1"

    def test_chunk_large_file(self, chunking_service):
        """Test chunking a large file (> threshold)."""
        # Create content larger than SMALL_FILE_THRESHOLD
        content = "\n".join([f"line {i}" for i in range(300)])

        chunks = chunking_service.chunk_file(
            file_path="large.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        # Should have multiple chunks
        assert len(chunks) > 1

        # All chunks should be segments
        for chunk in chunks:
            assert chunk.chunk_type == ChunkType.segment

        # First chunk should start at line 1
        assert chunks[0].start_line == 1

        # Chunks should have overlap
        if len(chunks) >= 2:
            # Second chunk should start before first chunk ends
            assert chunks[1].start_line < chunks[0].end_line

    def test_chunk_preserves_content(self, chunking_service):
        """Test that chunking preserves content."""
        content = "line1\nline2\nline3"

        chunks = chunking_service.chunk_file(
            file_path="test.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        assert chunks[0].content == content

    def test_chunk_generates_unique_ids(self, chunking_service):
        """Test that each chunk gets a unique ID."""
        content = "\n".join([f"line {i}" for i in range(300)])

        chunks = chunking_service.chunk_file(
            file_path="test.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        ids = [chunk.id for chunk in chunks]
        assert len(ids) == len(set(ids))  # All unique

    def test_chunk_generates_content_hash(self, chunking_service):
        """Test that chunks have content hashes."""
        content = "test content"

        chunks = chunking_service.chunk_file(
            file_path="test.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        assert chunks[0].content_hash is not None
        assert len(chunks[0].content_hash) == 16  # 16 hex chars

    def test_chunk_same_content_same_hash(self, chunking_service):
        """Test that same content produces same hash."""
        content = "identical content"

        chunks1 = chunking_service.chunk_file(
            file_path="file1.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        chunks2 = chunking_service.chunk_file(
            file_path="file2.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        assert chunks1[0].content_hash == chunks2[0].content_hash

    def test_chunk_handles_empty_content(self, chunking_service):
        """Test chunking empty content."""
        chunks = chunking_service.chunk_file(
            file_path="empty.py",
            content="",
            language="python",
            project_id="proj-1",
        )

        assert len(chunks) == 1
        assert chunks[0].content == ""

    def test_chunk_handles_no_language(self, chunking_service):
        """Test chunking without language."""
        chunks = chunking_service.chunk_file(
            file_path="test.txt",
            content="some text",
            language=None,
            project_id="proj-1",
        )

        assert chunks[0].language is None

    def test_chunk_boundary_at_threshold(self, chunking_service):
        """Test file exactly at threshold."""
        content = "\n".join([f"line {i}" for i in range(SMALL_FILE_THRESHOLD - 1)])

        chunks = chunking_service.chunk_file(
            file_path="boundary.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        # Should be treated as small file (single chunk)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == ChunkType.file

    def test_chunk_just_over_threshold(self, chunking_service):
        """Test file just over threshold."""
        content = "\n".join([f"line {i}" for i in range(SMALL_FILE_THRESHOLD + 10)])

        chunks = chunking_service.chunk_file(
            file_path="over.py",
            content=content,
            language="python",
            project_id="proj-1",
        )

        # Should be split into segments
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.chunk_type == ChunkType.segment


class TestChunkingServiceCollectFiles:
    """Tests for collect_files method."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some Python files
            Path(tmpdir, "main.py").write_text("def main(): pass")
            Path(tmpdir, "utils.py").write_text("def util(): pass")

            # Create a subdirectory
            subdir = Path(tmpdir, "src")
            subdir.mkdir()
            Path(subdir, "app.py").write_text("class App: pass")

            # Create a .gitignore
            Path(tmpdir, ".gitignore").write_text("*.pyc\n__pycache__/\n")

            # Create an ignored file
            Path(tmpdir, "ignored.pyc").write_text("compiled")

            yield tmpdir

    def test_collect_files_finds_python_files(self, temp_repo):
        """Test that collect_files finds Python files."""
        service = ChunkingService()
        files = list(service.collect_files(temp_repo))

        paths = [f[0] for f in files]
        assert "main.py" in paths
        assert "utils.py" in paths
        assert "src/app.py" in paths or "src\\app.py" in paths

    def test_collect_files_returns_content(self, temp_repo):
        """Test that collect_files returns file content."""
        service = ChunkingService()
        files = list(service.collect_files(temp_repo))

        # Find main.py
        main_file = next((f for f in files if f[0] == "main.py"), None)
        assert main_file is not None
        assert main_file[1] == "def main(): pass"
        assert main_file[2] == "Python"  # LanguageDetector returns capitalized names

    def test_collect_files_ignores_gitignore_patterns(self, temp_repo):
        """Test that .gitignore patterns are respected."""
        service = ChunkingService()
        files = list(service.collect_files(temp_repo))

        paths = [f[0] for f in files]
        assert "ignored.pyc" not in paths

    def test_collect_files_skips_large_files(self, temp_repo):
        """Test that large files are skipped."""
        # Create a large file
        large_content = "x" * (1024 * 1024 * 2)  # 2MB
        Path(temp_repo, "large.py").write_text(large_content)

        service = ChunkingService(max_file_size_mb=1)  # 1MB limit
        files = list(service.collect_files(temp_repo))

        paths = [f[0] for f in files]
        assert "large.py" not in paths

    def test_collect_files_skips_empty_files(self, temp_repo):
        """Test that empty files are skipped."""
        Path(temp_repo, "empty.py").write_text("")

        service = ChunkingService()
        files = list(service.collect_files(temp_repo))

        paths = [f[0] for f in files]
        assert "empty.py" not in paths

    def test_collect_files_detects_language(self, temp_repo):
        """Test that language is detected for files."""
        Path(temp_repo, "script.js").write_text("function test() {}")

        service = ChunkingService()
        files = list(service.collect_files(temp_repo))

        js_file = next((f for f in files if f[0] == "script.js"), None)
        assert js_file is not None
        assert js_file[2] == "JavaScript"  # LanguageDetector returns capitalized names


class TestChunkingServiceChunkProject:
    """Tests for chunk_project method."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        mock = MagicMock()
        mock.query.return_value.filter.return_value.delete.return_value = None
        mock.commit = MagicMock()
        mock.add = MagicMock()
        mock.rollback = MagicMock()
        return mock

    @pytest.fixture
    def mock_embedding_provider(self):
        """Create a mock embedding provider."""
        mock = AsyncMock()
        mock.embed = AsyncMock(return_value=[[0.1] * 384])
        return mock

    @pytest.fixture
    def mock_vector_service(self):
        """Create a mock vector service."""
        mock = AsyncMock()
        mock.ensure_collection = AsyncMock(return_value=True)
        mock.delete_project_chunks = AsyncMock(return_value=0)
        mock.upsert_chunks = AsyncMock(return_value=1)
        return mock

    @pytest.mark.asyncio
    async def test_chunk_project(
        self, mock_db, mock_embedding_provider, mock_vector_service
    ):
        """Test chunking a project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "main.py").write_text("def main(): pass")

            service = ChunkingService()
            count = await service.chunk_project(
                project_id="proj-1",
                repo_path=tmpdir,
                db=mock_db,
                embedding_provider=mock_embedding_provider,
                vector_service=mock_vector_service,
            )

            assert count >= 1
            mock_vector_service.ensure_collection.assert_called_once()
            mock_vector_service.delete_project_chunks.assert_called_once_with("proj-1")
            mock_embedding_provider.embed.assert_called()
            mock_vector_service.upsert_chunks.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_chunk_project_empty_repo(
        self, mock_db, mock_embedding_provider, mock_vector_service
    ):
        """Test chunking an empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = ChunkingService()
            count = await service.chunk_project(
                project_id="proj-1",
                repo_path=tmpdir,
                db=mock_db,
                embedding_provider=mock_embedding_provider,
                vector_service=mock_vector_service,
            )

            assert count == 0

    @pytest.mark.asyncio
    async def test_chunk_project_handles_embedding_error(
        self, mock_db, mock_embedding_provider, mock_vector_service
    ):
        """Test that embedding errors are handled."""
        mock_embedding_provider.embed = AsyncMock(side_effect=Exception("API error"))

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "main.py").write_text("def main(): pass")

            service = ChunkingService()

            with pytest.raises(Exception, match="API error"):
                await service.chunk_project(
                    project_id="proj-1",
                    repo_path=tmpdir,
                    db=mock_db,
                    embedding_provider=mock_embedding_provider,
                    vector_service=mock_vector_service,
                )

            mock_db.rollback.assert_called()
