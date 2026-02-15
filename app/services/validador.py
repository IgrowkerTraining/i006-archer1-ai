"""Validador de respuestas IA para resúmenes agrícolas (modo texto narrativo)."""

import re
from typing import Tuple, Union

from app.core.logging import get_logger

logger = get_logger(__name__)

# Frases prescriptivas que la IA no debe usar
FRASES_PROHIBIDAS = [
    r"\bse recomienda\b",
    r"\bse sugiere\b",
    r"\bdebería\b",
    r"\bdeberían\b",
    r"\bes aconsejable\b",
    r"\bse aconseja\b",
    r"\bconviene que\b",
    r"\bsería recomendable\b",
    r"\bsería conveniente\b",
    r"\bhabría que\b",
    r"\bse debe\b",
    r"\brecomendamos\b",
    r"\bsugerimos\b",
    r"\baconsejamos\b",
]

_PATRON_PROHIBIDO = re.compile("|".join(FRASES_PROHIBIDAS), re.IGNORECASE)

# Límites de longitud
MIN_LENGTH = 100
MAX_LENGTH = 15000


def validar_respuesta_ia(respuesta_texto: str) -> Tuple[bool, Union[str, str]]:
    # Valida que la respuesta sea texto narrativo válido
    if not respuesta_texto or not respuesta_texto.strip():
        return False, "La respuesta de la IA está vacía."

    texto = respuesta_texto.strip()

    # Si la IA devolvió JSON en vez de texto narrativo, intentar extraer
    if texto.startswith("{") and texto.endswith("}"):
        try:
            import json
            parsed = json.loads(texto)
            for key in ["resumen_descriptivo", "resumen_texto", "resumen", "texto", "contenido"]:
                if key in parsed and isinstance(parsed[key], str) and len(parsed[key]) > MIN_LENGTH:
                    texto = parsed[key]
                    logger.info(f"Texto extraído del campo JSON '{key}'")
                    break
            else:
                return False, "La IA devolvió JSON en lugar de texto narrativo."
        except (json.JSONDecodeError, Exception):
            return False, "La IA devolvió formato no reconocido."

    # Longitud mínima
    if len(texto) < MIN_LENGTH:
        return False, f"Resumen demasiado corto ({len(texto)} chars, mínimo {MIN_LENGTH})."

    # Truncar si excede máximo
    if len(texto) > MAX_LENGTH:
        texto = texto[:MAX_LENGTH]

    # Detectar lenguaje prescriptivo
    match = _PATRON_PROHIBIDO.search(texto.lower())
    if match:
        return False, (
            f"El resumen contiene lenguaje prescriptivo: '{match.group(0)}'. "
            f"Debe ser descriptivo, no prescriptivo."
        )

    # Limpiar artefactos de markdown
    texto = re.sub(r"^#{1,6}\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", texto)

    logger.info(f"Respuesta validada ({len(texto)} chars)")
    return True, texto
