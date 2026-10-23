# Resultados de pruebas y QA — 2026-10-23

Guardado para corregir más adelante. Resumen: backend 76/76 OK, frontend 28/28 OK, qa_db 8 de 20 chequeos con avisos.

## Pendientes a corregir

| Código | Problema | Registros |
|---|---|---|
| ASSAY-01 | `chemical_id` repetido (< 100000) | 10 |
| ASSAY-02 | `chemical_id` >= 100000 (timestamps Unix) | 1.153 |
| ASSAY-03 | Ensayos duplicados (muestra, fecha, hora, instancia) | 17 |
| ASSAY-04 | Fecha < 2015 (decisión: se conservan) | 25 |
| ASSAY-07 | %Sol fuera de 0..100 (id 9980 = 295) | 1 |
| ASSAY-08 | Peso seco > peso neto (ids 15637, 9980) | 2 |
| TASKP-01 | Tareas programadas huérfanas (jun-2026) | 8 |
| USER-01 | Usuarios sin login de Django | 5 |

Otros hallazgos (no son de datos): migraciones no reconstruibles desde cero (0005), `template1` con collation
inconsistente, filtro de jerarquía "(Vacías)" + valores devuelve vacío, avisos de `npm audit`, API sin autenticación.

## Backend (Django) — `python manage.py test works4cdp --settings=data4cdp_v1.settings_test`
```
Creating test database for alias 'default' ('test_mydb')...
test_assay_con_chemical_id_repetido_por_api_devuelve_400 (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_autofill_asigna_en_orden_natural_solo_a_los_vacios (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_autofill_errores (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_autofill_filtra_por_fecha (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_autofill_reassign_recalcula_todos_desde_el_maximo (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_next_chemical_id_continua_la_serie (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_next_chemical_id_errores (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_next_chemical_id_sin_datos_usa_la_base_de_la_planta (works4cdp.tests.test_api.ChemicalIdEndpointsTests) ... ok
test_assays_acepta_user_y_sample_id (works4cdp.tests.test_api.ContratoConElFrontendTests) ... ok
test_taskp_acepta_estado_id (works4cdp.tests.test_api.ContratoConElFrontendTests) ... ok
test_users_acepta_group_y_no_group_id (works4cdp.tests.test_api.ContratoConElFrontendTests) ... ok
test_filtros_year_week_date_mapean_a_creation_date (works4cdp.tests.test_api.CorrectiveTaskFilterTests) ... ok
test_ids_invalidos_se_ignoran (works4cdp.tests.test_api.DeleteImpactTests) ... ok
test_impacto_de_area_y_sistema (works4cdp.tests.test_api.DeleteImpactTests) ... ok
test_impacto_de_equipo_por_post (works4cdp.tests.test_api.DeleteImpactTests) ... ok
test_impacto_de_planta_por_get (works4cdp.tests.test_api.DeleteImpactTests) ... ok
test_recurso_inexistente_devuelve_404 (works4cdp.tests.test_api.EndpointsBasicosTests) ... ok
test_schema_de_assays_incluye_campos_de_laboratorio (works4cdp.tests.test_api.EndpointsBasicosTests) ... ok
test_todos_exponen_schema_con_los_campos_del_modelo (works4cdp.tests.test_api.EndpointsBasicosTests) ... ok
test_todos_los_listados_responden_paginados (works4cdp.tests.test_api.EndpointsBasicosTests) ... ok
test_filtro_de_assays_por_equipo_de_la_muestra (works4cdp.tests.test_api.FiltrosYPaginacionTests) ... ok
test_filtros_icontains_e_in (works4cdp.tests.test_api.FiltrosYPaginacionTests) ... ok
test_ordenamiento (works4cdp.tests.test_api.FiltrosYPaginacionTests) ... ok
test_paginacion_por_defecto_y_page_size (works4cdp.tests.test_api.FiltrosYPaginacionTests) ... ok
test_borrar_planta_borra_en_cascada (works4cdp.tests.test_api.PlantCrudTests) ... ok
test_ciclo_completo_crear_leer_editar_borrar (works4cdp.tests.test_api.PlantCrudTests) ... ok
test_validacion_campos_obligatorios_y_longitud (works4cdp.tests.test_api.PlantCrudTests) ... ok
test_delega_en_el_servicio (works4cdp.tests.test_api.SyncEquipmentEndpointTests) ... ok
test_error_inesperado_devuelve_500_controlado (works4cdp.tests.test_api.SyncEquipmentEndpointTests) ... ok
test_requiere_equipment_id_y_fecha_valida (works4cdp.tests.test_api.SyncEquipmentEndpointTests) ... ok
test_estado_por_defecto_es_pendiente (works4cdp.tests.test_api.TaskPEstadoDefaultTests) ... ok
test_excluye_tareas_huerfanas (works4cdp.tests.test_api.TaskPTests) ... ok
test_get_devuelve_tareas_y_calendario (works4cdp.tests.test_api.WeeklyTaskViewTests) ... ok
test_get_semana_sin_datos (works4cdp.tests.test_api.WeeklyTaskViewTests) ... ok
test_get_valida_parametros (works4cdp.tests.test_api.WeeklyTaskViewTests) ... ok
test_post_actualiza_estados (works4cdp.tests.test_api.WeeklyTaskViewTests) ... ok
test_post_invalido_no_guarda_nada (works4cdp.tests.test_api.WeeklyTaskViewTests) ... ok
test_psol_manual_no_se_sobrescribe (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_psol_no_se_calcula_si_falta_un_peso (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_psol_no_se_calcula_si_peso_neto_no_es_positivo (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_psol_se_calcula_desde_los_pesos (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_psol_se_redondea_a_dos_decimales (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_timestamp_combina_fecha_y_hora_con_zona (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_timestamp_se_actualiza_al_cambiar_fecha (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_timestamp_usa_medianoche_si_no_hay_hora (works4cdp.tests.test_models.AssaySaveTests) ... ok
test_representaciones_de_texto (works4cdp.tests.test_models.StrTests) ... ok
test_chemical_id_nulo_es_valido (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_nan_se_serializa_como_null (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_permite_conservar_su_propio_chemical_id_al_editar (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_rechaza_chemical_id_repetido (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_sample_se_lee_anidado_y_se_escribe_por_id (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_timestamp_es_solo_lectura (works4cdp.tests.test_serializers.AssaySerializerTests) ... ok
test_user_id_y_group_id_son_obligatorios_al_crear (works4cdp.tests.test_serializers.CalendarSerializerTests) ... ok
test_estado_id_es_obligatorio (works4cdp.tests.test_serializers.TaskPSerializerTests) ... ok
test_lee_relaciones_anidadas_y_escribe_ids (works4cdp.tests.test_serializers.TaskPSerializerTests) ... ok
test_asigna_codigo_a_ensayos_previos_sin_chemical_id (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_continua_la_serie_existente_e_ignora_timestamps_unix (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_equipo_sin_ip_configurada (works4cdp.tests.test_services.AssaySyncServiceTests) ... El equipo con ID 999999 no tiene una dirección IP configurada.
ok
test_equipo_sin_muestras (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_es_idempotente (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_ignora_lecturas_de_otra_fecha_y_duplicadas_en_el_mismo_archivo (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_inserta_y_asigna_chemical_id_en_orden_natural (works4cdp.tests.test_services.AssaySyncServiceTests) ... ok
test_base_por_equipo_sin_planta (works4cdp.tests.test_services.NextChemicalIdTests) ... ok
test_base_por_planta_sin_datos (works4cdp.tests.test_services.NextChemicalIdTests) ... ok
test_build_timestamp (works4cdp.tests.test_services.AssayTransformerTests) ... ok
test_clean_string (works4cdp.tests.test_services.AssayTransformerTests) ... ok
test_parse_date_formatos_soportados (works4cdp.tests.test_services.AssayTransformerTests) ... ok
test_parse_date_invalida (works4cdp.tests.test_services.AssayTransformerTests) ... Formato de fecha no reconocido recibido de API: '31.02.2026'
Formato de fecha no reconocido recibido de API: 'ayer'
ok
test_parse_float_acepta_coma_decimal (works4cdp.tests.test_services.AssayTransformerTests) ... ok
test_parse_int_redondea_y_tolera_basura (works4cdp.tests.test_services.AssayTransformerTests) ... ok
test_parse_time (works4cdp.tests.test_services.AssayTransformerTests) ... Formato de hora no reconocido recibido de API: '25:00'
ok
test_error_de_red_devuelve_lista_vacia (works4cdp.tests.test_services.CLBClientTests) ... No se pudo obtener datos del Courier 10.0.0.1 para tag 'c_01_s01': caído
ok
test_lee_la_lista_por_tag_en_minusculas (works4cdp.tests.test_services.CLBClientTests) ... ok
test_modo_dev_devuelve_datos_simulados_sin_red (works4cdp.tests.test_services.CLBClientTests) ... ok
test_assay_sort_key_tolera_muestra_hora_e_instancia_nulas (works4cdp.tests.test_services.SortKeyTests) ... ok
test_orden_natural (works4cdp.tests.test_services.SortKeyTests) ... ok

----------------------------------------------------------------------
Ran 76 tests in 2.198s

OK
Destroying test database for alias 'default' ('test_mydb')...
Found 76 test(s).
    Creating table django_admin_log
    Creating table auth_permission
    Creating table auth_group
    Creating table auth_user
    Creating table django_content_type
    Creating table django_session
    Creating table works4cdp_estado
    Creating table works4cdp_plant
    Creating table works4cdp_area
    Creating table works4cdp_system
    Creating table works4cdp_equipment
    Creating table works4cdp_taskcatalog
    Creating table works4cdp_task
    Creating table works4cdp_userp
    Creating table works4cdp_user
    Creating table works4cdp_calendar
    Creating table works4cdp_taskp
    Creating table works4cdp_taskgroupassignment
    Creating table works4cdp_correctivetask
    Creating table works4cdp_sample
    Creating table works4cdp_assay
    Creating table works4cdp_assayspsi
    Running deferred SQL...
  No migrations to apply.
System check identified no issues (0 silenced).
```

