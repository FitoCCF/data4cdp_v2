<template>
  <div class="samples-view">
    <!--
      Componente ExcelGrid reutilizable
      - title: Título de la tabla
      - headers: Nombres de las columnas
      - data: Matriz de datos a mostrar
      - columnsConfig: Configuración especial para columnas (ej. dropdowns)
      - @save: Evento emitido al guardar
      - @delete: Evento emitido al eliminar filas
    -->
    <ExcelGrid
      title="Mantenimiento de Muestras"
      :headers="headers"
      :data="samplesData"
      :columnsConfig="columnsConfig"
      @save="handleSave"
      @delete="handleDelete"
    />

    <!-- Indicador de carga que se superpone a la vista -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error que aparece si falla la carga o guardado -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importaciones de Vue
import { ref, onMounted, computed } from 'vue';
// Importación del componente reutilizable
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importación del cliente API
import { api } from '../../api';

// --- Configuración de la Tabla ---

// Define los encabezados de las columnas que se mostrarán en la tabla
// Índices: 0:ID, 1:Tag, 2:Nombre, 3:Equipo
const headers = ['ID', 'Tag', 'Nombre', 'Equipo'];

// --- Estado Reactivo ---

// Almacena los datos de las muestras en formato de matriz para ExcelGrid
const samplesData = ref([]);
// Almacena la lista completa de objetos de equipo para el dropdown
const equipmentsList = ref([]);
// Controla la visibilidad del overlay de carga
const loading = ref(false);
// Almacena el mensaje de error a mostrar
const error = ref(null);

// --- Propiedades Computadas ---

/**
 * Configuración dinámica para las columnas de ExcelGrid.
 * Esta propiedad computada se recalcula si `equipmentsList` cambia.
 */
const columnsConfig = computed(() => {
    return {
        // La clave '3' corresponde al índice de la columna 'Equipo' en el array `headers`
        3: {
            // Define el tipo de celda como un menú desplegable
            type: 'select',
            // Genera las opciones para el dropdown
            options: equipmentsList.value.map(equipment => {
                // Para cada equipo, crea una etiqueta concatenando nombre y descripción
                const label = `${equipment.name || ''} - ${equipment.description || ''}`.trim();

                // Retorna un objeto con el formato { value: ID, label: TEXTO_CONCATENADO }
                return {
                    value: equipment.id,
                    // Si el label queda como '-', usar solo el nombre o un identificador
                    label: label === '-' ? (equipment.name || `Equipo ID: ${equipment.id}`) : label
                };
            })
        }
    };
});

// --- Métodos de API ---

/**
 * Carga los datos de muestras y equipos desde el backend.
 */
const loadData = async () => {
  // Activa el estado de carga
  loading.value = true;
  // Limpia errores previos
  error.value = null;

  try {
    // Realiza peticiones en paralelo para optimizar tiempos de carga
    const [samplesRes, equipmentsRes] = await Promise.all([
        api.get('samples/'),
        api.get('equipments/')
    ]);

    // Procesa y almacena la lista de equipos
    if (Array.isArray(equipmentsRes.data)) {
        equipmentsList.value = equipmentsRes.data;
    }

    // Procesa y transforma los datos de las muestras
    if (Array.isArray(samplesRes.data)) {
        samplesData.value = samplesRes.data.map(sample => [
            sample.id,
            sample.tag || '',
            sample.name || '',
            // Extrae el ID de la clave foránea 'equipment'
            (sample.equipment && typeof sample.equipment === 'object') ? sample.equipment.id : (sample.equipment || '')
        ]);
    } else {
        // Si la API no devuelve un array, inicializa como vacío y advierte en consola
        samplesData.value = [];
        console.warn('La API de muestras no devolvió un array:', samplesRes.data);
    }

  } catch (err) {
    // Manejo de errores de la petición
    console.error('Error cargando datos:', err);
    error.value = 'Error al cargar los datos de la base de datos.';
  } finally {
    // Desactiva el estado de carga, independientemente del resultado
    loading.value = false;
  }
};

/**
 * Maneja el evento 'save' emitido por ExcelGrid para guardar los cambios.
 * @param {Array} updatedGrid - La matriz de datos actualizada desde el componente hijo.
 */
const handleSave = async (updatedGrid) => {
  // Activa el estado de carga
  loading.value = true;
  try {
    // Mapea cada fila de la matriz a una promesa de petición (PUT o POST)
    const promises = updatedGrid.map(async (row) => {
        const id = row[0]; // El ID está en la primera columna
        const payload = {
            tag: row[1],
            name: row[2],
            equipment: row[3] // El ID del equipo seleccionado
        };

        // Si el ID de equipo es nulo o vacío, no lo envía en el payload
        if (!payload.equipment) delete payload.equipment;

        // Determina si es una actualización (PUT) o una creación (POST)
        if (id && String(id).trim() !== '') {
            return api.put(`samples/${id}/`, payload);
        } else {
            // Solo crea si hay datos mínimos (tag o nombre)
            if (payload.tag || payload.name) {
                return api.post('samples/', payload);
            }
        }
    });

    // Espera a que todas las peticiones se completen
    await Promise.all(promises);

    // Notifica al usuario del éxito
    alert('Cambios guardados correctamente.');

    // Recarga los datos para reflejar los cambios y obtener nuevos IDs
    await loadData();

  } catch (err) {
    // Manejo de errores durante el guardado
    console.error('Error guardando muestras:', err);
    alert('Error al guardar. Verifique la relación con Equipo.');
  } finally {
    // Desactiva el estado de carga
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
        const deletePromises = idsToDelete.map(id => api.delete(`samples/${id}/`));
        await Promise.all(deletePromises);

        alert(`${idsToDelete.length} fila(s) eliminada(s) correctamente.`);

    } catch (err) {
        console.error('Error eliminando muestras:', err);
        alert('Error al eliminar las filas.');
        await loadData();
    } finally {
        loading.value = false;
    }
};

// --- Ciclo de Vida ---

// Hook que se ejecuta cuando el componente se monta en el DOM
onMounted(() => {
  // Llama a la función para cargar los datos iniciales
  loadData();
});
</script>

<style scoped>
/* Contenedor principal de la vista */
.samples-view {
  position: relative;
  height: 100%;
}

/* Overlay de carga para feedback visual */
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
