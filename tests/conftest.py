# Definición de fixtures para settings y mocks de clientes HTTP y Supabase.

import pytest
from unittest.mock import MagicMock
from app.config.settings import Settings


@pytest.fixture
def mock_settings():
    # Fixture que proporciona una instancia de Settings con valores dummy para tests, evitando .env real.
    return Settings(
        app_name="Test App",
        app_version="1.0.0-test",
        debug=True,
        openrouter_api_key="dummy_api_key_for_tests",  # Clave falsa, no llama a API real
        openrouter_base_url="https://mock.openrouter.ai/api/v1",  # URL mock para httpx
        default_ai_model="test-model",
        ai_request_timeout=5.0,  # Timeout corto para tests rápidos
        supabase_url="https://mock.supabase.co",  # URL falsa
        supabase_anon_key="dummy_supabase_key",  # Clave falsa
        api_host="127.0.0.1",
        api_port=8000,
        cors_origins=["http://localhost:3000"],  # Restringido para tests
        cors_allow_credentials=False,  # Deshabilitado para simplicidad
        log_level="DEBUG",  # Más verbose en tests
    )


@pytest.fixture
def mock_httpx_client():
    # Fixture que proporciona un cliente httpx mockeado para simular respuestas HTTP de OpenRouter.
    client = MagicMock()
    return client


@pytest.fixture
def mock_supabase_client():
    # Fixture que proporciona un cliente Supabase mockeado para tests de DB.
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "test_id"}] # Simula una respuesta exitosa de insert.
    return client