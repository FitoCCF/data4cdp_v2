<template>
  <!-- Contenedor principal de la vista de mantenimiento para la Programación de Tareas Preventivas (Modelo TaskP) -->
  <div class="scheduled-tasks-view">
    <!-- Encabezado de la vista con título e información de acciones rápidas -->
    <header class="view-header">
      <div class="title-group">
        <h1 class="view-title">Mantenimiento de Programación de Tareas (TaskP)</h1>
        <p class="view-subtitle">Gestión interactiva de órdenes de trabajo preventivas programadas en grilla estilo Excel</p>
      </div>
      
      <!-- Grupo de botones de acción rápida en el encabezado -->
      <div class="header-actions">
        <!-- Botón para abrir el modal especializado en Cierre y Reprogramaciones -->
        <button type="button" class="btn btn-primary" @click="openManagementModal">
          <span class="icon">📝</span> Cierre / Reprogramar Tarea
        </button>
        <!-- Botón para recargar todos los datos y catálogos de la vista -->
        <button
          type="button"
          class="btn btn-blue"
          @click="refreshAllData"
          :disabled="loading"
        >
          <span class="icon">🔄</span> {{ loading ? 'Cargando...' : 'Recargar Datos' }}
        </button>
      </div>
    </header>

    <!-- Banner visual para mostrar mensajes de error cuando ocurre algún fallo en las peticiones -->
    <p v-if="error" class="feedback error">⚠️ {{ error }}</p>

    <!-- Envoltorio principal para montar el componente de tabla editable ExcelGrid -->
    <!-- Se escucha el evento @rowDblClick para abrir el modal especializado directamente al hacer doble clic -->
    <div class="grid-wrapper">
      <ExcelGrid
        v-if="!loading"
        title="Cronograma y Ejecución de Tareas Programadas Preventivas (Haz clic para seleccionar o doble clic para gestionar Cierre / Reprogramación)"
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
        @rowDblClick="handleRowDblClick"
        @rowSelect="handleRowSelect"
      />
      <!-- Mensaje secundario de carga si aún no se han recibido los datos iniciales -->
      <p v-else class="loading-text">Cargando programación y jerarquías...</p>
    </div>

    <!-- MODAL ESPECIALIZADO PARA CIERRES Y REPROGRAMACIONES DE TASKP -->
    <div v-if="isModalOpen" class="modal-backdrop" @click.self="closeModal">
      <div class="modal-dialog">
        <!-- Cabecera del modal -->
        <div class="modal-header">
          <h3>📋 Gestión de Orden de Trabajo #{{ modalForm.id || 'N/A' }}</h3>
          <button class="btn-close" @click="closeModal">✕</button>
        </div>

        <!-- Selector de pestañas dentro del modal -->
        <div class="modal-tabs">
          <button
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'close' }"
            @click="activeTab = 'close'"
          >
            ✅ Cierre / Finalización
          </button>
          <button
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === 'reschedule' }"
            @click="activeTab = 'reschedule'"
          >
            🗓️ Reprogramación / Excepción
          </button>
        </div>

        <!-- Cuerpo del formulario modal -->
        <div class="modal-body">
          <form @submit.prevent="saveTaskPFromModal">
            <!-- INFORMACIÓN RESUMIDA DE LA TAREA PROGRAMADA -->
            <div class="task-info-card">
              <div><strong>Descripción / Catálogo:</strong> {{ selectedTaskCatalogDesc }}</div>
              <div><strong>Ubicación:</strong> {{ selectedTaskLocation }}</div>
              <div><strong>Fecha Planificada:</strong> {{ modalForm.date || 'Sin fecha' }} (Semana {{ modalForm.week || '-' }})</div>
            </div>

            <!-- PESTAÑA 1: CIERRE Y FINALIZACIÓN DE ORDEN DE TRABAJO -->
            <div v-if="activeTab === 'close'" class="tab-content">
              <fieldset class="form-section">
                <legend>✅ Registro de Ejecución Real y Cierre</legend>

                <div class="form-row">
                  <!-- Estado de Ejecución -->
                  <div class="form-group required">
                    <label for="modal-estado">Estado de Ejecución (*):</label>
                    <select id="modal-estado" v-model="modalForm.estado_id" class="form-control" required>
                      <option v-for="e in estadosList" :key="e.id" :value="e.id">
                        {{ e.estado_nombre || e.name }}
                      </option>
                    </select>
                  </div>

                  <!-- Fecha Real de Término / Completado -->
                  <div class="form-group">
                    <label for="modal-completion-date">Fecha de Término Real:</label>
                    <input id="modal-completion-date" type="date" v-model="modalForm.completion_date" class="form-control" />
                  </div>
                </div>

                <!-- Comentarios u observaciones finales del operador -->
                <div class="form-group">
                  <label for="modal-comments">Comentarios / Notas de Cierre:</label>
                  <textarea id="modal-comments" v-model="modalForm.comments" class="form-control" rows="4" placeholder="Ingrese hallazgos, repuestos utilizados u observaciones de cierre..."></textarea>
                </div>
              </fieldset>
            </div>

            <!-- PESTAÑA 2: REPROGRAMACIÓN Y MANEJO DE EXCEPCIONES -->
            <div v-if="activeTab === 'reschedule'" class="tab-content">
              <fieldset class="form-section">
                <legend>🗓️ Control de Reprogramación</legend>

                <div class="form-row">
                  <!-- Marca de Reprogramado (Booleano) -->
                  <div class="form-group checkbox-group">
                    <label class="checkbox-label">
                      <input type="checkbox" v-model="modalForm.rescheduled" />
                      <strong>Marcar como Tarea Reprogramada / Atrasada</strong>
                    </label>
                  </div>

                  <!-- Marca de Reprogramación Permanente -->
                  <div class="form-group checkbox-group">
                    <label class="checkbox-label">
                      <input type="checkbox" v-model="modalForm.is_permanent_reschedule" />
                      <strong>Aplicar Reprogramación Permanente a Rutinas Futuras</strong>
                    </label>
                  </div>
                </div>

                <div class="form-row">
                  <!-- Nueva Fecha Reprogramada -->
                  <div class="form-group" :class="{ required: modalForm.rescheduled }">
                    <label for="modal-rescheduled-date">Nueva Fecha Reprogramada:</label>
                    <input id="modal-rescheduled-date" type="date" v-model="modalForm.reschedule_date" class="form-control" :required="modalForm.rescheduled" />
                  </div>

                  <!-- Grupo / Operador Asignado -->
                  <div class="form-group">
                    <label for="modal-group">Grupo / Cuadrilla Asignada:</label>
                    <select id="modal-group" v-model="modalForm.group_id" class="form-control">
                      <option :value="null">-- Sin Grupo Asignado --</option>
                      <option v-for="u in usersPList" :key="u.id" :value="u.id">{{ u.name }}</option>
                    </select>
                  </div>
                </div>

                <!-- Razón o Justificación de la Reprogramación -->
                <div class="form-group" :class="{ required: modalForm.rescheduled }">
                  <label for="modal-reschedule-reason">Razón / Justificación Técnica de la Reprogramación:</label>
                  <textarea id="modal-reschedule-reason" v-model="modalForm.reschedule_reason" class="form-control" rows="3" placeholder="Ej. Retraso en llegada de repuestos, falta de disponibilidad de equipo..." :required="modalForm.rescheduled"></textarea>
                </div>
              </fieldset>
            </div>

            <!-- Botones de Acción del Modal -->
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">Cancelar</button>
              <button type="submit" class="btn btn-success" :disabled="modalSaving">
                {{ modalSaving ? 'Guardando...' : 'Guardar Cambios de la Orden' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// --- IMPORTACIÓN DE MÓDULOS DE VUE 3 Y LIBRERÍAS DE SOPORTE ---
// Importamos primitivas reactivas del core de Vue
import { onMounted, ref, computed } from 'vue';
// Importamos la instancia configurada de Axios para realizar llamadas REST a la API de Django
import { api } from '../../api';
// Importamos el componente reutilizable de grilla editable interactiva
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos el composable para la resolución de la jerarquía de equipos (Planta -> Área -> Sistema -> Equipo)
import { useEquipmentHierarchies } from '../../composables/useEquipmentHierarchies';

// --- ESTADOS REACTIVOS PRINCIPALES ---
// Indica si la pantalla se encuentra realizando peticiones de red
const loading = ref(false);
// Mensaje de error para notificaciones al usuario
const error = ref('');
// Almacena las respuestas JSON originales de la API sin transformar
const rawTasksP = ref([]);

// --- ESTADOS DE PAGINACIÓN, FILTROS Y ORDENAMIENTO ---
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]); 

