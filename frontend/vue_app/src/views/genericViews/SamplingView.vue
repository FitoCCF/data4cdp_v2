<!--
  SamplingView.vue
  Vista principal para visualizar y generar el reporte de Muestreo de Calibración de Courier.
  Refactorizado para utilizar el componente ExcelGrid de forma explícita y sencilla.
-->
<template>
  <!-- Sección principal del componente de muestreo -->
  <section class="assays-view">
    <div class="report-wrapper">
      <!-- Tabla que estructura la cabecera oficial del reporte -->
      <table class="report-table">
        <!-- Fila 1: Logo corporativo, Título y código de control -->
        <tr>
          <td class="logo-cell">
            <div class="logo-container">
              <div class="logo-placeholder">
                <span class="logo-main">GrupoMéxico</span><br>
                <span class="logo-sub">MINERÍA</span><br>
                <span class="logo-bottom">SouthernPerú</span>
              </div>
            </div>
          </td>
          <td class="title-cell">
            <div class="title-text">FORMATO DE MUESTREO DE CALIBRACIÓN DE COURIER</div>
            <!-- Muestra el equipo en mayúsculas como en la imagen -->
            <div v-if="selectedEquipment" class="selected-equipment-title">
              {{ selectedEquipmentLabel.toUpperCase() }}
            </div>
            <div class="equipment-select-container">
              <!-- Selector para filtrar datos por equipo y cargar opciones dinámicamente -->
              <select v-model="selectedEquipment" class="header-select red-box-style">
                <option value="">-- Seleccionar Equipo --</option>
                <option v-for="eq in equipmentOptions" :key="eq.id" :value="eq.id">
                  {{ eq.label }}
                </option>
              </select>
            </div>
          </td>
          <td class="code-cell">
            <div>Código: CON-PSG-CPR-FM.005</div>
            <div>Versión: 02</div>
            <div>Página: 1 de 1</div>
          </td>
        </tr>

        <!-- Fila 2: Unidad minera fija -->
        <tr>
          <td colspan="3" class="full-width-cell">
            <div class="flex-row-space">
              <span class="label">UNIDAD MINERA:</span>
              <span class="value">Toquepala</span>
            </div>
          </td>
        </tr>

        <!-- Fila 3: Gerencia y Área fijas -->
        <tr>
          <td colspan="3" class="no-padding-cell">
            <table class="inner-table">
              <tr>
                <td class="label-cell">GERENCIA:</td>
                <td class="value-cell">Concentradora</td>
                <td class="label-cell">DEPARTAMENTO / ÁREA:</td>
                <td class="value-cell">Control de Procesos</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Fila 4: Datos variables del reporte (Fecha, Enviado Por, Operador) -->
        <tr>
          <td colspan="3" class="no-padding-cell">
            <table class="inner-table">
              <tr>
                <td class="label-cell-wide">FECHA DE MUESTREO:</td>
                <td class="input-cell">
                  <!-- Input de tipo fecha para filtrar y asignar fecha a nuevos ensayos -->
                  <input type="date" v-model="selectedDate" class="date-input red-box-style full-width" />
                </td>
                <td rowspan="3" class="right-logo-cell">
                  <div class="logo-container">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1976d2" stroke-width="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <line x1="12" y1="16" x2="12" y2="12"></line>
                      <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    <div class="logo-text-right">Control de Procesos<br>2025</div>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="label-cell-wide">ENVIADO POR:</td>
                <td class="input-cell">
                  <!-- Selector del usuario del sistema (con nombre y apellido) con estilo de texto en rojo -->
                  <select v-model="selectedUser" class="header-select red-box-style red-text-style full-width">
                    <option value="">-- Seleccionar --</option>
                    <option v-for="u in userOptions" :key="u.id" :value="u.id">
                      {{ u.nombre }} {{ u.apellido }}
                    </option>
                  </select>
                </td>
              </tr>
              <tr>
                <td class="label-cell-wide">OPERADOR DE METALURGIA:</td>
                <td class="input-cell">
                  <!-- Selector del operador metalúrgico -->
                  <select v-model="selectedMetaUser" class="header-select red-box-style full-width">
                    <option value="">-- Seleccionar --</option>
                    <option v-for="mu in metaUserOptions" :key="mu" :value="mu">
                      {{ mu }}
                    </option>
                  </select>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Mensajes de Carga y Errores del Servidor -->
      <div v-if="loading" class="state-message">Cargando datos...</div>
      <div v-else-if="error" class="state-message error">{{ error }}</div>

      <!-- Contenedor del grid de Excel reutilizable -->
      <div class="table-container">
        <!-- Instanciamos ExcelGrid pasándole las cabeceras, grupos, datos y eventos correspondientes -->
        <ExcelGrid
          title="Detalle de Muestreo de Ensayos"
          :headers="headers"
          :headerGroups="headerGroups"
          :data="gridData"
          :columnsConfig="columnsConfig"
          @save="handleSave"
          @delete="handleDelete"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
