"""Settings API endpoints."""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

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
from app.services.llm import get_llm_provider, get_embedding_provider
from app.services.llm.ollama_provider import OllamaProvider

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
