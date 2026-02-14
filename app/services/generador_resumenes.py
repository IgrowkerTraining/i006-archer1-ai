"""Generador de resúmenes mensuales de actividades agrícolas."""

from typing import List, Dict, Optional
from datetime import datetime

from app.services.ai_service import ai_service
from app.services.supabase_service import supabase_service
from app.services.validador import validar_respuesta_ia
from app.core.logging import get_logger

logger = get_logger(__name__)

# Nombres de meses en español
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _formatear_actividades(actividades: List[Dict]) -> str:
    """Format activities list into a readable chronological string."""
    if not actividades:
        return "No se registraron actividades en este período."

    # Sort by date if available
    try:
        actividades_sorted = sorted(
            actividades,
            key=lambda a: a.get("fecha", "0000-00-00"),
        )
    except Exception:
        actividades_sorted = actividades

    lineas = []
    for i, act in enumerate(actividades_sorted, 1):
        partes = [f"Actividad {i}:"]

        if act.get("fecha"):
            partes.append(f"  Fecha: {act['fecha']}")
        if act.get("hora"):
            partes.append(f"  Hora: {act['hora']}")
        if act.get("tipo_actividad"):
            partes.append(f"  Tipo: {act['tipo_actividad']}")
        if act.get("parcela"):
            partes.append(f"  Parcela: {act['parcela']}")
        if act.get("cultivo"):
            partes.append(f"  Cultivo: {act['cultivo']}")
        if act.get("variedad"):
            partes.append(f"  Variedad: {act['variedad']}")
        if act.get("superficie"):
            partes.append(f"  Superficie: {act['superficie']}")
        if act.get("producto"):
            partes.append(f"  Producto: {act['producto']}")
        if act.get("numero_registro_producto"):
            partes.append(f"  Nº registro producto: {act['numero_registro_producto']}")
        if act.get("dosis"):
            partes.append(f"  Dosis: {act['dosis']}")
        if act.get("metodo_aplicacion"):
            partes.append(f"  Método de aplicación: {act['metodo_aplicacion']}")
        if act.get("condiciones"):
            partes.append(f"  Condiciones: {act['condiciones']}")
        if act.get("responsable"):
            partes.append(f"  Responsable: {act['responsable']}")
        if act.get("dni_responsable"):
            partes.append(f"  DNI/NIE responsable: {act['dni_responsable']}")
        if act.get("maquinaria"):
            partes.append(f"  Maquinaria: {act['maquinaria']}")
        if act.get("motivo"):
            partes.append(f"  Motivo: {act['motivo']}")
        if act.get("observaciones_productor"):
            partes.append(f"  Observaciones del productor: {act['observaciones_productor']}")
        if act.get("registro_confirmado_por"):
            partes.append(f"  Registro confirmado por: {act['registro_confirmado_por']}")

        lineas.append("\n".join(partes))

    return "\n".join(lineas)


def _extraer_observaciones(actividades: List[Dict]) -> str:
    """Extract technical observations from activities."""
    obs = []
    for act in actividades:
        observacion = act.get("observacion_tecnica") or act.get("observaciones_tecnico")
        if observacion:
            fecha = act.get("fecha_observacion") or act.get("fecha", "sin fecha")
            tecnico_obs = act.get("tecnico_observacion") or "técnico no identificado"
            obs.append(f"- [{fecha}] {tecnico_obs}: {observacion}")

        obs_productor = act.get("observaciones_productor")
        if obs_productor:
            fecha = act.get("fecha", "sin fecha")
            obs.append(f"- [{fecha}] Observación del productor: {obs_productor}")

    return "\n".join(obs) if obs else "Sin observaciones técnicas registradas en el período."


