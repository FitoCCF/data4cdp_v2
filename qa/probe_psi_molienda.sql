-- Probe de SOLO LECTURA para armar la vista de muestreo del PSI Molienda C1.
-- No modifica nada: solo SELECT. Ver BITACORA.md.
--
-- Qué se busca:
--   1. Qué equipo de works4cdp_equipment es el PSI de Molienda C1 (su id, para el selector).
--   2. Qué muestras (works4cdp_sample) cuelgan de ese equipo: son las filas del formato.
--   3. Si works4cdp_assayspsi existe y tiene datos (el modelo AssaysPsi está en models.py pero no
--      tiene serializer ni ruta en la API).

\pset pager off

\echo ''
\echo '=== 1. Equipos cuyo nombre/descripcion/tag menciona PSI, MOLIENDA o GRANULOMET ==='
SELECT e.id,
       e.tag,
       e.name,
       e.description,
       s.name  AS sistema,
       a.name  AS area,
       p.name  AS planta
  FROM works4cdp_equipment e
  LEFT JOIN works4cdp_system s ON s.id = e.system_id
  LEFT JOIN works4cdp_area   a ON a.id = e.area_id
  LEFT JOIN works4cdp_plant  p ON p.id = a.plant_id
 WHERE e.name        ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
    OR e.description ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
    OR e.tag         ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
 ORDER BY e.id;

\echo ''
\echo '=== 2. Los equipos que ya usa la vista Sampling de couriers (ids 1, 2, 5, 6), como referencia ==='
SELECT e.id, e.tag, e.name, e.description, a.name AS area, p.name AS planta
  FROM works4cdp_equipment e
  LEFT JOIN works4cdp_area  a ON a.id = e.area_id
  LEFT JOIN works4cdp_plant p ON p.id = a.plant_id
 WHERE e.id IN (1, 2, 5, 6)
 ORDER BY e.id;

\echo ''
\echo '=== 3. Muestras de los equipos del punto 1 (son las filas del formato impreso) ==='
SELECT sm.equipment_id,
       e.name AS equipo,
       sm.id,
       sm.tag,
       sm.name,
       sm.sn
  FROM works4cdp_sample sm
  JOIN works4cdp_equipment e ON e.id = sm.equipment_id
 WHERE e.name        ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
    OR e.description ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
    OR e.tag         ILIKE ANY (ARRAY['%psi%', '%molienda%', '%granulom%'])
 ORDER BY sm.equipment_id, sm.tag;

\echo ''
\echo '=== 4. Cuantas muestras tiene cada equipo (para ver cuales estan listos para un formato) ==='
SELECT e.id, e.name, count(sm.id) AS muestras
  FROM works4cdp_equipment e
  LEFT JOIN works4cdp_sample sm ON sm.equipment_id = e.id
 GROUP BY e.id, e.name
HAVING count(sm.id) > 0
 ORDER BY count(sm.id) DESC, e.id;

\echo ''
\echo '=== 5. La tabla works4cdp_assayspsi: existe? tiene filas? ==='
SELECT to_regclass('works4cdp_assayspsi') AS tabla_assayspsi;

SELECT count(*) AS filas,
       min(date) AS fecha_min,
       max(date) AS fecha_max,
       count(DISTINCT sample_id) AS muestras_distintas
  FROM works4cdp_assayspsi;

\echo ''
\echo '=== 6. Columnas reales de works4cdp_assayspsi (para contrastar con el modelo) ==='
SELECT ordinal_position AS pos, column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_name = 'works4cdp_assayspsi'
 ORDER BY ordinal_position;
