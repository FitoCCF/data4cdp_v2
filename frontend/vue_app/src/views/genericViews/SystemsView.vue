<template>
  <div class="systems-view">
    <!--
      Componente ExcelGrid reutilizable
      - title: Título de la tabla
      - headers: Array con los nombres de las columnas
      - data: Matriz de datos
      - save: Evento emitido al guardar cambios
      - delete: Evento emitido al eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Sistemas"
      :headers="headers"
      :data="systemsData"
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
import { ref, onMounted } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';

// Configuración de columnas para la tabla de Sistemas
const headers = ['ID', 'Tag', 'Nombre', 'Descripción'];

// Estado reactivo
const systemsData = ref([]); // Almacena los datos en formato matriz
const loading = ref(false);  // Controla la visibilidad del loader
const error = ref(null);     // Almacena mensajes de error

/**
 * Carga los datos de sistemas desde la API
 */
const loadData = async () => {
  loading.value = true;
  error.value = null;

  try {
    // Petición GET al endpoint de sistemas
    const response = await api.get('systems/');

    if (Array.isArray(response.data)) {
        // Transformar array de objetos a matriz de arrays para ExcelGrid
        // Mapeo: [id, tag, name, description]
        systemsData.value = response.data.map(s => [
            s.id,
            s.tag || '',
            s.name || '',
            s.description || ''
        ]);
    } else {
        systemsData.value = [];
        console.warn('La API no devolvió un array:', response.data);
    }

  } catch (err) {
    console.error('Error cargando sistemas:', err);
    error.value = 'Error al cargar los datos de la base de datos.';
  } finally {
    loading.value = false;
  }
};

/**
 * Maneja el guardado de cambios (Creación y Edición)
 * @param {Array} updatedGrid - Matriz con los datos modificados
 */
const handleSave = async (updatedGrid) => {
  loading.value = true;
  try {
    // Iterar sobre cada fila para determinar si es update o create
    const promises = updatedGrid.map(async (row) => {
        const id = row[0]; // ID está en la primera columna
        const payload = {
            tag: row[1],
            name: row[2],
            description: row[3]
        };

        // Si tiene ID válido, es una actualización (PUT)
        if (id && String(id).trim() !== '') {
            return api.put(`systems/${id}/`, payload);
        } else {
            // Si no tiene ID, es una creación (POST)
            // Solo crear si hay datos mínimos (tag o nombre)
            if (payload.tag || payload.name) {
                return api.post('systems/', payload);
            }
        }
    });

    // Esperar a que todas las peticiones terminen
    await Promise.all(promises);

    alert('Cambios guardados correctamente.');

    // Recargar datos para obtener IDs nuevos y asegurar sincronización
    await loadData();

  } catch (err) {
    console.error('Error guardando sistemas:', err);
    alert('Error al guardar los cambios en la base de datos.');
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
        const deletePromises = idsToDelete.map(id => api.delete(`systems/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);

    } catch (err) {
        console.error('Error eliminando sistemas:', err);
        alert('Error al eliminar las filas.');
        await loadData();
    } finally {
        loading.value = false;
    }
};

// Cargar datos al montar el componente
onMounted(() => {
  loadData();
});
</script>

<style scoped>
.systems-view {
  position: relative;
  height: 100%;
}

/* Overlay de carga centrado */
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

/* Estilo para mensajes de error */
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
