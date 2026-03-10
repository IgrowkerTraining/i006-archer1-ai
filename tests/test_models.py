import pytest
from pydantic import ValidationError
from app.models.schemas import ChatRequest, ChatMessage, ActivityInput, ResumenRequest, TechnicianInfo, ObservationInput

# Test para ChatRequest (modelo de chat con IA)
def test_chat_request_valid():
    # Caso válido: Datos correctos
    request = ChatRequest(
        model="test-model",
        messages=[ChatMessage(role="user", content="Hola")],
        max_tokens=100,
        temperature=0.5
    )
    assert request.model == "test-model"
    assert len(request.messages) == 1
    assert request.max_tokens == 100
    # Pydantic valida automáticamente rangos/tipos

def test_chat_request_invalid_max_tokens():
    # Caso inválido: max_tokens fuera de rango
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(
            model="test-model",
            messages=[ChatMessage(role="user", content="Hola")],
            max_tokens=5000  # > 4096, inválido
        )
    assert "max_tokens" in str(exc_info.value)  # Confirma que el error es por max_tokens

def test_chat_request_invalid_temperature():
    # Caso inválido: temperature fuera de rango
    with pytest.raises(ValidationError):
        ChatRequest(
            model="test-model",
            messages=[ChatMessage(role="user", content="Hola")],
            temperature=3.0  # > 2.0, inválido
        )

# Test para ActivityInput (actividad agrícola)
def test_activity_input_valid():
    # Caso válido
    activity = ActivityInput(
        activitytype="Siembra",
        plot="Parcela 1",
        crop="Maíz",
        date_day="15",
        date_month="05",
        date_year="2023",
        responsible="Juan",
        description="Siembra inicial",
        observations=[ObservationInput(technician=TechnicianInfo(name="Ana"), description="Todo bien")]
    )
    assert activity.activitytype == "Siembra"
    assert activity.observations[0].technician.name == "Ana"  # Accede como objeto
    assert activity.observations[0].description == "Todo bien"

def test_activity_input_missing_required():
    # Caso inválido: Falta campo obligatorio
    with pytest.raises(ValidationError):
        ActivityInput(
            # Falta activitytype
            plot="Parcela 1",
            crop="Maíz",
            date_day="15",
            date_month="05",
            date_year="2023",
            responsible="Juan",
            description="Siembra inicial"
        )

# Test para ResumenRequest (request para generar resumen)
def test_resumen_request_valid():
    # Caso válido
    request = ResumenRequest(
        exploitationid="EXP001",
        mes="05",
        anio="2023",
        activities=[
            ActivityInput(
                activitytype="Cosecha",
                plot="Parcela 2",
                crop="Trigo",
                date_day="20",
                date_month="06",
                date_year="2023",
                responsible="Pedro",
                description="Cosecha final"
            )
        ]
    )
    assert request.exploitationid == "EXP001"
    assert len(request.activities) == 1

def test_resumen_request_empty_activities():
    # Caso válido: activities vacío (opcional)
    request = ResumenRequest(
        exploitationid="EXP001",
        mes="05",
        anio="2023",
        activities=[]  # Vacío, pero válido
    )
    assert request.activities == []