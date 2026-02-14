"""Factory functions for creating LLM, embedding providers, and vector service."""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import settings

from .base import LLMProvider, EmbeddingProvider
from .ollama_provider import OllamaProvider
from .embedding_provider import EmbeddingServiceProvider

logger = logging.getLogger(__name__)

# Singleton instances
_llm_provider: Optional[LLMProvider] = None
_embedding_provider: Optional[EmbeddingProvider] = None
_vector_service = None  # Type hint omitted to avoid circular import

# Thread safety lock for provider operations
_provider_lock = threading.Lock()

# Provider metadata for status reporting
_provider_info: Dict[str, Any] = {
    "provider_type": None,
    "model": None,
    "base_url": None,
    "initialized_at": None,
}


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider.

    Returns a singleton instance of the LLM provider based on configuration.
    If no provider has been initialized via reload_provider(), creates one
    using environment configuration.

    Returns:
        LLMProvider instance
    """
    global _llm_provider

    with _provider_lock:
        if _llm_provider is None:
            # Initialize with default configuration from environment
            _initialize_default_provider()

        return _llm_provider


def _initialize_default_provider() -> None:
    """Initialize provider with default configuration from environment."""
    global _llm_provider, _provider_info

    provider_type = settings.llm_provider.lower()

    if provider_type == "ollama":
        _llm_provider = OllamaProvider(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
        _provider_info = {
            "provider_type": "ollama_container",
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "initialized_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Initialized Ollama provider with model {settings.llm_model}")
    else:
        # Default to Ollama
        logger.warning(f"Unknown LLM provider '{provider_type}', defaulting to Ollama")
        _llm_provider = OllamaProvider(
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )
        _provider_info = {
            "provider_type": "ollama_container",
            "model": settings.llm_model,
            "base_url": settings.llm_base_url,
            "initialized_at": datetime.utcnow().isoformat(),
        }


async def reload_provider(config: Dict[str, Any]) -> LLMProvider:
    """Reload the LLM provider with new configuration.

    This function is thread-safe and properly cleans up the old provider
    before creating a new one.

    Args:
        config: New provider configuration dict with keys:
            - provider_type: str (ollama_container, ollama_external,
                                  openrouter_byok, openrouter_managed)
            - model: str
            - base_url: Optional[str]
            - api_key: Optional[str] (required for OpenRouter)

    Returns:
        New LLMProvider instance

    Raises:
        ValueError: Unknown provider type or missing required config
    """
    global _llm_provider, _provider_info

    provider_type = config.get("provider_type", "ollama_container")
    model = config.get("model", "qwen2.5-coder:7b")
    base_url = config.get("base_url")
    api_key = config.get("api_key")

    with _provider_lock:
        # Close existing provider if it has a close method
        if _llm_provider is not None:
            try:
                if hasattr(_llm_provider, "close"):
                    await _llm_provider.close()
                    logger.debug("Closed existing LLM provider")
            except Exception as e:
                logger.warning(f"Error closing existing provider: {e}")

        # Create new provider based on type
        if provider_type in ("ollama_container", "ollama_external"):
            # For container Ollama, fall back to the environment-configured URL
            # (e.g. http://ollama:11434 inside Docker) rather than localhost
            if base_url:
                effective_base_url = base_url
            elif provider_type == "ollama_container":
                effective_base_url = settings.llm_base_url
            else:
                effective_base_url = "http://localhost:11434"
            _llm_provider = OllamaProvider(
                base_url=effective_base_url,
                model=model,
            )
            _provider_info = {
                "provider_type": provider_type,
                "model": model,
                "base_url": effective_base_url,
                "initialized_at": datetime.utcnow().isoformat(),
            }
            logger.info(
                f"Reloaded LLM provider: {provider_type} with model {model} "
                f"at {effective_base_url}"
            )

        elif provider_type in ("openrouter_byok", "openrouter_managed"):
            if not api_key:
                raise ValueError("API key is required for OpenRouter provider")

            # Import here to avoid circular imports and loading when not needed
            from .openrouter_provider import OpenRouterProvider

            effective_base_url = base_url or "https://openrouter.ai/api/v1"
            _llm_provider = OpenRouterProvider(
                api_key=api_key,
                model=model,
                base_url=effective_base_url,
            )
            _provider_info = {
                "provider_type": provider_type,
                "model": model,
                "base_url": effective_base_url,
                "initialized_at": datetime.utcnow().isoformat(),
            }
            logger.info(
                f"Reloaded LLM provider: {provider_type} with model {model}"
            )

        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        return _llm_provider


def reload_provider_sync(config: Dict[str, Any]) -> LLMProvider:
    """Synchronous wrapper for reload_provider.

    Use this when calling from synchronous code. Creates a new event loop
    if needed to run the async reload.

    Args:
        config: Provider configuration (see reload_provider for details)

    Returns:
        New LLMProvider instance

    Raises:
        RuntimeError: If called from an async context (use reload_provider instead)
    """
    try:
        # Detect if we're already in an async context
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, safe to create one
        return asyncio.run(reload_provider(config))
    else:
        # Running event loop detected: this sync wrapper must not be used here
        raise RuntimeError(
            "reload_provider_sync cannot be called from an async context; "
            "use the async 'reload_provider' function instead."
        )


def get_provider_status() -> Dict[str, Any]:
    """Get current provider status for health checks.

    Returns:
        Dict with provider_type, model, base_url, initialized_at, status
    """
    global _llm_provider, _provider_info

    with _provider_lock:
        if _llm_provider is None:
            return {
                "provider_type": None,
                "model": None,
                "base_url": None,
                "initialized_at": None,
                "status": "not_initialized",
            }

        return {
            **_provider_info,
            "status": "initialized",
        }


async def get_provider_health() -> Dict[str, Any]:
    """Get provider health status including connectivity check.

    Note: Captures provider reference under lock, then releases lock before
    the health check. This means the result may be for a provider that was
    just replaced, but avoids blocking other operations during the check.

    Returns:
        Dict with status info and health check result
    """
    global _llm_provider, _provider_info

    # Capture provider and status under lock to avoid race conditions
    with _provider_lock:
        if _llm_provider is None:
            return {
                "provider_type": None,
                "model": None,
                "base_url": None,
                "initialized_at": None,
                "status": "not_initialized",
                "healthy": False,
            }

        provider = _llm_provider
        status: Dict[str, Any] = {
            **_provider_info,
            "status": "initialized",
        }

    # Perform health check outside the lock to avoid blocking other operations
    try:
        healthy = await provider.health_check()
        return {
            **status,
            "healthy": healthy,
            "status": "ready" if healthy else "unavailable",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            **status,
            "healthy": False,
            "status": "error",
            "error": str(e),
        }


def get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider.

    Returns a singleton instance of the embedding provider.

    Returns:
        EmbeddingProvider instance
    """
    global _embedding_provider

    if _embedding_provider is None:
        _embedding_provider = EmbeddingServiceProvider(
            base_url=settings.embedding_base_url,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
        )
        logger.info(f"Initialized embedding provider with model {settings.embedding_model}")

    return _embedding_provider