// Importamos dependencias reactivas de Vue
import { ref, computed, onMounted, watch } from 'vue';
// Importamos el cliente HTTP API configurado
import { api } from '../../api';
// Importamos el composable de control de llamadas a la API
import { useApi } from '../../composables/useApi';
// Importamos el componente reutilizable ExcelGrid
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos la función de utilidades compartida para construir el payload sanitizado
import { buildPayloadFromRow } from '../../utils/gridHelpers';

// --- Estado Reactivo ---
// Fecha seleccionada por defecto es la fecha actual (ISO string)
const selectedDate = ref(new Date().toISOString().split('T')[0]);
// ID del equipo seleccionado en el filtro
const selectedEquipment = ref('');
// ID del usuario que envía (enviado por)
const selectedUser = ref('');
// Nombre del operador metalurgista seleccionado
const selectedMetaUser = ref('');

// Lista cruda de ensayos obtenidos desde la API
const assays = ref([]);
// Diccionarios para acceso rápido a relaciones por ID
const samplesById = ref({});
const usersById = ref({});
const userPsById = ref({});

// Listas para las opciones de los dropdowns en la cabecera
const equipmentOptions = ref([]);
const userOptions = ref([]);
const metaUserOptions = ref([]);

// Extraemos los estados reactivos de red y la función execute
const { loading, error, execute } = useApi();

// --- Configuración de Columnas para ExcelGrid ---
// Nombres de las cabeceras individuales de columnas a mostrar
const headers = [
  'ID DB',             // Columna 0: ID base de datos (clave primaria de sólo lectura)
  'CÓDIGO',            // Columna 1: chemical_id del ensayo
  'MUESTRA',           // Columna 2: sample (ID de la Muestra)
  'SN',                // Columna 3: tag de la Muestra
  'ID',                // Columna 4: instance del ensayo
  'HORA',              // Columna 5: time del ensayo
  'TARA',              // Columna 6: tara del ensayo
  'PESO TOTAL',        // Columna 7: tweight del ensayo
  'PESO SECO',         // Columna 8: dweight del ensayo
  '% SÓLIDOS',         // Columna 9: pSol del ensayo
  '%Fe',               // Columna 10: pFe del ensayo
  '%Cu',               // Columna 11: pCu del ensayo
  '%Zn',               // Columna 12: pZn del ensayo
  '%Mo',               // Columna 13: pMo del ensayo
  '%Ins'               // Columna 14: pIns del ensayo
];

// Nombres de las llaves en el modelo correspondientes a cada columna de la matriz
const colKeys = [
  'id',
  'chemical_id',
  'sample',
  'sample__tag',       // Campo de muestra anidada (ignorado al guardar por buildPayloadFromRow al contener '__')
  'instance',
  'time',
  'tara',
  'tweight',
  'dweight',
  'pSol',
  'pFe',
  'pCu',
  'pZn',
  'pMo',
  'pIns'
];

// Configuración de los grupos de cabeceras en base a colspans del formulario físico
const headerGroups = [
  { label: '', colspan: 10 }, // Las primeras 10 columnas (incluyendo la oculta) no tienen etiqueta
  { label: 'ELEMENTOS POR ANALIZAR', colspan: 5 } // Las últimas 5 columnas (porcentajes de elementos)
];

// --- Propiedades Computadas ---

