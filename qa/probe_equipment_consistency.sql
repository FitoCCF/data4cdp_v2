-- Consistencia de works4cdp_equipment. Solo SELECT: no modifica nada.
--
--   docker exec -i postgres_db psql -U myuser -d mydb -f - < qa/probe_equipment_consistency.sql
--
-- Resultados comentados de la corrida del 2026-11-05 en qa/resultados_equipment_2026-11-05.md
\pset pager off

\echo '=== 1. Volumen y vacíos'
SELECT count(*) AS total,
       count(*) FILTER (WHERE area_id IS NULL)                     AS sin_area,
       count(*) FILTER (WHERE tag IS NULL)                         AS tag_null,
       count(*) FILTER (WHERE tag = '')                            AS tag_cadena_vacia,
       count(*) FILTER (WHERE description IS NULL)                  AS desc_null,
       count(*) FILTER (WHERE description = '')                     AS desc_cadena_vacia
  FROM works4cdp_equipment;

\echo '=== 2. Mismo nombre en la misma área (candidatos a duplicado)'
SELECT p.name AS planta, a.name AS area, upper(btrim(e.name)) AS equipo,
       count(*) AS veces, count(DISTINCT e.system_id) AS sistemas,
       string_agg(e.id::text, ',' ORDER BY e.id) AS ids
  FROM works4cdp_equipment e
  JOIN works4cdp_area a ON a.id = e.area_id
  JOIN works4cdp_plant p ON p.id = a.plant_id
 GROUP BY 1, 2, 3 HAVING count(*) > 1
 ORDER BY veces DESC, 1, 2, 3;

\echo '=== 3. Filas realmente indistinguibles (nombre+area+sistema+tag+descripcion iguales)'
SELECT a.name AS area, e.name, s.name AS sistema, count(*) AS veces,
       string_agg(e.id::text, ',' ORDER BY e.id) AS ids
  FROM works4cdp_equipment e
  JOIN works4cdp_system s ON s.id = e.system_id
  LEFT JOIN works4cdp_area a ON a.id = e.area_id
 GROUP BY a.name, e.name, s.name, coalesce(e.tag, ''), coalesce(e.description, '')
HAVING count(*) > 1 ORDER BY 4 DESC;

\echo '=== 4. Tags duplicados (el tag debería identificar al equipo)'
SELECT upper(btrim(tag)) AS tag, count(*) AS veces,
       string_agg(id || ':' || name, ' | ' ORDER BY id) AS equipos
  FROM works4cdp_equipment
 WHERE tag IS NOT NULL AND btrim(tag) <> ''
 GROUP BY 1 HAVING count(*) > 1 ORDER BY veces DESC;

\echo '=== 5. Higiene de texto'
SELECT 'nombre con espacios al borde' AS problema, count(*) FROM works4cdp_equipment WHERE name <> btrim(name)
UNION ALL SELECT 'nombre con espacios dobles',  count(*) FROM works4cdp_equipment WHERE name ~ '  '
UNION ALL SELECT 'tag con espacios al borde',   count(*) FROM works4cdp_equipment WHERE tag IS NOT NULL AND tag <> btrim(tag)
UNION ALL SELECT 'tag con minusculas',          count(*) FROM works4cdp_equipment WHERE tag IS NOT NULL AND tag <> upper(tag)
UNION ALL SELECT 'variantes de un mismo nombre por tilde/mayuscula', count(*) FROM (
    SELECT translate(upper(btrim(name)), 'ÁÉÍÓÚÑ', 'AEIOUN')
      FROM works4cdp_equipment GROUP BY 1 HAVING count(DISTINCT name) > 1) v;

\echo '=== 6. Secuencia de id vs ids reales: cuántos INSERT aguanta antes de chocar'
SELECT (SELECT last_value FROM pg_sequences
         WHERE schemaname = 'public' AND sequencename = 'works4cdp_equipment_id_seq') AS secuencia_en,
       (SELECT max(id) FROM works4cdp_equipment)                                      AS id_maximo,
       (SELECT min(id) FROM works4cdp_equipment WHERE id > (
           SELECT last_value FROM pg_sequences
            WHERE schemaname='public' AND sequencename='works4cdp_equipment_id_seq'))  AS primer_id_ocupado,
       (SELECT min(id) FROM works4cdp_equipment WHERE id > (
           SELECT last_value FROM pg_sequences
            WHERE schemaname='public' AND sequencename='works4cdp_equipment_id_seq'))
       - (SELECT last_value + 1 FROM pg_sequences
            WHERE schemaname='public' AND sequencename='works4cdp_equipment_id_seq')   AS inserts_antes_del_error;

