<template>
  <div class="schedule-view-container">
    <div class="header-actions">
      <h2>Calendario de Rotación por Personal</h2>
      <p class="subtitle">{{ dateRangeText }}</p>
    </div>

    <!-- 
      Barra de navegación de semanas directamente en GroupScheduleView.vue 
    -->
    <div class="navigation-bar">
      <div class="nav-buttons">
        <button 
          class="btn btn-gray btn-sm" 
          @click="shiftWeeks(-4)" 
          :disabled="startIndex <= 0"
          title="Retroceder 4 semanas"
        >
          &laquo;&laquo; 4 Semanas
        </button>
        <button 
          class="btn btn-blue btn-sm" 
          @click="shiftWeeks(-1)" 
          :disabled="startIndex <= 0"
          title="Retroceder 1 semana"
        >
          &laquo; 1 Semana
        </button>
        <button 
          class="btn btn-blue btn-sm" 
          @click="shiftWeeks(1)" 
          :disabled="startIndex >= maxStartIndex"
          title="Avanzar 1 semana"
        >
          1 Semana &raquo;
        </button>
        <button 
          class="btn btn-gray btn-sm" 
          @click="shiftWeeks(4)" 
          :disabled="startIndex >= maxStartIndex"
          title="Avanzar 4 semanas"
        >
          4 Semanas &raquo;&raquo;
        </button>
      </div>
      <div class="range-info">
        <span>Mostrando días {{ startIndex + 1 }} al {{ Math.min(allUniqueDates.length, startIndex + 28) }} (Total: {{ allUniqueDates.length }} días)</span>
      </div>
    </div>

    <!-- 
      Componente ExcelGrid pasándole las cabeceras y los datos reactivos del personal
    -->
    <div class="grid-wrapper">
      <ExcelGrid 
        title="Rotación de Turnos por Personal (4 Semanas)"
        :headers="gridColumns" 
        :headerGroups="gridHeaderGroups"
        :columnsConfig="columnsConfig"
        :data="gridData" 
      />
      
      <!-- Overlay de carga y mensajes de error -->
      <div v-if="loading" class="loading-overlay">Cargando datos del calendario y personal...</div>
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
// Subimos un nivel en la estructura para alcanzar components/
import ExcelGrid from '../../components/ExcelGrid.vue'; 
import { api } from '../../api';
// Se importa el composable para estandarizar las conexiones API
import { useApi } from '../../composables/useApi';

// Datos originales de BD cargados en memoria
const allUniqueDates = ref([]);
const allUsers = ref([]);
const dateToWeekMap = ref({});
const userExceptionMap = ref({});
const groupMap = ref({});

// Índice de inicio de la ventana deslizante (en días)
const startIndex = ref(0);

// Nombres de los meses para el título
const monthNames = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

// Sustituimos las variables manuales por las que expone el composable
const { loading, error, execute } = useApi();

// Feriados nacionales en Perú aplicados al rango (1 de Mayo: Trabajo, 7 de Junio: Bandera)
const holidays = ['05-01', '06-07'];

// Determina si una fecha dada en formato YYYY-MM-DD es feriado nacional
const isHoliday = (dateStr) => {
  return holidays.some(h => dateStr.endsWith(`-${h}`));
};

// Helper de cálculo de semana extendida (inversa de base 1963)
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

// Fecha máxima de inicio de la ventana para evitar rebasar la longitud de los datos
const maxStartIndex = computed(() => {
  return Math.max(0, allUniqueDates.value.length - 28);
});

// Desplaza la ventana de fechas hacia adelante o atrás por semanas
const shiftWeeks = (numWeeks) => {
  const days = numWeeks * 7;
  const newIndex = startIndex.value + days;
  startIndex.value = Math.max(0, Math.min(maxStartIndex.value, newIndex));
};

// Ventana de 28 días (4 semanas) seleccionada de forma reactiva
const projectedDates = computed(() => {
  if (allUniqueDates.value.length === 0) return [];
  return allUniqueDates.value.slice(startIndex.value, startIndex.value + 28);
});

// Rango de fechas legible para el subtítulo de la vista
const dateRangeText = computed(() => {
  const dates = projectedDates.value;
  if (dates.length === 0) return 'Proyección de 4 semanas';
  const format = (dStr) => {
    const [y, m, d] = dStr.split('-');
    return `${parseInt(d)}/${parseInt(m)}/${y}`;
  };
  return `Proyección de 4 semanas (${format(dates[0])} - ${format(dates[dates.length - 1])})`;
});

