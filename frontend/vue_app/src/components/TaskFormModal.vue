<template>
  <!-- Contenedor backdrop que cubre toda la pantalla cuando el modal está activo -->
  <div v-if="isOpen" class="modal-backdrop" @click.self="handleClose">
    <!-- Ventana flotante (tarjeta principal) que contiene el formulario -->
    <div class="modal-card" role="dialog" aria-modal="true">
      
      <!-- Cabecera del modal: muestra el título dinámico y el botón de cerrar -->
      <header class="modal-header">
        <!-- Título que cambia según si estamos creando o editando una tarea -->
        <h2 class="modal-title">
          {{ isEditing ? 'Editar Plantilla de Tarea' : 'Nueva Plantilla de Tarea' }}
        </h2>
        <!-- Botón para cerrar el modal mediante una cruz (X) -->
        <button type="button" class="btn-icon-close" title="Cerrar ventana" @click="handleClose">
          &times;
        </button>
      </header>

      <!-- Formulario principal con prevención del submit estándar del navegador -->
      <form @submit.prevent="handleSubmit(false)" class="modal-form">
        
        <!-- ============================================================ -->
        <!-- SECCIÓN 1: JERARQUÍA OPERACIONAL Y ASIGNACIÓN DE EQUIPO       -->
        <!-- ============================================================ -->
        <fieldset class="form-section">
          <!-- Título visible del primer bloque organizativo -->
          <legend class="section-legend">1. Ubicación Operacional y Activo</legend>
          
          <!-- Fila con dos columnas: Planta y Área -->
          <div class="form-row two-cols">
            <!-- Grupo de entrada: Selector de Planta -->
            <div class="form-group">
              <!-- Etiqueta descriptiva para el selector de Planta -->
              <label for="select-planta">Planta Operativa</label>
              <!-- Selector reactivo que filtra las áreas al cambiar -->
              <select id="select-planta" v-model="selectedPlantId" @change="handlePlantChange" class="form-control">
                <!-- Opción neutra inicial -->
                <option value="">-- Todas las Plantas --</option>
                <!-- Iteramos sobre todas las plantas disponibles -->
                <option v-for="plant in plantsList" :key="plant.id" :value="plant.id">
                  {{ plant.name }} ({{ plant.tag }})
                </option>
              </select>
            </div>

            <!-- Grupo de entrada: Selector de Área -->
            <div class="form-group">
              <!-- Etiqueta descriptiva para el selector de Área -->
              <label for="select-area">Área Funcional</label>
              <!-- Selector reactivo que se activa según la planta seleccionada -->
              <select id="select-area" v-model="selectedAreaId" @change="handleAreaChange" class="form-control">
                <!-- Opción neutra inicial -->
                <option value="">-- Todas las Áreas --</option>
                <!-- Iteramos sobre las áreas filtradas por la planta -->
                <option v-for="area in availableAreas" :key="area.id" :value="area.id">
                  {{ area.name }}
                </option>
              </select>
            </div>
          </div>

          <!-- Fila con dos columnas: Sistema y Equipo Asignado -->
          <div class="form-row two-cols">
            <!-- Grupo de entrada: Selector de Sistema -->
            <div class="form-group">
              <!-- Etiqueta descriptiva para el selector de Sistema -->
              <label for="select-sistema">Sistema de Proceso</label>
              <!-- Selector reactivo de sistemas técnicos -->
              <select id="select-sistema" v-model="selectedSystemId" @change="handleSystemChange" class="form-control">
                <!-- Opción neutra inicial -->
                <option value="">-- Todos los Sistemas --</option>
                <!-- Iteramos sobre la lista completa de sistemas -->
                <option v-for="sys in systemsList" :key="sys.id" :value="sys.id">
                  {{ sys.name }}
                </option>
              </select>
            </div>

            <!-- Grupo de entrada: Selector final de Equipo -->
            <div class="form-group">
              <!-- Etiqueta con indicador de campo obligatorio -->
              <label for="select-equipo">Equipo Asignado <span class="required-asterisk">*</span></label>
              <!-- Selector reactivo del equipo al cual se asignará la plantilla -->
              <select id="select-equipo" v-model="formData.equipment" required class="form-control highlight-select">
                <!-- Opción por defecto cuando no se ha elegido equipo -->
                <option value="" disabled>-- Selecciona un equipo ({{ availableEquipments.length }} disponibles) --</option>
                <!-- Iteramos sobre los equipos filtrados por la jerarquía superior -->
                <option v-for="eq in availableEquipments" :key="eq.id" :value="eq.id">
                  {{ eq.tag ? `[${eq.tag}] ` : '' }}{{ eq.name }} {{ eq.description ? `- ${eq.description}` : '' }}
                </option>
              </select>
            </div>
          </div>
        </fieldset>

        <!-- ============================================================ -->
        <!-- SECCIÓN 2: DEFINICIÓN DE LA TAREA Y PROCEDIMIENTO PETS       -->
        <!-- ============================================================ -->
        <fieldset class="form-section">
          <!-- Título visible del segundo bloque organizativo -->
          <legend class="section-legend">2. Estandarización y Procedimiento</legend>

          <!-- Grupo para la selección del Catálogo de Tareas -->
          <div class="form-group">
            <!-- Etiqueta del catálogo -->
            <label for="select-catalogo">Tipo de Tarea (Catálogo Maestro) <span class="required-asterisk">*</span></label>
            <!-- Contenedor horizontal que permite combinar el select con un botón para crear nueva tarea -->
            <div class="input-action-wrapper">
              <!-- Selector de tareas maestras normalizadas -->
              <select id="select-catalogo" v-model="formData.task_catalog" required class="form-control flex-grow">
                <!-- Opción vacía inicial -->
                <option value="" disabled>-- Selecciona del catálogo normalizado --</option>
                <!-- Iteramos sobre los ítems del catálogo listando la descripción en vez del nombre -->
                <option v-for="cat in sortedCatalogs" :key="cat.id" :value="cat.id">
                  {{ cat.description || cat.name }}
                </option>
              </select>
              <!-- Botón que activa el subformulario para registrar una nueva tarea en el catálogo al vuelo -->
              <button type="button" class="btn btn-outline" @click="showNewCatalogForm = !showNewCatalogForm">
                {{ showNewCatalogForm ? 'Cancelar Nuevo' : '+ Nuevo al Catálogo' }}
              </button>
            </div>
          </div>

          <!-- Subformulario desplegable para registrar nuevo catálogo de tarea -->
          <div v-if="showNewCatalogForm" class="subform-card">
            <!-- Subtítulo informativo -->
            <div class="subform-header">Registrar Nuevo Nombre en el Catálogo</div>
            <!-- Input para el nuevo nombre -->
            <input
              type="text"
              v-model="newCatalogName"
              placeholder="Ej: Inspección Termográfica de Tablero"
              class="form-control mb-2"
            />
            <!-- Input para la descripción por defecto -->
            <input
              type="text"
              v-model="newCatalogDescription"
              placeholder="Descripción general (opcional)..."
              class="form-control mb-2"
            />
            <!-- Botón para guardar el nuevo catálogo en el backend -->
            <button
              type="button"
              class="btn btn-sm btn-primary"
              :disabled="!newCatalogName.trim() || creatingCatalog"
              @click="handleCreateCatalog"
            >
              {{ creatingCatalog ? 'Registrando...' : 'Confirmar e Insertar al Catálogo' }}
            </button>
          </div>

          <!-- Grupo de entrada: Descripción detallada específica de esta plantilla -->
          <div class="form-group">
            <!-- Etiqueta del campo de descripción -->
            <label for="tarea-descripcion">Descripción Específica del Trabajo</label>
            <!-- Textarea para notas o detalles específicos de la tarea -->
            <textarea
              id="tarea-descripcion"
              v-model="formData.description"
              rows="2"
              placeholder="Describa el alcance específico de este mantenimiento preventivo..."
              class="form-control"
            ></textarea>
          </div>

          <!-- Grupo de entrada: Enlace al documento PETS en SharePoint -->
          <div class="form-group">
            <!-- Etiqueta informativa del enlace -->
            <label for="tarea-procedure">Procedimiento Escrito de Trabajo Seguro (Enlace PETS / SharePoint)</label>
            <!-- Contenedor con enlace y botón de prueba rápida -->
            <div class="input-action-wrapper">
              <!-- Campo de texto tipo URL -->
              <input
                id="tarea-procedure"
                type="url"
                v-model="formData.procedure"
                placeholder="https://americasmining-my.sharepoint.com/:w:/r/..."
                class="form-control flex-grow"
              />
              <!-- Botón que abre el enlace en una pestaña nueva si es válido -->
              <a
                v-if="formData.procedure"
                :href="formData.procedure"
                target="_blank"
                rel="noopener noreferrer"
                class="btn btn-outline"
                title="Abrir y verificar procedimiento en nueva pestaña"
              >
                🔗 Probar Enlace
              </a>
            </div>
          </div>
        </fieldset>

        <!-- ============================================================ -->
        <!-- SECCIÓN 3: PARÁMETROS OPERACIONALES Y PLANIFICACIÓN          -->
        <!-- ============================================================ -->
        <fieldset class="form-section">
          <!-- Título visible del tercer bloque organizativo -->
          <legend class="section-legend">3. Frecuencia y Planificación de Recursos</legend>

          <!-- Grupo de entrada: Frecuencia con botones tipo Chips -->
          <div class="form-group">
            <!-- Etiqueta de la frecuencia -->
            <label>Frecuencia de Repetición</label>
            <!-- Contenedor de botones seleccionables para frecuencias típicas de planta -->
            <div class="chips-selector">
              <!-- Botón para cada frecuencia predeterminada -->
              <button
                type="button"
                v-for="preset in frequencyPresets"
                :key="preset.value"
                class="chip-button"
                :class="{ active: formData.frequency === preset.value && !isCustomFrequency }"
                @click="selectFrequencyPreset(preset.value)"
              >
                {{ preset.label }}
              </button>
              <!-- Botón para habilitar ingreso manual en días -->
              <button
                type="button"
                class="chip-button"
                :class="{ active: isCustomFrequency }"
                @click="enableCustomFrequency"
              >
                Personalizado (días)
              </button>
            </div>

            <!-- Input que aparece solo si el usuario seleccionó frecuencia personalizada -->
            <div v-if="isCustomFrequency" class="custom-freq-wrapper">
              <!-- Entrada numérica para cantidad de días -->
              <input
                type="number"
                v-model="customFrequencyDays"
                min="1"
                placeholder="Ingrese días (ej: 45)"
                class="form-control custom-freq-input"
                @input="applyCustomFrequency"
              />
              <!-- Sufijo explicativo -->
              <span class="text-muted">días entre cada ejecución</span>
            </div>
          </div>

          <!-- Fila con tres columnas: Duración, Trabajadores y Turno -->
          <div class="form-row three-cols">
            
            <!-- Entrada de Duración en horas -->
            <div class="form-group">
              <!-- Etiqueta de duración -->
              <label for="input-duracion">Duración Estimada (Horas)</label>
              <!-- Contenedor con controles numéricos de incremento y decremento -->
              <div class="number-stepper">
                <!-- Botón para restar media hora -->
                <button type="button" class="btn-stepper" @click="stepDuration(-0.5)">-</button>
                <!-- Input numérico directo -->
                <input
                  id="input-duracion"
                  type="number"
                  v-model.number="formData.duration"
                  min="0.5"
                  step="0.5"
                  class="form-control text-center"
                />
                <!-- Botón para sumar media hora -->
                <button type="button" class="btn-stepper" @click="stepDuration(0.5)">+</button>
              </div>
            </div>

            <!-- Entrada de Cantidad de Trabajadores requeridos -->
            <div class="form-group">
              <!-- Etiqueta de trabajadores -->
              <label for="input-workers">Personal Requerido</label>
              <!-- Contenedor con controles numéricos de incremento y decremento -->
              <div class="number-stepper">
                <!-- Botón para restar una persona -->
                <button type="button" class="btn-stepper" @click="stepWorkers(-1)">-</button>
                <!-- Input numérico directo -->
                <input
                  id="input-workers"
                  type="number"
                  v-model.number="formData.workers"
                  min="1"
                  step="1"
                  class="form-control text-center"
                />
                <!-- Botón para sumar una persona -->
                <button type="button" class="btn-stepper" @click="stepWorkers(1)">+</button>
              </div>
            </div>

            <!-- Entrada de Turno asignado -->
            <div class="form-group">
              <!-- Etiqueta del turno -->
              <label>Turno Asignado</label>
              <!-- Grupo de botones segmentados para seleccionar turno de trabajo -->
              <div class="segmented-control">
                <!-- Opción Turno A -->
                <label class="segment-option" :class="{ active: formData.turn === 'A' }">
                  <input type="radio" v-model="formData.turn" value="A" class="hidden-radio" />
                  Turno A
                </label>
                <!-- Opción Turno B -->
                <label class="segment-option" :class="{ active: formData.turn === 'B' }">
                  <input type="radio" v-model="formData.turn" value="B" class="hidden-radio" />
                  Turno B
                </label>
                <!-- Opción Ambos turnos (rotativo) -->
                <label class="segment-option" :class="{ active: formData.turn === 'AB' }">
                  <input type="radio" v-model="formData.turn" value="AB" class="hidden-radio" />
                  Ambos (AB)
                </label>
              </div>
            </div>

          </div>

          <!-- Fila para la Fecha de Inicio de la primera ejecución -->
          <div class="form-row">
            <!-- Grupo de entrada: Fecha de Inicio -->
            <div class="form-group">
              <!-- Etiqueta de fecha -->
              <label for="input-start-date">Fecha de Inicio de Planificación</label>
              <!-- Selector nativo de fecha con formato estándar ISO -->
              <input
                id="input-start-date"
                type="date"
                v-model="formData.start_date"
                class="form-control"
              />
            </div>
          </div>

        </fieldset>

        <!-- Mensaje de error visible si la validación interna o del backend falla -->
        <div v-if="validationError" class="alert-error">
          {{ validationError }}
        </div>

        <!-- Barra inferior con botones de acción -->
        <footer class="modal-footer">
          <!-- Botón secundario para descartar cambios y cerrar -->
          <button type="button" class="btn btn-secondary" @click="handleClose">
            Cancelar
          </button>
          
          <!-- Botón adicional para flujo ágil de creación continua (solo en modo creación) -->
          <button
            v-if="!isEditing"
            type="button"
            class="btn btn-outline"
            :disabled="submitting"
            @click="handleSubmit(true)"
          >
            Guardar y Crear Otra
          </button>

          <!-- Botón principal de guardado -->
          <button type="submit" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? 'Guardando...' : (isEditing ? 'Actualizar Tarea' : 'Crear Tarea') }}
          </button>
        </footer>

      </form>
    </div>
  </div>
