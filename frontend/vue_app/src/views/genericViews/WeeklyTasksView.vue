<template>
  <div>
    <!-- Título de la tabla con un campo de entrada para cambiar la semana -->
       <!-- ARCHIVO DE PRODUCCION -->
    <h2>
      Planificación de Tareas - Semana
      <input type="text" v-model="nsemana" :placeholder="rsemana" class="week">
      
    </h2>

    <!-- Botón para exportar los datos a un archivo Excel -->
    <button @click="exportToExcel">Descargar Excel</button>

    <!-- Tabla de planificación de tareas -->
    <table>
      <thead>
        <tr>
          <th>Planta</th>
          <th>Sistema</th>
          <th>Equipo</th>
          <th>Tarea</th>
          <!-- Encabezados de días dinámicos generados a partir de los datos -->
          <th v-for="(dia, index) in diasSemana" :key="dia" colspan="2">
            {{ dia }}<br>{{ fechasOrd[index] }}
          </th>
        </tr>
      </thead>
      <tbody>
        <!-- Iterar sobre las tareas agrupadas -->
        <tr v-for="(item, index) in tareasAgrupadas" :key="index">
          <td>{{ item.planta }}</td>
          <td>{{ item.sistema }}</td>
          <td>{{ item.equipo }}</td>
          <td>{{ item.tarea }}</td>

          <!-- Generar dinámicamente las celdas para cada día de la semana -->
          <template v-for="(dia, index) in diasSemana" :key="dia">
            <td :class="getClass(item.dias[dia]?.turno, false)"> 
              {{ item.dias[dia]?.turno || '' }}
              <!-- {{ item.dias[dia]?.id_taskp || '' }} -->
            </td>
            <td :class="getClass(item.dias[dia]?.estado, true)">
              <!-- Si el objeto `item.dias[dia]` existe, muestra un input para editar el estado -->
              <template v-if="item.dias[dia]">
                <input 
                  type="text"
                  v-model="item.dias[dia].estado"
                  :placeholder="item.dias[dia].estado || 'Ingrese estado...'"
                  @blur="updateEstado(item.dias[dia].id_taskp, item.dias[dia].estado, nsemana||rsemana)"
                />
              </template>
              <template v-else>
                <span> - </span> <!-- Muestra un guion si no hay datos -->
              </template>
            </td>
          </template>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'; // Importar funciones reactivas y eventos de Vue
import { api } from '../../api'; // Importar la API definida
import { getWeek } from 'date-fns'; // Función para calcular la semana del año
import * as XLSX from 'xlsx'; // Librería para exportar datos a Excel

// Variables reactivas
const rsemana = ref(null); // Semana actual obtenida de la API
const nsemana = ref(''); // Semana ingresada por el usuario en el input
const diasSemana = ref([]); // Lista de días únicos en la API
const fechasOrd = ref([]); // Fechas ordenadas extraídas de la API
const tareasAgrupadas = ref([]); // Lista de tareas organizadas

// Función para calcular la semana basada en la fecha actual
const actualWeek = (fecha) => {
  const semana = getWeek(fecha, { weekStartsOn: 1 });
  const anio = fecha.getFullYear();
   //xweek = initial_week + 6 + ((year - 1963) * 52)
  return semana + 6 + ((anio - 1963) * 52); // Ajuste según la lógica específica del usuario
};

// Función para cargar los datos de la API en base a una semana específica
const cargarDatos = async (semana) => {
  try {
    const response = await api.get(`vtaskp/?semana=${semana}`);
    const tareas = response.data;

    if (tareas.length === 0) return;

    // Actualizar la semana actual
    rsemana.value = semana;
    
    // Obtener los días únicos y ordenarlos
    const diasUnicos = [...new Set(tareas.map(t => t.dia_semana))];
    const fechasUnicas = [...new Set(tareas.map(t => t.fecha))].sort();

    // Lista de días en orden
    const ordenDias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    diasSemana.value = ordenDias.filter(d => diasUnicos.includes(d));
    fechasOrd.value = fechasUnicas;

    // Agrupar las tareas por planta, sistema, equipo y tarea
    const agrupadas = {};
    tareas.forEach(t => {
      const key = `${t.planta}-${t.sistema}-${t.equipo} ${t.descripcion}-${t.tarea_descripcion}`;

      if (!agrupadas[key]) {
        agrupadas[key] = {
          id: key,
          planta: t.planta,
          sistema: t.sistema,
          equipo: `${t.equipo} ${t.descripcion}`,
          tarea: t.tarea_descripcion,
          dias: {}
        };
      }

      // Mapear los turnos a las siglas correspondientes
      agrupadas[key].dias[t.dia_semana] = {
        turno: t.turno === 'A' ? 'D' : t.turno === 'B' ? 'N' : 'DN',
        estado: t.estado,
        id_taskp: t.id_taskp
      };
    });

    tareasAgrupadas.value = Object.values(agrupadas);
  } catch (error) {
    console.error("Error al obtener las tareas:", error);
  }
};

