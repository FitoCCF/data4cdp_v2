<template>
  <div class="areas-view">
    <ExcelGrid
      title="Mantenimiento de Áreas"
      :headers="headers"
      :data="areasData"
      :columnsConfig="columnsConfig"
      @save="handleSave"
      @delete="handleDelete"
    />
    
    <!-- Mensaje de carga o error -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';

// Configuración de columnas
const headers = ['ID', 'Tag', 'Nombre', 'Descripción', 'Planta'];

// Estado
const areasData = ref([]);
const plantsList = ref([]); // Lista de plantas para el dropdown
const loading = ref(false);
const error = ref(null);

// Configuración dinámica de columnas para ExcelGrid
const columnsConfig = computed(() => {
    return {
        4: { // Índice de la columna 'Planta'
            type: 'select',
            options: plantsList.value.map(p => ({ value: p.id, label: p.name }))
        }
    };
});

// Cargar datos
const loadData = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Cargar Áreas y Plantas en paralelo
    const [areasRes, plantsRes] = await Promise.all([
        api.get('areas/'),
        api.get('plants/')
    ]);
    
    // Procesar Plantas
    if (Array.isArray(plantsRes.data)) {
        plantsList.value = plantsRes.data;
    }

    // Procesar Áreas
    if (Array.isArray(areasRes.data)) {
        areasData.value = areasRes.data.map(a => [
            a.id,
            a.tag || '',
            a.name || '',
            a.description || '',
            // Manejo de FK: si viene objeto {id, name} tomamos id, si viene id directo lo usamos
            (a.plant && typeof a.plant === 'object') ? a.plant.id : (a.plant || '')
        ]);
    } else {
        areasData.value = [];
        console.warn('La API no devolvió un array:', areasRes.data);
    }

  } catch (err) {
    console.error('Error cargando datos:', err);
    error.value = 'Error al cargar los datos de la base de datos.';
  } finally {
    loading.value = false;
  }
};

// Guardar cambios
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    const promises = updatedGrid.map(async (row) => {
        const id = row[0];
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3],
            plant: row[4] // Aquí irá el ID de la planta seleccionado
        };

        // Validación básica de FK
        if (!payload.plant) delete payload.plant;

        if (id && String(id).trim() !== '') {
            return api.put(`areas/${id}/`, payload);
        } else {
            if (payload.tag || payload.name) {
                return api.post('areas/', payload);
            }
        }
    });

    await Promise.all(promises);
    alert('Cambios guardados correctamente.');
    await loadData();

  } catch (err) {
    console.error('Error guardando áreas:', err);
    alert('Error al guardar. Verifique los datos.');
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
        const deletePromises = idsToDelete.map(id => api.delete(`areas/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);

    } catch (err) {
        console.error('Error eliminando áreas:', err);
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
.areas-view {
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
}
</style>