</template>

<script setup>
// Importamos funciones reactivas esenciales del core de Vue 3
import { ref, reactive, computed, watch } from 'vue';
// Importamos el cliente HTTP para peticiones al API REST de Django
import { api } from '../api';

// Definición explícita de las propiedades (props) recibidas por este componente
const props = defineProps({
  // Controla si el modal está visible en pantalla
  isOpen: {
    type: Boolean,
    default: false
  },
  // Objeto con la tarea que se desea editar (nulo si es creación nueva)
  taskData: {
    type: Object,
    default: null
  },
  // Lista de ítems del catálogo de tareas maestros
  catalogs: {
    type: Array,
    default: () => []
  },
  // Lista de plantas disponibles para la jerarquía
  plantsList: {
    type: Array,
    default: () => []
  },
  // Lista de áreas disponibles para la jerarquía
  areasList: {
    type: Array,
    default: () => []
  },
  // Lista de sistemas técnicos para la jerarquía
  systemsList: {
    type: Array,
    default: () => []
  },
  // Lista de equipos de planta disponibles
  equipmentsList: {
    type: Array,
    default: () => []
  }
});

// Definición explícita de eventos emitidos hacia el componente padre
const emit = defineEmits(['close', 'saved', 'catalogCreated']);

// Variable booleana que indica si el modal está en modo edición o creación
const isEditing = computed(() => Boolean(props.taskData && props.taskData.id));

