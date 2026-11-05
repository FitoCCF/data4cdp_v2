# Bitácora del proyecto data4cdpv1

Registro de cambios hechos y de temas pendientes de revisión.

## 2026-10-23 — Revisión integral y refactor del backend

### Hecho
- `backend/works4cdp/views.py`: reescrito con mixins (`SchemaMixin`, `DeleteImpactMixin`, `BaseViewSet`); imports explícitos; corregido `NameError` latente de `time` en `autofill_chemical_ids`; validación de parámetros en `weekly-tasks`, `autofill-chemical-ids` y `delete-impact`; POST de `weekly-tasks` con validación previa y transacción.
- `backend/works4cdp/services/clb_syncer.py`: `assay_sort_key`, `get_max_chemical_id` y `_is_concentradora_1` centralizan lógica que estaba duplicada.
- `backend/works4cdp/serializers.py`: imports explícitos; eliminado `WeeklyTaskSerializer` (roto y sin uso).
- `backend/data4cdp_v1/settings.py`: SECRET_KEY, DEBUG, ALLOWED_HOSTS, credenciales de BD y CORS se leen del entorno (valores por defecto = comportamiento anterior).
- `backend/works4cdp/admin.py`: registro automático de todos los modelos.
- `backend/requirements.txt` nuevo (versiones fijas) y `backend/Dockerfile` instala desde él. La imagen NO se ha reconstruido.
- Eliminados archivos muertos: `backend/test.py`, `backend/works4cdp/urls.py`, `SamplesView copy.vue`, `WeeklyTasksView 2.vue`, `WeeklyTasksView copy.vue`, `WeeklyTasksView.vue.default`.
- `docker-compose.yml`: se dejó tal cual, con un comentario que indica que es solo referencia.
- Verificación: 40 respuestas de la API comparadas antes/después (idénticas salvo `userp/schema/`, que ahora existe); `manage.py check` y `makemigrations --check` sin cambios; `vite build` correcto.

### Decisiones
- Los 25 `Assay` con fecha 1999-12-31 se CONSERVAN (no se borran ni se corrigen).
- `docker-compose.yml` no se usa; se conserva como referencia.

### Pendiente de revisar más adelante
1. **Cambios de esquema (requieren migración, decidir antes):**
   - `TaskP.reschedule_user_id` es un `IntegerField` suelto; debería ser `ForeignKey` a `User`.
   - `AssaysPsi` no tiene clave natural para evitar duplicados al importar (propuesta: muestra + fecha + hora, o un campo con el `CalibrationID` del PSI).
2. **Frontend:**
   - Archivos muy grandes (`SamplingView.vue` 2.026 líneas, `ExcelGrid.vue` 1.288, `CTasksView.vue` 1.207, `TaskFormModal.vue` 1.069).
   - 10 `console.log` y uso extendido de `alert()` en lugar de un componente de mensajes.
   - `useApi` (manejo de loading/error) casi sin uso: solo 2 vistas.
   - Refactorizar vista por vista.

### Observaciones sin decisión aún
- La API no tiene autenticación ni permisos; con `DEBUG=True` y CORS abierto es un riesgo en producción.
- Carrera posible en la asignación de `chemical_id` entre peticiones simultáneas (mitigada en `autofill`, no eliminada).
- El servidor de Django corre con `runserver` (modo desarrollo) sobre datos reales.

## Trabajo con los PSI (en pausa)
- PSI Molienda C2 (172.18.16.192): API `psi2dcs` en :8082 activa; accesible desde el contenedor del backend. Solo últimos 100 registros, sin distribución granulométrica, hora mal formada (`06: 7:42`).
- Solo el equipo 7 (Molienda C2) tiene muestras (L1 id 32, L2 id 33); faltan las de los otros 3 PSI.
- Pendiente: serializer/viewset y servicio de importación de `AssaysPsi`; convención de signo de `aP*` (retenido vs pasante); modificar `psi2dcs.js` requiere reiniciar el servicio (necesita confirmación).

## 2026-10-23 — Pruebas unitarias, de API y QA de datos

### Cómo ejecutar
- Backend (76 pruebas; crea y destruye `test_mydb`, no toca `mydb`):
  `docker exec django_backend python manage.py test works4cdp --settings=data4cdp_v1.settings_test`
- Frontend (28 pruebas, Vitest): `docker exec vue_frontend sh -c 'cd /app/vue_app && npm test'`
- QA de datos sobre la base real (solo lectura): `docker exec django_backend python manage.py qa_db`

### Errores encontrados y corregidos
- **Grilla de usuarios y de ensayos no guardaba `group` ni `user`.** `gridHelpers.mapGridKeyToPayload` enviaba `group_id` y `user_id`, pero `UserSerializer` y `AssaySerializer` esperan `group` y `user`; DRF los ignoraba sin error. Corregido y cubierto por `ContratoConElFrontendTests` y `tests/gridHelpers.test.js`.
- **Paginación de `/api/userp/` sin orden** (UnorderedObjectListWarning): podía repetir u omitir grupos entre páginas. Se ordena por `id`.

### Hallazgos sin corregir (pendientes de decisión)
- **Las migraciones no se pueden aplicar en una base vacía**: la 0005 crea un constraint `works4cdp_assay_pkey`, mismo nombre que la PK. Las pruebas lo esquivan (`works4cdp/test_runner.py`), pero reconstruir la base desde cero fallaría.
- **`template1` de PostgreSQL con versión de collation inconsistente** (imagen Alpine): impide `CREATE DATABASE` normal; requiere `ALTER DATABASE ... REFRESH COLLATION VERSION`.
- ~~`TaskP.estado` con `default=1` (R)~~ → corregido a `default=2` (P) en la migración 0018 (aplicada el 2026-10-23; datos sin cambios: R=1046, P=6403, D=38).
- **Resultados de `qa_db`** (2026-10-23): 10 `chemical_id` repetidos; 1.153 con `chemical_id` >= 100000 (timestamps Unix); 17 ensayos duplicados por (muestra, fecha, hora, instancia); 25 con fecha < 2015 (se conservan); 1 con %Sol = 295 (id 9980); 2 con peso seco > neto (ids 15637, 9980); 8 TaskP huérfanas (jun-2026); 5 usuarios sin login de Django.
- ~~Filtro con "(Vacías)" + valores combinaba `__in` y `__isnull` con AND~~ → corregido (ver sección de filtros).
- `npm audit` reporta avisos en dependencias del frontend; revisar.

### Estados de TaskP (tabla works4cdp_estado)
- 1 = R (Realizado), 2 = P (Pendiente), 3 = D (Deshabilitado), 10 = S (significado no recordado; se conserva).

- Salida completa de pruebas y QA: `qa/resultados_2026-10-23.md`.

## 2026-10-23 — Usabilidad de los filtros de las grillas (ExcelGrid)

### Problemas encontrados (pruebas contra la API real)
- 23 columnas cuyo filtro u orden la API ignoraba en silencio: todas las de ensayos fuera de
  id/fecha/muestra (pCu, chemical_id, n1fe, ...), y en tareas programadas `task_id`, `estado_id`,
  `group_id`, `day`, `priority`, `completion_date` y las columnas de jerarquía.
- "(Vacías)" sola no filtraba nada; "(Vacías)" + valores devolvía 0 filas; los vacíos guardados como ''
  no se encontraban con `__isnull` (en equipos: 107 '' + 49 NULL).
- Menús de filtro alimentados descargando la tabla entera (`page_size=10000`): en tareas programadas
  tardaba 34,6 s y 5,6 MB; mientras tanto el menú solo mostraba los valores de la página actual.
- "Buscar" en el menú no tenía efecto al pulsar Aceptar; detección de "Seleccionar todo" por tamaño;
  orden de valores lexicográfico ("10" antes que "2"); menú cortado en las últimas columnas;
  al cambiar de equipo en Ensayos la grilla seguía mostrando filtros que ya no se aplicaban;
  listeners de window sin liberar al salir de la vista.
- Listado de tareas programadas con N+1 consultas (500 filas: 2,7 s).

### Cambios
- Backend `works4cdp/grid_filters.py`: parámetro único `grid_filters` (JSON) para cualquier campo del
  modelo y rutas declaradas en `grid_extra_fields`; modos `in` / `not_in`; vacío = NULL o '';
  errores de campo/valor -> 400. Endpoint `GET /<recurso>/grid-values/` (valores distintos de una
  columna con filtrado cruzado, búsqueda y límite). Orden por cualquier campo con desempate por pk.
