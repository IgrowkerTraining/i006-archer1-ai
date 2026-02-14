"""Supabase service for IA database operations."""

from typing import Optional
from supabase import create_client, Client

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Service for interacting with Supabase (BD IA separada)."""

    def __init__(self):
        """Initialize the Supabase client."""
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client."""
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_anon_key:
                raise RuntimeError(
                    "Supabase no configurado. "
                    "Definir SUPABASE_URL y SUPABASE_ANON_KEY en .env"
                )
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key,
            )
            logger.info("Supabase client initialized")
        return self._client

    # ── Resúmenes generados ───────────────────────────────────────────

    def guardar_resumen(
        self,
        explotacion_id: str,
        mes: int,
        anio: int,
        resumen_json: dict,
        modelo: str,
        exitoso: bool,
    ) -> dict:
        """Save a generated summary to the resumenes_generados table."""
        payload = {
            "explotacion_id": explotacion_id,
            "mes": mes,
            "anio": anio,
            "resumen_json": resumen_json,
            "modelo_usado": modelo,
            "exitoso": exitoso,
        }
        try:
            result = (
                self.client.table("resumenes_generados")
                .insert(payload)
                .execute()
            )
            logger.info(
                f"Resumen guardado para explotacion={explotacion_id} "
                f"{mes}/{anio} exitoso={exitoso}"
            )
            return result.data[0] if result.data else payload
        except Exception as e:
            logger.error(f"Error guardando resumen en Supabase: {e}")
            raise

    def obtener_resumenes(
        self,
        explotacion_id: str,
        mes: Optional[int] = None,
        anio: Optional[int] = None,
    ) -> list[dict]:
        """Retrieve summaries for a given exploitation, optionally filtered."""
        try:
            query = (
                self.client.table("resumenes_generados")
                .select("*")
                .eq("explotacion_id", explotacion_id)
                .order("fecha_generacion", desc=True)
            )
            if mes is not None:
                query = query.eq("mes", mes)
            if anio is not None:
                query = query.eq("anio", anio)

            result = query.execute()
            logger.info(
                f"Obtenidos {len(result.data)} resúmenes para "
                f"explotacion={explotacion_id}"
            )
            return result.data
        except Exception as e:
            logger.error(f"Error obteniendo resúmenes de Supabase: {e}")
            raise

    # ── Logs IA ───────────────────────────────────────────────────────

    def guardar_log(
        self,
        peticion: str,
        respuesta: str,
        error: Optional[str],
        latencia: float,
    ) -> None:
        """Log an IA request/response pair."""
        payload = {
            "peticion": peticion[:10000],       # truncate for safety
            "respuesta": respuesta[:10000],
            "error": error,
            "latencia": latencia,
        }
        try:
            self.client.table("logs_ia").insert(payload).execute()
            logger.debug(f"Log IA guardado (latencia={latencia}s)")
        except Exception as e:
            # Logging failures should NOT break the main flow
            logger.warning(f"No se pudo guardar log IA en Supabase: {e}")


# Global instance
supabase_service = SupabaseService()
