<template>
  <!-- Contenedor principal de la vista del calendario mensual y tareas diarias -->
  <div class="monthly-calendar-container">
    
    <!-- Sección superior: Controles del calendario (Mes y Año) -->
    <div class="calendar-header">
      <!-- Botón para retroceder un mes -->
      <button @click="prevMonth" class="nav-btn">&laquo; Mes Anterior</button>
      <!-- Etiqueta que muestra el mes y año actual en texto -->
      <h2 class="month-title">{{ monthNames[currentMonth] }} {{ currentYear }}</h2>
      <!-- Botón para avanzar un mes -->
      <button @click="nextMonth" class="nav-btn">Mes Siguiente &raquo;</button>
    </div>

    <!-- Grilla del calendario -->
    <div class="calendar-grid">
      <!-- Cabecera de la grilla: Nombres de los días de la semana -->
      <div v-for="dia in diasSemana" :key="dia" class="calendar-day-header">
        {{ dia }}
      </div>
      
      <!-- Celdas de los días del mes generadas dinámicamente -->
      <!-- Asignación de clases dinámicas: celda vacía, celda clickeable y día seleccionado -->
      <!-- Evento click para cargar las tareas del día específico -->
      <div 
        v-for="(dayObj, index) in daysInMonth" 
        :key="index" 
        :class="['calendar-cell', { 'empty-cell': dayObj.empty, 'active-day': selectedDate === dayObj.dateStr }]"
        @click="handleSelectDay(dayObj)"
      >
        <template v-if="!dayObj.empty">
          <!-- Muestra el número del día -->
          <span class="day-number">{{ dayObj.day }}</span>
          
          <!-- Contenedor de stickers del personal -->
          <div class="stickers-container">
            <span 
              v-for="(sticker, idx) in initialsMap[dayObj.dateStr]" 
              :key="idx" 
              :class="['personnel-sticker', 'sticker-' + sticker.type, { 'sticker-overtime': sticker.overtime > 0 }]"
              :title="'Personal asignado: ' + (sticker.fullName || sticker.text) + (sticker.overtime > 0 ? ' (Trabajo en Descanso)' : '')"
            >
              {{ sticker.text }}
            </span>
          </div>
        </template>
      </div>
    </div>

    <!-- Modal: Detalle de Tareas Diarias -->
    <div v-if="selectedDate" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>Tareas para el día: {{ selectedDate }}</h3>
          <button @click="closeModal" class="close-btn" title="Cerrar modal">&times;</button>
        </div>
        <div class="modal-body">
          <ExcelGrid
            :title="'Planificación Diaria'"
            :headers="headers"
            :data="gridData"
            :columnsConfig="dashboardConfig"
            @save="handleSaveFromGrid"
          />
        </div>
      </div>
    </div>

    <!-- Superposición (Overlay) que indica que el sistema está cargando datos de la red -->
    <div v-if="loading" class="loading-overlay">Cargando información del día...</div>
    <!-- Mensaje de error visual si la petición a la API falla -->
    <div v-if="error" class="error-message">{{ error }}</div>

  </div>
</template>

<script setup>
// Importaciones principales del ecosistema Vue
import { ref, computed, onMounted, watch } from 'vue';
// Importación de la instancia Axios configurada para consumir el backend Django
import { api } from '../../api';
// Importación del componente de tabla editable (ExcelGrid)
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importación del composable global que administra estados de carga y error automáticamente
import { useApi } from '../../composables/useApi';

// Desestructuración de variables y funciones útiles proporcionadas por el composable useApi
const { loading, error, execute } = useApi();

// --- VARIABLES DE ESTADO DEL CALENDARIO ---
// Se obtiene la fecha actual exacta del sistema del usuario
const today = new Date();
// Se inicializa la variable reactiva del mes actual (0 = Enero, 11 = Diciembre)
const currentMonth = ref(today.getMonth());
// Se inicializa la variable reactiva del año actual
const currentYear = ref(today.getFullYear());
// Se inicializa la variable reactiva que almacenará la fecha clickeada en formato 'YYYY-MM-DD'
const selectedDate = ref(null);

// --- ARREGLOS DE TEXTO ESTATICOS ---
// Nombres de los meses para el título del calendario
const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
// Abreviaturas de los días de la semana para las columnas del calendario (Lunes primero)
const diasSemana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

