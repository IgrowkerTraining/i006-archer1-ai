"""Health check API endpoints."""

from fastapi import APIRouter
from datetime import datetime

from app.models.schemas import HealthResponse
from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the service.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        message="Service is running normally"
    )