// --- LISTAS AUXILIARES PARA SELECTORES DESPLEGABLES ---
// Lista de plantillas de tareas preventivas (Task)
const tasksList = ref([]);
// Lista completa del catálogo de tareas (TaskCatalog) para mostrar la descripción
const taskCatalogList = ref([]);
// Lista de grupos / operadores asignables (UserP)
const usersPList = ref([]); 
// Lista de estados de ejecución (Estado)
const estadosList = ref([]);

// --- INICIALIZACIÓN DE COMPOSABLES ---
// Obtenemos funciones para resolver nombres de jerarquía y construir parámetros de filtrado server-side
const { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams } = useEquipmentHierarchies();

// --- ESTADOS REACTIVOS PARA MODAL ESPECIALIZADO ---
// Controla la visibilidad del modal de gestión
const isModalOpen = ref(false);
// Controla la pestaña activa del modal ('close' para finalización o 'reschedule' para reprogramación)
const activeTab = ref('close');
// Estado de guardado dentro del modal
const modalSaving = ref(false);

// Objeto de formulario reactivo para el modal de TaskP
const modalForm = ref({
  id: null,
  task_id: null,
  date: '',
  year: null,
  week: null,
  estado_id: null,
  completion_date: '',
  comments: '',
  rescheduled: false,
  reschedule_date: '',
  reschedule_reason: '',
  is_permanent_reschedule: false,
  group_id: null,
  priority: 2
});