- Frontend `ExcelGrid.vue` (cambio general): prop `filterValuesLoader`, carga de valores bajo demanda,
  búsqueda en servidor si la lista se truncó, "Borrar filtro de esta columna", indicador de orden,
  orden natural, Buscar como en Excel, `clearFilters()` expuesto, limpieza de listeners.
  Lógica pura en `utils/gridFilterLogic.js`; conexión con la API en `utils/gridQuery.js`.
- Las 11 vistas con filtrado en servidor usan `buildGridParams` + `createGridValuesLoader`; se eliminó
  `loadFilterData` (descarga masiva). `useEquipmentHierarchies.buildFilterParams` eliminado (la API
  resuelve la jerarquía).
- `select_related` en tareas, tareas programadas y correctivas: 500 filas de 2,7 s a 0,19 s (salida idéntica).

### Verificación
- Backend 99 pruebas OK; frontend 52 pruebas OK; `vite build` OK.
- `qa/probe_grid_filters.py`: 109 columnas de 11 vistas probadas contra la API real (filtro por valor,
  "(Vacías)", exclusión y orden): 0 problemas.

### Pendiente / observaciones
- En tareas programadas la columna `completion_date` muestra solo la fecha, pero el menú lista fecha y hora (filtra bien).
- Las grillas con filtrado local (semanal, mensual, calendario de grupos, muestreo) reciben las mejoras
  del menú, pero siguen filtrando solo lo cargado en pantalla.
- Hay un equipo con datos de persona (id 99353, "Adolfo Ccallo / Tecnico", sistema 1000): revisar.

## 2026-10-23 — Filtros de columna limitados a la página cargada

Decisión del usuario: en las grillas paginadas (p. ej. Ensayos de Courier Cobre, 25 por página) el
filtro de columna debe actuar SOLO sobre los registros de la página; el resultado nunca supera 25.

- `ExcelGrid.vue`: nueva prop `filterScope` = 'page' (por defecto) | 'all'.
  - 'page': el menú ofrece solo los valores de la página, filtra en el navegador, no recarga ni consulta
    al servidor; al cambiar de página el filtro se aplica a las filas nuevas. La barra de paginación
    muestra "Filtro en esta página: X de 25".
  - 'all': filtra todos los registros en el servidor (grid_filters / grid-values, ver sección anterior).
    Queda disponible por si alguna vista lo necesita: basta con `filterScope="all"`.
- ~~"Ordenar A a Z / Z a A" en grillas paginadas ordenaba en el servidor~~ → ahora también es de página
  (ver la sección "Filtrar y luego ordenar").
- Desmarcar valores se guarda como exclusión: al pasar de página siguen ocultos los valores
  desmarcados y se ven los valores nuevos. Con texto en "Buscar" se guarda como inclusión (solo coincidencias).
- Ensayos: la exportación CLB ya no aplica los filtros de la grilla (son de página); usa analizador,
  muestra y rango de fechas.
- Pruebas: `tests/views.pageFilter.test.js` monta las 11 vistas paginadas con 1.000 registros simulados y
  verifica que filtrar deja 23 de 25 filas sin pedir datos al servidor; `ExcelGrid.filters.test.js`
  cubre el cambio de página y el orden. Frontend: 69 pruebas OK.

## 2026-10-23 — Pegado desde Excel externo en modo edición

- Error: al hacer clic en una celda y pegar (Ctrl+V) varias celdas copiadas de Excel, la celda clicada
  quedaba vacía (o con su valor anterior) y el resto se pegaba desde la fila siguiente, dando la
  impresión de que los valores se "corrían" hacia abajo.
- Causa: `handlePaste` guardaba los valores y luego desenfocaba la celda; ese `blur` ejecutaba
  `handleBlur`, que copiaba al estado el texto VIEJO que todavía mostraba el DOM, pisando el primer valor.
- Corrección (`ExcelGrid.vue`): el blur provocado por el pegado no copia el DOM (`skipBlurSync`); tras
  pegar se redibujan las celdas desde el estado (`renderVersion`) y la selección marca el bloque pegado.
- Pruebas: `tests/ExcelGrid.paste.test.js` (columna, bloque, reemplazo, filas nuevas, pegar tras escribir)
  y una prueba por cada una de las 11 vistas paginadas en `tests/views.pageFilter.test.js`. Sin la
  corrección fallan las 11 vistas; con ella pasan. Frontend: 85 pruebas OK.

## 2026-10-23 — Filtrar y luego ordenar: los registros desaparecían

- Escenario reportado (Ensayos, 50 por página): filtrar por fecha y luego ordenar la columna Muestra
  (A→Z o Z→A) dejaba la grilla vacía.
- Causa: el filtro era de página (local) pero el orden se pedía al servidor, que devolvía OTROS 50
  registros (los primeros por muestra de toda la tabla); el filtro de fecha los ocultaba a todos.
- Corrección (`ExcelGrid.vue`): el orden sigue el mismo alcance que el filtro. Con `filterScope='page'`
  (por defecto) ordena las filas cargadas, sin pedir datos al servidor; con `'all'` ordena el servidor.
- Además se corrigió la comparación del orden (`compareCellText` en `utils/gridFilterLogic.js`):
  antes usaba parseFloat, así que '2026-10-20' y '2026-10-22' valían 2026 y no se ordenaban; ahora
  números por valor, fechas/horas/códigos en orden natural (C_01_S2 < C_01_S10), vacías al final.
  En columnas tipo select (Muestra) se ordena por la etiqueta visible, no por el id.
- Pruebas: `tests/ExcelGrid.sortFilter.test.js` reproduce el caso (0 filas antes, 17 después);
  en `tests/views.pageFilter.test.js`, las 11 vistas paginadas filtran y luego ordenan por CADA columna,
  A→Z y Z→A, sin perder registros ni pedir datos al servidor, y Ensayos repite el escenario exacto
  (fecha + Muestra). Frontend: 117 pruebas OK.

## 2026-10-23 — Columnas calculadas: Peso Prod. y % Sol

- Ensayos: "Peso Prod." = Peso Total − Tara (solo lectura) y "% Sol" = Peso Seco / (Peso Total − Tara) × 100
  (2 decimales; se recalcula al cambiar los pesos y admite corrección manual).
- General (`ExcelGrid.vue`): `columnsConfig[col].formula = { dependsOn, compute, editable, description }`.
  Se recalcula en cascada al escribir, pegar (cada columna pegada), elegir en desplegable o autoincrementar;
  las columnas no editables no aceptan escritura ni pegado y se muestran en azul claro con la fórmula como ayuda.
  Si faltan datos, una columna de solo lectura se vacía y una editable conserva su valor.
- Fórmulas compartidas en `utils/gridFormulas.js` (`assayWeightFormulas`), usadas por Ensayos y por
  Muestreo (que reemplaza su rowCalculator propio por la misma fórmula de % Sol).
- Backend: `Assay.save()` calcula `pweight = tweight − tara` cuando ambos existen (misma regla que la grilla).
- Pruebas: `tests/gridFormulas.test.js`, `tests/ExcelGrid.formulas.test.js` y prueba de la vista Ensayos
  (pegar pesos -> Peso Prod. 60, % Sol 50, enviados al guardar); backend `test_models`. Frontend 131 OK, backend 101 OK.
- Pendiente de decisión: en la base hay ensayos con Tara y Peso Total cuyo Peso Prod. está vacío o no
  coincide con la fórmula (ver consulta en la conversación). No se modificaron: se corrigen solos al editarlos,
  o se puede hacer una actualización masiva si se autoriza.

### Corrección: al pegar pesos solo se calculaban algunas filas
- Causa: los pesos >= 1000 llegan de Excel con separador de miles ('1,035.5' o '1.035,5'); la conversión
  solo cambiaba la primera coma por punto y esos valores no eran números, así que esas filas no se
  calculaban (en la base, 1.038 de 2.584 pesos totales son >= 1000). Al guardar, la API los habría rechazado.
- Corrección (formato definido por el usuario): el ÚNICO formato aceptado es `1,035.5`: punto = decimal,
  coma = separador de miles, que se descarta -> `1035.5`. `normalizeNumberText` (utils/gridFormulas.js)
  se aplica al calcular, al pegar en columnas de entrada de fórmulas (la celda queda `1035.5`) y en
  `sanitizeValue` antes de enviar a la API. Otros usos de la coma ('114,5', '0,84', '1.035,5') NO se
  convierten: la celda se marca en rojo y no se calcula, para no guardar un número equivocado.
