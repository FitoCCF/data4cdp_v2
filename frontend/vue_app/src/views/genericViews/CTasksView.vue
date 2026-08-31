<template>
  <!-- Contenedor principal de la vista de mantenimiento para Tareas Correctivas (Modelo CorrectiveTask) -->
  <div class="corrective-tasks-view">
    <!-- Barra superior de acciones para crear nuevas tareas y refrescar datos -->
    <div class="action-bar">
      <!-- Título de la vista -->
      <h2 class="view-title">Mantenimiento de Tareas Correctivas</h2>
      
      <!-- Grupo de botones de acción rápida -->
      <div class="button-group">
        <!-- Botón principal para abrir el modal en modo creación de una nueva tarea correctiva -->
        <button class="btn btn-primary" @click="openCreateModal">
          <span class="icon">+</span> Nueva Tarea Correctiva
        </button>
        <!-- Botón para recargar los datos manualmente -->
        <button class="btn btn-secondary" @click="refreshAllData" :disabled="loading">
          <span class="icon">🔄</span> Actualizar
        </button>
      </div>
    </div>

    <!-- Componente ExcelGrid reutilizable para la visualización tabular y filtrado masivo -->
    <!-- Se incluye la escucha del evento @rowDblClick para abrir la edición detallada en modal al hacer doble clic -->
    <ExcelGrid
      title="Catálogo y Registro de Tareas Correctivas Imprevistas (Doble clic en fila para editar en modal)"
      :headers="headers"
      :data="gridData"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :totalItems="totalItems"
      :pageSize="pageSize"
      :serverSideFiltering="true"
      :filterData="filterData"
      :columnsConfig="columnsConfig"
      @save="handleSaveFromGrid"
      @delete="confirmDeleteFromGrid"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
      @rowDblClick="handleRowDblClick"
    />

    <!-- Overlay visual de carga que se muestra cuando 'loading' es verdadero -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>Cargando tareas correctivas...</span>
    </div>

    <!-- Banner para mostrar mensajes de error cuando falla la comunicación con la API -->
    <div v-if="error" class="error-banner">
      <span>⚠️ {{ error }}</span>
      <button class="btn-close-error" @click="clearError">✕</button>
    </div>

    <!-- MODAL DE CREACIÓN Y EDICIÓN DETALLADA (SIN SELECTOR INTERNO DE BÚSQUEDA) -->
    <div v-if="isModalOpen" class="modal-backdrop" @click.self="closeModal">
      <!-- Contenedor del diálogo modal -->
      <div class="modal-dialog">
        <!-- Cabecera del modal con título dinámico de creación o edición -->
        <div class="modal-header">
          <h3>{{ isEditing ? '✏️ Editando Tarea Correctiva #' + form.id : '➕ Registrar Nueva Tarea Correctiva' }}</h3>
          <button class="btn-close" @click="closeModal">✕</button>
        </div>

        <!-- Cuerpo del formulario modal -->
        <div class="modal-body">
          <form @submit.prevent="saveTaskFromModal">
            <!-- SECCIÓN 1: UBICACIÓN TÉCNICA (JERARQUÍA DE EQUIPOS EN CASCADA) -->
            <fieldset class="form-section">
              <legend>📍 Ubicación Técnica (Equipo Afectado)</legend>
              
              <div class="form-row">
                <!-- Selector de Planta -->
                <div class="form-group">
                  <label for="modal-plant">Planta:</label>
                  <select id="modal-plant" v-model="selectedPlantId" @change="onPlantChange" class="form-control">
                    <option value="">-- Seleccionar Planta --</option>
                    <option v-for="p in plantsOptions" :key="p.id" :value="p.id">{{ p.name }}</option>
                  </select>
                </div>

                <!-- Selector de Área (filtrado por la Planta seleccionada) -->
                <div class="form-group">
                  <label for="modal-area">Área:</label>
                  <select id="modal-area" v-model="selectedAreaId" @change="onAreaChange" class="form-control" :disabled="!selectedPlantId">
                    <option value="">-- Seleccionar Área --</option>
                    <option v-for="a in filteredAreasOptions" :key="a.id" :value="a.id">{{ a.name }}</option>
                  </select>
                </div>
              </div>

              <div class="form-row">
                <!-- Selector de Sistema (filtrado o independiente) -->
                <div class="form-group">
                  <label for="modal-system">Sistema:</label>
                  <select id="modal-system" v-model="selectedSystemId" @change="onSystemChange" class="form-control">
                    <option value="">-- Seleccionar Sistema --</option>
                    <option v-for="s in systemsOptions" :key="s.id" :value="s.id">{{ s.name }}</option>
                  </select>
                </div>

                <!-- Selector del Equipo Final (Requerido) -->
                <div class="form-group required">
                  <label for="modal-equipment">Equipo Asignado (*):</label>
                  <select id="modal-equipment" v-model="form.equipment" class="form-control" required>
                    <option value="">-- Seleccionar Equipo --</option>
                    <option v-for="eq in filteredEquipmentsOptions" :key="eq.id" :value="eq.id">
                      {{ eq.name }} {{ eq.description ? ' - ' + eq.description : '' }}
                    </option>
                  </select>
                </div>
              </div>
            </fieldset>

            <!-- SECCIÓN 2: INFORMACIÓN GENERAL DE LA FALLA Y CATEGORÍA DEL CATÁLOGO -->
            <fieldset class="form-section">
              <legend>📋 Detalle del Incidente / Falla</legend>

              <div class="form-row">
                <!-- Nombre o Título corto de la tarea correctiva -->
                <div class="form-group required">
                  <label for="modal-name">Título / Nombre Corto (*):</label>
                  <input id="modal-name" type="text" v-model="form.name" class="form-control" placeholder="Ej. Fuga de lubricante en sello inferior" required />
                </div>

                <!-- Categoría del Catálogo de Tareas (Muestra 'description' en las opciones) -->
                <div class="form-group">
                  <label for="modal-catalog">Categoría (Catálogo):</label>
                  <select id="modal-catalog" v-model="form.task_catalog" class="form-control">
                    <option :value="null">-- Sin categoría específica --</option>
                    <!-- Mapeo de categorías existentes mostrando su campo 'description' -->
                    <option v-for="cat in taskCatalogList" :key="cat.id" :value="cat.id">
                      {{ cat.description || cat.name }}
                    </option>
                    <!-- OPCIÓN AL FINAL DEL SELECTOR PARA INGRESAR LA DESCRIPCIÓN DE UN NUEVO REGISTRO EN EL CATÁLOGO -->
                    <option value="__NEW_CATALOG__">
                      ➕ + Escribir nueva descripción para crear registro en Catálogo...
                    </option>
                  </select>
                </div>
              </div>

              <!-- CAMPO QUE APARECE AL SELECCIONAR LA OPCIÓN FINAL DEL SELECTOR DE CATÁLOGO PARA INGRESAR SU DESCRIPCIÓN -->
              <div v-if="form.task_catalog === '__NEW_CATALOG__'" class="form-group required new-cat-input-container">
                <label for="new-cat-description">
                  <strong>Descripción del Nuevo Registro para el Catálogo (*):</strong>
                </label>
                <input
                  id="new-cat-description"
                  type="text"
                  v-model="newCategoryDescription"
                  class="form-control highlight-input"
                  placeholder="Ingrese la descripción para este nuevo registro en el catálogo..."
                  required
                />
                <small class="help-text">
                  ℹ️ Se utilizará el <strong>Título / Nombre Corto</strong> ("{{ form.name || 'Sin título' }}") como identificador <code>name</code> del nuevo catálogo.
                </small>
              </div>

              <!-- Descripción amplia del incidente (Textarea cómodo para textos largos) -->
              <div class="form-group required">
                <label for="modal-description">Descripción de la Falla (*):</label>
                <textarea id="modal-description" v-model="form.description" class="form-control" rows="4" placeholder="Describa el incidente, síntomas u observaciones iniciales..." required></textarea>
              </div>

              <!-- Diagnóstico de Causa Raíz (Textarea cómodo para textos largos) -->
              <div class="form-group">
                <label for="modal-root-cause">Causa Raíz / Diagnóstico Técnico:</label>
                <textarea id="modal-root-cause" v-model="form.root_cause" class="form-control" rows="4" placeholder="Ingrese el análisis de causa raíz determinado por el equipo técnico..."></textarea>
              </div>
            </fieldset>

            <!-- SECCIÓN 3: CLASIFICACIÓN, RESPONSABLE Y ATRIBUTOS DE CONTROL -->
            <fieldset class="form-section">
              <legend>⚙️ Parámetros de Control</legend>

              <div class="form-row">
                <!-- Nivel de Criticidad / Prioridad -->
                <div class="form-group required">
                  <label for="modal-priority">Criticidad / Prioridad (*):</label>
                  <select id="modal-priority" v-model.number="form.priority" class="form-control" required>
                    <option :value="1">🔴 Alta (Emergencia / Parada)</option>
                    <option :value="2">🟡 Media (Atención Urgente)</option>
                    <option :value="3">🟢 Baja (Mantenimiento Programable)</option>
                  </select>
                </div>

                <!-- Turno de Trabajo -->
                <div class="form-group">
                  <label for="modal-turno">Turno Asignado:</label>
                  <select id="modal-turno" v-model="form.turno" class="form-control">
                    <option value="">-- Sin Turno --</option>
                    <option value="A">Turno A</option>
                    <option value="B">Turno B</option>
                    <option value="C">Turno C</option>
                    <option value="DN">Día / Noche (DN)</option>
                  </select>
                </div>
              </div>

              <div class="form-row">
                <!-- Fecha de Reporte -->
                <div class="form-group required">
                  <label for="modal-date">Fecha de Reporte (*):</label>
                  <input id="modal-date" type="date" v-model="form.creation_date" class="form-control" required />
                </div>

                <!-- Usuario Reportante -->
                <div class="form-group required">
                  <label for="modal-user">Reportado por (*):</label>
                  <select id="modal-user" v-model="form.created_by_user" class="form-control" required>
                    <option value="">-- Seleccionar Usuario --</option>
                    <option v-for="u in usersList" :key="u.id" :value="u.id">
                      {{ u.nombre }} {{ u.apellido }}
                    </option>
                  </select>
                </div>
              </div>
            </fieldset>

            <!-- Acciones del Formulario Modal -->
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">Cancelar</button>
              <button type="submit" class="btn btn-success" :disabled="modalSaving">
                {{ modalSaving ? 'Guardando...' : (isEditing ? 'Actualizar Registro #' + form.id : 'Guardar Tarea Correctiva') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- MODAL DE CONFIRMACIÓN DE ELIMINACIÓN SEGURA -->
    <div v-if="isDeleteModalOpen" class="modal-backdrop" @click.self="closeDeleteModal">
      <div class="modal-dialog modal-small">
        <div class="modal-header header-danger">
          <h3>⚠️ Confirmar Eliminación</h3>
          <button class="btn-close" @click="closeDeleteModal">✕</button>
        </div>
        <div class="modal-body">
          <p>¿Está seguro de que desea eliminar permanentemente <strong>{{ itemsToDelete.length }}</strong> tarea(s) correctiva(s)?</p>
          <div class="warning-box">
            <strong>Nota Importante:</strong> Si la tarea correctiva tiene órdenes de trabajo programadas (<code>TaskP</code>) asociadas en el calendario, estas también serán removidas en cascada.
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeDeleteModal">Cancelar</button>
          <button class="btn btn-danger" @click="executeDelete" :disabled="deleting">
            {{ deleting ? 'Eliminando...' : 'Sí, Eliminar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// --- IMPORTACIÓN DE MÓDULOS DE VUE 3 Y LIBRERÍAS DE SOPORTE ---
// Importamos las primitivas reactivas del core de Vue
import { ref, onMounted, computed } from 'vue';
// Importamos el componente de tabla editable reutilizable estilo Excel
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos el cliente HTTP de Axios para peticiones REST a Django
import { api } from '../../api';
// Importamos el composable para manejo de estado de carga y errores de API
import { useApi } from '../../composables/useApi';
// Importamos el composable para la gestión de la jerarquía de equipos
import { useEquipmentHierarchies } from '../../composables/useEquipmentHierarchies';

// --- DEFINICIÓN DE ESTRUCTURA Y NOMBRES DE COLUMNAS DE LA GRILLA ---
// Definimos los títulos visibles de la tabla en el orden deseado
const headers = [
  'ID', 
  'Categoría Catálogo', 
  'Título / Nombre Corto', 
  'Planta', 
  'Área', 
  'Sistema', 
  'Equipo Asignado', 
  'Descripción del Incidente', 
  'Diagnóstico Causa Raíz', 
  'Fecha Reporte', 
  'Criticidad', 
  'Reportado por', 
  'Turno'
];

// Mapeamos las claves de datos correspondientes a los campos del modelo CorrectiveTask y de la jerarquía
const colKeys = [
  'id', 
  'task_catalog', 
  'name', 
  'equipment__area__plant__name', 
  'equipment__area__name', 
  'equipment__system__name', 
  'equipment',
  'description', 
  'root_cause', 
  'creation_date', 
  'priority', 
  'created_by_user', 
  'turno'
];

// --- ESTADOS REACTIVOS PRINCIPALES ---
// Almacena las filas en matriz 2D para ser renderizadas por el componente ExcelGrid
const gridData = ref([]);
// Almacena el universo de datos para construir los desplegables de filtro por columna
const filterData = ref([]);
// Lista completa de usuarios obtenida del backend para los selectores
const usersList = ref([]);
// Lista completa del catálogo de tareas (TaskCatalog)
const taskCatalogList = ref([]);
// Lista completa de tareas correctivas en objeto para resolver la carga en modal al hacer doble clic
const rawTasksList = ref([]);
// Listas auxiliares para la jerarquía técnica en los formularios modales
const plantsOptions = ref([]);
const areasOptions = ref([]);
const systemsOptions = ref([]);

// --- ESTADO PARA CREAR REGISTRO EN EL CATÁLOGO DESDE EL MISMO SELECTOR DE CATEGORÍA ---
// Almacena la descripción del nuevo catálogo a crear cuando se selecciona la opción final del desplegable
const newCategoryDescription = ref('');

// --- INICIALIZACIÓN DE COMPOSABLES ---
// Obtenemos helpers para peticiones asíncronas con feedback automático
const { loading, error, execute } = useApi();
// Obtenemos helpers para resolver la jerarquía de equipos (Planta -> Área -> Sistema -> Equipo)
const { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams } = useEquipmentHierarchies();

// --- ESTADOS DE PAGINACIÓN, FILTROS Y ORDENAMIENTO ---
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });

// --- ESTADOS REACTIVOS PARA MODAL ---
// Controla la visibilidad del modal de creación/edición
const isModalOpen = ref(false);
// Indica si el modal se encuentra en modo edición (true) o creación (false)
const isEditing = ref(false);
// Estado de guardado dentro del modal
const modalSaving = ref(false);

// Control de modal de eliminación
const isDeleteModalOpen = ref(false);
const itemsToDelete = ref([]);
const deleting = ref(false);

// Selecciones auxiliares de jerarquía dentro del modal
const selectedPlantId = ref('');
const selectedAreaId = ref('');
const selectedSystemId = ref('');

// Objeto de formulario reactivo mapeado al modelo CorrectiveTask
const form = ref({
  id: null,
  name: '',
  task_catalog: null,
  equipment: '',
  description: '',
  creation_date: new Date().toISOString().substring(0, 10),
  priority: 2,
  created_by_user: '',
  root_cause: '',
  turno: 'A'
});

// --- PROPIEDADES COMPUTADAS AUXILIARES ---
// Filtra las áreas disponibles en el modal según la planta seleccionada
const filteredAreasOptions = computed(() => {
  if (!selectedPlantId.value) return [];
  return areasOptions.value.filter(a => a.plant === selectedPlantId.value || a.plant?.id === selectedPlantId.value);
});

// Filtra los equipos disponibles en el modal según los selectores de planta/área/sistema
const filteredEquipmentsOptions = computed(() => {
  return equipmentsList.value.filter(eq => {
    // Si hay un área seleccionada, verificar coincidencia de área
    if (selectedAreaId.value && eq.area !== selectedAreaId.value && eq.area?.id !== selectedAreaId.value) {
      return false;
    }
    // Si hay un sistema seleccionado, verificar coincidencia de sistema
    if (selectedSystemId.value && eq.system !== selectedSystemId.value && eq.system?.id !== selectedSystemId.value) {
      return false;
    }
    return true;
  });
});

// Configuración avanzada de tipos de celdas y listas desplegables para ExcelGrid
const columnsConfig = computed(() => {
  return {
    // Columna 1: Categoría de Catálogo (Muestra el campo 'description' de la tabla TaskCatalog)
    1: {
      type: 'select',
      options: taskCatalogList.value.map(cat => ({
        value: cat.id,
        label: cat.description || cat.name || 'Sin Descripción'
      })).sort((a, b) => a.label.localeCompare(b.label))
    },
    // Columnas 3, 4, 5: Planta, Área, Sistema (Solo lectura derivadas de la jerarquía)
    3: { readOnly: true },
    4: { readOnly: true },
    5: { readOnly: true },
    // Columna 6: Equipo Asignado
    6: {
      type: 'select',
      options: equipmentsList.value.map(eq => ({
        value: eq.id,
        label: `${eq.name || 'Equipo sin nombre'}${eq.description ? ' - ' + eq.description : ''}`
      })).sort((a, b) => a.label.localeCompare(b.label))
    },
    // Columna 10: Criticidad / Prioridad
    10: {
      type: 'select',
      options: [
        { value: 1, label: '1 - Alta (Emergencia)' },
        { value: 2, label: '2 - Media (Urgente)' },
        { value: 3, label: '3 - Baja (Programable)' }
      ]
    },
    // Columna 11: Usuario Reportante
    11: {
      type: 'select',
      options: usersList.value.map(u => ({
        value: u.id,
        label: `${u.nombre || ''} ${u.apellido || ''}`.trim() || 'Usuario sin nombre'
      })).sort((a, b) => a.label.localeCompare(b.label))
    },
    // Columna 12: Turno
    12: {
      type: 'select',
      options: [
        { value: 'A', label: 'Turno A' },
        { value: 'B', label: 'Turno B' },
        { value: 'C', label: 'Turno C' },
        { value: 'DN', label: 'Día / Noche (DN)' }
      ]
    }
  };
});

// --- FUNCIONES AUXILIARES DE CARGA DE DATOS ---
// Extrae de forma segura el arreglo de resultados contemplando respuestas paginadas o directas
const extractData = (res) => res.data?.results || res.data || [];

// Carga la lista completa de usuarios registrantes desde la API
const loadUsers = async () => {
  try {
    const res = await api.get('users/', { params: { page_size: 10000 } });
    usersList.value = extractData(res);
  } catch (e) {
    console.error('Error al obtener el listado de usuarios:', e);
  }
};

// Carga la lista completa del catálogo de tareas (TaskCatalog)
const loadTaskCatalogs = async () => {
  try {
    const res = await api.get('taskcatalogs/', { params: { page_size: 10000 } });
    taskCatalogList.value = extractData(res);
  } catch (e) {
    console.error('Error al obtener el catálogo de tareas:', e);
  }
};

// Carga catálogos de Plantas, Áreas y Sistemas para los selectores del modal
const loadHierarchySelectors = async () => {
  try {
    const [pRes, aRes, sRes] = await Promise.all([
      api.get('plants/', { params: { page_size: 10000 } }),
      api.get('areas/', { params: { page_size: 10000 } }),
      api.get('systems/', { params: { page_size: 10000 } })
    ]);
    plantsOptions.value = extractData(pRes);
    areasOptions.value = extractData(aRes);
    systemsOptions.value = extractData(sRes);
  } catch (e) {
    console.error('Error al cargar opciones de jerarquía para el modal:', e);
  }
};

// Carga los datos globales para alimentar los filtros de cabecera en ExcelGrid
const loadFilterData = async () => {
  try {
    const res = await api.get('correctivetasks/', { params: { page_size: 10000 } });
    const results = extractData(res);

    filterData.value = results.map(t => {
      const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
      const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);
      const userId = (t.created_by_user && typeof t.created_by_user === 'object') ? t.created_by_user.id : (t.created_by_user || '');

      return [
        t.id,
        t.task_catalog || '',
        t.name || '',
        plantName,
        areaName,
        systemName,
        eqId,
        t.description || '',
        t.root_cause || '',
        t.creation_date || '',
        t.priority || '',
        userId,
        t.turno || ''
      ];
    });
  } catch (e) {
    console.error('Error al cargar datos para los filtros:', e);
  }
};

// Carga la lista paginada de tareas correctivas aplicando los filtros y el ordenamiento actual
const loadData = async (page = 1) => {
  await execute(async () => {
    let params = { page, page_size: pageSize.value };

    // Definición de índices de jerarquía para la construcción de filtros backend
    const hierarchyIndexes = { plant: '3', area: '4', system: '5', equipment: '6' };
    params = buildFilterParams(params, currentFilters.value, colKeys, hierarchyIndexes);

    // Configurar ordenamiento según la columna seleccionada
    if (currentSort.value.colIndex !== null) {
      const fieldName = colKeys[currentSort.value.colIndex];
      if (fieldName && !fieldName.includes('__')) {
        params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
      }
    }

    // Petición al endpoint de tareas correctivas
    const res = await api.get('correctivetasks/', { params });
    const responseData = res.data;
    let dataArray = [];

    // Verificamos si la respuesta viene paginada por DRF o como arreglo simple
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

    // Guardamos los objetos crudos para resolver la edición al hacer doble clic
    rawTasksList.value = dataArray;

    // Transformamos los objetos JSON recibidos a una matriz 2D para ExcelGrid
    gridData.value = dataArray.map(t => {
      const eqId = (t.equipment && typeof t.equipment === 'object') ? t.equipment.id : (t.equipment || '');
      const { plantName, areaName, systemName } = getEquipmentHierarchyRow(eqId);
      const userId = (t.created_by_user && typeof t.created_by_user === 'object') ? t.created_by_user.id : (t.created_by_user || '');

      return [
        t.id,
        t.task_catalog || '',
        t.name || '',
        plantName,
        areaName,
        systemName,
        eqId,
        t.description || '',
        t.root_cause || '',
        t.creation_date || '',
        t.priority || '',
        userId,
        t.turno || ''
      ];
    });
  }, 'Error al consultar la lista de tareas correctivas desde el servidor.');
};

// Refresca todos los recursos del componente
const refreshAllData = async () => {
  await loadDependencies();
  await loadTaskCatalogs();
  await loadUsers();
  await loadHierarchySelectors();
  await loadData(currentPage.value);
  await loadFilterData();
};

// Cierra cualquier mensaje de error visible
const clearError = () => {
  error.value = null;
};

// --- MANEJADORES DE EVENTOS DE GRILLA (EXCELGRID) ---
const handlePageChange = (p) => loadData(p);
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
const handleFilterChange = (f) => { currentFilters.value = f; loadData(1); };
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// MANEJADOR DE DOBLE CLIC EN FILA DE GRILLA PARA EDICIÓN DIRECTA EN MODAL
const handleRowDblClick = ({ row }) => {
  if (!row || row.length === 0) return;
  const taskId = Number(row[0]);
  if (isNaN(taskId) || !taskId) return;

  // Buscamos el objeto de tarea correspondiente en rawTasksList
  const taskObj = rawTasksList.value.find(t => t.id === taskId);
  if (taskObj) {
    populateFormWithTask(taskObj);
    isModalOpen.value = true;
  }
};

// Guarda cambios directos realizados desde la grilla interactiva (POST para nuevos, PUT para existentes)
const handleSaveFromGrid = async (updatedGrid) => {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

  // Validación de datos antes de enviar la petición al backend
  for (let i = 0; i < updatedGrid.length; i++) {
    const nameVal = updatedGrid[i][2];        // Título / Nombre Corto
    const eqVal = updatedGrid[i][6];          // Equipo Asignado
    const descVal = updatedGrid[i][7];        // Descripción
    const dateVal = updatedGrid[i][9];        // Fecha de Reporte
    const priorityVal = updatedGrid[i][10];    // Criticidad
    const userVal = updatedGrid[i][11];       // Usuario

    if (!nameVal || String(nameVal).trim() === '') {
      alert(`No se puede guardar: El campo "Título / Nombre Corto" está vacío en la fila ${i + 1}.`);
      return;
    }
    if (!eqVal || String(eqVal).trim() === '') {
      alert(`No se puede guardar: Debe seleccionar un "Equipo Asignado" en la fila ${i + 1}.`);
      return;
    }
    if (!descVal || String(descVal).trim() === '') {
      alert(`No se puede guardar: El campo "Descripción" está vacío en la fila ${i + 1}.`);
      return;
    }
    if (!dateVal || !dateRegex.test(String(dateVal).trim())) {
      alert(`No se puede guardar: La "Fecha de Reporte" en la fila ${i + 1} debe tener formato YYYY-MM-DD.`);
      return;
    }
    if (priorityVal === null || priorityVal === undefined || isNaN(Number(priorityVal))) {
      alert(`No se puede guardar: La "Criticidad" en la fila ${i + 1} debe ser un número (1, 2 o 3).`);
      return;
    }
    if (!userVal || String(userVal).trim() === '') {
      alert(`No se puede guardar: Debe seleccionar un "Reportado por" en la fila ${i + 1}.`);
      return;
    }
  }

  try {
    await execute(async () => {
      const promises = updatedGrid.map(row => {
        const payload = {};
        colKeys.forEach((key, idx) => {
          if (key.includes('__')) return; // Ignorar columnas calculadas de la jerarquía
          let val = row[idx];
          if (typeof val === 'string') val = val.trim();
          payload[key] = (val === '' || val === null) ? null : val;
        });

        const id = payload.id;
        const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));

        if (isExisting) {
          return api.put(`correctivetasks/${id}/`, payload);
        } else {
          delete payload.id;
          return api.post('correctivetasks/', payload);
        }
      });

      await Promise.all(promises);
      alert('Tareas correctivas guardadas con éxito.');
      await loadData(currentPage.value);
      await loadFilterData();
    });
  } catch (e) {
    alert('Ocurrió un error al guardar las tareas correctivas. Verifique la validez de los datos.');
  }
};

