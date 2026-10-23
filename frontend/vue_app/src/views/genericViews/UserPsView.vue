<template>
  <!-- Contenedor principal de la vista de mantenimiento de Grupos -->
  <div class="generic-view">
    <!-- Instanciamos el componente ExcelGrid pasándole las propiedades necesarias -->
    <ExcelGrid
      title="Mantenimiento de Grupos (UserP)"
      :headers="headers"
      :data="gridData"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :totalItems="totalItems"
      :pageSize="pageSize"
      :serverSideFiltering="true"
      :filterValuesLoader="filterValuesLoader"
      @save="handleSave"
      @delete="handleDelete"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
    />
    
    <!-- Muestra una capa superpuesta de carga si la variable loading es verdadera -->
    <div v-if="loading" class="loading-overlay">Cargando grupos...</div>
    <!-- Muestra un mensaje de error en color rojo si la petición falla -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importamos las utilidades de reactividad y ciclo de vida de Vue
import { ref, onMounted } from 'vue';
// Importamos el componente reutilizable de grilla
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos la instancia de Axios para las peticiones a la API
import { api } from '../../api';
import { buildGridParams, createGridValuesLoader } from '../../utils/gridQuery';
// Importamos el composable global que maneja automáticamente loading y error
import { useApi } from '../../composables/useApi';
// Importamos la función de utilidades compartida para construir el payload sanitizado
import { buildPayloadFromRow } from '../../utils/gridHelpers';

// Definimos los nombres visibles de las columnas (Sin Descripción)
const headers = ['ID', 'Nombre del Grupo'];
// Ajustamos a las claves nativas de tu base de datos
const colKeys = ['id', 'name'];

// Creamos la variable reactiva que almacenará la matriz de datos para la grilla
const gridData = ref([]);

// Extraemos las propiedades reactivas y la función ejecutora de nuestro composable
const { loading, error, execute } = useApi();

// --- Estado de Paginación y Filtrado ---
// Página actual de la tabla (inicia en 1)
const currentPage = ref(1);
// Total de páginas calculadas según los registros
const totalPages = ref(1);
// Total de ítems en la base de datos
const totalItems = ref(0);
// Cantidad de registros mostrados por página
const pageSize = ref(25);
// Objeto que almacena los filtros activos aplicados por columna
const currentFilters = ref({});
// Objeto que almacena la configuración de ordenamiento (columna y dirección)
const currentSort = ref({ colIndex: null, direction: null });
// Especificación de filtros de ExcelGrid para la API ({ in|not_in, empty } por columna).
const currentSpecs = ref({});
// Campo de la API que corresponde a cada columna de la grilla (por índice).
const colToField = colKeys;
// Carga los valores del menú de filtros desde el servidor (solo la columna abierta).
const filterValuesLoader = createGridValuesLoader('userp', colToField);

// Función principal que trae los grupos aplicando la paginación y filtros
const loadData = async (page = 1) => {
    // Envolvemos la llamada para mostrar el spinner
    await execute(async () => {
        // Parámetros de petición
        const params = { page, page_size: pageSize.value };
        
        // Filtros y orden de ExcelGrid (grid_filters + ordering, ver utils/gridQuery.js)
        Object.assign(params, buildGridParams({ specs: currentSpecs.value, sort: currentSort.value, colToField }));

        // Ejecutamos la petición GET al endpoint de UserP
        const res = await api.get('userp/', { params });
        const responseData = res.data;
        let dataArray = [];

        // Parseo seguro dependiente de la configuración de DRF
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

        // Transformamos los diccionarios en arrays planos para ExcelGrid
        gridData.value = dataArray.map(item => colKeys.map(k => item[k] || ''));
    }, 'Error al cargar la lista de grupos.');
};

// Enlaces funcionales desde el componente hijo hacia las lógicas locales
const handlePageChange = (p) => loadData(p);
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
const handleFilterChange = (f, specs = {}) => { currentFilters.value = f; currentSpecs.value = specs; loadData(1); };
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// Función que guarda las ediciones o creaciones enviadas desde ExcelGrid
const handleSave = async (updatedGrid) => {
    try {
        await execute(async () => {
            // Iteramos fila por fila y generamos las peticiones correspondientes
            const promises = updatedGrid.map(row => {
                // Vinculamos de vuelta las celdas a los identificadores del backend usando la utilidad compartida
                const payload = buildPayloadFromRow(row, colKeys);
                
                // Extraemos el ID y validamos que sea estrictamente un número
                const id = payload.id;
                const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));
                
                if (isExisting) {
                    return api.put(`userp/${id}/`, payload);
                } else {
                    // Si es nuevo (sin ID), creamos el registro
                    delete payload.id;
                    return api.post('userp/', payload);
                }
            });
            // Esperamos que todas las transacciones finalicen
            await Promise.all(promises);
            alert('Grupos guardados correctamente.');
            // Refrescamos la UI para obtener los IDs nuevos generados por la BD
            await loadData(currentPage.value);
        });
    } catch (e) {
        alert('Error al guardar grupos. Revisa los datos.');
    }
};

// Función para eliminar filas seleccionadas desde ExcelGrid
const handleDelete = async (idsToDelete) => {
    // Abortamos si no hay IDs para borrar
    if (!idsToDelete || idsToDelete.length === 0) return;
    try {
        await execute(async () => {
            // Generamos una promesa de DELETE por cada registro
            const promises = idsToDelete.map(id => api.delete(`userp/${id}/`));
            await Promise.all(promises);
            alert(`${idsToDelete.length} grupo(s) eliminado(s).`);
            // Forzamos actualización de vista
            await loadData(currentPage.value);
        });
    } catch (e) {
        alert('Error al eliminar grupos. Es posible que tengan dependencias.');
    }
};

// Se dispara inmediatamente después de que el componente carga en pantalla
onMounted(() => {
    loadData();
});
</script>

<style scoped>
/* Contenedor relativo para alojar elementos absolutos (overlay) */
.generic-view { position: relative; height: 100%; }
/* Pantalla de bloqueo blanca y transparente mientras dura una petición */
.loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; font-weight: bold; z-index: 100; }
/* Formato para destacar errores provenientes del catch */
.error-message { color: red; padding: 10px; text-align: center; }
</style>