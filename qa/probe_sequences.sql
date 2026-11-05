-- ¿Alguna secuencia de id quedó atrás del id máximo real? Solo SELECT: no modifica nada.
--
--   docker exec -i postgres_db psql -U myuser -d mydb -f - < qa/probe_sequences.sql
--
-- Un INSERT con id explícito no consume la secuencia: PostgreSQL solo la avanza cuando el id se
-- omite. Pasa al cargar datos por script y en las migraciones de datos que fijan el id (ver
-- 0010_add_deshabilitado_state). La secuencia queda atrás y los siguientes INSERT normales van
-- entregando ids ya ocupados hasta chocar con:
--
--     duplicate key value violates unique constraint "<tabla>_pkey"
--
-- Para cada tabla ATRASADA, el arreglo es una línea, idempotente y sin tocar ninguna fila:
--
--     SELECT setval('<tabla>_id_seq', (SELECT max(id) FROM <tabla>));
\pset pager off

-- El nombre de la secuencia se resuelve con pg_get_serial_sequence y NO se adivina como
-- '<tabla>_id_seq': `works4cdp_assay` y `works4cdp_sample` fueron renombradas y sus secuencias
-- conservan los nombres viejos (`assays_id_seq`, `samples_id_seq`). Adivinar el nombre dejaba esas
-- dos tablas fuera del informe, en silencio.
WITH maximos(tabla, secuencia, id_maximo) AS (
              SELECT 'works4cdp_area',                pg_get_serial_sequence('works4cdp_area', 'id'),                max(id) FROM works4cdp_area
    UNION ALL SELECT 'works4cdp_assay',               pg_get_serial_sequence('works4cdp_assay', 'id'),               max(id) FROM works4cdp_assay
    UNION ALL SELECT 'works4cdp_assayspsi',           pg_get_serial_sequence('works4cdp_assayspsi', 'id'),           max(id) FROM works4cdp_assayspsi
    UNION ALL SELECT 'works4cdp_calendar',            pg_get_serial_sequence('works4cdp_calendar', 'id'),            max(id) FROM works4cdp_calendar
    UNION ALL SELECT 'works4cdp_correctivetask',      pg_get_serial_sequence('works4cdp_correctivetask', 'id'),      max(id) FROM works4cdp_correctivetask
    UNION ALL SELECT 'works4cdp_equipment',           pg_get_serial_sequence('works4cdp_equipment', 'id'),           max(id) FROM works4cdp_equipment
    UNION ALL SELECT 'works4cdp_estado',              pg_get_serial_sequence('works4cdp_estado', 'id'),              max(id) FROM works4cdp_estado
    UNION ALL SELECT 'works4cdp_plant',               pg_get_serial_sequence('works4cdp_plant', 'id'),               max(id) FROM works4cdp_plant
    UNION ALL SELECT 'works4cdp_sample',              pg_get_serial_sequence('works4cdp_sample', 'id'),              max(id) FROM works4cdp_sample
    UNION ALL SELECT 'works4cdp_system',              pg_get_serial_sequence('works4cdp_system', 'id'),              max(id) FROM works4cdp_system
    UNION ALL SELECT 'works4cdp_task',                pg_get_serial_sequence('works4cdp_task', 'id'),                max(id) FROM works4cdp_task
    UNION ALL SELECT 'works4cdp_taskcatalog',         pg_get_serial_sequence('works4cdp_taskcatalog', 'id'),         max(id) FROM works4cdp_taskcatalog
    UNION ALL SELECT 'works4cdp_taskgroupassignment', pg_get_serial_sequence('works4cdp_taskgroupassignment', 'id'), max(id) FROM works4cdp_taskgroupassignment
    UNION ALL SELECT 'works4cdp_taskp',               pg_get_serial_sequence('works4cdp_taskp', 'id'),               max(id) FROM works4cdp_taskp
    UNION ALL SELECT 'works4cdp_user',                pg_get_serial_sequence('works4cdp_user', 'id'),                max(id) FROM works4cdp_user
    UNION ALL SELECT 'works4cdp_userp',               pg_get_serial_sequence('works4cdp_userp', 'id'),               max(id) FROM works4cdp_userp
)
SELECT m.tabla,
       split_part(m.secuencia, '.', 2) AS secuencia,
       s.last_value                    AS secuencia_en,
       m.id_maximo,
       -- last_value NULL = secuencia nunca usada: el próximo id es el start_value (normalmente 1).
       coalesce(s.last_value + 1, s.start_value) AS proximo_id,
       CASE
           WHEN m.secuencia IS NULL                        THEN 'SIN SECUENCIA (revisar)'
           WHEN m.id_maximo IS NULL                        THEN 'tabla vacia'
           WHEN coalesce(s.last_value, 0) >= m.id_maximo   THEN 'OK'
           ELSE 'ATRASADA'
       END                             AS estado
  FROM maximos m
  LEFT JOIN pg_sequences s
    ON s.schemaname = split_part(m.secuencia, '.', 1)
   AND s.sequencename = split_part(m.secuencia, '.', 2)
 ORDER BY (coalesce(s.last_value, 0) < coalesce(m.id_maximo, 0)) DESC, m.tabla;