// Estados reactivos para la navegación en cascada de la jerarquía
const selectedPlantId = ref('');
const selectedAreaId = ref('');
const selectedSystemId = ref('');

// Estados para la creación rápida de nuevos catálogos dentro del modal
const showNewCatalogForm = ref(false);
const newCatalogName = ref('');
const newCatalogDescription = ref('');
const creatingCatalog = ref(false);

// Estados para manejo de frecuencia personalizada
const isCustomFrequency = ref(false);
const customFrequencyDays = ref('');

// Estados para el envío del formulario y feedback de validación
const submitting = ref(false);
const validationError = ref('');

// Estado reactivo principal que almacena los valores a enviar al endpoint
const formData = reactive({
  id: null,
  task_catalog: '',
  equipment: '',
  duration: 1,
  workers: 1,
  frequency: '35',
  turn: 'A',
  start_date: new Date().toISOString().split('T')[0],
  description: '',
  procedure: ''
});

// Lista declarativa de frecuencias estándares utilizadas en la planta
const frequencyPresets = [
  { label: 'Diario (1d)', value: '1' },
  { label: 'Semanal (7d)', value: '7' },
  { label: 'Quincenal (14d)', value: '14' },
  { label: 'Mensual (28d)', value: '28' },
  { label: '5 Semanas (35d)', value: '35' },
  { label: 'Bimestral (70d)', value: '70' },
  { label: 'Trimestral (105d)', value: '105' },
  { label: 'Semestral (210d)', value: '210' },
  { label: 'Parada Planta (999d)', value: '999' }
];

