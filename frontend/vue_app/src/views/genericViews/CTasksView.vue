<template>
  <!-- Contenedor principal de la vista de mantenimiento para las Tareas Correctivas (Modelo CorrectiveTask) -->
  <div class="generic-view">
    <!-- Instanciamos el componente ExcelGrid pasándole las propiedades y eventos necesarios para visualizar y editar la tabla CorrectiveTask -->
    <ExcelGrid
      title="Mantenimiento de Tareas Correctivas (CorrectiveTask)"
      :headers="headers"
      :data="gridData"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :totalItems="totalItems"
      :pageSize="pageSize"
      :serverSideFiltering="true"
      :filterData="filterData"
      :columnsConfig="columnsConfig"
      @save="handleSave"
      @delete="handleDelete"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
    />
    
    <!-- Overlay de estado: Muestra una capa superpuesta de carga si la variable 'loading' es verdadera -->
    <div v-if="loading" class="loading-overlay">Cargando tareas correctivas...</div>
    <!-- Feedback visual: Muestra un mensaje de error en color rojo si alguna de las peticiones falla -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importamos las utilidades de reactividad y ciclo de vida del framework Vue 3
import { ref, onMounted, computed } from 'vue';
// Importamos el componente reutilizable de grilla que permite la edición estilo Excel
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos la instancia configurada de Axios para realizar las peticiones HTTP a Django
import { api } from '../../api';
// Importamos el composable global que maneja automáticamente los estados de loading y error
import { useApi } from '../../composables/useApi';
// Importamos el composable que encapsula toda la lógica de la jerarquía de equipos
import { useEquipmentHierarchies } from '../../composables/useEquipmentHierarchies';

// 1. Definimos los nombres visibles de las columnas para el componente de tabla
const headers = [
  'ID', 'Categoría de Tarea', 'Nombre Manual', 'Planta', 'Área', 'Sistema', 'Equipo Asignado', 
  'Descripción', 'Causa Raíz', 'Fecha de Reporte', 'Criticidad', 'Reportado por', 'Turno'
];

// 2. Mapeamos las claves exactas según los campos del modelo CorrectiveTask en backend/works4cdp/models.py
// Agregamos nombres con doble guión bajo ('__') para las columnas de Planta, Área y Sistema de la jerarquía,
// las cuales son de solo lectura y sirven únicamente de apoyo para visualización y filtros.
const colKeys = [
  'id', 'task_catalog', 'name', 'equipment__area__plant__name', 'equipment__area__name', 'equipment__system__name', 'equipment',
  'description', 'root_cause', 'creation_date', 'priority', 'created_by_user', 'turno'
];

// --- Variables Reactivas para los Datos ---
// Almacena la matriz bidimensional de datos mapeados que requiere ExcelGrid
const gridData = ref([]);
// Almacena los datos completos requeridos por los filtros de ExcelGrid
const filterData = ref([]);
// Almacena la lista de usuarios cargada para el dropdown 'Reportado por'
const usersList = ref([]);
// Almacena la lista de tareas del catálogo
const taskCatalogList = ref([]);

// Extraemos estados globales (loading y error) junto con la función 'execute' para envolver promesas
const { loading, error, execute } = useApi();

// Instanciamos el composable para delegar la carga y filtrado de la jerarquía de equipos
const { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams } = useEquipmentHierarchies();

// --- Estado para Paginación, Filtros y Ordenamiento ---
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });

// --- Carga del catálogo de tareas ---
const loadTaskCatalogs = async () => {
    try {
        const res = await api.get('taskcatalogs/', { params: { page_size: 10000 } });
        taskCatalogList.value = res.data.results || res.data || [];
    } catch (e) {
        console.error("Error al cargar el catálogo de tareas:", e);
    }
};

// --- Configuración Especial para Columnas del Grid ---
const columnsConfig = computed(() => {
    return {
        // La columna 1 corresponde a 'Categoría de Tarea' (task_catalog)
        1: {
            type: 'select',
            options: taskCatalogList.value.map(cat => ({
                value: cat.id,
                label: cat.name || 'Sin nombre'
            })).sort((a, b) => a.label.localeCompare(b.label))
        },
        // Configuramos las columnas 3, 4 y 5 (Planta, Área y Sistema) como columnas de solo lectura (antes 2, 3 y 4)
        3: { readOnly: true },
        4: { readOnly: true },
        5: { readOnly: true },
        // La columna 6 corresponde a 'Equipo Asignado' (antes 5)
        6: {
            type: 'select', // Define la celda como un menú desplegable (dropdown)
            // Generamos dinámicamente las opciones del selector cruzando la información de los equipos
            options: equipmentsList.value.map(eq => {
                const equipoName = eq.name || 'Equipo sin nombre';
                const equipoDesc = eq.description ? ` - ${eq.description}` : '';
                const fullLabel = `${equipoName}${equipoDesc}`;
                return {
                    value: eq.id,
                    label: fullLabel
                };
            }).sort((a, b) => a.label.localeCompare(b.label)) // Ordenamos alfabéticamente
        },
        // La columna 11 corresponde a 'Reportado por' (antes 10)
        11: {
            type: 'select', // Define la celda como un menú desplegable
            // Generamos dinámicamente las opciones usando el catálogo de usuarios
            options: usersList.value.map(u => {
                const fullLabel = `${u.nombre || ''} ${u.apellido || ''}`.trim() || 'Usuario sin nombre';
                return {
                    value: u.id,
                    label: fullLabel
                };
            }).sort((a, b) => a.label.localeCompare(b.label)) // Ordenamos alfabéticamente
        }
    };
});