## Frontend (Vitest) — `npm test`
```

 RUN  v3.2.4 /app/vue_app

 ✓ tests/gridHelpers.test.js > sanitizeValue > convierte vacíos en null 5ms
 ✓ tests/gridHelpers.test.js > sanitizeValue > recorta espacios y conserva el texto 1ms
 ✓ tests/gridHelpers.test.js > sanitizeValue > cambia la coma decimal por punto solo en campos numéricos 1ms
 ✓ tests/gridHelpers.test.js > sanitizeValue > no altera números ni el cero 1ms
 ✓ tests/gridHelpers.test.js > mapGridKeyToPayload > usa los campos de escritura de los serializers 1ms
 ✓ tests/gridHelpers.test.js > mapGridKeyToPayload > envía user y group con su nombre real (AssaySerializer y UserSerializer) 1ms
 ✓ tests/gridHelpers.test.js > mapGridKeyToPayload > en la grilla de tareas programadas group se envía como group_id 0ms
 ✓ tests/gridHelpers.test.js > mapGridKeyToPayload > deja igual el resto de claves 1ms
 ✓ tests/gridHelpers.test.js > buildPayloadFromRow > arma el payload de un ensayo 3ms
 ✓ tests/gridHelpers.test.js > buildPayloadFromRow > omite las columnas de solo lectura con "__" 1ms
 ✓ tests/useApi.test.js > useApi > activa loading durante la llamada y devuelve el resultado 4ms
 ✓ tests/useApi.test.js > useApi > formatea el error del servidor y lo relanza 2ms
 ✓ tests/useApi.test.js > useApi > usa el mensaje personalizado si se indica 1ms
 ✓ tests/useApi.test.js > useApi > errores sin respuesta del servidor (red caída) 0ms
 ✓ tests/useApi.test.js > useApi > limpia el error anterior al reintentar 0ms
[@vue/compiler-sfc] `defineProps` is a compiler macro and no longer needs to be imported.

 ✓ tests/useEquipmentHierarchies.test.js > loadDependencies > carga los cuatro catálogos con page_size alto 4ms
 ✓ tests/useEquipmentHierarchies.test.js > loadDependencies > si la API falla no lanza error y deja las listas vacías 1ms
 ✓ tests/useEquipmentHierarchies.test.js > getEquipmentHierarchyRow > devuelve los nombres de la jerarquía de un equipo 1ms
 ✓ tests/useEquipmentHierarchies.test.js > getEquipmentHierarchyRow > con un equipo desconocido devuelve textos vacíos 0ms
 ✓ tests/useEquipmentHierarchies.test.js > buildFilterParams > sin filtros devuelve los parámetros base 1ms
 ✓ tests/useEquipmentHierarchies.test.js > buildFilterParams > filtro estándar -> campo__in y (Vacías) -> campo__isnull 1ms
 ✓ tests/useEquipmentHierarchies.test.js > buildFilterParams > filtro por planta se traduce a equipment__in con los equipos de esa planta 1ms
 ✓ tests/useEquipmentHierarchies.test.js > buildFilterParams > filtros de jerarquía combinados se intersectan 0ms
 ✓ tests/useEquipmentHierarchies.test.js > buildFilterParams > filtro directo por equipo 0ms
 ✓ tests/components.test.js > BaseTable > muestra encabezados capitalizados y una fila por elemento 28ms
 ✓ tests/components.test.js > BaseTable > sin datos muestra el mensaje ocupando todas las columnas 5ms
 ✓ tests/components.test.js > router > registra todas las vistas 1ms
 ✓ tests/components.test.js > router > cada ruta resuelve a un componente que se puede cargar 1368ms

 Test Files  4 passed (4)
      Tests  28 passed (28)
   Start at  19:08:01
   Duration  2.81s (transform 1.09s, setup 0ms, collect 655ms, tests 1.44s, environment 3.04s, prepare 408ms)

```

