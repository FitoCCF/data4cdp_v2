<template>
  <div class="weekly-task-container">
    <div class="week-selector-bar">
      <label>Semana de Operación:</label>
      <input 
        type="number" 
        v-model="semanaActiva" 
        @change="cargarDatos" 
        class="week-input"
      />
      <span class="info-year">Año: {{ currentYear }}</span>
    </div>

    <ExcelGrid
      :title="'Planificación Semanal de Tareas'"
      :headers="headers"
      :data="gridData"
      :columnsConfig="dashboardConfig"
      @save="handleSaveFromGrid"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { api } from '../../api'; // Ajustado según tu árbol
import ExcelGrid from '../../components/ExcelGrid.vue'; // Subir dos niveles: genericViews -> views -> src/components

// ESTADO
const semanaActiva = ref(3289);
const currentYear = ref(2026);
const gridData = ref([]);

// CONFIGURACIÓN DE COLUMNAS
const headers = [
  'Planta', 'Sistema', 'Equipo', 'Tarea', 
  'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
];

// Mapeo para que las celdas de días (índices 4 al 10) sean selectores P/R
const dashboardConfig = {
  4: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  5: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  6: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  7: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  8: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  9: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
  10: { type: 'select', options: [{label: 'P', value: '1'}, {label: 'R', value: '2'}] },
};

// CARGA Y TRANSFORMACIÓN
const cargarDatos = async () => {
  try {
    const res = await api.get(`/weekly-tasks/?week=${semanaActiva.value}&year=${currentYear.value}`);
    const data = res.data;

    const mapa = {};
    data.forEach(t => {
      const key = `${t.planta}-${t.equipo}-${t.tarea_nombre}`;
      if (!mapa[key]) {
        // Estructura plana para ExcelGrid: [Planta, Sistema, Equipo, Tarea, Lun, Mar, Mie, Jue, Vie, Sab, Dom]
        mapa[key] = [t.planta, t.sistema, t.equipo, t.tarea_nombre, "", "", "", "", "", "", ""];
        // Atributo no enumerable para guardar los IDs de TaskP correspondientes a cada columna de día
        Object.defineProperty(mapa[key], '_taskIds', { value: {}, enumerable: false, writable: true });
      }
      
      const indicesDias = { "Lunes": 4, "Martes": 5, "Miércoles": 6, "Jueves": 7, "Viernes": 8, "Sábado": 9, "Domingo": 10 };
      const colIndex = indicesDias[t.day];
      
      if (colIndex) {
        // En la celda mostramos el ID del estado (para el select), 
        // pero incluimos al personal asignado como metadato si quieres que sea visible
        mapa[key][colIndex] = String(t.estado); 
        mapa[key]._taskIds[colIndex] = t.id;
      }
    });

    gridData.value = Object.values(mapa);
  } catch (error) {
    console.error("Error al cargar Weekly Tasks:", error);
  }
};

// GUARDADO DESDE EL COMPONENTE GENÉRICO
const handleSaveFromGrid = async (updatedLocalGrid) => {
  const updates = [];
  
  updatedLocalGrid.forEach(fila => {
    // Recorremos solo las columnas de los días (4-10)
    for (let i = 4; i <= 10; i++) {
      const taskId = fila._taskIds?.[i];
      if (taskId) {
        updates.push({
          id: taskId,
          estado_id: fila[i] // El valor actualizado del select en el grid
        });
      }
    }
  });

  if (updates.length === 0) return;

  try {
    await api.post('/weekly-tasks/bulk-update/', { updates });
    alert("Cambios guardados con éxito.");
    await cargarDatos();
  } catch (error) {
    alert("Error al sincronizar con el servidor.");
  }
};

onMounted(cargarDatos);
</script>

<style scoped>
.weekly-task-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.week-selector-bar {
  padding: 10px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  gap: 15px;
}
.week-input {
  width: 80px;
  padding: 4px;
  font-weight: bold;
}
.info-year {
  color: #6c757d;
  font-size: 0.9rem;
}
</style>
