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

class ActividadInput(BaseModel):
    # Campos obligatorios
    fecha: str
    tipo_actividad: str
    parcela: str
    # Campos opcionales
    hora: Optional[str] = None
    cultivo: Optional[str] = None
    variedad: Optional[str] = None
    superficie: Optional[str] = None
    producto: Optional[str] = None
    numero_registro_producto: Optional[str] = None
    dosis: Optional[str] = None
    metodo_aplicacion: Optional[str] = None
    condiciones_climaticas: Optional[str] = None
    responsable: Optional[str] = None
    dni_responsable: Optional[str] = None
    maquinaria: Optional[str] = None
    motivo: Optional[str] = None
    observaciones_productor: Optional[str] = None
    registro_confirmado_por: Optional[str] = None


class ResumenRequest(BaseModel):
    explotacion_id: str
    mes: int = Field(..., ge=1, le=12)
    anio: int = Field(..., ge=2000, le=2100)
    nombre_explotacion: str
    titular: str
    tecnico: Optional[str] = None
    actividades: List[ActividadInput] = []


class ResumenResponse(BaseModel):
    id: Optional[str] = None
    explotacion_id: str
    mes: int
    anio: int
    resumen: Union[str, Dict]
    fecha_generacion: str
    modelo_usado: str
    exitoso: bool


class ResumenListResponse(BaseModel):
    resumenes: List[ResumenResponse] = []
    total: int
