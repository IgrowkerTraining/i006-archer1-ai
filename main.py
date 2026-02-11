"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1 import api_router
from app.models.schemas import RootResponse
from app.services.ai_service import ai_service

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    await ai_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI template with OpenRouter AI integration",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routers
app.include_router(api_router)


@app.get("/", response_model=RootResponse)
async def read_root():
    """Root endpoint with basic information."""
    return RootResponse(
        message=f"Welcome to {settings.app_name}",
        version=settings.app_version,
        docs="/docs",
        health="/api/v1/health"
    )


# Legacy endpoint for backward compatibility
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Example endpoint from original template."""
    return {"item_id": item_id, "q": q}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
