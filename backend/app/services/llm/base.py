"""Abstract base classes for LLM and Embedding providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """Result of text generation."""
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class ChatMessage:
    """Chat message for conversation."""
    role: str  # "user", "assistant", or "system"
    content: str


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    size: Optional[str] = None
    modified_at: Optional[str] = None
    digest: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific options (temperature, max_tokens, etc.)

        Returns:
            GenerationResult with the generated text
        """
        pass

    @abstractmethod
    async def chat(self, messages: List[ChatMessage], **kwargs) -> GenerationResult:
        """Chat with the model using a conversation history.

        Args:
            messages: List of ChatMessage objects representing the conversation
            **kwargs: Additional provider-specific options

        Returns:
            GenerationResult with the assistant's response
        """
        pass

    @abstractmethod
    def chat_stream(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat response tokens.

        Args:
            messages: List of ChatMessage objects representing the conversation
            **kwargs: Additional provider-specific options

        Yields:
            String tokens as they are generated
        """
        # Abstract async generator - implementation must use 'async def' with 'yield'
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.

        Returns:
            True if the provider is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models.

        Returns:
            List of ModelInfo objects
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name.

        Returns:
            The name of the currently configured model
        """
        pass


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Get the embedding dimensions.

        Returns:
            The number of dimensions in the embedding vectors
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.

        Returns:
            True if the provider is healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name.

        Returns:
            The name of the currently configured embedding model
        """
        pass