// Computed: Ordena el catálogo alfabéticamente por su descripción para facilitar la lectura al usuario
const sortedCatalogs = computed(() => {
  return [...props.catalogs].sort((a, b) => {
    const textA = a.description || a.name || '';
    const textB = b.description || b.name || '';
    return textA.localeCompare(textB);
  });
});

// Computed: Filtra las áreas basándose en la planta seleccionada
const availableAreas = computed(() => {
  if (!selectedPlantId.value) {
    return props.areasList;
  }
  return props.areasList.filter(area => {
    return Number(area.plant_id || area.plant) === Number(selectedPlantId.value);
  });
});

// Computed: Filtra los equipos basándose en el área y sistema seleccionados
const availableEquipments = computed(() => {
  return props.equipmentsList.filter(eq => {
    // Si se seleccionó una planta pero no un área específica, verificar que el área pertenezca a la planta
    if (selectedPlantId.value && !selectedAreaId.value) {
      const parentArea = props.areasList.find(a => a.id === eq.area || a.id === eq.area_id);
      if (!parentArea || Number(parentArea.plant || parentArea.plant_id) !== Number(selectedPlantId.value)) {
        return false;
      }
    }
    // Filtrar por área si se seleccionó una
    if (selectedAreaId.value && Number(eq.area || eq.area_id) !== Number(selectedAreaId.value)) {
      return false;
    }
    // Filtrar por sistema si se seleccionó uno
    if (selectedSystemId.value && Number(eq.system || eq.system_id) !== Number(selectedSystemId.value)) {
      return false;
    }
    return true;
  });
});

