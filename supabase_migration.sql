-- ============================================================
-- Archer1 IA — Tablas en Supabase
-- Ejecutar en SQL Editor del dashboard de Supabase
-- ============================================================

-- 1. Tabla de resúmenes generados
CREATE TABLE IF NOT EXISTS resumenes_generados (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    exploitationid  TEXT NOT NULL,
    mes             TEXT NOT NULL,
    anio            TEXT NOT NULL,
    resumen_json    JSONB NOT NULL DEFAULT '{}',
    fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT now(),
    modelo_usado    TEXT NOT NULL,
    exitoso         BOOLEAN NOT NULL DEFAULT false
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_resumenes_explotacion
    ON resumenes_generados (exploitationid);

CREATE INDEX IF NOT EXISTS idx_resumenes_periodo
    ON resumenes_generados (exploitationid, mes, anio);

-- 2. Tabla de logs IA
CREATE TABLE IF NOT EXISTS logs_ia (
    id        UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    peticion  TEXT,
    respuesta TEXT,
    error     TEXT,
    latencia  DOUBLE PRECISION,
    fecha     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice por fecha para consultas de auditoría
CREATE INDEX IF NOT EXISTS idx_logs_fecha
    ON logs_ia (fecha DESC);

-- 3. Row Level Security (RLS) — deshabilitar para API con anon key
--    Si en el futuro necesitas RLS, habilítalo y agrega policies.
ALTER TABLE resumenes_generados ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs_ia ENABLE ROW LEVEL SECURITY;

-- Policies abiertas para anon key (ajustar en producción)
CREATE POLICY "Allow all for anon" ON resumenes_generados
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all for anon" ON logs_ia
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================
-- Migración: renombrar explotacion_id → exploitationid, mes/anio a TEXT
-- Ejecutar SOLO si la tabla ya existía con el esquema anterior.
-- ============================================================
ALTER TABLE resumenes_generados RENAME COLUMN explotacion_id TO exploitationid;
ALTER TABLE resumenes_generados ALTER COLUMN mes TYPE TEXT USING mes::TEXT;
ALTER TABLE resumenes_generados ALTER COLUMN anio TYPE TEXT USING anio::TEXT;
ALTER TABLE resumenes_generados DROP CONSTRAINT IF EXISTS resumenes_generados_mes_check;
ALTER TABLE resumenes_generados DROP CONSTRAINT IF EXISTS resumenes_generados_anio_check;
DROP INDEX IF EXISTS idx_resumenes_explotacion;
DROP INDEX IF EXISTS idx_resumenes_periodo;
CREATE INDEX idx_resumenes_explotacion ON resumenes_generados (exploitationid);
CREATE INDEX idx_resumenes_periodo ON resumenes_generados (exploitationid, mes, anio);