- Pruebas: los tres formatos reproducían el fallo (filas con 1.035,5 y 1.117,5 quedaban vacías); ahora
  calculan todas. Frontend 155 pruebas OK.

## 2026-10-23 — Orden por defecto: Fecha y, dentro de cada fecha, Muestra (Ensayos)

- `ExcelGrid.vue`: nueva prop `defaultSort` = [{ colIndex, direction }, ...] (orden de varios niveles sobre
  las filas cargadas). "Ordenar A a Z / Z a A" pone esa columna como primer criterio y deja el orden por
  defecto como desempate; "Quitar orden" vuelve al orden por defecto. Los criterios por defecto se indican
  con una flecha gris en el encabezado.
- Ensayos: `defaultSort` = Fecha ↑, Muestra ↑ (orden natural del tag: C_01_S2, C_01_S3, C_01_S10), Hora ↑.
  Ej.: filtrar 3 fechas -> filas agrupadas por fecha y, en cada una, ordenadas por muestra.
- Orden "congelado" al editar: el orden y los filtros se recalculan al cargar datos o al cambiar
  filtro/orden, NO al escribir o pegar. Antes, con el orden por Fecha, pegar en esa columna movía la fila
  de lugar al instante (detectado por las pruebas). Las filas nuevas se agregan al final.
- Pruebas: grilla (orden de 2 niveles, desempate, quitar orden, editar sin mover filas) y vista Ensayos
  real (filtrar 3 fechas y verificar el orden por fecha y muestra). Frontend 159 pruebas OK.

## 2026-10-24 — Peso Prod. editable, corrección de datos y fechas más recientes primero

- Datos (autorizado por el usuario): 51 ensayos con Peso Prod. inconsistente (no 151 como se informó
  antes; el conteo actual con Tara y Peso Total presentes). Respaldo previo en CSV (scratchpad de la sesión).
  - 2 tipeados a mano con diferencia de centésimas (12768: 712.75 -> 712.7; 13474: 926.49 -> 926.5):
    Peso Prod. y % Sol recalculados (el % Sol no cambió al redondear a 2 decimales).
  - 49 con Peso Prod. vacío (2026-07-02 a 2026-08-25): Peso Prod. = Peso Total − Tara. Su % Sol ya era
    coherente y se conservó.
  - Verificación: 0 ensayos inconsistentes. 13,424 ensayos sin Tara o Peso Total no se tocan.
- Peso Prod. y % Sol: calculados y editables a mano. `assayWeightFormulas` (opción `pweightEditable`);
  % Sol usa el Peso Prod. de la celda, así una corrección manual de Peso Prod. recalcula % Sol.
- `applyFormulas`: evalúa las fórmulas en orden de dependencias (Peso Prod. antes que % Sol, aunque la
  columna % Sol esté antes en la grilla) y acepta varias columnas editadas a la vez; al pegar un bloque,
  un Peso Prod. pegado se respeta y no lo pisa el cálculo de Tara/Peso Total.
- Backend `Assay.save()`: Peso Prod. solo se calcula si llega vacío (respeta el valor manual) y el % Sol
  de respaldo usa Peso Prod. como peso neto.
- Ensayos: orden por defecto Fecha ↓ (más reciente primero), Muestra ↑, Hora ↑.
- Pruebas: backend 103 OK, frontend 164 OK, build OK.

## 2026-10-24 — Código químico (chemical_id) de Courier moly C2 saltó a 53100

- Causa: el siguiente código era el mayor de TODA la historia de la planta + 1. Dos ensayos de 2023 de
  Courier 5 (id 12637, 2023-06-07, C_01_S15 = 53099; id 10171, 2023-06-14, C_01_S01 = 53098) tenían un
  dígito de más (~5309); se guardaron desde la grilla la noche del 24/10 hacia las 00:07. Hoy el Courier
  moly C2 generó 53100-53102 en vez de seguir al cobre del 21 (10746-10754).
- Datos (autorizado por el usuario; respaldo CSV en el scratchpad de la sesión):
  - 12637 y 10171: chemical_id en blanco (no se conoce el valor correcto).
  - 17312, 17313, 17314 (2026-10-24, C_02_S03/S04/S05): 53100-53102 -> 10755-10757.
- `AssaySyncService.get_max_chemical_id`: ahora toma el mayor código solo de los ensayos de los últimos
  90 días (desde el ensayo más reciente con código), así un código mal tipeado en un ensayo antiguo ya no
  rompe la serie. Verificado con datos reales: siguiente C1 = 26870, C2 = 10758.
- ExcelGrid: nueva opción `columnsConfig[col].seriesCheck` (utils/gridValidation.js). Marca en naranja los
  códigos que son más del doble o menos de la mitad de la mediana de los cargados (dígito de más o de
  menos) y avisa en el diálogo de guardado. No bloquea. Activada en chemical_id de Ensayos y Muestreo.
- Pendiente: el autollenado de códigos SIN fecha (autofill-chemical-ids) asignaría códigos nuevos a los
  ensayos 12637 y 10171, que ahora no tienen código.
- Pruebas: backend 104 OK, frontend 168 OK, build OK.

## 2026-10-29 — Administración de tareas: análisis (sin cambios en código ni datos)

### Modelo y flujo
- `TaskCatalog` → `Task` (plantilla: frecuencia en días, turno A/B/AB, fecha de inicio) → `TaskP`
  (ocurrencia programada: año, semana, día, fecha, estado, campos de reprogramación).
- `Calendar`: 7 grupos por día con turno A (día), B (noche) o x (descanso). `TaskGroupAssignment` une
  `TaskP` con el grupo del día.
- Estados: 1 R (realizado), 2 P (pendiente), 3 D (se muestra como "X" en la vista semanal), 10 S.
- Vistas: semanal (`WeeklyTasksView`, `/weekly-tasks/?week&year`), calendario mensual, programación de
  grupos (solo lectura), tareas S y correctivas.

### Problemas encontrados
- No existe generador de `TaskP` en la aplicación; se generaron con scripts locales (ver abajo).
- Las correctivas no crean `TaskP` (4 sin ocurrencia). Marcar R no llena `completion_date` (5 de 1082).
- 4907 tareas P vencidas. Los campos de reprogramación no tienen lógica. `TaskP.group` no se usa.
- POST de la vista semanal con estado inválido devuelve 500. 8 `TaskP` huérfanas.
- 109 plantillas sin frecuencia y 18 con 999 (el script las salta: 999 = no programar, por confirmar).
- 16 plantillas sin turno: sus tareas nunca reciben cuadrilla.
- 165 asignaciones apuntan a un grupo en descanso (x): el calendario cambió después de asignar y nada
  recalcula las asignaciones.
- Los datos (calendario, tareas, asignaciones) terminan el 2027-01-03.

### Scripts locales que generaron los datos (`../data4cdpv1_local/scripts`)
- `generar_calendario.py`: patrón de 49 días (B/A/x) desfasado 7 días por grupo, 7 grupos,
  2026-01-19 a 2027-01-03.
- `taskpx.py` (`insert_task`) + `xtaskp.py`: genera `TaskP` con estado P desde 2026-01-19 hasta
  2027-01-03 para plantillas con frecuencia válida. Frecuencia < 7: patrón por día de la semana que se
  repite cada semana (2 = lun/mié/vie, 4 = lun/vie), no "cada N días". Salta domingos en frecuencias
  < 7 y no múltiplos de 7. Una plantilla sin fecha de inicio haría fallar el script.
- `assign_tasks.py`: asigna por fecha y turno (AB va a A y B), sin duplicar.
- `reset_table.py`: `TRUNCATE works4cdp_taskp ... CASCADE`. **No ejecutar en producción**: borraría
  7487 tareas, 18550 asignaciones y los estados R registrados.
- Los scripts tienen la contraseña de la base escrita en texto plano; no copiarlos al repositorio.

### Cálculo de la semana
- Fórmula: semana ISO + 6 + (año ISO − 1963) × 52 (2026-01-19 = 3286). Hoy todas las semanas
  guardadas coinciden con la fórmula.
- Error al cruzar de año: 2026 tiene 53 semanas ISO, así que 2026-W53 y 2027-W01 dan ambas 3335.
  `taskpx.py` cuenta semanas de forma continua (2027-W01 = 3336) y diverge de la fórmula.