// --- Funciones Auxiliares ---
// Extrae resultados de forma segura contemplando la paginación estándar de Django REST Framework
const extractData = (res) => res.data.results || res.data || [];

// Carga la lista de usuarios completa desde la API para el catálogo
const loadUsers = async () => {
    try {
        const res = await api.get('users/', { params: { page_size: 10000 } });
        usersList.value = extractData(res);
    } catch (e) {
        console.error("Error al cargar la lista de usuarios:", e);
    }
};

// Descarga un universo más grande de Tareas Correctivas para que los filtros de la cabecera funcionen correctamente
const loadFilterData = async () => {
    try {
        const res = await api.get('correctivetasks/', { params: { page_size: 10000 } });
        const results = extractData(res);

        // Construimos el array bidimensional para los menús de filtro en el mismo orden que colKeys
        filterData.value = results.map(t => {
            // Buscamos las relaciones para poder incluirlas en los filtros
            const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
            const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);
            const userId = (t.created_by_user && typeof t.created_by_user === 'object') ? t.created_by_user.id : (t.created_by_user || '');

            return [
                t.id, 
                t.task_catalog || '', 
                t.name || '', 
                plantName, 
                areaName, 
                systemName, 
                eqId, 
                t.description || '', 
                t.root_cause || '', 
                t.creation_date || '', 
                t.priority || '', 
                userId,
                t.turno || ''
            ];
        });
    } catch(e) {
        console.error("Error al cargar los datos para los filtros:", e);
    }
};

// Descarga los datos de la página actual aplicando filtros y ordenamiento que el usuario configuró
const loadData = async (page = 1) => {
    await execute(async () => {
        let params = { page, page_size: pageSize.value };

        // Usamos el composable para construir los parámetros de filtro, incluyendo la jerarquía de equipos
        const hierarchyIndexes = { plant: '3', area: '4', system: '5', equipment: '6' };
        params = buildFilterParams(params, currentFilters.value, colKeys, hierarchyIndexes);

        // Si hay un ordenamiento, enviamos el comando de DRF pertinente (agregando '-' si es descendente)
        if (currentSort.value.colIndex !== null) {
            const fieldName = colKeys[currentSort.value.colIndex];
            // Solo permitimos ordenar por campos directos del modelo CorrectiveTask para evitar errores
            if (fieldName && !fieldName.includes('__')) {
                params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
            }
        }

        // Pedimos los datos al endpoint de CorrectiveTask
        const resCorrective = await api.get('correctivetasks/', { params });
        const responseData = resCorrective.data;
        let dataArray = [];

        // Verificamos y almacenamos de acuerdo a si el backend paginó el resultado o no
        if (responseData && responseData.results) {
            dataArray = responseData.results;
            totalItems.value = responseData.count;
            totalPages.value = Math.ceil(responseData.count / pageSize.value);
            currentPage.value = page;
        } else if (Array.isArray(responseData)) {
            dataArray = responseData;
            totalItems.value = dataArray.length;
            totalPages.value = 1;
            currentPage.value = 1;
        }

        // Mapeamos los diccionarios a una matriz 2D para ser procesada por ExcelGrid
        gridData.value = dataArray.map(t => {
            // Extraemos el ID del equipo asignado a esta tarea correctiva
            const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
            const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);
            const userId = (t.created_by_user && typeof t.created_by_user === 'object') ? t.created_by_user.id : (t.created_by_user || '');

            return [
                t.id, 
                t.task_catalog || '', 
                t.name || '', 
                plantName, 
                areaName, 
                systemName, 
                eqId, 
                t.description || '', 
                t.root_cause || '', 
                t.creation_date || '', 
                t.priority || '', 
                userId,
                t.turno || ''
            ];
        });
    }, 'Error al cargar la lista de tareas correctivas desde la base de datos.');
};

