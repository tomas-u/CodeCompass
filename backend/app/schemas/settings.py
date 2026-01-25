"""Settings schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict


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
