"""Unit tests for Vector service."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.vector_service import VectorService, COLLECTION_NAME
from app.schemas.code_chunk import ChunkData, ChunkType, ChunkWithContent


class TestVectorService:
    """Tests for VectorService."""

    @pytest.fixture
    def vector_service(self):
        """Create a VectorService instance."""
        with patch("app.services.vector_service.settings") as mock_settings:
            mock_settings.qdrant_host = "localhost"
            mock_settings.qdrant_port = 6333
            mock_settings.embedding_dimensions = 384
            service = VectorService()
        return service

    @pytest.fixture
    def sample_chunk(self):
        """Create a sample chunk for testing."""
        return ChunkData(
            id="chunk-1",
            project_id="proj-1",
            file_path="src/main.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=50,
            language="python",
            content='def main():\n    print("Hello")',
            content_hash="abc123",
        )

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding vector."""
        return [0.1] * 384

    def test_init_default_values(self):
        """Test initialization with default values."""
        with patch("app.services.vector_service.settings") as mock_settings:
            mock_settings.qdrant_host = "localhost"
            mock_settings.qdrant_port = 6333
            mock_settings.embedding_dimensions = 384

            service = VectorService()

            assert service.host == "localhost"
            assert service.port == 6333
            assert service.dimensions == 384

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        service = VectorService(
            host="custom-host",
            port=1234,
            dimensions=768,
        )

        assert service.host == "custom-host"
        assert service.port == 1234
        assert service.dimensions == 768

    def test_get_client_creates_client(self, vector_service):
        """Test that _get_client creates a client."""
        with patch("app.services.vector_service.QdrantClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            client = vector_service._get_client()

            MockClient.assert_called_once_with(
                host=vector_service.host,
                port=vector_service.port,
            )
            assert client == mock_client

    def test_get_client_reuses_client(self, vector_service):
        """Test that _get_client reuses existing client."""
        mock_client = MagicMock()
        vector_service._client = mock_client

        client = vector_service._get_client()

        assert client == mock_client

    @pytest.mark.asyncio
    async def test_health_check_success(self, vector_service):
        """Test health check when Qdrant is available."""
        mock_client = MagicMock()
        mock_client.get_collections.return_value = MagicMock()
        vector_service._client = mock_client

        result = await vector_service.health_check()

        assert result is True
        mock_client.get_collections.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, vector_service):
        """Test health check when Qdrant is unavailable."""
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Connection refused")
        vector_service._client = mock_client

        result = await vector_service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_ensure_collection_exists(self, vector_service):
        """Test ensure_collection when collection already exists."""
        mock_collection = MagicMock()
        mock_collection.name = COLLECTION_NAME

        mock_client = MagicMock()
        mock_collections_response = MagicMock()
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response
        vector_service._client = mock_client

        result = await vector_service.ensure_collection()

        assert result is True
        mock_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_collection_creates(self, vector_service):
        """Test ensure_collection creates collection when missing."""
        mock_client = MagicMock()
        mock_collections_response = MagicMock()
        mock_collections_response.collections = []
        mock_client.get_collections.return_value = mock_collections_response
        vector_service._client = mock_client

        result = await vector_service.ensure_collection()

        assert result is True
        mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_chunks(self, vector_service, sample_chunk, sample_embedding):
        """Test upserting chunks."""
        mock_client = MagicMock()
        vector_service._client = mock_client

        count = await vector_service.upsert_chunks(
            chunks=[sample_chunk],
            embeddings=[sample_embedding],
        )

        assert count == 1
        mock_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_chunks_empty(self, vector_service):
        """Test upserting empty list."""
        count = await vector_service.upsert_chunks([], [])
        assert count == 0

    @pytest.mark.asyncio
    async def test_upsert_chunks_mismatch(self, vector_service, sample_chunk, sample_embedding):
        """Test upserting with mismatched counts."""
        # Note: when embeddings is empty, early return triggers before mismatch check
        # So we need to provide both non-empty lists with different lengths
        with pytest.raises(ValueError, match="mismatch"):
            await vector_service.upsert_chunks(
                chunks=[sample_chunk, sample_chunk],  # 2 chunks
                embeddings=[sample_embedding],  # 1 embedding - actual mismatch
            )

    @pytest.mark.asyncio
    async def test_upsert_chunks_batching(self, vector_service, sample_embedding):
        """Test that large upserts are batched."""
        # Create 150 chunks (should be split into 2 batches of 100)
        chunks = [
            ChunkData(
                id=f"chunk-{i}",
                project_id="proj-1",
                file_path=f"file{i}.py",
                chunk_type=ChunkType.file,
                start_line=1,
                end_line=10,
                content=f"content {i}",
                content_hash=f"hash{i}",
            )
            for i in range(150)
        ]
        embeddings = [sample_embedding] * 150

        mock_client = MagicMock()
        vector_service._client = mock_client

        count = await vector_service.upsert_chunks(chunks, embeddings)

        assert count == 150
        assert mock_client.upsert.call_count == 2  # Two batches

    @pytest.mark.asyncio
    async def test_search(self, vector_service):
        """Test searching for chunks."""
        mock_result = MagicMock()
        mock_result.id = "chunk-1"
        mock_result.score = 0.9
        mock_result.payload = {
            "project_id": "proj-1",
            "file_path": "main.py",
            "chunk_type": "file",
            "start_line": 1,
            "end_line": 10,
            "language": "python",
            "content": "def main(): pass",
        }

        mock_response = MagicMock()
        mock_response.points = [mock_result]

        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_response
        vector_service._client = mock_client

        results = await vector_service.search(
            query_vector=[0.1] * 384,
            project_id="proj-1",
            limit=10,
        )

        assert len(results) == 1
        assert results[0].id == "chunk-1"
        assert results[0].score == 0.9
        assert results[0].file_path == "main.py"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_service):
        """Test search with additional filters."""
        mock_response = MagicMock()
        mock_response.points = []

        mock_client = MagicMock()
        mock_client.query_points.return_value = mock_response
        vector_service._client = mock_client

        await vector_service.search(
            query_vector=[0.1] * 384,
            project_id="proj-1",
            limit=5,
            filters={"languages": ["python", "javascript"]},
        )

        mock_client.query_points.assert_called_once()
        # Verify filter was passed
        call_kwargs = mock_client.query_points.call_args.kwargs
        assert call_kwargs["query_filter"] is not None

    @pytest.mark.asyncio
    async def test_search_error_returns_empty(self, vector_service):
        """Test that search errors return empty list."""
        mock_client = MagicMock()
        mock_client.query_points.side_effect = Exception("Search failed")
        vector_service._client = mock_client

        results = await vector_service.search(
            query_vector=[0.1] * 384,
            project_id="proj-1",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_delete_project_chunks(self, vector_service):
        """Test deleting chunks for a project."""
        mock_count_result = MagicMock()
        mock_count_result.count = 10

        mock_client = MagicMock()
        mock_client.count.return_value = mock_count_result
        vector_service._client = mock_client

        count = await vector_service.delete_project_chunks("proj-1")

        assert count == 10
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_collection_info(self, vector_service):
        """Test getting collection information."""
        mock_info = MagicMock()
        mock_info.points_count = 1000
        mock_info.vectors_count = 1000
        mock_info.status = MagicMock(value="green")

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_info
        vector_service._client = mock_client

        info = await vector_service.get_collection_info()

        assert info["name"] == COLLECTION_NAME
        assert info["points_count"] == 1000
        assert info["status"] == "green"

    @pytest.mark.asyncio
    async def test_get_collection_info_error(self, vector_service):
        """Test get_collection_info handles errors."""
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Not found")
        vector_service._client = mock_client

        info = await vector_service.get_collection_info()

        assert info is None