// Muestra el modal de confirmación antes de eliminar permanentemente registros
const confirmDeleteFromGrid = (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  itemsToDelete.value = idsToDelete;
  isDeleteModalOpen.value = true;
};

// Cierra el modal de confirmación de borrado
const closeDeleteModal = () => {
  isDeleteModalOpen.value = false;
  itemsToDelete.value = [];
};

// Ejecuta la petición DELETE para eliminar los registros marcados
const executeDelete = async () => {
  deleting.value = true;
  try {
    await execute(async () => {
      const promises = itemsToDelete.value.map(id => api.delete(`correctivetasks/${id}/`));
      await Promise.all(promises);
      alert(`${itemsToDelete.value.length} tarea(s) correctiva(s) eliminada(s) correctamente.`);
      closeDeleteModal();
      await loadData(currentPage.value);
      await loadFilterData();
    });
  } catch (e) {
    alert('No se pudo eliminar la tarea correctiva. Es posible que tenga registros históricos o referencias asociadas.');
  } finally {
    deleting.value = false;
  }
};

// --- GESTIÓN DE EDICIÓN Y CREACIÓN EN MODAL ---
// Rellena el formulario modal con los datos de una tarea correctiva existente para su modificación
const populateFormWithTask = (taskObj) => {
  if (!taskObj) return;

  isEditing.value = true;
  newCategoryDescription.value = '';

  const eqId = (taskObj.equipment && typeof taskObj.equipment === 'object') ? taskObj.equipment.id : taskObj.equipment;
  const catalogId = (taskObj.task_catalog && typeof taskObj.task_catalog === 'object') ? taskObj.task_catalog.id : taskObj.task_catalog;
  const userId = (taskObj.created_by_user && typeof taskObj.created_by_user === 'object') ? taskObj.created_by_user.id : taskObj.created_by_user;

  // Sincronizamos los selectores de jerarquía (Planta, Área, Sistema) según el equipo asignado
  const eqObj = equipmentsList.value.find(e => e.id === eqId);
  if (eqObj) {
    const areaId = typeof eqObj.area === 'object' ? eqObj.area.id : eqObj.area;
    selectedAreaId.value = areaId || '';
    const areaObj = areasOptions.value.find(a => a.id === areaId);
    if (areaObj) {
      selectedPlantId.value = typeof areaObj.plant === 'object' ? areaObj.plant.id : areaObj.plant;
    } else {
      selectedPlantId.value = '';
    }
    const sysId = typeof eqObj.system === 'object' ? eqObj.system.id : eqObj.system;
    selectedSystemId.value = sysId || '';
  } else {
    selectedPlantId.value = '';
    selectedAreaId.value = '';
    selectedSystemId.value = '';
  }

  // Asignamos todos los campos del registro al formulario reactivo
  form.value = {
    id: taskObj.id,
    name: taskObj.name || '',
    task_catalog: catalogId || null,
    equipment: eqId || '',
    description: taskObj.description || '',
    creation_date: taskObj.creation_date || new Date().toISOString().substring(0, 10),
    priority: taskObj.priority || 2,
    created_by_user: userId || (usersList.value.length > 0 ? usersList.value[0].id : ''),
    root_cause: taskObj.root_cause || '',
    turno: taskObj.turno || 'A'
  };
};

