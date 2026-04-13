<template>
  <section class="tasks-view">
    <header class="view-header">
      <h1>Mantenimiento de Programación (TaskP)</h1>
      <div class="header-actions">
        <button
          type="button"
          class="btn btn-blue"
          @click="loadData(1)"
          :disabled="loading"
        >
          {{ loading ? 'Cargando...' : 'Recargar Datos' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <div class="grid-wrapper">
      <ExcelGrid
        v-if="!loading"
        title="Programación de Tareas"
        :headers="gridHeaders"
        :data="gridData"
        :columnsConfig="gridConfig"
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
      <p v-else class="loading-text">Cargando programación...</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { api } from '../../api';
import ExcelGrid from '../../components/ExcelGrid.vue';

// --- Estado ---
const loading = ref(false);
const error = ref('');
const rawTasksP = ref([]);

// Paginación y Filtrado
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]); 

// Listas Auxiliares para Selects
const tasksList = ref([]);
const usersPList = ref([]); // Grupos (UserP)
const estadosList = ref([]);

// --- Configuración de Grilla ---

const gridHeaders = [
  'ID', 'Tarea', 'Año', 'Semana', 'Día', 'Fecha',
  'Grupo/Usuario', 'Estado', 'Prioridad', 'Reprogramado',
  'Razón Reprog.', 'Fecha Reprog.'
];

// IMPORTANTE: 'group' debe coincidir con el campo en TaskP (models.py)
const colKeys = [
  'id', 'task', 'year', 'week', 'day', 'date',
  'group', 'estado', 'priority', 'rescheduled',
  'reschedule_reason', 'reschedule_date'
];

const gridConfig = computed(() => {
  const taskOptions = tasksList.value.map(t => ({ value: String(t.id), label: t.name || `Tarea ${t.id}` }));
  const groupOptions = usersPList.value.map(u => ({ value: String(u.id), label: u.name || `Grupo ${u.id}` }));
  const estadoOptions = estadosList.value.map(e => ({ value: String(e.id), label: e.estado_nombre || `Estado ${e.id}` }));
  const boolOptions = [{ value: 'true', label: 'Sí' }, { value: 'false', label: 'No' }];

  return {
    0: { readOnly: true },
    1: { type: 'select', options: taskOptions },
    6: { type: 'select', options: groupOptions }, // Índice 6 = 'group'
    7: { type: 'select', options: estadoOptions },
    9: { type: 'select', options: boolOptions }
  };
});

// TRANSFORMACIÓN DE DATOS: Convierte el JSON complejo de la API en el Array plano para ExcelGrid
const gridData = computed(() => {
  return rawTasksP.value.map(item => {
    return colKeys.map(key => {
      let val = item[key];
      
      // Si el campo es una Foreign Key (objeto), extraemos el ID
      if (val && typeof val === 'object' && val.id !== undefined) {
        val = val.id;
      }
      
      // Convertir booleanos a strings para los selectores del grid
      if (typeof val === 'boolean') {
        val = val ? 'true' : 'false';
      }
      
      // ExcelGrid necesita Strings para comparar en los filtros
      return val === null || val === undefined ? '' : String(val);
    });
  });
});

// --- Métodos de Carga ---

const extractData = (response) => {
    if (response.data && response.data.results) return response.data.results;
    if (Array.isArray(response.data)) return response.data;
    return [];
};

const loadSelectionLists = async () => {
    try {
        const params = { page_size: 1000 };
        const [tasksRes, usersPRes, estadosRes] = await Promise.all([
            api.get('tasks/', { params }),
            api.get('userp/', { params }),
            api.get('estados/', { params })
        ]);
        tasksList.value = extractData(tasksRes);
        usersPList.value = extractData(usersPRes);
        estadosList.value = extractData(estadosRes);
    } catch (err) {
        console.error("Error cargando listas:", err);
    }
};

const loadData = async (page = 1) => {
  loading.value = true;
  error.value = '';

  try {
    const params = {
        page: page,
        page_size: pageSize.value
    };

    // Filtros dinámicos (Server-side)
    Object.entries(currentFilters.value).forEach(([colIndex, values]) => {
        const fieldName = colKeys[colIndex];
        if (fieldName && values && Array.from(values).length > 0) {
            const vals = Array.from(values);
            const validVals = vals.filter(v => v !== '');
            if (validVals.length > 0) {
                params[`${fieldName}__in`] = validVals.join(',');
            }
            if (vals.includes('')) {
                params[`${fieldName}__isnull`] = 'True';
            }
        }
    });

    // Ordenamiento
    if (currentSort.value.colIndex !== null) {
        const fieldName = colKeys[currentSort.value.colIndex];
        if (fieldName) {
            params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
        }
    }

    const response = await api.get('taskp/', { params });

    if (response.data && response.data.results) {
        rawTasksP.value = response.data.results;
        totalItems.value = response.data.count;
        totalPages.value = Math.ceil(response.data.count / pageSize.value);
        currentPage.value = page;
    } else {
        // Fallback si el API no devuelve paginación DRF estándar
        const data = extractData(response);
        rawTasksP.value = data;
        totalItems.value = data.length;
        totalPages.value = 1;
        currentPage.value = 1;
    }
  } catch (err) {
    error.value = "Error al conectar con la API de Programación.";
  } finally {
    loading.value = false;
  }
};

// --- Manejo de Eventos ---

const handlePageChange = (newPage) => loadData(newPage);
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

const handleSave = async (gridRows) => {
  loading.value = true;
  try {
    const promises = gridRows.map(row => {
      const payload = {};
      colKeys.forEach((key, index) => {
        let val = row[index];
        if (val === '') val = null;
        if (val === 'true') val = true;
        if (val === 'false') val = false;
        payload[key] = val;
      });

      const id = payload.id;
      if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
        return api.put(`taskp/${id}/`, payload);
      } else {
        delete payload.id;
        return api.post('taskp/', payload);
      }
    });

    await Promise.all(promises);
    alert('Programación actualizada correctamente.');
    await loadData(currentPage.value);
  } catch (err) {
    error.value = "Error al guardar cambios. Verifique los datos.";
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (idsToDelete) => {
  if (!confirm(`¿Eliminar ${idsToDelete.length} registros permanentemente?`)) return;
  loading.value = true;
  try {
    await Promise.all(idsToDelete.map(id => api.delete(`taskp/${id}/`)));
    alert('Registros eliminados.');
    await loadData(currentPage.value);
  } catch (err) {
    error.value = "Error al intentar eliminar registros.";
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadSelectionLists();
  await loadData();
});
</script>

<style scoped>
.tasks-view { display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem; height: 85vh; }
.view-header { display: flex; justify-content: space-between; align-items: center; }
.grid-wrapper { flex-grow: 1; overflow: hidden; display: flex; flex-direction: column; border: 1px solid #ddd; }
.feedback.error { color: #b91c1c; background: #fee2e2; padding: 10px; border-radius: 4px; border: 1px solid #f87171; }
.btn { padding: 8px 16px; border-radius: 4px; border: none; cursor: pointer; font-weight: bold; }
.btn-blue { background-color: #3b82f6; color: white; }
</style>
