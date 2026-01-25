"""Integration tests for OpenRouter provider with real API.

These tests require a valid OPENROUTER_API_KEY environment variable.
They are skipped in CI unless the key is available.
"""

import os
import pytest

from app.services.llm.openrouter_provider import (
    OpenRouterProvider,
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
)
from app.services.llm.base import ChatMessage


# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set - skipping integration tests",
)


def get_provider() -> OpenRouterProvider:
    """Get an OpenRouter provider with the API key from environment."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return OpenRouterProvider(
        api_key=api_key,
        model="anthropic/claude-3-haiku",  # Use cheapest model for tests
    )


class TestOpenRouterIntegration:
    """Integration tests with real OpenRouter API."""

    @pytest.mark.asyncio
    async def test_health_check_real(self):
        """Test health check with real API."""
        provider = get_provider()

        try:
            result = await provider.health_check()
            assert result is True
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_list_models_real(self):
        """Test listing models from real API."""
        provider = get_provider()

        try:
            models = await provider.list_models()

            assert len(models) > 0
            # Should have some well-known models
            model_names = [m.name for m in models]
            assert any("claude" in name.lower() for name in model_names)
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_chat_real(self):
        """Test real chat completion."""
        provider = get_provider()

        try:
            messages = [
                ChatMessage(role="user", content="Reply with only the word 'hello'")
            ]
            result = await provider.chat(messages, max_tokens=10)

            assert result.content is not None
            assert len(result.content) > 0
            assert result.model is not None
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_chat_stream_real(self):
        """Test real streaming chat."""
        provider = get_provider()

        try:
            messages = [
                ChatMessage(role="user", content="Count from 1 to 3")
            ]

            tokens = []
            async for token in provider.chat_stream(messages, max_tokens=20):
                tokens.append(token)

            assert len(tokens) > 0
            full_response = "".join(tokens)
            assert len(full_response) > 0
        finally:
            await provider.close()

    @pytest.mark.asyncio
    async def test_generate_real(self):
        """Test real text generation."""
        provider = get_provider()

        try:
            result = await provider.generate(
                "Complete this: 2 + 2 = ",
                max_tokens=5,
            )

            assert result.content is not None
            assert "4" in result.content
        finally:
            await provider.close()


class TestOpenRouterIntegrationErrors:
    """Test error handling with real API."""

    @pytest.mark.asyncio
    async def test_invalid_model(self):
        """Test with invalid model name."""
        provider = get_provider()
        provider.set_model("invalid/nonexistent-model-12345")

        try:
            messages = [ChatMessage(role="user", content="Hello")]

            # OpenRouter returns 4xx for invalid models, handled as OpenRouterError
            with pytest.raises(OpenRouterError):
                await provider.chat(messages)
        finally:
            await provider.close()