// Abre el modal configurado exclusivamente en modo CREACIÓN de una nueva tarea
const openCreateModal = () => {
  isEditing.value = false;
  selectedPlantId.value = '';
  selectedAreaId.value = '';
  selectedSystemId.value = '';
  newCategoryDescription.value = '';
  form.value = {
    id: null,
    name: '',
    task_catalog: null,
    equipment: '',
    description: '',
    creation_date: new Date().toISOString().substring(0, 10),
    priority: 2,
    created_by_user: usersList.value.length > 0 ? usersList.value[0].id : '',
    root_cause: '',
    turno: 'A'
  };
  isModalOpen.value = true;
};

// Cierra el modal de creación/edición y resetea estados auxiliares
const closeModal = () => {
  isModalOpen.value = false;
  newCategoryDescription.value = '';
};

// Manejador del cambio de Planta en el modal (resetea el área seleccionada)
const onPlantChange = () => {
  selectedAreaId.value = '';
};

// Manejador del cambio de Área en el modal
const onAreaChange = () => {
  // Ajuste automático si se requiere
};

// Manejador del cambio de Sistema en el modal
const onSystemChange = () => {
  // Ajuste automático si se requiere
};

// Guarda o actualiza los datos desde el formulario modal
const saveTaskFromModal = async () => {
  // Validaciones del formulario modal
  if (!form.value.name || form.value.name.trim() === '') {
    alert('Por favor, ingrese un título o nombre corto para la tarea correctiva.');
    return;
  }
  if (!form.value.equipment) {
    alert('Debe seleccionar un equipo afectado.');
    return;
  }
  if (!form.value.description || form.value.description.trim() === '') {
    alert('Por favor, detalle la descripción del incidente.');
    return;
  }
  if (!form.value.creation_date) {
    alert('Por favor, seleccione la fecha de reporte.');
    return;
  }
  if (!form.value.created_by_user) {
    alert('Debe indicar qué usuario reportó el incidente.');
    return;
  }

  // Validación de creación automática de registro en el catálogo si se eligió la opción final
  if (form.value.task_catalog === '__NEW_CATALOG__') {
    if (!newCategoryDescription.value || newCategoryDescription.value.trim() === '') {
      alert('Por favor, ingrese la descripción para el nuevo registro que se creará en el catálogo.');
      return;
    }
  }

  modalSaving.value = true;
  try {
    await execute(async () => {
      let finalCatalogId = form.value.task_catalog;

      // SI SE SELECCIONÓ CREAR UN NUEVO REGISTRO EN EL CATÁLOGO DESDE EL SELECTOR:
      if (form.value.task_catalog === '__NEW_CATALOG__') {
        const catPayload = {
          name: form.value.name.trim(),
          description: newCategoryDescription.value.trim()
        };

        const catRes = await api.post('taskcatalogs/', catPayload);
        const newCat = catRes.data;
        finalCatalogId = newCat.id;
        await loadTaskCatalogs();
      }

      // CONSTRUCCIÓN DEL PAYLOAD FINAL PARA CORRECTIVETASK
      const payload = {
        name: form.value.name.trim(),
        task_catalog: finalCatalogId || null,
        equipment: form.value.equipment,
        description: form.value.description.trim(),
        creation_date: form.value.creation_date,
        priority: Number(form.value.priority),
        created_by_user: form.value.created_by_user,
        root_cause: form.value.root_cause ? form.value.root_cause.trim() : null,
        turno: form.value.turno || null
      };

      if (isEditing.value && form.value.id) {
        // Petición PUT para actualizar el registro existente
        await api.put(`correctivetasks/${form.value.id}/`, payload);
        alert(`Tarea correctiva #${form.value.id} actualizada correctamente.`);
      } else {
        // Petición POST para registrar una nueva tarea correctiva
        await api.post('correctivetasks/', payload);
        alert('Nueva tarea correctiva registrada con éxito.');
      }

      closeModal();
      await loadData(currentPage.value);
      await loadFilterData();
    });
  } catch (e) {
    alert('Error al procesar la solicitud en el servidor. Verifique los datos o si el nombre del catálogo ya existe.');
  } finally {
    modalSaving.value = false;
  }
};