// Extrae la descripción o nombre limpio del equipo seleccionado
const selectedEquipmentLabel = computed(() => {
  const eq = equipmentOptions.value.find(e => e.id == selectedEquipment.value);
  if (eq) {
    const parts = eq.label.split('-');
    if (parts.length > 1) {
      return parts[1].trim(); // Extrae la parte de descripción, por ejemplo: "COURIER COBRE C2"
    }
    return eq.label;
  }
  return '';
});

// Configura dinámicamente las columnas en el Grid (ej. dropdown selector de muestras)
const columnsConfig = computed(() => {
  // Filtramos la lista de muestras para mostrar sólo las correspondientes al equipo seleccionado en el reporte
  const filteredSamples = Object.values(samplesById.value).filter(s => {
    if (!selectedEquipment.value) return true;
    const eqId = (typeof s.equipment === 'object') ? s.equipment.id : s.equipment;
    return eqId == selectedEquipment.value;
  });

  return {
    // La columna index 0 es 'ID DB' y la ocultamos mediante la clase CSS 'hidden-column'
    0: {
      headerClass: 'hidden-column'
    },
    // La columna index 2 ("MUESTRA") se comporta como un dropdown con las muestras de este equipo
    2: {
      type: 'select',
      options: filteredSamples.map(s => ({
        value: s.id,
        label: s.name
      }))
    }
  };
});

// Filtra localmente los ensayos según la fecha y equipo seleccionados en la cabecera
const filteredAssays = computed(() => {
  return assays.value.filter(a => {
    // 1. Filtrar por Fecha
    if (selectedDate.value && a.date !== selectedDate.value) return false;

    // 2. Filtrar por Equipo
    if (selectedEquipment.value) {
      // Extraemos el ID de la muestra de forma segura (objeto o ID directo)
      const sampleId = a.sample && typeof a.sample === 'object' ? a.sample.id : a.sample;
      const s = samplesById.value[sampleId];
      let eqId = null;
      if (s && s.equipment) {
        eqId = (typeof s.equipment === 'object') ? s.equipment.id : s.equipment;
      }
      if (eqId != selectedEquipment.value) return false;
    }

    return true;
  });
});

// Convierte el array de objetos filtrado a una matriz plana bidimensional para ser leída por ExcelGrid
const gridData = computed(() => {
  return filteredAssays.value.map(assay => {
    // Identificar el ID de muestra asociado al ensayo
    const sampleId = assay.sample && typeof assay.sample === 'object' ? assay.sample.id : assay.sample;
    const sampleObj = samplesById.value[sampleId];
    
    // SN corresponde exactamente al valor de la columna 'tag' de la muestra en la base de datos
    const snValue = sampleObj ? sampleObj.tag : '';

    return [
      assay.id || '',                  // Columna 0: ID base de datos (PK read-only)
      assay.chemical_id || '',         // Columna 1: Código químico
      sampleId || '',                  // Columna 2: ID de la Muestra (para dropdown select)
      snValue,                         // Columna 3: SN (Mapeado a 'tag' de la muestra)
      assay.instance || '',            // Columna 4: ID de Instancia
      formatTime(assay.time),          // Columna 5: Hora formateada HH:MM
      formatNumber(assay.tara),        // Columna 6: Peso Tara
      formatNumber(assay.tweight),     // Columna 7: Peso Total
      formatNumber(assay.dweight),     // Columna 8: Peso Seco
      formatNumber(assay.pSol),        // Columna 9: % Sólidos
      formatNumber(assay.pFe),         // Columna 10: %Fe
      formatNumber(assay.pCu),         // Columna 11: %Cu
      formatNumber(assay.pZn),         // Columna 12: %Zn
      formatNumber(assay.pMo),         // Columna 13: %Mo
      formatNumber(assay.pIns)         // Columna 14: %Ins
    ];
  });
});



// --- Métodos de API y Comunicación ---

