"""Settings database models."""

from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func

from app.database import Base


class ProviderType(str, Enum):
    """LLM provider types."""

    OLLAMA_CONTAINER = "ollama_container"
    OLLAMA_EXTERNAL = "ollama_external"
    OPENROUTER_BYOK = "openrouter_byok"
    OPENROUTER_MANAGED = "openrouter_managed"


class LLMSettingsModel(Base):
    """Persistent LLM settings.

    Stores the user's LLM configuration including provider type, model,
    and encrypted API keys for cloud providers.
    """

    __tablename__ = "llm_settings"

    # Primary key - use "default" for singleton pattern
    id = Column(String(50), primary_key=True, default="default")

    # Provider configuration
    provider_type = Column(
        String(50),
        nullable=False,
        default=ProviderType.OLLAMA_CONTAINER.value,
    )
    model = Column(String(200), nullable=False, default="qwen2.5-coder:7b")
    base_url = Column(String(500), nullable=True)
    api_format = Column(String(20), nullable=True)  # "ollama" or "openai"

    # Encrypted API key (for OpenRouter providers)
    api_key_encrypted = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    # Health check cache
    last_health_check = Column(DateTime, nullable=True)
    last_health_status = Column(Boolean, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LLMSettingsModel(id={self.id}, provider_type={self.provider_type}, "
            f"model={self.model})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary (excludes encrypted API key)."""
        return {
            "id": self.id,
            "provider_type": self.provider_type,
            "model": self.model,
            "base_url": self.base_url,
            "api_format": self.api_format,
            "has_api_key": bool(self.api_key_encrypted),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_health_check": self.last_health_check,
            "last_health_status": self.last_health_status,
        }
