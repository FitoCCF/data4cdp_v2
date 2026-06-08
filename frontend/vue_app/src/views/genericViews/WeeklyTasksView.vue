<template>
  <div class="weekly-task-container">
    <div class="week-selector-bar">
      <div class="week-controls">
        <label>Semana de Operación:</label>
        <input 
          type="number" 
          v-model="semanaActiva" 
          @change="cargarDatos" 
          class="week-input"
        />
        <span class="info-year">Año: {{ currentYear }}</span>
      </div>
      <button @click="exportToExcel" class="export-button">Descargar Excel</button>
    </div>

    <ExcelGrid
      :title="'Planificación Semanal de Tareas'"
      :headers="headers"
      :headerGroups="headerGroups"
      :data="gridData"
      :columnsConfig="dashboardConfig"
      @save="handleSaveFromGrid"
    />

    <!-- GRÁFICO COMBINADO SVG (PERSONAL Y ESTADÍSTICA DE ACTIVIDADES) -->
    <div v-if="chartDataReady && gridData.length > 0" class="chart-section">
      <h3 class="chart-title">ACTIVIDAD SEMANA {{ semanaActiva }}</h3>
      <div class="chart-wrapper">
        <svg viewBox="0 0 1000 450" class="svg-chart" width="100%" height="100%">
          <!-- Definición de gradientes y sombras -->
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#3b82f6" />
              <stop offset="100%" stop-color="#1d4ed8" />
            </linearGradient>
            <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15" />
            </filter>
          </defs>

          <!-- Líneas de cuadrícula horizontales (Líneas de 0 a 6 de personal) -->
          <line v-for="i in 7" :key="'grid-'+i"
                x1="80" :y1="380 - (i-1) * 50"
                x2="900" :y2="380 - (i-1) * 50"
                stroke="#e5e7eb" stroke-dasharray="4 4" stroke-width="1" />

          <!-- Eje Izquierdo (Cantidad de Personal 0 a 6) -->
          <g v-for="i in 7" :key="'left-axis-'+i">
            <text x="50" :y="384 - (i-1) * 50" class="axis-label text-left">{{ i-1 }}</text>
            <line x1="75" :y1="380 - (i-1) * 50" x2="80" :y2="380 - (i-1) * 50" stroke="#9ca3af" stroke-width="1.5" />
          </g>
          <text x="25" y="220" transform="rotate(-90 25 220)" class="axis-title-text" text-anchor="middle">Personal</text>

          <!-- Eje Derecho (Porcentaje de Actividades 0% a 100%) -->
          <g v-for="i in 6" :key="'right-axis-'+i">
            <text x="925" :y="384 - (i-1) * 60" class="axis-label text-right">{{ (i-1) * 20 }}%</text>
            <line x1="900" :y1="380 - (i-1) * 60" x2="905" :y2="380 - (i-1) * 60" stroke="#9ca3af" stroke-width="1.5" />
          </g>
          <text x="975" y="220" transform="rotate(90 975 220)" class="axis-title-text" text-anchor="middle">Estadistica Actividad Semanal</text>

          <!-- Línea Base del Eje X -->
          <line x1="80" y1="380" x2="900" y2="380" stroke="#9ca3af" stroke-width="2" />
          
          <!-- Líneas de Eje Y -->
          <line x1="80" y1="80" x2="80" y2="380" stroke="#9ca3af" stroke-width="1.5" />
          <line x1="900" y1="80" x2="900" y2="380" stroke="#9ca3af" stroke-width="1.5" />

          <!-- Etiquetas de los Días del Eje X -->
          <g v-for="(day, idx) in chartDaysShort" :key="'x-label-'+idx">
            <text :x="135 + idx * 110" y="405" class="day-label" text-anchor="middle">{{ day }}</text>
          </g>

          <!-- Barras de Personal Activo (Suma Día + Noche) -->
          <g v-for="(val, idx) in chartPersonnel" :key="'bar-group-'+idx">
            <rect :x="110 + idx * 110" :y="380 - val * 50"
                  width="50" :height="val * 50"
                  fill="url(#barGradient)" rx="4" filter="url(#shadow)" />
            <!-- Valor en la barra -->
            <text :x="135 + idx * 110" :y="380 - val * 50 - 8" class="bar-value" text-anchor="middle">{{ val }}</text>
          </g>

          <!-- Línea del Porcentaje de Actividades -->
          <path :d="linePathD" fill="none" stroke="#f97316" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          
          <!-- Marcadores de Diamante para la línea -->
          <g v-for="(pct, idx) in chartStats" :key="'dot-group-'+idx">
            <polygon :points="getDiamondPoints(135 + idx * 110, 380 - pct * 3.0)"
                     fill="#ffffff" stroke="#f97316" stroke-width="2.5" />
            <!-- Valor del porcentaje sobre el marcador -->
            <text :x="135 + idx * 110" :y="380 - pct * 3.0 - 12" class="line-value" text-anchor="middle">{{ pct }}%</text>
          </g>

          <!-- Leyenda del Gráfico -->
          <g transform="translate(320, 25)">
            <!-- Leyenda Personal -->
            <rect x="0" y="0" width="16" height="12" fill="url(#barGradient)" rx="2" />
            <text x="25" y="10" class="legend-text">Personal</text>

            <!-- Leyenda Línea -->
            <line x1="130" y1="6" x2="160" y2="6" stroke="#f97316" stroke-width="3" />
            <polygon points="145,2 149,6 145,10 141,6" fill="#ffffff" stroke="#f97316" stroke-width="2" />
            <text x="170" y="10" class="legend-text">Estadistica Actividad Semanal</text>
          </g>
        </svg>
      </div>
    </div>

    <!-- Agregamos el indicador visual de carga apoyado en el composable -->
    <div v-if="loading" class="loading-overlay">Cargando planificación...</div>
    <!-- Agregamos el banner de alerta en caso de fallos nativos de Axios -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, reactive, computed } from 'vue';