- El año guardado es el del calendario: del 28 al 31/12/2026 queda 2026 y del 1 al 3/01/2027 queda
  2027 en la misma semana 3335. La vista semanal calcula 2027 para la 3335 y oculta las 91 tareas del
  28 al 31/12/2026.
- Propuesta (pendiente de decisión): semana continua calibrada en 3286 = 2026-01-19, una sola función
  para scripts, backend y frontend; comando de generación anual en el backend que agregue solo lo que
  falta (sin truncar) y no asigne a grupos en descanso.
- Preguntas abiertas: ¿2027-W01 = 3336?; ¿frecuencia 2 = lun/mié/vie o cada 2 días?; ¿qué es 999?

## 2026-10-29 — PSI REMOLIENDA (172.18.16.193): calibración del LVDT (solo lectura)

- Mismo software que el PSI Molienda C2 (PSI300i v1.4.1). Equipo de otra área (líneas VTM 1 y VTM 2).
  Acceso solo lectura; no se cambió ni reinició nada.
- 172.19.x.x es una red interna de Docker de este servidor; los PSI están en 172.18.16.x.
- Conversión de la señal: cuentas crudas 0–32760; **µm = cuentas ÷ 8** (0–4095 µm), fija en el código
  (`s(g, 32760, 4095)`). Por ciclo de sonda se toma el mínimo de promedios recortados; lecturas sobre
  `lvdtSignalThreshold = 29000` marcan sonda abierta.
- **Span**: no hay parámetro de span ni ganancia en software ni en la interfaz. Verificación en
  Opciones → Avanzado → Instrumentos → "Sonda Medición de Partículas" (cuentas y "Posición de Caliper"
  en µm, solo con el motor detenido). Un ajuste sería mecánico o del acondicionador (manual de Outotec;
  no hay manuales en el equipo). Esto último es inferencia.
- **Cero (zero check)**: con la celda lavada y sin muestra mide 30 s; la media se guarda en `zcPrimary`
  y se resta a cada medición (`average −= latestZC.avg`). No se ingresa a mano. Límites (export 2023):
  media 300–1300, desviación < 7; fuera de límite da aviso y luego error.
  - Forzarlo: Standby → Opciones (PIN) → Avanzado → Prueba del Sistema → "Zero Check", o el botón físico
    de cero (entrada digital valor 8 del Wago). Existe "Zero Check Override" que lo desactiva un tiempo.
  - Historial: Tendencias → Niveles de Cero (`zcPrimary`, promedios semanales en `zcSecondary`).
  - Estado al 2026-10-29: cero 967 µm, desviación 0–1.1, cada ~22 min; semanas 34–43 entre 965.4 y
    969.4. Estable, no requiere ajuste.
- Las ecuaciones de mallas, sólidos y P80 se ajustan con muestras de calibración contra laboratorio
  (`calibrationSamples`); eso es lo que corrige la escala del resultado.
- Seguridad (pendiente, sin tocar):
  - La clave root es la misma en .192 y .193: cambiarla en ambos.
  - `/var/www/export/psi300i-parameters-…-2023-10-12….json` contiene en texto plano los PIN de opciones
    y de fábrica, y la carpeta probablemente se sirve por el puerto 80 sin autenticación (no probado).
- El PSI .192 no respondió el 2026-10-29 (posible equipo apagado o red cortada).

## 2026-11-04 — P → R: registro del cambio y salida hacia la lista de SharePoint (Power Apps)

> Parte de la integración `SIG_CDP_POWERAPPS` (ver la entrada al final de la bitácora).

Objetivo: que al pasar una tarea de P a R el registro llegue a una lista de SharePoint que se crea y
edita desde Power Apps. Lo que faltaba no era el transporte, sino que el cambio dejara rastro.

### Punto único de cambio de estado
- `WeeklyTaskView.post` hacía `TaskP.objects.filter(id=...).update(estado_id=...)`. Un `.update()` de
  queryset no ejecuta `save()`: no llenaba `completion_date`, no disparaba señales y nada marcaba
  cuándo cambió la tarea. Y es el camino por el que el operador marca en la vista semanal.
- Nuevo `works4cdp/services/taskp_status.py` (`aplicar_cambios_estado`): valida la forma de los items
  y la existencia del `estado_id` antes de escribir, bloquea las filas con `select_for_update` y
  devuelve resumen (`cambiadas`, `sin_cambio`, `no_encontradas`, `realizadas`). La vista semanal ahora
  delega ahí; el frontend ignora el cuerpo de la respuesta, así que los campos nuevos no lo afectan.
- POST con `estado_id` inexistente: antes 500 por violación de clave foránea, ahora 400.
- `TaskP.save()` llena `completion_date` cuando el estado queda en R y está vacía (regla idempotente),
  así el PATCH del grid y el admin también la aplican. `models.estado_es_realizado` compara por nombre
  ('R', o 'Realiz…') y no por id=1.
- Al salir de R **no** se borra `completion_date`: queda como señal de que la tarea llegó a reportarse
  realizada y de que ya existe un item en la lista externa que hay que corregir, no abandonar.

### `TaskP.updated_at` (migración 0019, aplicada el 2026-11-04)
- Campo `auto_now` con índice: marca de último cambio para sondear sin recorrer las 7487 tareas.
- Al agregar una columna `auto_now`, Django rellena las filas existentes con la hora de la migración
  (`_effective_default` usa `datetime.now()` para `auto_now`/`auto_now_add`, aunque sea `null=True`).
  Las 7487 quedaron marcadas como "modificadas ahora", lo que haría que la primera sincronización
  publicara el histórico completo. La migración ahora hace `UPDATE ... SET updated_at = NULL` después
  del `AddField`; verificado: 0 filas con valor.

### Script del banco local (`../data4cdpv1_local/scripts/taskp2sharepoint.py`)
- Autenticación MSAL con **caché de tokens persistida** (`~/.config/data4cdp/sp_token_cache.json`,
  permisos 600): `--login` una vez de forma interactiva (device code) y después `acquire_token_silent`
  renueva solo, que es lo que permite correrlo por cron. El device flow a secas no sirve desatendido.
- `wsl2sharepoint.py` tenía un error: con `office365-rest-python-client 2.6.2`, `with_access_token()`
  espera **un callable que devuelva `TokenResponse`**, no el string del token.
- Modos: `--lists` y `--fields` (descubrir los nombres INTERNOS de columna, que no son los visibles),
  `--dry-run` (no toca SharePoint ni necesita credenciales), `--historico` (carga inicial por fecha de
  tarea, porque lo anterior a la 0019 tiene `updated_at` en NULL).
- Upsert por la columna clave `id_taskp` = `TaskP.id`. Nunca borra y escribe solo las columnas de
  `FIELD_MAP`, para no pisar lo que el operador llena desde Power Apps. Reenviar es inocuo.
- Publica las tareas que llegaron a R (estado R ahora **o** `completion_date` no nulo) con su estado
  actual, así una marcación deshecha corrige el item en vez de dejarlo desactualizado en R.
- Se decidió **no** usar tabla outbox: con el upsert idempotente y `updated_at`, el sondeo alcanza.

### Verificación
- Backend 117 pruebas OK (13 nuevas: `TaskPStatusTests` y 2 de la vista semanal).
- Extremo a extremo contra el stack real: `POST /api/weekly-tasks/` con la tarea **7441** (P→R) llenó
  `completion_date` y `updated_at`; el script la listó sola con `--days 1`; al deshacer (R→P) siguió
  apareciendo con `estado: P`. La 7441 quedó en P, su estado original, con `completion_date` puesta.

### Objetivo y contexto (aclarado con el usuario)
- La lista de SharePoint la llenan hoy los trabajadores con un **formulario de Power Apps**, cada uno
  logeado con su cuenta, reportando tareas rutinarias que están en `TaskP`.
- Lo que se quiere es usar la **interfaz de TaskP como vía alternativa y más práctica** para llenar
  esa misma lista (marcar muchas tareas en la grilla en vez de una por formulario). **El formulario
  queda siempre**: son dos productores sobre la misma lista, no un reemplazo.
- Por lo tanto la dirección Django → lista es la correcta y **no hace falta el camino de vuelta**.
- El sitio/lista los administra una **cuenta virtual** que no es de ningún trabajador: es la identidad
  correcta para el sincronizador desatendido (`--login` una vez con ella). Si rotan su contraseña hay
  que repetir el login; si el sync se detiene más de 90 días, el refresh token caduca.
