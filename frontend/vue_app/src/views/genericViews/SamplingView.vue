<!--
  SamplingView.vue
  Vista principal para visualizar y generar el reporte de Muestreo de Calibración de Courier.
  Refactorizado para utilizar el componente ExcelGrid de forma explícita y sencilla.
-->
<template>
  <!-- Sección principal del componente de muestreo -->
  <section class="assays-view">
    <!-- Barra de herramientas superior para acciones (Oculta en impresión y no afecta el diseño oficial) -->
    <div class="report-toolbar no-print">
      <div class="toolbar-left">
        <span class="report-badge">📋 FORMATO CON-PSG-CPR-FM.005</span>
        <span class="report-version">Versión 02</span>
      </div>
      <div class="toolbar-actions">
        <button
          type="button"
          class="btn-toolbar btn-excel"
          :disabled="loading || gridData.length === 0"
          @click="exportToExcel"
          title="Exportar reporte a Excel (.xlsx) con el formato y cabecera oficial"
        >
          <span class="btn-icon">📥</span> Exportar a Excel
        </button>
        <button
          type="button"
          class="btn-toolbar btn-print"
          :disabled="loading"
          @click="printReport"
          title="Imprimir formato oficial (sin controles de edición ni sincronización)"
        >
          <span class="btn-icon">🖨️</span> Imprimir
        </button>
      </div>
    </div>

    <div class="report-wrapper">
      <!-- Tabla que estructura la cabecera oficial del reporte exactamente según formato CON-PSG-CPR-FM.005 -->
      <table class="report-table">
        <!-- Filas 1 a 4 del Excel: Logo corporativo, Título con Equipo y Código de control -->
        <tr class="row-header-top">
          <td class="logo-cell">
            <div class="logo-container">
              <img :src="logoSouthern" alt="Grupo México Southern Perú" class="corporate-logo" />
            </div>
          </td>
          <td class="title-cell">
            <div class="title-text">FORMATO DE MUESTREO DE CALIBRACIÓN DE COURIER</div>
            <!-- Muestra el equipo en mayúsculas como en la hoja de Excel -->
            <div class="selected-equipment-title">
              {{ selectedEquipmentLabel ? selectedEquipmentLabel.toUpperCase() : 'COURIER COBRE C2' }}
            </div>
            <div class="equipment-select-container screen-only">
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
            <div class="code-box">
              <div class="code-line"><span class="code-label">Código:</span> CON-PSG-CPR-FM.005</div>
              <div class="code-line"><span class="code-label">Versión:</span> 02</div>
              <div class="code-line"><span class="code-label">Página:</span> 1 de 1</div>
            </div>
          </td>
        </tr>

        <!-- Fila 5 del Excel: Unidad minera fija -->
        <tr class="row-unidad-minera">
          <td colspan="3" class="full-width-cell">
            <div class="flex-row-header">
              <span class="label-header">UNIDAD MINERA:</span>
              <span class="value-header">Toquepala</span>
            </div>
          </td>
        </tr>

        <!-- Fila 6 del Excel: Gerencia y Área fijas -->
        <tr class="row-gerencia-area">
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

        <!-- Filas 8 a 10 del Excel: Datos variables del reporte (Fecha, Enviado Por, Operador) y Logo Control de Procesos -->
        <tr class="row-meta-section">
          <td colspan="3" class="no-padding-cell">
            <table class="inner-table meta-table">
              <tr>
                <td class="label-cell-wide">FECHA DE MUESTREO:</td>
                <td class="input-cell">
                  <!-- Pantalla: Selector interactivo de fecha -->
                  <input type="date" v-model="selectedDate" class="date-input screen-only" />
                  <!-- Impresión: Texto limpio formateado -->
                  <span class="print-only value-text">{{ formatDateDisplay(selectedDate) }}</span>
                </td>
                <td rowspan="3" class="right-logo-cell">
                  <div class="logo-container right-logo-container">
                    <img :src="logoControl" alt="Control de Procesos 2025" class="department-logo" />
                  </div>
                </td>
              </tr>
              <tr>
                <td class="label-cell-wide">ENVIADO POR:</td>
                <td class="input-cell">
                  <!-- Pantalla: Selector del usuario -->
                  <select v-model="selectedUser" class="header-select red-text-style screen-only">
                    <option value="">-- Seleccionar --</option>
                    <option v-for="u in userOptions" :key="u.id" :value="u.id">
                      {{ u.nombre }} {{ u.apellido }}
                    </option>
                  </select>
                  <!-- Impresión: Nombre en texto rojo oficial -->
                  <span class="print-only value-text red-text-style">{{ selectedUserName || '-' }}</span>
                </td>
              </tr>
              <tr>
                <td class="label-cell-wide">OPERADOR DE METALURGIA:</td>
                <td class="input-cell">
                  <!-- Pantalla: Selector de operador metalúrgico -->
                  <select v-model="selectedMetaUser" class="header-select screen-only">
                    <option value="">-- Seleccionar --</option>
                    <option v-for="mu in metaUserOptions" :key="mu" :value="mu">
                      {{ mu }}
                    </option>
                  </select>
                  <!-- Impresión: Texto de operador limpio -->
                  <span class="print-only value-text">{{ selectedMetaUser || '-' }}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Mensajes de Carga y Errores del Servidor -->
      <div v-if="loading" class="state-message no-print">Cargando datos...</div>
      <div v-else-if="error" class="state-message error no-print">{{ error }}</div>

      <!-- Contenedor del grid de Excel reutilizable (Celdas y cálculos sin modificar) -->
      <div class="table-container">
        <!-- Instanciamos ExcelGrid pasándole las cabeceras, grupos, datos y eventos correspondientes -->
        <ExcelGrid
          title="Detalle de Muestreo de Ensayos"
          :headers="headers"
          :headerGroups="headerGroups"
          :data="gridData"
          :columnsConfig="columnsConfig"
          :rowCalculator="calculateSamplingRow"
          @save="handleSave"
          @delete="handleDelete"
        >
          <!-- Botón para sincronizar manualmente con la API del Courier a la altura de 'Habilitar Edición' (Oculto en impresión) -->
          <template #actions-end>
            <button
              type="button"
              class="sync-courier-btn no-print"
              :disabled="loading || isSyncing || !selectedEquipment"
              title="Consultar y sincronizar con la API del analizador Courier para la fecha y equipo seleccionados"
              @click="handleManualSync"
            >
              {{ isSyncing ? '⏳ Verificando API...' : '🔄 Sincronizar API Courier' }}
            </button>
          </template>
        </ExcelGrid>
      </div>
    </div>
  </section>
