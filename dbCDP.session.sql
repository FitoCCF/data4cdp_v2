SELECT 
    tp.year AS anio,
    tp.week AS semana,
    tp.date AS fecha,
    tp.day AS dia_semana,
    p.name AS planta,
    a.name AS area,
    sys.name AS sistema,
    t.name AS tarea_descripcion,
    eq.name AS equipo,
    t.turn AS turno,
    STRING_AGG(DISTINCT g.name, ' / ') AS cuadrilla_grupo,
    STRING_AGG(DISTINCT u.nombre || ' ' || u.apellido, ', ') AS usuarios_asignados,
    e.estado_nombre AS estado
FROM works4cdp_taskp tp
-- 1. Unimos para obtener el detalle de la Tarea y el Equipo
LEFT JOIN works4cdp_task t ON tp.task_id = t.id
LEFT JOIN works4cdp_equipment eq ON t.equipment_id = eq.id

-- Unimos para obtener el Sistema, Área y Planta asociados al Equipo
LEFT JOIN works4cdp_system sys ON eq.system_id = sys.id
LEFT JOIN works4cdp_area a ON eq.area_id = a.id
LEFT JOIN works4cdp_plant p ON a.plant_id = p.id

-- 2. Unimos para obtener el Estado (Pendiente, Realizada, etc.)
LEFT JOIN works4cdp_estado e ON tp.estado_id = e.id

-- 3. Unimos con la tabla de asignación y el calendario para encontrar qué grupo tomó el turno
LEFT JOIN works4cdp_taskgroupassignment tga ON tga.taskp_id = tp.id
LEFT JOIN works4cdp_calendar c ON tga.calendar_id = c.id
LEFT JOIN works4cdp_userp g ON c.group_id = g.id
LEFT JOIN works4cdp_user u ON u.group_id = g.id

-- Filtramos por el año y la semana deseada (Cambia estos valores según necesites)
-- WHERE tp.week = 32 
--   AND tp.year = 2026

-- Agrupamos para poder usar STRING_AGG y concatenar todos los usuarios en una sola fila por tarea
GROUP BY 
    tp.id, 
    tp.year, 
    tp.week, 
    tp.date, 
    tp.day, 
    p.name,
    a.name,
    sys.name,
    t.name, 
    eq.name, 
    t.turn, 
    e.estado_nombre
    
-- Ordenamos cronológicamente y por turno
ORDER BY 
    tp.date ASC, 
    t.turn ASC;
