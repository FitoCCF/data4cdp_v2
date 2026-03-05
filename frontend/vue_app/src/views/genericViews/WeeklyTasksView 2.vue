<template>
  <div>
    <!-- Título de la tabla -->
    <!--<h2>Planificación de Tareas - Semana {{ rsemana }}</h2> -->
    <h2>
      Planificación de Tareas - Semana
       <input type="text" v-model="nsemana" :placeholder="rsemana">
    </h2>

    <!-- Botón para descargar Excel -->
    <button @click="exportToExcel">Descargar Excel</button>

    <!-- Tabla de tareas -->
    <table>
      <thead>
        <tr>
          <th>Planta</th>
          <th>Sistema</th>
          <th>Equipo</th>
          <th>Tarea</th>
          <th v-for="(dia, index) in diasSemana" :key="dia" colspan="2">
            {{ dia }}<br>{{ fechasOrd[index] }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in tareasAgrupadas" :key="index">
          <td>{{ item.planta }}</td>
          <td>{{ item.sistema }}</td>
          <td>{{ item.equipo }}</td>
          <td>{{ item.tarea }}</td>
          <template v-for="(dia, index) in diasSemana" :key="dia">
            <td :class="getClass(item.dias[dia]?.turno, false)"> 
              {{ item.dias[dia]?.turno || '' }}
             <!-- {{ item.dias[dia]?.id_taskp || '' }} -->
            </td>
            <td :class="getClass(item.dias[dia]?.estado, true)">
  <template v-if="item.dias[dia]">
    <input 
      type="text"
      v-model="item.dias[dia].estado"
      :placeholder="item.dias[dia].estado || 'Ingrese estado...'"
      @blur="updateEstado(item.dias[dia].id_taskp, item.dias[dia].estado, 3239)"
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
import { ref, onMounted, watch } from 'vue';
import { api } from '../../api';
import axios from 'axios';
import { getWeek } from 'date-fns';
import * as XLSX from 'xlsx';

const rsemana = ref(null);
const diasSemana = ref([]);
const fechasOrd = ref([]);
const tareasAgrupadas = ref([]);
const nsemana = ref('')
const isemana = ref('')

// Semana ISO del día que se está visualizando (semana real del calendario)
const actualWeek = (fecha) => getWeek(fecha, { weekStartsOn: 1 });




// Función para actualizar el estado cuando el usuario haga clic fuera del input text
const updateEstado = async (id, nuevoEstado, week) => {
  console.log('id', id);
  console.log('estado', nuevoEstado);
  console.log('semana', week);
  console.log('semanain', tituloSemana.value);
  if (!id || !nuevoEstado || !week) return;
  

  try {
   
    const url = `http://localhost:8000/api/vtaskp/update-estado/`;
    await axios.put(url, { 
      id_taskp: id,
      estado: nuevoEstado,
      semana: week
     }, {
      headers: { "Content-Type": "application/json" }
    });

    console.log(`Estado actualizado correctamente para la tarea con ID ${id}`);
  } catch (error) {
    console.error("Error al actualizar el estado:", error);
  }
};


const cargarDatos = async (numeroSemana) => {
  const semana = Number(numeroSemana);
  if (!semana) return false;

  try {
    const response = await api.get(`vtaskp/?semana=${semana}`);
    const tareas = response.data;
    if (!tareas || !tareas.length) return false;

    rsemana.value = tareas[0].semana;
    const diasUnicos = [...new Set(tareas.map(t => t.dia_semana))];
    const fechasUnicas = [...new Set(tareas.map(t => t.fecha))].sort();

    const ordenDias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    diasSemana.value = ordenDias.filter(d => diasUnicos.includes(d));
    fechasOrd.value = fechasUnicas;
  
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

      agrupadas[key].dias[t.dia_semana] = {
        turno: t.turno === 'A' ? 'D' : t.turno === 'B' ? 'N' : 'DN',
        estado: t.estado,
        id_taskp: t.id_taskp
      };
    });

    tareasAgrupadas.value = Object.values(agrupadas);
    return true;
  } catch (error) {
    console.error("Error al obtener las tareas:", error);
    return false;
  }
};

// Busca la semana más reciente disponible; prioriza semanas <= semana actual
const cargarSemanaMasReciente = async (semanaHoy) => {
  try {
    const response = await api.get('vtaskp/');
    const tareas = response.data || [];
    if (!tareas.length) return false;

    const semanas = tareas
      .map(t => Number(t.semana))
      .filter(sem => !Number.isNaN(sem));

    if (!semanas.length) return false;

    const semanasValidas = semanas.filter(sem => sem <= semanaHoy);
    const semanaReciente = (semanasValidas.length ? Math.max(...semanasValidas) : Math.max(...semanas));
    return cargarDatos(semanaReciente);
  } catch (error) {
    console.error("Error al buscar semanas disponibles:", error);
    return false;
  }
};