import { api } from '../../api'; // Ajustado según tu árbol
import ExcelGrid from '../../components/ExcelGrid.vue'; // Subir dos niveles: genericViews -> views -> src/components
import * as XLSX from 'xlsx';
// Importamos la utilidad global para el manejo de las peticiones
import { useApi } from '../../composables/useApi';

// --- LÓGICA DE NEGOCIO Y CÁLCULO DE SEMANA EXTENDIDA ---
const getExtendedWeek = (date) => {
  const target = new Date(date.valueOf());
  const dayNr = (date.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = target.valueOf();
  target.setMonth(0, 1);
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
  }
  const isoWeek = 1 + Math.ceil((firstThursday - target) / 604800000);
  const isoYear = target.getFullYear();
  const yearsSince1963 = isoYear - 1963;
  const accumulatedWeeks = yearsSince1963 * 52;
  return isoWeek + 6 + accumulatedWeeks;
};

// ESTADO INICIAL BASADO EN LA FECHA ACTUAL
const today = new Date();
const initialWeek = getExtendedWeek(today);
const initialYear = today.getFullYear();

// ESTADO
const semanaActiva = ref(initialWeek);
const currentYear = ref(initialYear);
const gridData = ref([]);
const diasSemana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

// Desestructuramos loading, error y la función ejecutora para nuestra API
const { loading, error, execute } = useApi();

// VARIABLES PARA EL GRÁFICO COMBINADO SVG
const chartDataReady = ref(false);
const chartPersonnel = ref([]);
const chartStats = ref([]);
const chartDays = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const chartDaysShort = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO'];

// ESTADO PARA EL RESUMEN DE PERSONAL (Usamos Sets para evitar usuarios duplicados en el mismo día)
const personalDia = reactive({ Lunes: new Set(), Martes: new Set(), Miércoles: new Set(), Jueves: new Set(), Viernes: new Set(), Sábado: new Set(), Domingo: new Set() });
const personalNoche = reactive({ Lunes: new Set(), Martes: new Set(), Miércoles: new Set(), Jueves: new Set(), Viernes: new Set(), Sábado: new Set(), Domingo: new Set() });

