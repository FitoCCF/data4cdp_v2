<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="handleClose">
    <div class="modal-card" role="dialog" aria-modal="true">
      <!-- Cabecera del modal -->
      <header class="modal-header">
        <h2 class="modal-title">
          {{ isEditing ? 'Editar Equipo' : 'Nuevo Equipo' }}
        </h2>
        <button type="button" class="btn-icon-close" title="Cerrar" @click="handleClose">&times;</button>
      </header>

      <!-- Formulario de creación/edición -->
      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="modal-body">
          <!-- 1. Identificación del Equipo -->
          <fieldset class="form-section">
            <legend class="section-legend">1. Identificación del Equipo</legend>

            <div class="form-row two-cols">
              <div class="form-group">
                <label for="eq-tag">
                  TAG / Código Técnico
                  <span class="char-count">({{ formData.tag.length }}/50)</span>
                </label>
                <input
                  id="eq-tag"
                  type="text"
                  v-model="formData.tag"
                  maxlength="50"
                  placeholder="Ej: SAG-01, PUMP-204"
                  class="form-control"
                />
              </div>

              <div class="form-group">
                <label for="eq-name">
                  Nombre del Equipo <span class="required-asterisk">*</span>
                  <span class="char-count">({{ formData.name.length }}/100)</span>
                </label>
                <input
                  id="eq-name"
                  type="text"
                  v-model="formData.name"
                  maxlength="100"
                  required
                  placeholder="Ej: Molino SAG 01"
                  class="form-control"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="eq-desc">Descripción Operativa</label>
              <textarea
                id="eq-desc"
                v-model="formData.description"
                rows="2"
                placeholder="Detalle técnico, capacidad o función del equipo..."
                class="form-control"
              ></textarea>
            </div>
          </fieldset>

          <!-- 2. Ubicación Operacional y Sistema (Cascada) -->
          <fieldset class="form-section">
            <legend class="section-legend">2. Ubicación y Clasificación Funcional</legend>

            <!-- Cascada Planta -> Área -->
            <div class="form-row two-cols">
              <div class="form-group">
                <label for="eq-plant">Planta Operativa</label>
                <select id="eq-plant" v-model="selectedPlantId" @change="handlePlantChange" class="form-control">
                  <option value="">-- Seleccionar Planta --</option>
                  <option v-for="plant in plantsList" :key="plant.id" :value="plant.id">
                    {{ plant.name }} ({{ plant.tag }})
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label for="eq-area">
                  Área Funcional
                  <span v-if="selectedPlantId" class="badge-filter">Filtrado</span>
                </label>
                <div class="input-action-wrapper">
                  <select id="eq-area" v-model="formData.area" class="form-control flex-grow">
                    <option value="">-- Sin Área Específica --</option>
                    <option v-for="area in availableAreas" :key="area.id" :value="area.id">
                      {{ area.name }} {{ area.tag ? `(${area.tag})` : '' }}
                    </option>
                  </select>
                  <button 
                    type="button" 
                    class="btn-mini-action" 
                    @click="showNewArea = !showNewArea" 
                    title="Crear nueva área al vuelo"
                  >
                    {{ showNewArea ? '✕' : '+ Área' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Subformulario: Crear Área al vuelo -->
            <div v-if="showNewArea" class="subform-card">
              <div class="subform-title">Nueva Área en {{ getPlantName(selectedPlantId) || 'Planta' }}</div>
              <div class="form-row two-cols">
                <input type="text" v-model="newAreaTag" placeholder="Tag Área (máx 10)" maxlength="10" class="form-control" />
                <input type="text" v-model="newAreaName" placeholder="Nombre Área" class="form-control" />
              </div>
              <button 
                type="button" 
                class="btn btn-sm btn-primary mt-2" 
                :disabled="!newAreaName.trim() || savingSub" 
                @click="createAreaInPlace"
              >
                {{ savingSub ? 'Guardando...' : 'Crear y Seleccionar Área' }}
              </button>
            </div>

            <!-- Selector de Sistema -->
            <div class="form-group mt-3">
              <label for="eq-system">Sistema Funcional <span class="required-asterisk">*</span></label>
              <div class="input-action-wrapper">
                <select id="eq-system" v-model="formData.system" required class="form-control flex-grow">
                  <option value="" disabled>-- Selecciona el Sistema --</option>
                  <option v-for="sys in systemsList" :key="sys.id" :value="sys.id">
                    {{ sys.name }} {{ sys.tag ? `[${sys.tag}]` : '' }}
                  </option>
                </select>
                <button 
                  type="button" 
                  class="btn-mini-action" 
                  @click="showNewSystem = !showNewSystem" 
                  title="Crear nuevo sistema al vuelo"
                >
                  {{ showNewSystem ? '✕' : '+ Sistema' }}
                </button>
              </div>
            </div>

            <!-- Subformulario: Crear Sistema al vuelo -->
            <div v-if="showNewSystem" class="subform-card">
              <div class="subform-title">Nuevo Sistema Funcional</div>
              <div class="form-row two-cols">
                <input type="text" v-model="newSystemTag" placeholder="Tag Sistema (máx 50)" maxlength="50" class="form-control" />
                <input type="text" v-model="newSystemName" placeholder="Nombre Sistema" class="form-control" />
              </div>
              <button 
                type="button" 
                class="btn btn-sm btn-primary mt-2" 
                :disabled="!newSystemName.trim() || savingSub" 
                @click="createSystemInPlace"
              >
                {{ savingSub ? 'Guardando...' : 'Crear y Seleccionar Sistema' }}
              </button>
            </div>
          </fieldset>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="handleClose" :disabled="saving">
            Cancelar
          </button>
          <button type="submit" class="btn btn-success" :disabled="saving">
            {{ saving ? 'Guardando...' : (isEditing ? 'Actualizar Equipo' : 'Guardar Equipo') }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { api } from '../api';

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  equipmentId: { type: [Number, String], default: null }
});

const emit = defineEmits(['close', 'saved']);

const isEditing = computed(() => !!props.equipmentId);

const formData = ref({
  tag: '',
  name: '',
  description: '',
  system: '',
  area: ''
});

const selectedPlantId = ref('');
const plantsList = ref([]);
const areasList = ref([]);
const systemsList = ref([]);
const saving = ref(false);
const savingSub = ref(false);

// Subformularios
const showNewArea = ref(false);
const newAreaTag = ref('');
const newAreaName = ref('');

const showNewSystem = ref(false);
const newSystemTag = ref('');
const newSystemName = ref('');

const loadCatalogs = async () => {
  try {
    const [pRes, aRes, sRes] = await Promise.all([
      api.get('plants/', { params: { page_size: 10000 } }),
      api.get('areas/', { params: { page_size: 10000 } }),
      api.get('systems/', { params: { page_size: 10000 } })
    ]);
    plantsList.value = pRes.data.results || pRes.data || [];
    areasList.value = aRes.data.results || aRes.data || [];
    systemsList.value = sRes.data.results || sRes.data || [];
  } catch (err) {
    console.error('Error cargando catálogos para EquipmentFormModal:', err);
  }
};

const availableAreas = computed(() => {
  if (!selectedPlantId.value) return areasList.value;
  return areasList.value.filter(a => {
    const pId = typeof a.plant === 'object' ? a.plant?.id : a.plant;
    return String(pId) === String(selectedPlantId.value);
  });
});

const getPlantName = (pId) => {
  const p = plantsList.value.find(item => String(item.id) === String(pId));
  return p ? p.name : '';
};

const handlePlantChange = () => {
  // Si el área seleccionada ya no pertenece a la planta, se deselecciona
  if (formData.value.area) {
    const currentAreaObj = areasList.value.find(a => String(a.id) === String(formData.value.area));
    const pId = typeof currentAreaObj?.plant === 'object' ? currentAreaObj?.plant?.id : currentAreaObj?.plant;
    if (String(pId) !== String(selectedPlantId.value)) {
      formData.value.area = '';
    }
  }
};

const resetForm = () => {
  formData.value = {
    tag: '',
    name: '',
    description: '',
    system: '',
    area: ''
  };
  selectedPlantId.value = '';
  showNewArea.value = false;
  showNewSystem.value = false;
};

const loadItemData = async (id) => {
  try {
    const res = await api.get(`equipments/${id}/`);
    const data = res.data;
    formData.value = {
      tag: data.tag || '',
      name: data.name || '',
      description: data.description || '',
      system: typeof data.system === 'object' ? data.system?.id : (data.system || ''),
      area: typeof data.area === 'object' ? data.area?.id : (data.area || '')
    };

    // Deducir planta a partir del área
    if (formData.value.area) {
      const currentArea = areasList.value.find(a => String(a.id) === String(formData.value.area));
      if (currentArea) {
        selectedPlantId.value = typeof currentArea.plant === 'object' ? currentArea.plant?.id : currentArea.plant;
      }
    }
  } catch (err) {
    console.error('Error cargando datos del equipo:', err);
  }
};

watch(() => props.isOpen, async (newVal) => {
  if (newVal) {
    await loadCatalogs();
    if (props.equipmentId) {
      await loadItemData(props.equipmentId);
    } else {
      resetForm();
    }
  }
});

// Creación de Área al vuelo
const createAreaInPlace = async () => {
  if (!newAreaName.value.trim()) return;
  savingSub.value = true;
  try {
    const payload = {
      tag: newAreaTag.value.trim(),
      name: newAreaName.value.trim(),
      plant: selectedPlantId.value || (plantsList.value[0]?.id || null)
    };
    const res = await api.post('areas/', payload);
    const createdArea = res.data;
    areasList.value.push(createdArea);
    formData.value.area = createdArea.id;
    if (createdArea.plant && !selectedPlantId.value) {
      selectedPlantId.value = createdArea.plant;
    }
    showNewArea.value = false;
    newAreaTag.value = '';
    newAreaName.value = '';
  } catch (err) {
    console.error('Error creando área al vuelo:', err);
    alert('No se pudo crear el área. Verifique los datos.');
  } finally {
    savingSub.value = false;
  }
};

// Creación de Sistema al vuelo
const createSystemInPlace = async () => {
  if (!newSystemName.value.trim()) return;
  savingSub.value = true;
  try {
    const payload = {
      tag: newSystemTag.value.trim(),
      name: newSystemName.value.trim()
    };
    const res = await api.post('systems/', payload);
    const createdSys = res.data;
    systemsList.value.push(createdSys);
    formData.value.system = createdSys.id;
    showNewSystem.value = false;
    newSystemTag.value = '';
    newSystemName.value = '';
  } catch (err) {
    console.error('Error creando sistema al vuelo:', err);
    alert('No se pudo crear el sistema.');
  } finally {
    savingSub.value = false;
  }
};

const handleSubmit = async () => {
  if (!formData.value.name.trim() || !formData.value.system) {
    alert('Por favor complete los campos obligatorios (*)');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      tag: formData.value.tag.trim(),
      name: formData.value.name.trim(),
      description: formData.value.description ? formData.value.description.trim() : '',
      system: formData.value.system,
      area: formData.value.area || null
    };

    if (isEditing.value) {
      await api.put(`equipments/${props.equipmentId}/`, payload);
    } else {
      await api.post('equipments/', payload);
    }

    emit('saved');
  } catch (err) {
    console.error('Error guardando equipo:', err);
    alert('Error al guardar el equipo. Verifique los datos.');
  } finally {
    saving.value = false;
  }
};

