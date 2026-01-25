"""Unit tests for the OpenRouter LLM provider."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import httpx

from app.services.llm.openrouter_provider import (
    OpenRouterProvider,
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterModelInfo,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    APP_REFERER,
    APP_TITLE,
)
from app.services.llm.base import ChatMessage, GenerationResult, ModelInfo


class TestOpenRouterProviderInit:
    """Tests for OpenRouterProvider initialization."""

    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        provider = OpenRouterProvider(api_key="sk-test-key")

        assert provider._api_key == "sk-test-key"
        assert provider.model == DEFAULT_MODEL
        assert provider.base_url == DEFAULT_BASE_URL
        assert provider.timeout == 120.0

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        provider = OpenRouterProvider(
            api_key="sk-test-key",
            model="openai/gpt-4",
            base_url="https://custom.api.com/v1",
            timeout=60.0,
        )

        assert provider.model == "openai/gpt-4"
        assert provider.base_url == "https://custom.api.com/v1"
        assert provider.timeout == 60.0

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="API key is required"):
            OpenRouterProvider(api_key="")

        with pytest.raises(ValueError, match="API key is required"):
            OpenRouterProvider(api_key=None)

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        provider = OpenRouterProvider(
            api_key="sk-test",
            base_url="https://api.example.com/v1/",
        )
        assert provider.base_url == "https://api.example.com/v1"


class TestOpenRouterProviderHeaders:
    """Tests for request headers."""

    def test_get_headers(self):
        """Test that headers are correctly set."""
        provider = OpenRouterProvider(api_key="sk-test-key-123")
        headers = provider._get_headers()

        assert headers["Authorization"] == "Bearer sk-test-key-123"
        assert headers["HTTP-Referer"] == APP_REFERER
        assert headers["X-Title"] == APP_TITLE
        assert headers["Content-Type"] == "application/json"


class TestOpenRouterProviderChat:
    """Tests for chat functionality."""

    @pytest.mark.asyncio
    async def test_chat_success(self):
        """Test successful chat completion."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"role": "assistant", "content": "Hello! How can I help?"}}
            ],
            "model": "anthropic/claude-3-haiku",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18,
            },
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hello")]
            result = await provider.chat(messages)

            assert isinstance(result, GenerationResult)
            assert result.content == "Hello! How can I help?"
            assert result.model == "anthropic/claude-3-haiku"
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 8
            assert result.total_tokens == 18

    @pytest.mark.asyncio
    async def test_chat_with_custom_params(self):
        """Test chat with custom parameters."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}],
            "model": "openai/gpt-4",
            "usage": {},
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Test")]
            await provider.chat(
                messages,
                model="openai/gpt-4",
                temperature=0.7,
                max_tokens=100,
                top_p=0.9,
            )

            # Verify payload
            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["model"] == "openai/gpt-4"
            assert payload["temperature"] == 0.7
            assert payload["max_tokens"] == 100
            assert payload["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_chat_auth_error(self):
        """Test chat with invalid API key."""
        provider = OpenRouterProvider(api_key="invalid-key")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hello")]

            with pytest.raises(OpenRouterAuthError, match="Authentication failed"):
                await provider.chat(messages)

    @pytest.mark.asyncio
    async def test_chat_rate_limit_error(self):
        """Test chat with rate limit exceeded."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hello")]

            with pytest.raises(OpenRouterRateLimitError) as exc_info:
                await provider.chat(messages)

            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_chat_timeout_error(self):
        """Test chat with timeout."""
        provider = OpenRouterProvider(api_key="sk-test")

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_get_client.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hello")]

            with pytest.raises(OpenRouterError, match="timed out"):
                await provider.chat(messages)


