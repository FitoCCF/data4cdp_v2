<template>
  <div class="plants-view">
    <!-- Componente ExcelGrid reutilizable para mantenimiento avanzado -->
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
      @delete="confirmDeleteFromGrid"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
      @rowDblClick="handleRowDblClick"
    >
      <template #actions-end>
        <button 
          type="button" 
          class="btn btn-sm btn-outline-primary" 
          @click="openCreateModal"
          title="Crear planta de forma guiada con validaciones"
        >
          ➕ Nueva Planta
        </button>
      </template>
    </ExcelGrid>

    <!-- Modal asistido para creación y edición de Plantas -->
    <AssetSimpleModal
      v-if="isModalOpen"
      :isOpen="isModalOpen"
      :entityType="'plant'"
      :itemId="selectedPlantId"
      @close="isModalOpen = false"
      @saved="onItemSaved"
    />

    <!-- Modal de confirmación de borrado seguro con auditoría de impacto -->
    <SafeDeleteModal
      v-if="isDeleteModalOpen"
      :isOpen="isDeleteModalOpen"
      :endpoint="'plants'"
      :entityTitle="'Plantas'"
      :idsToDelete="pendingDeleteIds"
      @close="isDeleteModalOpen = false"
      @confirmed="executeConfirmedDelete"
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
import AssetSimpleModal from '../../components/AssetSimpleModal.vue';
import SafeDeleteModal from '../../components/SafeDeleteModal.vue';
import { api } from '../../api';
// Importamos la función de utilidades compartida para sanitizar valores individuales
import { sanitizeValue } from '../../utils/gridHelpers';

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

// Estado para modales asistidos y borrado seguro
const isModalOpen = ref(false);
const selectedPlantId = ref(null);
const isDeleteModalOpen = ref(false);
const pendingDeleteIds = ref([]);

const openCreateModal = () => {
  selectedPlantId.value = null;
  isModalOpen.value = true;
};

const handleRowDblClick = ({ row }) => {
  if (row && row[0]) {
    selectedPlantId.value = row[0];
    isModalOpen.value = true;
  }
};

const onItemSaved = async () => {
  isModalOpen.value = false;
  await loadData(currentPage.value);
  await loadFilterData();
};

const confirmDeleteFromGrid = (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  pendingDeleteIds.value = idsToDelete;
  isDeleteModalOpen.value = true;
};

const executeConfirmedDelete = async () => {
  isDeleteModalOpen.value = false;
  await handleDelete(pendingDeleteIds.value);
};

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
 * Maneja el guardado de cambios masivos en ExcelGrid (Creación y Edición)
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        
          const payload = {
            tag: sanitizeValue(row[1]),
            name: sanitizeValue(row[2]),
            description: sanitizeValue(row[3]),
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
    await loadData(currentPage.value);
    await loadFilterData();
  } catch (err) {
    console.error('Error guardando plantas:', err);
    alert('Error al guardar los cambios en la base de datos.');
  } finally {
    loading.value = false;
  }
};

/**
 * Maneja la eliminación de filas confirmadas
 * @param {Array} idsToDelete - Array de IDs a eliminar
 */
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    loading.value = true;
    try {
        const deletePromises = idsToDelete.map(id => api.delete(`plants/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);
        await loadFilterData();
        await loadData(currentPage.value);

    } catch (err) {
        console.error('Error eliminando plantas:', err);
        alert('Error al eliminar las filas.');
        await loadData(currentPage.value);
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

.btn-outline-primary {
  background-color: transparent;
  border: 1px solid #3b82f6;
  color: #3b82f6;
  font-weight: 600;
}

.btn-outline-primary:hover {
  background-color: #3b82f6;
  color: #ffffff;
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