def get_vector_service():
    """Get the vector service for Qdrant operations.

    Returns a singleton instance of the vector service.

    Returns:
        VectorService instance
    """
    global _vector_service

    if _vector_service is None:
        # Import here to avoid circular imports
        from app.services.vector_service import VectorService

        _vector_service = VectorService(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            dimensions=settings.embedding_dimensions,
        )
        logger.info(f"Initialized vector service (Qdrant at {settings.qdrant_host}:{settings.qdrant_port})")

    return _vector_service


def reset_providers():
    """Reset provider instances. Useful for testing or reconfiguration.

    Note: This does NOT close existing providers. For proper cleanup,
    use reload_provider() which handles closing before recreating.
    """
    global _llm_provider, _embedding_provider, _vector_service, _provider_info

    with _provider_lock:
        _llm_provider = None
        _embedding_provider = None
        _vector_service = None
        _provider_info = {
            "provider_type": None,
            "model": None,
            "base_url": None,
            "initialized_at": None,
        }


async def close_providers():
    """Close all providers gracefully. Call this on application shutdown."""
    global _llm_provider, _embedding_provider

    with _provider_lock:
        if _llm_provider is not None:
            try:
                if hasattr(_llm_provider, "close"):
                    await _llm_provider.close()
                    logger.info("Closed LLM provider")
            except Exception as e:
                logger.warning(f"Error closing LLM provider: {e}")

        # Embedding provider may also have resources to close
        if _embedding_provider is not None:
            try:
                if hasattr(_embedding_provider, "close"):
                    await _embedding_provider.close()
                    logger.info("Closed embedding provider")
            except Exception as e:
                logger.warning(f"Error closing embedding provider: {e}")