// Extrae y construye la lista de operadores y pre-pobla los campos "Enviado Por" y "Operador de Metalurgia"
const updateHeaderFieldsFromAssays = () => {
  // Construye la lista única de operadores metalúrgicos
  const metas = new Set();
  
  // Agrega los operadores registrados en los ensayos actuales
  assays.value.forEach(a => {
    if (a.meta_user) metas.add(a.meta_user);
  });
  
  // Agrega todos los nombres de los usuarios del sistema como opciones disponibles
  userOptions.value.forEach(u => metas.add(`${u.nombre} ${u.apellido}`));
  metaUserOptions.value = Array.from(metas).sort();

  // Si hay ensayos cargados, pre-poblamos el selector de "Enviado Por" y "Operador de Metalurgia"
  if (assays.value.length > 0) {
    // Busca el primer ensayo que tenga un usuario registrado y asigna su ID
    const firstWithUser = assays.value.find(a => a.user);
    if (firstWithUser) {
      selectedUser.value = (firstWithUser.user && typeof firstWithUser.user === 'object')
        ? firstWithUser.user.id
        : (firstWithUser.user || '');
    } else {
      selectedUser.value = '';
    }

    // Busca el primer ensayo que tenga un operador metalúrgico asignado
    const firstWithMeta = assays.value.find(a => a.meta_user);
    if (firstWithMeta) {
      selectedMetaUser.value = firstWithMeta.meta_user;
    } else {
      selectedMetaUser.value = '';
    }
  } else {
    // Si no hay ensayos para este filtro, limpiamos las selecciones
    selectedUser.value = '';
    selectedMetaUser.value = '';
  }
};

// Carga los ensayos de la base de datos aplicando la fecha seleccionada para evitar límites de paginación
const loadAssays = async () => {
  // Si no hay un equipo seleccionado en la parte superior, limpiamos los datos y evitamos la consulta
  if (!selectedEquipment.value) {
    assays.value = [];
    selectedUser.value = '';
    selectedMetaUser.value = '';
    return;
  }

  await execute(async () => {
    const params = {
      page_size: 10000 // Tamaño de página grande para recuperar todos los registros diarios
    };
    if (selectedDate.value) {
      params.date = selectedDate.value;
    }
    if (selectedEquipment.value) {
      params.sample__equipment = selectedEquipment.value;
    }

    const res = await api.get('assays/', { params });
    assays.value = res.data.results || res.data || [];

    // Llamamos a la pre-población y configuración de operadores en base a los ensayos cargados
    updateHeaderFieldsFromAssays();
  }, 'Error al cargar los ensayos del servidor.');
};

// Carga los datos de catálogos iniciales para los filtros y selects del reporte
const loadData = async () => {
  await execute(async () => {
    // Descarga en paralelo muestras, usuarios, perfiles y equipos del sistema
    const [samplesRes, usersRes, userPsRes, equipRes] = await Promise.all([
      api.get('samples/', { params: { page_size: 10000 } }),
      api.get('users/', { params: { page_size: 10000 } }).catch(() => ({ data: [] })),
      api.get('userp/', { params: { page_size: 10000 } }).catch(() => ({ data: [] })),
      api.get('equipments/', { params: { page_size: 10000 } }).catch(() => ({ data: [] }))
    ]);

    // Mapea las muestras a un diccionario indexado por ID
    const samples = samplesRes.data.results || samplesRes.data || [];
    samplesById.value = samples.reduce((acc, s) => {
      acc[s.id] = s;
      return acc;
    }, {});

    // Mapea los usuarios a un diccionario y lista
    const users = usersRes.data.results || usersRes.data || [];
    userOptions.value = users;
    usersById.value = users.reduce((acc, u) => {
      acc[u.id] = u;
      return acc;
    }, {});

    // Mapea los perfiles UserP a un diccionario
    const userPs = userPsRes.data.results || userPsRes.data || [];
    userPsById.value = userPs.reduce((acc, up) => {
      acc[up.id] = up;
      return acc;
    }, {});

    // Filtra las opciones de Equipos permitidas para este formato específico
    const equips = equipRes.data.results || equipRes.data || [];
    const allowedEquipments = [1, 2, 5, 6];
    equipmentOptions.value = equips
      .filter(e => allowedEquipments.includes(e.id))
      .map(e => ({
        id: e.id,
        label: `${e.name} - ${e.description}`
      })).sort((a, b) => a.label.localeCompare(b.label));

    // Carga los ensayos asociados (que llamará internamente a updateHeaderFieldsFromAssays)
    await loadAssays();
  }, 'Error al cargar los datos del servidor.');
};

// --- Manejadores de Eventos del Componente ExcelGrid ---

