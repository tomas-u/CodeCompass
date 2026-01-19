"""Embedding service provider implementation."""

import logging
from typing import List, Optional

import httpx

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)


class EmbeddingServiceProvider(EmbeddingProvider):
    """Embedding provider using the external embedding microservice."""

    def __init__(
        self,
        base_url: str = "http://localhost:11435",
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimensions: int = 384,
        timeout: float = 60.0,
    ):
        """Initialize the embedding service provider.

        Args:
            base_url: Embedding service base URL
            model: Embedding model name (for reference)
            dimensions: Expected embedding dimensions
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimensions = dimensions
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        client = await self._get_client()

        try:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"texts": texts},
            )
            response.raise_for_status()
            data = response.json()

            embeddings = data.get("embeddings", [])

            # Update dimensions from actual response if available
            if embeddings and data.get("dimensions"):
                self._dimensions = data["dimensions"]

            return embeddings
        except httpx.HTTPStatusError as e:
            logger.error(f"Embedding service error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text])
        if not embeddings:
            raise ValueError("No embedding returned")
        return embeddings[0]

    def get_dimensions(self) -> int:
        """Get the embedding dimensions."""
        return self._dimensions

    async def health_check(self) -> bool:
        """Check if the embedding service is healthy."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                # Update dimensions from health check
                if data.get("dimensions"):
                    self._dimensions = data["dimensions"]
                return True
            return False
        except Exception as e:
            logger.warning(f"Embedding service health check failed: {e}")
            return False

    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model