const handleClose = () => {
  if (!saving.value) {
    emit('close');
  }
};

onMounted(() => {
  if (props.isOpen) {
    loadCatalogs();
  }
});
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
  backdrop-filter: blur(2px);
  padding: 20px;
}

.modal-card {
  background: #ffffff;
  border-radius: 10px;
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.97); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  background-color: #f8fafc;
}

.modal-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
}

.btn-icon-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
}

.modal-form {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px 16px;
  margin: 0;
}

.section-legend {
  font-weight: 700;
  font-size: 0.85rem;
  color: #0369a1;
  padding: 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-row {
  display: flex;
  gap: 12px;
}

.two-cols > .form-group {
  flex: 1;
}

.form-group {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.required-asterisk {
  color: #ef4444;
}

.char-count {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 400;
  margin-left: auto;
}

.badge-filter {
  font-size: 0.7rem;
  background-color: #e0f2fe;
  color: #0284c7;
  padding: 1px 6px;
  border-radius: 4px;
}

.form-control {
  padding: 8px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
  background-color: #ffffff;
  transition: border-color 0.15s;
}

.form-control:focus {
  border-color: #0284c7;
  box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.15);
}

.input-action-wrapper {
  display: flex;
  gap: 6px;
}

.flex-grow {
  flex: 1;
}

.btn-mini-action {
  background-color: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #0284c7;
  cursor: pointer;
  white-space: nowrap;
}

.btn-mini-action:hover {
  background-color: #e2e8f0;
}

.subform-card {
  background-color: #f0f9ff;
  border: 1px dashed #0284c7;
  border-radius: 6px;
  padding: 10px 12px;
  margin-top: 8px;
}

.subform-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #0369a1;
  margin-bottom: 8px;
}

.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background-color: #f8fafc;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background-color 0.15s;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 0.8rem;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: #334155;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #cbd5e1;
}

.btn-primary {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0369a1;
}

.btn-success {
  background-color: #10b981;
  color: #ffffff;
}

.btn-success:hover:not(:disabled) {
  background-color: #059669;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