// Textos descriptivos para el encabezado informativo del modal
const selectedTaskCatalogDesc = ref('');
const selectedTaskLocation = ref('');

// --- CONFIGURACIÓN DE CABECERAS Y CAMPOS DE LA GRILLA ---
const gridHeaders = [
  'ID', 
  'Descripción del Catálogo', 
  'Planta', 
  'Área', 
  'Sistema', 
  'Equipo Asignado', 
  'Año', 
  'Semana', 
  'Día', 
  'Fecha Planificada', 
  'Grupo / Asignado', 
  'Estado de Ejecución', 
  'Prioridad', 
  'Fecha Completado', 
  'Comentarios / Notas', 
  'Reprogramado', 
  'Razón Reprogramación', 
  'Nueva Fecha Reprog.', 
  'Reprog. Permanente'
];

// Mapeo exacto de las claves del modelo TaskP y relaciones de jerarquía
const colKeys = [
  'id', 
  'task_id', 
  'equipment__area__plant__name', 
  'equipment__area__name', 
  'equipment__system__name', 
  'equipment__name', 
  'year', 
  'week', 
  'day', 
  'date', 
  'group_id', 
  'estado_id', 
  'priority', 
  'completion_date', 
  'comments', 
  'rescheduled', 
  'reschedule_reason', 
  'reschedule_date', 
  'is_permanent_reschedule'
];