// --- COMPUTADOS (LÓGICA VISUAL DEL CALENDARIO) ---
// Computed property que calcula los días exactos de un mes y los espacios en blanco requeridos
const daysInMonth = computed(() => {
  // Array principal que contendrá los objetos de cada celda
  const days = [];
  // Instancia de fecha apuntando al primer día del mes actual visualizado
  const date = new Date(currentYear.value, currentMonth.value, 1);
  
  // Obtiene el índice del primer día de la semana (Domingo es 0 en JS)
  // Lo ajustamos para que Lunes sea 1 y Domingo sea 7
  let firstDayIndex = date.getDay() || 7;
  
  // Bucle para rellenar con celdas vacías los días previos al inicio del mes
  for (let i = 1; i < firstDayIndex; i++) {
    // Se empuja un objeto indicando que es un espacio vacío sin contenido
    days.push({ empty: true });
  }
  
  // Bucle que recorre cada día mientras siga perteneciendo al mes actual
  while (date.getMonth() === currentMonth.value) {
    // Construcción manual y forzada de la cadena YYYY-MM-DD conservando ceros iniciales
    const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    // Se inserta en el array la información del día válido
    days.push({
      empty: false, // Indica que es un día con fecha
      dateStr: dateStr, // String formateado
      day: date.getDate(), // Número del día
      dateObj: new Date(date) // Copia literal del objeto fecha
    });
    // Avanzamos el cursor de fecha al día siguiente
    date.setDate(date.getDate() + 1);
  }
  
  // Retorna el array completo listo para ser renderizado por el v-for
  return days;
});

// --- MÉTODOS DE NAVEGACIÓN ---
// Función para avanzar un mes
const nextMonth = () => {
  // Si es Diciembre (11), el próximo mes es Enero (0) y sumamos un año
  if (currentMonth.value === 11) {
    currentMonth.value = 0;
    currentYear.value++;
  } else {
    // En cualquier otro caso solo sumamos un mes
    currentMonth.value++;
  }
};

// Función para retroceder un mes
const prevMonth = () => {
  // Si es Enero (0), el mes anterior es Diciembre (11) y restamos un año
  if (currentMonth.value === 0) {
    currentMonth.value = 11;
    currentYear.value--;
  } else {
    // En cualquier otro caso solo restamos un mes
    currentMonth.value--;
  }
};

// --- LÓGICA DE NEGOCIO Y CÁLCULO DE SEMANA EXTENDIDA ---
// Calcula de forma precisa el número de semana extendida ISO (Año base 1963)
const getExtendedWeek = (date) => {
  // Creamos un objetivo (target) clonado para no alterar la fecha original
  const target = new Date(date.valueOf());
  // Encontramos la posición del día dentro de la semana ISO (Lunes=0, Domingo=6)
  const dayNr = (date.getDay() + 6) % 7;
  // Ajustamos el target al jueves más cercano (jueves determina el año ISO)
  target.setDate(target.getDate() - dayNr + 3);
  // Guardamos los milisegundos exactos de este primer jueves de la semana
  const firstThursday = target.valueOf();
  // Reseteamos el objetivo al primero de enero de su respectivo año
  target.setMonth(0, 1);
  // Si el 1 de enero no es jueves, ajustamos al jueves de esa primera semana
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
  }
  // Calculamos la semana ISO actual restando los jueves y dividiendo por una semana en milisegundos
  const isoWeek = 1 + Math.ceil((firstThursday - target) / 604800000);
  // Obtenemos el año estricto ISO resultante
  const isoYear = target.getFullYear();
  
  // Aplicamos la misma fórmula del script Python 'generar_calendario.py'
  const yearsSince1963 = isoYear - 1963;
  const accumulatedWeeks = yearsSince1963 * 52;
  // Semana actual + Desfase (6) + Semanas de todos los años transcurridos
  return isoWeek + 6 + accumulatedWeeks;
};

// --- CARGA DE DATOS MENSUALES PARA STICKERS ---
const monthCalendarData = ref([]);