onMounted(async () => {
  isemana.value = actualWeek(new Date());
  console.log('Semana actual de calendario', isemana.value);

  const cargada = await cargarDatos(isemana.value);
  if (!cargada) {
    await cargarSemanaMasReciente(isemana.value);
  }
});

// Permite ingresar manualmente otra semana
watch(nsemana, async (val) => {
  if (!val) return;
  if (Number(val) === rsemana.value) return;
  await cargarDatos(val);
});

// Función para asignar clases CSS
const getClass = (value, isEstado) => {
if (isEstado) {
  return value === 'P' ? 'pending' : value === 'R' ? 'success' : ''; 
} else {
  return value === 'D' ? 'turno-d' : value === 'N' ? 'turno-n' : value === 'DN' ? 'turno-dn' : ''; 
}
};

// Función para exportar la tabla a Excel manteniendo los estilos y celdas combinadas
const exportToExcel = () => {
const wb = XLSX.utils.book_new();
const wsData = [];

// Encabezado de la tabla
const headerRow = ["Planta", "Sistema", "Equipo", "Tarea", ...diasSemana.value.flatMap(d => [d + " Turno", d + " Estado"])];
wsData.push(headerRow);

// Datos de la tabla
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

// Crear la hoja de cálculo
const ws = XLSX.utils.aoa_to_sheet(wsData);

// Aplicar estilos básicos
ws['!cols'] = [{ wch: 15 }, { wch: 15 }, { wch: 20 }, { wch: 25 }, ...Array(diasSemana.value.length * 2).fill({ wch: 10 })];

// Fusionar encabezados de días
ws['!merges'] = diasSemana.value.map((_, index) => ({
  s: { r: 0, c: 4 + index * 2 },
  e: { r: 0, c: 5 + index * 2 }
}));

// Aplicar colores a las celdas de turno
tareasAgrupadas.value.forEach((item, rowIndex) => {
  diasSemana.value.forEach((dia, colIndex) => {
    const turnoCell = XLSX.utils.encode_cell({ r: rowIndex + 1, c: 4 + colIndex * 2 });
    const turnoValue = item.dias[dia]?.turno || '';

    if (turnoValue === 'D') ws[turnoCell].s = { fill: { fgColor: { rgb: "FFFF00" } } };
    if (turnoValue === 'N') ws[turnoCell].s = { fill: { fgColor: { rgb: "ADD8E6" } } };
    if (turnoValue === 'DN') ws[turnoCell].s = { fill: { fgColor: { rgb: "90EE90" } } };
  });
});

// Guardar el archivo Excel
XLSX.utils.book_append_sheet(wb, ws, "Planificación");
XLSX.writeFile(wb, `Planificacion_Semana_${semana.value}.xlsx`);
};
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
  position: relative; /* Asegura que los elementos internos se alineen correctamente */
}
th {
  background-color: #f2f2f2;
}

/* Estilos para los turnos */
.turno-d {
  background-color: yellow;
  font-weight: bold;
}
.turno-n {
  background-color: lightblue;
  font-weight: bold;
}
.turno-dn {
  background-color: lightgreen;
  font-weight: bold;
}

/* Asegurar que el input ocupe todo el espacio de la celda */
td input[type="text"] {
  width: 100%;
  height: 100%;
  border: none;
  outline: none;
  padding: 8px;
  text-align: center;
  font-size: 1em;
  box-sizing: border-box; /* Evita que el padding afecte el tamaño */
}

/* Estilos cuando el input tiene estado 'pending' */
.pending input[type="text"] {
  color: red;
  font-weight: bold;
  background-color: #ffcccc; /* Un rojo claro para mayor visibilidad */
}

/* Estilos cuando el input tiene estado 'success' */
.success input[type="text"] {
  color: green;
  font-weight: bold;
  background-color: #ccffcc; /* Un verde claro para mayor visibilidad */
}

/* Estilos para el botón */
button {
  margin-bottom: 10px;
  padding: 8px 15px;
  border: none;
  background-color: #4CAF50;
  color: white;
  cursor: pointer;
}
button:hover {
  background-color: #45a049;
}
</style>                                                                                                                                                                                  1
