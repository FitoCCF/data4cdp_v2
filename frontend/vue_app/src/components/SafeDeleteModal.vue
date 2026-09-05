<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="handleClose">
    <div class="modal-card" role="dialog" aria-modal="true">
      <!-- Cabecera del modal de advertencia -->
      <header class="modal-header">
        <div class="header-title-group">
          <span class="warning-badge">⚠️ Confirmación Crítica</span>
          <h2 class="modal-title">Eliminar {{ entityTitle }} ({{ idsToDelete.length }})</h2>
        </div>
        <button type="button" class="btn-icon-close" title="Cerrar" @click="handleClose">&times;</button>
      </header>

      <!-- Cuerpo con reporte de impacto -->
      <div class="modal-body">
        <div v-if="loadingImpact" class="loading-state">
          <div class="spinner"></div>
          <p>Analizando dependencias y registros relacionados en cascada...</p>
        </div>

        <div v-else-if="impactList.length > 0" class="impact-report">
          <p class="impact-intro">
            Esta acción eliminará de forma <strong>permanente e irreversible</strong> los siguientes registros principales y todas sus entidades dependientes:
          </p>

          <div class="impact-items-list">
            <div v-for="item in impactList" :key="item.id" class="impact-item-card">
              <div class="item-header">
                <span class="item-tag">{{ item.tag || 'S/T' }}</span>
                <span class="item-name">{{ item.name }}</span>
                <span class="item-id">(ID: {{ item.id }})</span>
              </div>

              <!-- Desglose de registros dependientes -->
              <div class="item-dependencies">
                <div v-if="item.areas_count !== undefined" class="dep-badge" :class="{ 'has-deps': item.areas_count > 0 }">
                  📂 Áreas: <strong>{{ item.areas_count }}</strong>
                </div>
                <div v-if="item.equipments_count !== undefined" class="dep-badge" :class="{ 'has-deps': item.equipments_count > 0 }">
                  🔧 Equipos: <strong>{{ item.equipments_count }}</strong>
                </div>
                <div v-if="item.tasks_count !== undefined" class="dep-badge" :class="{ 'has-deps': item.tasks_count > 0 }">
                  📋 Tareas Preventivas: <strong>{{ item.tasks_count }}</strong>
                </div>
                <div v-if="item.correctives_count !== undefined" class="dep-badge" :class="{ 'has-deps': item.correctives_count > 0 }">
                  ⚠️ Tareas Correctivas: <strong>{{ item.correctives_count }}</strong>
                </div>
                <div v-if="item.samples_count !== undefined" class="dep-badge" :class="{ 'has-deps': item.samples_count > 0 }">
                  🧪 Muestras: <strong>{{ item.samples_count }}</strong>
                </div>
              </div>

              <div v-if="item.total_impact > 0" class="impact-alert">
                ⚠️ Se destruirán <strong>{{ item.total_impact }}</strong> registros secundarios vinculados a este elemento.
              </div>
              <div v-else class="impact-safe">
                ✓ No se detectaron dependencias activas.
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <p>¿Está seguro de eliminar las filas seleccionadas?</p>
        </div>
      </div>

      <!-- Pie con acciones -->
      <footer class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="handleClose" :disabled="deleting">
          Cancelar
        </button>
        <button type="button" class="btn btn-danger" @click="handleConfirm" :disabled="deleting">
          {{ deleting ? 'Eliminando...' : 'Confirmar y Eliminar' }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { api } from '../api';

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  endpoint: { type: String, required: true }, // ej: 'plants', 'areas', 'systems', 'equipments'
  entityTitle: { type: String, default: 'Registro(s)' },
  idsToDelete: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'confirmed']);

const loadingImpact = ref(false);
const deleting = ref(false);
const impactList = ref([]);

const fetchImpact = async () => {
  if (!props.idsToDelete || props.idsToDelete.length === 0) {
    impactList.value = [];
    return;
  }

  loadingImpact.value = true;
  try {
    const res = await api.post(`${props.endpoint}/delete-impact/`, { ids: props.idsToDelete });
    impactList.value = res.data.impact || [];
  } catch (err) {
    console.warn('No se pudo obtener el reporte de impacto previo:', err);
    // Respaldo visual básico
    impactList.value = props.idsToDelete.map(id => ({
      id,
      tag: '',
      name: `ID ${id}`,
      total_impact: 0
    }));
  } finally {
    loadingImpact.value = false;
  }
};

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchImpact();
  } else {
    impactList.value = [];
  }
});

const handleClose = () => {
  if (!deleting.value) {
    emit('close');
  }
};

const handleConfirm = () => {
  emit('confirmed', props.idsToDelete);
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
  z-index: 1100;
  backdrop-filter: blur(2px);
  padding: 20px;
}

.modal-card {
  background: #ffffff;
  border-radius: 10px;
  width: 100%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.96); }
  to { opacity: 1; transform: scale(1); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  background-color: #fff1f2;
}

.warning-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #e11d48;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: 2px;
}

.modal-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #9f1239;
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

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.loading-state {
  text-align: center;
  padding: 30px;
  color: #64748b;
}

.spinner {
  width: 32px;
  height: 32px;
  margin: 0 auto 12px;
  border: 3px solid #e2e8f0;
  border-top-color: #e11d48;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.impact-intro {
  margin-top: 0;
  margin-bottom: 14px;
  font-size: 0.9rem;
  color: #334155;
}

.impact-items-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.impact-item-card {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px 14px;
  background-color: #f8fafc;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.item-tag {
  background-color: #0284c7;
  color: #ffffff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.item-name {
  font-weight: 600;
  color: #0f172a;
}

.item-id {
  font-size: 0.8rem;
  color: #64748b;
}

.item-dependencies {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.dep-badge {
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 4px;
  background-color: #e2e8f0;
  color: #475569;
}

.dep-badge.has-deps {
  background-color: #fee2e2;
  color: #991b1b;
  font-weight: 600;
}

.impact-alert {
  font-size: 0.8rem;
  color: #dc2626;
  font-weight: 600;
  background-color: #fef2f2;
  padding: 6px 10px;
  border-radius: 4px;
  border-left: 3px solid #ef4444;
}

.impact-safe {
  font-size: 0.8rem;
  color: #16a34a;
  font-weight: 600;
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

.btn-danger {
  background-color: #e11d48;
  color: #ffffff;
}

.btn-danger:hover:not(:disabled) {
  background-color: #be123c;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