class TestOpenRouterProviderGenerate:
    """Tests for generate functionality."""

    @pytest.mark.asyncio
    async def test_generate_wraps_chat(self):
        """Test that generate wraps prompt in chat message."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}}],
            "model": "test-model",
            "usage": {},
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await provider.generate("Test prompt")

            assert result.content == "Generated text"

            # Verify the prompt was wrapped in a user message
            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["messages"] == [{"role": "user", "content": "Test prompt"}]


class TestOpenRouterProviderStreaming:
    """Tests for streaming functionality."""

    @pytest.mark.asyncio
    async def test_chat_stream_success(self):
        """Test successful streaming chat."""
        provider = OpenRouterProvider(api_key="sk-test")

        # Simulate SSE response
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            'data: {"choices":[{"delta":{"content":"!"}}]}',
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in sse_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch("app.services.llm.openrouter_provider.httpx.AsyncClient") as MockClient:
            # Create mock client that works as async context manager
            mock_client = MagicMock()

            # Create mock stream context manager
            mock_stream_ctx = MagicMock()
            mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)

            # Set up client as async context manager
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            MockClient.return_value = mock_client

            messages = [ChatMessage(role="user", content="Hello")]
            tokens = []

            async for token in provider.chat_stream(messages):
                tokens.append(token)

            assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_chat_stream_handles_empty_lines(self):
        """Test streaming handles empty lines gracefully."""
        provider = OpenRouterProvider(api_key="sk-test")

        sse_lines = [
            "",
            'data: {"choices":[{"delta":{"content":"Test"}}]}',
            "",
            "data: [DONE]",
        ]

        async def mock_aiter_lines():
            for line in sse_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch("app.services.llm.openrouter_provider.httpx.AsyncClient") as MockClient:
            mock_client = MagicMock()

            mock_stream_ctx = MagicMock()
            mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
            mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_client.stream = MagicMock(return_value=mock_stream_ctx)

            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            MockClient.return_value = mock_client

            messages = [ChatMessage(role="user", content="Test")]
            tokens = []

            async for token in provider.chat_stream(messages):
                tokens.append(token)

            assert tokens == ["Test"]


class TestOpenRouterProviderHealthCheck:
    """Tests for health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with valid API key."""
        provider = OpenRouterProvider(api_key="sk-valid-key")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await provider.health_check()

            assert result is True
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_invalid_key(self):
        """Test health check with invalid API key."""
        provider = OpenRouterProvider(api_key="sk-invalid")

        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await provider.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_network_error(self):
        """Test health check with network error."""
        provider = OpenRouterProvider(api_key="sk-test")

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_get_client.return_value = mock_client

            result = await provider.health_check()

            assert result is False


class TestOpenRouterProviderListModels:
    """Tests for list models functionality."""

    @pytest.mark.asyncio
    async def test_list_models_success(self):
        """Test listing models successfully."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "anthropic/claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "context_length": 200000,
                    "pricing": {"prompt": "0.00000025", "completion": "0.00000125"},
                    "description": "Fast and efficient",
                },
                {
                    "id": "openai/gpt-4",
                    "name": "GPT-4",
                    "context_length": 8192,
                    "pricing": {"prompt": "0.00003", "completion": "0.00006"},
                },
            ]
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            models = await provider.list_models()

            assert len(models) == 2
            assert models[0].name == "anthropic/claude-3-haiku"
            assert models[0].details["context_length"] == 200000
            assert models[0].details["pricing"]["prompt"] == 0.00000025
            assert models[1].name == "openai/gpt-4"

    @pytest.mark.asyncio
    async def test_list_models_detailed(self):
        """Test listing models with detailed info."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "anthropic/claude-3-opus",
                    "name": "Claude 3 Opus",
                    "context_length": 200000,
                    "pricing": {"prompt": "0.000015", "completion": "0.000075"},
                    "description": "Most capable model",
                },
            ]
        }

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            models = await provider.list_models_detailed()

            assert len(models) == 1
            assert isinstance(models[0], OpenRouterModelInfo)
            assert models[0].id == "anthropic/claude-3-opus"
            assert models[0].context_length == 200000
            assert models[0].pricing["prompt"] == 0.000015

    @pytest.mark.asyncio
    async def test_list_models_error(self):
        """Test list models returns empty list on error."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            models = await provider.list_models()

            assert models == []


class TestOpenRouterProviderModelManagement:
    """Tests for model management."""

    def test_get_model_name(self):
        """Test getting current model name."""
        provider = OpenRouterProvider(api_key="sk-test", model="test/model")
        assert provider.get_model_name() == "test/model"

    def test_set_model(self):
        """Test setting model."""
        provider = OpenRouterProvider(api_key="sk-test")
        assert provider.model == DEFAULT_MODEL

        provider.set_model("openai/gpt-4-turbo")
        assert provider.model == "openai/gpt-4-turbo"
        assert provider.get_model_name() == "openai/gpt-4-turbo"


class TestOpenRouterProviderApiKeyRedaction:
    """Tests for API key redaction in logs."""

    def test_redact_api_key(self):
        """Test that API key is redacted from text."""
        provider = OpenRouterProvider(api_key="sk-secret-key-12345")

        text_with_key = "Error: Invalid key sk-secret-key-12345 provided"
        redacted = provider._redact_api_key(text_with_key)

        assert "sk-secret-key-12345" not in redacted
        assert "[REDACTED]" in redacted

    def test_redact_api_key_not_present(self):
        """Test redaction when key is not in text."""
        provider = OpenRouterProvider(api_key="sk-secret")

        text = "Some error message without the key"
        redacted = provider._redact_api_key(text)

        assert redacted == text

    @pytest.mark.asyncio
    async def test_api_key_not_in_error_logs(self):
        """Test that API key is not logged in error messages."""
        api_key = "sk-super-secret-key"
        provider = OpenRouterProvider(api_key=api_key)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = f"Error with key {api_key}"
        mock_response.json.return_value = {"error": {"message": f"Key {api_key} invalid"}}

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with patch("app.services.llm.openrouter_provider.logger") as mock_logger:
                messages = [ChatMessage(role="user", content="Test")]

                with pytest.raises(OpenRouterError):
                    await provider.chat(messages)

                # Check that API key was not logged
                for call in mock_logger.error.call_args_list:
                    logged_message = str(call)
                    assert api_key not in logged_message


class TestOpenRouterProviderClose:
    """Tests for client lifecycle management."""

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the HTTP client."""
        provider = OpenRouterProvider(api_key="sk-test")

        # Create a mock client
        mock_client = AsyncMock()
        mock_client.is_closed = False
        provider._client = mock_client

        await provider.close()

        mock_client.aclose.assert_called_once()
        assert provider._client is None

    @pytest.mark.asyncio
    async def test_close_already_closed_client(self):
        """Test closing an already closed client."""
        provider = OpenRouterProvider(api_key="sk-test")

        mock_client = AsyncMock()
        mock_client.is_closed = True
        provider._client = mock_client

        # Should not raise error
        await provider.close()

        mock_client.aclose.assert_not_called()