</template>

<script setup>
// Importamos dependencias reactivas de Vue
import { ref, computed, onMounted, watch } from 'vue';
// Importamos SheetJS para exportación a Excel oficial
import * as XLSX from 'xlsx';
// Importamos logos corporativos extraídos del formato oficial
import logoSouthern from '../../assets/courier_image3.png';
import logoControl from '../../assets/courier_image2.png';
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
  // Ordenar los ensayos por la columna SN (tag de la muestra) en orden alfanumérico natural
  const sortedAssays = [...filteredAssays.value].sort((a, b) => {
    const sampleIdA = a.sample && typeof a.sample === 'object' ? a.sample.id : a.sample;
    const sampleIdB = b.sample && typeof b.sample === 'object' ? b.sample.id : b.sample;
    const tagA = (samplesById.value[sampleIdA]?.tag || '').toString();
    const tagB = (samplesById.value[sampleIdB]?.tag || '').toString();

    const snComparison = tagA.localeCompare(tagB, undefined, { numeric: true, sensitivity: 'base' });
    if (snComparison !== 0) return snComparison;

    // Criterio secundario: ID de instancia o ID del ensayo
    const instA = (a.instance || '').toString();
    const instB = (b.instance || '').toString();
    return instA.localeCompare(instB, undefined, { numeric: true, sensitivity: 'base' });
  });

  return sortedAssays.map(assay => {
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

// Variable reactiva para controlar el estado de sincronización manual con la API
const isSyncing = ref(false);

// Carga los ensayos EXCLUSIVAMENTE desde la base de datos local aplicando la fecha y equipo seleccionados
const loadAssays = async () => {
  // Si no hay un equipo seleccionado en la parte superior, limpiamos los datos y evitamos la consulta
  if (!selectedEquipment.value) {
    assays.value = [];
    selectedUser.value = '';
    selectedMetaUser.value = '';
    return;
  }

  await execute(async () => {
    // Parámetros para filtrar ensayos por fecha y equipo en la base de datos local
    const params = {
      page_size: 10000 // Tamaño de página grande para recuperar todos los registros diarios
    };
    if (selectedDate.value) {
      params.date = selectedDate.value;
    }
    if (selectedEquipment.value) {
      params.sample__equipment = selectedEquipment.value;
    }

    // CONSULTA ESTRICTA Y EXCLUSIVAMENTE A LA BASE DE DATOS LOCAL (PostgreSQL/TimescaleDB)
    const res = await api.get('assays/', { params });
    assays.value = res.data.results || res.data || [];

    // Llamamos a la pre-población y configuración de operadores en base a los ensayos cargados
    updateHeaderFieldsFromAssays();
  }, 'Error al cargar los ensayos desde la base de datos.');
};

// Sincronización MANUAL con la API externa del analizador Courier activada únicamente mediante el botón
const handleManualSync = async () => {
  // 1. Validamos que se haya seleccionado un equipo Courier
  if (!selectedEquipment.value) {
    alert('Por favor, selecciona primero un equipo Courier para consultar y sincronizar su API.');
    return;
  }

  // 2. Validamos que se haya seleccionado una fecha
  if (!selectedDate.value) {
    alert('Por favor, selecciona una fecha para verificar los datos en la API.');
    return;
  }

  isSyncing.value = true;
  try {
    // Petición al endpoint backend que verifica la existencia de datos en la API del Courier para la fecha y equipo
    const syncRes = await api.post('assays/sync-equipment/', {
      equipment_id: selectedEquipment.value,
      date: selectedDate.value
    });

    const data = syncRes.data || {};

    // Notificación explícita de validación de datos en la API
    if (data.status === 'ok') {
      if (data.found_in_api === 0) {
        alert(`ℹ️ Verificación en API: No existen datos registrados en la API del Courier para la fecha ${selectedDate.value}.`);
      } else if (data.inserted > 0) {
        alert(`✅ Sincronización exitosa: Se encontraron ${data.found_in_api} registro(s) en la API y se insertaron ${data.inserted} nuevo(s) en la base de datos.`);
      } else {
        alert(`ℹ️ Verificación en API: Se encontraron ${data.found_in_api} registro(s) en la API para la fecha ${selectedDate.value}. Todos ya se encontraban registrados en la base de datos.`);
      }
    } else {
      alert(`⚠️ Aviso: ${data.message || 'No se pudo completar la sincronización con el analizador.'}`);
    }

    // Tras la sincronización con la API, recargamos los ensayos actualizados desde la base de datos local
    await loadAssays();
  } catch (syncErr) {
    console.error('Error al sincronizar con la API Courier:', syncErr);
    const errorDetail = syncErr.response?.data?.error || syncErr.message || 'Error de conexión con el analizador Courier.';
    alert(`❌ Error al conectar con la API: ${errorDetail}`);
  } finally {
    isSyncing.value = false;
  }
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

// Calcula automáticamente % SÓLIDOS (col 9) a partir de TARA (col 6), PESO TOTAL (col 7) y PESO SECO (col 8)
// Fórmula: (PESO SECO) / (PESO TOTAL - TARA) * 100
// Si el usuario edita directamente % SÓLIDOS (col 9), se preserva la edición manual del operador.
const calculateSamplingRow = (row, changedColIndex) => {
  const weightCols = [6, 7, 8];

  // Si el cambio fue en una columna posterior a los pesos (ej. edición manual directa de % SÓLIDOS en col 9), respetarlo
  if (changedColIndex !== undefined && !weightCols.includes(changedColIndex) && changedColIndex > 8) {
    return;
  }

  const taraVal = row[6];
  const tweightVal = row[7];
  const dweightVal = row[8];

  if (
    taraVal !== '' && tweightVal !== '' && dweightVal !== '' &&
    taraVal !== null && tweightVal !== null && dweightVal !== null &&
    taraVal !== undefined && tweightVal !== undefined && dweightVal !== undefined
  ) {
    const tara = parseFloat(String(taraVal).replace(',', '.'));
    const tweight = parseFloat(String(tweightVal).replace(',', '.'));
    const dweight = parseFloat(String(dweightVal).replace(',', '.'));

    if (!isNaN(tara) && !isNaN(tweight) && !isNaN(dweight)) {
      const netWeight = tweight - tara;
      if (netWeight > 0) {
        const pSol = (dweight / netWeight) * 100;
        row[9] = parseFloat(pSol.toFixed(2));
      }
    }
  }
};

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

// Nombre del usuario seleccionado para visualización limpia en impresión y exportación
const selectedUserName = computed(() => {
  const u = userOptions.value.find(usr => usr.id == selectedUser.value);
  if (u) return `${u.nombre} ${u.apellido}`;
  return '';
});

// Formatea la fecha ISO (YYYY-MM-DD) a formato DD/MM/YYYY para impresión y Excel
const formatDateDisplay = (dateStr) => {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return dateStr;
};

// Imprime el formato oficial ocultando controles de edición y botones
const printReport = () => {
  window.print();
};

// Exporta el reporte a Excel (.xlsx) replicando exactamente la estructura de la cabecera CON-PSG-CPR-FM.005
// Excluye controles de edición, botones de sincronización e IDs internos de BD
const exportToExcel = () => {
  if (!gridData.value || gridData.value.length === 0) {
    alert('No hay datos disponibles para exportar.');
    return;
  }

  const wsData = [];
  const eqName = selectedEquipmentLabel.value ? selectedEquipmentLabel.value.toUpperCase() : 'COURIER COBRE C2';

  // Fila 1 a 4 del Excel: Cabecera principal (Título, Logos y Control)
  wsData.push([
    'Grupo México\nSouthern Perú', '',
    `FORMATO DE MUESTREO DE CALIBRACIÓN DE COURIER\n${eqName}`, '', '', '', '', '', '', '', '',
    'Código: CON-PSG-CPR-FM.005\nVersión: 02\nPágina: 1 de 1', '', ''
  ]);
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);

  // Fila 5: Unidad Minera
  wsData.push(['UNIDAD MINERA:', '', 'Toquepala', '', '', '', '', '', '', '', '', '', '', '']);

  // Fila 6: Gerencia y Área
  wsData.push([
    'GERENCIA:', '', 'Concentradora', '', '', '', '', '',
    'DEPARTAMENTO / ÁREA:', '', '', 'Control de Procesos', '', ''
  ]);

  // Fila 7: Espaciador
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);

  // Fila 8: Fecha de Muestreo y Logo derecho
  const displayDate = formatDateDisplay(selectedDate.value) || selectedDate.value;
  wsData.push([
    'FECHA DE MUESTREO:', '', displayDate, '', '', '', '', '',
    '', '', '', '', 'Control de Procesos\n2025', ''
  ]);

  // Fila 9: Enviado Por
  wsData.push([
    'ENVIADO POR:', '', selectedUserName.value || '', '', '', '', '', '',
    '', '', '', '', '', ''
  ]);

  // Fila 10: Operador de Metalurgia
  wsData.push([
    'OPERADOR DE METALURGIA:', '', selectedMetaUser.value || '', '', '', '', '', '',
    '', '', '', '', '', ''
  ]);

  // Filas 11 a 13: Espaciadores
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);
  wsData.push(['', '', '', '', '', '', '', '', '', '', '', '', '', '']);

  // Fila 14: Grupo de Cabecera ELEMENTOS POR ANALIZAR (columnas J a N)
  wsData.push([
    '', '', '', '', '', '', '', '', '',
    'ELEMENTOS POR ANALIZAR', '', '', '', ''
  ]);

  // Fila 15: Cabeceras de Columnas del Formato Físico (sin ID DB)
  wsData.push([
    'CÓDIGO',
    'MUESTRA',
    'SN',
    'ID',
    'HORA',
    'TARA',
    'PESO TOTAL',
    'PESO SECO',
    '% SÓLIDOS',
    '%Fe',
    '%Cu',
    '%Zn',
    '%Mo',
    '%Ins'
  ]);

  // Filas 16+: Registros de datos del grid
  gridData.value.forEach(row => {
    // row[0] es ID DB (interno), no se incluye en el reporte oficial
    // row[2] es sampleId, lo convertimos al nombre legible de la muestra
    const sampleId = row[2];
    const sampleName = samplesById.value[sampleId]?.name || (sampleId ? String(sampleId) : '');

    const parseNum = (val) => {
      if (val === '' || val === null || val === undefined) return '';
      const n = parseFloat(String(val).replace(',', '.'));
      return isNaN(n) ? val : n;
    };

    wsData.push([
      row[1] || '',           // Col 1: CÓDIGO
      sampleName,             // Col 2: MUESTRA
      row[3] || '',           // Col 3: SN
      row[4] || '',           // Col 4: ID
      row[5] || '',           // Col 5: HORA
      parseNum(row[6]),       // Col 6: TARA
      parseNum(row[7]),       // Col 7: PESO TOTAL
      parseNum(row[8]),       // Col 8: PESO SECO
      parseNum(row[9]),       // Col 9: % SÓLIDOS
      parseNum(row[10]),      // Col 10: %Fe
      parseNum(row[11]),      // Col 11: %Cu
      parseNum(row[12]),      // Col 12: %Zn
      parseNum(row[13]),      // Col 13: %Mo
      parseNum(row[14])       // Col 14: %Ins
    ]);
  });

  // Generamos la hoja de cálculo con SheetJS
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  // Configuramos los rangos combinados exactamente como en el formato CON-PSG-CPR-FM.005
  ws['!merges'] = [
    // Bloque 1: A1:B4 (Logo corporativo)
    { s: { r: 0, c: 0 }, e: { r: 3, c: 1 } },
    // Bloque 2: C1:K4 (Título y Equipo)
    { s: { r: 0, c: 2 }, e: { r: 3, c: 10 } },
    // Bloque 3: L1:N4 (Código de control documental)
    { s: { r: 0, c: 11 }, e: { r: 3, c: 13 } },
    // Fila 5: UNIDAD MINERA
    { s: { r: 4, c: 0 }, e: { r: 4, c: 1 } },
    { s: { r: 4, c: 2 }, e: { r: 4, c: 13 } },
    // Fila 6: GERENCIA & ÁREA
    { s: { r: 5, c: 0 }, e: { r: 5, c: 1 } },
    { s: { r: 5, c: 2 }, e: { r: 5, c: 7 } },
    { s: { r: 5, c: 8 }, e: { r: 5, c: 10 } },
    { s: { r: 5, c: 11 }, e: { r: 5, c: 13 } },
    // Filas 8-10: Metadatos
    { s: { r: 7, c: 0 }, e: { r: 7, c: 1 } },
    { s: { r: 7, c: 2 }, e: { r: 7, c: 6 } },
    { s: { r: 8, c: 0 }, e: { r: 8, c: 1 } },
    { s: { r: 8, c: 2 }, e: { r: 8, c: 6 } },
    { s: { r: 9, c: 0 }, e: { r: 9, c: 1 } },
    { s: { r: 9, c: 2 }, e: { r: 9, c: 6 } },
    // Logo derecho Control de Procesos (filas 8 a 10, columnas M y N)
    { s: { r: 7, c: 12 }, e: { r: 9, c: 13 } },
    // Fila 14: ELEMENTOS POR ANALIZAR (columnas J a N)
    { s: { r: 13, c: 9 }, e: { r: 13, c: 13 } }
  ];

  // Definimos anchos óptimos de columnas para lectura idéntica al archivo oficial
  ws['!cols'] = [
    { wch: 12 }, // CÓDIGO
    { wch: 32 }, // MUESTRA
    { wch: 12 }, // SN
    { wch: 10 }, // ID
    { wch: 10 }, // HORA
    { wch: 11 }, // TARA
    { wch: 12 }, // PESO TOTAL
    { wch: 12 }, // PESO SECO
    { wch: 12 }, // % SÓLIDOS
    { wch: 10 }, // %Fe
    { wch: 10 }, // %Cu
    { wch: 10 }, // %Zn
    { wch: 10 }, // %Mo
    { wch: 10 }  // %Ins
  ];

  const wb = XLSX.utils.book_new();
  const sheetName = selectedEquipmentLabel.value
    ? selectedEquipmentLabel.value.replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 31)
    : 'C1_COURIER_NORTE';
  XLSX.utils.book_append_sheet(wb, ws, sheetName);

  const cleanDate = selectedDate.value || 'fecha';
  const cleanEq = selectedEquipmentLabel.value ? selectedEquipmentLabel.value.replace(/\s+/g, '_') : 'Courier';
  const fileName = `${cleanDate}_${cleanEq}_Calibracion.xlsx`;

  XLSX.writeFile(wb, fileName);
};