// Función para actualizar el estado en la API cuando el usuario edita el campo de texto
const updateEstado = async (id, nuevoEstado, week) => {
  if (!id || !nuevoEstado || !week) return;

  try {
    await api.put('vtaskp/update-estado/', {
      id_taskp: id,
      estado: nuevoEstado,
      semana: week
    });

    console.log(`Estado actualizado correctamente para la tarea con ID ${id}`);
  } catch (error) {
    console.error("Error al actualizar el estado:", error);
  }
};


// Función para exportar la tabla a Excel
const exportToExcel = () => {
  const wb = XLSX.utils.book_new();
  const wsData = [];

  // Encabezado
  const headerRow1 = ["Planta", "Sistema", "Equipo", "Tarea", ...diasSemana.value.flatMap(d => [`${d} Turno`, `${d} Estado`])];
  const headerRow2 = ["", "", "", "", ...fechasOrd.value.flatMap(date => [date, date])];
  wsData.push(headerRow1);
  wsData.push(headerRow2);
  
  

  // Datos
  tareasAgrupadas.value.forEach(item => {
    const row = [
      item.planta,
      item.sistema,
      item.equipo,
      item.tarea,
      ...diasSemana.value.flatMap(dia => [
        item.dias[dia]?.turno || '',
        item.dias[dia]?.estado || ''
      ])
    ];
    wsData.push(row);
  });

  // Crear hoja de cálculo
  const ws = XLSX.utils.aoa_to_sheet(wsData);
  ws['!cols'] = [{ wch: 15 }, { wch: 15 }, { wch: 20 }, { wch: 25 }, ...Array(diasSemana.value.length * 2).fill({ wch: 10 })];

  // Guardar archivo Excel
  XLSX.utils.book_append_sheet(wb, ws, "Planificación");
  XLSX.writeFile(wb, `Planificacion_Semana_${rsemana.value}.xlsx`);
};

// Detectar cambios en la semana ingresada y recargar los datos dinámicamente
watch(nsemana, (newVal) => {
  if (newVal && newVal !== rsemana.value) {
    cargarDatos(newVal);
  }
});

// Cargar datos cuando el componente se monta
onMounted(() => {
  const semanaInicial = actualWeek(new Date());
  cargarDatos(semanaInicial);
});

// Función para asignar clases CSS según el valor de turno o estado
const getClass = (value, isEstado) => {
  if (isEstado) {
    return value === 'P' ? 'pending' : value === 'R' ? 'success' : ''; 
  } else {
    return value === 'D' ? 'turno-d' : value === 'N' ? 'turno-n' : value === 'DN' ? 'turno-dn' : ''; 
  }
};
</script>

<style scoped>
/* Estilos generales de la tabla */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center; 
}
th {
  background-color: #f2f2f2;
}

/* Estilos para los turnos */
.turno-d { background-color: yellow; font-weight: bold; }
.turno-n { background-color: lightblue; font-weight: bold; }
.turno-dn { background-color: lightgreen; font-weight: bold; }

/* Ajuste de tamaño del input */
td input[type="text"] {
  width: 100%;
  height: 100%;
  text-align: center;
  font-size: 1em;
}

/* Colores para los estados */
.pending input { color: red; font-weight: bold; background-color: #ffcccc; border: 0; }
.success input { color: green; font-weight: bold; background-color: #ccffcc; border: 0; }

.week { width: min-content; border: 0; font-size: large; font-weight: bold; }

button { background-color: #4CAF50; color: white; }
</style>
