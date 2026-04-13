<template>
  <!-- Contenedor principal de la vista de mantenimiento para las Plantillas de Tareas (Modelo Task) -->
  <div class="generic-view">
    <!-- Instanciamos el componente ExcelGrid pasándole las propiedades y eventos necesarios para visualizar y editar la tabla Task -->
    <ExcelGrid
      title="Mantenimiento de Plantillas de Tareas (Task)"
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
    <div v-if="loading" class="loading-overlay">Cargando tareas...</div>
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
import { useApi } from './useApi';
// Importamos el composable que encapsula toda la lógica de la jerarquía de equipos
import { useEquipmentHierarchies } from './useEquipmentHierarchies';

// 1. Definimos los nombres visibles de las columnas para el componente de tabla
const headers = [
  'ID', 'Nombre', 'Duración (hrs)', 'Trabajadores', 'Frecuencia', 
  'Fecha de Inicio', 'Descripción', 'Planta', 'Área', 'Sistema', 'Equipo Asignado', 'Procedimiento', 'Turno'
];

// 2. Mapeamos las claves exactas según los campos del modelo Task en backend/works4cdp/models.py
// Agregamos nombres con doble guión bajo ('__') para las columnas de Planta, Área y Sistema, 
// lo cual es compatible con los filtros por defecto de Django y nos servirá para ignorarlas
// a la hora de guardar, ya que esos campos no pertenecen a la tabla Task directamente.
const colKeys = [
  'id', 'name', 'duration', 'workers', 'frequency', 
  'start_date', 'description', 'equipment__area__plant__name', 'equipment__area__name', 'equipment__system__name', 'equipment', 'procedure', 'turn'
];

// --- Variables Reactivas para los Datos ---
// Almacena la matriz bidimensional de datos mapeados que requiere ExcelGrid
const gridData = ref([]);
// Almacena los datos completos requeridos por los filtros de ExcelGrid
const filterData = ref([]);

// Extraemos estados globales (loading y error) junto con la función 'execute' para envolver promesas
const { loading, error, execute } = useApi();

// Instanciamos el composable para delegar la carga y filtrado de la jerarquía
const { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams } = useEquipmentHierarchies();

// --- Estado para Paginación, Filtros y Ordenamiento ---
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });

// --- Configuración Especial para Columnas del Grid ---
const columnsConfig = computed(() => {
    return {
        // Configuramos los índices 7, 8 y 9 (Planta, Área y Sistema) como columnas de solo lectura
        7: { readOnly: true },
        8: { readOnly: true },
        9: { readOnly: true },
        // El índice 10 corresponde a la columna 'Equipo Asignado'
        10: {
            type: 'select', // Define la celda como un menú desplegable (dropdown)
            // Generamos dinámicamente las opciones del selector cruzando la información de los equipos
            options: equipmentsList.value.map(eq => {
                // Asignamos valores por defecto si viene vacío
                const equipoName = eq.name || 'Equipo sin nombre';
                const equipoDesc = eq.description ? ` - ${eq.description}` : '';

                // Concatenamos únicamente el Nombre y la Descripción del Equipo
                const fullLabel = `${equipoName}${equipoDesc}`;

                // Retornamos la estructura que el dropdown necesita: { value: <id>, label: <texto> }
                return {
                    value: eq.id,
                    label: fullLabel
                };
            }).sort((a, b) => a.label.localeCompare(b.label)) // Ordenamos alfabéticamente para facilitar la selección al usuario
        }
    };
});

// --- Funciones Auxiliares ---
// Extrae resultados de forma segura contemplando la paginación estándar de Django REST Framework
const extractData = (res) => res.data.results || res.data || [];

