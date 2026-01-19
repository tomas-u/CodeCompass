"""Factory functions for creating LLM, embedding providers, and vector service."""

import logging
from typing import Optional

from app.config import settings

from .base import LLMProvider, EmbeddingProvider
from .ollama_provider import OllamaProvider
from .embedding_provider import EmbeddingServiceProvider

logger = logging.getLogger(__name__)

# Singleton instances
_llm_provider: Optional[LLMProvider] = None
_embedding_provider: Optional[EmbeddingProvider] = None
_vector_service = None  # Type hint omitted to avoid circular import


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider.

    Returns a singleton instance of the LLM provider based on configuration.

    Returns:
        LLMProvider instance
    """
    global _llm_provider

    if _llm_provider is None:
        provider_type = settings.llm_provider.lower()

        if provider_type == "ollama":
            _llm_provider = OllamaProvider(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
            logger.info(f"Initialized Ollama provider with model {settings.llm_model}")
        else:
            # Default to Ollama for now
            logger.warning(f"Unknown LLM provider '{provider_type}', defaulting to Ollama")
            _llm_provider = OllamaProvider(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )

    return _llm_provider


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
    """Reset provider instances. Useful for testing or reconfiguration."""
    global _llm_provider, _embedding_provider, _vector_service
    _llm_provider = None
    _embedding_provider = None
    _vector_service = None
