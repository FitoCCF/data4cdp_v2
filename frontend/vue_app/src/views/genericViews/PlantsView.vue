<template>
  <div class="plants-view">
    <!--
      Componente ExcelGrid reutilizable
      - @save: Evento para guardar cambios (crear/actualizar)
      - @delete: Evento para eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Plantas"
      :headers="headers"
      :data="plantsData"
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

// Configuración de columnas
const headers = ['ID', 'Tag', 'Nombre', 'Descripción'];

// Estado
const plantsData = ref([]);
const loading = ref(false);
const error = ref(null);

// Estado Paginación y Filtrado
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]);

const loadFilterData = async () => {
    try {
        const response = await api.get('plants/', { params: { page_size: 10000 } });
        const results = response.data.results || response.data;
        filterData.value = results.map(p => [
            p.id,
            p.tag || '',
            p.name || '',
            p.description || ''
        ]);
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

/**
 * Carga los datos de plantas desde la API
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

    const response = await api.get('plants/', { params });
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

    plantsData.value = dataArray.map(p => [
        p.id,
        p.tag || '',
        p.name || '',
        p.description || ''
    ]);

  } catch (err) {
    console.error('Error cargando plantas:', err);
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
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3]
        };

        if (id && String(id).trim() !== '') {
            return api.put(`plants/${id}/`, payload);
        } else {
            if (payload.tag || payload.name) {
                return api.post('plants/', payload);
            }
        }
    });

    await Promise.all(promises);
    alert('Cambios guardados correctamente en la base de datos.');
    await loadData();
    await loadFilterData();
  } catch (err) {
    console.error('Error guardando plantas:', err);
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
        // Crear una promesa de eliminación para cada ID
        const deletePromises = idsToDelete.map(id => api.delete(`plants/${id}/`));

        // Esperar a que todas las eliminaciones se completen
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);

        await loadFilterData();

        // No es necesario recargar los datos, ya que el grid local ya se actualizó.
        // Opcionalmente, se puede recargar para asegurar consistencia total.
        // await loadData();

    } catch (err) {
        console.error('Error eliminando plantas:', err);
        alert('Error al eliminar las filas.');
        // Si falla, recargar los datos para revertir el cambio visual
        await loadData();
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
  loadData();
  loadFilterData();
});
</script>

<style scoped>
.plants-view {
  position: relative;
  height: 100%;
}

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

.error-message {
  color: red;
  padding: 10px;
  text-align: center;
}
</style>
