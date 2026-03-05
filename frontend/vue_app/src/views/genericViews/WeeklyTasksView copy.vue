<template>
    <div>
      <!-- Título de la tabla que muestra la semana actual -->
      <h2>Planificación de Tareas - Semana {{ semana }}</h2>
      
      <!-- Tabla para mostrar las tareas -->
      <table>
        <thead>
          <tr>
            <th>Planta</th> <!-- Columna de la planta -->
            <th>Sistema</th> <!-- Columna del sistema -->
            <th>Equipo</th> <!-- Columna del equipo -->
            <th>Tarea</th> <!-- Columna de la tarea -->
            <!-- Genera dinámicamente las columnas de los días de la semana con las fechas correspondientes -->
            <th v-for="(dia, index) in diasSemana" :key="dia" colspan="2">
              {{ dia }}<br>{{ fechasOrd[index] }}
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Recorre las tareas agrupadas y genera una fila para cada una -->
          <tr v-for="(item, index) in tareasAgrupadas" :key="index">
            <td>{{ item.planta }}</td> <!-- Muestra la planta -->
            <td>{{ item.sistema }}</td> <!-- Muestra el sistema -->
            <td>{{ item.equipo }}</td> <!-- Muestra el equipo concatenado -->
            <td>{{ item.tarea }}</td> <!-- Muestra la tarea -->
            <!-- Genera dinámicamente las celdas de cada día con turno y estado -->
            <template v-for="(dia, index) in diasSemana" :key="dia">
              <td :class="getClass(item.dias[dia]?.turno)">
                {{ item.dias[dia]?.turno || '' }}
              </td>
              <td :class="getClass(item.dias[dia]?.estado, true)">
                {{ item.dias[dia]?.estado || '' }}
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'; // Importa las funciones reactivas de Vue
import { api } from '../../api'; // Importa la instancia de axios para hacer peticiones HTTP

// Variables reactivas
const semana = ref(null); // Almacena el número de la semana
const diasSemana = ref([]); // Lista de días de la semana presentes en los datos
const fechasOrd = ref([]); // Lista de fechas ordenadas
const tareasAgrupadas = ref([]); // Lista de tareas agrupadas por equipo y tarea

onMounted(async () => {
  try {
    // Realiza una petición a la API para obtener las tareas
    const response = await api.get('vtaskp/');
    const tareas = response.data; // Guarda los datos obtenidos

    // Si la respuesta está vacía, no hacer nada
    if (tareas.length === 0) return;

    // Extraer la semana de los datos (es la misma para todos los registros)
    semana.value = tareas[0].semana;

    // Extraer los días únicos y fechas únicas ordenadas
    const diasUnicos = [...new Set(tareas.map(t => t.dia_semana))]; // Obtiene los nombres únicos de los días
    const fechasUnicas = [...new Set(tareas.map(t => t.fecha))].sort(); // Obtiene las fechas únicas ordenadas

    // Orden estándar de los días de la semana
    const ordenDias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
    // Filtra los días en base a los que están presentes en los datos
    diasSemana.value = ordenDias.filter(d => diasUnicos.includes(d));
    // Asigna las fechas ordenadas
    fechasOrd.value = fechasUnicas;

    // Objeto para agrupar las tareas por planta, sistema, equipo y tarea
    const agrupadas = {};
    tareas.forEach(t => {
      // Se crea una clave única combinando planta, sistema, equipo y tarea
      const key = `${t.planta}-${t.sistema}-${t.equipo} ${t.descripcion}-${t.tarea_descripcion}`;

      // Si la clave no existe en el objeto de agrupadas, se crea una nueva entrada
      if (!agrupadas[key]) {
        agrupadas[key] = {
          id: key, // Identificador único
          planta: t.planta, // Nombre de la planta
          sistema: t.sistema, // Nombre del sistema
          equipo: `${t.equipo} ${t.descripcion}`, // Equipo con la descripción concatenada
          tarea: t.tarea_descripcion, // Descripción de la tarea
          dias: {} // Objeto que almacena los turnos por día
        };
      }

      // Asigna 'D' si el turno es 'A', 'N' si es 'B' y 'DN' si es 'AB'
      agrupadas[key].dias[t.dia_semana] = {
        turno: t.turno === 'A' ? 'D' : t.turno === 'B' ? 'N' : 'DN',
        estado: t.estado // Muestra el estado de la tarea junto con el turno
      };
    });

    // Convierte el objeto de agrupadas en un array para usarlo en el template
    tareasAgrupadas.value = Object.values(agrupadas);
  } catch (error) {
    console.error("Error al obtener las tareas:", error); // Muestra el error en la consola en caso de fallar la petición
  }
});

// Función para asignar clases CSS según el turno ('D', 'N', 'DN') y estado ('P', 'R')
const getClass = (value, isEstado = false) => {
  if (isEstado) {
    return value === 'P' ? 'pending' : value === 'R' ? 'success' : ''; 
  } else {
    return value === 'D' ? 'turno-d' : value === 'N' ? 'turno-n' : value === 'DN' ? 'turno-dn' : ''; 
  }
};
</script>

<style scoped>
/* Estilos de la tabla */
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
  background-color: #f2f2f2; /* Color de fondo para los encabezados */
}

/* Estilos de las celdas según el turno */
.turno-d {
  background-color: yellow; /* Fondo amarillo para 'D' */
  font-weight: bold;
}

.turno-n {
  background-color: lightblue; /* Fondo azul claro para 'N' */
  font-weight: bold;
}

.turno-dn {
  background-color: lightgreen; /* Fondo verde claro para 'DN' */
  font-weight: bold;
}

/* Estilos de los estados */
.pending {
  color: red; /* Color rojo para tareas pendientes */
  font-weight: bold;
}

.success {
  color: green; /* Color verde para tareas completadas */
  font-weight: bold;
}
</style>
