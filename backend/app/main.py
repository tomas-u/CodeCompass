"""FastAPI application entry point."""

import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import projects, analysis, reports, diagrams, files, search, chat, settings_routes, admin
from app.database import init_db

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
    """Initialize database on application startup."""
    init_db()
    print(f"✓ Database initialized: {settings.database_name}")

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
    """Health check endpoint."""
    uptime = int(time.time() - start_time)
    return {
        "status": "healthy",
        "version": settings.version,
        "uptime_seconds": uptime,
        "llm_provider": settings.llm_provider,
        "llm_status": "ready"
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
