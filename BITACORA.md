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
- Filtro de jerarquía en grillas: si se marcan valores y "(Vacías)" a la vez se envían `equipment__in` y `equipment__isnull` juntos y el backend los combina con AND (sin resultados).
- `npm audit` reporta avisos en dependencias del frontend; revisar.

### Estados de TaskP (tabla works4cdp_estado)
- 1 = R (Realizado), 2 = P (Pendiente), 3 = D (Deshabilitado), 10 = S (significado no recordado; se conserva).

- Salida completa de pruebas y QA: `qa/resultados_2026-10-23.md`.