def construir_prompt(
    explotacion_id: str,
    mes: int,
    anio: int,
    actividades: List[Dict],
    nombre_explotacion: str = "",
    titular: str = "",
    tecnico: Optional[str] = None,
) -> str:
    """Build the prompt for summary generation."""
    nombre_mes = MESES_ES.get(mes, str(mes))
    actividades_fmt = _formatear_actividades(actividades)
    observaciones = _extraer_observaciones(actividades)

    # Determine first and last day of the month
    total = len(actividades)

    # Extract unique responsables
    responsables = set()
    for act in actividades:
        if act.get("responsable"):
            responsables.add(act["responsable"])
    responsables_str = ", ".join(responsables) if responsables else "No identificado"

    tecnico_str = tecnico if tecnico else "No asignado"

    prompt = f"""Eres un asistente especializado en agricultura que genera informes descriptivos mensuales de auditoría.

DATOS DEL PERÍODO:
- Explotación: {nombre_explotacion or explotacion_id}
- Titular: {titular or 'No especificado'}
- Responsable(s) operativo(s): {responsables_str}
- Técnico asesor: {tecnico_str}
- Período analizado: 1 al último día de {nombre_mes} de {anio}
- Fecha de generación: {datetime.now().strftime('%d de %B de %Y')}
- Origen de datos: Registros operativos ingresados por el productor en el sistema
- Total actividades registradas: {total}

ACTIVIDADES REGISTRADAS (orden cronológico):
{actividades_fmt}

OBSERVACIONES TÉCNICAS (si existen):
{observaciones}

INSTRUCCIONES:
Genera un resumen descriptivo narrativo en texto plano (NO en JSON) siguiendo este formato exacto:

1. ENCABEZADO con los datos de la explotación:
   - Explotación: [nombre]
   - Titular: [nombre]
   - Responsable operativo: [nombre(s)]
   - Técnico asesor: [nombre]
   - Período analizado: 1 al [último día] de [mes] de [año]
   - Fecha de generación: [fecha actual]
   - Origen de datos: Registros operativos ingresados por el productor en el sistema

2. CUERPO NARRATIVO con párrafos descriptivos que:
   - Mencionen el volumen total de actividades del período
   - Describan la secuencia cronológica de las principales labores realizadas
   - Identifiquen las parcelas, cultivos y superficies involucradas
   - Destaquen las aplicaciones fitosanitarias (producto, dosis, método, responsable)
   - Mencionen labores previas registradas y la secuencia temporal
   - Indiquen si el técnico asesor dejó observaciones y cuándo
   - Sean objetivos, descriptivos y NO prescriptivos

3. CIERRE con la frase:
   "El presente resumen se ha generado a partir de la información registrada por el productor y las observaciones incorporadas por el técnico asesor."

REGLAS ESTRICTAS:
- Responde ÚNICAMENTE con texto narrativo plano, NO uses formato JSON
- NO uses Markdown, ni asteriscos, ni headers con #
- NO añadas recomendaciones técnicas ("se recomienda", "debería", "se sugiere", etc.)
- NO evalúes si las prácticas son correctas o incorrectas
- NO inventes datos que no estén en las actividades proporcionadas
- Si no hay actividades, el resumen debe indicarlo claramente
- Usa lenguaje formal de auditoría, objetivo y preciso
- Escribe en español
"""

    return prompt


async def generar_resumen_mensual(
    explotacion_id: str,
    mes: int,
    anio: int,
    actividades: List[Dict],
    nombre_explotacion: str = "",
    titular: str = "",
    tecnico: Optional[str] = None,
) -> dict:
    """
    Generate a monthly summary for a given exploitation.

    Returns dict with keys:
      - exitoso (bool)
      - resumen (str | None)  — texto narrativo
      - error (str | None)
      - modelo (str)
      - latencia (float)
      - id (str | None)
    """
    # 1. Build the prompt
    prompt = construir_prompt(
        explotacion_id=explotacion_id,
        mes=mes,
        anio=anio,
        actividades=actividades,
        nombre_explotacion=nombre_explotacion,
        titular=titular,
        tecnico=tecnico,
    )

    # 2. Call AI service
    resultado_ia = await ai_service.generar_respuesta(prompt)

    respuesta_texto = resultado_ia["respuesta"]
    latencia = resultado_ia["latencia"]
    modelo = resultado_ia["modelo"]
    error_ia = resultado_ia["error"]

    # 3. Log the request/response in Supabase
    try:
        supabase_service.guardar_log(
            peticion=prompt[:5000],
            respuesta=respuesta_texto[:5000] if respuesta_texto else "",
            error=error_ia,
            latencia=latencia,
        )
    except Exception as log_err:
        logger.warning(f"No se pudo guardar log IA: {log_err}")

    # 4. Handle AI error
    if error_ia:
        try:
            supabase_service.guardar_resumen(
                explotacion_id=explotacion_id,
                mes=mes,
                anio=anio,
                resumen_json={"error": error_ia},
                modelo=modelo,
                exitoso=False,
            )
        except Exception:
            pass
        return {
            "exitoso": False,
            "resumen": None,
            "error": f"Error de IA: {error_ia}",
            "modelo": modelo,
            "latencia": latencia,
            "id": None,
        }

    # 5. Validate response (now validates narrative text, not JSON)
    valido, resultado_validacion = validar_respuesta_ia(respuesta_texto)

    if not valido:
        try:
            supabase_service.guardar_resumen(
                explotacion_id=explotacion_id,
                mes=mes,
                anio=anio,
                resumen_json={"error": resultado_validacion, "respuesta_raw": respuesta_texto[:2000]},
                modelo=modelo,
                exitoso=False,
            )
        except Exception:
            pass
        return {
            "exitoso": False,
            "resumen": None,
            "error": f"Validación fallida: {resultado_validacion}",
            "modelo": modelo,
            "latencia": latencia,
            "id": None,
        }

    # 6. Save successful summary
    resumen_id = None
    try:
        guardado = supabase_service.guardar_resumen(
            explotacion_id=explotacion_id,
            mes=mes,
            anio=anio,
            resumen_json={"resumen_texto": respuesta_texto},
            modelo=modelo,
            exitoso=True,
        )
        resumen_id = guardado.get("id") if guardado else None
    except Exception as e:
        logger.warning(f"No se pudo guardar resumen en Supabase: {e}")

    logger.info(
        f"Resumen generado exitosamente — explotacion={explotacion_id} "
        f"periodo={mes}/{anio} modelo={modelo} latencia={latencia:.2f}s"
    )

    return {
        "exitoso": True,
        "resumen": respuesta_texto,
        "error": None,
        "modelo": modelo,
        "latencia": latencia,
        "id": resumen_id,
    }
