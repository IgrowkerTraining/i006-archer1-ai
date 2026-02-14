"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from datetime import datetime
from typing import Union

from pyparsing import Any


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(default="stepfun/step-3.5-flash:free", description="AI model to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: Optional[bool] = Field(default=False, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Chat completion response model."""
    id: str = Field(..., description="Response ID")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, Any]] = Field(default=None, description="Token usage information")


class ModelInfo(BaseModel):
    """AI model information."""
    id: str = Field(..., description="Model ID")
    name: Optional[str] = Field(default=None, description="Model display name")
    description: Optional[str] = Field(default=None, description="Model description")
    pricing: Optional[Dict[str, Any]] = Field(default=None, description="Pricing information")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: Optional[str] = Field(default=None, description="Additional status message")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")


# ─── Schemas para Resúmenes IA ───────────────────────────────────────────────


class ActividadInput(BaseModel):
    """Input de una actividad agrícola recibida del backend principal."""
    fecha: str = Field(..., description="Fecha de la actividad (DD/MM/AAAA)")
    hora: Optional[str] = Field(default=None, description="Hora aproximada")
    tipo_actividad: str = Field(..., description="Tipo de actividad realizada")
    parcela: str = Field(..., description="Identificación de la parcela")
    cultivo: Optional[str] = Field(default=None, description="Tipo de cultivo")
    variedad: Optional[str] = Field(default=None, description="Variedad del cultivo")
    superficie: Optional[str] = Field(default=None, description="Superficie trabajada")
    producto: Optional[str] = Field(default=None, description="Producto utilizado")
    numero_registro_producto: Optional[str] = Field(default=None, description="Número de registro del producto")
    dosis: Optional[str] = Field(default=None, description="Dosis aplicada")
    metodo_aplicacion: Optional[str] = Field(default=None, description="Método de aplicación")
    condiciones_climaticas: Optional[str] = Field(default=None, description="Condiciones climáticas")
    responsable: Optional[str] = Field(default=None, description="Responsable de la actividad")
    dni_responsable: Optional[str] = Field(default=None, description="DNI/NIE del responsable")
    maquinaria: Optional[str] = Field(default=None, description="Maquinaria utilizada")
    motivo: Optional[str] = Field(default=None, description="Motivo de la actividad")
    observaciones_productor: Optional[str] = Field(default=None, description="Observaciones del productor")
    registro_confirmado_por: Optional[str] = Field(default=None, description="Quién confirmó el registro")


class ResumenRequest(BaseModel):
    """Request para generar un resumen mensual de actividades."""
    explotacion_id: str = Field(..., description="ID de la explotación agrícola")
    mes: int = Field(..., ge=1, le=12, description="Mes del resumen (1-12)")
    anio: int = Field(..., ge=2000, le=2100, description="Año del resumen")
    nombre_explotacion: str = Field(..., description="Nombre de la explotación")
    titular: str = Field(..., description="Titular de la explotación")
    tecnico: Optional[str] = Field(default=None, description="Técnico asesor asignado")
    actividades: List[ActividadInput] = Field(default=[], description="Lista de actividades del período")


class ResumenResponse(BaseModel):
    """Response con el resumen generado."""
    id: Optional[str] = Field(default=None, description="ID del resumen en BD")
    explotacion_id: str = Field(..., description="ID de la explotación")
    mes: int = Field(..., description="Mes del resumen")
    anio: int = Field(..., description="Año del resumen")
    resumen: Union[str, Dict] = Field(..., description="Contenido del resumen generado")
    fecha_generacion: str = Field(..., description="Fecha y hora de generación")
    modelo_usado: str = Field(..., description="Modelo de IA utilizado")
    exitoso: bool = Field(..., description="Si la generación fue exitosa")


class ResumenListResponse(BaseModel):
    """Response con lista de resúmenes."""
    resumenes: List[ResumenResponse] = Field(default=[], description="Lista de resúmenes")
    total: int = Field(..., description="Total de resúmenes encontrados")