// CONFIGURACIÓN DE GRUPOS DE CABECERAS (SUPERIORES)
const headerGroups = ref([
  { label: 'Información de la Tarea', colspan: 5 },
  { label: 'Lunes', colspan: 2 },
  { label: 'Martes', colspan: 2 },
  { label: 'Miércoles', colspan: 2 },
  { label: 'Jueves', colspan: 2 },
  { label: 'Viernes', colspan: 2 },
  { label: 'Sábado', colspan: 2 },
  { label: 'Domingo', colspan: 2 }
]);

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
    // Calcular dinámicamente el año correspondiente a la semana activa (Fórmula inversa de base 1963)
    currentYear.value = 1963 + Math.floor((semanaActiva.value - 7) / 52);
    const res = await api.get(`/weekly-tasks/?week=${semanaActiva.value}&year=${currentYear.value}`);
    
    // Extraemos las listas del nuevo formato de respuesta
    const tasksData = res.data.tasks || res.data;
    const calendarData = res.data.calendar || [];

    // --- MAPEO DINÁMICO DE FECHAS A LA CABECERA ---
    const mapDiasFechas = {};
    tasksData.forEach(t => {
      if (t.dia_semana && (t.date || t.fecha)) mapDiasFechas[t.dia_semana] = t.date || t.fecha;
    });
    calendarData.forEach(c => {
      if (c.dia_semana && (c.date || c.fecha)) mapDiasFechas[c.dia_semana] = c.date || c.fecha;
    });

    // Inferir fechas faltantes usando un día base (por si la BD no envía tareas algún día)
    let fechaBaseStr = null;
    let indexBase = -1;
    for (let i = 0; i < diasSemana.length; i++) {
      if (mapDiasFechas[diasSemana[i]]) {
        fechaBaseStr = mapDiasFechas[diasSemana[i]];
        indexBase = i;
        break;
      }
    }

    if (fechaBaseStr && indexBase !== -1) {
      const [year, month, day] = fechaBaseStr.split('-').map(Number);
      const baseDate = new Date(year, month - 1, day);
      diasSemana.forEach((dia, index) => {
        if (!mapDiasFechas[dia]) {
          const newDate = new Date(baseDate);
          newDate.setDate(baseDate.getDate() + (index - indexBase));
          const y = newDate.getFullYear();
          const m = String(newDate.getMonth() + 1).padStart(2, '0');
          const d = String(newDate.getDate()).padStart(2, '0');
          mapDiasFechas[dia] = `${y}-${m}-${d}`;
        }
      });
    }

    // Reconstruir la cabecera dinámica de la semana
    const newHeaderGroups = [{ label: 'Información de la Tarea', colspan: 5 }];
    diasSemana.forEach(dia => {
      const fechaStr = mapDiasFechas[dia];
      let labelStr = dia;
      if (fechaStr) {
        const parts = fechaStr.split('-');
        if (parts.length === 3) {
          labelStr = `${dia} ${parts[1]}/${parts[2]}`; // Formato: "Día MM/DD"
        }
      }
      newHeaderGroups.push({ label: labelStr, colspan: 2 });
    });
    headerGroups.value = newHeaderGroups;

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
    const countTareasCompletadas = { Lunes: 0, Martes: 0, Miércoles: 0, Jueves: 0, Viernes: 0, Sábado: 0, Domingo: 0 };

    const mapa = {};
    tasksData.forEach(t => {
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

        // Incrementar si la tarea fue realizada (estado_id = 1)
        if (String(t.estado_id) === '1') {
          countTareasCompletadas[t.dia_semana]++;
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

    // --- LLENAR ESTADÍSTICAS DE PERSONAL BASADO EN EL CALENDARIO REAL ---
    calendarData.forEach(c => {
      if (c.usuario_nombre) {
        const isOvertime = c.horas_extra && Number(c.horas_extra) > 0;
        const overtimeSuffix = isOvertime ? ' (Trabajo en Descanso)' : '';
        const fullName = `${c.usuario_nombre} ${c.usuario_apellido || ''}${overtimeSuffix}`.trim();
        const strTurno = String(c.turno || '').toUpperCase();
        const dia = c.dia_semana;
        
        // Si el calendario marca descanso 'X', ignoramos a la persona ese día
        if (strTurno === 'X' || !strTurno) return;

        // Clasificamos el turno
        const isNoche = (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE'));
        const isAmbos = (strTurno === 'AB' || strTurno === 'DN');
        
        if (isAmbos) {
          if (personalDia[dia]) personalDia[dia].add(fullName);
          if (personalNoche[dia]) personalNoche[dia].add(fullName);
        } else if (isNoche) {
          if (personalNoche[dia]) personalNoche[dia].add(fullName);
        } else {
          if (personalDia[dia]) personalDia[dia].add(fullName);
        }
      }
    });

    // --- GENERAR FILAS DE ESTADÍSTICAS / RESUMEN EN EL GRID ---
    const totalSemanalActividades = Object.values(countTareasTotal).reduce((a, b) => a + b, 0);
    const totalSemanalCompletadas = Object.values(countTareasCompletadas).reduce((a, b) => a + b, 0);
    const porcentajeSemanal = totalSemanalActividades > 0 ? Math.round((totalSemanalCompletadas / totalSemanalActividades) * 100) : 0;

    const createSummaryRow = (label, dataFn, useColspan = false) => {
      // Las 5 primeras columnas son de información, dejamos las 4 primeras vacías y usamos la columna "Tarea" (índice 4) para el label.
      const row = ["", "", "", "", label];
      diasSemana.forEach(dia => {
        const val = dataFn(dia);
        if (useColspan) {
          if (typeof val === 'object' && val !== null) {
            row.push(val);
          } else {
            row.push({ value: val, colspan: 2 }); // Celda de origen que ocupa 2 columnas
          }
          row.push(null);                      // Celda omitida por la combinación
        } else {
          row.push(val);
          row.push("");
        }
      });
      Object.defineProperty(row, 'isSummary', { value: true, enumerable: false, writable: true });
      Object.defineProperty(row, '_taskIds', { value: {}, enumerable: false, writable: true });
      return row;
    };

    const emptyRow = createSummaryRow("", () => ""); // Espaciador visual
    const rowActDia = createSummaryRow("Actividades de Día", dia => countTareasDia[dia]);
    const rowActNoche = createSummaryRow("Actividades de Noche", dia => countTareasNoche[dia]);
    const rowActAB = createSummaryRow("Actividades Turno AB", dia => countTareasAB[dia]);
    const rowActTotal = createSummaryRow(`Cantidad de Actividades Diarias (Total: ${totalSemanalActividades})`, dia => countTareasTotal[dia]);
    const rowActCompleted = createSummaryRow(`Actividades Completadas (Total: ${totalSemanalCompletadas})`, dia => countTareasCompletadas[dia]);
    const rowActStats = createSummaryRow(`Estadística de Actividades (Global: ${porcentajeSemanal}%)`, dia => {
      const total = countTareasTotal[dia];
      const completed = countTareasCompletadas[dia];
      return total > 0 ? Math.round((completed / total) * 100) + "%" : "0%";
    });
    
    const countDiaRow = createSummaryRow("Personal Turno Día", dia => {
      const namesList = Array.from(personalDia[dia]).join('\n');
      const count = personalDia[dia].size;
      const hasOvertime = Array.from(personalDia[dia]).some(name => name.includes('(Trabajo en Descanso)'));
      return { value: count, tooltip: namesList || 'Sin personal asignado', hasOvertime, colspan: 2 };
    }, true);
    
    const countNocheRow = createSummaryRow("Personal Turno Noche", dia => {
      const namesList = Array.from(personalNoche[dia]).join('\n');
      const count = personalNoche[dia].size;
      const hasOvertime = Array.from(personalNoche[dia]).some(name => name.includes('(Trabajo en Descanso)'));
      return { value: count, tooltip: namesList || 'Sin personal asignado', hasOvertime, colspan: 2 };
    }, true);

    const rowTotalPersonal = createSummaryRow("Total Personal", dia => personalDia[dia].size + personalNoche[dia].size, true);

    newData.push(
      emptyRow, 
      rowActDia, 
      rowActNoche, 
      rowActAB, 
      rowActTotal, 
      rowActCompleted,
      rowActStats,
      countDiaRow, 
      countNocheRow,
      rowTotalPersonal
    );

    // Cargar los datos para el gráfico combinado SVG
    chartPersonnel.value = diasSemana.map(dia => personalDia[dia].size + personalNoche[dia].size);
    chartStats.value = diasSemana.map(dia => {
      const total = countTareasTotal[dia];
      const completed = countTareasCompletadas[dia];
      return total > 0 ? Math.round((completed / total) * 100) : 0;
    });
    chartDataReady.value = true;

    gridData.value = newData;
  // Registramos un string para que actualice la variable 'error.value' nativamente si cae
  }, 'Error al cargar Weekly Tasks desde el servidor.');
};

// PROPIEDADES COMPUTADAS Y MÉTODOS PARA EL TRAZADO DEL GRÁFICO SVG
const linePathD = computed(() => {
  if (chartStats.value.length === 0) return '';
  return chartStats.value.map((pct, idx) => {
    const x = 135 + idx * 110;
    const y = 380 - pct * 3.0; // Escalado de 0% a 100% (y = 380 a y = 80)
    return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');
});

const getDiamondPoints = (x, y) => {
  const size = 5;
  return `${x},${y - size} ${x + size},${y} ${x},${y + size} ${x - size},${y}`;
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
      await api.post('/weekly-tasks/', { updates });
      alert("Cambios guardados con éxito.");
      await cargarDatos();
    });
  } catch (err) {
    // Mantenemos la alerta manual del programador si el guardado falla
    alert("Error al sincronizar con el servidor.");
  }
};

