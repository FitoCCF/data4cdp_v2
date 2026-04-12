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
      :headerGroups="headerGroups"
      :data="gridData"
      :columnsConfig="dashboardConfig"
      @save="handleSaveFromGrid"
    />

    <!-- Agregamos el indicador visual de carga apoyado en el composable -->
    <div v-if="loading" class="loading-overlay">Cargando planificación...</div>
    <!-- Agregamos el banner de alerta en caso de fallos nativos de Axios -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive } from 'vue';
import { api } from '../../api'; // Ajustado según tu árbol
import ExcelGrid from '../../components/ExcelGrid.vue'; // Subir dos niveles: genericViews -> views -> src/components
// Importamos la utilidad global para el manejo de las peticiones
import { useApi } from './useApi';

// ESTADO
const semanaActiva = ref(3289);
const currentYear = ref(2026);
const gridData = ref([]);
const diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

// Desestructuramos loading, error y la función ejecutora para nuestra API
const { loading, error, execute } = useApi();

// ESTADO PARA EL RESUMEN DE PERSONAL (Usamos Sets para evitar usuarios duplicados en el mismo día)
const personalDia = reactive({ Lunes: new Set(), Martes: new Set(), Miércoles: new Set(), Jueves: new Set(), Viernes: new Set(), Sábado: new Set(), Domingo: new Set() });
const personalNoche = reactive({ Lunes: new Set(), Martes: new Set(), Miércoles: new Set(), Jueves: new Set(), Viernes: new Set(), Sábado: new Set(), Domingo: new Set() });

// CONFIGURACIÓN DE GRUPOS DE CABECERAS (SUPERIORES)
const headerGroups = [
  { label: 'Información de la Tarea', colspan: 5 },
  { label: 'Lunes', colspan: 2 },
  { label: 'Martes', colspan: 2 },
  { label: 'Miércoles', colspan: 2 },
  { label: 'Jueves', colspan: 2 },
  { label: 'Viernes', colspan: 2 },
  { label: 'Sábado', colspan: 2 },
  { label: 'Domingo', colspan: 2 }
];

// CONFIGURACIÓN DE COLUMNAS
const headers = [
  'Planta', 'Área', 'Sistema', 'Equipo', 'Tarea',
  'Turno', 'Estado', 'Turno', 'Estado', 
  'Turno', 'Estado', 'Turno', 'Estado', 
  'Turno', 'Estado', 'Turno', 'Estado', 
  'Turno', 'Estado'
];

// Mapeo para que las celdas de Estado sean selectores P/R
const dashboardConfig = {
  6: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  8: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  10: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  12: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  14: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  16: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
  18: { type: 'select', options: [{label: 'R', value: '1'}, {label: 'P', value: '2'}] },
};

