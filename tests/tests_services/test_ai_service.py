import pytest
from unittest.mock import MagicMock, AsyncMock  # MagicMock para objetos, AsyncMock para async functions
from app.services.ai_service import AIService
from app.models.schemas import ChatRequest, ChatMessage
from httpx import TimeoutException


# Test para AIService.chat_completion (método principal)
@pytest.mark.asyncio  # Marca como async test (necesario para await)
async def test_chat_completion_success(mock_settings, mock_httpx_client):
    # Setup: Crear instancia de AIService con settings mockeados
    service = AIService()  # Instancia real, pero inyectamos mocks
    service.client = mock_httpx_client  # Reemplaza cliente real con mock (de conftest.py)
    
    # Configurar mock para simular respuesta exitosa de OpenRouter
    mock_response = MagicMock()
    mock_response.json.return_value = {  # Simula JSON de API
        "id": "test_id",
        "created": 123456,
        "model": "test-model",
        "choices": [{"message": {"content": "Respuesta IA"}}],
        "usage": {"tokens": 100}
    }
    mock_response.raise_for_status = MagicMock()  # Simula no error HTTP
    mock_httpx_client.post = AsyncMock(return_value=mock_response)  # Mockea POST async
    
    # Act: Llamar al método con request válido
    request = ChatRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hola")]
    )
    result = await service.chat_completion(request)  # Await porque es async
    
    # Assert: Verificar resultado
    assert result.id == "test_id"  # Debe devolver lo mockeado
    assert result.choices[0]["message"]["content"] == "Respuesta IA"
    mock_httpx_client.post.assert_called_once()  # Verifica que se llamó POST una vez

@pytest.mark.asyncio
async def test_chat_completion_timeout(mock_settings, mock_httpx_client):
    # Setup
    service = AIService()
    service.client = mock_httpx_client
    
    # Configurar mock para timeout
    mock_httpx_client.post = AsyncMock(side_effect=TimeoutException("Timeout"))  # Simula error
    
    # Act & Assert: Debe lanzar Exception
    request = ChatRequest(model="test-model", messages=[ChatMessage(role="user", content="Hola")])
    with pytest.raises(Exception, match="OpenRouter timeout"):  # Espera error con mensaje
        await service.chat_completion(request)

# Test para generar_respuesta (método de texto)
@pytest.mark.asyncio
async def test_generar_respuesta_success(mock_settings, mock_httpx_client):
    # Setup
    service = AIService()
    service.client = mock_httpx_client
    
    # Mock respuesta de chat_completion
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Respuesta generada"}}]
    }
    mock_httpx_client.post = AsyncMock(return_value=mock_response)
    
    # Act
    result = await service.generar_respuesta("Prompt test")
    
    # Assert
    assert result["respuesta"] == "Respuesta generada"
    assert "latencia" in result  # Debe incluir latencia
    assert result["error"] is None  # Sin error

# Test para list_models
@pytest.mark.asyncio
async def test_list_models_success(mock_settings, mock_httpx_client):
    # Setup
    service = AIService()
    service.client = mock_httpx_client
    
    # Mock respuesta de /models
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "model1", "name": "Model 1"}]}
    mock_httpx_client.get = AsyncMock(return_value=mock_response)
    
    # Act
    models = await service.list_models()
    
    # Assert
    assert len(models) == 1
    assert models[0].id == "model1"