\echo '=== 7. Bloques de id (delatan las cargas manuales)'
SELECT (id / 1000) * 1000 AS bloque, count(*), min(id), max(id)
  FROM works4cdp_equipment GROUP BY 1 ORDER BY 1;

\echo '=== 8. Filas que no son equipos (personas, vehículos, almacenes)'
SELECT e.id, e.name, coalesce(nullif(btrim(e.description), ''), '(vacio)') AS descripcion,
       s.name AS sistema, a.name AS area,
       (SELECT count(*) FROM works4cdp_task t WHERE t.equipment_id = e.id) AS tareas
  FROM works4cdp_equipment e
  JOIN works4cdp_system s ON s.id = e.system_id
  LEFT JOIN works4cdp_area a ON a.id = e.area_id
 WHERE s.name IN ('Seguridad y Salud Ocupacional', 'Otros')
 ORDER BY s.name, e.id;

\echo '=== 9. description usada como campo libre (área codificada, tipo, ubicación)'
SELECT coalesce(nullif(btrim(description), ''), '(vacio)') AS descripcion, count(*) AS equipos
  FROM works4cdp_equipment GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 20;

\echo '=== 10. Coherencia: el area codificada en description vs el area_id real'
SELECT e.id, e.name, e.description, a.name AS area_real, p.name AS planta_real
  FROM works4cdp_equipment e
  JOIN works4cdp_area a ON a.id = e.area_id
  JOIN works4cdp_plant p ON p.id = a.plant_id
 WHERE e.description ~ '^C[12]'
   AND NOT ((e.description LIKE 'C1%' AND p.name = 'Concentradora 1')
         OR (e.description LIKE 'C2%' AND p.name = 'Concentradora 2'))
 ORDER BY e.id;

\echo '=== 11. Equipos sin ningún uso, y áreas / sistemas sin ningún equipo'
SELECT count(*) AS equipos_sin_uso FROM works4cdp_equipment e
 WHERE NOT EXISTS (SELECT 1 FROM works4cdp_task t          WHERE t.equipment_id = e.id)
   AND NOT EXISTS (SELECT 1 FROM works4cdp_correctivetask c WHERE c.equipment_id = e.id)
   AND NOT EXISTS (SELECT 1 FROM works4cdp_sample m         WHERE m.equipment_id = e.id);
SELECT p.name AS planta, a.name AS area_sin_equipos
  FROM works4cdp_area a JOIN works4cdp_plant p ON p.id = a.plant_id
 WHERE NOT EXISTS (SELECT 1 FROM works4cdp_equipment e WHERE e.area_id = a.id) ORDER BY 1, 2;
SELECT s.name AS sistema, count(e.id) AS equipos
  FROM works4cdp_system s LEFT JOIN works4cdp_equipment e ON e.system_id = s.id
 GROUP BY 1 ORDER BY 2 DESC;

\echo '=== 12. Radio de explosión del CASCADE: borrar un área borra equipos, tareas y TaskP'
SELECT p.name AS planta, a.name AS area,
       count(DISTINCT e.id)  AS equipos,
       count(DISTINCT t.id)  AS tareas,
       count(DISTINCT tp.id) AS ocurrencias_taskp,
       count(DISTINCT tp.id) FILTER (WHERE tp.estado_id = 1) AS realizadas_R
  FROM works4cdp_area a
  JOIN works4cdp_plant p ON p.id = a.plant_id
  LEFT JOIN works4cdp_equipment e ON e.area_id = a.id
  LEFT JOIN works4cdp_task t ON t.equipment_id = e.id
  LEFT JOIN works4cdp_taskp tp ON tp.task_id = t.id
 GROUP BY 1, 2 ORDER BY ocurrencias_taskp DESC LIMIT 10;

\echo '=== 13. Equipos con tareas pero sin tag (lo que el sync tendría que publicar)'
SELECT count(DISTINCT e.id) AS con_tareas,
       count(DISTINCT e.id) FILTER (WHERE e.tag IS NULL OR btrim(e.tag) = '') AS sin_tag
  FROM works4cdp_equipment e JOIN works4cdp_task t ON t.equipment_id = e.id;
