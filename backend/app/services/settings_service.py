"""Settings service for LLM configuration management."""

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional, List
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.settings import LLMSettingsModel
from app.schemas.settings import ProviderType
from app.repositories.settings_repository import SettingsRepository
from app.services.secrets_service import SecretsService, get_secrets_service
from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openrouter_provider import (
    OpenRouterProvider,
    OpenRouterAuthError,
    OpenRouterError,
)

logger = logging.getLogger(__name__)

# Validation constants
BLOCKED_HOSTS = {"ngrok.io", "ngrok.app", "localtunnel.me", "loca.lt", "serveo.net"}
MODEL_NAME_PATTERN = re.compile(r"^[\w\-\./:\d]+$")
OPENROUTER_KEY_PREFIX = "sk-or-"
OPENROUTER_KEY_MIN_LENGTH = 20


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    provider_status: str
    model_available: bool
    test_response_ms: Optional[int] = None
    error: Optional[str] = None
    details: Optional[dict] = None


@dataclass
class OpenRouterModelInfo:
    """OpenRouter model information for API responses."""

    id: str
    name: str
    provider: str
    context_length: int
    pricing: dict
    capabilities: List[str]
    description: Optional[str] = None


class SettingsService:
    """Service for managing LLM settings.

    Provides validation, connection testing, and settings management
    with support for hot-reload of LLM providers.
    """

    def __init__(self, db: Session, secrets: Optional[SecretsService] = None):
        """Initialize the settings service.

        Args:
            db: SQLAlchemy database session
            secrets: Optional secrets service (uses singleton if not provided)
        """
        self.db = db
        self.secrets = secrets or get_secrets_service()
        self.repository = SettingsRepository(db=db, secrets=self.secrets)

    # -------------------------------------------------------------------------
    # Validation methods
    # -------------------------------------------------------------------------

    def validate_base_url(self, url: str) -> tuple[bool, Optional[str]]:
        """Validate a base URL for LLM providers.

        Args:
            url: The URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "Base URL is required"

        try:
            parsed = urlparse(url)

            # Must be http or https
            if parsed.scheme not in ("http", "https"):
                return False, "URL must use http or https protocol"

            # Must have valid host
            if not parsed.netloc:
                return False, "URL must have a valid host"

            # Block tunneling services
            host = parsed.netloc.lower()
            for blocked in BLOCKED_HOSTS:
                if blocked in host:
                    return False, f"Tunneling services ({blocked}) are not allowed"

            return True, None

        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"

    def validate_model_name(self, name: str) -> tuple[bool, Optional[str]]:
        """Validate a model name.

        Args:
            name: The model name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Model name is required"

        if len(name) > 200:
            return False, "Model name too long (max 200 characters)"

        if not MODEL_NAME_PATTERN.match(name):
            return False, "Model name contains invalid characters"

        return True, None

    def validate_openrouter_key(self, key: str) -> tuple[bool, Optional[str]]:
        """Validate an OpenRouter API key format.

        Args:
            key: The API key to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not key:
            return False, "API key is required for OpenRouter"

        if not key.startswith(OPENROUTER_KEY_PREFIX):
            return False, f"API key must start with '{OPENROUTER_KEY_PREFIX}'"

        if len(key) < OPENROUTER_KEY_MIN_LENGTH:
            return False, f"API key too short (minimum {OPENROUTER_KEY_MIN_LENGTH} characters)"

        return True, None

    # -------------------------------------------------------------------------
    # Connection testing
    # -------------------------------------------------------------------------

    async def test_connection(
        self,
        provider_type: ProviderType,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_format: Optional[str] = None,
    ) -> ValidationResult:
        """Test a connection to an LLM provider.

        Args:
            provider_type: The type of provider
            model: The model to test
            base_url: Optional base URL for the provider
            api_key: Optional API key for cloud providers
            api_format: Optional API format (ollama or openai)

        Returns:
            ValidationResult with test results
        """
        start_time = time.time()

        try:
            # Validate inputs based on provider type
            if provider_type in (ProviderType.OLLAMA_CONTAINER, ProviderType.OLLAMA_EXTERNAL):
                return await self._test_ollama_connection(
                    provider_type, model, base_url, api_format, start_time
                )
            elif provider_type in (ProviderType.OPENROUTER_BYOK, ProviderType.OPENROUTER_MANAGED):
                return await self._test_openrouter_connection(
                    provider_type, model, base_url, api_key, start_time
                )
            else:
                return ValidationResult(
                    valid=False,
                    provider_status="error",
                    model_available=False,
                    error=f"Unknown provider type: {provider_type}",
                )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Connection test failed: {e}")
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                test_response_ms=elapsed_ms,
                error=str(e),
            )

    async def _test_ollama_connection(
        self,
        provider_type: ProviderType,
        model: str,
        base_url: Optional[str],
        api_format: Optional[str],
        start_time: float,
    ) -> ValidationResult:
        """Test connection to Ollama provider."""
        # Validate base URL
        url = base_url or "http://localhost:11434"
        valid, error = self.validate_base_url(url)
        if not valid:
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                error=error,
            )

        # Validate model name
        valid, error = self.validate_model_name(model)
        if not valid:
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                error=error,
            )

        try:
            provider = OllamaProvider(base_url=url, model=model)

            # Health check
            is_healthy = await provider.health_check()
            if not is_healthy:
                return ValidationResult(
                    valid=False,
                    provider_status="unavailable",
                    model_available=False,
                    test_response_ms=int((time.time() - start_time) * 1000),
                    error="Cannot connect to Ollama service",
                )

            # Check if model is available
            models = await provider.list_models()
            model_names = [m.name for m in models]
            model_available = model in model_names

            # Try a simple generation to verify
            if model_available:
                await provider.generate("Say 'test' in one word.", model=model)

            elapsed_ms = int((time.time() - start_time) * 1000)

            return ValidationResult(
                valid=True,
                provider_status="ready",
                model_available=model_available,
                test_response_ms=elapsed_ms,
                details={
                    "available_models": model_names[:10],  # Limit to 10 for response size
                    "model_count": len(model_names),
                },
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                test_response_ms=elapsed_ms,
                error=f"Connection failed: {str(e)}",
            )

    async def _test_openrouter_connection(
        self,
        provider_type: ProviderType,
        model: str,
        base_url: Optional[str],
        api_key: Optional[str],
        start_time: float,
    ) -> ValidationResult:
        """Test connection to OpenRouter provider."""
        # Validate API key
        if not api_key:
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                error="API key is required for OpenRouter",
            )

        valid, error = self.validate_openrouter_key(api_key)
        if not valid:
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                error=error,
            )

        # Validate model name
        valid, error = self.validate_model_name(model)
        if not valid:
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                error=error,
            )

        url = base_url or "https://openrouter.ai/api/v1"

        try:
            provider = OpenRouterProvider(
                api_key=api_key,
                model=model,
                base_url=url,
            )

            # Health check (validates API key)
            is_healthy = await provider.health_check()
            if not is_healthy:
                await provider.close()
                return ValidationResult(
                    valid=False,
                    provider_status="unavailable",
                    model_available=False,
                    test_response_ms=int((time.time() - start_time) * 1000),
                    error="API key validation failed",
                )

            # List models to check availability and get pricing
            models = await provider.list_models_detailed()
            model_info = next((m for m in models if m.id == model), None)

            elapsed_ms = int((time.time() - start_time) * 1000)
            await provider.close()

            details = None
            if model_info:
                details = {
                    "model_name": model_info.name,
                    "context_length": model_info.context_length,
                    "pricing": {
                        "input_per_million": model_info.pricing.get("prompt", 0) * 1_000_000,
                        "output_per_million": model_info.pricing.get("completion", 0) * 1_000_000,
                    },
                }

            return ValidationResult(
                valid=True,
                provider_status="ready",
                model_available=model_info is not None,
                test_response_ms=elapsed_ms,
                details=details,
            )

        except OpenRouterAuthError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                test_response_ms=elapsed_ms,
                error=f"Authentication failed: {str(e)}",
            )
        except OpenRouterError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ValidationResult(
                valid=False,
                provider_status="error",
                model_available=False,
                test_response_ms=elapsed_ms,
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Settings management
    # -------------------------------------------------------------------------

    def get_current_settings(self) -> Optional[LLMSettingsModel]:
        """Get current LLM settings.

        Returns:
            LLMSettingsModel if settings exist, None otherwise.
        """
        return self.repository.get_llm_settings()

    def get_or_create_settings(self) -> LLMSettingsModel:
        """Get current LLM settings or create defaults.

        Returns:
            LLMSettingsModel with current or default settings.
        """
        return self.repository.get_or_create_llm_settings()

    def save_settings(
        self,
        provider_type: ProviderType,
        model: str,
        base_url: Optional[str] = None,
        api_format: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> LLMSettingsModel:
        """Save LLM settings.

        Args:
            provider_type: The provider type
            model: The model name
            base_url: Optional base URL
            api_format: Optional API format
            api_key: Optional API key (will be encrypted)

        Returns:
            The saved LLMSettingsModel.
        """
        return self.repository.save_llm_settings(
            provider_type=provider_type,
            model=model,
            base_url=base_url,
            api_format=api_format,
            api_key=api_key,
        )

    def get_decrypted_api_key(self, settings: LLMSettingsModel) -> Optional[str]:
        """Get decrypted API key from settings.

        Args:
            settings: The settings model

        Returns:
            Decrypted API key or None.
        """
        return self.repository.get_decrypted_api_key(settings)

    # -------------------------------------------------------------------------
    # OpenRouter model listing
    # -------------------------------------------------------------------------

    async def list_openrouter_models(
        self, api_key: str
    ) -> List[OpenRouterModelInfo]:
        """List available OpenRouter models.

        Args:
            api_key: OpenRouter API key

        Returns:
            List of OpenRouterModelInfo objects.
        """
        # Validate API key format
        valid, error = self.validate_openrouter_key(api_key)
        if not valid:
            raise ValueError(error)

        try:
            provider = OpenRouterProvider(api_key=api_key)
            models = await provider.list_models_detailed()
            await provider.close()

            result = []
            for m in models:
                # Extract provider from model ID (e.g., "anthropic/claude-3" -> "anthropic")
                provider_name = m.id.split("/")[0] if "/" in m.id else "unknown"

                # Determine capabilities (simplified)
                capabilities = ["chat"]
                if "code" in m.id.lower() or "coder" in m.name.lower():
                    capabilities.append("code")

                result.append(OpenRouterModelInfo(
                    id=m.id,
                    name=m.name,
                    provider=provider_name,
                    context_length=m.context_length,
                    pricing={
                        "input_per_million": m.pricing.get("prompt", 0) * 1_000_000,
                        "output_per_million": m.pricing.get("completion", 0) * 1_000_000,
                    },
                    capabilities=capabilities,
                    description=m.description,
                ))

            return result

        except OpenRouterAuthError as e:
            raise ValueError(f"Authentication failed: {str(e)}")
        except OpenRouterError as e:
            raise ValueError(str(e))


def get_settings_service(db: Session) -> SettingsService:
    """Factory function to create a settings service.

    Args:
        db: SQLAlchemy database session

    Returns:
        SettingsService instance.
    """
    return SettingsService(db=db)