- No hace falta on-premises data gateway: es SharePoint **Online** y la salida HTTPS está verificada
  desde el host WSL2 y desde el contenedor `django_backend`, sin proxy. El gateway solo haría falta si
  Power Apps leyera el PostgreSQL directo, o para que algo de la nube entre a la red.

### Dos productores sobre la misma lista
- Columna `origen` con valor fijo (`VALORES_FIJOS`, por defecto "TaskP") para distinguir las filas del
  sincronizador de las del formulario. Además las del formulario llevan la identidad del trabajador en
  `Author` y las del sync la de la cuenta virtual.
- Las filas del formulario no traen `id_taskp`, así que el upsert no las encuentra ni las modifica: el
  script solo toca lo que él mismo creó. Nunca borra.
- **Riesgo abierto: duplicados.** Si un trabajador reporta la tarea X por formulario y el supervisor
  marca esa misma X en la vista semanal, quedan dos filas de la misma tarea y nada las vincula. Las
  salidas posibles: (a) que el formulario escriba también `id_taskp` (lo deduplica de raíz), (b) hacer
  que el sync detecte candidatos por tarea+fecha+equipo y avise sin fusionar, (c) convivir con el
  duplicado y resolverlo en el reporte. Sin decidir.
- `--check-map` verifica `FIELD_MAP` contra las columnas reales antes de escribir (nombres internos
  inexistentes o de solo lectura), y `upsert` lo exige, para no dejar escrituras a medias.

### La API REST de SharePoint está bloqueada: se pasó a Microsoft Graph (2026-11-05)
- Con el client_id público de Azure CLI, `GET /_api/web` devuelve 401 y la cabecera que la librería
  descartaba lo explica: `x-ms-diagnostics: 3001003; reason="App is not allowed to call SPO with
  user_impersonation scope"`. Microsoft bloquea a las apps de primera parte para llamar a SPO con el
  scope genérico; no es configurable en el tenant. Agregados `--token-info` y `--probe` al script
  para diagnosticar esto (el claim `aud` era correcto y el `tid` coincidía con el realm del sitio, así
  que no era problema de tenant ni de audiencia).
- **Graph sí funciona** con la misma cuenta y el mismo refresh token: `GET /v1.0/sites/...` responde
  200. Token con `aud: https://graph.microsoft.com` y `scp` sin ningún `Sites.*` (User.Read.All,
  Group.ReadWrite.All, Directory.AccessAsUser.All, …), y aun así la lectura del sitio, de las listas y
  de las columnas funciona. **Falta probar la escritura**, que es donde puede pedir consentimiento.
- El script se reescribió sobre Graph con `msal` + `requests`: se fue la dependencia
  `office365-rest-python-client`, lo que simplifica la integración al backend.

### La lista real es `TareasCdP`, nombre interno `SIGCDP` (leída el 2026-11-05)
- El sitio tiene 18 listas; `adf_user` era solo la de prueba. La URL de la lista es `/Lists/SIGCDP`:
  ese es su nombre interno y `TareasCdP` el visible. Es la misma lista.
- **Error de medición que conviene no repetir:** `--sample` usaba `$orderby=id desc`, que Graph
  **ignora silenciosamente** en items de lista. Devolvió los dos items más ANTIGUOS (ids 31 y 32) y de
  ahí se concluyó mal que la lista tenía ~32 registros abandonados desde junio 2025. Lo correcto es
  paginar todo y ordenar localmente por `lastModifiedDateTime`.
- Realidad: **3147 items, ids 31 a 3181, el último del 2026-11-05 00:23 UTC (19:23 del 4/11 en Perú),
  y escriben 9 usuarios distintos.** La lista está en uso diario intenso.
- Columnas escribibles y lo que el formulario guarda de verdad:
  `trab_fecha` (dateTime), `trab_turno` (choice A/B), `trab_planta`, `trab_area`, `trab_equipo`,
  `equipo_tag` (texto), `trab_hdw_sfw`, `trab_tipo_trabajo` (PREVENTIVO/CORRECTIVO/SOPORTE/
  IMPLEMENTACIÓN), `trab_descripcion` (texto, **obligatoria**), `trab_responsable` (personOrGroup),
  `trab_estado` (COMPLETADO/PENDIENTE), `trab_sistema` (8 opciones).
- `trab_planta`, `trab_area` y `trab_equipo` son columnas de opciones **mal configuradas** (quedaron
  con 'Opción 1', '1' y '2'), pero aceptan valores libres: el formulario escribe
  "CONCENTRADORA 1", "PLANTA MOLY", "FILTRO MOLY". Todo en **MAYÚSCULAS**, y el sync las replica así.
- `trab_responsable` es personOrGroup (el formulario manda `trab_responsableLookupId`), así que una
  cuadrilla como "Grupo 2 / Grupo 7" no entra ahí: va en `trab_descripcion`.
- El SQL ahora trae además `sistema`, `equipo_tag` y `es_correctiva` (para `trab_tipo_trabajo`).

### Los dos vocabularios no se reconcilian (hallazgo principal)
- `trab_planta` y `trab_area` toman valores de las listas maestras `Plantas` (5 valores) y `Areas`
  (34), todas en MAYÚSCULAS. En 3147 registros `trab_planta` solo usa CONCENTRADORA 1 (1553),
  CONCENTRADORA 2 (1350), QUEBRADA HONDA (87), MISCELANEOS (79), PROYECTOS (76) y 2 'Opción 1'.
- Convención de ellos para las áreas: **sin sufijo = Concentradora 1, " 2" = Concentradora 2,
  " QH" = Quebrada Honda** (ANALIZADORES / ANALIZADORES 2, CUARTO DE CONTROL / CUARTO DE CONTROL 2,
  INFRAESTRUCTURA TI / ... 2 / ... QH, AUXILIARES / AUXILIARES 2).
- Cruce con la base: de 38 nombres (5 plantas + 33 áreas) **solo 10 resuelven solos** (6 exactos y 4
  por convención: Chancado Secundario C1, Flotacion C1, Molienda C1, Remolienda C1). **Los otros 28 no
  existen en la lista maestra**, y faltan sistemáticamente las contrapartes C2 (FLOTACION 2,
  MOLIENDA 2, REMOLIENDA 2, FILTROS 2…). Tampoco son consistentes ellos: tienen NEUTRALIZACIÓN sin "2"
  para un área que en la base es solo C2.
- Tabla para completar: `../data4cdpv1_local/data/mapeo_vocabulario_sharepoint.csv`, generada por
  `scripts/mapeo_vocabulario.py`. El mapeo por similitud de texto (difflib) se descartó: daba
  disparates (Administración → NEUTRALIZACIÓN, Data Center C1 → PLANTA DE CAL).
- **Propuesta (sin decidir): que el mapeo viva en la base, como columna en `Area` y `Plant`**
  (p. ej. `sp_name`), editable desde las grillas que ya existen, en vez de un diccionario en el
  script. Son 33 áreas que van a crecer y el sync no debería requerir cambio de código por cada una.

### El riesgo de duplicados dejó de ser teórico
- Los trabajadores YA reportan tareas rutinarias a mano: un registro real de ayer es
  `CONCENTRADORA 2 / ANALIZADORES 2 / COURIER COBRE / PREVENTIVO / "Limpieza, inspección y muestreo
  de rutina…"`, que es exactamente una ocurrencia de `TaskP`.
- `id_taskp` solo deduplica las filas del propio sincronizador; no reconoce las que escribió una
  persona. Con 9 personas reportando a diario, empujar cada P→R duplicaría de forma sistemática lo
  que ya tipearon. Decidir la regla ANTES de la primera escritura real.

### Pendiente (decisiones y datos que faltan)
- **Faltan dos columnas en `TareasCdP`: `id_taskp` (número) y `origen` (texto).** Sin `id_taskp` el
  upsert no tiene clave y cada corrida duplicaría filas. `--check-map` lo confirma; el resto del
  mapeo ya cuadra con la lista real.
- **`trab_turno` solo tiene A y B**, y en los 3147 registros reales no hay ni un `AB` ni un `C`,
  pero en la base hay tareas con turno `AB` (ambos turnos) y `C` (default de las correctivas).
  Sin decidir qué escribir.
