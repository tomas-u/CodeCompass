"""Ollama LLM provider implementation."""

import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator

import httpx

from .base import LLMProvider, GenerationResult, ChatMessage, ModelInfo

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "phi3.5",
        timeout: float = 120.0,
    ):
        """Initialize the Ollama provider.

        Args:
            base_url: Ollama API base URL
            model: Default model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
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

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            **kwargs: Additional options (temperature, max_tokens, etc.)

        Returns:
            GenerationResult with the generated text
        """
        client = await self._get_client()

        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = kwargs["max_tokens"]

        try:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return GenerationResult(
                content=data.get("response", ""),
                model=data.get("model", self.model),
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                total_tokens=(
                    (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)
                    if data.get("prompt_eval_count") or data.get("eval_count")
                    else None
                ),
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            raise

    async def chat(self, messages: List[ChatMessage], **kwargs) -> GenerationResult:
        """Chat with the model using a conversation history.

        Args:
            messages: List of ChatMessage objects representing the conversation
            **kwargs: Additional options

        Returns:
            GenerationResult with the assistant's response
        """
        client = await self._get_client()

        # Convert ChatMessage objects to dicts
        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": message_dicts,
            "stream": False,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = kwargs["max_tokens"]
        if "num_ctx" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_ctx"] = kwargs["num_ctx"]

        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            return GenerationResult(
                content=data.get("message", {}).get("content", ""),
                model=data.get("model", self.model),
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                total_tokens=(
                    (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)
                    if data.get("prompt_eval_count") or data.get("eval_count")
                    else None
                ),
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise

    async def chat_stream(self, messages: List[ChatMessage], **kwargs) -> AsyncIterator[str]:
        """Stream chat response tokens.

        Args:
            messages: List of ChatMessage objects representing the conversation
            **kwargs: Additional options

        Yields:
            String tokens as they are generated
        """
        # Convert ChatMessage objects to dicts
        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": kwargs.get("model", self.model),
            "messages": message_dicts,
            "stream": True,  # Enable streaming
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = kwargs["max_tokens"]
        if "num_ctx" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_ctx"] = kwargs["num_ctx"]

        try:
            # Use a new client with streaming support
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse streaming response: {line}")
                                continue
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama streaming API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Ollama streaming chat failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is healthy and accessible."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List available models in Ollama."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("models", []):
                models.append(ModelInfo(
                    name=model_data.get("name", ""),
                    size=self._format_size(model_data.get("size")),
                    modified_at=model_data.get("modified_at"),
                    digest=model_data.get("digest"),
                    details=model_data.get("details"),
                ))
            return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            # Use a longer timeout for model pulls
            response = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=1800.0,  # 30 minutes for large models
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama.

        Args:
            model_name: Name of the model to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False

    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model

    def set_model(self, model: str):
        """Set the default model.

        Args:
            model: The model name to use
        """
        self.model = model

    @staticmethod
    def _format_size(size_bytes: Optional[int]) -> Optional[str]:
        """Format size in bytes to human readable string."""
        if size_bytes is None:
            return None

        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