// --- Ciclo de Vida ---
onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* Contenedor principal de la vista */
.assays-view {
  font-family: Arial, Helvetica, sans-serif;
  color: #000;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  background: white;
  padding: 15px 20px;
  box-sizing: border-box;
  overflow-x: auto;
}

/* Barra de herramientas superior para acciones (Excel, Imprimir) */
.report-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 100%;
  margin-bottom: 12px;
  padding: 8px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.report-badge {
  font-weight: 700;
  font-size: 0.85rem;
  color: #1e293b;
  background: #e2e8f0;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.report-version {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-toolbar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 5px;
  font-size: 0.85rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.btn-excel {
  background-color: #1b5e20;
  color: #ffffff;
  border-color: #144917;
  box-shadow: 0 1px 2px rgba(27, 94, 32, 0.2);
}

.btn-excel:hover:not(:disabled) {
  background-color: #2e7d32;
  box-shadow: 0 2px 4px rgba(27, 94, 32, 0.3);
}

.btn-print {
  background-color: #374151;
  color: #ffffff;
  border-color: #1f2937;
  box-shadow: 0 1px 2px rgba(55, 65, 81, 0.2);
}

.btn-print:hover:not(:disabled) {
  background-color: #4b5563;
  box-shadow: 0 2px 4px rgba(55, 65, 81, 0.3);
}

.btn-toolbar:disabled {
  background-color: #e2e8f0;
  color: #94a3b8;
  border-color: #cbd5e1;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-icon {
  font-size: 1rem;
}

/* Envolvedor del reporte para alinear el encabezado y la tabla al mismo ancho */
.report-wrapper {
  width: max-content;
  margin: 0 auto;
}

/* Estilos de la tabla de reporte que replica exactamente el formato físico CON-PSG-CPR-FM.005 */
.report-table {
  width: 100% !important;
  border-collapse: collapse;
  margin-bottom: 12px;
  border: 1px solid #000000;
  box-sizing: border-box;
}

.report-table td {
  border: 1px solid #000000;
  padding: 4px 6px;
  vertical-align: middle;
}

/* Fila 1 a 4: Logos y Título */
.row-header-top {
  height: 80px;
}

.logo-cell {
  width: 180px;
  min-width: 180px;
  text-align: center;
  padding: 6px !important;
}

.corporate-logo {
  max-height: 55px;
  max-width: 165px;
  object-fit: contain;
  display: block;
  margin: 0 auto;
}

.title-cell {
  text-align: center;
  padding: 6px 12px !important;
}

.title-text {
  font-weight: bold;
  font-size: 11pt;
  line-height: 1.3;
  color: #000000;
  letter-spacing: 0.3px;
}

.selected-equipment-title {
  font-weight: bold;
  font-size: 11pt;
  margin-top: 4px;
  color: #000000;
}

.equipment-select-container {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.code-cell {
  width: 190px;
  min-width: 190px;
  padding: 6px 10px !important;
  text-align: left;
  vertical-align: middle;
}

.code-box {
  font-size: 9.5pt;
  line-height: 1.5;
  color: #000000;
}

.code-line {
  white-space: nowrap;
}

.code-label {
  font-weight: bold;
}

/* Fila 5: Unidad Minera */
.row-unidad-minera td {
  padding: 4px 10px !important;
}

.flex-row-header {
  display: flex;
  align-items: center;
  width: 100%;
}

.label-header {
  font-weight: bold;
  font-size: 10pt;
  min-width: 140px;
}

.value-header {
  font-size: 10pt;
  text-align: center;
  flex: 1;
}

/* Fila 6 y Metadatos */
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
  border-bottom: 1px solid #000000;
}

.inner-table tr:last-child {
  border-bottom: none;
}

.inner-table td {
  border: none;
  border-right: 1px solid #000000;
  padding: 4px 8px;
  font-size: 10pt;
}

.inner-table td:last-child {
  border-right: none;
}

.label-cell {
  width: 16%;
  font-weight: bold;
  background-color: #ffffff;
}

.value-cell {
  width: 34%;
  text-align: center;
}

/* Metadatos (Filas 8 a 10) */
.meta-table tr {
  height: 28px;
}

.label-cell-wide {
  width: 25%;
  font-weight: bold;
  background-color: #ffffff;
}

.input-cell {
  width: 45%;
  vertical-align: middle;
}

.right-logo-cell {
  width: 30%;
  text-align: center;
  vertical-align: middle;
  border-left: 1px solid #000000 !important;
  padding: 4px !important;
}

.right-logo-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.department-logo {
  max-height: 60px;
  max-width: 140px;
  object-fit: contain;
  display: block;
}

/* Campos de entrada interactivos en pantalla */
.date-input, .header-select {
  border: none;
  border-bottom: 1px dashed #444;
  background: transparent;
  font-family: inherit;
  font-size: 9.5pt;
  font-weight: bold;
  outline: none;
  cursor: pointer;
  color: #000000;
  text-align: left;
  padding: 2px 4px;
}

.red-text-style {
  color: #c62828 !important;
  font-weight: bold;
}

.value-text {
  font-size: 10pt;
  font-weight: bold;
}

/* Control de visibilidad para pantalla vs impresión */
.screen-only {
  display: inline-block;
}

.print-only {
  display: none;
}

/* Botón de sincronización con API del Courier */
.sync-courier-btn {
  padding: 4px 10px;
  background-color: #1976d2;
  color: #fff;
  border: 1px solid #1565c0;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.sync-courier-btn:hover:not(:disabled) {
  background-color: #1565c0;
}

.sync-courier-btn:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;
  border-color: #bdbdbd;
  cursor: not-allowed;
  box-shadow: none;
}

