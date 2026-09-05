<template>
  <!-- Contenedor raíz de la vista de gestión de tareas -->
  <div class="tasks-view-container">
    
    <!-- Barra superior de acciones para enriquecer la experiencia de usuario (UI/UX) -->
    <div class="view-header-bar">
      <!-- Sección izquierda: Título y descripción funcional -->
      <div class="header-titles">
        <!-- Título principal de la pantalla -->
        <h1 class="view-main-title">Gestión de Plantillas de Tareas</h1>
        <!-- Subtítulo con orientación para el usuario -->
        <p class="view-subtitle">
          Configure planes preventivos, frecuencias y asigne activos. Doble clic en una fila para editar en el formulario guiado.
        </p>
      </div>

      <!-- Sección derecha: Botón principal de acción -->
      <div class="header-actions">
        <!-- Botón destacado con estilo primario para registrar una nueva tarea -->
        <button type="button" class="btn-create-task" @click="openCreateModal">
          <!-- Icono visual representativo de adición -->
          <span class="btn-icon">+</span>
          <!-- Texto explícito de la acción -->
          <span class="btn-text">Nueva Plantilla de Tarea</span>
        </button>
      </div>
    </div>

    <!-- Componente de grilla interactiva para visualización masiva, ordenamiento y filtrado -->
    <ExcelGrid
      title="Catálogo de Plantillas Preventivas Registradas"
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
      @rowDblClick="handleRowDblClick"
    />

    <!-- Componente Modal para Creación y Edición guiada con código explícito -->
    <TaskFormModal
      :isOpen="isModalOpen"
      :taskData="selectedTaskToEdit"
      :catalogs="taskCatalogList"
      :plantsList="plantsList"
      :areasList="areasList"
      :systemsList="systemsList"
      :equipmentsList="equipmentsList"
      @close="closeModal"
      @saved="handleModalSaved"
      @catalogCreated="handleCatalogCreated"
    />
    
    <!-- Capa de bloqueo translúcida que informa al usuario cuando se están cargando datos -->
    <div v-if="loading" class="loading-overlay">
      <!-- Mensaje explícito de estado de carga -->
      <div class="loading-spinner-box">Cargando plantillas de tareas desde la base de datos...</div>
    </div>

    <!-- Banner informativo de error si ocurre un fallo en peticiones HTTP -->
    <div v-if="error" class="error-banner">
      <!-- Muestra el mensaje de error capturado -->
      {{ error }}
    </div>

  </div>
</template>

<script setup>
// Importamos funciones reactivas esenciales del core de Vue 3
import { ref, onMounted, computed } from 'vue';
// Importamos el componente de grilla estilo Excel
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos el nuevo componente modal de formulario guiado
import TaskFormModal from '../../components/TaskFormModal.vue';
// Importamos la instancia configurada de Axios para realizar llamadas al backend
import { api } from '../../api';
// Importamos el composable para manejo de estado asíncrono y mensajes de error
import { useApi } from '../../composables/useApi';
// Importamos el composable con los catálogos y funciones de la jerarquía de activos
import { useEquipmentHierarchies } from '../../composables/useEquipmentHierarchies';
// Importamos la función utilitaria para mapear filas editadas al formato de la API
import { buildPayloadFromRow } from '../../utils/gridHelpers';

// 1. Títulos de columnas visibles en la cabecera de la grilla
const headers = [
  'ID', 'Nombre', 'Duración (hrs)', 'Trabajadores', 'Frecuencia', 
  'Fecha de Inicio', 'Descripción', 'Planta', 'Área', 'Sistema', 'Equipo Asignado', 'Procedimiento', 'Turno'
];

// 2. Claves de correspondencia con los campos de la base de datos y modelo Task de Django
const colKeys = [
  'id', 'task_catalog', 'duration', 'workers', 'frequency', 
  'start_date', 'description', 'equipment__area__plant__name', 'equipment__area__name', 'equipment__system__name', 'equipment', 'procedure', 'turn'
];

// Matriz bidimensional reactiva con las celdas mapeadas para ExcelGrid
const gridData = ref([]);
// Arreglo con la totalidad de registros para alimentar los filtros de columna
const filterData = ref([]);
// Listado de tareas normalizadas del catálogo maestro
const taskCatalogList = ref([]);
// Almacena los objetos planos de tareas de la página actual para permitir edición al hacer doble clic
const rawTasksList = ref([]);

// Estado reactivo que controla la apertura del modal
const isModalOpen = ref(false);
// Almacena la tarea seleccionada para edición en el modal (null si es creación)
const selectedTaskToEdit = ref(null);

// Extraemos utilidades del composable de llamadas HTTP seguras
const { loading, error, execute } = useApi();

// Extraemos catálogos completos de la jerarquía desde el composable
const {
  equipmentsList,
  plantsList,
  areasList,
  systemsList,
  loadDependencies,
  getEquipmentHierarchyRow,
  buildFilterParams
} = useEquipmentHierarchies();

