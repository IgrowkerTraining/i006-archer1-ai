"""AI service for OpenRouter integration."""

import httpx
import time
import uuid
from datetime import datetime
from typing import List, Optional

from app.config.settings import settings
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage, ModelInfo
from app.core.logging import get_logger
from app.core.security import mask_api_key

logger = get_logger(__name__)


class AIService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/igrowker/i006-archer1-ai",
                "X-Title": settings.app_name,
            },
            timeout=settings.ai_request_timeout,
        )
        logger.info(f"AIService inicializado | key: {mask_api_key(settings.openrouter_api_key)}")
        logger.info(f"Modelo: {settings.default_ai_model} | Timeout: {settings.ai_request_timeout}s")

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        # Envía request a OpenRouter /chat/completions
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            return ChatResponse(
                id=data.get("id", str(uuid.uuid4())),
                created=data.get("created", int(datetime.now().timestamp())),
                model=data.get("model", request.model),
                choices=data.get("choices", []),
                usage=data.get("usage"),
            )
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.TimeoutException:
            error_msg = f"OpenRouter timeout después de {settings.ai_request_timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error llamando OpenRouter: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def generar_respuesta(self, prompt: str, modelo: Optional[str] = None) -> dict:
        # Genera una respuesta de texto a partir de un prompt
        modelo = modelo or settings.default_ai_model
        start_time = time.time()

        request = ChatRequest(
            model=modelo,
            messages=[ChatMessage(role="user", content=prompt)],
            max_tokens=4096,
            temperature=0.3,
            stream=False,
        )

        try:
            chat_response = await self.chat_completion(request)
            latencia = round(time.time() - start_time, 3)

            # Extraer texto de la respuesta
            respuesta_texto = ""
            if chat_response.choices:
                choice = chat_response.choices[0]
                message = choice.get("message", {})
                respuesta_texto = message.get("content", "")

            # Detectar respuesta vacía
            if not respuesta_texto or not respuesta_texto.strip():
                logger.warning(f"Modelo {modelo} devolvió respuesta vacía ({latencia}s)")
                return {
                    "respuesta": "",
                    "latencia": latencia,
                    "modelo": modelo,
                    "error": f"El modelo {modelo} devolvió respuesta vacía después de {latencia}s",
                }

            logger.info(f"Respuesta generada en {latencia}s ({len(respuesta_texto)} chars)")
            return {
                "respuesta": respuesta_texto,
                "latencia": latencia,
                "modelo": modelo,
                "error": None,
            }

        except Exception as e:
            latencia = round(time.time() - start_time, 3)
            logger.error(f"Error generando respuesta ({latencia}s): {e}")
            return {
                "respuesta": "",
                "latencia": latencia,
                "modelo": modelo,
                "error": str(e),
            }

    async def list_models(self) -> List[ModelInfo]:
        # Obtiene lista de modelos de OpenRouter
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()

            return [
                ModelInfo(
                    id=m.get("id", ""),
                    name=m.get("name"),
                    description=m.get("description"),
                    pricing=m.get("pricing"),
                )
                for m in data.get("data", [])
            ]
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            raise

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception as e:
            logger.error(f"Health check fallido: {e}")
            return False

    async def close(self):
        await self.client.aclose()
        logger.info("AIService cerrado")


# Instancia global
ai_service = AIService()