// --- CONFIGURACIÓN DINÁMICA DE CELDAS Y DESPLEGABLES (columnsConfig) ---
const gridConfig = computed(() => {
  const taskOptions = tasksList.value.map(t => {
    const catalogId = typeof t.task_catalog === 'object' ? t.task_catalog?.id : t.task_catalog;
    const catObj = taskCatalogList.value.find(c => c.id === catalogId) || {};
    const labelDesc = catObj.description || t.task_catalog_description || t.description || t.name || `Tarea #${t.id}`;
    
    return { 
      value: String(t.id), 
      label: labelDesc 
    };
  }).sort((a, b) => a.label.localeCompare(b.label));

  const groupOptions = usersPList.value.map(u => ({ 
    value: String(u.id), 
    label: u.name || `Grupo #${u.id}` 
  })).sort((a, b) => a.label.localeCompare(b.label));

  const estadoOptions = estadosList.value.map(e => ({ 
    value: String(e.id), 
    label: e.estado_nombre || `Estado #${e.id}` 
  })).sort((a, b) => a.label.localeCompare(b.label));

  const boolOptions = [
    { value: 'true', label: 'Sí' }, 
    { value: 'false', label: 'No' }
  ];

  const priorityOptions = [
    { value: '1', label: '1 - Alta' },
    { value: '2', label: '2 - Media' },
    { value: '3', label: '3 - Baja' }
  ];

  return {
    0: { readOnly: true },
    1: { type: 'select', options: taskOptions },
    2: { readOnly: true },
    3: { readOnly: true },
    4: { readOnly: true },
    5: { readOnly: true },
    10: { type: 'select', options: groupOptions },
    11: { type: 'select', options: estadoOptions },
    12: { type: 'select', options: priorityOptions },
    15: { type: 'select', options: boolOptions },
    18: { type: 'select', options: boolOptions }
  };
});

// --- HELPER PARA RESOLVER EL ID DEL EQUIPO DESDE TASKP ---
const getEquipmentIdFromTaskP = (item) => {
  if (item.task && typeof item.task === 'object') {
    return typeof item.task.equipment === 'object' ? item.task.equipment?.id : item.task.equipment;
  }
  return item.equipment || null;
};

// --- TRANSFORMACIÓN DE DATOS A MATRIZ 2D PARA EXCELGRID ---
const gridData = computed(() => {
  return rawTasksP.value.map(item => {
    const eqId = getEquipmentIdFromTaskP(item);
    const { plantName, areaName, systemName, equipmentName } = getEquipmentHierarchyRow(eqId);

    return colKeys.map(key => {
      if (key === 'equipment__area__plant__name') return plantName;
      if (key === 'equipment__area__name') return areaName;
      if (key === 'equipment__system__name') return systemName;
      if (key === 'equipment__name') return equipmentName;

      if (key === 'task_id') {
        const val = item.task;
        return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
      }
      if (key === 'group_id') {
        const val = item.group;
        return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
      }
      if (key === 'estado_id') {
        const val = item.estado;
        return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
      }

      let val = item[key];
      if (typeof val === 'boolean') val = val ? 'true' : 'false';
      if (typeof val === 'string' && val.includes('T')) val = val.split('T')[0];
      return val === null || val === undefined ? '' : String(val);
    });
  });
});

// --- MÉTODOS AUXILIARES Y PETICIONES A LA API ---

const extractData = (response) => {
  if (response.data && response.data.results) return response.data.results;
  if (Array.isArray(response.data)) return response.data;
  return [];
};

const loadSelectionLists = async () => {
  try {
    const params = { page_size: 10000 };
    const [tasksRes, catalogRes, usersPRes, estadosRes] = await Promise.all([
      api.get('tasks/', { params }),
      api.get('taskcatalogs/', { params }),
      api.get('userp/', { params }),
      api.get('estados/', { params })
    ]);
    tasksList.value = extractData(tasksRes);
    taskCatalogList.value = extractData(catalogRes);
    usersPList.value = extractData(usersPRes);
    estadosList.value = extractData(estadosRes);
  } catch (err) {
    console.error("Error al cargar listas auxiliares de programación:", err);
  }
};

