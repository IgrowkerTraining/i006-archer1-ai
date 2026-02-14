"""Endpoints para generación y consulta de resúmenes IA."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.models.schemas import (
    ResumenRequest,
    ResumenResponse,
    ResumenListResponse,
)
from app.services.generador_resumenes import generar_resumen_mensual
from app.services.supabase_service import supabase_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ia", tags=["ia-resumenes"])


@router.post("/resumen-mensual", response_model=ResumenResponse)
async def crear_resumen_mensual(request: ResumenRequest):
    """
    Generate a monthly descriptive summary from agricultural activities.

    Receives exploitation data + activities list, calls OpenRouter AI,
    validates the response, stores it in Supabase and returns the result.
    """
    logger.info(
        f"POST /ia/resumen-mensual — explotacion={request.explotacion_id} "
        f"periodo={request.mes}/{request.anio} "
        f"actividades={len(request.actividades)}"
    )

    # Convert Pydantic models to dicts for the generator
    actividades_dict = [act.model_dump(exclude_none=True) for act in request.actividades]

    try:
        resultado = await generar_resumen_mensual(
            explotacion_id=request.explotacion_id,
            mes=request.mes,
            anio=request.anio,
            actividades=actividades_dict,
            nombre_explotacion=request.nombre_explotacion,
            titular=request.titular,
            tecnico=request.tecnico,
        )
    except Exception as e:
        logger.error(f"Error generando resumen: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    if not resultado["exitoso"]:
        logger.warning(f"Resumen no exitoso: {resultado['error']}")
        # Still return a response with exitoso=False so the caller knows
        return ResumenResponse(
            id=None,
            explotacion_id=request.explotacion_id,
            mes=request.mes,
            anio=request.anio,
            resumen={"error": resultado["error"]},
            fecha_generacion=datetime.now().isoformat(),
            modelo_usado=resultado["modelo"],
            exitoso=False,
        )

    return ResumenResponse(
        id=resultado.get("id"),
        explotacion_id=request.explotacion_id,
        mes=request.mes,
        anio=request.anio,
        resumen=resultado["resumen"],
        fecha_generacion=datetime.now().isoformat(),
        modelo_usado=resultado["modelo"],
        exitoso=True,
    )


@router.get("/resumenes/{explotacion_id}", response_model=ResumenListResponse)
async def obtener_resumenes(
    explotacion_id: str,
    mes: Optional[int] = Query(default=None, ge=1, le=12, description="Filtrar por mes"),
    anio: Optional[int] = Query(default=None, ge=2000, le=2100, description="Filtrar por año"),
):
    """
    Retrieve stored summaries for a given exploitation.

    Optionally filter by month and/or year.
    """
    logger.info(
        f"GET /ia/resumenes/{explotacion_id} — mes={mes}, anio={anio}"
    )

    try:
        datos = supabase_service.obtener_resumenes(
            explotacion_id=explotacion_id,
            mes=mes,
            anio=anio,
        )
    except Exception as e:
        logger.error(f"Error consultando resúmenes: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando BD: {str(e)}")

    resumenes = [
        ResumenResponse(
            id=r.get("id"),
            explotacion_id=r.get("explotacion_id", explotacion_id),
            mes=r.get("mes", 0),
            anio=r.get("anio", 0),
            resumen=r.get("resumen_json", {}),
            fecha_generacion=r.get("fecha_generacion", ""),
            modelo_usado=r.get("modelo_usado", ""),
            exitoso=r.get("exitoso", False),
        )
        for r in datos
    ]

    return ResumenListResponse(
        resumenes=resumenes,
        total=len(resumenes),
    )
