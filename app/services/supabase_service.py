"""Supabase service for IA database operations."""

from typing import Optional
from supabase import create_client, Client

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupabaseService:
    """Servicio para interactuar con la base de datos de Supabase (IA)."""

    def __init__(self):
        """Inicializa el cliente de Supabase."""
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Inicialización perezosa del cliente de Supabase."""
        if self._client is None:
            if not settings.supabase_url:
                raise RuntimeError(
                    "Supabase no configurado. "
                    "Definir SUPABASE_URL en .env"
                )
            # Preferir service_role key (bypasea RLS) sobre anon key
            key = settings.supabase_service_role_key or settings.supabase_anon_key
            if not key:
                raise RuntimeError(
                    "Supabase key no configurada. "
                    "Definir SUPABASE_SERVICE_ROLE_KEY o SUPABASE_ANON_KEY en .env"
                )
            self._client = create_client(
                settings.supabase_url,
                key,
            )
            role = "service_role" if settings.supabase_service_role_key else "anon"
            logger.info(f"Supabase client initialized (role={role})")
        return self._client

    # ── Resúmenes generados ───────────────────────────────────────────

    def guardar_resumen(
        self,
        exploitationid: str,
        mes: str,
        anio: str,
        resumen_json: dict,
        modelo: str,
        exitoso: bool,
    ) -> dict:
        """Guarda un resumen generado en la tabla resumenes_generados."""
        payload = {
            "exploitationid": exploitationid,
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
                f"Resumen guardado para exploitationid={exploitationid} "
                f"{mes}/{anio} exitoso={exitoso}"
            )
            return result.data[0] if result.data else payload
        except Exception as e:
            logger.error(f"Error guardando resumen en Supabase: {e}")
            raise

    def obtener_resumenes(
        self,
        exploitationid: str,
        mes: Optional[str] = None,
        anio: Optional[str] = None,
    ) -> list[dict]:
        """Obtiene resúmenes para una explotación dada, opcionalmente filtrados por mes y año."""
        try:
            query = (
                self.client.table("resumenes_generados")
                .select("*")
                .eq("exploitationid", exploitationid)
                .order("fecha_generacion", desc=True)
            )
            if mes is not None:
                query = query.eq("mes", mes)
            if anio is not None:
                query = query.eq("anio", anio)

            result = query.execute()
            logger.info(
                f"Obtenidos {len(result.data)} resúmenes para "
                f"exploitationid={exploitationid}"
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
        """Registra un par de petición/respuesta de IA."""
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
            # Fallos en el logging NO deben interrumpir el flujo principal
            logger.warning(f"No se pudo guardar log IA en Supabase: {e}")


# Instancia global
supabase_service = SupabaseService()
