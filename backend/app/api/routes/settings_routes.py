"""Settings API endpoints."""

from fastapi import APIRouter

from app.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
    ProvidersResponse,
    ProviderInfo,
    TestConnectionRequest,
    TestConnectionResponse,
    LLMSettings,
    LLMCapabilities,
    EmbeddingSettings,
    AnalysisSettings,
    ModelInfo,
)
from app.config import settings

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings."""
    return SettingsResponse(
        llm=LLMSettings(
            provider=settings.llm_provider,
            model=settings.llm_model,
            status="ready",
            capabilities=LLMCapabilities(
                max_context_length=4096,
                supports_streaming=True
            )
        ),
        embedding=EmbeddingSettings(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            status="ready"
        ),
        analysis=AnalysisSettings(
            supported_languages=["python", "javascript", "typescript"],
            max_file_size_mb=settings.max_file_size_mb,
            max_repo_size_mb=settings.max_repo_size_mb
        )
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """Update settings."""
    # In MVP, just return current settings
    # In real implementation, would update configuration
    return await get_settings()


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """List available LLM providers."""
    providers = [
        ProviderInfo(
            id="local",
            name="Local (HuggingFace)",
            status="ready",
            models=["microsoft/Phi-3.5-mini-instruct"]
        ),
        ProviderInfo(
            id="ollama",
            name="Ollama",
            status="available",
            models=[]
        ),
        ProviderInfo(
            id="lmstudio",
            name="LM Studio",
            status="unavailable",
            models=[]
        ),
    ]

    return ProvidersResponse(providers=providers)


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """Test LLM connection."""
    # Mock successful test
    return TestConnectionResponse(
        success=True,
        response_time_ms=1500,
        model_info=ModelInfo(
            name=request.model,
            parameters="3B",
            context_length=8192
        )
    )