/* Contenedor de la tabla de datos */
.table-container {
  overflow-x: auto;
  margin-top: 15px;
  width: max-content;
}

/* Forzar que el table-wrapper de ExcelGrid muestre todas las columnas sin scroll interno */
.table-container :deep(.table-wrapper) {
  overflow: visible !important;
}

.table-container :deep(.excel-container) {
  width: max-content !important;
}

/* --- OVERRIDES DEL DISEÑO DE EXCELGRID MEDIANTE DEEP SELECTORS (SIN MODIFICAR CELDAS NI LÓGICA) --- */

/* Ocultar la primera columna (ID DB de la base de datos) */
.table-container :deep(.hidden-column) {
  display: none !important;
}
.table-container :deep(.excel-table td[data-col-index="0"]) {
  display: none !important;
}

/* Estilo para las cabeceras individuales (Fondo verde pastel y bordes negros según Excel) */
.table-container :deep(.excel-table th) {
  background-color: #e2f0d9 !important;
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
  height: 28px !important;
  padding: 3px 6px !important;
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
  font-weight: 500;
}
.state-message.error {
  color: #dc2626;
}

/* --- REGLAS DE IMPRESIÓN OFICIAL (@media print) --- */
@media print {
  @page {
    size: landscape;
    margin: 6mm 8mm;
  }

  /* Ocultar elementos de interfaz, navegación y botones de control */
  .no-print,
  .report-toolbar,
  .sync-courier-btn,
  .screen-only,
  .state-message,
  :deep(.excel-actions),
  :deep(.excel-pagination),
  :deep(.btn-edit),
  :deep(.btn-save),
  :deep(.btn-delete),
  :deep(.btn-add),
  nav,
  header,
  aside,
  .sidebar,
  .layout-header,
  .layout-sidebar {
    display: none !important;
  }

  /* Mostrar datos limpios de impresión */
  .print-only {
    display: inline-block !important;
  }

  body, html {
    background: #ffffff !important;
    color: #000000 !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  .assays-view {
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    width: 100% !important;
    overflow: visible !important;
  }

  .report-wrapper {
    width: 100% !important;
    margin: 0 !important;
  }

  .report-table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin-bottom: 6px !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .report-table td {
    border: 1px solid #000000 !important;
    padding: 3px 5px !important;
  }

  .table-container {
    margin-top: 5px !important;
    width: 100% !important;
    overflow: visible !important;
  }

  .table-container :deep(.table-wrapper) {
    overflow: visible !important;
  }

  .table-container :deep(.excel-container) {
    width: 100% !important;
    box-shadow: none !important;
    border: none !important;
    background: transparent !important;
  }

  .table-container :deep(.excel-table) {
    width: 100% !important;
    font-size: 7.5pt !important;
    border-collapse: collapse !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.excel-table th) {
    background-color: #e2f0d9 !important;
    border: 1px solid #000000 !important;
    color: #000000 !important;
    padding: 2px 4px !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.excel-table th.group-header-cell) {
    background-color: #d9d9d9 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.excel-table td) {
    font-size: 7.5pt !important;
    height: 20px !important;
    padding: 2px 4px !important;
    border: 1px solid #000000 !important;
  }
}
</style>