// Guarda los cambios realizados en ExcelGrid (tanto inserciones como ediciones) hacia el backend
const handleSave = async (updatedGrid) => {
  try {
    await execute(async () => {
      const promises = updatedGrid.map(row => {
        // Mapea la fila editada a un payload estructurado usando el helper
        const payload = buildPayloadFromRow(row, colKeys);

        // Añade valores variables de la cabecera del reporte físico
        payload.date = selectedDate.value;
        payload.user_id = selectedUser.value ? selectedUser.value : null;
        payload.meta_user = selectedMetaUser.value ? selectedMetaUser.value : null;

        const id = payload.id;
        // Si el registro ya existe en base de datos ejecuta PUT, si no ejecuta POST
        if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
          return api.put(`assays/${id}/`, payload);
        } else {
          delete payload.id;
          return api.post('assays/', payload);
        }
      });

      // Ejecuta todas las peticiones de guardado en paralelo
      await Promise.all(promises);
      alert('Cambios guardados correctamente.');
      // Vuelve a solicitar los ensayos actualizados a la API
      await loadAssays();
    });
  } catch (err) {
    alert('Error al guardar. Revisa el mensaje de error en pantalla.');
  }
};

// Elimina registros seleccionados en la tabla ExcelGrid de la base de datos
const handleDelete = async (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  try {
    await execute(async () => {
      // Mapea los ids de los ensayos seleccionados para eliminarlos
      const deletePromises = idsToDelete.map(id => api.delete(`assays/${id}/`));
      await Promise.all(deletePromises);
      alert(`${idsToDelete.length} ensayo(s) eliminado(s) correctamente.`);
      // Vuelve a solicitar los ensayos actualizados a la API
      await loadAssays();
    });
  } catch (err) {
    alert('Ocurrió un error al eliminar los registros.');
  }
};

// --- Vigilantes (Watchers) ---
// Recarga dinámicamente los ensayos de la base de datos si cambia la fecha o el equipo en la cabecera
watch([selectedDate, selectedEquipment], async () => {
  await loadAssays();
});

// --- Helpers Auxiliares ---

// Corta los segundos de la hora si es necesario
const formatTime = (timeStr) => {
  if (!timeStr) return '';
  return timeStr.length > 5 ? timeStr.substring(0, 5) : timeStr;
};

// Formatea números
const formatNumber = (val) => {
  if (val === null || val === undefined) return '';
  return val;
};

// --- Ciclo de Vida ---
onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* Contenedor principal de la vista */
.assays-view {
  font-family: 'Arial', sans-serif;
  color: #000;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  background: white;
  padding: 20px;
  box-sizing: border-box;
  overflow-x: auto; /* Permite el scroll de toda la hoja junta si supera la pantalla */
}

/* Envolvedor del reporte para alinear el encabezado y la tabla al mismo ancho */
.report-wrapper {
  width: max-content;
  margin: 0 auto;
}

/* Estilos de la tabla de reporte que replica el formato físico */
.report-table {
  width: 100% !important;
  border-collapse: collapse;
  margin-bottom: 20px;
  border: 1px solid #000;
  box-sizing: border-box;
}

.report-table td {
  border: 1px solid #000;
  padding: 5px;
  vertical-align: middle;
}

.logo-cell {
  width: 20%;
  text-align: center;
}
.logo-main {
  font-weight: bold;
  font-size: 1.1rem;
  color: #c62828;
}
.logo-sub {
  font-size: 0.8rem;
  color: #555;
  letter-spacing: 2px;
}
.logo-bottom {
  font-weight: bold;
  font-size: 0.9rem;
  color: #555;
}

.title-cell {
  width: 60%;
  text-align: center;
}
.title-text {
  font-weight: bold;
  font-size: 1.1rem;
  margin-bottom: 5px;
}
.selected-equipment-title {
  font-weight: bold;
  font-size: 1rem;
  margin-bottom: 5px;
  color: #000;
}
.equipment-select-container {
  display: inline-block;
  padding: 2px;
  min-width: 250px;
}

.code-cell {
  width: 20%;
  font-size: 0.8rem;
  text-align: right;
  vertical-align: top;
  line-height: 1.4;
}

