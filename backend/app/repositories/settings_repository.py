"""Settings repository for database operations."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.settings import LLMSettingsModel
from app.schemas.settings import ProviderType
from app.services.secrets_service import SecretsService, InvalidToken

logger = logging.getLogger(__name__)

# Default settings ID (singleton pattern)
DEFAULT_SETTINGS_ID = "default"


class SettingsRepository:
    """Repository for LLM settings persistence.

    Handles CRUD operations for LLM settings with automatic
    encryption/decryption of API keys.
    """

    def __init__(self, db: Session, secrets: SecretsService):
        """Initialize the repository.

        Args:
            db: SQLAlchemy database session
            secrets: Secrets service for API key encryption
        """
        self.db = db
        self.secrets = secrets

    def get_llm_settings(self) -> Optional[LLMSettingsModel]:
        """Get current LLM settings.

        Returns:
            LLMSettingsModel if settings exist, None otherwise.
        """
        return self.db.query(LLMSettingsModel).filter(
            LLMSettingsModel.id == DEFAULT_SETTINGS_ID
        ).first()

    def get_or_create_llm_settings(self) -> LLMSettingsModel:
        """Get existing LLM settings or create default.

        Returns:
            LLMSettingsModel with current or default settings.
        """
        settings = self.get_llm_settings()

        if settings is None:
            logger.info("Creating default LLM settings")
            settings = LLMSettingsModel(
                id=DEFAULT_SETTINGS_ID,
                provider_type=ProviderType.OLLAMA_CONTAINER,
                model="qwen2.5-coder:7b",
                base_url="http://localhost:11434",
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

        return settings

    def save_llm_settings(
        self,
        provider_type: ProviderType,
        model: str,
        base_url: Optional[str] = None,
        api_format: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> LLMSettingsModel:
        """Save LLM settings.

        If an API key is provided, it will be encrypted before storage.

        Args:
            provider_type: The provider type (ollama_container, openrouter_byok, etc.)
            model: The model name/identifier
            base_url: Optional base URL for the provider
            api_format: Optional API format ("ollama" or "openai")
            api_key: Optional plain-text API key (will be encrypted)

        Returns:
            The saved LLMSettingsModel.
        """
        settings = self.get_or_create_llm_settings()

        # Update fields
        settings.provider_type = provider_type
        settings.model = model
        settings.base_url = base_url
        settings.api_format = api_format

        # Encrypt API key if provided
        if api_key is not None:
            if api_key:
                settings.api_key_encrypted = self.secrets.encrypt(api_key)
                logger.debug("API key encrypted and saved")
            else:
                # Empty string means clear the API key
                settings.api_key_encrypted = None
                logger.debug("API key cleared")

        # Reset health check cache on settings change
        settings.last_health_check = None
        settings.last_health_status = None

        self.db.commit()
        self.db.refresh(settings)

        logger.info(
            f"LLM settings saved: provider={provider_type.value}, model={model}"
        )

        return settings

    def get_decrypted_api_key(self, settings: LLMSettingsModel) -> Optional[str]:
        """Decrypt and return the API key.

        Args:
            settings: The LLM settings model with encrypted key

        Returns:
            Decrypted API key string, or None if no key is stored.

        Raises:
            InvalidToken: If the encrypted key is corrupted or tampered with.
        """
        if not settings.api_key_encrypted:
            return None

        try:
            return self.secrets.decrypt(settings.api_key_encrypted)
        except InvalidToken:
            logger.error("Failed to decrypt API key - key may be corrupted")
            raise

    def update_health_status(
        self,
        settings: LLMSettingsModel,
        is_healthy: bool,
    ) -> None:
        """Update the cached health check status.

        Args:
            settings: The settings model to update
            is_healthy: Whether the provider is healthy
        """
        settings.last_health_check = datetime.utcnow()
        settings.last_health_status = is_healthy
        self.db.commit()

    def delete_llm_settings(self) -> bool:
        """Delete LLM settings (reset to default on next access).

        Returns:
            True if settings were deleted, False if none existed.
        """
        settings = self.get_llm_settings()
        if settings:
            self.db.delete(settings)
            self.db.commit()
            logger.info("LLM settings deleted")
            return True
        return False
