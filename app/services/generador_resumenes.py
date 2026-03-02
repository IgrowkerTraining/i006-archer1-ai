"""Generador de resúmenes mensuales de actividades agrícolas."""

from typing import List, Dict
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


def _componer_fecha(act: Dict) -> str:
    """Compone una fecha ordenable (YYYY-MM-DD) a partir de date_year, date_month, date_day."""
    year = str(act.get("date_year", "0000")).zfill(4)
    month = str(act.get("date_month", "00")).zfill(2)
    day = str(act.get("date_day", "00")).zfill(2)
    return f"{year}-{month}-{day}"


def _fecha_legible(act: Dict) -> str:
    """Devuelve la fecha en formato legible: DD/MM/YYYY."""
    day = str(act.get("date_day", "?"))
    month = str(act.get("date_month", "?"))
    year = str(act.get("date_year", "?"))
    return f"{day}/{month}/{year}"


def _formatear_actividades(actividades: List[Dict]) -> str:
    """Formatea la lista de actividades en una cadena legible y cronológica."""
    if not actividades:
        return "No se registraron actividades en este período."

    # Ordenar por fecha compuesta
    try:
        actividades_sorted = sorted(
            actividades,
            key=lambda a: _componer_fecha(a),
        )
    except Exception:
        actividades_sorted = actividades

    lineas = []
    for i, act in enumerate(actividades_sorted, 1):
        partes = [f"Actividad {i}:"]

        fecha = _fecha_legible(act)
        partes.append(f"  Fecha: {fecha}")

        if act.get("activitytype"):
            partes.append(f"  Tipo: {act['activitytype']}")
        if act.get("plot"):
            partes.append(f"  Parcela: {act['plot']}")
        if act.get("crop"):
            partes.append(f"  Cultivo: {act['crop']}")
        if act.get("responsible"):
            partes.append(f"  Responsable: {act['responsible']}")
        if act.get("description"):
            partes.append(f"  Descripción: {act['description']}")

        # Observaciones de técnicos
        observations = act.get("observations", [])
        if observations:
            partes.append("  Observaciones técnicas:")
            for j, obs in enumerate(observations, 1):
                technician = obs.get("technician", {})
                tech_name = technician.get("name", "Técnico no identificado")
                obs_desc = obs.get("description", "")
                partes.append(f"    {j}. {tech_name}: {obs_desc}")

        lineas.append("\n\n".join(partes) if False else "\n".join(partes))

    return "\n\n".join(lineas)


def _extraer_observaciones(actividades: List[Dict]) -> str:
    """Extrae todas las observaciones técnicas de las actividades."""
    obs_list = []
    for act in actividades:
        fecha = _fecha_legible(act)
        observations = act.get("observations", [])
        for obs in observations:
            technician = obs.get("technician", {})
            tech_name = technician.get("name", "Técnico no identificado")
            obs_desc = obs.get("description", "")
            if obs_desc:
                obs_list.append(f"- [{fecha}] {tech_name}: {obs_desc}")

    return "\n".join(obs_list) if obs_list else "Sin observaciones técnicas registradas en el período."


def _extraer_tecnicos(actividades: List[Dict]) -> str:
    """Extrae nombres únicos de técnicos desde las observaciones de las actividades."""
    tecnicos = set()
    for act in actividades:
        for obs in act.get("observations", []):
            technician = obs.get("technician", {})
            name = technician.get("name")
            if name:
                tecnicos.add(name)
    return ", ".join(sorted(tecnicos)) if tecnicos else "No asignado"