// Cabeceras bidimensionales reactivas (Meses y Semanas agrupados por Colspan)
const gridHeaderGroups = computed(() => {
  const dates = projectedDates.value;
  if (dates.length === 0) return [];

  // 1. Agrupar por Meses
  const monthGroups = [];
  let currentMonth = null;
  let currentMonthSpan = 0;

  dates.forEach(dateStr => {
    const [, m] = dateStr.split('-');
    const monthLabel = monthNames[parseInt(m) - 1];
    
    if (currentMonth === null) {
      currentMonth = monthLabel;
      currentMonthSpan = 1;
    } else if (currentMonth === monthLabel) {
      currentMonthSpan++;
    } else {
      monthGroups.push({ label: currentMonth, colspan: currentMonthSpan });
      currentMonth = monthLabel;
      currentMonthSpan = 1;
    }
  });
  if (currentMonth !== null) {
    monthGroups.push({ label: currentMonth, colspan: currentMonthSpan });
  }

  // 2. Agrupar por Semanas de Operación
  const weekGroups = [];
  let currentWeek = null;
  let currentWeekSpan = 0;

  dates.forEach(dateStr => {
    let weekNum = dateToWeekMap.value[dateStr];
    if (!weekNum) {
      const [y, m, d] = dateStr.split('-');
      weekNum = getExtendedWeek(new Date(parseInt(y), parseInt(m) - 1, parseInt(d)));
    }
    const weekLabel = `Semana   ${weekNum}`;
    
    if (currentWeek === null) {
      currentWeek = weekLabel;
      currentWeekSpan = 1;
    } else if (currentWeek === weekLabel) {
      currentWeekSpan++;
    } else {
      weekGroups.push({ label: currentWeek, colspan: currentWeekSpan });
      currentWeek = weekLabel;
      currentWeekSpan = 1;
    }
  });
  if (currentWeek !== null) {
    weekGroups.push({ label: currentWeek, colspan: currentWeekSpan });
  }

  return [
    [{ label: '', colspan: 1 }, ...monthGroups],
    [{ label: '', colspan: 1 }, ...weekGroups]
  ];
});

// Cabecera principal reactiva de días/fechas (Fila 3)
const gridColumns = computed(() => {
  const dates = projectedDates.value;
  if (dates.length === 0) return ['Personal'];
  const cols = ['Personal'];
  const dayNames = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];

  dates.forEach(dateStr => {
    const [y, m, d] = dateStr.split('-');
    const dateObj = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
    const dayLabel = dayNames[dateObj.getDay()];
    cols.push(`${dayLabel}\n${parseInt(m)}/${parseInt(d)}`);
  });

  return cols;
});

// Configuración de estilos y clases en las cabeceras individuales de la grilla
const columnsConfig = computed(() => {
  const dates = projectedDates.value;
  const config = {};

  dates.forEach((dateStr, idx) => {
    const colIndex = idx + 1; // La columna 0 es 'Personal'
    
    // Agregamos la clase 'hide-filter' a todas las columnas de fechas para ocultar su filtro vía CSS
    let headerClass = 'hide-filter';
    let headerStyle = {};

    if (isHoliday(dateStr)) {
      headerStyle = {
        backgroundColor: '#b91c1c',
        color: '#ffffff',
        fontWeight: 'bold'
      };
    }

    config[colIndex] = {
      headerClass,
      headerStyle
    };
  });

  return config;
});

// Datos bidimensionales reactivos de turnos mapeados por personal
const gridData = computed(() => {
  const dates = projectedDates.value;
  const users = allUsers.value;
  if (dates.length === 0 || users.length === 0) return [];

  return users.map(user => {
    const fullName = `${user.nombre} ${user.apellido}`;
    const rowData = [fullName];

    dates.forEach(dateStr => {
      let turn = 'x';

      // 1. Priorizar excepciones individuales
      if (userExceptionMap.value[user.id] && userExceptionMap.value[user.id][dateStr] !== undefined) {
        turn = userExceptionMap.value[user.id][dateStr];
      } 
      // 2. Si no hay excepción, usar el turno del grupo del usuario
      else if (user.group) {
        const userGroupId = (typeof user.group === 'object') ? user.group.id : user.group;
        if (groupMap.value[userGroupId] && groupMap.value[userGroupId][dateStr] !== undefined) {
          turn = groupMap.value[userGroupId][dateStr];
        }
      }

      rowData.push(turn);
    });

    return rowData;
  });
});

