<template>
  <div class="samples-view">
    <!--
      Componente ExcelGrid reutilizable
      - title: Título de la tabla
      - headers: Nombres de las columnas
      - data: Matriz de datos a mostrar
      - columnsConfig: Configuración especial para columnas (ej. dropdowns)
      - @save: Evento emitido al guardar
      - @delete: Evento emitido al eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Muestras"
      :headers="headers"
      :data="samplesData"
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

    <!-- Indicador de carga que se superpone a la vista -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error que aparece si falla la carga o guardado -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importaciones de Vue
import { ref, onMounted, computed } from 'vue';
// Importación del componente reutilizable
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importación del cliente API
import { api } from '../../api';
// Importación del composable genérico de peticiones HTTP
import { useApi } from './useApi';

// --- Configuración de la Tabla ---

// Define los encabezados de las columnas que se mostrarán en la tabla
// Índices: 0:ID, 1:Tag, 2:Nombre, 3:Equipo
const headers = ['ID', 'Tag', 'Nombre', 'Equipo'];

// --- Estado Reactivo ---

// Almacena los datos de las muestras en formato de matriz para ExcelGrid
const samplesData = ref([]);
// Almacena la lista completa de objetos de equipo para el dropdown
const equipmentsList = ref([]);

// Extraer estados de carga y función execute del composable
const { loading, error, execute } = useApi();

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
        const response = await api.get('samples/', { params: { page_size: 10000 } });
        const results = response.data.results || response.data;
        filterData.value = results.map(s => [
            s.id,
            s.tag || '',
            s.name || '',
            (s.equipment && typeof s.equipment === 'object') ? s.equipment.id : (s.equipment || '')
        ]);
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

// --- Propiedades Computadas ---

/**
 * Configuración dinámica para las columnas de ExcelGrid.
 * Esta propiedad computada se recalcula si `equipmentsList` cambia.
 */
const columnsConfig = computed(() => {
    return {
        // La clave '3' corresponde al índice de la columna 'Equipo' en el array `headers`
        3: {
            // Define el tipo de celda como un menú desplegable
            type: 'select',
            // Genera las opciones para el dropdown
            options: equipmentsList.value.map(equipment => {
                // Para cada equipo, crea una etiqueta concatenando nombre y descripción
                const label = `${equipment.name || ''} - ${equipment.description || ''}`.trim();

                // Retorna un objeto con el formato { value: ID, label: TEXTO_CONCATENADO }
                return {
                    value: equipment.id,
                    // Si el label queda como '-', usar solo el nombre o un identificador
                    label: label === '-' ? (equipment.name || `Equipo ID: ${equipment.id}`) : label
                };
            })
        }
    };
});

// --- Métodos de API ---

/**
 * Carga los datos de muestras y equipos desde el backend.
 */
const loadData = async (page = 1) => {
  await execute(async () => {
    const params = { 
        page, 
        page_size: pageSize.value 
    };

    const colToFieldMap = {
        0: 'id',
        1: 'tag',
        2: 'name',
        3: 'equipment'
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

    // Realiza peticiones en paralelo: Muestras (Paginadas) y Equipos (Todos los registros para el dropdown)
    const [samplesRes, equipmentsRes] = await Promise.all([
        api.get('samples/', { params }),
        // Agregamos page_size: 10000 para ignorar la paginación estándar y proveer todas las opciones al selector
        api.get('equipments/', { params: { page_size: 10000 } })
    ]);

    // Procesa y almacena la lista de equipos
    if (equipmentsRes.data) {
        equipmentsList.value = Array.isArray(equipmentsRes.data) ? equipmentsRes.data : 
                               (equipmentsRes.data.results ? equipmentsRes.data.results : []);
    }

    // Procesa y transforma los datos de las muestras
    const responseData = samplesRes.data;
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

    samplesData.value = dataArray.map(sample => [
        sample.id,
        sample.tag || '',
        sample.name || '',
        // Extrae el ID de la clave foránea 'equipment'
        (sample.equipment && typeof sample.equipment === 'object') ? sample.equipment.id : (sample.equipment || '')
    ]);
  }, 'Error al cargar los datos de la base de datos.');
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
 * Maneja el evento 'save' emitido por ExcelGrid para guardar los cambios.
 * @param {Array} updatedGrid - La matriz de datos actualizada desde el componente hijo.
 */
const handleSave = async (updatedGrid) => {
  try {
    await execute(async () => {
      // Mapea cada fila de la matriz a una promesa de petición (PUT o POST)
      const promises = updatedGrid.map(async (row) => {
          const id = row[0];
          const payload = {
              tag: row[1],
              name: row[2],
              equipment: row[3]
          };

          if (!payload.equipment) delete payload.equipment;

          if (id && String(id).trim() !== '') {
              return api.put(`samples/${id}/`, payload);
          } else {
              if (payload.tag || payload.name) {
                  return api.post('samples/', payload);
              }
          }
      });

      await Promise.all(promises);
      alert('Cambios guardados correctamente.');

      await loadData();
      await loadFilterData();
    });
  } catch (err) {
    // Manejo de errores durante el guardado
    alert('Error al guardar. Verifique la relación con Equipo.');
  }
};

/**
 * Maneja la eliminación de filas
 * @param {Array} idsToDelete - Array de IDs a eliminar
 */
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    try {
        await execute(async () => {
            const deletePromises = idsToDelete.map(id => api.delete(`samples/${id}/`));
            await Promise.all(deletePromises);

            alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);
            await loadFilterData();
        });
    } catch (err) {
        alert('Error al eliminar las filas.');
        await loadData();
    }
};

// --- Ciclo de Vida ---

// Hook que se ejecuta cuando el componente se monta en el DOM
onMounted(() => {
  // Llama a la función para cargar los datos iniciales
  loadData();
  loadFilterData();
});
</script>

<style scoped>
/* Contenedor principal de la vista */
.samples-view {
  position: relative;
  height: 100%;
}

/* Overlay de carga para feedback visual */
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