def construir_prompt(
    exploitationid: str,
    mes: str,
    anio: str,
    actividades: List[Dict],
) -> str:
    """Construye el prompt para la generación del resumen."""
    # Convertir mes a nombre en español
    try:
        mes_int = int(mes)
        nombre_mes = MESES_ES.get(mes_int, mes)
    except (ValueError, TypeError):
        nombre_mes = mes

    actividades_fmt = _formatear_actividades(actividades)
    observaciones = _extraer_observaciones(actividades)
    total = len(actividades)

    # Extraer responsables únicos
    responsables = set()
    for act in actividades:
        if act.get("responsible"):
            responsables.add(act["responsible"])
    responsables_str = ", ".join(sorted(responsables)) if responsables else "No identificado"

    # Extraer técnicos desde observaciones
    tecnico_str = _extraer_tecnicos(actividades)

    prompt = f"""Eres un asistente especializado en agricultura que genera informes descriptivos mensuales de auditoría.

DATOS DEL PERÍODO:
- Explotación (ID): {exploitationid}
- Responsable(s) operativo(s): {responsables_str}
- Técnico(s) asesor(es): {tecnico_str}
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
   - Explotación (ID): [id]
   - Responsable operativo: [nombre(s)]
   - Técnico(s) asesor(es): [nombre(s)]
   - Período analizado: 1 al [último día] de [mes] de [año]
   - Fecha de generación: [fecha actual]
   - Origen de datos: Registros operativos ingresados por el productor en el sistema

2. CUERPO NARRATIVO con párrafos descriptivos que:
   - Mencionen el volumen total de actividades del período
   - Describan la secuencia cronológica de las principales labores realizadas
   - Identifiquen las parcelas y cultivos involucrados
   - Destaquen los detalles relevantes de cada actividad (tipo, responsable, descripción)
   - Mencionen labores previas registradas y la secuencia temporal
   - Indiquen si los técnicos asesores dejaron observaciones y cuándo
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
    exploitationid: str,
    mes: str,
    anio: str,
    actividades: List[Dict],
) -> dict:
    """
    Genera un resumen mensual para una explotación dada.

    Devuelve un dict con claves:
        - exitoso (bool)
        - resumen (str | None)  — texto narrativo
        - error (str | None)
        - modelo (str)
        - latencia (float)
        - id (str | None)
    """
    # 1. Construir el prompt
    prompt = construir_prompt(
        exploitationid=exploitationid,
        mes=mes,
        anio=anio,
        actividades=actividades,
    )

    # 2. Llamar al servicio de IA
    resultado_ia = await ai_service.generar_respuesta(prompt)

    respuesta_texto = resultado_ia.get("respuesta")
    latencia = resultado_ia.get("latencia")
    modelo = resultado_ia.get("modelo")
    error_ia = resultado_ia.get("error")

    # 3. Registrar la petición/respuesta en Supabase
    try:
        supabase_service.guardar_log(
            peticion=prompt[:5000],
            respuesta=respuesta_texto[:5000] if respuesta_texto else "",
            error=error_ia,
            latencia=latencia,
        )
    except Exception as log_err:
        logger.warning(f"No se pudo guardar log IA: {log_err}")

    # 4. Manejar error de la IA
    if error_ia:
        try:
            # Loggueo explícito del intento de guardar error para visibilidad
            logger.warning(f"IA devolvió error: {error_ia}. Intentando guardar resumen de error en BD.")
            supabase_service.guardar_resumen(
                exploitationid=exploitationid,
                mes=mes,
                anio=anio,
                resumen_json={"error": error_ia},
                modelo=modelo,
                exitoso=False,
            )
        except Exception as e:
            # Ahora no lo tragamos: lo registramos para debug
            logger.warning(f"No se pudo guardar resumen de error en Supabase: {e}")
        return {
            "exitoso": False,
            "resumen": None,
            "error": f"Error de IA: {error_ia}",
            "modelo": modelo,
            "latencia": latencia,
            "id": None,
        }

    # 5. Validar la respuesta (valida texto narrativo)
    valido, resultado_validacion = validar_respuesta_ia(respuesta_texto)

    if not valido:
        try:
            logger.warning(f"Validación fallida: {resultado_validacion}. Intentando guardar resumen de validación en BD.")
            supabase_service.guardar_resumen(
                exploitationid=exploitationid,
                mes=mes,
                anio=anio,
                resumen_json={"error": resultado_validacion, "respuesta_raw": (respuesta_texto or "")[:2000]},
                modelo=modelo,
                exitoso=False,
            )
        except Exception as e:
            logger.warning(f"No se pudo guardar resumen de validación en Supabase: {e}")
        return {
            "exitoso": False,
            "resumen": None,
            "error": f"Validación fallida: {resultado_validacion}",
            "modelo": modelo,
            "latencia": latencia,
            "id": None,
        }

    # resultado_validacion es el texto limpio cuando es válido
    texto_limpio = resultado_validacion

    # 6. Guardar resumen exitoso
    resumen_id = None
    try:
        logger.debug("Intentando guardar resumen exitoso en Supabase...")
        guardado = supabase_service.guardar_resumen(
            exploitationid=exploitationid,
            mes=mes,
            anio=anio,
            resumen_json={"resumen_texto": texto_limpio},
            modelo=modelo,
            exitoso=True,
        )
        logger.debug(f"guardar_resumen devolvió: {guardado}")
        if not guardado:
            logger.error("guardar_resumen devolvió un valor vacío/falsy. El resumen puede no haberse insertado.")
        else:
            # intento obtener id de la respuesta de guardado
            try:
                resumen_id = guardado.get("id") if isinstance(guardado, dict) else None
            except Exception:
                resumen_id = None
    except Exception as e:
        logger.warning(f"No se pudo guardar resumen en Supabase: {e}")

    logger.info(
        f"Resumen generado exitosamente — exploitationid={exploitationid} "
        f"periodo={mes}/{anio} modelo={modelo} latencia={latencia:.2f}s"
    )

    return {
        "exitoso": True,
        "resumen": texto_limpio,
        "error": None,
        "modelo": modelo,
        "latencia": latencia,
        "id": resumen_id,
    }