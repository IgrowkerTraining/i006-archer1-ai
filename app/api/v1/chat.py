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
    """Crea una finalización de chat usando la API de OpenRouter."""
    try:
        logger.info(f"Solicitud de finalización de chat para el modelo: {request.model}")
        response = await ai_service.chat_completion(request)
        return response
    except Exception as e:
        logger.error(f"Error en la finalización de chat : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """Lista los modelos de IA disponibles en OpenRouter."""
    try:
        models = await ai_service.list_models()
        return models
    except Exception as e:
        logger.error(f"Error obteniendo modelos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