const fetchMonthData = async () => {
  const uniqueWeeks = new Set();
  const weeksToFetch = [];
  
  // Encontrar todas las semanas ISO que abarcan los días de este mes
  daysInMonth.value.forEach(dayObj => {
    if (!dayObj.empty) {
      const week = getExtendedWeek(dayObj.dateObj);
      const year = dayObj.dateObj.getFullYear();
      const key = `${year}-${week}`;
      if (!uniqueWeeks.has(key)) {
        uniqueWeeks.add(key);
        weeksToFetch.push({ week, year });
      }
    }
  });

  if (weeksToFetch.length === 0) return;

  await execute(async () => {
    // Pedir en paralelo todas las semanas requeridas
    const promises = weeksToFetch.map(w => api.get(`/weekly-tasks/?week=${w.week}&year=${w.year}`));
    const responses = await Promise.all(promises);
    
    let allCalendar = [];
    responses.forEach(res => {
      const cal = res.data.calendar || [];
      allCalendar.push(...cal);
    });
    
    monthCalendarData.value = allCalendar;
  }, 'Error al cargar el calendario del mes.');
};

// Mapa computado para optimizar la visualización de iniciales por día
const initialsMap = computed(() => {
  const map = {};
  monthCalendarData.value.forEach(c => {
    const dateStr = c.date || c.fecha;
    if (!dateStr) return;
    
    const strTurno = String(c.turno || '').toUpperCase();
    // Ignorar personal que tiene día de descanso 'X'
    if (strTurno === 'X' || !strTurno) return;

    if (c.usuario_nombre) {
      const n = c.usuario_nombre.trim().charAt(0);
      const a = c.usuario_apellido ? c.usuario_apellido.trim().charAt(0) : '';
      const initial = (n + a).toUpperCase();
      
      if (!map[dateStr]) map[dateStr] = new Map();
      
      let shiftType = 'D'; // Turno Día por defecto
      if (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE')) shiftType = 'N';
      else if (strTurno === 'AB' || strTurno === 'DN') shiftType = 'DN';
      
      const hasOvertime = c.horas_extra && Number(c.horas_extra) > 0;
      const overtimeHours = hasOvertime ? Number(c.horas_extra) : 0;
      const fullName = `${c.usuario_nombre} ${c.usuario_apellido || ''}`.trim();
      
      if (map[dateStr].has(initial)) {
        const existing = map[dateStr].get(initial);
        let newType = existing.type;
        if (existing.type !== shiftType && existing.type !== 'DN') newType = 'DN';
        map[dateStr].set(initial, {
          type: newType,
          overtime: existing.overtime + overtimeHours,
          fullName: existing.fullName
        });
      } else {
        map[dateStr].set(initial, {
          type: shiftType,
          overtime: overtimeHours,
          fullName: fullName
        });
      }
    }
  });
  
  // Convertir los maps a un Array plano para la vista (v-for)
  const finalMap = {};
  for (const [date, personnelMap] of Object.entries(map)) {
    finalMap[date] = Array.from(personnelMap.entries()).map(([text, data]) => ({
      text,
      type: data.type,
      overtime: data.overtime,
      fullName: data.fullName
    }));
  }
  return finalMap;
});

// --- ESTADO Y CONFIGURACIÓN DE LA TABLA DE TAREAS (EXCELGRID) ---
// Cabeceras superiores estáticas para la tabla ExcelGrid
const headers = ['Planta', 'Área', 'Sistema', 'Equipo', 'Tarea', 'Turno', 'Estado'];
// Array reactivo que albergará la matriz de celdas a mostrar
const gridData = ref([]);

// Configuración específica de la columna 'Estado' (índice 6) para que sea un selector R/P/X
const dashboardConfig = {
  6: { type: 'select', options: [{ label: 'R', value: '1' }, { label: 'P', value: '2' }, { label: 'X', value: '3' }] }
};

// Vigilar cambios en el calendario para solicitar nueva información automáticamente
watch([currentMonth, currentYear], () => {
  selectedDate.value = null; // Reiniciar la selección
  gridData.value = [];       // Limpiar la tabla de ExcelGrid
  fetchMonthData();          // Actualizar los stickers
}, { immediate: true });

// --- EVENTO DE SELECCIÓN DE DÍA Y CARGA DE DATOS ---
// Se dispara al clickear cualquier día habilitado en el calendario
const handleSelectDay = async (dayObj) => {
  // Se previene la ejecución si se clickeó una celda de relleno (vacía)
  if (dayObj.empty) return;
  
  // Establece el día escogido en formato string
  selectedDate.value = dayObj.dateStr;
  
  // Envuelve la petición HTTP en execute para mostrar el spinner y atajar errores
  await execute(async () => {
    // Calcula la semana ISO-1963 para este día exacto
    const week = getExtendedWeek(dayObj.dateObj);
    // Obtiene el año de este día
    const year = dayObj.dateObj.getFullYear();
    
    // --- CONSULTAR TAREAS DESDE EL SERVIDOR ---
    // Consultamos únicamente weekly-tasks, la cual devuelve tanto preventivas como correctivas ya integradas
    const res = await api.get(`/weekly-tasks/?week=${week}&year=${year}`);
    
    // Extrae el array de tareas del objeto devuelto por el servidor (soportando respuestas paginadas)
    const tasksData = res.data.tasks || res.data;
    const calendarData = res.data.calendar || [];
    
    // Filtra las tareas de esa semana dejando únicamente las que coincidan con la fecha seleccionada
    const dailyTasks = tasksData.filter(t => (t.date || t.fecha) === dayObj.dateStr);
    
    // --- ESTADÍSTICAS DE TAREAS ---
    let countDia = 0;
    let countNoche = 0;
    let countAB = 0;
    let countDeshabilitadas = 0;
    // Excluir tareas deshabilitadas (estado_id = 3) del total principal de actividades
    let countTotal = dailyTasks.filter(t => String(t.estado_id) !== '3').length;
    
    // Transforma las tareas obtenidas al formato plano requerido por ExcelGrid
    const mappedTasks = dailyTasks.map(t => {
      // Clasificamos para los contadores usando la misma lógica de WeeklyTasksView
      if (String(t.estado_id) === '3') {
        countDeshabilitadas++;
      } else {
        const strTurno = String(t.turno || '').toUpperCase();
        if (strTurno === 'AB' || strTurno === 'DN') countAB++;
        else if (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE')) countNoche++;
        else countDia++;
      }

      // Se formatea y concatena el equipo junto con su descripción, limpiando espacios si hace falta
      const equipoDisplay = t.equipo_desc ? `${t.equipo || ""} ${t.equipo_desc}`.trim() : (t.equipo || "");
      // Se prioriza la descripción de tarea_detalle, o en su defecto tarea_descripcion, y prefijamos correctivas con [C]
      const tareaDisplay = t.is_corrective ? `[C] ${t.tarea_detalle || t.tarea_descripcion || ""}` : (t.tarea_detalle || t.tarea_descripcion || "");
      
      // Se transforma la letra de turno de la BD a notación amigable (D, N, DN)
      let turnoLabel = t.turno || '';
      if (t.turno === 'A') turnoLabel = 'D';
      else if (t.turno === 'B') turnoLabel = 'N';
      else if (t.turno === 'AB') turnoLabel = 'DN';
      
      // Se ensambla la fila en el mismo orden que las 'headers'
      const row = [
        t.planta || "", t.area || "", t.sistema || "", equipoDisplay, tareaDisplay, turnoLabel, String(t.estado_id)
      ];
      
      // Se inyecta una propiedad oculta (no enumerable) para almacenar el ID real de la tarea (TaskP ID)
      Object.defineProperty(row, '_taskId', { value: t.id, enumerable: false, writable: true });
      Object.defineProperty(row, '_isCorrective', { value: t.is_corrective, enumerable: false, writable: true });
      
      // Se retorna la fila completa hacia la grilla
      return row;
    });

    // --- ESTADÍSTICAS DE PERSONAL BASADO EN EL CALENDARIO ---
    const personalDia = new Set();
    const personalNoche = new Set();
    
    const dailyCalendar = calendarData.filter(c => (c.date || c.fecha) === dayObj.dateStr);
    dailyCalendar.forEach(c => {
      if (c.usuario_nombre) {
        const isOvertime = c.horas_extra && Number(c.horas_extra) > 0;
        const overtimeText = isOvertime ? ' (Trabajo en Descanso)' : '';
        const fullName = `${c.usuario_nombre} ${c.usuario_apellido || ''}${overtimeText}`.trim();
        const strTurno = String(c.turno || '').toUpperCase();
        
        // Si el calendario marca descanso 'X', ignoramos a la persona ese día
        if (strTurno === 'X' || !strTurno) return;

        // Clasificamos el turno
        const isNoche = (strTurno === 'N' || strTurno === 'B' || strTurno.includes('NOCHE'));
        const isAmbos = (strTurno === 'AB' || strTurno === 'DN');
        
        if (isAmbos) {
          personalDia.add(fullName);
          personalNoche.add(fullName);
        } else if (isNoche) {
          personalNoche.add(fullName);
        } else {
          personalDia.add(fullName);
        }
      }
    });

    // --- GENERAR FILAS DE RESUMEN ---
    const createSummaryRow = (label, value, useColspan = false) => {
      // Dejamos las primeras 4 columnas en blanco, usamos 'Tarea' para el label y 'Turno' para el valor
      const cellVal = useColspan ? { value: String(value), colspan: 2 } : String(value);
      const lastCell = useColspan ? null : "";
      const row = ["", "", "", "", label, cellVal, lastCell];
      Object.defineProperty(row, 'isSummary', { value: true, enumerable: false, writable: true });
      Object.defineProperty(row, '_taskId', { value: null, enumerable: false, writable: true });
      return row;
    };

    // Combinar preventivas y correctivas en el grid
    const newData = [...mappedTasks];
    
    newData.push(
      createSummaryRow("", ""), // Espaciador visual
      createSummaryRow("Actividades de Día", countDia),
      createSummaryRow("Actividades de Noche", countNoche),
      createSummaryRow("Actividades Turno AB", countAB),
      createSummaryRow("Total de Actividades", countTotal),
      createSummaryRow("Actividades Deshabilitadas", countDeshabilitadas),
      createSummaryRow("Cant. Personal Día", personalDia.size),
      createSummaryRow("Nombres Personal Día", Array.from(personalDia).join('\n') || '-', true),
      createSummaryRow("Cant. Personal Noche", personalNoche.size),
      createSummaryRow("Nombres Personal Noche", Array.from(personalNoche).join('\n') || '-', true)
    );

    gridData.value = newData;

  // Mensaje en caso de falla nativa
  }, 'Error al cargar tareas diarias desde el servidor.');
};

// --- EVENTO DE GUARDADO MASIVO DESDE LA TABLA ---
// Recibe la matriz entera modificada desde ExcelGrid para su almacenamiento
const handleSaveFromGrid = async (updatedLocalGrid) => {
  // Array vacío que agrupará los diccionarios de actualización a enviar
  const updatesTaskP = [];
  
  // Se recorre cada fila de la grilla que fue alterada
  updatedLocalGrid.forEach(fila => {
    if (fila.isSummary) return; // Ignorar las filas de estadísticas al guardar

    // Se recupera la propiedad oculta ID generada en la carga
    const taskId = fila._taskId;
    // Si existe un ID válido, preparamos el paquete de actualización
    if (taskId) {
      updatesTaskP.push({
        id: taskId, // ID real en base de datos (TaskP ID)
        estado_id: fila[6] // Valor recogido de la columna de estado (columna 6)
      });
    }
  });

  // Previene un envío a la red si por alguna razón no hay información
  if (updatesTaskP.length === 0) return;

  try {
    // Se envuelve la petición POST en el ejecutor global
    await execute(async () => {
      await api.post('/weekly-tasks/', { updates: updatesTaskP });
      // Notifica al usuario de la confirmación
      alert("Cambios diarios guardados con éxito.");
      
      // Fuerza una recarga en la interfaz volviendo a generar un click virtual en el día que estábamos viendo
      const reclickDay = daysInMonth.value.find(d => d.dateStr === selectedDate.value);
      if(reclickDay) await handleSelectDay(reclickDay);
    });
  } catch (err) {
    // Si fracasa de todos modos se emite alerta local
    alert("Error al sincronizar con el servidor.");
  }
};

const closeModal = () => {
  selectedDate.value = null;
  gridData.value = [];
};
</script>

<style scoped>
/* Contenedor principal que ocupa toda la altura posible y ancla su contenido */
.monthly-calendar-container {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: #fff;
}

/* Estilos para la barra superior donde yacen los botones de cambiar de mes */
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.month-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #343a40;
}
.nav-btn {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.nav-btn:hover {
  background-color: #0056b3;
}

/* Grilla principal de días visualizando un máximo de 7 columnas proporcionales */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
/* Cabeceras de los días de la semana */
.calendar-day-header {
  text-align: center;
  font-weight: bold;
  color: #495057;
  padding: 10px 0;
  border-bottom: 2px solid #dee2e6;
}
/* Celdas individuales cliqueables que representan días */
.calendar-cell {
  min-height: 80px;
  border: 1px solid #e9ecef;
  border-radius: 5px;
  padding: 10px;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* El número arriba, los stickers abajo */
  position: relative;
}
.calendar-cell:hover:not(.empty-cell) {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}
/* Si el día está seleccionado se colorea de forma vistosa */
.active-day {
  background-color: #e7f1ff !important;
  border-color: #0d6efd !important;
  box-shadow: 0 0 5px rgba(13, 110, 253, 0.5);
}
/* Celdas que fungen de espaciadores de días ajenos al mes actual */
.empty-cell {
  background-color: #f8f9fa;
  border: 1px dashed #e9ecef;
  cursor: default;
}
/* Tipografía para el número del día */
.day-number {
  align-self: flex-end; /* Mantiene el número alineado a la derecha */
  font-size: 1.2rem;
  font-weight: bold;
  color: #495057;
}

/* Contenedor y diseño de los stickers (iniciales) */
.stickers-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
.personnel-sticker {
  font-size: 0.75rem;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}
/* Colores dinámicos por turno */
.sticker-D {
  background-color: #f1c40f; /* Amarillo para turno de Día */
  color: #212529; /* Texto oscuro para contrastar */
}
.sticker-N {
  background-color: #2980b9; /* Azul para turno de Noche */
  color: white;
}
.sticker-DN {
  background-color: #27ae60; /* Verde para turnos combinados (Día y Noche) */
  color: white;
}

/* Contenedor superpuesto que bloquea la acción durante la red */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 1.2rem;
  z-index: 1100;
}

/* Estilos para el Modal (Popup) */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.25s ease-out;
}

