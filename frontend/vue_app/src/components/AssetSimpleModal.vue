<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="handleClose">
    <div class="modal-card" role="dialog" aria-modal="true">
      <header class="modal-header">
        <h2 class="modal-title">
          {{ isEditing ? `Editar ${entityLabel}` : `Nueva ${entityLabel}` }}
        </h2>
        <button type="button" class="btn-icon-close" title="Cerrar" @click="handleClose">&times;</button>
      </header>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="modal-body">
          <!-- TAG y Nombre -->
          <div class="form-row two-cols">
            <div class="form-group">
              <label for="asset-tag">
                TAG / Código
                <span class="char-count">({{ formData.tag.length }}/{{ tagMaxLength }})</span>
              </label>
              <input
                id="asset-tag"
                type="text"
                v-model="formData.tag"
                :maxlength="tagMaxLength"
                :placeholder="tagPlaceholder"
                class="form-control"
              />
            </div>

            <div class="form-group">
              <label for="asset-name">
                Nombre <span class="required-asterisk">*</span>
                <span class="char-count">({{ formData.name.length }}/100)</span>
              </label>
              <input
                id="asset-name"
                type="text"
                v-model="formData.name"
                maxlength="100"
                required
                :placeholder="namePlaceholder"
                class="form-control"
              />
            </div>
          </div>

          <!-- Si es Área, mostrar selector de Planta -->
          <div v-if="entityType === 'area'" class="form-group">
            <label for="area-plant">Planta Asignada <span class="required-asterisk">*</span></label>
            <select id="area-plant" v-model="formData.plant" required class="form-control">
              <option value="" disabled>-- Selecciona la Planta --</option>
              <option v-for="p in plantsList" :key="p.id" :value="p.id">
                {{ p.name }} ({{ p.tag }})
              </option>
            </select>
          </div>

          <!-- Descripción -->
          <div class="form-group">
            <label for="asset-desc">Descripción</label>
            <textarea
              id="asset-desc"
              v-model="formData.description"
              rows="3"
              placeholder="Descripción funcional u operativa..."
              class="form-control"
            ></textarea>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="handleClose" :disabled="saving">
            Cancelar
          </button>
          <button type="submit" class="btn btn-success" :disabled="saving">
            {{ saving ? 'Guardando...' : (isEditing ? `Actualizar ${entityLabel}` : `Guardar ${entityLabel}`) }}
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
  entityType: { 
    type: String, 
    required: true,
    validator: v => ['plant', 'area', 'system'].includes(v)
  },
  itemId: { type: [Number, String], default: null }
});

const emit = defineEmits(['close', 'saved']);

const isEditing = computed(() => !!props.itemId);

const entityLabel = computed(() => {
  switch (props.entityType) {
    case 'plant': return 'Planta';
    case 'area': return 'Área';
    case 'system': return 'Sistema';
    default: return 'Registro';
  }
});

const endpoint = computed(() => {
  switch (props.entityType) {
    case 'plant': return 'plants';
    case 'area': return 'areas';
    case 'system': return 'systems';
    default: return '';
  }
});

const tagMaxLength = computed(() => {
  return props.entityType === 'system' ? 50 : 10;
});

const tagPlaceholder = computed(() => {
  switch (props.entityType) {
    case 'plant': return 'Ej: CONC, DESAL';
    case 'area': return 'Ej: MOL, CHANC';
    case 'system': return 'Ej: SYS-LUB-01';
    default: return '';
  }
});

const namePlaceholder = computed(() => {
  switch (props.entityType) {
    case 'plant': return 'Ej: Planta Concentradora';
    case 'area': return 'Ej: Área de Molienda SAG';
    case 'system': return 'Ej: Sistema de Lubricación Alta Presión';
    default: return '';
  }
});

const formData = ref({
  tag: '',
  name: '',
  description: '',
  plant: ''
});

const plantsList = ref([]);
const saving = ref(false);

const loadPlants = async () => {
  if (props.entityType === 'area') {
    try {
      const res = await api.get('plants/', { params: { page_size: 10000 } });
      plantsList.value = res.data.results || res.data || [];
    } catch (err) {
      console.error('Error cargando plantas para selector de área:', err);
    }
  }
};

const resetForm = () => {
  formData.value = {
    tag: '',
    name: '',
    description: '',
    plant: ''
  };
};

const loadItemData = async (id) => {
  try {
    const res = await api.get(`${endpoint.value}/${id}/`);
    const data = res.data;
    formData.value = {
      tag: data.tag || '',
      name: data.name || '',
      description: data.description || '',
      plant: typeof data.plant === 'object' ? data.plant?.id : (data.plant || '')
    };
  } catch (err) {
    console.error(`Error cargando datos de ${props.entityType}:`, err);
  }
};

watch(() => props.isOpen, async (newVal) => {
  if (newVal) {
    await loadPlants();
    if (props.itemId) {
      await loadItemData(props.itemId);
    } else {
      resetForm();
    }
  }
});

const handleSubmit = async () => {
  if (!formData.value.name.trim()) {
    alert('El nombre es obligatorio.');
    return;
  }
  if (props.entityType === 'area' && !formData.value.plant) {
    alert('Debe asignar una planta al área.');
    return;
  }

  saving.value = true;
  try {
    const payload = {
      tag: formData.value.tag.trim(),
      name: formData.value.name.trim(),
      description: formData.value.description ? formData.value.description.trim() : ''
    };

    if (props.entityType === 'area') {
      payload.plant = formData.value.plant;
    }

    if (isEditing.value) {
      await api.put(`${endpoint.value}/${props.itemId}/`, payload);
    } else {
      await api.post(`${endpoint.value}/`, payload);
    }

    emit('saved');
  } catch (err) {
    console.error(`Error guardando ${props.entityType}:`, err);
    alert('Error al guardar los datos.');
  } finally {
    saving.value = false;
  }
};

const handleClose = () => {
  if (!saving.value) {
    emit('close');
  }
};
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
  max-width: 540px;
  max-height: 85vh;
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
  font-size: 1.15rem;
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
  gap: 14px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.two-cols > .form-group {
  flex: 1;
}

.form-group {
  display: flex;
  flex-direction: column;
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

.btn-secondary {
  background-color: #e2e8f0;
  color: #334155;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #cbd5e1;
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
