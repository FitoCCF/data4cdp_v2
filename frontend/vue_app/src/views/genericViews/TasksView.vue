<template>
  <!-- Contenedor principal de la vista de Tareas -->
  <div class="tasks-view">
    <!--
      Componente ExcelGrid reutilizable importado para mostrar datos.
      - title: Título que aparece en la parte superior de la grilla.
      - headers: Nombres de las columnas de la tabla.
      - data: Matriz de datos que se mostrará en las filas.
      - columnsConfig: Configuración para dropdowns de relaciones (ej. Equipo).
      - currentPage: Página actual para la paginación.
      - totalPages: Cantidad total de páginas disponibles.
      - totalItems: Cantidad total de registros en la base de datos.
      - pageSize: Cantidad de registros que se muestran por página.
      - serverSideFiltering: Indica que el filtrado se hace en el backend.
      - filterData: Datos que se usan para llenar las opciones de los filtros en las columnas.
      - @save: Evento que se dispara al guardar cambios (crear o actualizar filas).
      - @delete: Evento que se dispara al eliminar filas seleccionadas.
      - @pageChange: Evento que se dispara al cambiar de página.
      - @pageSizeChange: Evento que se dispara al cambiar la cantidad de elementos por página.
      - @filterChange: Evento que se dispara al aplicar un filtro en alguna columna.
      - @sortChange: Evento que se dispara al hacer clic en el encabezado de una columna para ordenar.
    -->
    <ExcelGrid
      title="Mantenimiento de Tareas"
      :headers="headers"
      :data="tasksData"
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
    
    <!-- Indicador visual que se muestra superpuesto cuando la variable 'loading' es verdadera -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error que se muestra si la variable 'error' contiene algún texto -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importación de funciones reactivas y del ciclo de vida desde Vue
import { ref, onMounted, computed } from 'vue';
// Importación del componente de grilla reutilizable
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importación de la instancia de Axios configurada para llamar al backend
import { api } from '../../api';

// Configuración estática de los encabezados (columnas) que mostrará la tabla
const headers = ['ID', 'Nombre', 'Duración (min)', 'Trabajadores', 'Frecuencia', 'Fecha Inicio', 'Descripción', 'Procedimiento', 'Turno', 'Equipo'];

// ===== Definición del Estado Reactivo =====
const tasksData = ref([]);
const equipmentsList = ref([]); // Lista de equipos para el cuadro desplegable (dropdown) en la tabla
const loading = ref(false);
const error = ref(null);

// ===== Estado de Paginación y Filtrado =====
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]);

/**
 * Función asíncrona para cargar los datos que poblarán los filtros.
 */
const loadFilterData = async () => {
    try {
        const response = await api.get('tasks/', { params: { page_size: 10000 } });
        const results = response.data.results || response.data;
        filterData.value = results.map(t => [
            t.id,
            t.name || '',
            t.duration || '',
            t.workers || '',
            t.frequency || '',
            t.start_date || '',
            t.description || '',
            t.procedure || '',
            t.turn || '',
            // Manejo de la relación: si el equipo viene como objeto completo, extraemos el ID
            (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '')
        ]);
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

/**
 * Configuración dinámica de columnas especiales para el ExcelGrid.
 * Define qué columnas usarán menús desplegables basados en datos de otras tablas.
 */
const columnsConfig = computed(() => {
    return {
        9: { // Índice 9 pertenece a la columna 'Equipo'
            type: 'select',
            options: equipmentsList.value.map(e => ({ value: e.id, label: e.name }))
        }
    };
});

/**
 * Función asíncrona principal que carga los datos de tareas y equipos simultáneamente.
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
        1: 'name',
        2: 'duration',
        3: 'workers',
        4: 'frequency',
        5: 'start_date',
        6: 'description',
        7: 'procedure',
        8: 'turn',
        9: 'equipment'
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

    // Cargar de manera simultánea ambas listas desde la API
    // Para 'equipments' solicitamos un listado completo (page_size: 10000) para poblar el select en la celda de edición
    const [tasksRes, eqRes] = await Promise.all([
        api.get('tasks/', { params }),
        api.get('equipments/', { params: { page_size: 10000 } })
    ]);
    
    // Asignar el diccionario de equipos a la variable reactiva
    if (eqRes.data) {
        equipmentsList.value = Array.isArray(eqRes.data) ? eqRes.data : 
                               (eqRes.data.results ? eqRes.data.results : []);
    }

    // Extraer tareas
    const responseData = tasksRes.data;
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

    // Formatear las filas para que el componente ExcelGrid las dibuje
    tasksData.value = dataArray.map(t => [
        t.id,
        t.name || '',
        t.duration || '',
        t.workers || '',
        t.frequency || '',
        t.start_date || '',
        t.description || '',
        t.procedure || '',
        t.turn || '',
        // Extraemos su ID. ExcelGrid convertirá automáticamente este ID en su "nombre" visualmente
        (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '')
    ]);

  } catch (err) {
    console.error('Error cargando tareas:', err);
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

const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        
        const payload = {
            name: row[1],
            duration: row[2] ? row[2] : null,
            workers: row[3] ? row[3] : null,
            frequency: row[4],
            start_date: row[5] ? row[5] : null,
            description: row[6],
            procedure: row[7],
            turn: row[8],
            equipment: row[9] // ID del equipo
        };

        // Prevención de envíos de strings vacíos para un campo foráneo numérico
        if (!payload.equipment) delete payload.equipment;

        if (id && String(id).trim() !== '') {
            return api.put(`tasks/${id}/`, payload);
        } else {
            if (payload.name) {
                return api.post('tasks/', payload);
            }
        }
    });

    await Promise.all(promises);
    alert('Cambios guardados correctamente en la base de datos.');
    
    await loadData();
    await loadFilterData();

  } catch (err) {
    console.error('Error guardando tareas:', err);
    alert('Error al guardar los cambios en la base de datos.');
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    loading.value = true;
    try {
        const deletePromises = idsToDelete.map(id => api.delete(`tasks/${id}/`));
        await Promise.all(deletePromises);
        alert(`${idsToDelete.length} tarea(s) eliminada(s) correctamente.`);
        await loadFilterData();
    } catch (err) {
        console.error('Error eliminando tareas:', err);
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
.tasks-view {
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