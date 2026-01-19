"""Unit tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.llm.base import (
    LLMProvider,
    EmbeddingProvider,
    GenerationResult,
    ChatMessage,
    ModelInfo,
)
from app.services.llm.ollama_provider import OllamaProvider


class TestChatMessage:
    """Tests for ChatMessage dataclass."""

    def test_chat_message_creation(self):
        """Test creating a ChatMessage."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_chat_message_roles(self):
        """Test different roles."""
        user_msg = ChatMessage(role="user", content="Hi")
        assistant_msg = ChatMessage(role="assistant", content="Hello!")
        system_msg = ChatMessage(role="system", content="You are helpful.")

        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_generation_result_creation(self):
        """Test creating a GenerationResult."""
        result = GenerationResult(
            content="Generated text",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        assert result.content == "Generated text"
        assert result.model == "test-model"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 20
        assert result.total_tokens == 30

    def test_generation_result_optional_tokens(self):
        """Test GenerationResult with optional token counts."""
        result = GenerationResult(
            content="Text",
            model="model",
        )
        assert result.prompt_tokens is None
        assert result.completion_tokens is None
        assert result.total_tokens is None


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating a ModelInfo."""
        info = ModelInfo(
            name="llama3.2:3b",
            size="2.0 GB",
            modified_at="2024-01-01T00:00:00Z",
            digest="abc123",
            details={"family": "llama"},
        )
        assert info.name == "llama3.2:3b"
        assert info.size == "2.0 GB"
        assert info.details == {"family": "llama"}

    def test_model_info_minimal(self):
        """Test ModelInfo with only required fields."""
        info = ModelInfo(name="test-model")
        assert info.name == "test-model"
        assert info.size is None
        assert info.modified_at is None


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    @pytest.fixture
    def provider(self):
        """Create an OllamaProvider instance."""
        return OllamaProvider(
            base_url="http://localhost:11434",
            model="test-model",
            timeout=30.0,
        )

    def test_init(self, provider):
        """Test provider initialization."""
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "test-model"
        assert provider.timeout == 30.0

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url."""
        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider.base_url == "http://localhost:11434"

    def test_get_model_name(self, provider):
        """Test getting model name."""
        assert provider.get_model_name() == "test-model"

    def test_set_model(self, provider):
        """Test setting model."""
        provider.set_model("new-model")
        assert provider.model == "new-model"
        assert provider.get_model_name() == "new-model"

    @pytest.mark.asyncio
    async def test_generate(self, provider):
        """Test generate method."""
        mock_response = {
            "response": "Generated text",
            "model": "test-model",
            "prompt_eval_count": 10,
            "eval_count": 20,
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_get_client.return_value = mock_client

            result = await provider.generate("Test prompt")

            assert result.content == "Generated text"
            assert result.model == "test-model"
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 20
            assert result.total_tokens == 30

    @pytest.mark.asyncio
    async def test_chat(self, provider):
        """Test chat method."""
        mock_response = {
            "message": {"content": "Hello!"},
            "model": "test-model",
            "prompt_eval_count": 5,
            "eval_count": 10,
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hi")]
            result = await provider.chat(messages)

            assert result.content == "Hello!"
            assert result.model == "test-model"

    @pytest.mark.asyncio
    async def test_chat_stream(self, provider):
        """Test chat_stream method."""
        # Simulate streaming response lines
        stream_lines = [
            '{"message": {"content": "Hello"}}',
            '{"message": {"content": " world"}}',
            '{"message": {"content": "!"}}',
        ]

        async def mock_aiter_lines():
            for line in stream_lines:
                yield line

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = mock_aiter_lines
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            mock_client.stream = MagicMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            MockClient.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hi")]
            tokens = []
            async for token in provider.chat_stream(messages):
                tokens.append(token)

            assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test health check when Ollama is available."""
        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """Test health check when Ollama is unavailable."""
        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=Exception("Connection refused"))
            mock_get_client.return_value = mock_client

            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """Test listing available models."""
        mock_response = {
            "models": [
                {
                    "name": "llama3.2:3b",
                    "size": 2000000000,
                    "modified_at": "2024-01-01T00:00:00Z",
                    "digest": "abc123",
                    "details": {"family": "llama"},
                },
                {
                    "name": "phi3.5",
                    "size": 4000000000,
                    "modified_at": "2024-01-02T00:00:00Z",
                    "digest": "def456",
                },
            ]
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_get_client.return_value = mock_client

            models = await provider.list_models()

            assert len(models) == 2
            assert models[0].name == "llama3.2:3b"
            assert models[1].name == "phi3.5"

    @pytest.mark.asyncio
    async def test_list_models_empty(self, provider):
        """Test listing models when none available."""
        mock_response = {"models": []}

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_get_client.return_value = mock_client

            models = await provider.list_models()
            assert models == []

    def test_format_size(self):
        """Test size formatting."""
        assert OllamaProvider._format_size(None) is None
        assert OllamaProvider._format_size(500) == "500.0 B"
        assert OllamaProvider._format_size(1024) == "1.0 KB"
        assert OllamaProvider._format_size(1024 * 1024) == "1.0 MB"
        assert OllamaProvider._format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert OllamaProvider._format_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"

    @pytest.mark.asyncio
    async def test_close(self, provider):
        """Test closing the provider."""
        # Create a client first
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.is_closed = False
            mock_client.aclose = AsyncMock()
            provider._client = mock_client

            await provider.close()

            mock_client.aclose.assert_called_once()
            assert provider._client is None