const loadFilterData = async () => {
  try {
    const res = await api.get('taskp/', { params: { page_size: 10000 } });
    const results = extractData(res);

    filterData.value = results.map(item => {
      const eqId = getEquipmentIdFromTaskP(item);
      const { plantName, areaName, systemName, equipmentName } = getEquipmentHierarchyRow(eqId);

      return colKeys.map(key => {
        if (key === 'equipment__area__plant__name') return plantName;
        if (key === 'equipment__area__name') return areaName;
        if (key === 'equipment__system__name') return systemName;
        if (key === 'equipment__name') return equipmentName;

        if (key === 'task_id') {
          const val = item.task;
          return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
        }
        if (key === 'group_id') {
          const val = item.group;
          return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
        }
        if (key === 'estado_id') {
          const val = item.estado;
          return val && typeof val === 'object' ? String(val.id) : (val !== null && val !== undefined ? String(val) : '');
        }

        let val = item[key];
        if (typeof val === 'boolean') val = val ? 'true' : 'false';
        if (typeof val === 'string' && val.includes('T')) val = val.split('T')[0];
        return val === null || val === undefined ? '' : String(val);
      });
    });
  } catch (err) {
    console.error("Error al cargar datos para los filtros:", err);
  }
};

const loadData = async (page = 1) => {
  loading.value = true;
  error.value = '';

  try {
    let params = {
      page: page,
      page_size: pageSize.value
    };

    const hierarchyIndexes = { plant: '2', area: '3', system: '4', equipment: '5' };
    params = buildFilterParams(params, currentFilters.value, colKeys, hierarchyIndexes);

    if (currentSort.value.colIndex !== null) {
      const fieldName = colKeys[currentSort.value.colIndex];
      if (fieldName && !fieldName.includes('__')) {
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
      const data = extractData(response);
      rawTasksP.value = data;
      totalItems.value = data.length;
      totalPages.value = 1;
      currentPage.value = 1;
    }
  } catch (err) {
    error.value = "Error al conectar con la API de Programación de Tareas (TaskP).";
  } finally {
    loading.value = false;
  }
};

const refreshAllData = async () => {
  await loadDependencies();
  await loadSelectionLists();
  await loadData(currentPage.value);
  await loadFilterData();
};

// --- MANEJADORES DE EVENTOS DE EXCELGRID ---
const handlePageChange = (newPage) => loadData(newPage);
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

// Variable reactiva para almacenar el registro de TaskP seleccionado activamente en ExcelGrid
const selectedTaskPItem = ref(null);

// Manejador de selección de fila al hacer clic en cualquier celda o fila de ExcelGrid
const handleRowSelect = ({ row }) => {
  if (!row || row.length === 0) return;
  const taskPId = Number(row[0]);
  if (isNaN(taskPId) || !taskPId) return;

  const item = rawTasksP.value.find(t => t.id === taskPId);
  if (item) {
    selectedTaskPItem.value = item;
  }
};

// MANEJADOR DE DOBLE CLIC EN FILAS PARA ABRIR EL MODAL DE GESTIÓN DE TASKP DE LA FILA SELECCIONADA
const handleRowDblClick = ({ row }) => {
  if (!row || row.length === 0) return;
  const taskPId = Number(row[0]);
  if (isNaN(taskPId) || !taskPId) return;

  const item = rawTasksP.value.find(t => t.id === taskPId);
  if (item) {
    selectedTaskPItem.value = item;
    populateModalFormWithTaskP(item);
    isModalOpen.value = true;
  }
};

// --- GESTIÓN DEL MODAL DE TASKP ---
const populateModalFormWithTaskP = (item) => {
  if (!item) return;

  const taskId = typeof item.task === 'object' ? item.task?.id : item.task;
  const groupId = typeof item.group === 'object' ? item.group?.id : item.group;
  const estadoId = typeof item.estado === 'object' ? item.estado?.id : item.estado;

  // Obtenemos textos informativos para la cabecera del modal
  const taskObj = tasksList.value.find(t => t.id === taskId) || {};
  const catalogId = typeof taskObj.task_catalog === 'object' ? taskObj.task_catalog?.id : taskObj.task_catalog;
  const catObj = taskCatalogList.value.find(c => c.id === catalogId) || {};
  selectedTaskCatalogDesc.value = catObj.description || taskObj.name || `Tarea #${taskId || '-'}`;

  const eqId = getEquipmentIdFromTaskP(item);
  const { plantName, areaName, systemName, equipmentName } = getEquipmentHierarchyRow(eqId);
  selectedTaskLocation.value = `${plantName} / ${areaName} / ${systemName} / ${equipmentName}`;

  let compDate = item.completion_date || '';
  if (compDate.includes('T')) compDate = compDate.split('T')[0];

  let resDate = item.reschedule_date || '';
  if (resDate.includes('T')) resDate = resDate.split('T')[0];

  modalForm.value = {
    id: item.id,
    task_id: taskId || null,
    date: item.date || '',
    year: item.year || null,
    week: item.week || null,
    estado_id: estadoId || (estadosList.value.length > 0 ? estadosList.value[0].id : null),
    completion_date: compDate,
    comments: item.comments || '',
    rescheduled: item.rescheduled || false,
    reschedule_date: resDate,
    reschedule_reason: item.reschedule_reason || '',
    is_permanent_reschedule: item.is_permanent_reschedule || false,
    group_id: groupId || null,
    priority: item.priority || 2
  };
};

// Abre el modal especializado jalando la tarea actualmente seleccionada en ExcelGrid
const openManagementModal = () => {
  if (selectedTaskPItem.value) {
    populateModalFormWithTaskP(selectedTaskPItem.value);
    isModalOpen.value = true;
    return;
  }

  // Fallback: Si el usuario aún no ha hecho clic en ninguna fila, se usa el primer registro cargado
  if (rawTasksP.value.length > 0) {
    selectedTaskPItem.value = rawTasksP.value[0];
    populateModalFormWithTaskP(rawTasksP.value[0]);
    isModalOpen.value = true;
  } else {
    alert('No hay órdenes de trabajo disponibles en la grilla.');
  }
};

const closeModal = () => {
  isModalOpen.value = false;
};

// Guarda los cambios de finalización o reprogramación desde el modal
const saveTaskPFromModal = async () => {
  if (!modalForm.value.id) {
    alert('No hay ninguna orden de trabajo seleccionada.');
    return;
  }

  modalSaving.value = true;
  try {
    const payload = {
      task_id: modalForm.value.task_id,
      estado_id: modalForm.value.estado_id,
      completion_date: modalForm.value.completion_date || null,
      comments: modalForm.value.comments ? modalForm.value.comments.trim() : null,
      rescheduled: Boolean(modalForm.value.rescheduled),
      reschedule_date: modalForm.value.reschedule_date || null,
      reschedule_reason: modalForm.value.reschedule_reason ? modalForm.value.reschedule_reason.trim() : null,
      is_permanent_reschedule: Boolean(modalForm.value.is_permanent_reschedule),
      group_id: modalForm.value.group_id || null,
      priority: Number(modalForm.value.priority)
    };

    await api.put(`taskp/${modalForm.value.id}/`, payload);
    alert(`Orden de trabajo #${modalForm.value.id} actualizada con éxito.`);
    closeModal();
    await loadData(currentPage.value);
    await loadFilterData();
  } catch (e) {
    alert('Error al guardar los cambios de la orden de trabajo en el servidor.');
  } finally {
    modalSaving.value = false;
  }
};

const handleSave = async (gridRows) => {
  loading.value = true;
  error.value = '';

  try {
    const promises = gridRows.map(row => {
      const payload = {};

      colKeys.forEach((key, idx) => {
        if (key.includes('__')) return;

        let val = row[idx];
        if (typeof val === 'string') val = val.trim();

        if (val === '' || val === null || val === undefined) {
          payload[key] = null;
          return;
        }

        if (key === 'rescheduled' || key === 'is_permanent_reschedule') {
          payload[key] = val === 'true';
          return;
        }

        if (['year', 'week', 'priority', 'task_id', 'group_id', 'estado_id'].includes(key)) {
          payload[key] = isNaN(Number(val)) ? null : Number(val);
          return;
        }

        payload[key] = val;
      });

      const id = payload.id;
      const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));

      if (isExisting) {
        return api.put(`taskp/${id}/`, payload);
      } else {
        delete payload.id;
        return api.post('taskp/', payload);
      }
    });

    await Promise.all(promises);
    alert('Programación de tareas preventivas actualizada correctamente.');
    await loadData(currentPage.value);
    await loadFilterData();
  } catch (err) {
    error.value = "Error al guardar cambios. Verifique que las fechas (YYYY-MM-DD) y números sean válidos.";
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  if (!confirm(`¿Está seguro de eliminar ${idsToDelete.length} registro(s) de programación permanentemente?`)) return;

  loading.value = true;
  try {
    await Promise.all(idsToDelete.map(id => api.delete(`taskp/${id}/`)));
    alert('Registro(s) de programación eliminado(s) correctamente.');
    await loadData(currentPage.value);
    await loadFilterData();
  } catch (err) {
    error.value = "Error al intentar eliminar los registros seleccionados.";
  } finally {
    loading.value = false;
  }
};