- **`SISTEMA_MAP` tiene equivalencias INFERIDAS** sin confirmar: DCS → SYSTEM 800 ABB, PLC →
  ROCKWELL AB, Sistema SPLIT → SOFTWARE, y CCTV / Seguridad y Salud Ocupacional / Actividades CDP →
  MISCELANEOS. Lo que no está en la tabla se deja vacío y se avisa por log.
- La planta `Control de proceos` está mal escrita en la base (falta la 's'), y así se publicaría.
- Decidir la regla de duplicados contra las filas del formulario (arriba).
- Autenticación de producción: la caché de tokens de la cuenta virtual alcanza para el cron. Más
  robusto sería un registro de app propio con `Sites.Selected` acotado al sitio, en vez del client_id
  público de Azure CLI; depende de IT.
- Integración al backend como servicio + management command (`sync_taskp_sp`) y cron, una vez
  validada la escritura. Requiere `msal 1.36.0` en `requirements.txt` (`requests` ya está).

## 2026-11-05 — MER del sitio de SharePoint, y corrección del mapeo de áreas

> Parte de la integración `SIG_CDP_POWERAPPS` (ver la entrada al final de la bitácora).

Diagrama y detalle completo en [`mer_sharepoint_sigcdp.md`](mer_sharepoint_sigcdp.md). Levantado con
`data4cdpv1_local/scripts/sp_explorar_listas.py` (nuevo, solo lectura).

### `TareasCdP` no tiene ninguna relación de esquema
De las 18 listas del sitio, la principal depende de otras **tres**, y ninguna por lookup:
`trab_planta`, `trab_area` y `trab_equipo` guardan **texto copiado** de las maestras `Plantas` (5),
`Areas` (40) y `Equipo` (467). Los lookups reales están solo entre las maestras:
`Areas.Planta → Plantas`, `Equipo.Subarea → Areas` (la columna se llama `Subarea` pero apunta a
`Areas`) y `SubAreas.area_planta → Areas`. La jerarquía real es de tres niveles — Planta → Área →
Equipo — porque `SubAreas`, `ListaEquipos`, `Sistema` y `Tipo de Trabajo` están **vacías** (0 items):
el vocabulario de sistema y tipo de trabajo vive en la definición de las columnas `choice`.

Las `choice` de planta/área/equipo quedaron con los valores de fábrica (`['Opción 1']`, `['1']`,
`['2']`), que es lo que permite que el formulario escriba texto libre — y lo que permitiría al
sincronizador escribir cualquier cosa sin que SharePoint se queje.

### Pero el formulario respeta las maestras casi perfecto
Medido sobre las 3147 filas: `trab_planta` usa 6 valores distintos (1 fuera de la maestra, 2 filas),
`trab_area` 40 (1 fuera, 25 filas) y `trab_equipo` 201 de los 467 (1 fuera, 242 filas). En los tres
casos el único valor fuera de la maestra es el default de la choice, de guardados sin elegir. Todo lo
demás coincide **exacto**. `trab_responsable` está lleno en 3147 de 3147.

Consecuencia: el sincronizador tiene que escribir los nombres de las maestras tal cual o sus filas
serían las únicas rotas de la lista. Y una fila sin `trab_responsable` también se notaría.

