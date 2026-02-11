"""Chat-related API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.schemas import ChatRequest, ChatResponse, ModelInfo
from app.services.ai_service import AIService
from app.api.dependencies import get_ai_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Create a chat completion using OpenRouter API.
    
    - **model**: AI model to use (e.g., "openai/gpt-3.5-turbo")
    - **messages**: List of chat messages
    - **max_tokens**: Maximum tokens to generate (1-4096)
    - **temperature**: Sampling temperature (0.0-2.0)
    - **stream**: Enable streaming response (not yet implemented)
    """
    try:
        logger.info(f"Chat completion request for model: {request.model}")
        response = await ai_service.chat_completion(request)
        return response
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[ModelInfo])
async def list_models(ai_service: AIService = Depends(get_ai_service)):
    """
    List all available AI models from OpenRouter.
    
    Returns a list of available models with their information.
    """
    try:
        models = await ai_service.list_models()
        return models
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