.modal-content {
  background: #ffffff;
  border-radius: 12px;
  width: 95%;
  max-width: 1500px;
  height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #dee2e6;
  background-color: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #212529;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.75rem;
  line-height: 1;
  color: #6c757d;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: #e9ecef;
  color: #212529;
}

.modal-body {
  padding: 12px;
  overflow: hidden;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background-color: #fcfcfc;
}

/* Forzar que el componente ExcelGrid llene la altura del modal y no cause scroll externo */
.modal-body :deep(.excel-container) {
  height: 100% !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* Animaciones */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Mensaje de retroalimentación de error */
.error-message {
  color: red;
  text-align: center;
  margin-top: 10px;
}

/* Permitir saltos de línea (pre-wrap) en las celdas de resumen dentro del ExcelGrid */
:deep(.summary-cell) {
  white-space: pre-wrap !important;
}

/* Estilos personalizados para las celdas de Turno y Estado sin alterar ExcelGrid globalmente */
:deep(.cell:not(.summary-cell)[data-col-index="5"]) {
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

:deep(.cell:not(.summary-cell)[data-col-index="6"]) {
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
:deep(.cell:not(.summary-cell)[data-value="3"]) {
  background-color: #e5e7eb !important; /* Deshabilitado (Gris) */
  color: #4b5563 !important;
  font-weight: bold;
}

/* Colorear la celda de turno de gris si la celda de estado está deshabilitada (estado = 3) */
:deep(tr:has(td[data-col-index="6"][data-value="3"]) td[data-col-index="5"]) {
  background-color: #e5e7eb !important;
  color: #4b5563 !important;
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

.sticker-D.sticker-overtime {
  background-color: #fef08a !important; /* Amarillo */
  color: #dc2626 !important; /* Texto rojo */
  font-weight: bold !important;
  border: 1.5px solid #dc2626 !important;
}

.sticker-N.sticker-overtime {
  background-color: #dbeafe !important; /* Azul */
  color: #dc2626 !important; /* Texto rojo */
  font-weight: bold !important;
  border: 1.5px solid #dc2626 !important;
}

.sticker-DN.sticker-overtime {
  background-color: #ccdbe7 !important; /* Combinado */
  color: #dc2626 !important; /* Texto rojo */
  font-weight: bold !important;
  border: 1.5px solid #dc2626 !important;
}
</style>