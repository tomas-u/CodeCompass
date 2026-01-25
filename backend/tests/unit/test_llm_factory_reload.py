"""Unit tests for LLM factory hot-reload functionality.

Tests cover:
- reload_provider() with different provider types
- Thread-safety of provider operations
- Provider lifecycle (init, reload, close)
- Status and health check functions
"""

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.factory import (
    reload_provider,
    reload_provider_sync,
    get_provider_status,
    get_provider_health,
    close_providers,
    reset_providers,
    get_llm_provider,
    _provider_lock,
)


class TestReloadProvider:
    """Tests for reload_provider function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    @pytest.mark.asyncio
    async def test_reload_ollama_container(self):
        """Test reloading with ollama_container provider type."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "ollama_container",
                "model": "qwen2.5-coder:7b",
                "base_url": "http://ollama:11434",
            }

            provider = await reload_provider(config)

            assert provider == mock_provider
            mock_provider_class.assert_called_once_with(
                base_url="http://ollama:11434",
                model="qwen2.5-coder:7b",
            )

    @pytest.mark.asyncio
    async def test_reload_ollama_external(self):
        """Test reloading with ollama_external provider type."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "ollama_external",
                "model": "llama3:8b",
                "base_url": "http://localhost:11434",
            }

            provider = await reload_provider(config)

            assert provider == mock_provider
            mock_provider_class.assert_called_once_with(
                base_url="http://localhost:11434",
                model="llama3:8b",
            )

    @pytest.mark.asyncio
    async def test_reload_openrouter_byok(self):
        """Test reloading with openrouter_byok provider type."""
        with patch(
            "app.services.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "openrouter_byok",
                "model": "anthropic/claude-3-haiku",
                "api_key": "sk-or-v1-test-key",
            }

            provider = await reload_provider(config)

            assert provider == mock_provider
            mock_provider_class.assert_called_once_with(
                api_key="sk-or-v1-test-key",
                model="anthropic/claude-3-haiku",
                base_url="https://openrouter.ai/api/v1",
            )

    @pytest.mark.asyncio
    async def test_reload_openrouter_managed(self):
        """Test reloading with openrouter_managed provider type."""
        with patch(
            "app.services.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "openrouter_managed",
                "model": "meta-llama/llama-3-8b",
                "api_key": "sk-or-managed-key",
                "base_url": "https://openrouter.ai/api/v1",
            }

            provider = await reload_provider(config)

            assert provider == mock_provider

    @pytest.mark.asyncio
    async def test_reload_openrouter_missing_api_key(self):
        """Test that OpenRouter requires API key."""
        config = {
            "provider_type": "openrouter_byok",
            "model": "anthropic/claude-3-haiku",
        }

        with pytest.raises(ValueError, match="API key is required"):
            await reload_provider(config)

    @pytest.mark.asyncio
    async def test_reload_unknown_provider_type(self):
        """Test that unknown provider type raises error."""
        config = {
            "provider_type": "unknown_provider",
            "model": "test-model",
        }

        with pytest.raises(ValueError, match="Unknown provider type"):
            await reload_provider(config)

    @pytest.mark.asyncio
    async def test_reload_closes_existing_provider(self):
        """Test that reload properly closes existing provider."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            # First provider
            old_provider = MagicMock()
            old_provider.close = AsyncMock()

            # Second provider
            new_provider = MagicMock()

            mock_provider_class.side_effect = [old_provider, new_provider]

            # First reload
            await reload_provider(
                {"provider_type": "ollama_container", "model": "model1"}
            )

            # Second reload should close the first
            await reload_provider(
                {"provider_type": "ollama_container", "model": "model2"}
            )

            old_provider.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_handles_close_error(self):
        """Test that reload continues even if close fails."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            old_provider = MagicMock()
            old_provider.close = AsyncMock(side_effect=Exception("Close failed"))

            new_provider = MagicMock()

            mock_provider_class.side_effect = [old_provider, new_provider]

            # First reload
            await reload_provider(
                {"provider_type": "ollama_container", "model": "model1"}
            )

            # Second reload should still work despite close error
            result = await reload_provider(
                {"provider_type": "ollama_container", "model": "model2"}
            )

            assert result == new_provider

    @pytest.mark.asyncio
    async def test_reload_uses_default_values(self):
        """Test that reload uses default values for missing config."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            # Empty config should use defaults
            provider = await reload_provider({})

            mock_provider_class.assert_called_once_with(
                base_url="http://localhost:11434",
                model="qwen2.5-coder:7b",
            )

    @pytest.mark.asyncio
    async def test_reload_custom_base_url(self):
        """Test that reload uses custom base URL for OpenRouter."""
        with patch(
            "app.services.llm.openrouter_provider.OpenRouterProvider"
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "openrouter_byok",
                "model": "test-model",
                "api_key": "sk-or-v1-key",
                "base_url": "https://custom.openrouter.ai/v1",
            }

            await reload_provider(config)

            mock_provider_class.assert_called_once_with(
                api_key="sk-or-v1-key",
                model="test-model",
                base_url="https://custom.openrouter.ai/v1",
            )