// Variables de estado para la paginación de la tabla
const currentPage = ref(1);
// Total de páginas calculadas
const totalPages = ref(1);
// Total de registros en la base de datos
const totalItems = ref(0);
// Cantidad de elementos por página por defecto
const pageSize = ref(25);
// Filtros actualmente activos seleccionados en la grilla
const currentFilters = ref({});
// Ordenamiento actual (columna y dirección asc/desc)
const currentSort = ref({ colIndex: null, direction: null });

// Función para descargar el catálogo maestro de nombres de tareas
const loadTaskCatalogs = async () => {
  try {
    // Solicitamos todos los catálogos con tamaño de página alto
    const res = await api.get('taskcatalogs/', { params: { page_size: 10000 } });
    // Guardamos la lista en la variable reactiva
    taskCatalogList.value = res.data.results || res.data || [];
  } catch (e) {
    // Registramos en consola si ocurre un error
    console.error('Error al cargar el catálogo de tareas:', e);
  }
};

// Configuración especial de columnas dentro de ExcelGrid (selects y columnas de solo lectura)
const columnsConfig = computed(() => {
  return {
    // Columna 1: Catálogo de Tareas (Dropdown)
    1: {
      type: 'select',
      options: taskCatalogList.value.map(cat => ({
        value: cat.id,
        label: cat.description || cat.name || 'Sin nombre'
      })).sort((a, b) => a.label.localeCompare(b.label))
    },
    // Columnas 7, 8 y 9: Planta, Área y Sistema (Solo lectura)
    7: { readOnly: true },
    8: { readOnly: true },
    9: { readOnly: true },
    // Columna 10: Equipo Asignado (Dropdown enriquecido con Nombre y Descripción)
    10: {
      type: 'select',
      options: equipmentsList.value.map(eq => {
        const equipoName = eq.name || 'Equipo sin nombre';
        const equipoDesc = eq.description ? ` - ${eq.description}` : '';
        const fullLabel = eq.tag ? `[${eq.tag}] ${equipoName}${equipoDesc}` : `${equipoName}${equipoDesc}`;
        return {
          value: eq.id,
          label: fullLabel
        };
      }).sort((a, b) => a.label.localeCompare(b.label))
    }
  };
});

// Función auxiliar para extraer datos considerando paginación DRF
const extractData = (res) => res.data.results || res.data || [];

// Carga la información requerida por los filtros de cabecera de la grilla
const loadFilterData = async () => {
  try {
    // Consulta masiva para extraer opciones de filtro
    const res = await api.get('tasks/', { params: { page_size: 10000 } });
    // Extraemos resultados
    const results = extractData(res);

    // Mapeamos a una matriz 2D con los datos necesarios para filtrar
    filterData.value = results.map(t => {
      // Obtenemos el ID del equipo de forma segura
      const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
      // Obtenemos los nombres de jerarquía
      const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);

      // Retornamos el array de valores en el mismo orden que colKeys
      return [
        t.id, 
        t.task_catalog || '', 
        t.duration || '', 
        t.workers || '', 
        t.frequency || '', 
        t.start_date || '', 
        t.description || '', 
        plantName,
        areaName,
        systemName,
        eqId,
        t.procedure || '', 
        t.turn || ''
      ];
    });
  } catch (e) {
    // Manejo de excepciones en consola
    console.error('Error al cargar datos para filtros:', e);
  }
};

// Carga las tareas paginadas de la base de datos aplicando filtros y orden
const loadData = async (page = 1) => {
  // Envolvemos la llamada en la función execute para gestionar loading y error automáticamente
  await execute(async () => {
    // Parámetros base de paginación
    let params = { page, page_size: pageSize.value };

    // Índices de columnas que componen la jerarquía operacional
    const hierarchyIndexes = { plant: '7', area: '8', system: '9', equipment: '10' };
    // Traducimos filtros activos a parámetros compatibles con Django
    params = buildFilterParams(params, currentFilters.value, colKeys, hierarchyIndexes);

    // Si el usuario aplicó ordenamiento sobre una columna directa
    if (currentSort.value.colIndex !== null) {
      const fieldName = colKeys[currentSort.value.colIndex];
      // Ignoramos campos relacionales virtuales con '__'
      if (fieldName && !fieldName.includes('__')) {
        params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
      }
    }

    // Petición GET al endpoint de tareas
    const resTasks = await api.get('tasks/', { params });
    const responseData = resTasks.data;
    let dataArray = [];

    // Verificamos si la respuesta viene paginada o como arreglo simple
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

    // Almacenamos los objetos planos para usarlos al editar
    rawTasksList.value = dataArray;

    // Convertimos los objetos en la matriz bidimensional que requiere ExcelGrid
    gridData.value = dataArray.map(t => {
      const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
      const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);

      return [
        t.id, 
        t.task_catalog || '', 
        t.duration || '', 
        t.workers || '', 
        t.frequency || '', 
        t.start_date || '', 
        t.description || '', 
        plantName,
        areaName,
        systemName,
        eqId,
        t.procedure || '', 
        t.turn || ''
      ];
    });
  }, 'Error al cargar la lista de tareas desde la base de datos.');
};

