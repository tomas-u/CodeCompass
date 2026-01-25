"""FastAPI application entry point."""

import time
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import projects, analysis, reports, diagrams, files, search, chat, settings_routes, admin
from app.database import init_db, SessionLocal
from app.services.llm import reload_provider, close_providers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug,
)


# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and LLM provider on application startup."""
    init_db()
    print(f"✓ Database initialized: {settings.database_name}")

    # Initialize LLM provider from persisted settings
    await initialize_llm_from_settings()


async def initialize_llm_from_settings():
    """Initialize LLM provider from database settings or environment defaults."""
    try:
        from app.repositories.settings_repository import SettingsRepository
        from app.services.secrets_service import get_secrets_service

        db = SessionLocal()
        try:
            secrets = get_secrets_service()
            repo = SettingsRepository(db=db, secrets=secrets)
            settings_model = repo.get_llm_settings()

            if settings_model:
                # Decrypt API key if present
                api_key = None
                if settings_model.api_key_encrypted:
                    try:
                        api_key = repo.get_decrypted_api_key(settings_model)
                    except Exception as e:
                        logging.warning(f"Failed to decrypt API key, using without: {e}")

                # Build config from database settings
                config = {
                    "provider_type": settings_model.provider_type.value,
                    "model": settings_model.model,
                    "base_url": settings_model.base_url,
                    "api_key": api_key,
                }

                await reload_provider(config)
                print(
                    f"✓ LLM provider initialized from settings: "
                    f"{settings_model.provider_type.value} / {settings_model.model}"
                )
            else:
                # No saved settings, use environment defaults
                print("✓ LLM provider using environment defaults (no saved settings)")

        finally:
            db.close()

    except Exception as e:
        logging.warning(f"Could not initialize LLM from settings: {e}")
        print("✓ LLM provider using environment defaults")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    await close_providers()
    print("✓ Providers closed")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track uptime
start_time = time.time()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "docs_url": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint with actual Ollama status."""
    uptime = int(time.time() - start_time)

    # Default values
    llm_status = "unknown"
    llm_model_loaded = None
    available_models = []

    # Query Ollama for actual status
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is reachable
            tags_response = await client.get(f"{settings.llm_base_url}/api/tags")
            if tags_response.status_code == 200:
                llm_status = "connected"
                tags_data = tags_response.json()
                available_models = [m.get("name") for m in tags_data.get("models", [])]

            # Check which model is currently loaded
            ps_response = await client.get(f"{settings.llm_base_url}/api/ps")
            if ps_response.status_code == 200:
                ps_data = ps_response.json()
                loaded_models = ps_data.get("models", [])
                if loaded_models:
                    llm_model_loaded = loaded_models[0].get("name")
                    llm_status = "ready"
                else:
                    llm_status = "idle"  # Connected but no model loaded
    except Exception as e:
        llm_status = "unavailable"

    return {
        "status": "healthy",
        "version": settings.version,
        "uptime_seconds": uptime,
        "llm_provider": settings.llm_provider,
        "llm_model_configured": settings.llm_model,
        "llm_model_loaded": llm_model_loaded,
        "llm_models_available": available_models,
        "llm_status": llm_status
    }


# Include API routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(analysis.router, prefix="/api/projects", tags=["analysis"])
app.include_router(reports.router, prefix="/api/projects", tags=["reports"])
app.include_router(diagrams.router, prefix="/api/projects", tags=["diagrams"])
app.include_router(files.router, prefix="/api/projects", tags=["files"])
app.include_router(search.router, prefix="/api/projects", tags=["search"])
app.include_router(chat.router, prefix="/api/projects", tags=["chat"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["settings"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found",
                "details": {"path": str(request.url.path)}
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
