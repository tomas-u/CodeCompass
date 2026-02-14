"""Unit tests for RAG service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag_service import RAGService, RAGContext, RAGResponse
from app.services.llm.base import ChatMessage, GenerationResult
from app.schemas.code_chunk import ChunkWithContent, ChunkType


class TestRAGContext:
    """Tests for RAGContext dataclass."""

    def test_rag_context_creation(self):
        """Test creating a RAGContext."""
        chunks = [
            ChunkWithContent(
                id="1",
                project_id="proj1",
                file_path="test.py",
                chunk_type=ChunkType.file,
                start_line=1,
                end_line=10,
                content="test content",
                score=0.9,
            )
        ]
        context = RAGContext(
            chunks=chunks,
            query="test query",
            total_tokens_estimate=100,
        )
        assert len(context.chunks) == 1
        assert context.query == "test query"
        assert context.total_tokens_estimate == 100


class TestRAGResponse:
    """Tests for RAGResponse dataclass."""

    def test_rag_response_creation(self):
        """Test creating a RAGResponse."""
        response = RAGResponse(
            content="Generated response",
            sources=[],
            prompt_tokens=50,
            completion_tokens=100,
        )
        assert response.content == "Generated response"
        assert response.sources == []
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 100


class TestRAGService:
    """Tests for RAGService."""

    @pytest.fixture
    def rag_service(self):
        """Create a RAGService instance with mocked dependencies."""
        service = RAGService()
        return service

    @pytest.fixture
    def mock_chunk(self):
        """Create a mock chunk for testing."""
        return ChunkWithContent(
            id="chunk-1",
            project_id="proj-1",
            file_path="src/main.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=50,
            language="python",
            content='def main():\n    print("Hello")',
            score=0.85,
        )

    def test_build_rag_prompt_with_chunks(self, rag_service, mock_chunk):
        """Test building RAG prompt with context chunks."""
        prompt = rag_service.build_rag_prompt(
            query="How does main work?",
            project_name="TestProject",
            chunks=[mock_chunk],
        )

        assert "TestProject" in prompt
        assert "How does main work?" in prompt
        assert "src/main.py" in prompt
        assert "def main():" in prompt
        assert "lines 1-50" in prompt

    def test_build_rag_prompt_empty_chunks(self, rag_service):
        """Test building RAG prompt without chunks."""
        prompt = rag_service.build_rag_prompt(
            query="What is this?",
            project_name="TestProject",
            chunks=[],
        )

        assert "TestProject" in prompt
        assert "What is this?" in prompt
        assert "no relevant code context was found" in prompt

    def test_build_rag_prompt_multiple_chunks(self, rag_service):
        """Test building RAG prompt with multiple chunks."""
        chunks = [
            ChunkWithContent(
                id=f"chunk-{i}",
                project_id="proj-1",
                file_path=f"file{i}.py",
                chunk_type=ChunkType.file,
                start_line=1,
                end_line=10,
                language="python",
                content=f"# File {i} content",
                score=0.9 - i * 0.1,
            )
            for i in range(3)
        ]

        prompt = rag_service.build_rag_prompt(
            query="Explain",
            project_name="Multi",
            chunks=chunks,
        )

        assert "file0.py" in prompt
        assert "file1.py" in prompt
        assert "file2.py" in prompt

    @pytest.mark.asyncio
    async def test_retrieve_context(self, rag_service, mock_chunk):
        """Test retrieving context from vector store."""
        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.embed_single = AsyncMock(return_value=[0.1] * 384)

        mock_vector_service = AsyncMock()
        mock_vector_service.search = AsyncMock(return_value=[mock_chunk])

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        context = await rag_service.retrieve_context(
            query="test query",
            project_id="proj-1",
            max_chunks=5,
            min_score=0.1,
        )

        assert len(context.chunks) == 1
        assert context.chunks[0].file_path == "src/main.py"
        assert context.query == "test query"

    @pytest.mark.asyncio
    async def test_retrieve_context_filters_low_scores(self, rag_service):
        """Test that low-score chunks are filtered out."""
        low_score_chunk = ChunkWithContent(
            id="low",
            project_id="proj-1",
            file_path="low.py",
            chunk_type=ChunkType.file,
            start_line=1,
            end_line=10,
            content="low score",
            score=0.01,  # Below default threshold
        )

        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.embed_single = AsyncMock(return_value=[0.1] * 384)

        mock_vector_service = AsyncMock()
        mock_vector_service.search = AsyncMock(return_value=[low_score_chunk])

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        context = await rag_service.retrieve_context(
            query="test",
            project_id="proj-1",
            min_score=0.05,
        )

        assert len(context.chunks) == 0

    @pytest.mark.asyncio
    async def test_chat_with_context(self, rag_service, mock_chunk):
        """Test full RAG chat pipeline."""
        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.health_check = AsyncMock(return_value=True)
        mock_embedding_provider.embed_single = AsyncMock(return_value=[0.1] * 384)

        mock_vector_service = AsyncMock()
        mock_vector_service.health_check = AsyncMock(return_value=True)
        mock_vector_service.search = AsyncMock(return_value=[mock_chunk])

        mock_llm_provider = AsyncMock()
        mock_llm_provider.health_check = AsyncMock(return_value=True)
        mock_llm_provider.chat = AsyncMock(
            return_value=GenerationResult(
                content="The main function prints Hello",
                model="test-model",
                prompt_tokens=100,
                completion_tokens=50,
            )
        )

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        with patch("app.services.rag_service.get_llm_provider", return_value=mock_llm_provider):
            response = await rag_service.chat_with_context(
                query="What does main do?",
                project_id="proj-1",
                project_name="TestProject",
            )

        assert "main function prints Hello" in response.content
        assert len(response.sources) == 1
        assert response.prompt_tokens == 100
        assert response.completion_tokens == 50

    @pytest.mark.asyncio
    async def test_chat_with_context_llm_unavailable(self, rag_service, mock_chunk):
        """Test RAG chat when LLM is unavailable."""
        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.health_check = AsyncMock(return_value=True)
        mock_embedding_provider.embed_single = AsyncMock(return_value=[0.1] * 384)

        mock_vector_service = AsyncMock()
        mock_vector_service.health_check = AsyncMock(return_value=True)
        mock_vector_service.search = AsyncMock(return_value=[mock_chunk])

        mock_llm_provider = AsyncMock()
        mock_llm_provider.health_check = AsyncMock(return_value=False)

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        with patch("app.services.rag_service.get_llm_provider", return_value=mock_llm_provider):
            response = await rag_service.chat_with_context(
                query="test",
                project_id="proj-1",
                project_name="Test",
            )

        assert "unavailable" in response.content.lower()

    @pytest.mark.asyncio
    async def test_chat_with_context_stream(self, rag_service, mock_chunk):
        """Test streaming RAG chat."""
        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.health_check = AsyncMock(return_value=True)
        mock_embedding_provider.embed_single = AsyncMock(return_value=[0.1] * 384)

        mock_vector_service = AsyncMock()
        mock_vector_service.health_check = AsyncMock(return_value=True)
        mock_vector_service.search = AsyncMock(return_value=[mock_chunk])

        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " world"
            yield "!"

        mock_llm_provider = MagicMock()
        mock_llm_provider.health_check = AsyncMock(return_value=True)
        mock_llm_provider.chat_stream = mock_stream

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        with patch("app.services.rag_service.get_llm_provider", return_value=mock_llm_provider):
            events = []
            async for event in rag_service.chat_with_context_stream(
                query="test",
                project_id="proj-1",
                project_name="Test",
            ):
                events.append(event)

        # Should have: sources, tokens, done
        event_types = [e["type"] for e in events]
        assert "sources" in event_types
        assert "token" in event_types
        assert "done" in event_types

        # Check sources event
        sources_event = next(e for e in events if e["type"] == "sources")
        assert len(sources_event["sources"]) == 1

        # Check tokens
        token_events = [e for e in events if e["type"] == "token"]
        tokens = [e["content"] for e in token_events]
        assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_chat_with_context_stream_llm_error(self, rag_service):
        """Test streaming handles LLM errors."""
        mock_embedding_provider = AsyncMock()
        mock_embedding_provider.health_check = AsyncMock(return_value=True)

        mock_vector_service = AsyncMock()
        mock_vector_service.health_check = AsyncMock(return_value=True)

        mock_llm_provider = AsyncMock()
        mock_llm_provider.health_check = AsyncMock(return_value=False)

        rag_service._embedding_provider = mock_embedding_provider
        rag_service._vector_service = mock_vector_service

        with patch("app.services.rag_service.get_llm_provider", return_value=mock_llm_provider):
            events = []
            async for event in rag_service.chat_with_context_stream(
                query="test",
                project_id="proj-1",
                project_name="Test",
            ):
                events.append(event)

        # Should have error event
        assert any(e["type"] == "error" for e in events)