// Carga la información de la base de datos
const loadCalendarData = async () => {
  await execute(async () => {
    const [calendarsResponse, usersResponse] = await Promise.all([
      api.get('calendars/', { params: { page_size: 10000 } }),
      api.get('users/', { params: { page_size: 1000 } })
    ]);

    const calendars = calendarsResponse.data.results || calendarsResponse.data;
    const users = usersResponse.data.results || usersResponse.data;

    if (!Array.isArray(users) || users.length === 0) {
      error.value = "No se encontraron registros de personal en la base de datos.";
      return;
    }

    if (!Array.isArray(calendars) || calendars.length === 0) {
      error.value = "No se encontraron registros de turnos de calendario en la base de datos.";
      return;
    }

    // Guardar listado de usuarios
    allUsers.value = users;

    // Extraer y ordenar cronológicamente todas las fechas únicas
    allUniqueDates.value = [...new Set(calendars.map(item => item.date))].sort();

    // Guardar mapa de fechas a semanas operativas
    const dateToWeek = {};
    calendars.forEach(item => {
      if (item.date && item.week) {
        dateToWeek[item.date] = item.week;
      }
    });
    dateToWeekMap.value = dateToWeek;

    // Construir mapas de búsqueda rápidos para excepciones y calendarios grupales
    const userExceptions = {};
    const groupCalendars = {};

    calendars.forEach(item => {
      const dateStr = item.date;
      if (!dateStr) return;

      if (item.user) {
        const uId = (typeof item.user === 'object') ? item.user.id : item.user;
        if (!userExceptions[uId]) {
          userExceptions[uId] = {};
        }
        userExceptions[uId][dateStr] = item.turn;
      } else if (item.group) {
        const gId = (typeof item.group === 'object') ? item.group.id : item.group;
        if (!groupCalendars[gId]) {
          groupCalendars[gId] = {};
        }
        groupCalendars[gId][dateStr] = item.turn;
      }
    });

    userExceptionMap.value = userExceptions;
    groupMap.value = groupCalendars;

    // Resetear el índice de inicio
    startIndex.value = 0;

  }, 'Ocurrió un error al intentar obtener el calendario de rotación desde la base de datos.');
};

onMounted(() => {
  loadCalendarData();
});
</script>

<style scoped>
.schedule-view-container {
  position: relative;
  padding: 24px;
  background-color: #f8f9fa;
  height: 100%;
}
.header-actions {
  margin-bottom: 12px;
}
.subtitle {
  color: #6c757d;
}
.navigation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  background-color: #ffffff;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}
.nav-buttons {
  display: flex;
  gap: 8px;
}
.range-info {
  font-size: 0.9rem;
  color: #4b5563;
  font-weight: 500;
}
.grid-wrapper {
  position: relative;
  height: calc(100% - 150px); /* Ajustado para dejar espacio a la barra de navegación */
}
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
  color: #721c24;
  padding: 15px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  margin-top: 10px;
  border-radius: 4px;
  text-align: center;
}

/* Ocultar el icono de filtro de la grilla en las columnas que tengan la clase 'hide-filter' */
:deep(.hide-filter .filter-icon) {
  display: none !important;
}

/* ========================================================
   ESTILOS DE CELDAS DE TURNOS SEGÚN VALOR
   ======================================================== */

/* DM: Verde oscuro con texto blanco */
:deep(.cell:not(.summary-cell)[data-value="DM"]) {
  background-color: #15803d !important;
  color: #ffffff !important;
  font-weight: bold;
  text-align: center;
}

/* D: Amarillo con texto marrón oscuro */
:deep(.cell:not(.summary-cell)[data-value="D"]) {
  background-color: #fef08a !important;
  color: #854d0e !important;
  font-weight: bold;
  text-align: center;
}

/* STA: Naranja con texto blanco */
:deep(.cell:not(.summary-cell)[data-value="STA"]) {
  background-color: #f97316 !important;
  color: #ffffff !important;
  font-weight: bold;
  text-align: center;
}

/* N: Azul oscuro con texto blanco */
:deep(.cell:not(.summary-cell)[data-value="N"]) {
  background-color: #1e40af !important;
  color: #ffffff !important;
  font-weight: bold;
  text-align: center;
}

/* x: Rojo claro con texto rojo oscuro */
:deep(.cell:not(.summary-cell)[data-value="x"]) {
  background-color: #fee2e2 !important;
  color: #991b1b !important;
  font-weight: bold;
  text-align: center;
  font-family: monospace;
}

/* Centrado alineado en todas las columnas de la tabla de turnos, excepto la columna del nombre */
:deep(.excel-table td:not(:first-child)) {
  text-align: center;
}
</style>