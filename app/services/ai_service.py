"""AI service for OpenRouter integration."""

import httpx
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config.settings import settings
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage, ModelInfo
from app.core.logging import get_logger
from app.core.security import mask_api_key

logger = get_logger(__name__)


class AIService:
    """Service for interacting with OpenRouter API."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-username/template-python-fastapi",
                "X-Title": settings.app_name,
            },
            timeout=settings.ai_request_timeout
        )
        logger.info(f"AI Service initialized with API key: {mask_api_key(settings.openrouter_api_key)}")
        logger.info(f"Default AI model: {settings.default_ai_model}")
        logger.info(f"Request timeout: {settings.ai_request_timeout}s")
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Create a chat completion using OpenRouter API."""
        
        # Convert ChatMessage objects to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream,
        }
        
        try:
            logger.info(f"Sending chat completion request for model: {request.model}")
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            chat_response = ChatResponse(
                id=data.get("id", str(uuid.uuid4())),
                created=data.get("created", int(datetime.now().timestamp())),
                model=data.get("model", request.model),
                choices=data.get("choices", []),
                usage=data.get("usage")
            )
            
            logger.info(f"Chat completion successful: {chat_response.id}")
            return chat_response
            
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException:
            error_msg = f"OpenRouter API timeout after {settings.ai_request_timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error calling OpenRouter API: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def generar_respuesta(self, prompt: str, modelo: Optional[str] = None) -> dict:
        """
        Generate a response from OpenRouter using a prompt string.
        
        Returns dict with keys: respuesta (str), latencia (float), modelo (str), error (str|None)
        """
        modelo = modelo or settings.default_ai_model
        start_time = time.time()
        
        request = ChatRequest(
            model=modelo,
            messages=[
                ChatMessage(role="user", content=prompt)
            ],
            max_tokens=4096,
            temperature=0.3,
            stream=False,
        )
        
        try:
            logger.info(f"Generating response with model: {modelo}")
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            chat_response = await self.chat_completion(request)
            latencia = round(time.time() - start_time, 3)
            
            # Extract text from response
            respuesta_texto = ""
            if chat_response.choices:
                choice = chat_response.choices[0]
                message = choice.get("message", {})
                respuesta_texto = message.get("content", "")
            
            # Detect empty response (model returned nothing useful)
            if not respuesta_texto or not respuesta_texto.strip():
                logger.warning(f"Model {modelo} returned empty response after {latencia}s")
                return {
                    "respuesta": "",
                    "latencia": latencia,
                    "modelo": modelo,
                    "error": f"El modelo {modelo} devolvió una respuesta vacía después de {latencia}s. "
                             f"Posible timeout parcial o modelo no disponible.",
                }
            
            logger.info(f"Response generated in {latencia}s ({len(respuesta_texto)} chars)")
            
            return {
                "respuesta": respuesta_texto,
                "latencia": latencia,
                "modelo": modelo,
                "error": None,
            }
            
        except Exception as e:
            latencia = round(time.time() - start_time, 3)
            error_msg = str(e)
            logger.error(f"Error generating response ({latencia}s): {error_msg}")
            return {
                "respuesta": "",
                "latencia": latencia,
                "modelo": modelo,
                "error": error_msg,
            }
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenRouter."""
        try:
            logger.info("Fetching available models from OpenRouter")
            response = await self.client.get("/models")
            response.raise_for_status()
            
            data = response.json()
            models_data = data.get("data", [])
            
            models = [
                ModelInfo(
                    id=model.get("id", ""),
                    name=model.get("name"),
                    description=model.get("description"),
                    pricing=model.get("pricing")
                )
                for model in models_data
            ]
            
            logger.info(f"Retrieved {len(models)} models")
            return models
            
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error fetching models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        try:
            # Try to fetch models as a simple health check
            await self.list_models()
            return True
        except Exception as e:
            logger.error(f"AI service health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("AI service client closed")


# Global AI service instance
ai_service = AIService()
