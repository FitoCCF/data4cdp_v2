-- Sincroniza las secuencias de id de works4cdp con el id máximo real de cada tabla.
--
--   docker exec -i postgres_db psql -U myuser -d mydb -f - < qa/fix_sequences.sql
--
-- Diagnóstico con qa/probe_sequences.sql. Medido en mydb el 2026-11-05: 8 de 16 secuencias
-- atrasadas, y en works4cdp_userp / works4cdp_plant / works4cdp_user el PRÓXIMO insert ya chocaba;
-- en works4cdp_correctivetask, el segundo.
--
-- QUÉ TOCA: solo el contador de cada secuencia. NO modifica, borra ni inserta ninguna fila, y no
-- cambia ningún id existente. Es idempotente: correrlo dos veces da el mismo resultado.
--
-- ADVERTENCIA: setval NO es transaccional. Igual que nextval, su efecto persiste aunque la
-- transacción se revierta, así que envolverlo en BEGIN/ROLLBACK no sirve de marcha atrás. La vuelta
-- atrás real es volver a correr setval con el valor anterior, que qa/probe_sequences.sql deja
-- registrado en la columna `secuencia_en` antes de tocar nada. Guardá esa salida primero.
--
-- EFECTO VISIBLE: los ids nuevos arrancan arriba. Después de esto, un equipo nuevo recibe el 99354,
-- un área el 14001 y una tarea el 14006. Son feos pero correctos. Bajar la secuencia a un hueco
-- libre sería peor: vuelve a chocar más adelante.
--
-- Se incluyen las 16 tablas, no solo las 8 atrasadas: las que ya están OK quedan igual.
-- El nombre de la secuencia se resuelve con pg_get_serial_sequence porque works4cdp_assay y
-- works4cdp_sample fueron renombradas y conservan `assays_id_seq` y `samples_id_seq`.
--
-- El tercer argumento de setval (is_called) hace que el próximo nextval devuelva max(id) + 1. Para
-- una tabla vacía se pasa 1 con is_called = false, para que el primer id sea el 1.
-- VERIFICACIÓN: setval devuelve el valor que dejó, que es max(id). La columna
-- `secuencia_queda_en` de la salida tiene que coincidir con la columna `id_maximo` de
-- qa/probe_sequences.sql. Correr ese sondeo antes y después, como comando aparte: acá no se puede
-- incluir con \i porque psql corre dentro del contenedor y el archivo vive en el host.
\pset pager off

SELECT 'works4cdp_area' AS tabla,
       setval(pg_get_serial_sequence('works4cdp_area', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_area), 1),
              (SELECT count(*) > 0 FROM works4cdp_area)) AS secuencia_queda_en
UNION ALL SELECT 'works4cdp_assay',
       setval(pg_get_serial_sequence('works4cdp_assay', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_assay), 1),
              (SELECT count(*) > 0 FROM works4cdp_assay))
UNION ALL SELECT 'works4cdp_assayspsi',
       setval(pg_get_serial_sequence('works4cdp_assayspsi', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_assayspsi), 1),
              (SELECT count(*) > 0 FROM works4cdp_assayspsi))
UNION ALL SELECT 'works4cdp_calendar',
       setval(pg_get_serial_sequence('works4cdp_calendar', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_calendar), 1),
              (SELECT count(*) > 0 FROM works4cdp_calendar))
UNION ALL SELECT 'works4cdp_correctivetask',
       setval(pg_get_serial_sequence('works4cdp_correctivetask', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_correctivetask), 1),
              (SELECT count(*) > 0 FROM works4cdp_correctivetask))
UNION ALL SELECT 'works4cdp_equipment',
       setval(pg_get_serial_sequence('works4cdp_equipment', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_equipment), 1),
              (SELECT count(*) > 0 FROM works4cdp_equipment))
UNION ALL SELECT 'works4cdp_estado',
       setval(pg_get_serial_sequence('works4cdp_estado', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_estado), 1),
              (SELECT count(*) > 0 FROM works4cdp_estado))
UNION ALL SELECT 'works4cdp_plant',
       setval(pg_get_serial_sequence('works4cdp_plant', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_plant), 1),
              (SELECT count(*) > 0 FROM works4cdp_plant))
UNION ALL SELECT 'works4cdp_sample',
       setval(pg_get_serial_sequence('works4cdp_sample', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_sample), 1),
              (SELECT count(*) > 0 FROM works4cdp_sample))
UNION ALL SELECT 'works4cdp_system',
       setval(pg_get_serial_sequence('works4cdp_system', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_system), 1),
              (SELECT count(*) > 0 FROM works4cdp_system))
UNION ALL SELECT 'works4cdp_task',
       setval(pg_get_serial_sequence('works4cdp_task', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_task), 1),
              (SELECT count(*) > 0 FROM works4cdp_task))
UNION ALL SELECT 'works4cdp_taskcatalog',
       setval(pg_get_serial_sequence('works4cdp_taskcatalog', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_taskcatalog), 1),
              (SELECT count(*) > 0 FROM works4cdp_taskcatalog))
UNION ALL SELECT 'works4cdp_taskgroupassignment',
       setval(pg_get_serial_sequence('works4cdp_taskgroupassignment', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_taskgroupassignment), 1),
              (SELECT count(*) > 0 FROM works4cdp_taskgroupassignment))
UNION ALL SELECT 'works4cdp_taskp',
       setval(pg_get_serial_sequence('works4cdp_taskp', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_taskp), 1),
              (SELECT count(*) > 0 FROM works4cdp_taskp))
UNION ALL SELECT 'works4cdp_user',
       setval(pg_get_serial_sequence('works4cdp_user', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_user), 1),
              (SELECT count(*) > 0 FROM works4cdp_user))
UNION ALL SELECT 'works4cdp_userp',
       setval(pg_get_serial_sequence('works4cdp_userp', 'id'),
              coalesce((SELECT max(id) FROM works4cdp_userp), 1),
              (SELECT count(*) > 0 FROM works4cdp_userp))
ORDER BY 1;