.full-width-cell {
  font-weight: bold;
}
.flex-row-space {
  display: flex;
  justify-content: space-between;
  width: 100%;
  align-items: center;
}

.no-padding-cell {
  padding: 0 !important;
}

.inner-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
  border: none;
}
.inner-table tr {
  border-bottom: 1px solid #000;
}
.inner-table tr:last-child {
  border-bottom: none;
}
.inner-table td {
  border: none;
  border-right: 1px solid #000;
  padding: 5px;
}
.inner-table td:last-child {
  border-right: none;
}

.label-cell {
  width: 20%;
  font-weight: bold;
  background-color: #f5f5f5;
}
.value-cell {
  width: 30%;
}

.label-cell-wide {
  width: 30%;
  font-weight: bold;
}
.input-cell {
  width: 40%;
}
.right-logo-cell {
  width: 30%;
  text-align: center;
  vertical-align: middle;
}

/* Campos de entrada con línea discontinua (simula el formato físico de la imagen) */
.date-input, .header-select {
  border: none;
  border-bottom: 1px dashed #000;
  background: transparent;
  font-family: inherit;
  font-size: 1rem;
  font-weight: bold;
  outline: none;
  cursor: pointer;
  color: #000;
  text-align: left;
  text-align-last: left;
}

/* Cambiar texto a color rojo en el selector de usuario enviado por */
.red-text-style {
  color: #c62828 !important;
}

.red-box-style {
  padding: 2px 5px;
  font-weight: bold;
}
.full-width {
  width: 100%;
  box-sizing: border-box;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.logo-text-right {
  font-size: 0.8rem;
  color: #1976d2;
  font-weight: bold;
  margin-top: 5px;
}

/* Contenedor de la tabla */
.table-container {
  overflow-x: auto;
  margin-top: 20px;
  width: max-content; /* Se ajusta exactamente al ancho de excel-container */
}

/* Forzar que el table-wrapper de ExcelGrid muestre todas las columnas sin scroll interno */
.table-container :deep(.table-wrapper) {
  overflow: visible !important;
}

.table-container :deep(.excel-container) {
  width: max-content !important;
}

/* --- OVERRIDES DEL DISEÑO DE EXCELGRID MEDIANTE DEEP SELECTORS --- */

/* Ocultar la primera columna (ID DB de la base de datos) */
.table-container :deep(.hidden-column) {
  display: none !important;
}
.table-container :deep(.excel-table td[data-col-index="0"]) {
  display: none !important;
}

/* Estilo para las cabeceras individuales (Fondo verde pastel y bordes negros) */
.table-container :deep(.excel-table th) {
  background-color: #e2f0d9 !important; /* Verde menta claro */
  color: #000000 !important;
  font-weight: bold !important;
  border: 1px solid #000000 !important;
  text-align: center !important;
  font-size: 0.85rem !important;
}

/* El grupo de cabecera 'ELEMENTOS POR ANALIZAR' (Fondo gris como en la imagen) */
.table-container :deep(.excel-table th.group-header-cell) {
  background-color: #d9d9d9 !important; 
}

/* El primer grupo de cabecera que es vacío para alinear las columnas del lado izquierdo */
.table-container :deep(.excel-table th.group-header-cell:first-of-type) {
  background-color: transparent !important;
  border: none !important;
  border-bottom: 1px solid #000000 !important; 
}

/* Celdas del grid con bordes negros sólidos */
.table-container :deep(.excel-table td) {
  border: 1px solid #000000 !important;
  font-size: 0.85rem !important;
  height: 30px !important;
  padding: 4px 6px !important;
  text-align: center !important;
}

/* Estilos de color azul para celdas de CÓDIGO, ID y HORA */
.table-container :deep(.excel-table td[data-col-index="1"]),
.table-container :deep(.excel-table td[data-col-index="4"]),
.table-container :deep(.excel-table td[data-col-index="5"]) {
  color: #0056b3 !important;
  font-weight: bold;
}

/* Negrita para la columna SN */
.table-container :deep(.excel-table td[data-col-index="3"]) {
  font-weight: bold !important;
}

/* Mensajes de estado (cargando / error) */
.state-message {
  text-align: center;
  padding: 10px;
}
.state-message.error {
  color: red;
}
</style>
