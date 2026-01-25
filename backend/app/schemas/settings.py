"""Settings schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """LLM provider types for configuration."""

    OLLAMA_CONTAINER = "ollama_container"
    OLLAMA_EXTERNAL = "ollama_external"
    OPENROUTER_BYOK = "openrouter_byok"
    OPENROUTER_MANAGED = "openrouter_managed"


class LLMCapabilities(BaseModel):
    """LLM capabilities."""
    max_context_length: int
    supports_streaming: bool


class LLMSettings(BaseModel):
    """LLM settings."""
    provider: str
    model: str
    status: str = "ready"
    capabilities: Optional[LLMCapabilities] = None
    base_url: Optional[str] = None


class EmbeddingSettings(BaseModel):
    """Embedding settings."""
    model: str
    dimensions: int
    status: str = "ready"


class AnalysisSettings(BaseModel):
    """Analysis settings."""
    supported_languages: List[str]
    max_file_size_mb: int
    max_repo_size_mb: int


class SettingsResponse(BaseModel):
    """Settings response."""
    llm: LLMSettings
    embedding: EmbeddingSettings
    analysis: AnalysisSettings

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    """Settings update request."""
    llm: Optional[LLMSettings] = None


class ProviderInfo(BaseModel):
    """Provider information."""
    id: str
    name: str
    status: str
    models: List[str]


class ProvidersResponse(BaseModel):
    """Providers list response."""
    providers: List[ProviderInfo]


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    parameters: str
    context_length: int


class TestConnectionRequest(BaseModel):
    """Test connection request."""
    provider: str
    model: str
    base_url: Optional[str] = None


class TestConnectionResponse(BaseModel):
    """Test connection response."""
    success: bool
    response_time_ms: int
    model_info: Optional[ModelInfo] = None
    error: Optional[str] = None


# Hardware detection schemas
class GPUInfoResponse(BaseModel):
    """GPU information response."""
    detected: bool
    name: Optional[str] = None
    vendor: Optional[str] = None
    vram_total_gb: Optional[float] = None
    vram_available_gb: Optional[float] = None
    compute_capability: Optional[str] = None


class CPUInfoResponse(BaseModel):
    """CPU information response."""
    name: str
    cores: int
    threads: int
    ram_total_gb: float
    ram_available_gb: float


class ModelRecommendationResponse(BaseModel):
    """Model recommendation response."""
    name: str
    reason: str


class RecommendationsResponse(BaseModel):
    """Hardware recommendations response."""
    max_model_params: str
    recommended_models: List[ModelRecommendationResponse]
    inference_mode: str


class HardwareInfoResponse(BaseModel):
    """Hardware information response."""
    gpu: GPUInfoResponse
    cpu: CPUInfoResponse
    recommendations: RecommendationsResponse


# LLM Configuration schemas for persistence
class LLMConfigUpdate(BaseModel):
    """Request to update LLM configuration."""

    provider_type: ProviderType = Field(
        ...,
        description="Type of LLM provider",
    )
    model: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Model name/identifier",
    )
    base_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Base URL for the provider API",
    )
    api_format: Optional[Literal["ollama", "openai"]] = Field(
        None,
        description="API format for external LLM providers",
    )
    api_key: Optional[str] = Field(
        None,
        description="API key (plain text, will be encrypted before storage)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "provider_type": "openrouter_byok",
                "model": "anthropic/claude-3-haiku",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "sk-or-v1-xxxxx",
            }
        }


class LLMConfigResponse(BaseModel):
    """Response with LLM configuration."""

    provider_type: ProviderType = Field(
        ...,
        description="Type of LLM provider",
    )
    model: str = Field(
        ...,
        description="Model name/identifier",
    )
    base_url: Optional[str] = Field(
        None,
        description="Base URL for the provider API",
    )
    api_format: Optional[str] = Field(
        None,
        description="API format (ollama or openai)",
    )
    has_api_key: bool = Field(
        False,
        description="Whether an API key is configured (never returns actual key)",
    )
    status: str = Field(
        "unknown",
        description="Current provider status",
    )
    last_health_check: Optional[datetime] = Field(
        None,
        description="Timestamp of last health check",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "provider_type": "ollama_container",
                "model": "qwen2.5-coder:7b",
                "base_url": "http://localhost:11434",
                "has_api_key": False,
                "status": "ready",
                "last_health_check": "2024-01-25T12:00:00Z",
            }
        }