// --- CICLO DE VIDA DEL COMPONENTE DE VUE ---
onMounted(async () => {
  // Carga inicial secuencial de dependencias y catálogos
  await loadDependencies();
  await loadTaskCatalogs();
  await loadUsers();
  await loadHierarchySelectors();
  await loadData();
  await loadFilterData();
});
</script>

<style scoped>
/* Estilos generales del contenedor de la vista */
.corrective-tasks-view {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px;
}

/* Barra superior de título y botones */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #ffffff;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.view-title {
  margin: 0;
  font-size: 1.25rem;
  color: #1e293b;
  font-weight: 700;
}

.button-group {
  display: flex;
  gap: 10px;
}

/* Estilos de botones estándar */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s, transform 0.1s;
}

.btn:active {
  transform: scale(0.98);
}

.btn-primary {
  background-color: #2563eb;
  color: #ffffff;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-secondary {
  background-color: #64748b;
  color: #ffffff;
}

.btn-secondary:hover {
  background-color: #475569;
}

.btn-success {
  background-color: #16a34a;
  color: #ffffff;
}

.btn-success:hover {
  background-color: #15803d;
}

.btn-danger {
  background-color: #dc2626;
  color: #ffffff;
}

.btn-danger:hover {
  background-color: #b91c1c;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #64748b;
}

