<!--
  AssaysView.vue
  Vista de Mantenimiento de Ensayos (CRUD).
  Muestra todas las columnas de la tabla assays con capacidades de filtrado, edición, creación y borrado.
-->
<template>
  <section class="samples-view">
    <header class="view-header">
      <h1>Mantenimiento de Ensayos</h1>
      <div class="header-actions">
        <!-- Filtro rápido por fecha -->
        <input 
          type="date" 
          v-model="filterDate" 
          class="date-filter"
          title="Filtrar por fecha"
        />

        <button
          type="button"
          class="btn btn-blue"
          @click="loadData"
          :disabled="loading || saving || removing || editingId !== null"
        >
          {{ loading ? 'Actualizando…' : 'Actualizar' }}
        </button>
        <button
          type="button"
          class="btn btn-green"
          @click="startCreate"
          :disabled="loading || saving || removing || creating || editingId !== null"
        >
          Nuevo registro
        </button>
      </div>
    </header>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <!-- Contenedor con scroll horizontal para soportar muchas columnas -->
    <div class="table-container">
      <table v-if="filteredAssays.length || creating" class="samples-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Chemical ID</th>
            <th>Muestra</th>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Instancia</th>
            
            <!-- Leyes (a*) -->
            <th>A1 Fe</th>
            <th>A2 Cu</th>
            <th>A3 Zn</th>
            <th>A4 Mo</th>
            <th>A5 A5</th>
            <th>A6 Sol</th>
            <th>A7 A7</th>
            
            <!-- Porcentajes (p*) -->
            <th>% Fe</th>
            <th>% Cu</th>
            <th>% Zn</th>
            <th>% Mo</th>
            <th>% Ins</th>
            <th>% Sol</th>
            
            <!-- Counts (n*) -->
            <th>N1 Fe</th>
            <th>N2 Cu</th>
            <th>N3 Zn</th>
            <th>N4 Mo</th>
            <th>N5 Ech5</th>
            <th>N6 Sc</th>
            <th>N7 Ech7</th>
            
            <!-- Pesos -->
            <th>Tara</th>
            <th>Peso Total</th>
            <th>Peso Seco</th>
            <th>Peso Prod.</th>
            
            <!-- Otros -->
            <th>User P</th>
            <th>Meta User</th>
            <th>Turno</th>
            <th class="actions-cell">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="assay in filteredAssays" :key="assay.id">

            <!-- ID -->
            <td>
              <span v-if="assay.id === NEW_ASSAY_ID" class="new-badge">Nuevo</span>
              <span v-else>{{ assay.id }}</span>
            </td>

            <!-- Chemical ID -->
            <td>
               <input v-if="isEditing(assay)" v-model.number="editForm.chemical_id" type="number" class="edit-input small" />
               <span v-else>{{ assay.chemical_id }}</span>
            </td>

            <!-- Sample (Select) -->
            <td>
               <select v-if="isEditing(assay)" v-model="editForm.sample" class="edit-select">
                  <option :value="null">-- Sel --</option>
                  <option v-for="s in samplesList" :key="s.id" :value="s.id">
                    {{ s.name || s.tag || s.id }}
                  </option>
               </select>
               <span v-else>{{ getSampleName(assay.sample) }}</span>
            </td>

            <!-- Date -->
            <td>
               <input v-if="isEditing(assay)" v-model="editForm.date" type="date" class="edit-input" />
               <span v-else>{{ assay.date }}</span>
            </td>

            <!-- Time -->
            <td>
               <input v-if="isEditing(assay)" v-model="editForm.time" type="time" class="edit-input" step="1" />
               <span v-else>{{ formatTime(assay.time) }}</span>
            </td>

            <!-- Instance -->
            <td>
               <input v-if="isEditing(assay)" v-model.number="editForm.instance" type="number" class="edit-input small" />
               <span v-else>{{ assay.instance }}</span>
            </td>

            <!-- Leyes A -->
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a1fe" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a1fe }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a2cu" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a2cu }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a3zn" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a3zn }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a4mo" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a4mo }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a5a5" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a5a5 }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a6sol" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a6sol }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.a7a7" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.a7a7 }}</span></td>

            <!-- Porcentajes P -->
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pFe" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pFe }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pCu" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pCu }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pZn" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pZn }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pMo" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pMo }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pIns" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pIns }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pSol" type="number" step="0.001" class="edit-input" /><span v-else>{{ assay.pSol }}</span></td>

            <!-- Counts N -->
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n1fe" type="number" class="edit-input small" /><span v-else>{{ assay.n1fe }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n2cu" type="number" class="edit-input small" /><span v-else>{{ assay.n2cu }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n3zn" type="number" class="edit-input small" /><span v-else>{{ assay.n3zn }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n4mo" type="number" class="edit-input small" /><span v-else>{{ assay.n4mo }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n5ech5" type="number" class="edit-input small" /><span v-else>{{ assay.n5ech5 }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n6sc" type="number" class="edit-input small" /><span v-else>{{ assay.n6sc }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.n7ech7" type="number" class="edit-input small" /><span v-else>{{ assay.n7ech7 }}</span></td>

            <!-- Pesos -->
            <td><input v-if="isEditing(assay)" v-model.number="editForm.tara" type="number" step="0.01" class="edit-input" /><span v-else>{{ assay.tara }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.tweight" type="number" step="0.01" class="edit-input" /><span v-else>{{ assay.tweight }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.dweight" type="number" step="0.01" class="edit-input" /><span v-else>{{ assay.dweight }}</span></td>
            <td><input v-if="isEditing(assay)" v-model.number="editForm.pweight" type="number" step="0.01" class="edit-input" /><span v-else>{{ assay.pweight }}</span></td>

            <!-- Otros -->
            <td>
               <input v-if="isEditing(assay)" v-model.number="editForm.userp" type="number" class="edit-input small" />
               <span v-else>{{ assay.userp }}</span>
            </td>
            <td>
               <input v-if="isEditing(assay)" v-model="editForm.meta_user" type="text" class="edit-input" />
               <span v-else>{{ assay.meta_user }}</span>
            </td>
            <td>
               <input v-if="isEditing(assay)" v-model="editForm.turn" type="text" class="edit-input small" />
               <span v-else>{{ assay.turn }}</span>
            </td>

            <!-- Acciones (Sticky right) -->
            <td class="actions-cell">
              <div v-if="editingId === assay.id" class="action-buttons">
                <!-- Botón para guardar cambios -->
                <button
                  class="btn btn-green"
                  @click="saveEdit(assay)"
                  :disabled="saving || loading"
                >
                  Guardar
                </button>
                <!-- Botón para cancelar edición -->
                <button
                  class="btn btn-gray"
                  @click="cancelEdit"
                  :disabled="saving"
                >
                  Cancelar
                </button>
              </div>
              <div v-else class="action-buttons">
                <!-- Botón para iniciar edición -->
                <button
                  class="btn btn-blue"
                  @click="startEdit(assay)"
                  :disabled="loading || saving || creating || editingId !== null"
                >
                  Editar
                </button>
                <!-- Botón para eliminar registro -->
                <button
                  class="btn btn-red"
                  @click="deleteAssay(assay.id)"
                  :disabled="loading || saving || creating || editingId !== null"
                >
                  Eliminar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty" :class="{ loading }">
        {{ loading ? 'Cargando ensayos…' : 'No hay ensayos registrados o no coinciden con el filtro.' }}
      </p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue';
import { api } from '../../api';

// --- Constantes y Estado ---
const NEW_ASSAY_ID = 'nuevo';
const assays = ref([]);
const samplesList = ref([]);
const loading = ref(false);
const error = ref('');
const saving = ref(false);
const removing = ref(false);
const editingId = ref(null);
const creating = ref(false);

// Filtro por fecha (opcional, para no cargar todo si son muchos)
const filterDate = ref('');

// Formulario reactivo con TODOS los campos
const editForm = reactive({
    date: '', time: '', instance: null,
    n1fe: null, n2cu: null, n3zn: null, n4mo: null, n5ech5: null, n6sc: null, n7ech7: null,
    pFe: null, pCu: null, pZn: null, pMo: null, pIns: null, pSol: null,
    tara: null, tweight: null, dweight: null, pweight: null,
    chemical_id: null, sample: null,
    a1fe: null, a2cu: null, a3zn: null, a4mo: null, a5a5: null, a6sol: null, a7a7: null,
    userp: null, meta_user: '', turn: ''
});

// --- Computed ---
const filteredAssays = computed(() => {
    if (!filterDate.value) return assays.value;
    return assays.value.filter(a => a.date === filterDate.value || a.id === NEW_ASSAY_ID);
});

// --- Métodos de Carga ---
const loadData = async () => {
    loading.value = true;
    error.value = '';
    try {
        const [assaysRes, samplesRes] = await Promise.all([
            api.get('assays/'),
            api.get('samples/')
        ]);
        assays.value = Array.isArray(assaysRes.data) ? assaysRes.data : [];
        samplesList.value = Array.isArray(samplesRes.data) ? samplesRes.data : [];
        
        // Ordenar por fecha desc por defecto
        assays.value.sort((a, b) => {
            if (a.date > b.date) return -1;
            if (a.date < b.date) return 1;
            return 0;
        });

    } catch (err) {
        console.error("Error loading data", err);
        error.value = "Error al cargar datos.";
        assays.value = [];
    } finally {
        loading.value = false;
    }
};

// --- Helpers de Formato ---
const getSampleName = (sampleId) => {
    if (!sampleId) return '';
    // Si viene objeto
    if (typeof sampleId === 'object') return sampleId.name || sampleId.tag || sampleId.id;
    // Si viene ID, buscar en lista
    const s = samplesList.value.find(x => x.id === sampleId);
    return s ? (s.name || s.tag) : sampleId;
};

const formatTime = (t) => {
  if (!t) return '';
  return t.length > 5 ? t.substring(0, 5) : t;
}

const isEditing = (assay) => editingId.value === assay.id;

// --- CRUD Actions ---

// Limpiar formulario
const clearForm = () => {
    Object.keys(editForm).forEach(key => editForm[key] = null);
    editForm.meta_user = ''; 
    editForm.turn = '';
    // Valores por defecto si necesario
};

// Cancelar Edición
const cancelEdit = () => {
    editingId.value = null;
    clearForm();
    error.value = '';
    if (creating.value) {
        assays.value = assays.value.filter(a => a.id !== NEW_ASSAY_ID);
        creating.value = false;
    }
};

// Iniciar Creación
const startCreate = () => {
    if (loading.value || saving.value || removing.value || editingId.value !== null) return;
    cancelEdit();
    creating.value = true;
    editingId.value = NEW_ASSAY_ID;
    clearForm();
    
    // Pre-poblar fecha actual
    editForm.date = new Date().toISOString().split('T')[0];
    editForm.time = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

    const newRow = { id: NEW_ASSAY_ID, ...editForm };
    assays.value.unshift(newRow);
};

// Iniciar Edición
const startEdit = (assay) => {
    if (loading.value || saving.value || removing.value || editingId.value !== null) return;
    cancelEdit();
    editingId.value = assay.id;
    
    // Copiar valores al formulario
    Object.keys(editForm).forEach(key => {
        // Manejo especial para sample si viene como objeto
        if (key === 'sample' && typeof assay[key] === 'object' && assay[key] !== null) {
            editForm[key] = assay[key].id;
        } else {
            editForm[key] = assay[key];
        }
    });
};

// Guardar (Crear o Actualizar)
const saveEdit = async (assay) => {
    saving.value = true;
    error.value = '';
    
    // Payload básico
    const payload = { ...editForm };
    // Limpiezas: strings vacíos a null si es numérico? DRF suele manejarlo si el campo es null=True
    // Asegurar sample es ID
    
    try {
        if (assay.id === NEW_ASSAY_ID) {
            await api.post('assays/', payload);
        } else {
            await api.put(`assays/${assay.id}/`, payload);
        }
        cancelEdit();
        await loadData();
    } catch (err) {
        console.error("Error saving", err);
        error.value = "Error al guardar el registro. Revise los datos.";
    } finally {
        saving.value = false;
    }
};

// Eliminar
const deleteAssay = async (id) => {
    if (!confirm("¿Está seguro de eliminar este ensayo?")) return;
    removing.value = true;
    try {
        await api.delete(`assays/${id}/`);
        await loadData();
    } catch (err) {
        console.error("Error deleting", err);
        error.value = "No se pudo eliminar.";
    } finally {
        removing.value = false;
    }
};

onMounted(() => {
    // Si filterDate vacía, cargar todo. O poner fecha actual por defecto.
    // filterDate.value = new Date().toISOString().split('T')[0];
    loadData();
});
</script>

<style scoped>
/* Contenedor principal de la vista (Igual a SamplesView) */
.samples-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.06);
  max-width: 100%;
  overflow: hidden;
}

/* Estilos del encabezado (Igual a SamplesView) */
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.view-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1e293b;
}

/* Estilos de mensaje vacío (Igual a SamplesView) */
.empty {
  margin: 0;
  text-align: center;
  color: #64748b;
}
.empty.loading {
  color: #1e293b;
}

/* -- Estilos Específicos de Assays (Scroll, Inputs) -- */

.date-filter {
    padding: 0.4rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.table-container {
  overflow-x: auto;
  /* Borde eliminado para parecerse a SamplesView que no tiene doble borde */
  border-radius: 6px; 
}

.samples-table {
  min-width: 2500px; /* Ancho forzado para scroll horizontal */
}

/* Sticky Column Styles */
.actions-cell {
    position: sticky;
    right: 0;
    background: white;
    z-index: 5;
    border-left: 2px solid #e2e8f0;
}

th.actions-cell {
    z-index: 20 !important;
    background-color: #f8f9fa;
}

.new-badge {
    background: #10b981;
    color: white;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.7rem;
}

.edit-input {
    width: 80px;
    padding: 4px;
}
.edit-input.small {
    width: 50px;
}
.edit-select {
    width: 120px;
}

.action-buttons {
    display: flex;
    gap: 0.2rem;
}

.feedback.error { color: red; }
</style>
