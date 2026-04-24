-- ═══════════════════════════════════════════════════════
-- TABLAS DE CONFIGURACIÓN — Sistema de Bonos QiORA
-- Ejecutar en: Supabase Dashboard → SQL Editor
-- ═══════════════════════════════════════════════════════

-- 1. DISTRITOS: metas por cuadrilla, tipo (A/B/C), penalización activa
CREATE TABLE IF NOT EXISTS config_distritos (
  id              BIGSERIAL PRIMARY KEY,
  distrito        TEXT NOT NULL,
  tipo            TEXT NOT NULL CHECK (tipo IN ('A','B','C')),
  penalizacion    BOOLEAN NOT NULL DEFAULT false,
  meta_normal     INT NOT NULL,
  meta_moto       INT NOT NULL,
  meta_hibrida    INT NOT NULL,
  meta_elite      INT NOT NULL,
  meta_multidistrito INT NOT NULL,
  fecha_inicio    DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin       DATE DEFAULT NULL,   -- NULL = vigente
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 2. BONOS BASE: monto por tipo de distrito y tramo de alcance
CREATE TABLE IF NOT EXISTS config_bonos_base (
  id              BIGSERIAL PRIMARY KEY,
  tipo_distrito   TEXT NOT NULL CHECK (tipo_distrito IN ('A','B','C')),
  pct_min         INT NOT NULL,   -- ej. 80
  pct_max         INT NOT NULL,   -- ej. 90 (exclusivo)
  monto           INT NOT NULL,
  fecha_inicio    DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin       DATE DEFAULT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. SERVICIOS: puntos (estrellas) por tipo de orden
CREATE TABLE IF NOT EXISTS config_servicios (
  id              BIGSERIAL PRIMARY KEY,
  tipo            TEXT NOT NULL,
  puntos          INT NOT NULL DEFAULT 0,
  fecha_inicio    DATE NOT NULL DEFAULT CURRENT_DATE,
  fecha_fin       DATE DEFAULT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── RLS: permitir lectura y escritura con anon key ───────────────────────────
ALTER TABLE config_distritos  ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_bonos_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_servicios  ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='config_distritos'  AND policyname='anon_all_distritos') THEN
    CREATE POLICY "anon_all_distritos"  ON config_distritos  FOR ALL USING (true) WITH CHECK (true); END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='config_bonos_base' AND policyname='anon_all_bonos')     THEN
    CREATE POLICY "anon_all_bonos"      ON config_bonos_base FOR ALL USING (true) WITH CHECK (true); END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='config_servicios'  AND policyname='anon_all_servicios') THEN
    CREATE POLICY "anon_all_servicios"  ON config_servicios  FOR ALL USING (true) WITH CHECK (true); END IF;
END $$;

-- ── DATOS INICIALES (valores actuales del sistema) ──────────────────────────
INSERT INTO config_distritos (distrito, tipo, penalizacion, meta_normal, meta_moto, meta_hibrida, meta_elite, meta_multidistrito, fecha_inicio) VALUES
  ('CTA-TPI-INT-CUN CANCUN 1',          'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-VRZ VERACRUZ',           'B', true,  84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-TUX TUXTLA',             'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-XAL XALAPA',             'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-MER MERIDA',             'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-IRA IRAPUATO',           'B', true,  75, 60, 75, 75, 75, '2026-01-01'),
  ('CTA-TPI-INT-LON LEON',               'B', true,  75, 70, 75, 75, 75, '2026-01-01'),
  ('CTA-TPI-INT-MOR MORELIA',            'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-PUE PUEBLA',             'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-GBA GDL BARRANCA',       'A', true,  90, 70, 90, 90, 90, '2026-01-01'),
  ('CTA-TPI-INT-GPR GDL PRIMAVERA',      'A', true,  90, 60, 90, 90, 90, '2026-01-01'),
  ('CTA-TPI-INT-GES GDL ESTADIO',        'A', true,  90, 60, 90, 90, 90, '2026-01-01'),
  ('CTA-TPI-INT-CBA CORDOBA ORIZABA',    'B', false, 75, 60, 75, 75, 75, '2026-01-01'),
  ('CTA-TPI-INT-GLM GDL LOPEZ MATEOS',   'A', true,  75, 60, 75, 75, 75, '2026-01-01'),
  ('CTA-TPI-INT-AGS AGUASCALIENTES',     'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-TEP TEPIC',              'B', false, 84, 70, 84, 84, 84, '2026-01-01'),
  ('CTA-TPI-INT-COL COLIMA',             'B', false, 90, 70, 90, 90, 90, '2026-01-01');

INSERT INTO config_bonos_base (tipo_distrito, pct_min, pct_max, monto, fecha_inicio) VALUES
  ('A', 80, 90,  500,  '2026-01-01'),
  ('A', 90, 100, 900,  '2026-01-01'),
  ('A', 100,999, 2500, '2026-01-01'),
  ('B', 80, 90,  450,  '2026-01-01'),
  ('B', 90, 100, 800,  '2026-01-01'),
  ('B', 100,999, 1800, '2026-01-01'),
  ('C', 80, 90,  300,  '2026-01-01'),
  ('C', 90, 100, 700,  '2026-01-01'),
  ('C', 100,999, 1400, '2026-01-01');

INSERT INTO config_servicios (tipo, puntos, fecha_inicio) VALUES
  ('Instalación',            6, '2026-01-01'),
  ('Soporte',                3, '2026-01-01'),
  ('Mantenimiento Mayor',    4, '2026-01-01'),
  ('Mantenimiento',          3, '2026-01-01'),
  ('Addons',                 2, '2026-01-01'),
  ('Cambio De Domicilio',    6, '2026-01-01'),
  ('Cambio De Equipo',       2, '2026-01-01'),
  ('Soporte Empresarial',    5, '2026-01-01'),
  ('Instalación Empresarial',8, '2026-01-01'),
  ('Recolección Pi',         1, '2026-01-01'),
  ('Recolección',            1, '2026-01-01'),
  ('Cambio De Plan',         2, '2026-01-01'),
  ('Factibilidad',           1, '2026-01-01'),
  ('No Aplica',              0, '2026-01-01');