class TestReloadProviderSync:
    """Tests for reload_provider_sync function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    def test_sync_wrapper_works(self):
        """Test that sync wrapper properly calls async function."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            config = {
                "provider_type": "ollama_container",
                "model": "test-model",
            }

            provider = reload_provider_sync(config)

            assert provider == mock_provider


class TestGetProviderStatus:
    """Tests for get_provider_status function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    def test_status_not_initialized(self):
        """Test status when no provider is initialized."""
        status = get_provider_status()

        assert status["status"] == "not_initialized"
        assert status["provider_type"] is None
        assert status["model"] is None

    @pytest.mark.asyncio
    async def test_status_after_reload(self):
        """Test status after provider is reloaded."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {
                    "provider_type": "ollama_container",
                    "model": "qwen2.5-coder:7b",
                    "base_url": "http://ollama:11434",
                }
            )

            status = get_provider_status()

            assert status["status"] == "initialized"
            assert status["provider_type"] == "ollama_container"
            assert status["model"] == "qwen2.5-coder:7b"
            assert status["base_url"] == "http://ollama:11434"
            assert status["initialized_at"] is not None


class TestGetProviderHealth:
    """Tests for get_provider_health function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    @pytest.mark.asyncio
    async def test_health_not_initialized(self):
        """Test health when no provider is initialized."""
        health = await get_provider_health()

        assert health["healthy"] is False
        assert health["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_health_provider_healthy(self):
        """Test health when provider is healthy."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.health_check = AsyncMock(return_value=True)
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {"provider_type": "ollama_container", "model": "test-model"}
            )

            health = await get_provider_health()

            assert health["healthy"] is True
            assert health["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_provider_unhealthy(self):
        """Test health when provider is unavailable."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.health_check = AsyncMock(return_value=False)
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {"provider_type": "ollama_container", "model": "test-model"}
            )

            health = await get_provider_health()

            assert health["healthy"] is False
            assert health["status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_health_check_error(self):
        """Test health when health check raises error."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.health_check = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {"provider_type": "ollama_container", "model": "test-model"}
            )

            health = await get_provider_health()

            assert health["healthy"] is False
            assert health["status"] == "error"
            assert "Connection failed" in health["error"]


class TestCloseProviders:
    """Tests for close_providers function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    @pytest.mark.asyncio
    async def test_close_llm_provider(self):
        """Test that close_providers closes the LLM provider."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.close = AsyncMock()
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {"provider_type": "ollama_container", "model": "test-model"}
            )

            await close_providers()

            mock_provider.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_error(self):
        """Test that close_providers handles errors gracefully."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider.close = AsyncMock(side_effect=Exception("Close failed"))
            mock_provider_class.return_value = mock_provider

            await reload_provider(
                {"provider_type": "ollama_container", "model": "test-model"}
            )

            # Should not raise
            await close_providers()

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self):
        """Test that close_providers works when no provider is initialized."""
        # Should not raise
        await close_providers()


class TestThreadSafety:
    """Tests for thread-safety of provider operations."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    @pytest.mark.asyncio
    async def test_concurrent_reloads(self):
        """Test that concurrent reloads are handled safely."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            providers_created = []

            def create_provider(*args, **kwargs):
                provider = MagicMock()
                provider.close = AsyncMock()
                providers_created.append(provider)
                return provider

            mock_provider_class.side_effect = create_provider

            # Run multiple reloads concurrently
            tasks = [
                reload_provider(
                    {"provider_type": "ollama_container", "model": f"model-{i}"}
                )
                for i in range(5)
            ]

            await asyncio.gather(*tasks)

            # Should have created multiple providers (one per reload)
            assert len(providers_created) == 5

    def test_lock_exists(self):
        """Test that the provider lock exists."""
        assert _provider_lock is not None
        assert isinstance(_provider_lock, type(threading.Lock()))


class TestGetLLMProvider:
    """Tests for get_llm_provider function."""

    @pytest.fixture(autouse=True)
    def reset_state(self):
        """Reset provider state before each test."""
        reset_providers()
        yield
        reset_providers()

    def test_get_creates_default_provider(self):
        """Test that get_llm_provider creates default provider if none exists."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            provider = get_llm_provider()

            assert provider == mock_provider
            mock_provider_class.assert_called_once()

    def test_get_returns_same_instance(self):
        """Test that get_llm_provider returns the same instance."""
        with patch("app.services.llm.factory.OllamaProvider") as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            provider1 = get_llm_provider()
            provider2 = get_llm_provider()

            assert provider1 is provider2
            mock_provider_class.assert_called_once()  # Only created once