// Manejador del cambio de planta: limpia el área seleccionada y revalida equipo
const handlePlantChange = () => {
  selectedAreaId.value = '';
  validateEquipmentSelection();
};

// Manejador del cambio de área: revalida equipo
const handleAreaChange = () => {
  validateEquipmentSelection();
};

// Manejador del cambio de sistema: revalida equipo
const handleSystemChange = () => {
  validateEquipmentSelection();
};

// Revalida si el equipo seleccionado sigue existiendo en el nuevo subconjunto filtrado
const validateEquipmentSelection = () => {
  if (!formData.equipment) return;
  const exists = availableEquipments.value.some(eq => eq.id === formData.equipment);
  if (!exists) {
    formData.equipment = '';
  }
};

// Selección de un preset de frecuencia estándar
const selectFrequencyPreset = (presetVal) => {
  isCustomFrequency.value = false;
  formData.frequency = presetVal;
};

// Habilitación de la frecuencia personalizada
const enableCustomFrequency = () => {
  isCustomFrequency.value = true;
  customFrequencyDays.value = formData.frequency || '';
};

// Aplicación del valor numérico personalizado al campo formData.frequency
const applyCustomFrequency = () => {
  formData.frequency = String(customFrequencyDays.value || '');
};

// Incremento / decremento seguro de la duración
const stepDuration = (delta) => {
  const current = Number(formData.duration) || 0;
  const next = Math.max(0.5, current + delta);
  formData.duration = next;
};

