<template>
  <div class="equipments-view">
    <!--
      Componente ExcelGrid reutilizable
      - columnsConfig: Configuración para dropdowns de Sistema y Área
      - @delete: Evento para eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Equipos"
      :headers="headers"
      :data="equipmentsData"
      :columnsConfig="columnsConfig"
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
import { ref, onMounted, computed } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';

// Configuración de columnas
// Índices: 0:ID, 1:Tag, 2:Nombre, 3:Descripción, 4:Sistema, 5:Área
const headers = ['ID', 'Tag', 'Nombre', 'Descripción', 'Sistema', 'Área'];

// Estado reactivo
const equipmentsData = ref([]);
const systemsList = ref([]); // Lista de sistemas para dropdown
const areasList = ref([]);   // Lista de áreas para dropdown
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
        const response = await api.get('equipments/', { params: { page_size: 10000 } });
        const results = response.data.results || response.data;
        filterData.value = results.map(e => [
            e.id,
            e.tag || '',
            e.name || '',
            e.description || '',
            (e.system && typeof e.system === 'object') ? e.system.id : (e.system || ''),
            (e.area && typeof e.area === 'object') ? e.area.id : (e.area || '')
        ]);
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

// Configuración dinámica de columnas para ExcelGrid (Dropdowns)
const columnsConfig = computed(() => {
    return {
        4: { // Columna 'Sistema'
            type: 'select',
            options: systemsList.value.map(s => ({ value: s.id, label: s.name }))
        },
        5: { // Columna 'Área'
            type: 'select',
            options: areasList.value.map(a => ({ value: a.id, label: a.name }))
        }
    };
});

/**
 * Carga los datos de equipos, sistemas y áreas desde la API
 */
const loadData = async (page = 1) => {
  loading.value = true;
  error.value = null;

  try {
    // Configurar parámetros de la petición (Paginación + Filtros + Sort)
    const params = { 
        page, 
        page_size: pageSize.value 
    };

    // Mapeo seguro de índices de columna a campos del backend Django
    const colToFieldMap = {
        0: 'id',
        1: 'tag',
        2: 'name',
        3: 'description',
        4: 'system',
        5: 'area'
    };

    // Aplicar filtros dinámicos (búsqueda exacta/in usando DjangoFilters/DRF)
    for (const [colIndex, values] of Object.entries(currentFilters.value)) {
        const fieldName = colToFieldMap[colIndex];
        if (fieldName && values.length > 0) {
            // Ejemplo: si seleccionaron Área = 'Área 1', mandamos ?area__in=Area1,Area2
            // Ojo: Esto requiere que el backend tenga configurado DjangoFilterBackend para estos campos
            params[`${fieldName}__in`] = values.join(','); 
        }
    }

    // Aplicar ordenamiento dinámico
    if (currentSort.value.colIndex !== null) {
        const fieldName = colToFieldMap[currentSort.value.colIndex];
        if (fieldName) {
            // DRF usa ?ordering=campo o ?ordering=-campo
            params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
        }
    }

    // Carga paralela de recursos: Equipos (Paginados), Sistemas y Áreas (Listas enteras para Dropdowns)
    const [eqRes, sysRes, areaRes] = await Promise.all([
        api.get('equipments/', { params }),
        // Agregamos page_size: 10000 a ambas relaciones para asegurar que el dropdown muestre todos los items disponibles
        api.get('systems/', { params: { page_size: 10000 } }),
        api.get('areas/', { params: { page_size: 10000 } })
    ]);
    
    // Procesar listas auxiliares
    if (sysRes.data) systemsList.value = Array.isArray(sysRes.data) ? sysRes.data : (sysRes.data.results ? sysRes.data.results : []);
    if (areaRes.data) areasList.value = Array.isArray(areaRes.data) ? areaRes.data : (areaRes.data.results ? areaRes.data.results : []);

    // Procesar Equipos
    const responseData = eqRes.data;
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

    equipmentsData.value = dataArray.map(e => [
        e.id,
        e.tag || '',
        e.name || '',
        e.description || '',
        // Manejo de FKs: extraer ID si viene objeto completo
        (e.system && typeof e.system === 'object') ? e.system.id : (e.system || ''),
        (e.area && typeof e.area === 'object') ? e.area.id : (e.area || '')
    ]);

  } catch (err) {
    console.error('Error cargando datos:', err);
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
    loadData(1); // Volver a la primera página al cambiar el tamaño
};

const handleFilterChange = (filters) => {
    currentFilters.value = filters;
    loadData(1); // Volver a la primera página al aplicar filtros
};

const handleSortChange = (sortConfig) => {
    currentSort.value = sortConfig;
    loadData(1); // Volver a la primera página al ordenar
};

/**
 * Maneja el guardado de cambios
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3],
            system: row[4], // ID del sistema seleccionado
            area: row[5]    // ID del área seleccionada
        };

        // Limpiar FKs vacías para evitar errores de validación
        if (!payload.system) delete payload.system;
        if (!payload.area) delete payload.area;

        // Actualizar (PUT) o Crear (POST)
        if (id && String(id).trim() !== '') {
            return api.put(`equipments/${id}/`, payload);
        } else {
            if (payload.tag || payload.name) {
                return api.post('equipments/', payload);
            }
        }
    });

    await Promise.all(promises);
    alert('Cambios guardados correctamente.');
    await loadData();
    await loadFilterData();

  } catch (err) {
    console.error('Error guardando equipos:', err);
    alert('Error al guardar. Verifique las relaciones (Sistema/Área).');
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
        const deletePromises = idsToDelete.map(id => api.delete(`equipments/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);
        await loadFilterData();

    } catch (err) {
        console.error('Error eliminando equipos:', err);
        alert('Error al eliminar las filas.');
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
.equipments-view {
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
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  margin: 10px;
  border-radius: 4px;
}
</style>
