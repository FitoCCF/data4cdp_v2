<!--
  AssaysView.vue
  Vista de Mantenimiento de Ensayos usando ExcelGrid.
  Muestra ensayos filtrados inicialmente por Equipo ID=1.
-->
<template>
  <section class="assays-view">
    <header class="view-header">
      <h1>Mantenimiento de Ensayos (Equipo 1)</h1>
      <div class="header-actions">
        <!-- Filtro rápido por fecha -->
        <input 
          type="date" 
          v-model="filterDate" 
          class="date-filter"
          title="Filtrar por fecha"
          @change="loadData"
        />

        <button
          type="button"
          class="btn btn-blue"
          @click="loadData"
          :disabled="loading"
        >
          {{ loading ? 'Cargando...' : 'Recargar Datos' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <!-- Componente ExcelGrid -->
    <div class="grid-wrapper">
      <ExcelGrid
        v-if="!loading"
        title="Ensayos - Equipo 1"
        :headers="gridHeaders"
        :data="gridData"
        :columnsConfig="gridConfig"
        @save="handleSave"
        @delete="handleDelete"
      />
      <p v-else class="loading-text">Cargando datos...</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { api } from '../../api';
import ExcelGrid from '../../components/ExcelGrid.vue';

// --- Estado ---
const loading = ref(false);
const error = ref('');
const filterDate = ref('');
const rawAssays = ref([]);
const samplesList = ref([]);

// --- Configuración de la Grilla ---

// 1. Definición de Encabezados (Orden visual de columnas)
const gridHeaders = [
  'ID', 'Chemical ID', 'Muestra', 'Fecha', 'Hora', 'Instancia',
  'A1 Fe', 'A2 Cu', 'A3 Zn', 'A4 Mo', 'A5 A5', 'A6 Sol', 'A7 A7',
  '% Fe', '% Cu', '% Zn', '% Mo', '% Ins', '% Sol',
  'N1 Fe', 'N2 Cu', 'N3 Zn', 'N4 Mo', 'N5 Ech5', 'N6 Sc', 'N7 Ech7',
  'Tara', 'Peso Total', 'Peso Seco', 'Peso Prod.',
  'User P', 'Meta User', 'Turno'
];

// 2. Mapeo de índices de columna a claves del objeto API
// Esto es crucial para traducir de Array (Grilla) <-> Objeto (API)
const colKeys = [
  'id', 'chemical_id', 'sample', 'date', 'time', 'instance',
  'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7',
  'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pSol',
  'n1fe', 'n2cu', 'n3zn', 'n4mo', 'n5ech5', 'n6sc', 'n7ech7',
  'tara', 'tweight', 'dweight', 'pweight',
  'userp', 'meta_user', 'turn'
];

// 3. Configuración de columnas especiales (Selects, ReadOnly, etc.)
const gridConfig = computed(() => {
  // Construir opciones para el select de Muestras
  const sampleOptions = samplesList.value.map(s => ({
    value: s.id,
    label: s.name || s.tag || `ID ${s.id}`
  }));

  return {
    0: { readOnly: true }, // ID no editable
    2: { type: 'select', options: sampleOptions }, // Columna 'Muestra' es un Select
    // Se pueden agregar más configuraciones aquí si es necesario
  };
});

// --- Computed Data para la Grilla ---
// Transforma los objetos de la API en Arrays para ExcelGrid
const gridData = computed(() => {
  return rawAssays.value.map(assay => {
    return colKeys.map(key => {
      // Manejo especial para campos anidados o nulos
      if (key === 'sample' && typeof assay[key] === 'object' && assay[key] !== null) {
        return assay[key].id; // Extraer ID si viene objeto completo
      }
      return assay[key] === null || assay[key] === undefined ? '' : assay[key];
    });
  });
});

// --- Carga de Datos ---
const loadData = async () => {
  loading.value = true;
  error.value = '';
  try {
    // Construir parámetros de consulta
    const params = {
      sample__equipment: 1 // FILTRO FIJO: Solo equipo ID 1
    };
    if (filterDate.value) {
      params.date = filterDate.value;
    }

    const [assaysRes, samplesRes] = await Promise.all([
      api.get('assays/', { params }),
      api.get('samples/', { params: { equipment: 1 } }) // Optimización: Cargar solo muestras del equipo 1 si es posible
    ]);

    rawAssays.value = Array.isArray(assaysRes.data) ? assaysRes.data : [];

    // Si la API de samples no soporta filtro, cargar todas (fallback)
    // Idealmente samplesRes.data debería venir filtrado o ser pocos
    samplesList.value = Array.isArray(samplesRes.data) ? samplesRes.data : [];

  } catch (err) {
    console.error("Error cargando datos:", err);
    error.value = "Error al cargar datos del servidor.";
  } finally {
    loading.value = false;
  }
};

// --- Guardado (Batch Update) ---
const handleSave = async (gridRows) => {
  loading.value = true;
  error.value = '';

  try {
    const promises = [];

    // Iterar sobre las filas de la grilla
    for (const row of gridRows) {
      // Convertir Array de grilla a Objeto API
      const payload = {};
      colKeys.forEach((key, index) => {
        let val = row[index];
        // Convertir strings vacíos a null para campos numéricos/fechas si es necesario
        if (val === '') val = null;
        payload[key] = val;
      });

      const id = payload.id;

      // Determinar si es Crear o Actualizar
      if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
        // UPDATE
        promises.push(api.put(`assays/${id}/`, payload));
      } else {
        // CREATE
        // Eliminar ID temporal o vacío para que el backend asigne uno nuevo
        delete payload.id;
        // Asegurar que tenga el equipo correcto indirectamente a través de la muestra
        // (El usuario debe seleccionar una muestra válida del equipo 1)
        promises.push(api.post('assays/', payload));
      }
    }

    // Ejecutar todas las peticiones
    await Promise.all(promises);
    
    // Recargar datos para ver cambios y nuevos IDs
    await loadData();
    alert('Cambios guardados exitosamente.');

  } catch (err) {
    console.error("Error guardando:", err);
    error.value = "Error al guardar cambios. Verifique los datos.";
  } finally {
    loading.value = false;
  }
};

// --- Eliminación ---
const handleDelete = async (idsToDelete) => {
  loading.value = true;
  try {
    const promises = idsToDelete.map(id => api.delete(`assays/${id}/`));
    await Promise.all(promises);
    await loadData();
    alert('Registros eliminados.');
  } catch (err) {
    console.error("Error eliminando:", err);
    error.value = "Error al eliminar registros.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.assays-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  height: 100%;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.date-filter {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.grid-wrapper {
  flex-grow: 1;
  overflow: hidden; /* El scroll lo maneja ExcelGrid */
}

.loading-text {
  text-align: center;
  font-size: 1.2rem;
  color: #666;
  margin-top: 2rem;
}

.feedback.error {
  color: red;
  background: #fee2e2;
  padding: 10px;
  border-radius: 4px;
}
</style>