// Incremento / decremento seguro del número de trabajadores
const stepWorkers = (delta) => {
  const current = Number(formData.workers) || 1;
  const next = Math.max(1, current + delta);
  formData.workers = next;
};

// Registro de nuevo catálogo de tarea al vuelo
const handleCreateCatalog = async () => {
  if (!newCatalogName.value.trim()) return;
  creatingCatalog.value = true;
  try {
    const payload = {
      name: newCatalogName.value.trim(),
      description: newCatalogDescription.value.trim() || null
    };
    const res = await api.post('taskcatalogs/', payload);
    const created = res.data;
    emit('catalogCreated', created);
    formData.task_catalog = created.id;
    newCatalogName.value = '';
    newCatalogDescription.value = '';
    showNewCatalogForm.value = false;
  } catch (err) {
    console.error('Error al crear catálogo de tarea:', err);
    alert('No se pudo registrar la nueva tarea en el catálogo.');
  } finally {
    creatingCatalog.value = false;
  }
};

// Sincroniza los datos cuando se abre el modal o cambia la propiedad taskData
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      validationError.value = '';
      showNewCatalogForm.value = false;

      if (props.taskData) {
        // Modo Edición: cargamos datos existentes
        formData.id = props.taskData.id || null;
        formData.task_catalog = props.taskData.task_catalog || '';
        formData.equipment = props.taskData.equipment || '';
        formData.duration = props.taskData.duration ?? 1;
        formData.workers = props.taskData.workers ?? 1;
        formData.frequency = String(props.taskData.frequency ?? '35');
        formData.turn = props.taskData.turn || 'A';
        formData.start_date = props.taskData.start_date || new Date().toISOString().split('T')[0];
        formData.description = props.taskData.description || '';
        formData.procedure = props.taskData.procedure || '';

        // Detección de frecuencia personalizada vs preset
        const matchedPreset = frequencyPresets.find(p => p.value === formData.frequency);
        if (!matchedPreset && formData.frequency) {
          isCustomFrequency.value = true;
          customFrequencyDays.value = formData.frequency;
        } else {
          isCustomFrequency.value = false;
        }

        // Resolución inversa de jerarquía a partir del equipo existente
        if (formData.equipment) {
          const eqObj = props.equipmentsList.find(e => e.id === formData.equipment);
          if (eqObj) {
            selectedAreaId.value = eqObj.area || eqObj.area_id || '';
            selectedSystemId.value = eqObj.system || eqObj.system_id || '';
            const areaObj = props.areasList.find(a => a.id === selectedAreaId.value);
            if (areaObj) {
              selectedPlantId.value = areaObj.plant || areaObj.plant_id || '';
            }
          }
        }
      } else {
        // Modo Creación: limpiamos el formulario con valores por defecto
        formData.id = null;
        formData.task_catalog = '';
        formData.equipment = '';
        formData.duration = 1;
        formData.workers = 1;
        formData.frequency = '35';
        formData.turn = 'A';
        formData.start_date = new Date().toISOString().split('T')[0];
        formData.description = '';
        formData.procedure = '';
        isCustomFrequency.value = false;
        customFrequencyDays.value = '';
        selectedPlantId.value = '';
        selectedAreaId.value = '';
        selectedSystemId.value = '';
      }
    }
  },
  { immediate: true }
);

