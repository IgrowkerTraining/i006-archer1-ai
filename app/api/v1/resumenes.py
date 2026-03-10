"""Endpoints para generación y consulta de resúmenes IA."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
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
    Generar un resumen descriptivo mensual a partir de actividades agrícolas.
    Recibe datos de la explotación + lista de actividades, llama al AI de
    OpenRouter, valida la respuesta, la almacena en Supabase y devuelve el resultado.
    """
    logger.info(
        f"POST /ia/resumen-mensual — exploitationid={request.exploitationid} "
        f"periodo={request.mes}/{request.anio} "
        f"actividades={len(request.activities)}"
    )

    # Convertir modelos Pydantic a diccionarios para el generador
    actividades_dict = [act.model_dump() for act in request.activities]

    try:
        resultado = await generar_resumen_mensual(
            exploitationid=request.exploitationid,
            mes=request.mes,
            anio=request.anio,
            actividades=actividades_dict,
        )
    except Exception as e:
        logger.error(f"Error generando resumen: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    if not resultado["exitoso"]:
        logger.warning(f"Resumen no exitoso: {resultado['error']}")
        return ResumenResponse(
            id=None,
            exploitationid=request.exploitationid,
            mes=request.mes,
            anio=request.anio,
            resumen={"error": resultado["error"]},
            fecha_generacion=datetime.now().isoformat(),
            modelo_usado=resultado["modelo"],
            exitoso=False,
        )

    return ResumenResponse(
        id=resultado.get("id"),
        exploitationid=request.exploitationid,
        mes=request.mes,
        anio=request.anio,
        resumen=resultado["resumen"],
        fecha_generacion=datetime.now().isoformat(),
        modelo_usado=resultado["modelo"],
        exitoso=True,
    )


@router.get("/resumenes/{exploitationid}", response_model=ResumenListResponse)
async def obtener_resumenes(
    exploitationid: str,
    mes: Optional[str] = Query(default=None, description="Filtrar por mes"),
    anio: Optional[str] = Query(default=None, description="Filtrar por año"),
):
    """
    Recuperar resúmenes almacenados para una explotación dada.
    Opcionalmente filtrar por mes y/o año.
    """
    logger.info(
        f"GET /ia/resumenes/{exploitationid} — mes={mes}, anio={anio}"
    )

    try:
        datos = supabase_service.obtener_resumenes(
            exploitationid=exploitationid,
            mes=mes,
            anio=anio,
        )
    except Exception as e:
        logger.error(f"Error consultando resúmenes: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando BD: {str(e)}")

    resumenes = [
        ResumenResponse(
            id=r.get("id"),
            exploitationid=r.get("exploitationid", exploitationid),
            mes=r.get("mes", ""),
            anio=r.get("anio", ""),
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


@router.get(
    "/resumenes/{exploitationid}/texto",
    response_class=PlainTextResponse,
    summary="Obtener resumen como texto plano",
)
async def obtener_resumen_texto(
    exploitationid: str,
    mes: Optional[str] = Query(default=None, description="Filtrar por mes"),
    anio: Optional[str] = Query(default=None, description="Filtrar por año"),
):
    """
    Devuelve únicamente el contenido narrativo del resumen (resumen_texto)
    como texto plano, sin envoltorio JSON.
    """
    logger.info(
        f"GET /ia/resumenes/{exploitationid}/texto — mes={mes}, anio={anio}"
    )

    try:
        datos = supabase_service.obtener_resumenes(
            exploitationid=exploitationid,
            mes=mes,
            anio=anio,
        )
    except Exception as e:
        logger.error(f"Error consultando resúmenes: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando BD: {str(e)}")

    if not datos:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron resúmenes para los filtros indicados.",
        )

    resumen_json = datos[0].get("resumen_json", {})
    texto = resumen_json.get("resumen_texto", "") if isinstance(resumen_json, dict) else ""

    if not texto:
        raise HTTPException(
            status_code=404,
            detail="El resumen existe pero no contiene texto narrativo.",
        )

    return PlainTextResponse(content=texto, media_type="text/plain; charset=utf-8")
