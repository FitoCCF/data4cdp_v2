<!--
  STasksViews.vue
  Vista de Mantenimiento de Tareas Programadas (TaskP).
  Replica la arquitectura de AssaysView: Paginación, filtrado y ordenamiento delegados a ExcelGrid.
-->
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
const filterData = ref([]); // Datos para poblar los filtros de columna

// Listas Auxiliares (Foreign Keys)
const tasksList = ref([]);
const usersPList = ref([]);
const estadosList = ref([]);

// --- Configuración de Grilla ---

// 1. Encabezados
const gridHeaders = [
  'ID', 'Tarea', 'Año', 'Semana', 'Día', 'Fecha',
  'Usuario', 'Estado', 'Prioridad', 'Reprogramado',
  'Razón Reprog.', 'Fecha Reprog.'
];

// 2. Claves de API
// NOTA: Estas claves deben coincidir con los campos retornados por el API para visualización,
// y se usan para construir los parámetros de filtro (e.g. task__in=...).
const colKeys = [
  'id', 'task', 'year', 'week', 'day', 'date',
  'usuario', 'estado', 'priority', 'rescheduled',
  'reschedule_reason', 'reschedule_date'
];

// 3. Configuración de Columnas
const gridConfig = computed(() => {
  const taskOptions = tasksList.value.map(t => ({ value: t.id, label: t.name || `Tarea ${t.id}` }));

  const userOptions = usersPList.value.map(u => {
    let label = `UserP ${u.id}`;
    if (u.user && u.user.nombre) {
        label = `${u.user.nombre} ${u.user.apellido || ''} (${u.date})`;
    } else if (u.day) {
        label = `${u.day} - ${u.turn}`;
    }
    return { value: u.id, label };
  });

  const estadoOptions = estadosList.value.map(e => ({ value: e.id, label: e.estado_nombre || `Estado ${e.id}` }));
  const boolOptions = [{ value: 'true', label: 'Sí' }, { value: 'false', label: 'No' }];

  return {
    0: { readOnly: true },
    1: { type: 'select', options: taskOptions },
    6: { type: 'select', options: userOptions },
    7: { type: 'select', options: estadoOptions },
    9: { type: 'select', options: boolOptions }
  };
});

// 4. Datos Transformados
const gridData = computed(() => {
  return rawTasksP.value.map(item => {
    return colKeys.map(key => {
      let val = item[key];
      if (val && typeof val === 'object') val = val.id;
      if (typeof val === 'boolean') val = val ? 'true' : 'false';
      return val === null || val === undefined ? '' : val;
    });
  });
});

// --- Métodos ---

const extractData = (response) => {
    if (response.data && Array.isArray(response.data)) return response.data;
    if (response.data && response.data.results) return response.data.results;
    return [];
};

// Carga listas auxiliares (una sola vez)
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
        error.value = "Error cargando listas desplegables.";
    }
};

// Carga datos para los filtros de columna (todos los datos, sin paginar o paginación muy grande)
// Esto permite que el usuario vea todas las opciones posibles en el filtro del ExcelGrid
const loadFilterData = async () => {
    try {
        const params = { page_size: 5000 }; // Límite razonable para filtros
        const response = await api.get('taskp/', { params });
        const results = extractData(response);

        // Transformar datos para que coincidan con la estructura de la grilla
        filterData.value = results.map(item => {
            return colKeys.map(key => {
                let val = item[key];
                if (val && typeof val === 'object') val = val.id;
                if (typeof val === 'boolean') val = val ? 'true' : 'false';
                // Asegurar conversión a String para consistencia con ExcelGrid
                return val === null || val === undefined ? '' : String(val);
            });
        });
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

// Carga datos principales
const loadData = async (page = 1) => {
  loading.value = true;
  error.value = '';

  try {
    const params = {
        page: page,
        page_size: pageSize.value
    };

    // Aplicar filtros dinámicos
    for (const [colIndex, values] of Object.entries(currentFilters.value)) {
        const fieldName = colKeys[colIndex];

        if (fieldName && values) {
            // Caso 1: El usuario deseleccionó TODO en el filtro -> No mostrar resultados.
            // Si values está vacío, significa que el filtro está activo (la clave existe en currentFilters)
            // pero no hay valores permitidos.
            if (values.length === 0) {
                rawTasksP.value = [];
                totalItems.value = 0;
                totalPages.value = 1;
                loading.value = false;
                return;
            }

            // Caso 2: Hay valores seleccionados.
            // Enviamos los valores separados por coma.
            // Usamos values.join(',') directamente para incluir todos los valores seleccionados.
            // Nota: Si values incluye strings vacíos (''), estos se enviarán.
            // El backend y django-filter deben manejar 'campo__in=valor,' o 'campo__in=,valor' adecuadamente.
            params[`${fieldName}__in`] = values.join(',');
        }
    }

    // Aplicar ordenamiento
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
        rawTasksP.value = extractData(response);
        totalItems.value = rawTasksP.value.length;
        totalPages.value = 1;
        currentPage.value = 1;
    }

  } catch (err) {
    console.error("Error cargando datos:", err);
    error.value = "Error de conexión al cargar datos.";
  } finally {
    loading.value = false;
  }
};

// Manejadores de Eventos de ExcelGrid
const handlePageChange = (newPage) => loadData(newPage);
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

// Guardar Cambios
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
    await loadData(currentPage.value);
    await loadFilterData(); // Recargar filtros por si hubo nuevos valores
    alert('Guardado exitosamente.');
  } catch (err) {
    console.error("Error guardando:", err);
    error.value = "Error al guardar cambios.";
  } finally {
    loading.value = false;
  }
};

// Eliminar
const handleDelete = async (idsToDelete) => {
  if (!confirm(`¿Eliminar ${idsToDelete.length} registros?`)) return;
  loading.value = true;
  try {
    await Promise.all(idsToDelete.map(id => api.delete(`taskp/${id}/`)));
    await loadData(currentPage.value);
    await loadFilterData();
    alert('Eliminado exitosamente.');
  } catch (err) {
    console.error("Error eliminando:", err);
    error.value = "Error al eliminar.";
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadSelectionLists();
  await loadData();
  loadFilterData(); // Carga asíncrona de datos para filtros
});
</script>

<style scoped>
.tasks-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  height: 100%;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.grid-wrapper {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.loading-text {
  text-align: center;
  font-size: 1.2rem;
  color: #666;
  margin-top: 2rem;
}

.feedback.error {
  color: #b91c1c;
  background: #fee2e2;
  padding: 10px;
  border-radius: 4px;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-blue { background-color: #3b82f6; color: white; }
.btn-blue:hover { background-color: #2563eb; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
