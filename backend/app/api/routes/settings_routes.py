"""Settings API endpoints."""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
    HardwareInfoResponse,
    GPUInfoResponse,
    CPUInfoResponse,
    RecommendationsResponse,
    ModelRecommendationResponse,
    LLMConfigUpdate,
    LLMConfigResponse,
    LLMConfigUpdateResponse,
    LLMValidationResponse,
    ValidationDetailsResponse,
    OpenRouterModelsResponse,
    OpenRouterModel,
    OpenRouterPricing,
)
from app.config import settings
from app.database import get_db
from app.services.llm import get_llm_provider, get_embedding_provider, reload_provider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.hardware_service import detect_hardware
from app.services.settings_service import get_settings_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Additional schemas for model management
class ModelListResponse(BaseModel):
    """Response with list of models."""
    models: List[dict]


class ModelPullRequest(BaseModel):
    """Request to pull a model."""
    model: str


class ModelPullResponse(BaseModel):
    """Response from model pull."""
    success: bool
    model: str
    message: str


class ModelDeleteRequest(BaseModel):
    """Request to delete a model."""
    model: str


class ServiceStatusResponse(BaseModel):
    """Response with service status."""
    llm: dict
    embedding: dict


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings."""
    # Check actual service status
    llm = get_llm_provider()
    embedding = get_embedding_provider()

    llm_healthy = await llm.health_check()
    embedding_healthy = await embedding.health_check()

    return SettingsResponse(
        llm=LLMSettings(
            provider=settings.llm_provider,
            model=settings.llm_model,
            status="ready" if llm_healthy else "unavailable",
            capabilities=LLMCapabilities(
                max_context_length=4096,
                supports_streaming=True
            ),
            base_url=settings.llm_base_url
        ),
        embedding=EmbeddingSettings(
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            status="ready" if embedding_healthy else "unavailable"
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
    llm = get_llm_provider()
    llm_healthy = await llm.health_check()

    # Get models from Ollama if available
    ollama_models = []
    if llm_healthy and isinstance(llm, OllamaProvider):
        models = await llm.list_models()
        ollama_models = [m.name for m in models]

    providers = [
        ProviderInfo(
            id="ollama",
            name="Ollama",
            status="ready" if llm_healthy else "unavailable",
            models=ollama_models
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
    start_time = time.time()

    llm = get_llm_provider()

    try:
        # Try to generate a simple response
        if isinstance(llm, OllamaProvider):
            result = await llm.generate("Say 'Hello' in one word.", model=request.model)
            response_time_ms = int((time.time() - start_time) * 1000)

            return TestConnectionResponse(
                success=True,
                response_time_ms=response_time_ms,
                model_info=ModelInfo(
                    name=request.model,
                    parameters="Unknown",
                    context_length=4096
                )
            )
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return TestConnectionResponse(
            success=False,
            response_time_ms=int((time.time() - start_time) * 1000),
            error=str(e)
        )

    return TestConnectionResponse(
        success=False,
        response_time_ms=int((time.time() - start_time) * 1000),
        error="Provider not supported for testing"
    )


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """Get status of LLM and embedding services."""
    llm = get_llm_provider()
    embedding = get_embedding_provider()

    llm_healthy = await llm.health_check()
    embedding_healthy = await embedding.health_check()

    llm_status = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "healthy": llm_healthy,
        "status": "ready" if llm_healthy else "unavailable"
    }

    embedding_status = {
        "model": settings.embedding_model,
        "base_url": settings.embedding_base_url,
        "dimensions": settings.embedding_dimensions,
        "healthy": embedding_healthy,
        "status": "ready" if embedding_healthy else "unavailable"
    }

    return ServiceStatusResponse(llm=llm_status, embedding=embedding_status)


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """List available models from Ollama."""
    llm = get_llm_provider()

    if not isinstance(llm, OllamaProvider):
        raise HTTPException(status_code=400, detail="Model listing only supported for Ollama")

    is_healthy = await llm.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="Ollama service is not available")

    models = await llm.list_models()

    return ModelListResponse(
        models=[
            {
                "name": m.name,
                "size": m.size,
                "modified_at": m.modified_at,
                "details": m.details
            }
            for m in models
        ]
    )


@router.post("/models/pull", response_model=ModelPullResponse)
async def pull_model(request: ModelPullRequest, background_tasks: BackgroundTasks):
    """Pull a model from Ollama library.

    Note: This starts the pull in the background as it can take a long time.
    """
    llm = get_llm_provider()

    if not isinstance(llm, OllamaProvider):
        raise HTTPException(status_code=400, detail="Model pulling only supported for Ollama")

    is_healthy = await llm.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="Ollama service is not available")

    # Start the pull in the background
    async def do_pull():
        try:
            success = await llm.pull_model(request.model)
            if success:
                logger.info(f"Successfully pulled model: {request.model}")
            else:
                logger.error(f"Failed to pull model: {request.model}")
        except Exception as e:
            logger.error(f"Error pulling model {request.model}: {e}")

    background_tasks.add_task(do_pull)

    return ModelPullResponse(
        success=True,
        model=request.model,
        message=f"Started pulling model '{request.model}'. This may take several minutes."
    )


@router.delete("/models/{model_name}", response_model=ModelPullResponse)
async def delete_model(model_name: str):
    """Delete a model from Ollama."""
    llm = get_llm_provider()

    if not isinstance(llm, OllamaProvider):
        raise HTTPException(status_code=400, detail="Model deletion only supported for Ollama")

    is_healthy = await llm.health_check()
    if not is_healthy:
        raise HTTPException(status_code=503, detail="Ollama service is not available")

    success = await llm.delete_model(model_name)

    if success:
        return ModelPullResponse(
            success=True,
            model=model_name,
            message=f"Successfully deleted model '{model_name}'"
        )
    else:
        raise HTTPException(status_code=500, detail=f"Failed to delete model '{model_name}'")


@router.get("/hardware", response_model=HardwareInfoResponse)
async def get_hardware_info():
    """Get hardware information and model recommendations.

    Detects GPU, CPU, and RAM to provide intelligent model recommendations.
    """
    hardware = await detect_hardware()

    return HardwareInfoResponse(
        gpu=GPUInfoResponse(
            detected=hardware.gpu.detected,
            name=hardware.gpu.name,
            vendor=hardware.gpu.vendor,
            vram_total_gb=hardware.gpu.vram_total_gb,
            vram_available_gb=hardware.gpu.vram_available_gb,
            compute_capability=hardware.gpu.compute_capability,
        ),
        cpu=CPUInfoResponse(
            name=hardware.cpu.name,
            cores=hardware.cpu.cores,
            threads=hardware.cpu.threads,
            ram_total_gb=hardware.cpu.ram_total_gb,
            ram_available_gb=hardware.cpu.ram_available_gb,
        ),
        recommendations=RecommendationsResponse(
            max_model_params=hardware.recommendations.max_model_params,
            recommended_models=[
                ModelRecommendationResponse(name=m.name, reason=m.reason)
                for m in hardware.recommendations.recommended_models
            ],
            inference_mode=hardware.recommendations.inference_mode,
        ),
    )


# -------------------------------------------------------------------------
# LLM Configuration Endpoints (Issue #83)
# -------------------------------------------------------------------------


@router.get("/llm", response_model=LLMConfigResponse)
async def get_llm_config(db: Session = Depends(get_db)):
    """Get current LLM configuration.

    Returns the current LLM settings without exposing the API key.
    """
    service = get_settings_service(db)
    settings_model = service.get_or_create_settings()

    # Determine status based on cached health check
    status = "unknown"
    if settings_model.last_health_status is not None:
        status = "ready" if settings_model.last_health_status else "unavailable"

    return LLMConfigResponse(
        provider_type=settings_model.provider_type,
        model=settings_model.model,
        base_url=settings_model.base_url,
        api_format=settings_model.api_format,
        has_api_key=bool(settings_model.api_key_encrypted),
        status=status,
        last_health_check=settings_model.last_health_check,
    )


@router.put("/llm", response_model=LLMConfigUpdateResponse)
async def update_llm_config(
    config: LLMConfigUpdate,
    db: Session = Depends(get_db),
):
    """Update LLM configuration with hot-reload.

    Saves the new configuration and reloads the LLM provider
    so changes take effect immediately without restart.
    """
    service = get_settings_service(db)

    # Save settings
    settings_model = service.save_settings(
        provider_type=config.provider_type,
        model=config.model,
        base_url=config.base_url,
        api_format=config.api_format,
        api_key=config.api_key,
    )

    # Hot-reload: Properly close existing provider and create new one with updated config
    new_provider = await reload_provider({
        "provider_type": config.provider_type.value,
        "model": config.model,
        "base_url": config.base_url,
        "api_key": config.api_key,
    })

    # Run health check so GET /api/settings/llm returns accurate status immediately
    try:
        healthy = await new_provider.health_check()
        service.repository.update_health_status(settings_model, healthy)
        status = "ready" if healthy else "unavailable"
    except Exception as e:
        logger.warning(f"Health check after reload failed: {e}")
        service.repository.update_health_status(settings_model, False)
        status = "unavailable"

    logger.info(
        f"LLM config updated: provider={config.provider_type.value}, model={config.model}"
    )

    return LLMConfigUpdateResponse(
        success=True,
        provider_type=settings_model.provider_type,
        model=settings_model.model,
        status=status,
        reloaded=True,
    )


@router.post("/llm/validate", response_model=LLMValidationResponse)
async def validate_llm_config(
    config: LLMConfigUpdate,
    db: Session = Depends(get_db),
):
    """Validate LLM configuration before saving.

    Tests the connection to the provider and verifies the model is available.
    Does not save the configuration.
    """
    service = get_settings_service(db)

    result = await service.test_connection(
        provider_type=config.provider_type,
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        api_format=config.api_format,
    )

    # Convert details to response schema
    details = None
    if result.details:
        details = ValidationDetailsResponse(
            model_name=result.details.get("model_name"),
            context_length=result.details.get("context_length"),
            pricing=result.details.get("pricing"),
            available_models=result.details.get("available_models"),
            model_count=result.details.get("model_count"),
        )

    return LLMValidationResponse(
        valid=result.valid,
        provider_status=result.provider_status,
        model_available=result.model_available,
        test_response_ms=result.test_response_ms,
        error=result.error,
        details=details,
    )


@router.get("/openrouter/models", response_model=OpenRouterModelsResponse)
async def list_openrouter_models(
    x_openrouter_key: Optional[str] = Header(None, alias="X-OpenRouter-Key"),
    db: Session = Depends(get_db),
):
    """List available OpenRouter models.

    Requires a valid OpenRouter API key, either:
    - In the X-OpenRouter-Key header (for browsing before save)
    - Or from stored settings (if already configured)

    Returns models with pricing information.
    """
    from app.services.secrets_service import InvalidToken

    service = get_settings_service(db)

    # Get API key from header or stored settings
    api_key = x_openrouter_key
    if not api_key:
        # Try to get from stored settings
        settings_model = service.get_current_settings()
        if settings_model and settings_model.api_key_encrypted:
            try:
                api_key = service.get_decrypted_api_key(settings_model)
            except InvalidToken:
                logger.error("Failed to decrypt stored API key - may be corrupted")
                raise HTTPException(
                    status_code=500,
                    detail="Stored API key is corrupted. Please reconfigure your OpenRouter settings.",
                )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="OpenRouter API key required. Provide via X-OpenRouter-Key header or configure in settings.",
        )

    try:
        models = await service.list_openrouter_models(api_key)

        return OpenRouterModelsResponse(
            models=[
                OpenRouterModel(
                    id=m.id,
                    name=m.name,
                    provider=m.provider,
                    context_length=m.context_length,
                    pricing=OpenRouterPricing(
                        input_per_million=m.pricing.get("input_per_million", 0),
                        output_per_million=m.pricing.get("output_per_million", 0),
                    ),
                    capabilities=m.capabilities,
                    description=m.description,
                )
                for m in models
            ]
        )

    except ValueError as e:
        error_msg = str(e)
        if "Authentication failed" in error_msg:
            raise HTTPException(status_code=401, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