// CARGA Y TRANSFORMACIÓN
const cargarDatos = async () => {
  // Envolvemos el cuerpo completo en execute para que lance la vista de "Cargando planificación..."
  await execute(async () => {
    const res = await api.get(`/weekly-tasks/?week=${semanaActiva.value}&year=${currentYear.value}`);
    const data = res.data;

    // Limpiamos el personal antes de procesar
    diasSemana.forEach(dia => {
      personalDia[dia].clear();
      personalNoche[dia].clear();
    });

    // Objetos para contar la cantidad de tareas por turno y día
    const countTareasDia = { Lunes: 0, Martes: 0, Miércoles: 0, Jueves: 0, Viernes: 0, Sábado: 0, Domingo: 0 };
    const countTareasNoche = { Lunes: 0, Martes: 0, Miércoles: 0, Jueves: 0, Viernes: 0, Sábado: 0, Domingo: 0 };
    const countTareasAB = { Lunes: 0, Martes: 0, Miércoles: 0, Jueves: 0, Viernes: 0, Sábado: 0, Domingo: 0 };
    const countTareasTotal = { Lunes: 0, Martes: 0, Miércoles: 0, Jueves: 0, Viernes: 0, Sábado: 0, Domingo: 0 };

    const mapa = {};
    data.forEach(t => {
      // LLAVE BASE: Planta, Área, Sistema, Equipo y Tarea
      const baseKey = `${t.planta}-${t.area}-${t.sistema}-${t.equipo}-${t.tarea_descripcion}`;
      
      if (!mapa[baseKey]) {
        mapa[baseKey] = [];
      }
      
      // Actualizar contadores de tareas por turno (incluye turno AB)
      if (t.dia_semana && countTareasTotal[t.dia_semana] !== undefined) {
        countTareasTotal[t.dia_semana]++;
        const strTurno = String(t.turno || '').toUpperCase();
        if (strTurno === 'AB' || strTurno === 'DN') {
          countTareasAB[t.dia_semana]++;
        } else if (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE')) {
          countTareasNoche[t.dia_semana]++;
        } else {
          countTareasDia[t.dia_semana]++;
        }
      }

      // Acumular usuarios para el panel inferior
      if (t.usuarios_asignados) {
        const users = t.usuarios_asignados.split(',').map(u => u.trim()).filter(Boolean);
        const strTurno = String(t.turno || '').toUpperCase();
        
        // Clasificamos el turno
        const isNoche = (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE'));
        const isAmbos = (strTurno === 'AB' || strTurno === 'DN');
        
        if (isAmbos) {
          // Si es un turno de 24h, el personal trabaja en ambos
          users.forEach(u => { personalDia[t.dia_semana].add(u); personalNoche[t.dia_semana].add(u); });
        } else if (isNoche) {
          users.forEach(u => personalNoche[t.dia_semana].add(u));
        } else {
          // Por defecto asume turno Día (A, D)
          users.forEach(u => personalDia[t.dia_semana].add(u));
        }
      }

      const indicesDias = { 
        "Lunes": { t: 5, e: 6 }, 
        "Martes": { t: 7, e: 8 }, 
        "Miércoles": { t: 9, e: 10 }, 
        "Jueves": { t: 11, e: 12 }, 
        "Viernes": { t: 13, e: 14 }, 
        "Sábado": { t: 15, e: 16 }, 
        "Domingo": { t: 17, e: 18 } 
      };
      const colIndices = indicesDias[t.dia_semana];
      
      if (colIndices) {
        // Transformar visualmente 'A' a 'D' (Día) y 'B' a 'N' (Noche) si viene así de la BD
        let turnoLabel = t.turno || '';
        if (t.turno === 'A') turnoLabel = 'D';
        else if (t.turno === 'B') turnoLabel = 'N';
        else if (t.turno === 'AB') turnoLabel = 'DN';
        

        // Buscar una fila existente para esta tarea donde el día esté vacío
        let targetRow = mapa[baseKey].find(row => row[colIndices.e] === "");

        // Si no hay fila disponible (ej. porque el mismo día tiene turno Día y Noche), creamos una nueva fila
        if (!targetRow) {
          const equipoDisplay = t.equipo_desc ? `${t.equipo || ""} ${t.equipo_desc}`.trim() : (t.equipo || "");
          const tareaDisplay = t.tarea_detalle || t.tarea_descripcion || "";

          targetRow = [
            t.planta || "", t.area || "", t.sistema || "", equipoDisplay, tareaDisplay,
            "", "", "", "", "", "", "", "", "", "", "", "", "", ""
          ];
          Object.defineProperty(targetRow, '_taskIds', { value: {}, enumerable: false, writable: true });
          mapa[baseKey].push(targetRow);
        }

        targetRow[colIndices.t] = turnoLabel; 
        targetRow[colIndices.e] = String(t.estado_id); 
        targetRow._taskIds[colIndices.e] = t.id;
      }
    });

    const newData = [];
    Object.values(mapa).forEach(rows => newData.push(...rows));

    // --- GENERAR FILAS DE ESTADÍSTICAS / RESUMEN EN EL GRID ---
    const createSummaryRow = (label, dataFn) => {
      // Las 5 primeras columnas son de información, dejamos las 4 primeras vacías y usamos la columna "Tarea" (índice 4) para el label.
      const row = ["", "", "", "", label];
      diasSemana.forEach(dia => {
        row.push(dataFn(dia)); // Se coloca en la celda del Turno
        row.push("");          // Se deja vacía la celda del Estado
      });
      Object.defineProperty(row, 'isSummary', { value: true, enumerable: false, writable: true });
      Object.defineProperty(row, '_taskIds', { value: {}, enumerable: false, writable: true });
      return row;
    };

    const emptyRow = createSummaryRow("", () => ""); // Espaciador visual
    const rowActDia = createSummaryRow("Actividades de Día", dia => countTareasDia[dia]);
    const rowActNoche = createSummaryRow("Actividades de Noche", dia => countTareasNoche[dia]);
    const rowActAB = createSummaryRow("Actividades Turno AB", dia => countTareasAB[dia]);
    const rowActTotal = createSummaryRow("Total de Actividades", dia => countTareasTotal[dia]);
    
    // Funciones auxiliares para detectar personal duplicado (fatiga/doble turno)
    const getNombresDia = (dia) => {
      return Array.from(personalDia[dia]).map(u => {
        // Si el trabajador también está registrado en la noche de este mismo día, lanzamos alerta
        return personalNoche[dia].has(u) ? `⚠️ ${u} (Doble)` : u;
      }).join('\n') || '-';
    };

    const getNombresNoche = (dia) => {
      return Array.from(personalNoche[dia]).map(u => {
        return personalDia[dia].has(u) ? `⚠️ ${u} (Doble)` : u;
      }).join('\n') || '-';
    };

    const countDiaRow = createSummaryRow("Cant. Personal Día", dia => personalDia[dia].size || 0);
    const namesDiaRow = createSummaryRow("Nombres Personal Día", getNombresDia);
    const countNocheRow = createSummaryRow("Cant. Personal Noche", dia => personalNoche[dia].size || 0);
    const namesNocheRow = createSummaryRow("Nombres Personal Noche", getNombresNoche);

    newData.push(
      emptyRow, 
      rowActDia, 
      rowActNoche, 
      rowActAB, 
      rowActTotal, 
      countDiaRow, 
      namesDiaRow, 
      countNocheRow, 
      namesNocheRow
    );

    gridData.value = newData;
  // Registramos un string para que actualice la variable 'error.value' nativamente si cae
  }, 'Error al cargar Weekly Tasks desde el servidor.');
};

// GUARDADO DESDE EL COMPONENTE GENÉRICO
const handleSaveFromGrid = async (updatedLocalGrid) => {
  const updates = [];
  
  updatedLocalGrid.forEach(fila => {
    if (fila.isSummary) return; // Ignorar las filas de estadísticas al guardar

    // Recorremos las columnas de estado de los días
    const columnasEstado = [6, 8, 10, 12, 14, 16, 18];
    for (let i of columnasEstado) {
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
    // Envolvemos el guardado masivo para bloquear la UI mientras dure la red
    await execute(async () => {
      await api.post('/weekly-tasks/bulk-update/', { updates });
      alert("Cambios guardados con éxito.");
      await cargarDatos();
    });
  } catch (err) {
    // Mantenemos la alerta manual del programador si el guardado falla
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

/* Permitir saltos de línea (pre-wrap) en las celdas de resumen dentro del ExcelGrid */
:deep(.summary-cell) {
  white-space: pre-wrap !important;
}

/* Estilos inyectados para el overlay de carga y error */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 1.2rem;
  z-index: 100;
}
.error-message {
  color: red;
  text-align: center;
  margin-top: 10px;
}
</style>