const exportToExcel = () => {
  const wb = XLSX.utils.book_new();
  const wsData = [];

  // 1. Fila de Grupos de Encabezado
  const headerGroupRow = [];
  headerGroups.value.forEach(g => {
    headerGroupRow.push(g.label);
    // Rellenar celdas vacías para el colspan
    for (let i = 1; i < g.colspan; i++) {
      headerGroupRow.push("");
    }
  });
  wsData.push(headerGroupRow);

  // 2. Fila de Encabezados
  wsData.push(headers);

  // 3. Filas de Datos
  gridData.value.forEach(row => {
    const newRow = row.map(cell => (typeof cell === 'string' ? cell : cell));
    wsData.push(newRow);
  });

  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // 4. Combinar celdas para los grupos de encabezado
  ws['!merges'] = [];
  let currentCol = 0;
  headerGroups.value.forEach(group => {
    if (group.colspan > 1) {
      ws['!merges'].push({ s: { r: 0, c: currentCol }, e: { r: 0, c: currentCol + group.colspan - 1 } });
    }
    currentCol += group.colspan;
  });

  // 5. Ancho de Columnas
  ws['!cols'] = [
    { wch: 15 }, { wch: 15 }, { wch: 15 }, { wch: 25 }, { wch: 35 }, // Info Tarea
    ...Array(14).fill({ wch: 12 }) // Columnas de Días
  ];

  // 6. Aplicar Estilos
  gridData.value.forEach((row, rowIndex) => {
    const excelRowIndex = rowIndex + 2; // +2 por las dos filas de encabezado

    if (row.isSummary) {
      for (let c = 0; c < row.length; c++) {
        const cellAddress = XLSX.utils.encode_cell({ r: excelRowIndex, c });
        if (ws[cellAddress]) {
          ws[cellAddress].s = { font: { bold: true }, alignment: { wrapText: true, vertical: 'top' } };
        }
      }
      return; // No aplicar más estilos a filas de resumen
    }

    // Estilos para Turno y Estado
    for (let i = 0; i < 7; i++) {
      const turnoCol = 5 + i * 2;
      const estadoCol = 6 + i * 2;

      const turnoValue = row[turnoCol];
      const estadoValue = row[estadoCol];

      // Estilo de Turno
      const turnoCellAddress = XLSX.utils.encode_cell({ r: excelRowIndex, c: turnoCol });
      if (ws[turnoCellAddress] && turnoValue) {
        let turnoStyle = { font: { bold: true } };
        if (turnoValue === 'D') turnoStyle.fill = { fgColor: { rgb: "FFFF00" } }; // Amarillo
        else if (turnoValue === 'N') turnoStyle.fill = { fgColor: { rgb: "ADD8E6" } }; // Azul claro
        else if (turnoValue === 'DN') turnoStyle.fill = { fgColor: { rgb: "90EE90" } }; // Verde claro
        ws[turnoCellAddress].s = turnoStyle;
      }

      // Estilo de Estado
      const estadoCellAddress = XLSX.utils.encode_cell({ r: excelRowIndex, c: estadoCol });
      if (ws[estadoCellAddress] && estadoValue) {
        let estadoStyle = { font: { bold: true } };
        if (estadoValue === '1') { // Realizado
          ws[estadoCellAddress].v = 'R';
          estadoStyle.fill = { fgColor: { rgb: "C6EFCE" } };
          estadoStyle.font.color = { rgb: "006100" };
        } else if (estadoValue === '2') { // Pendiente
          ws[estadoCellAddress].v = 'P';
          estadoStyle.fill = { fgColor: { rgb: "FFC7CE" } };
          estadoStyle.font.color = { rgb: "9C0006" };
        }
        ws[estadoCellAddress].s = estadoStyle;
      }
    }
  });

  // 7. Generar y Descargar Archivo
  XLSX.utils.book_append_sheet(wb, ws, "Planificación Semanal");
  XLSX.writeFile(wb, `Planificacion_Semana_${semanaActiva.value}_${currentYear.value}.xlsx`);
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
  justify-content: space-between;
}
.week-controls {
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
.export-button {
  padding: 6px 12px;
  background-color: #198754; /* Verde Bootstrap */
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.export-button:hover {
  background-color: #157347;
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

/* Estilos personalizados para las celdas de Turno y Estado sin alterar ExcelGrid globalmente */
:deep(.cell:not(.summary-cell)[data-col-index="5"]),
:deep(.cell:not(.summary-cell)[data-col-index="7"]),
:deep(.cell:not(.summary-cell)[data-col-index="9"]),
:deep(.cell:not(.summary-cell)[data-col-index="11"]),
:deep(.cell:not(.summary-cell)[data-col-index="13"]),
:deep(.cell:not(.summary-cell)[data-col-index="15"]),
:deep(.cell:not(.summary-cell)[data-col-index="17"]) {
  text-align: center;
}

:deep(.cell:not(.summary-cell)[data-value="D"]) {
  background-color: #fef08a !important; /* Amarillo */
  color: #854d0e !important;
  font-weight: bold;
}
:deep(.cell:not(.summary-cell)[data-value="N"]) {
  background-color: #dbeafe !important; /* Azul */
  color: #1e40af !important;
  font-weight: bold;
}
:deep(.cell:not(.summary-cell)[data-value="DN"]) {
  background-color: #ccdbe7 !important; /* Verde */
  color: #065f46 !important;
  font-weight: bold;
}

:deep(.cell:not(.summary-cell)[data-col-index="6"]),
:deep(.cell:not(.summary-cell)[data-col-index="8"]),
:deep(.cell:not(.summary-cell)[data-col-index="10"]),
:deep(.cell:not(.summary-cell)[data-col-index="12"]),
:deep(.cell:not(.summary-cell)[data-col-index="14"]),
:deep(.cell:not(.summary-cell)[data-col-index="16"]),
:deep(.cell:not(.summary-cell)[data-col-index="18"]) {
  text-align: center;
}

:deep(.cell:not(.summary-cell)[data-value="1"]) {
  background-color: #c6efce !important; /* Realizado (Verde) */
  color: #006100 !important;
  font-weight: bold;
}
:deep(.cell:not(.summary-cell)[data-value="2"]) {
  background-color: #ffc7ce !important; /* Pendiente (Rojo) */
  color: #9c0006 !important;
  font-weight: bold;
}

/* Permitir que el selector dropdown herede los colores de la celda */
:deep(.cell:not(.summary-cell) .cell-select) {
  background-color: transparent !important;
  color: inherit !important;
  font-weight: inherit !important;
  text-align: center;
  border: none;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

/* --- ESTILOS DEL GRÁFICO COMBINADO SVG --- */
.chart-section {
  margin-top: 30px;
  margin-bottom: 20px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

.chart-title {
  margin: 0 0 20px 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #3b82f6;
  display: inline-block;
  padding-bottom: 4px;
}

.chart-wrapper {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
}

.svg-chart {
  display: block;
}

.axis-label {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  fill: #6b7280;
  font-weight: 500;
}

.axis-title-text {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  fill: #374151;
  font-weight: 600;
  letter-spacing: 0.025em;
}

.day-label {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  fill: #4b5563;
  font-weight: 600;
}

.bar-value {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  fill: #1d4ed8;
  font-weight: 700;
}

.line-value {
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  fill: #ea580c;
  font-weight: 700;
}

.legend-text {
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  fill: #4b5563;
  font-weight: 600;
}
</style>
