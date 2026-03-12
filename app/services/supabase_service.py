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
        # Normalizar mes/anio como strings; mes en formato 2 dígitos para consistencia.
        mes = str(mes).strip().zfill(2)
        anio = str(anio).strip()

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

            result = query.execute()
            rows = result.data or []

            # Si no se pasan filtros devolvemos todo (comportamiento anterior).
            if mes is None and anio is None:
                logger.info(
                    f"Obtenidos {len(rows)} resúmenes para exploitationid={exploitationid}"
                )
                return rows

            # Construir conjuntos de candidatas para mes/anio (tolerantes a "1" vs "01").
            def _candidates(value: Optional[str]) -> Optional[set]:
                if value is None:
                    return None
                s = str(value).strip()
                cand = {s, s.lstrip("0") or "0", s.zfill(2)}
                return {c for c in cand if c}

            mes_cand = _candidates(mes)
            anio_cand = _candidates(anio)

            # Filtrar en Python (robusto ante formatos mixtos en DB).
            def _row_matches(r: dict) -> bool:
                if mes_cand is not None:
                    if str(r.get("mes", "")).strip() not in mes_cand:
                        return False
                if anio_cand is not None:
                    if str(r.get("anio", "")).strip() not in anio_cand:
                        return False
                return True

            filtered = [r for r in rows if _row_matches(r)]
            logger.info(
                f"Obtenidos {len(filtered)} resúmenes para exploitationid={exploitationid}"
            )
            return filtered

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