## Calidad de datos (base real, solo lectura) — `python manage.py qa_db`
```
[AVISO] ASSAY-01 Ensayos con chemical_id repetido (< 100000): 10
          (5084, 2)
          (5623, 2)
          (5309, 2)
          (5624, 2)
          (26427, 2)
[AVISO] ASSAY-02 Ensayos con chemical_id >= 100000 (timestamps Unix históricos): 1153
          (11857, 1740589303, datetime.date(2025, 2, 26))
          (12493, 1740589447, datetime.date(2025, 2, 26))
          (13269, 1740589435, datetime.date(2025, 2, 26))
          (12049, 1740589442, datetime.date(2025, 2, 26))
          (11470, 1740589445, datetime.date(2025, 2, 26))
[AVISO] ASSAY-03 Ensayos duplicados por clave natural (muestra, fecha, hora, instancia): 17
          (8, datetime.date(2024, 10, 25), datetime.time(9, 44, 8), 24181, 2)
          (31, datetime.date(2025, 12, 18), datetime.time(10, 35, 27), 1766072038, 2)
          (26, datetime.date(2021, 10, 19), datetime.time(17, 43, 8), 1634682047, 2)
          (5, datetime.date(2025, 8, 6), datetime.time(16, 26, 42), 348028, 2)
          (28, datetime.date(2025, 12, 18), datetime.time(10, 39, 47), 1766072046, 2)
[AVISO] ASSAY-04 Ensayos con fecha anterior a 2015 o futura: 25
          (251, datetime.date(2002, 1, 12), 12)
          (585, datetime.date(2002, 1, 14), 15)
          (586, datetime.date(2002, 1, 12), 15)
          (587, datetime.date(2002, 1, 12), 15)
          (873, datetime.date(2002, 1, 12), 16)
[OK]    ASSAY-05 Ensayos sin muestra
[OK]    ASSAY-06 Ensayos con timestamp distinto de fecha + hora
[AVISO] ASSAY-07 Ensayos con %Sol fuera de 0..100: 1
          (9980, 295.0)
[AVISO] ASSAY-08 Ensayos con pesos negativos o peso seco mayor que el neto: 2
          (15637, 113.5, 113.5, 180.0)
          (9980, 114.5, 174.5, 177.0)
[AVISO] TASKP-01 Tareas programadas huérfanas (sin plantilla ni correctiva): 8
          (7459, datetime.date(2026, 6, 22))
          (7461, datetime.date(2026, 6, 22))
          (7465, datetime.date(2026, 6, 23))
          (7469, datetime.date(2026, 6, 24))
          (7473, datetime.date(2026, 6, 25))
[OK]    TASKP-02 Tareas reprogramadas sin fecha de reprogramación
[OK]    TASKP-03 reschedule_user_id que no corresponde a ningún usuario
[OK]    TASKP-04 Fecha que no coincide con el año registrado
[OK]    ESTADO-01 El estado por defecto de TaskP no existe o no es "P" (Pendiente)
[OK]    CAL-01 Calendario duplicado (misma fecha, grupo y turno)
[OK]    CAL-02 Calendario sin grupo ni usuario
[OK]    EQ-01 Equipos sin área asignada
[OK]    SAMPLE-01 Muestras con tag repetido dentro del mismo equipo
[OK]    SAMPLE-02 Muestras sin tag
[AVISO] USER-01 Usuarios de la app sin login de Django vinculado: 5
          (2, 'Pool', 'Mendoza')
          (4, 'Sharon', 'Riquelme')
          (3, 'Eder', 'Aliaga')
          (5, 'Alexandra', 'Flores')
          (1, 'Adolfo', 'Ccallo')
[OK]    DB-01 works4cdp_assay no es hypertable de TimescaleDB
20 chequeos, 8 con avisos.
```
