"""API dependencies and utilities."""

from app.services.ai_service import ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_ai_service():
    """Return the global AI service instance."""
    return ai_service
