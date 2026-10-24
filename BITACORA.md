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