// --- CICLO DE VIDA DE VUE ---
onMounted(async () => {
  await loadDependencies();
  await loadSelectionLists();
  await loadData();
  await loadFilterData();
});
</script>

<style scoped>
/* Estilos generales del contenedor de la vista */
.scheduled-tasks-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  height: 100%;
  position: relative;
}

/* Encabezado con título e instrucciones */
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  padding: 14px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.view-title {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
  font-weight: 700;
}

.view-subtitle {
  margin: 0;
  font-size: 0.85rem;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 10px;
}

/* Envoltorio principal para la grilla ExcelGrid */
.grid-wrapper {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
}

/* Notificación de errores */
.feedback.error {
  color: #991b1b;
  background: #fef2f2;
  padding: 10px 16px;
  border-radius: 6px;
  border: 1px solid #fecaca;
  font-weight: 600;
  margin: 0;
}

/* Estilos de botones estándar */
.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #2563eb;
  color: #ffffff;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-blue {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-blue:hover {
  background-color: #0369a1;
}

.btn-secondary {
  background-color: #64748b;
  color: #ffffff;
}

.btn-success {
  background-color: #16a34a;
  color: #ffffff;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #64748b;
}

/* MODALES Y CAPAS DIÁLOGO DE TASKP */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-dialog {
  background: #ffffff;
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-header {
  padding: 16px 24px;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.15rem;
  color: #0f172a;
}

/* PESTAÑAS DEL MODAL */
.modal-tabs {
  display: flex;
  background-color: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
}

.tab-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  background: transparent;
  font-weight: 600;
  font-size: 0.9rem;
  color: #64748b;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background-color: #ffffff;
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
}

.task-info-card {
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
  font-size: 0.88rem;
  color: #1e3a8a;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #fafafa;
}

.form-section legend {
  font-weight: 700;
  font-size: 0.9rem;
  color: #334155;
  padding: 0 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}

.form-group.required label::after {
  content: " *";
  color: #dc2626;
}

.checkbox-group {
  justify-content: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.88rem;
  cursor: pointer;
}

.form-control {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: #ffffff;
}

textarea.form-control {
  resize: vertical;
}

.modal-footer {
  padding: 16px 24px;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.loading-text {
  padding: 20px;
  text-align: center;
  color: #64748b;
  font-weight: bold;
}
</style>
