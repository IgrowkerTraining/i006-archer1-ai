"""Validador de respuestas IA para resúmenes agrícolas."""

import json
import re
from typing import Tuple, Union

from app.core.logging import get_logger

logger = get_logger(__name__)

# Frases prescriptivas prohibidas (case-insensitive)
FRASES_PROHIBIDAS = [
    r"se\s+recomienda",
    r"se\s+sugiere",
    r"es\s+aconsejable",
    r"deber[íi]a",
    r"se\s+aconseja",
    r"conviene\s+que",
    r"ser[íi]a\s+conveniente",
    r"habr[íi]a\s+que",
    r"es\s+necesario\s+que",
    r"se\s+debe",
    r"recomendamos",
    r"sugerimos",
    r"aconsejamos",
]

# Compilar regex una sola vez
_PATRON_PROHIBIDO = re.compile(
    "|".join(FRASES_PROHIBIDAS), re.IGNORECASE
)


def _extraer_json(texto: str) -> str:
    """
    Extract JSON content from text that may be wrapped in markdown
    code blocks (```json ... ```) or contain leading/trailing text.
    """
    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", texto, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try extracting first { ... } block
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        return match.group(0).strip()

    # Return as-is and let JSON parse fail with clear error
    return texto.strip()


def validar_respuesta_ia(respuesta_texto: str) -> Tuple[bool, Union[dict, str]]:
    """
    Validate an IA response for summary generation.

    Returns:
        (True, parsed_dict) if valid
        (False, error_message) if invalid
    """
    if not respuesta_texto or not respuesta_texto.strip():
        return False, "La respuesta de la IA está vacía"

    # 1. Try to parse as JSON
    texto_limpio = _extraer_json(respuesta_texto)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError as e:
        logger.warning(f"Respuesta IA no es JSON válido: {e}")
        # If it's not JSON, treat the raw text as the summary content
        datos = {"resumen_texto": respuesta_texto.strip()}

    # 2. Check for prescriptive/recommendation language
    texto_completo = (
        json.dumps(datos, ensure_ascii=False)
        if isinstance(datos, dict)
        else str(datos)
    )
    match = _PATRON_PROHIBIDO.search(texto_completo)
    if match:
        frase = match.group(0)
        msg = (
            f"La respuesta contiene lenguaje prescriptivo prohibido: "
            f"'{frase}'. El resumen debe ser descriptivo, no prescriptivo."
        )
        logger.warning(msg)
        return False, msg

    # 3. Ensure it's a dict (not a list or primitive)
    if not isinstance(datos, dict):
        return False, f"Se esperaba un objeto JSON, se recibió {type(datos).__name__}"

    logger.info("Respuesta IA validada correctamente")
    return True, datos
