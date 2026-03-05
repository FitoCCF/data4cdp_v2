<template>
  <div class="equipments-view">
    <!--
      Componente ExcelGrid reutilizable
      - columnsConfig: Configuración para dropdowns de Sistema y Área
      - @delete: Evento para eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Equipos"
      :headers="headers"
      :data="equipmentsData"
      :columnsConfig="columnsConfig"
      @save="handleSave"
      @delete="handleDelete"
    />
    
    <!-- Indicador de carga -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';

// Configuración de columnas
// Índices: 0:ID, 1:Tag, 2:Nombre, 3:Descripción, 4:Sistema, 5:Área
const headers = ['ID', 'Tag', 'Nombre', 'Descripción', 'Sistema', 'Área'];

// Estado reactivo
const equipmentsData = ref([]);
const systemsList = ref([]); // Lista de sistemas para dropdown
const areasList = ref([]);   // Lista de áreas para dropdown
const loading = ref(false);
const error = ref(null);

// Configuración dinámica de columnas para ExcelGrid (Dropdowns)
const columnsConfig = computed(() => {
    return {
        4: { // Columna 'Sistema'
            type: 'select',
            options: systemsList.value.map(s => ({ value: s.id, label: s.name }))
        },
        5: { // Columna 'Área'
            type: 'select',
            options: areasList.value.map(a => ({ value: a.id, label: a.name }))
        }
    };
});

/**
 * Carga los datos de equipos, sistemas y áreas desde la API
 */
const loadData = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Carga paralela de recursos
    const [eqRes, sysRes, areaRes] = await Promise.all([
        api.get('equipments/'),
        api.get('systems/'),
        api.get('areas/')
    ]);
    
    // Procesar listas auxiliares
    if (Array.isArray(sysRes.data)) systemsList.value = sysRes.data;
    if (Array.isArray(areaRes.data)) areasList.value = areaRes.data;

    // Procesar Equipos
    if (Array.isArray(eqRes.data)) {
        equipmentsData.value = eqRes.data.map(e => [
            e.id,
            e.tag || '',
            e.name || '',
            e.description || '',
            // Manejo de FKs: extraer ID si viene objeto completo
            (e.system && typeof e.system === 'object') ? e.system.id : (e.system || ''),
            (e.area && typeof e.area === 'object') ? e.area.id : (e.area || '')
        ]);
    } else {
        equipmentsData.value = [];
        console.warn('La API no devolvió un array:', eqRes.data);
    }

  } catch (err) {
    console.error('Error cargando datos:', err);
    error.value = 'Error al cargar los datos de la base de datos.';
  } finally {
    loading.value = false;
  }
};

/**
 * Maneja el guardado de cambios
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3],
            system: row[4], // ID del sistema seleccionado
            area: row[5]    // ID del área seleccionada
        };

        // Limpiar FKs vacías para evitar errores de validación
        if (!payload.system) delete payload.system;
        if (!payload.area) delete payload.area;

        // Actualizar (PUT) o Crear (POST)
        if (id && String(id).trim() !== '') {
            return api.put(`equipments/${id}/`, payload);
        } else {
            if (payload.tag || payload.name) {
                return api.post('equipments/', payload);
            }
        }
    });

    await Promise.all(promises);
    alert('Cambios guardados correctamente.');
    await loadData();

  } catch (err) {
    console.error('Error guardando equipos:', err);
    alert('Error al guardar. Verifique las relaciones (Sistema/Área).');
  } finally {
    loading.value = false;
  }
};

/**
 * Maneja la eliminación de filas
 * @param {Array} idsToDelete - Array de IDs a eliminar
 */
const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    loading.value = true;
    try {
        const deletePromises = idsToDelete.map(id => api.delete(`equipments/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);

    } catch (err) {
        console.error('Error eliminando equipos:', err);
        alert('Error al eliminar las filas.');
        await loadData();
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.equipments-view {
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
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  margin: 10px;
  border-radius: 4px;
}
</style>
