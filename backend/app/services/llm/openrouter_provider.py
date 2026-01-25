"""OpenRouter LLM provider implementation."""

import json
import logging
from typing import List, Optional, AsyncIterator, Dict, Any
from dataclasses import dataclass

import httpx

from .base import LLMProvider, GenerationResult, ChatMessage, ModelInfo

logger = logging.getLogger(__name__)

# Constants
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3-haiku"
DEFAULT_TIMEOUT = 120.0

# Application identifiers for OpenRouter
APP_REFERER = "https://codecompass.dev"
APP_TITLE = "CodeCompass"


@dataclass
class OpenRouterModelInfo:
    """Extended model info for OpenRouter models."""

    id: str  # e.g., "anthropic/claude-3-haiku"
    name: str
    context_length: int
    pricing: Dict[str, float]  # {"prompt": 0.00025, "completion": 0.00125}
    description: Optional[str] = None


class OpenRouterError(Exception):
    """Base exception for OpenRouter errors."""

    pass


class OpenRouterAuthError(OpenRouterError):
    """Authentication error (invalid API key)."""

    pass


class OpenRouterRateLimitError(OpenRouterError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class OpenRouterProvider(LLMProvider):
    """LLM provider using OpenRouter API.

    OpenRouter provides access to various LLM models through a unified API,
    including Claude, GPT-4, Llama, Mistral, and many others.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key (required)
            model: Default model to use (e.g., "anthropic/claude-3-haiku")
            base_url: OpenRouter API base URL
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required for OpenRouter")

        self._api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": APP_REFERER,
            "X-Title": APP_TITLE,
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: The HTTP response

        Raises:
            OpenRouterAuthError: For 401/403 errors
            OpenRouterRateLimitError: For 429 errors
            OpenRouterError: For other errors
        """
        status = response.status_code

        # Try to get error message from response
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except json.JSONDecodeError:
            error_msg = response.text

        # Never log the API key - redact any potential key in error messages
        safe_error_msg = self._redact_api_key(error_msg)

        if status == 401 or status == 403:
            logger.error(f"OpenRouter authentication failed: {safe_error_msg}")
            raise OpenRouterAuthError(f"Authentication failed: {safe_error_msg}")

        if status == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            logger.warning(f"OpenRouter rate limit exceeded. Retry after: {retry_seconds}s")
            raise OpenRouterRateLimitError(
                f"Rate limit exceeded: {safe_error_msg}",
                retry_after=retry_seconds,
            )

        logger.error(f"OpenRouter API error ({status}): {safe_error_msg}")
        raise OpenRouterError(f"API error ({status}): {safe_error_msg}")

    def _redact_api_key(self, text: str) -> str:
        """Redact API key from text to prevent logging secrets."""
        if self._api_key and self._api_key in text:
            return text.replace(self._api_key, "[REDACTED]")
        return text

    async def generate(self, prompt: str, **kwargs) -> GenerationResult:
        """Generate text from a prompt.

        This wraps the prompt in a user message and uses the chat API.

        Args:
            prompt: The input prompt
            **kwargs: Additional options (temperature, max_tokens, etc.)

        Returns:
            GenerationResult with the generated text
        """
        messages = [ChatMessage(role="user", content=prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: List[ChatMessage], **kwargs) -> GenerationResult:
        """Chat with the model using a conversation history.

        Args:
            messages: List of ChatMessage objects representing the conversation
            **kwargs: Additional options (temperature, max_tokens, model)

        Returns:
            GenerationResult with the assistant's response
        """
        client = await self._get_client()

        # Convert ChatMessage objects to dicts
        message_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": message_dicts,
            "stream": False,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]

        try:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )

            if response.status_code != 200:
                self._handle_error_response(response)

            data = response.json()

            # Extract response content
            choices = data.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "")

            # Extract usage info
            usage = data.get("usage", {})

            return GenerationResult(
                content=content,
                model=data.get("model", self.model),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            )

        except (OpenRouterError, OpenRouterAuthError, OpenRouterRateLimitError):
            raise
        except httpx.TimeoutException:
            logger.error("OpenRouter request timed out")
            raise OpenRouterError("Request timed out")
        except Exception as e:
            logger.error(f"OpenRouter chat failed: {self._redact_api_key(str(e))}")
            raise OpenRouterError(f"Chat failed: {self._redact_api_key(str(e))}")

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

        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": message_dicts,
            "stream": True,
        }

        # Add optional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self._get_headers(),
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        # Read body for error handling
                        await response.aread()
                        self._handle_error_response(response)

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # SSE format: "data: {...}" or "data: [DONE]"
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                logger.debug(f"Failed to parse SSE data: {data_str}")
                                continue

        except (OpenRouterError, OpenRouterAuthError, OpenRouterRateLimitError):
            raise
        except httpx.TimeoutException:
            logger.error("OpenRouter streaming request timed out")
            raise OpenRouterError("Streaming request timed out")
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {self._redact_api_key(str(e))}")
            raise OpenRouterError(f"Streaming failed: {self._redact_api_key(str(e))}")

    async def health_check(self) -> bool:
        """Check if OpenRouter is accessible and API key is valid.

        Makes a minimal request to verify the API key works.

        Returns:
            True if the API is accessible and key is valid, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")

            if response.status_code == 200:
                return True
            elif response.status_code in (401, 403):
                logger.warning("OpenRouter health check failed: Invalid API key")
                return False
            else:
                logger.warning(f"OpenRouter health check failed: {response.status_code}")
                return False

        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {self._redact_api_key(str(e))}")
            return False

    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter.

        Returns:
            List of ModelInfo objects with model details
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")

            if response.status_code != 200:
                logger.error(f"Failed to list models: {response.status_code}")
                return []

            data = response.json()
            models = []

            for model_data in data.get("data", []):
                model_id = model_data.get("id", "")

                # Parse pricing (OpenRouter returns as strings)
                pricing = model_data.get("pricing", {})
                try:
                    prompt_price = float(pricing.get("prompt", "0"))
                    completion_price = float(pricing.get("completion", "0"))
                except (ValueError, TypeError):
                    prompt_price = 0.0
                    completion_price = 0.0

                models.append(ModelInfo(
                    name=model_id,
                    size=None,  # OpenRouter doesn't provide size
                    modified_at=None,
                    digest=None,
                    details={
                        "display_name": model_data.get("name", model_id),
                        "context_length": model_data.get("context_length", 0),
                        "description": model_data.get("description"),
                        "pricing": {
                            "prompt": prompt_price,
                            "completion": completion_price,
                        },
                        "architecture": model_data.get("architecture"),
                    },
                ))

            return models

        except Exception as e:
            logger.error(f"Failed to list OpenRouter models: {self._redact_api_key(str(e))}")
            return []

    async def list_models_detailed(self) -> List[OpenRouterModelInfo]:
        """List available models with detailed OpenRouter-specific info.

        This is an OpenRouter-specific extension and is not part of the
        standard LLMProvider interface. Callers should guard usage of this
        method to OpenRouterProvider instances only.

        Returns:
            List of OpenRouterModelInfo objects with pricing and context info.
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/models")

            if response.status_code != 200:
                return []

            data = response.json()
            models = []

            for model_data in data.get("data", []):
                # Parse pricing
                pricing = model_data.get("pricing", {})
                try:
                    pricing_dict = {
                        "prompt": float(pricing.get("prompt", "0")),
                        "completion": float(pricing.get("completion", "0")),
                    }
                except (ValueError, TypeError):
                    pricing_dict = {"prompt": 0.0, "completion": 0.0}

                models.append(OpenRouterModelInfo(
                    id=model_data.get("id", ""),
                    name=model_data.get("name", ""),
                    context_length=model_data.get("context_length", 0),
                    pricing=pricing_dict,
                    description=model_data.get("description"),
                ))

            return models

        except Exception as e:
            logger.error(f"Failed to list detailed models: {self._redact_api_key(str(e))}")
            return []

    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model

    def set_model(self, model: str) -> None:
        """Set the default model.

        Args:
            model: The model name to use (e.g., "anthropic/claude-3-haiku")
        """
        self.model = model