// Eventos delegados por ExcelGrid: cambio de página
const handlePageChange = (p) => loadData(p);
// Cambio de tamaño de página
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
// Cambio de filtros de columna
const handleFilterChange = (f) => { currentFilters.value = f; loadData(1); };
// Cambio de ordenamiento
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// Abre el modal en modo creación de nueva tarea
const openCreateModal = () => {
  // Limpiamos cualquier selección previa
  selectedTaskToEdit.value = null;
  // Mostramos el modal
  isModalOpen.value = true;
};

// Cierra el modal y limpia la selección
const closeModal = () => {
  isModalOpen.value = false;
  selectedTaskToEdit.value = null;
};

// Maneja la acción de doble clic sobre una fila para abrir el modal en modo edición
const handleRowDblClick = ({ row }) => {
  // El ID de la tarea se encuentra en la primera columna (índice 0)
  const taskId = row[0];
  if (!taskId) return;

  // Buscamos el objeto original en el listado de tareas cargadas
  const taskObj = rawTasksList.value.find(t => t.id === taskId);
  if (taskObj) {
    // Asignamos la tarea a editar y abrimos el modal
    selectedTaskToEdit.value = { ...taskObj };
    isModalOpen.value = true;
  }
};

// Maneja el evento de tarea guardada exitosamente desde el modal
const handleModalSaved = async () => {
  // Cerramos el modal
  closeModal();
  // Recargamos los datos para reflejar los cambios
  await loadData(currentPage.value);
  await loadFilterData();
};

// Añade dinámicamente un nuevo catálogo creado al vuelo a la lista local
const handleCatalogCreated = (newCatalog) => {
  taskCatalogList.value.push(newCatalog);
};

// Guardado por lotes desde la edición directa en la grilla ExcelGrid
const handleSave = async (updatedGrid) => {
  try {
    await execute(async () => {
      // Creamos una promesa por cada fila editada
      const promises = updatedGrid.map(row => {
        const payload = buildPayloadFromRow(row, colKeys);
        const id = payload.id;
        const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));

        if (isExisting) {
          return api.put(`tasks/${id}/`, payload);
        } else {
          delete payload.id;
          return api.post('tasks/', payload);
        }
      });

      await Promise.all(promises);
      alert('Cambios en la grilla guardados correctamente.');
      
      // Recarga de datos
      await loadData(currentPage.value);
      await loadFilterData();
    });
  } catch (e) {
    alert('Error al guardar. Verifique que los campos numéricos o fechas (YYYY-MM-DD) sean válidos.');
  }
};

// Eliminación de tareas seleccionadas
const handleDelete = async (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  try {
    await execute(async () => {
      const promises = idsToDelete.map(id => api.delete(`tasks/${id}/`));
      await Promise.all(promises);
      alert(`${idsToDelete.length} tarea(s) eliminada(s).`);
      
      await loadData(currentPage.value);
      await loadFilterData();
    });
  } catch (e) {
    alert('No se pudo eliminar la tarea. Podría estar asignada a un registro histórico del calendario.');
  }
};

// Hook de montaje inicial del componente
onMounted(async () => {
  // 1. Cargamos catálogos de dependencias jerárquicas
  await loadDependencies();
  // 2. Cargamos catálogo maestro de tareas
  await loadTaskCatalogs();
  // 3. Cargamos los datos de la primera página
  await loadData();
  // 4. Cargamos datos para los filtros
  await loadFilterData();
});
</script>

<style scoped>
/* Contenedor general de la vista */
.tasks-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  gap: 0.75rem;
}

/* Barra superior que contiene títulos y botón de acción */
.view-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1.25rem;
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Agrupación de títulos */
.header-titles {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

/* Título principal */
.view-main-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

/* Subtítulo informativo */
.view-subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

/* Botón principal para abrir el modal de creación */
.btn-create-task {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background-color: #2563eb;
  color: #ffffff;
  border: none;
  padding: 0.65rem 1.2rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
  transition: background-color 0.15s, transform 0.05s;
}

/* Efecto hover del botón */
.btn-create-task:hover {
  background-color: #1d4ed8;
}

/* Efecto click del botón */
.btn-create-task:active {
  transform: translateY(1px);
}

/* Icono dentro del botón */
.btn-icon {
  font-size: 1.15rem;
  line-height: 1;
  font-weight: bold;
}

/* Capa de carga sobrepuesta */
.loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}

/* Caja de texto del spinner de carga */
.loading-spinner-box {
  background-color: #1e293b;
  color: #ffffff;
  padding: 0.85rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Mensaje de error */
.error-banner {
  background-color: #fef2f2;
  border: 1px solid #f87171;
  color: #b91c1c;
  padding: 0.75rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>