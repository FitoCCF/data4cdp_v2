-- Qué registros dependen del área id 30. Solo lectura: ningún INSERT/UPDATE/DELETE.
-- A works4cdp_area apunta una sola FK en todo el esquema: works4cdp_equipment.area_id (PROTECT).
-- El resto (tareas, muestras, ensayos) cuelga de esos equipos, así que se sigue en cadena.
--
-- Uso:
--   docker exec -i postgres_db psql -U myuser -d mydb -f - < qa/probe_area_30.sql

\pset pager off

\echo '== 1. El área y su planta =='
SELECT a.id, a.tag, a.name, a.description, a.plant_id, p.tag AS plant_tag, p.name AS plant_name
FROM works4cdp_area a
LEFT JOIN works4cdp_plant p ON p.id = a.plant_id
WHERE a.id = 30;

\echo '== 2. Toda FK del esquema que referencia works4cdp_area (confirmación) =='
SELECT con.conrelid::regclass AS tabla_hija,
       att.attname           AS columna,
       -- Ojo: Django crea TODAS sus FK como NO ACTION ('a') y resuelve PROTECT/CASCADE en Python.
       -- Esta columna no distingue un on_delete de otro; para eso hay que leer models.py.
       con.confdeltype       AS on_delete_en_la_base
FROM pg_constraint con
JOIN unnest(con.conkey) AS k(attnum) ON TRUE
JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = k.attnum
WHERE con.contype = 'f'
  AND con.confrelid = 'works4cdp_area'::regclass
ORDER BY 1, 2;

\echo '== 3. Equipos del área 30 (dependientes directos) =='
SELECT e.id, e.tag, e.name, e.description, e.system_id, s.name AS system_name
FROM works4cdp_equipment e
LEFT JOIN works4cdp_system s ON s.id = e.system_id
WHERE e.area_id = 30
ORDER BY e.id;

\echo '== 4. Resumen: cuántos dependientes cuelgan del área 30, por tabla =='
WITH eq AS (SELECT id FROM works4cdp_equipment WHERE area_id = 30),
     sa AS (SELECT id FROM works4cdp_sample WHERE equipment_id IN (SELECT id FROM eq)),
     tk AS (SELECT id FROM works4cdp_task WHERE equipment_id IN (SELECT id FROM eq))
SELECT 'equipment (directo)'          AS tabla, (SELECT count(*) FROM eq) AS filas
UNION ALL SELECT 'task',               (SELECT count(*) FROM tk)
UNION ALL SELECT 'taskp (vía task)',   (SELECT count(*) FROM works4cdp_taskp WHERE task_id IN (SELECT id FROM tk))
UNION ALL SELECT 'correctivetask',     (SELECT count(*) FROM works4cdp_correctivetask WHERE equipment_id IN (SELECT id FROM eq))
UNION ALL SELECT 'sample',             (SELECT count(*) FROM sa)
UNION ALL SELECT 'assay (vía sample)', (SELECT count(*) FROM works4cdp_assay WHERE sample_id IN (SELECT id FROM sa))
UNION ALL SELECT 'assayspsi (vía sample)', (SELECT count(*) FROM works4cdp_assayspsi WHERE sample_id IN (SELECT id FROM sa));

\echo '== 5. Detalle de los dependientes en cadena (si hay) =='
\echo '-- 5a. Tareas preventivas de esos equipos'
SELECT t.id, t.equipment_id, tc.name AS tarea, t.frequency, t.start_date, t.turn
FROM works4cdp_task t
LEFT JOIN works4cdp_taskcatalog tc ON tc.id = t.task_catalog_id
WHERE t.equipment_id IN (SELECT id FROM works4cdp_equipment WHERE area_id = 30)
ORDER BY t.id;

\echo '-- 5b. Tareas correctivas de esos equipos'
SELECT c.id, c.equipment_id, c.name, c.description, c.creation_date, c.priority, c.turno
FROM works4cdp_correctivetask c
WHERE c.equipment_id IN (SELECT id FROM works4cdp_equipment WHERE area_id = 30)
ORDER BY c.id;

\echo '-- 5c. Muestras físicas de esos equipos'
SELECT m.id, m.equipment_id, m.tag, m.name
FROM works4cdp_sample m
WHERE m.equipment_id IN (SELECT id FROM works4cdp_equipment WHERE area_id = 30)
ORDER BY m.id;

\echo '== 6. Veredicto: se puede borrar el área 30 o PROTECT lo va a rechazar =='
SELECT CASE WHEN count(*) = 0
            THEN 'SIN EQUIPOS: el DELETE del área pasaría (y no arrastraría nada)'
            ELSE count(*) || ' equipo(s) la referencian: PROTECT rechaza el borrado -> HTTP 409. Hay que reasignarlos primero.'
       END AS veredicto
FROM works4cdp_equipment WHERE area_id = 30;
