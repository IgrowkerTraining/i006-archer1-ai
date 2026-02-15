"""Chat-related API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import ChatRequest, ChatResponse, ModelInfo
from app.services.ai_service import ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(request: ChatRequest):
    """Create a chat completion using OpenRouter API."""
    try:
        logger.info(f"Chat completion request for model: {request.model}")
        response = await ai_service.chat_completion(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List available AI models from OpenRouter."""
    try:
        models = await ai_service.list_models()
        return models
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