// Descarga un universo más grande de Tareas para que los filtros de la cabecera funcionen correctamente
const loadFilterData = async () => {
    try {
        const res = await api.get('tasks/', { params: { page_size: 10000 } });
        const results = extractData(res);

        // Construimos el array bidimensional para los menús de filtro en el mismo orden que colKeys
        filterData.value = results.map(t => {
            // Buscamos las relaciones para poder incluirlas en los filtros
            const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
            const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);

            return [
                t.id, 
                t.name || '', 
                t.duration || '', 
                t.workers || '', 
                t.frequency || '', 
                t.start_date || '', 
                t.description || '', 
                plantName, // Filtro Planta
                areaName,  // Filtro Área
                systemName,   // Filtro Sistema
                eqId,                // Filtro Equipo
                t.procedure || '', 
                t.turn || ''
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

        // Usamos el composable para construir los parámetros de filtro, incluyendo la jerarquía
        const hierarchyIndexes = { plant: '7', area: '8', system: '9', equipment: '10' };
        params = buildFilterParams(params, currentFilters.value, colKeys, hierarchyIndexes);

        // Si hay un ordenamiento, enviamos el comando de DRF pertinente (agregando '-' si es descendente)
        if (currentSort.value.colIndex !== null) {
            const fieldName = colKeys[currentSort.value.colIndex];
            // Solo permitimos ordenar por campos directos del modelo Task para evitar errores
            if (fieldName && !fieldName.includes('__')) {
                params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
            }
        }

        // Pedimos los datos al endpoint de Task
        const resTasks = await api.get('tasks/', { params });
        const responseData = resTasks.data;
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
            // Extraemos el ID del equipo asignado a esta tarea
            const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
            const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);

            return [
                t.id, 
                t.name || '', 
                t.duration || '', 
                t.workers || '', 
                t.frequency || '', 
                t.start_date || '', 
                t.description || '', 
                plantName, // Columna Planta (índice 7)
                areaName,  // Columna Área (índice 8)
                systemName,   // Columna Sistema (índice 9)
                eqId,                // Columna Equipo Asignado (índice 10, ID para el select)
                t.procedure || '', 
                t.turn || ''
            ];
        });
    }, 'Error al cargar la lista de tareas desde la base de datos.');
};

// --- Eventos Disparados por ExcelGrid ---
const handlePageChange = (p) => loadData(p);
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
const handleFilterChange = (f) => { currentFilters.value = f; loadData(1); };
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// Maneja la lógica CRUD para crear Tareas nuevas (POST) o editar las existentes (PUT)
const handleSave = async (updatedGrid) => {
    try {
        await execute(async () => {
            // Iteramos sobre las filas recibidas y creamos una Promesa de red para cada una
            const promises = updatedGrid.map(row => {
                const payload = {};
                // Emparejamos cada celda editada con el nombre de columna correspondiente que pide el backend
                colKeys.forEach((key, idx) => {
                    // Evitamos enviar columnas de solo lectura (Planta, Área, Sistema) identificadas por la nomenclatura '__'
                    if (key.includes('__')) return;
                    
                    let val = row[idx] === '' ? null : row[idx];
                    payload[key] = val;
                });

                // Determinamos la existencia basada en un ID válido
                const id = payload.id;
                const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));

                if (isExisting) {
                    // Actualiza la tarea usando su Primary Key
                    return api.put(`tasks/${id}/`, payload);
                } else {
                    // Almacena un registro totalmente nuevo
                    delete payload.id;
                    return api.post('tasks/', payload);
                }
            });

            // Lanzamos todas las peticiones concurrentemente
            await Promise.all(promises);
            alert('Tareas de mantenimiento guardadas correctamente.');
            
            // Refrescamos toda la vista para ver los nuevos IDs otorgados por la base de datos
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        alert('Error al guardar. Verifique que los campos numéricos o fechas (YYYY-MM-DD) sean válidos.');
    }
};

// Elimina filas permanentemente (DELETE)
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;
    try {
        await execute(async () => {
            const promises = idsToDelete.map(id => api.delete(`tasks/${id}/`));
            await Promise.all(promises);
            alert(`${idsToDelete.length} tarea(s) eliminada(s).`);
            
            // Refrescamos para purgar las filas ya borradas visualmente
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        alert('No se pudo eliminar la tarea. Podría estar asignada a un registro histórico del calendario.');
    }
};

// --- Hook del Ciclo de Vida de Vue ---
onMounted(async () => {
    // El orden de ejecución es crítico:
    // 1. Obtener opciones foráneas (Plantas, Áreas, Sistemas, Equipos)
    await loadDependencies();
    // 2. Traer las tareas actuales aplicando formato a la columna de equipos
    await loadData();
    // 3. Rellenar opciones de filtro
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