// --- Eventos Disparados por ExcelGrid ---
const handlePageChange = (p) => loadData(p);
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
const handleFilterChange = (f) => { currentFilters.value = f; loadData(1); };
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// Maneja la lógica CRUD para crear Tareas Correctivas nuevas (POST) o editar las existentes (PUT)
const handleSave = async (updatedGrid) => {
    // 1. Validaciones previas en el Frontend para evitar enviar datos inválidos
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    
    for (let i = 0; i < updatedGrid.length; i++) {
        const nameVal = updatedGrid[i][1];          // Nombre (índice 1)
        const eqVal = updatedGrid[i][5];            // Equipo (índice 5)
        const descVal = updatedGrid[i][6];          // Descripción (índice 6)
        const dateVal = updatedGrid[i][8];          // Fecha de Reporte (índice 8)
        const priorityVal = updatedGrid[i][9];      // Prioridad (índice 9)
        const userVal = updatedGrid[i][10];         // Reportado por (índice 10)

        if (!nameVal || String(nameVal).trim() === '') {
            alert(`No se puede guardar: El campo "Nombre" está vacío en la fila ${i + 1}.`);
            return;
        }
        if (!eqVal || String(eqVal).trim() === '') {
            alert(`No se puede guardar: Debe seleccionar un "Equipo Asignado" en la fila ${i + 1}.`);
            return;
        }
        if (!descVal || String(descVal).trim() === '') {
            alert(`No se puede guardar: El campo "Descripción" está vacío en la fila ${i + 1}.`);
            return;
        }
        if (!dateVal || !dateRegex.test(String(dateVal).trim())) {
            alert(`No se puede guardar: La "Fecha de Reporte" en la fila ${i + 1} debe tener formato YYYY-MM-DD.`);
            return;
        }
        if (priorityVal === null || priorityVal === undefined || String(priorityVal).trim() === '' || isNaN(Number(priorityVal))) {
            alert(`No se puede guardar: La "Criticidad" en la fila ${i + 1} debe ser un número entero.`);
            return;
        }
        if (!userVal || String(userVal).trim() === '') {
            alert(`No se puede guardar: Debe seleccionar un usuario en "Reportado por" en la fila ${i + 1}.`);
            return;
        }
    }

    try {
        await execute(async () => {
            // Iteramos sobre las filas recibidas y creamos una Promesa de red para cada una
            const promises = updatedGrid.map(row => {
                const payload = {};
                colKeys.forEach((key, idx) => {
                    if (key.includes('__')) return; // Saltar columnas readonly de la jerarquía
                    
                    let val = row[idx];
                    
                    if (typeof val === 'string') {
                        val = val.trim();
                    }

                    payload[key] = (val === '' || val === null) ? null : val;
                });

                // Determinamos si es un registro existente basado en un ID válido
                const id = payload.id;
                const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));

                if (isExisting) {
                    // Actualiza la tarea correctiva usando su Primary Key
                    return api.put(`correctivetasks/${id}/`, payload);
                } else {
                    // Almacena un registro totalmente nuevo (eliminamos el ID temporal 'nuevo')
                    delete payload.id;
                    return api.post('correctivetasks/', payload);
                }
            });

            // Lanzamos todas las peticiones concurrentemente
            await Promise.all(promises);
            alert('Tareas correctivas guardadas correctamente.');
            
            // Refrescamos toda la vista para ver los nuevos IDs otorgados por la base de datos
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        alert('Error al guardar. Verifique que los campos numéricos o fechas (YYYY-MM-DD) sean válidos y que el backend acepte los datos.');
    }
};

// Elimina filas permanentemente (DELETE)
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;
    try {
        await execute(async () => {
            const promises = idsToDelete.map(id => api.delete(`correctivetasks/${id}/`));
            await Promise.all(promises);
            alert(`${idsToDelete.length} tarea(s) correctiva(s) eliminada(s).`);
            
            // Refrescamos para purgar las filas ya borradas visualmente
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        alert('No se pudo eliminar la tarea correctiva. Podría estar asignada a registros históricos del calendario o ejecuciones de tareas.');
    }
};

// --- Hook del Ciclo de Vida de Vue ---
onMounted(async () => {
    // El orden de ejecución es crítico:
    // 1. Obtener opciones foráneas (Plantas, Áreas, Sistemas, Equipos) de la jerarquía
    await loadDependencies();
    // 1.5 Cargar catálogo de tareas
    await loadTaskCatalogs();
    // 2. Obtener lista de usuarios para el selector
    await loadUsers();
    // 3. Traer las tareas correctivas actuales aplicando formato
    await loadData();
    // 4. Rellenar opciones de filtro
    await loadFilterData();
});
</script>

<style scoped>
/* El contenedor usa alto total y posición relativa para anclar la pantalla de carga */
.generic-view { position: relative; height: 100%; }
/* Capa translúcida que bloquea la interacción con la tabla mientras carga por seguridad */
.loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; font-weight: bold; z-index: 100; }
/* Estilo simple para advertencias de problemas de conexión */
.error-message { color: red; padding: 10px; text-align: center; }
</style>