### Corrección: las contrapartes de Concentradora 2 SÍ existen
Lo que anoté ayer ("faltan sistemáticamente las contrapartes C2: no existen `FLOTACION 2`,
`MOLIENDA 2`, `REMOLIENDA 2`, `FILTROS 2`") **está mal**. La maestra `Areas` tiene 40 áreas e incluye
`FLOTACION 2`, `MOLIENDA 2`, `REMOLIENDA 2`, `CHANCADO SECUNDARIO 2`, `PLANTA FILTROS 2`,
`AGUAS Y RELAVES 2`, `PLANTA MOLY 2`, `ANALIZADORES 2`, `AUXILIARES 2`, `CUARTO DE CONTROL 2` e
`INFRAESTRUCTURA TI 2`. La lectura anterior fue parcial.

El problema real es otro y es más chico: **sinónimos**, no valores faltantes. `Filtros C1` es
`PLANTA FILTROS`, `Molibdeno C1` es `PLANTA MOLY`, `Relaves C1` y `Agua C1` son `AGUAS Y RELAVES`,
`Infraestructura de red C1` es `INFRAESTRUCTURA TI`. `mapeo_vocabulario.py` reescrito: de las 38
filas (5 plantas + 33 áreas), **14 resuelven solas, 20 tienen propuesta a confirmar y 4 no tienen
candidato** (`Laboratorio Quimico Metalurgico`, `Planta reactivos`, `Conduccion de arena`,
`Espesador de lamas`). No hay que ampliar la lista maestra.

Ambigüedad a resolver: `Neutralizacion C2` calza con `NEUTRALIZACIÓN`, pero en SharePoint esa área
cuelga de `QUEBRADA HONDA`, no de Concentradora 2.

### Observaciones sobre los datos de ellos
- `Areas` tiene el área `MISCELANEOS` **duplicada** (items 24 y 40, misma planta).
- `Equipo` tiene `Tag_equipo` lleno en solo 11 de 467 filas; en la base son 53 de 209. El tag no
  sirve como clave de cruce entre los dos lados.
- `Users-sig` (9 personas) guarda **usuario y contraseña en texto plano** en una columna de lista de
  SharePoint, y no está vinculada por esquema a nada: es una maestra de personas paralela a la de
  Azure AD que usa el Power App por su cuenta. No es nuestro sistema, pero conviene avisarlo.

## INTEGRACIÓN PENDIENTE — `SIG_CDP_POWERAPPS`

Nombre con el que se referencia de acá en adelante todo lo relativo a publicar las tareas de `TaskP`
en la lista de SharePoint que llena el formulario de Power Apps. Estado al **2026-11-05: no
integrada, ninguna escritura hecha.** Todo lo corrido contra SharePoint fue de lectura.

### Qué es
Al pasar una tarea de **P (pendiente) a R (realizado)** en la interfaz de `TaskP`, publicar esa
ocurrencia como item en la lista `TareasCdP` (interna `SIGCDP`) del sitio
`americasmining.sharepoint.com/sites/ControldeProcesosToquepala`.

Es una vía **adicional** al formulario de Power Apps, no un reemplazo: **el formulario queda
siempre**. Dos productores independientes escriben la misma lista. Dirección **única**: base →
SharePoint; no hay camino de vuelta.

### Qué ya está hecho (en el repo, sin commitear)
- `works4cdp/services/taskp_status.py`: punto único de cambio de estado. Llena `completion_date` en
  todo P → R, pase por la API o por `save()` directo.
- `TaskP.updated_at` (migración `0019`, aplicada) como marca de último cambio para la ventana de
  sincronización, con backfill a NULL.
- `WeeklyTaskView.post` delega en el servicio; estado inexistente devuelve 400 en vez de 500.
- 117 pruebas del backend en OK.

### Qué ya está hecho (banco de pruebas, `../data4cdpv1_local/`)
- `scripts/taskp2sharepoint.py`: transporte sobre **Microsoft Graph** (no SPO REST: Microsoft bloquea
  los first-party apps con `user_impersonation` contra SPO — `x-ms-diagnostics 3001003`). Login por
  device code una vez con la cuenta virtual, caché MSAL para el cron. Upsert idempotente por
  `id_taskp`. Flags de diagnóstico: `--lists --fields --sample --check-map --dry-run`.
- `scripts/sp_explorar_listas.py`: MER del sitio. Ver `mer_sharepoint_sigcdp.md`.
- `scripts/mapeo_vocabulario.py` + `data/mapeo_vocabulario_sharepoint.csv`: tabla de traducción.

### Bloqueantes (no avanza sin esto)
1. **Faltan `id_taskp` (número) y `origen` (texto) en `TareasCdP`.** Sin `id_taskp` el upsert no tiene
   clave y cada corrida duplicaría. Crearlas es un cambio de esquema en una lista de producción con
   3147 items y 9 personas escribiendo a diario: **requiere autorización explícita.**
2. **Regla de duplicados contra las filas del formulario.** Los trabajadores ya reportan a mano las
   mismas ocurrencias de `TaskP`. `id_taskp` solo deduplica lo nuestro. Opciones: que el Power App
   también escriba `id_taskp`; o publicar solo lo que nadie reportó ese día para ese equipo y avisar
   los choques; o aceptar duplicados.
3. **Escritura por Graph sin probar.** Las lecturas funcionaron sin `Sites.*` en el `scp`; el POST
   puede necesitar consentimiento de administrador. Probar con **una** tarea cuando existan las dos
   columnas.

### Decisiones de dominio abiertas
- **Mapeo de vocabulario**: 14 de 38 resuelven solas, 20 con propuesta a confirmar, 4 sin candidato
  (`Laboratorio Quimico Metalurgico`, `Planta reactivos`, `Conduccion de arena`,
  `Espesador de lamas`). Completar `VALOR_FINAL` en el CSV. Son sinónimos, no valores faltantes: la
  maestra `Areas` no hay que ampliarla.
- `Neutralizacion C2` calza con `NEUTRALIZACIÓN`, que en SharePoint cuelga de `QUEBRADA HONDA`.
- **Dónde vive el mapeo**: propuesta = columna `sp_name` en `Area` y `Plant`, editable desde las
  grillas, en vez de un diccionario en el script. Son 33 áreas que van a crecer.
- **`trab_turno`**: la columna solo tiene A y B, y en 3147 filas no hay ni un `AB` ni un `C`. En la
  base hay tareas con turno `AB` (ambos) y `C` (default de las correctivas). Decidir qué escribir.
- **`trab_responsable`**: está lleno en 3147 de 3147 filas y es `personOrGroup`. Una cuadrilla
  ("Grupo 2 / Grupo 7") no es una persona. Hoy el plan es no escribirlo y poner la cuadrilla en la
  descripción, pero eso deja nuestras filas visiblemente distintas. Decidir.
- **`SISTEMA_MAP`**: confirmar las inferidas — DCS → SYSTEM 800 ABB, PLC → ROCKWELL AB,
  Sistema SPLIT → SOFTWARE, y CCTV / Seguridad y Salud Ocupacional / Actividades CDP → MISCELANEOS.
- La planta `Control de proceos` está **mal escrita en la base** (falta la 's') y así se publicaría.

### Cuando se desbloquee
Integrar como servicio + management command `sync_taskp_sp` + cron, agregando `msal 1.36.0` a
`backend/requirements.txt` (`requests` ya está). Autenticación de producción: la caché de tokens de
la cuenta virtual alcanza; más robusto sería un registro de app propio con `Sites.Selected` acotado
al sitio, en vez del client_id público de Azure CLI — depende de IT.

### Referencias
- `mer_sharepoint_sigcdp.md` — MER del sitio y medición de integridad.
- Entrada `2026-11-04` de esta bitácora — diagnóstico del 401 y decisión Graph vs SPO REST.
- Entrada `2026-11-05` de esta bitácora — MER y corrección del mapeo de áreas.

## 2026-11-05 — `works4cdp_equipment`: consistencia, y borrado que ya no se lleva el historial

Análisis completo en [`qa/resultados_equipment_2026-11-05.md`](qa/resultados_equipment_2026-11-05.md);
sonda reutilizable en `qa/probe_equipment_consistency.sql` (solo SELECT).

### La tabla no tiene datos contradictorios
209 filas, 0 sin área, 0 nombres vacíos, 0 espacios al borde, 0 variantes del mismo nombre por tilde
o mayúscula, y **0 filas indistinguibles**: todo grupo que parece duplicado está separado por tag,
sistema o descripción. El área que viene codificada en `description` coincide con `area_id` en las 62
filas donde aparece. Lo que hay son problemas de modelo, no de datos sucios.

### Corrección: el borrado NO era silencioso
Anoté que borrar un área destruía el historial "sin un solo aviso". **Falso.** Ya existía
`SafeDeleteModal.vue` con reporte de impacto y confirmación crítica, enganchado en las cuatro vistas
de riesgo (Plantas, Áreas, Sistemas, Equipos) contra `/delete-impact/`. Está bien hecho y es
deliberado.

Lo que sí estaba mal es que **el aviso mentía por omisión**: `impact_counts` contaba equipos, tareas
preventivas, correctivas y muestras, y **no contaba TaskP**. Para `Molibdeno C1` decía 43 registros
cuando el borrado real se llevaba 1022.

### Qué se cambió
- **`on_delete=PROTECT`** en `Equipment.system`, `Equipment.area` y `Task.equipment`
  (migración `0020_protect_equipment_task`, aplicada). No toca el esquema ni una fila: `on_delete` es
  una regla de Django, no una restricción de PostgreSQL.
- **`ProtectedDeleteMixin`** en los ViewSets de Planta, Área, Sistema y Equipo: traduce
  `ProtectedError` a **HTTP 409** con `{error, bloqueado_por, detalle}` en vez de dejar escapar un 500.
- **`impact_counts` ahora cuenta TaskP por los dos caminos** que llegan al equipo
  (`task__equipment` y `corrective_task__equipment`; contar solo el primero subestimaba el impacto).
  Se agregó `impact_counts_info`, que se informa pero **no** se suma, para
  `taskp_realizadas_count`: es un subconjunto de `taskp_count` y sumarlo inflaría `total_impact`.
- **`SafeDeleteModal.vue`**: dos badges nuevos — "Ocurrencias programadas" y, destacado en rojo,
  "De ellas, ya reportadas como realizadas".
- **`utils/deleteErrors.js`** (nuevo) y las cuatro vistas: el 409 se muestra con qué lo bloqueó, en
  vez del `alert('Error al eliminar las filas.')` genérico.

Antes y después del reporte de impacto, con datos reales:

| Área | Antes decía | Ahora dice | De ellas en R |
|---|---:|---:|---:|
| Molibdeno C1 | 43 | **1022** | 191 |
| Flotacion C2 | 55 | **1037** | 195 |

10 pruebas nuevas (`ImpactoConTaskPTests`, `BorradoProtegidoTests`) y una reescrita
(`test_borrar_planta_borra_en_cascada` → `test_borrar_planta_con_equipos_se_rechaza`, que antes
afirmaba la cascada). **Suite: 127 pruebas, OK.**

### 8 secuencias de id atrasadas — ARREGLADO el 2026-11-05
Empezó como un hallazgo en `works4cdp_equipment`: los ids se cargaron a mano en bloques
(`2001-2012`, `10001-10010`, `14001-14003`, `20001-20901`, `21001-21902`, `22902`, `99353`) sin mover
la secuencia, que quedó en **184** con el id máximo real en **99353**. Un `INSERT` con id explícito
no consume la secuencia: PostgreSQL solo la avanza cuando el id se omite.

Al revisar las 16 tablas con `qa/probe_sequences.sql` resultó que **8 están atrasadas**, y el margen
real —cuántos `INSERT` entran antes de chocar con `duplicate key value violates unique constraint`—
es mucho menor de lo que sugería el caso de equipment:

| tabla | secuencia en | id máximo | margen |
|---|---:|---:|---:|
| `works4cdp_userp` | nunca usada | 7 | **0** |
| `works4cdp_plant` | 3 | 5 | **0** |
| `works4cdp_user` | 4 | 5 | **0** |
| `works4cdp_correctivetask` | 25 | 33 | **1** |
| `works4cdp_task` | 36 | 14005 | 64 |
| `works4cdp_equipment` | 184 | 99353 | 116 |
| `works4cdp_area` | 30 | 14000 | 969 |
| `works4cdp_system` | 14 | 1000 | 985 |

**Dar de alta un grupo, una planta o un usuario ya falla hoy.** `works4cdp_correctivetask` con margen
1 es el más grave en la práctica: las correctivas las cargan los trabajadores cuando algo se rompe, y
la segunda que carguen revienta.

Están OK: `assay` (`assays_id_seq`, 17381), `sample` (`samples_id_seq`, 33), `calendar`, `estado`,
`taskcatalog`, `taskgroupassignment`, `taskp`, y `assayspsi` que está vacía.

Arreglo listo en **`qa/fix_sequences.sql`** (las 16 tablas, idempotente). No modifica, borra ni
inserta ninguna fila, y no cambia ningún id existente: solo mueve el contador. Dos advertencias que
el archivo documenta:
- `setval` **no es transaccional**: su efecto persiste aunque la transacción se revierta, así que
  `BEGIN/ROLLBACK` no sirve de marcha atrás. Guardar antes la salida de `qa/probe_sequences.sql`, que
  deja registrado el valor anterior de cada secuencia.
- Después del arreglo los ids nuevos arrancan arriba: un equipo recibe el 99354, un área el 14001,
  una tarea el 14006. Feos pero correctos; bajar la secuencia a un hueco libre vuelve a chocar.

Nota sobre el sondeo: la primera versión adivinaba el nombre de la secuencia como `<tabla>_id_seq` y
dejaba fuera, en silencio, a `works4cdp_assay` y `works4cdp_sample`, que fueron renombradas y
conservan `assays_id_seq` y `samples_id_seq`. Ahora se resuelve con `pg_get_serial_sequence`.

**Ejecutado y verificado**: las 16 secuencias quedaron en `OK` (`assayspsi` sigue vacía), y cada
`secuencia_queda_en` coincide con el `id_maximo` de su tabla. Los ids nuevos arrancan en 99354
(equipment), 14006 (task), 14001 (area), 1001 (system), 34 (correctivetask), 8 (userp) y 6
(plant / user).

Evidencia de que el bug estaba activo, no latente: entre los dos sondeos del día,
`works4cdp_userp_id_seq` pasó de "nunca usada" a 1 sin que nada del sondeo la consumiera. Solo un
`nextval` la mueve, así que hubo un intento de crear un grupo que falló con
`duplicate key ... "works4cdp_userp_pkey"` sobre el id 1 (`Grupo 1`). El número se consumió igual
porque `nextval` no es transaccional.

### PENDIENTE — decisiones de dominio sobre los datos
- **10 filas que son personas** (`Juan Alvarez`, `Gonzalo Chavez`, `Albert Churata`,
  `Sebastian Pino`, `Sharon Riquelme`, `Esteban Cabala`, `Jean Pool Mendoza`, `Eder Aliaga`,
  `Alexandra Flores`, `Adolfo Ccallo`), todas en sistema `Seguridad y Salud Ocupacional` / área
  `Sistema Integrado de Gestion`, con el cargo en `description`. **Ninguna tiene una sola tarea** y 5
  ya existen en `works4cdp_user` (ahí con emails de relleno: `q@q.com`, `a@a.com`, `b@b.com`,
  `f@f.com`, `q@p.com`). Borrarlas no rompe nada: 0 referencias.
- **3 filas que no son equipos pero sí se usan**: `Camioneta S2417` (1 tarea) y `Minicelda` /
  `Remolienda` con descripción `Almacen` (2 tareas). O son equipos de verdad, o `Task` necesita poder
  colgar de algo que no sea un equipo.
- **`tag` falta en 156 de 209** (49 `NULL` + **107 cadena vacía**: las dos formas usadas para lo
  mismo; ídem `description`, 14 + 44). Normalizar a `NULL`. Y `name` no identifica: 60 filas se
  llaman `Controlador`. De los 130 equipos con tareas, **82 no tienen tag**.
- **2 tags duplicados**: `2101` en dos equipos distintos de `Espesador de lamas` (puede ser legítimo
  si es el código del área), y `8200` en dos `System800xA` de **plantas distintas** (Sistema de bombeo
  C2 y Barcazas): uno de los dos está mal.
- `description` repite a mano la ubicación que ya está en `area_id` (`Red` 28, `QH` 8, `C2_Molibdeno`
  4…). Hoy coincide en los 62 casos, pero es información duplicada. `C1_ExCuarto Molinos` no
  corresponde a ninguna área de `works4cdp_area`.
- **71 de 209 equipos (34 %) no se usan** en ninguna tabla. `Agua C1` y `Area 3100` no tienen ni un
  equipo; `Sistema PI`, `CCTV` y `Actividades CDP` tampoco.
- `Equipment` no declara ni un `UniqueConstraint`. El candidato `(lower(name), area, system)` **no
  pasa hoy**: lo violan `Relaves C1/HMI` (412, 415) y `Data Center C1/Sala de Servidores` (305, 373).

### PENDIENTE — el siguiente anillo de PROTECT
`Sample.equipment` y `CorrectiveTask.equipment` siguen en CASCADE, igual que `Area.plant`. Borrar un
equipo sin tareas todavía se lleva sus muestras y sus correctivas. No se tocó porque cambia el
flujo de limpieza y hay que decidirlo aparte.

### El proyecto no se podía levantar de cero — ARREGLADO
Dos migraciones fallaban en una base nueva, y las dos se descubrieron al correr las pruebas sobre
`test_mydb` recién creada. Ninguna se notaba en `mydb` porque ahí ya figuran aplicadas.

**`0005` — choque de nombre con la pkey implícita.** Declaraba
`UniqueConstraint(fields=('id','timestamp'), name='works4cdp_assay_pkey')`, y ese nombre no es
elegido: es el que PostgreSQL le da automáticamente a la clave primaria de `works4cdp_assay`. Fallaba
con `relation "works4cdp_assay_pkey" already exists`.

El origen: `works4cdp_assay` se convirtió **a mano** en hypertable de TimescaleDB, que exige la
columna de partición (`timestamp`) en toda clave única. El `ALTER TABLE` que reemplazó la PK de
`(id)` por la compuesta `(id, timestamp)` nunca quedó escrito en una migración; solo se versionó el
`UniqueConstraint` del `Meta`, cuyo fin era callar a `makemigrations`. Medido en `mydb`: la
restricción real es `contype = 'p'`, `PRIMARY KEY (id, "timestamp")` — o sea que la `0005`
**nunca se ejecutó de verdad**, está marcada como aplicada pero lo que corrió fue el ALTER manual.

Arreglo: la `0005` ahora usa `SeparateDatabaseAndState`. El estado de Django sigue declarando el
mismo `UniqueConstraint` (compatible con las bases donde ya figura aplicada); las operaciones de base
son el `ALTER TABLE` manual, escrito:

```sql
ALTER TABLE works4cdp_assay DROP CONSTRAINT IF EXISTS works4cdp_assay_pkey;
ALTER TABLE works4cdp_assay ADD CONSTRAINT works4cdp_assay_pkey PRIMARY KEY (id, "timestamp");
```

No se ejecuta en `mydb` (Django no reaplica una migración registrada). **Verificado**: `migrate` de
cero sobre una base vacía aplica las 20 en OK, y la restricción resultante es idéntica a la de
producción. `--fake` ya no hace falta.

No convierte la tabla en hypertable: una base nueva queda con la PK compuesta pero sin particionar.
Versionar `create_hypertable()` es una decisión aparte — obliga a tener TimescaleDB en todo entorno
que migre, pruebas incluidas.

**`0010` — INSERT con id explícito que no avanzaba la secuencia.**
`Estado.objects.get_or_create(id=3, ...)` dejaba `works4cdp_estado_id_seq` en 1 con la fila 3 ya
existiendo, así que el tercer `Estado.objects.create()` pedía el id 3 y chocaba con
`duplicate key value violates unique constraint "works4cdp_estado_pkey"`. Intermitente y engañoso:
las secuencias **no** se revierten con el rollback de transacción de cada prueba, así que en una base
ya usada la secuencia ya había pasado el 3 y no fallaba nada. Arreglo: la migración sincroniza la
secuencia con `max(id)` después de insertar. Es el mismo bicho que el `setval` pendiente de
`works4cdp_equipment`, y por eso se agregó `qa/probe_sequences.sql`.

### Un problema de entorno que queda
`template1` tiene una `datcollversion` vieja (2.36) que el glibc del contenedor ya no puede
confirmar, así que `CREATE DATABASE` desde `template1` falla y Django no puede crear su base de
pruebas por su cuenta. Se esquiva creando `test_mydb` desde `template0` y corriendo las pruebas con
`--keepdb`. Ya no es un parche que tape nada: con la `0005` arreglada, `migrate` de cero funciona.

### PENDIENTE — `timestamp` es NOT NULL en la base y nullable en el modelo
La PK compuesta impone `NOT NULL` en `works4cdp_assay.timestamp`, pero el modelo lo declara
`null=True, blank=True` (`models.py:265`) y `save()` solo lo llena **si hay `date`**
(`models.py:311-318`), que también es nullable. Un `Assay` sin fecha es válido para Django y
rechazado por PostgreSQL: `null value in column "timestamp" violates not-null constraint`. Hoy no
pasa porque las 16349 filas vienen del sincronizador, que siempre trae fecha (medido: 0 filas sin
timestamp, 16349 ids distintos). Las dos salidas posibles:

- `date` pasa a obligatoria (`null=False`), si una fila sin fecha no tiene sentido de negocio.
- `save()` cae en `timezone.now()` cuando no hay `date`, si sí lo tiene — pero entonces la fila
  aparece con la hora de carga, no con la del ensayo.

Sin decidir.
