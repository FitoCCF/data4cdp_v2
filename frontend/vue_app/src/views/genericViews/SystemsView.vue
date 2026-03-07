<template>
  <div class="systems-view">
    <!--
      Componente ExcelGrid reutilizable
      - title: Título de la tabla
      - headers: Array con los nombres de las columnas
      - data: Matriz de datos
      - save: Evento emitido al guardar cambios
      - delete: Evento emitido al eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Sistemas"
      :headers="headers"
      :data="systemsData"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :totalItems="totalItems"
      :pageSize="pageSize"
      :serverSideFiltering="true"
      :filterData="filterData"
      @save="handleSave"
      @delete="handleDelete"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
    />
    
    <!-- Indicador de carga -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';

// Configuración de columnas para la tabla de Sistemas
const headers = ['ID', 'Tag', 'Nombre', 'Descripción'];

// Estado reactivo
const systemsData = ref([]); // Almacena los datos en formato matriz
const loading = ref(false);  // Controla la visibilidad del loader
const error = ref(null);     // Almacena mensajes de error

// Estado Paginación y Filtrado
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]); // Datos completos para el popup de filtros

const loadFilterData = async () => {
    try {
        const response = await api.get('systems/', { params: { page_size: 10000 } });
        const results = response.data.results || response.data;
        filterData.value = results.map(s => [
            s.id,
            s.tag || '',
            s.name || '',
            s.description || ''
        ]);
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

/**
 * Carga los datos de sistemas desde la API
 */
const loadData = async (page = 1) => {
  loading.value = true;
  error.value = null;

  try {
    const params = { 
        page, 
        page_size: pageSize.value 
    };

    const colToFieldMap = {
        0: 'id',
        1: 'tag',
        2: 'name',
        3: 'description'
    };

    for (const [colIndex, values] of Object.entries(currentFilters.value)) {
        const fieldName = colToFieldMap[colIndex];
        if (fieldName && values.length > 0) {
            params[`${fieldName}__in`] = values.join(','); 
        }
    }

    if (currentSort.value.colIndex !== null) {
        const fieldName = colToFieldMap[currentSort.value.colIndex];
        if (fieldName) {
            params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
        }
    }

    // Petición GET al endpoint de sistemas
    const response = await api.get('systems/', { params });
    const responseData = response.data;
    let dataArray = [];

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
    } else {
        console.warn('La API no devolvió un formato válido:', responseData);
    }

    // Transformar array de objetos a matriz de arrays para ExcelGrid
    // Mapeo: [id, tag, name, description]
    systemsData.value = dataArray.map(s => [
        s.id,
        s.tag || '',
        s.name || '',
        s.description || ''
    ]);

  } catch (err) {
    console.error('Error cargando sistemas:', err);
    error.value = 'Error al cargar los datos de la base de datos.';
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage) => {
    loadData(newPage);
};

const handlePageSizeChange = (newSize) => {
    pageSize.value = newSize;
    loadData(1);
};

const handleFilterChange = (filters) => {
    currentFilters.value = filters;
    loadData(1);
};

const handleSortChange = (sortConfig) => {
    currentSort.value = sortConfig;
    loadData(1);
};

/**
 * Maneja el guardado de cambios (Creación y Edición)
 * @param {Array} updatedGrid - Matriz con los datos modificados
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    // Iterar sobre cada fila para determinar si es update o create
    const promises = updatedGrid.map(async (row) => {
        const id = row[0]; // ID está en la primera columna
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3]
        };

        // Si tiene ID válido, es una actualización (PUT)
        if (id && String(id).trim() !== '') {
            return api.put(`systems/${id}/`, payload);
        } else {
            // Si no tiene ID, es una creación (POST)
            // Solo crear si hay datos mínimos (tag o nombre)
            if (payload.tag || payload.name) {
                return api.post('systems/', payload);
            }
        }
    });

    // Esperar a que todas las peticiones terminen
    await Promise.all(promises);

    alert('Cambios guardados correctamente.');

    // Recargar datos para obtener IDs nuevos y asegurar sincronización
    await loadData();
    await loadFilterData();

  } catch (err) {
    console.error('Error guardando sistemas:', err);
    alert('Error al guardar los cambios en la base de datos.');
  } finally {
    loading.value = false;
  }
};

/**
 * Maneja la eliminación de filas
 * @param {Array} idsToDelete - Array de IDs a eliminar
 */
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    loading.value = true;
    try {
        const deletePromises = idsToDelete.map(id => api.delete(`systems/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);
        await loadFilterData();

    } catch (err) {
        console.error('Error eliminando sistemas:', err);
        alert('Error al eliminar las filas.');
    } finally {
        await loadData();
        loading.value = false;
    }
};

// Cargar datos al montar el componente
onMounted(() => {
  loadData();
  loadFilterData();
});
</script>

<style scoped>
.systems-view {
  position: relative;
  height: 100%;
}

/* Overlay de carga centrado */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255,255,255,0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  z-index: 100;
}

/* Estilo para mensajes de error */
.error-message {
  color: red;
  padding: 10px;
  text-align: center;
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  margin: 10px;
  border-radius: 4px;
}
</style>