.btn-close:hover {
  color: #0f172a;
}

/* Capa de carga translúcida */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #1e293b;
  z-index: 500;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid #cbd5e1;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Banner de error */
.error-banner {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 10px 16px;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-close-error {
  background: none;
  border: none;
  color: #991b1b;
  font-weight: bold;
  cursor: pointer;
}

/* MODALES Y CAPAS DIÁLOGO */
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
  max-width: 750px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-small {
  max-width: 450px;
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

.header-danger {
  background-color: #fef2f2;
  border-bottom-color: #fecaca;
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
}

.modal-footer {
  padding: 16px 24px;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* ESTILOS DE FORMULARIO MODULAR */
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

.form-control {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  background-color: #ffffff;
}

.form-control:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

textarea.form-control {
  resize: vertical;
}

/* ESTILO RESALTADO PARA CAMPO DE NUEVA CATEGORÍA DE CATÁLOGO */
.new-cat-input-container {
  background-color: #f0fdf4;
  border: 1px dashed #16a34a;
  border-radius: 8px;
  padding: 12px;
}

.highlight-input {
  border-color: #16a34a !important;
}

.help-text {
  font-size: 0.78rem;
  color: #15803d;
}

.warning-box {
  background-color: #fffbe6;
  border: 1px solid #ffe58f;
  padding: 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #d48806;
  margin-top: 12px;
}
</style>
