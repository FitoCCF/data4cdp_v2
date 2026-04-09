<template>
  <div class="schedule-view-container">
    <div class="header-actions">
      <h2>Calendario de Rotación por Grupos</h2>
      <p class="subtitle">Proyección de 7 semanas (49 días)</p>
    </div>

    <!-- 
      Reutilizamos tu componente ExcelGrid pasándole arrays simples.
    -->
    <div class="grid-wrapper">
      <ExcelGrid 
        title="Rotación de Turnos (49 días)"
        :headers="gridColumns" 
        :data="gridData" 
      />
      
      <!-- Overlay de carga y mensajes de error -->
      <div v-if="loading" class="loading-overlay">Cargando datos del calendario...</div>
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
// Subimos un nivel en la estructura para alcanzar components/
import ExcelGrid from '../../components/ExcelGrid.vue'; 
import { api } from '../../api';

const gridColumns = ref([]);
const gridData = ref([]);
const loading = ref(false);
const error = ref(null);

const loadCalendarData = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    // Si tu endpoint se llama distinto en Django, cambia 'calendars/' por 'calendar/' 
    const response = await api.get('calendars/', { params: { page_size: 10000 } });
    let data = response.data.results || response.data;
    
    if (!Array.isArray(data) || data.length === 0) {
      error.value = "No se encontraron registros de turnos en la base de datos.";
      gridColumns.value = ['Grupo (Calendar)'];
      gridData.value = [];
      return;
    }

    // 1. Extraer todas las fechas únicas y ordenarlas
    const allUniqueDates = [...new Set(data.map(item => item.date))].sort();
    
    // 2. Usar estrictamente las fechas que vienen de la base de datos
    // (Como la BD ya tiene todos los días registrados, no generamos días artificiales)
    let projectedDates = allUniqueDates;

    // 3. Generar Columnas para el ExcelGrid
    const cols = ['Grupo (Calendar)'];
    projectedDates.forEach(dateStr => {
      // dateStr viene en formato YYYY-MM-DD
      const [year, month, day] = dateStr.split('-');
      cols.push(`${parseInt(month)}/${parseInt(day)}`);
    });
    gridColumns.value = cols;

    // 4. Agrupar los turnos por Grupo y Fecha
    const groupedData = {};
    data.forEach(item => {
      // Si item.group (UserP) existe, toma su nombre. Si no, usa su ID como fallback.
      const groupName = item.group ? (item.group.name || item.group.nombre || `Grupo ${item.group.id}`) : `Grupo ID ${item.group_id || 'Desconocido'}`;
      
      if (!groupedData[groupName]) {
        groupedData[groupName] = {};
      }
      groupedData[groupName][item.date] = item.turn;
    });

    // 5. Construir las filas (Array de Arrays) para el ExcelGrid
    const rows = Object.keys(groupedData).map(groupName => {
      const rowData = [groupName];
      projectedDates.forEach(dateStr => {
        rowData.push(groupedData[groupName][dateStr] || 'x');
      });
      return rowData;
    });

    gridData.value = rows;

  } catch (err) {
    console.error('Error cargando los datos del calendario:', err);
    error.value = 'Ocurrió un error al intentar obtener el calendario desde la base de datos.';
  } finally {
    loading.value = false;
  }
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
  margin-bottom: 20px;
}
.subtitle {
  color: #6c757d;
}
.grid-wrapper {
  position: relative;
  height: calc(100% - 80px); /* Deja espacio para que el grid ocupe bien la pantalla */
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
</style>