// Manejador del cierre de ventana
const handleClose = () => {
  emit('close');
};

// Manejador de envío y persistencia de la tarea
const handleSubmit = async (createAnother = false) => {
  validationError.value = '';

  // Validaciones obligatorias explícitas
  if (!formData.task_catalog) {
    validationError.value = 'Debe seleccionar un Tipo de Tarea del catálogo.';
    return;
  }
  if (!formData.equipment) {
    validationError.value = 'Debe seleccionar un Equipo asignado.';
    return;
  }

  submitting.value = true;
  try {
    // Sanitización del payload explícito
    const payload = {
      task_catalog: Number(formData.task_catalog),
      equipment: Number(formData.equipment),
      duration: formData.duration ? Number(formData.duration) : null,
      workers: formData.workers ? Number(formData.workers) : null,
      frequency: formData.frequency ? String(formData.frequency) : null,
      turn: formData.turn || null,
      start_date: formData.start_date || null,
      description: formData.description?.trim() || null,
      procedure: formData.procedure?.trim() || null
    };

    let savedTask;
    if (isEditing.value && formData.id) {
      // Petición PUT para actualizar tarea existente
      const res = await api.put(`tasks/${formData.id}/`, payload);
      savedTask = res.data;
    } else {
      // Petición POST para registrar nueva plantilla de tarea
      const res = await api.post('tasks/', payload);
      savedTask = res.data;
    }

    emit('saved', savedTask);

    if (createAnother) {
      // Si el usuario eligió "Guardar y Crear Otra", mantenemos la jerarquía pero limpiamos campos de tarea
      formData.task_catalog = '';
      formData.description = '';
      formData.procedure = '';
      validationError.value = '';
      alert('Tarea guardada. Puede continuar agregando otra tarea para el mismo equipo o zona.');
    } else {
      handleClose();
    }
  } catch (err) {
    console.error('Error al guardar tarea:', err);
    validationError.value = 'Error al comunicarse con el servidor. Verifique los datos ingresados.';
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
/* Fondo oscurecido con desenfoque suave para enfocar la atención en el modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 1rem;
  backdrop-filter: blur(3px);
}

/* Tarjeta principal con bordes redondeados y sombra elevada */
.modal-card {
  background-color: #ffffff;
  width: 100%;
  max-width: 780px;
  max-height: 92vh;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: fadeInModal 0.2s ease-out;
}

/* Animación de entrada suave */
@keyframes fadeInModal {
  from { opacity: 0; transform: scale(0.97); }
  to { opacity: 1; transform: scale(1); }
}

/* Cabecera del modal */
.modal-header {
  padding: 1.25rem 1.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  background-color: #f8fafc;
}

/* Título de la cabecera */
.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
}

/* Botón icono de cierre */
.btn-icon-close {
  background: transparent;
  border: none;
  font-size: 1.75rem;
  line-height: 1;
  color: #64748b;
  cursor: pointer;
  padding: 0;
}
.btn-icon-close:hover {
  color: #0f172a;
}

/* Cuerpo con scroll independiente */
.modal-form {
  overflow-y: auto;
  padding: 1.25rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Agrupaciones temáticas de campos */
.form-section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
  margin: 0;
  background-color: #ffffff;
}

/* Leyenda de cada agrupación */
.section-legend {
  font-size: 0.875rem;
  font-weight: 700;
  color: #3b82f6;
  padding: 0 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Distribución en filas */
.form-row {
  display: grid;
  gap: 1rem;
  margin-top: 0.75rem;
}
.two-cols {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.three-cols {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

/* Grupo individual de etiqueta e input */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.form-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
}

/* Asterisco rojo para campos obligatorios */
.required-asterisk {
  color: #ef4444;
  font-weight: 700;
}

/* Estilo unificado para inputs y selects */
.form-control {
  width: 100%;
  padding: 0.55rem 0.75rem;
  font-size: 0.875rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background-color: #ffffff;
  color: #1e293b;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}
.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}
.highlight-select {
  border-color: #93c5fd;
  background-color: #f0fdf4;
}

/* Contenedor horizontal que acopla input con botón adyacente */
.input-action-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.flex-grow {
  flex-grow: 1;
}

/* Tarjeta secundaria para alta de nuevo catálogo */
.subform-card {
  margin-top: 0.5rem;
  padding: 0.85rem;
  background-color: #eff6ff;
  border: 1px dashed #3b82f6;
  border-radius: 6px;
}
.subform-header {
  font-size: 0.8rem;
  font-weight: 700;
  color: #1d4ed8;
  margin-bottom: 0.5rem;
}
.mb-2 {
  margin-bottom: 0.5rem;
}

/* Chips de frecuencia */
.chips-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.25rem;
}
.chip-button {
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid #cbd5e1;
  background-color: #f8fafc;
  color: #475569;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.chip-button:hover {
  background-color: #e2e8f0;
  color: #0f172a;
}
.chip-button.active {
  background-color: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
  font-weight: 600;
}

/* Frecuencia manual */
.custom-freq-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.custom-freq-input {
  width: 140px;
}
.text-muted {
  font-size: 0.8rem;
  color: #64748b;
}

/* Stepper numérico con botones + y - */
.number-stepper {
  display: flex;
  align-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
}
.number-stepper input {
  border: none;
  border-left: 1px solid #cbd5e1;
  border-right: 1px solid #cbd5e1;
  border-radius: 0;
}
.text-center {
  text-align: center;
}
.btn-stepper {
  background-color: #f1f5f9;
  border: none;
  width: 38px;
  height: 38px;
  font-size: 1.1rem;
  font-weight: bold;
  color: #334155;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-stepper:hover {
  background-color: #e2e8f0;
}

/* Segmented control para selección de turno */
.segmented-control {
  display: flex;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
}
.segment-option {
  flex: 1;
  text-align: center;
  padding: 0.55rem 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  background-color: #f8fafc;
  cursor: pointer;
  border-right: 1px solid #cbd5e1;
}
.segment-option:last-child {
  border-right: none;
}
.segment-option.active {
  background-color: #0284c7;
  color: #ffffff;
}
.hidden-radio {
  display: none;
}

/* Alerta de error */
.alert-error {
  background-color: #fef2f2;
  border: 1px solid #f87171;
  color: #b91c1c;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
}

/* Barra de acciones inferior */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.75rem;
  background-color: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

/* Botones estándar */
.btn {
  padding: 0.55rem 1.1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s, transform 0.05s;
  border: 1px solid transparent;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.btn:active {
  transform: translateY(1px);
}
.btn-primary {
  background-color: #2563eb;
  color: #ffffff;
}
.btn-primary:hover {
  background-color: #1d4ed8;
}
.btn-secondary {
  background-color: #e2e8f0;
  color: #334155;
}
.btn-secondary:hover {
  background-color: #cbd5e1;
}
.btn-outline {
  background-color: #ffffff;
  border-color: #cbd5e1;
  color: #334155;
}
.btn-outline:hover {
  background-color: #f1f5f9;
  border-color: #94a3b8;
}
.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.75rem;
}
</style>
