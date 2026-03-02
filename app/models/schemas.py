"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict, Union
from datetime import datetime


# ─── OpenRouter / Chat ───────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "stepfun/step-3.5-flash:free"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    pricing: Optional[Dict[str, Any]] = None


# ─── Health / Root ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class RootResponse(BaseModel):
    message: str
    version: str
    docs: str
    health: str


# ─── Resúmenes IA ────────────────────────────────────────────────────────────

class TechnicianInfo(BaseModel):
    """Datos del técnico que realiza la observación."""
    name: str


class ObservationInput(BaseModel):
    """Observación de un técnico sobre una actividad."""
    technician: TechnicianInfo
    description: str


class ActivityInput(BaseModel):
    """Actividad agrícola registrada por el productor."""
    # Campos obligatorios
    activitytype: str
    plot: str
    crop: str
    date_day: str
    date_month: str
    date_year: str
    responsible: str
    description: str
    # Observaciones del técnico (puede estar vacía)
    observations: List[ObservationInput] = []


class ResumenRequest(BaseModel):
    """Request del backend principal para generar un resumen mensual."""
    exploitationid: str
    mes: str
    anio: str
    activities: List[ActivityInput] = []


class ResumenResponse(BaseModel):
    id: Optional[str] = None
    exploitationid: str
    mes: str
    anio: str
    resumen: Union[str, Dict]
    fecha_generacion: str
    modelo_usado: str
    exitoso: bool


class ResumenListResponse(BaseModel):
    resumenes: List[ResumenResponse] = []
    total: int