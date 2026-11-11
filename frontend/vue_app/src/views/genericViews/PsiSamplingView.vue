<!--
  PsiSamplingView.vue
  MUESTREO DE CALIBRACIÓN DEL PSI DE MOLIENDA C1 — formato CON-PSG-CPR-FM.003, versión 02.

  El estilo y el armado de la cabecera son los MISMOS que SamplingView.vue (el formato de los
  Courier, CON-PSG-CPR-FM.005): las mismas clases, la misma tabla de cabecera y los mismos
  overrides de ExcelGrid. Lo único propio del PSI son los textos del formato y las columnas.

  Cada PSI tiene su propio formato, así que esta vista es SOLO la de Molienda C1 y no tiene selector
  de equipo. Los otros PSI (Remolienda C1, Molienda C2, Remolienda C2) necesitan su propia vista a
  partir de su propio Excel.

  Las columnas salen de la hoja `C1_PSI_MOLIENDA` del libro "10.10.2026_PSI Molienda C1 TA.xlsx":
  28 columnas (A..AB) en tres bloques — lo que se pesa en el laboratorio, lo que marcaba el PSI al
  tomar la muestra, y los porcentajes que devuelve el laboratorio.

  La vista NO se conecta al analizador: los datos del PSI se transcriben a mano desde su pantalla.
  Persiste contra /api/assayspsi/ (modelo AssaysPsi).
-->
<template>
  <section class="assays-view">
    <!-- Barra de herramientas superior (oculta en impresión) -->
    <div class="report-toolbar no-print">
      <div class="toolbar-left">
        <span class="report-badge">📋 FORMATO {{ CODIGO }}</span>
        <span class="report-version">Versión {{ VERSION }}</span>
      </div>
      <div class="toolbar-actions">
        <button
          type="button"
          class="btn-toolbar btn-print"
          :disabled="loading"
          @click="printReport"
          title="Imprimir formato oficial (sin controles de edición)"
        >
          <span class="btn-icon">🖨️</span> Imprimir
        </button>
      </div>
    </div>

    <div class="report-wrapper">
      <!-- Cabecera oficial del formato, con la misma estructura que la de los Courier -->
      <table class="report-table">
        <tbody>
          <!-- Logo corporativo, título con el equipo, y caja de código -->
          <tr class="row-header-top">
            <td class="logo-cell">
              <div class="logo-container">
                <img :src="logoSouthern" alt="Grupo México Southern Perú" class="corporate-logo" />
              </div>
            </td>
            <td class="title-cell">
              <div class="title-text">{{ TITULO }}</div>
              <!-- Fijo: este formato es de un solo PSI, no hay equipo que elegir -->
              <div class="selected-equipment-title">{{ SUBTITULO }}</div>
            </td>
            <td class="code-cell">
              <div class="code-box">
                <div class="code-line"><span class="code-label">Código:</span> {{ CODIGO }}</div>
                <div class="code-line"><span class="code-label">Versión:</span> {{ VERSION }}</div>
                <div class="code-line"><span class="code-label">Página:</span> 1 de 1</div>
              </div>
            </td>
          </tr>

          <!-- Unidad minera -->
          <tr class="row-unidad-minera">
            <td colspan="3" class="full-width-cell">
              <div class="flex-row-header">
                <span class="label-header">UNIDAD MINERA:</span>
                <span class="value-header">Toquepala</span>
              </div>
            </td>
          </tr>

          <!-- Gerencia y departamento / área -->
          <tr class="row-gerencia-area">
            <td colspan="3" class="no-padding-cell">
              <table class="inner-table">
                <tbody>
                  <tr>
                    <td class="label-cell">GERENCIA:</td>
                    <td class="value-cell">Concentradora</td>
                    <td class="label-cell">DEPARTAMENTO / ÁREA:</td>
                    <td class="value-cell">Control de Procesos</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>

          <!-- Datos variables del reporte y logo de Control de Procesos -->
          <tr class="row-meta-section">
            <td colspan="3" class="no-padding-cell">
              <table class="inner-table meta-table">
                <tbody>
                  <tr>
                    <td class="label-cell-wide">FECHA DE MUESTREO:</td>
                    <td class="input-cell">
                      <input type="date" v-model="selectedDate" class="date-input screen-only" />
                      <span class="print-only value-text">{{ formatDateDisplay(selectedDate) }}</span>
                    </td>
                    <td rowspan="3" class="right-logo-cell">
                      <div class="logo-container right-logo-container">
                        <img :src="logoControl" alt="Control de Procesos" class="department-logo" />
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td class="label-cell-wide">ENVIADO POR:</td>
                    <td class="input-cell">
                      <select v-model="selectedUser" class="header-select red-text-style screen-only">
                        <option value="">-- Seleccionar --</option>
                        <option v-for="u in userOptions" :key="u.id" :value="u.id">
                          {{ u.nombre }} {{ u.apellido }}
                        </option>
                      </select>
                      <span class="print-only value-text red-text-style">{{ selectedUserName || '-' }}</span>
                    </td>
                  </tr>
                  <tr>
                    <td class="label-cell-wide">OPERADOR DE METALURGIA:</td>
                    <td class="input-cell">
                      <select v-model="selectedMetaUser" class="header-select screen-only">
                        <option value="">-- Seleccionar --</option>
                        <option v-for="mu in metaUserOptions" :key="mu" :value="mu">{{ mu }}</option>
                      </select>
                      <span class="print-only value-text">{{ selectedMetaUser || '-' }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Mensajes de carga y errores del servidor -->
      <div v-if="loading" class="state-message no-print">Cargando datos...</div>
      <div v-else-if="error" class="state-message error no-print">{{ error }}</div>

      <!-- El equipo se resuelve por nombre y descripción; si no existe, nada puede funcionar -->
      <div v-if="!loading && !selectedEquipment" class="state-message error no-print">
        No se encontró el equipo «{{ EQUIPO.name }} — {{ EQUIPO.description }}» en la base de datos.
        Este formato es solo de ese PSI, así que hasta que exista el equipo no se pueden registrar
        muestreos.
      </div>

      <!-- La columna SECCIÓN es un desplegable de las muestras de este equipo -->
      <div v-else-if="!loading && sampleOptions.length === 0" class="state-message warning no-print">
        Este PSI no tiene muestras registradas, así que la columna SECCIÓN queda vacía y no se puede
        guardar. Hay que crearlas primero en «Metalurgia y Calidad → Muestras Físicas»: una por cada
        sección de molienda que se muestrea (en este formato son las secciones 3, 4 y 5).
      </div>

      <!-- Contenedor del grid reutilizable -->
      <div class="table-container">
        <ExcelGrid
          title="Detalle de Muestreo Granulométrico"
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
import { ref, computed, onMounted, watch } from 'vue';
// Logos corporativos del formato oficial (los mismos del formato de Courier)
import logoSouthern from '../../assets/courier_image3.png';
import logoControl from '../../assets/courier_image2.png';
import { api } from '../../api';
import { useApi } from '../../composables/useApi';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { buildPayloadFromRow } from '../../utils/gridHelpers';
import { assayWeightFormulas } from '../../utils/gridFormulas';

// --- Identidad del formato (literal del Excel de Molienda C1) ---
const CODIGO = 'CON-PSG-CPR-FM.003';
const VERSION = '02';
const TITULO = 'FORMATO DE MUESTREO DE CALIBRACIÓN DE PSI';
const SUBTITULO = 'PSI MOLIENDA NORTE 300i C1';

// El equipo de works4cdp_equipment al que pertenece este formato. Se busca por nombre y descripción
// en vez de por id fijo: hoy es el id 3, pero el id no es parte del formato.
const EQUIPO = { name: 'PSI', description: 'Molienda C1' };

// --- Estado ---
const selectedDate = ref(new Date().toISOString().split('T')[0]);
const selectedEquipment = ref('');
const selectedUser = ref('');
const selectedMetaUser = ref('');

const ensayos = ref([]);
const samplesById = ref({});
const userOptions = ref([]);
const metaUserOptions = ref([]);

const { loading, error, execute } = useApi();

// --- Configuración de columnas para ExcelGrid ---
// Textos de la fila 14 del Excel (los saltos de línea del original van como espacio).
const headers = [
  'ID DB',                     // 0  oculta: clave primaria, no existe en el Excel
  'MUESTRA',                   // 1  columna A: la ronda A/B/C
  'SECCIÓN',                   // 2  B: sección de molienda
  'HORA',                      // 3  C
  'TARA',                      // 4  D
  'PESO TOTAL',                // 5  E
  'PESO SECO',                 // 6  F
  '% SÓLIDOS',                 // 7  G — calculada, editable
  // El "PESO PARCIAL ... (gr)" del Excel pasa al grupo de cabecera: repetirlo en las cinco columnas
  // las hacía anchísimas (ExcelGrid dimensiona cada columna por el largo de su encabezado).
  'M+48',                      // 8  H
  'M+65',                      // 9  I
  'M+100',                     // 10 J
  'M+150',                     // 11 K
  'M+200',                     // 12 L
  'ID',                        // 13 M — DATOS PSI AL TOMAR MUESTRA
  'AVE',                       // 14 N
  'SD',                        // 15 O
  'Density',                   // 16 P
  '%SOL',                      // 17 Q
  '%M+48',                     // 18 R
  '%M+65',                     // 19 S
  '%M+100',                    // 20 T
  '%M+150',                    // 21 U
  '%M+200',                    // 22 V
  'P80',                       // 23 W
  '%M+48 LAB.',                // 24 X — LABORATORIO
  '%M+65 LAB.',                // 25 Y
  '%M+100 LAB.',               // 26 Z
  '%M+150 LAB.',               // 27 AA
  '%M+200 LAB.'                // 28 AB
];

// Campo del modelo AssaysPsi que corresponde a cada columna.
const colKeys = [
  'id',
  'turn',        // MUESTRA: la ronda A/B/C
  'sample',      // SECCIÓN
  'time',
  'tara',
  'tweight',
  'dweight',
  'psolid',
  'pW48', 'pW65', 'pW100', 'pW150', 'pW200',
  'instance',    // ID propio del analizador
  'aAvg', 'aSD', 'aDensity', 'aSol',
  'aP48', 'aP65', 'aP100', 'aP150', 'aP200',
  'P80',
  'pP48', 'pP65', 'pP100', 'pP150', 'pP200'
];

// Grupos de cabecera: los dos bloques de la fila 13 del formato físico, más 'PESO PARCIAL (gr)',
// que en el Excel está repetido en el texto de cada una de esas cinco columnas. Igual que en el
// formato de Courier, los colspan suman una columna menos que las cabeceras porque 'ID DB' va
// oculta por CSS.
const headerGroups = [
  { label: '', colspan: 7 },
  { label: 'PESO PARCIAL (gr)', colspan: 5 },
  { label: 'DATOS PSI AL TOMAR MUESTRA', colspan: 11 },
  { label: 'LABORATORIO', colspan: 5 }
];

// Letras de la columna MUESTRA: desplegable en vez de texto libre para que no entren variantes.
const LETRAS_MUESTRA = ['A', 'B', 'C'];

// --- Propiedades computadas ---

// Muestras de este PSI: son las secciones de molienda que se muestrean.
const sampleOptions = computed(() => {
  return Object.values(samplesById.value)
    .filter((s) => {
      if (!selectedEquipment.value) return false;
      const eqId = typeof s.equipment === 'object' ? s.equipment.id : s.equipment;
      return eqId == selectedEquipment.value;
    })
    .sort((a, b) => String(a.tag || '').localeCompare(String(b.tag || ''), undefined, { numeric: true }))
    .map((s) => ({ value: s.id, label: s.name || s.tag }));
});

const columnsConfig = computed(() => ({
  // La columna 0 ('ID DB') se oculta con la clase CSS 'hidden-column'
  0: { headerClass: 'hidden-column' },
  // MUESTRA: la ronda A/B/C
  1: { type: 'select', options: LETRAS_MUESTRA.map((l) => ({ value: l, label: l })) },
  // SECCIÓN: las muestras de este equipo
  2: { type: 'select', options: sampleOptions.value },
  // % SÓLIDOS = Peso Seco / (Peso Total − Tara) × 100. Es la misma fórmula del formato de Courier,
  // así que se reutiliza assayWeightFormulas: se le traduce 'pSol' al campo 'psolid' de AssaysPsi y
  // 'pweight' no existe en este formato (indexOf devuelve -1 y esa fórmula se omite sola).
  ...assayWeightFormulas((key) => colKeys.indexOf(key === 'pSol' ? 'psolid' : key))
}));

const filteredEnsayos = computed(() => {
  return ensayos.value.filter((e) => {
    if (selectedDate.value && e.date !== selectedDate.value) return false;
    if (selectedEquipment.value) {
      const sampleId = e.sample && typeof e.sample === 'object' ? e.sample.id : e.sample;
      const s = samplesById.value[sampleId];
      const eqId = s && s.equipment ? (typeof s.equipment === 'object' ? s.equipment.id : s.equipment) : null;
      if (eqId != selectedEquipment.value) return false;
    }
    return true;
  });
});

// Matriz plana para ExcelGrid, en el orden del formato impreso: por sección y después por ronda.
const gridData = computed(() => {
  const ordenadas = [...filteredEnsayos.value].sort((a, b) => {
    const idA = a.sample && typeof a.sample === 'object' ? a.sample.id : a.sample;
    const idB = b.sample && typeof b.sample === 'object' ? b.sample.id : b.sample;
    const tagA = String(samplesById.value[idA]?.tag || '');
    const tagB = String(samplesById.value[idB]?.tag || '');
    const porSeccion = tagA.localeCompare(tagB, undefined, { numeric: true, sensitivity: 'base' });
    if (porSeccion !== 0) return porSeccion;
    return String(a.turn || '').localeCompare(String(b.turn || ''));
  });

  return ordenadas.map((e) => {
    const sampleId = e.sample && typeof e.sample === 'object' ? e.sample.id : e.sample;
    return colKeys.map((key) => {
      if (key === 'id') return e.id || '';
      if (key === 'sample') return sampleId || '';
      if (key === 'time') return formatTime(e.time);
      return formatNumber(e[key]);
    });
  });
});

const selectedUserName = computed(() => {
  const u = userOptions.value.find((usr) => usr.id == selectedUser.value);
  return u ? `${u.nombre} ${u.apellido}` : '';
});

// --- Métodos de API ---

// Arma la lista de operadores de metalurgia y prellena la cabecera con lo ya registrado.
const updateHeaderFieldsFromEnsayos = () => {
  const metas = new Set();
  ensayos.value.forEach((e) => {
    if (e.meta_user) metas.add(e.meta_user);
  });
  userOptions.value.forEach((u) => metas.add(`${u.nombre} ${u.apellido}`));
  metaUserOptions.value = Array.from(metas).sort();

  if (ensayos.value.length > 0) {
    const conUsuario = ensayos.value.find((e) => e.user);
    selectedUser.value = conUsuario
      ? (typeof conUsuario.user === 'object' ? conUsuario.user.id : conUsuario.user)
      : '';
    const conMeta = ensayos.value.find((e) => e.meta_user);
    selectedMetaUser.value = conMeta ? conMeta.meta_user : '';
  } else {
    selectedUser.value = '';
    selectedMetaUser.value = '';
  }
};

const loadEnsayos = async () => {
  if (!selectedEquipment.value) {
    ensayos.value = [];
    return;
  }

  await execute(async () => {
    const params = { page_size: 10000, sample__equipment: selectedEquipment.value };
    if (selectedDate.value) params.date = selectedDate.value;

    const res = await api.get('assayspsi/', { params });
    ensayos.value = res.data.results || res.data || [];
    updateHeaderFieldsFromEnsayos();
  }, 'Error al cargar los ensayos granulométricos desde la base de datos.');
};

const loadData = async () => {
  await execute(async () => {
    const [samplesRes, usersRes, equipRes] = await Promise.all([
      api.get('samples/', { params: { page_size: 10000 } }),
      api.get('users/', { params: { page_size: 10000 } }).catch(() => ({ data: [] })),
      api.get('equipments/', { params: { page_size: 10000 } }).catch(() => ({ data: [] }))
    ]);

    const samples = samplesRes.data.results || samplesRes.data || [];
    samplesById.value = samples.reduce((acc, s) => {
      acc[s.id] = s;
      return acc;
    }, {});

    userOptions.value = usersRes.data.results || usersRes.data || [];

    // Este formato es de un solo PSI: se busca ese equipo y no se ofrece elegir otro.
    const equips = equipRes.data.results || equipRes.data || [];
    const equipo = equips.find(
      (e) =>
        String(e.name || '').trim().toUpperCase() === EQUIPO.name.toUpperCase() &&
        String(e.description || '').trim().toUpperCase() === EQUIPO.description.toUpperCase()
    );
    selectedEquipment.value = equipo ? equipo.id : '';

    await loadEnsayos();
  }, 'Error al cargar los datos del servidor.');
};

// --- Manejadores de eventos de ExcelGrid ---

const handleSave = async (updatedGrid) => {
  // La SECCIÓN es obligatoria: sin ella la fila no pertenece a ningún equipo y desaparecería del
  // formato al recargar, porque el filtro por equipo se hace a través de la muestra.
  const sampleColIndex = colKeys.indexOf('sample');
  const sinSeccion = [];
  updatedGrid.forEach((row, i) => {
    if (row.isSummary) return;
    const valor = row[sampleColIndex];
    if (valor === '' || valor === null || valor === undefined) sinSeccion.push(i + 1);
  });

  if (sinSeccion.length > 0) {
    alert(
      `⚠️ No se pueden guardar los cambios.\n\n` +
      `Falta la SECCIÓN en las filas: ${sinSeccion.join(', ')}.\n\n` +
      `Sin sección la fila no queda asociada al PSI y no volvería a aparecer en este formato.`
    );
    return;
  }

  try {
    await execute(async () => {
      const promises = updatedGrid.map((row) => {
        const payload = buildPayloadFromRow(row, colKeys);
        payload.date = selectedDate.value;
        payload.user_id = selectedUser.value ? selectedUser.value : null;
        payload.meta_user = selectedMetaUser.value ? selectedMetaUser.value : null;

        const id = payload.id;
        if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
          return api.put(`assayspsi/${id}/`, payload);
        }
        delete payload.id;
        return api.post('assayspsi/', payload);
      });

      await Promise.all(promises);
      alert('Cambios guardados correctamente.');
      await loadEnsayos();
    });
  } catch (err) {
    let backendMsg = '';
    if (err.response?.data) {
      if (typeof err.response.data === 'string') {
        backendMsg = err.response.data;
      } else if (err.response.data.detail) {
        backendMsg = err.response.data.detail;
      } else {
        backendMsg = Object.entries(err.response.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('\n');
      }
    }
    alert(`⚠️ Error al guardar los cambios:\n\n${backendMsg || err.message || 'Error en el servidor.'}`);
  }
};

const handleDelete = async (idsToDelete) => {
  if (!idsToDelete || idsToDelete.length === 0) return;
  try {
    await execute(async () => {
      await Promise.all(idsToDelete.map((id) => api.delete(`assayspsi/${id}/`)));
      alert(`${idsToDelete.length} ensayo(s) eliminado(s) correctamente.`);
      await loadEnsayos();
    });
  } catch (err) {
    alert('Ocurrió un error al eliminar los registros.');
  }
};

// --- Vigilantes ---
watch(selectedDate, async () => {
  await loadEnsayos();
});

onMounted(loadData);

// --- Helpers auxiliares ---

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

// Formatea la fecha ISO (YYYY-MM-DD) a DD/MM/YYYY para impresión
const formatDateDisplay = (dateStr) => {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : dateStr;
};

// Imprime el formato oficial ocultando controles y botones
const printReport = () => {
  window.print();
};
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

/* Barra de herramientas superior */
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

/*
  Envolvedor del reporte para alinear el encabezado y la tabla al mismo ancho.
  A diferencia del formato de Courier (15 columnas, que caben a su ancho natural), acá son 28 y hay
  que ajustarlas al ancho disponible; de ahí el 100% en lugar de max-content.
*/
.report-wrapper {
  width: 100%;
  margin: 0 auto;
}

/* Tabla de reporte que replica el formato físico */
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

/* Logos y título */
.row-header-top {
  height: 80px;
}

.logo-cell {
  width: 180px;
  min-width: 180px;
  text-align: center;
  padding: 6px !important;
}

.logo-container {
  display: flex;
  justify-content: center;
  align-items: center;
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

/* Unidad minera */
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

/* Gerencia y metadatos */
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

/* Contenedor de la tabla de datos */
.table-container {
  overflow-x: auto;
  margin-top: 15px;
  width: 100%;
}

/* Forzar que el table-wrapper de ExcelGrid muestre todas las columnas sin scroll interno */
.table-container :deep(.table-wrapper) {
  overflow: visible !important;
}

/*
  --- LAS 28 COLUMNAS ENTRAN A LO ANCHO, SIN SCROLL HORIZONTAL ---
  ExcelGrid calcula el ancho de cada columna con calculateAutoWidths() y lo escribe como estilo en
  línea, con un piso de MIN_COL_WIDTH = 80px. Con 28 columnas eso son 2240px como mínimo y la tabla
  siempre queda más ancha que la pantalla.
  Acá se anula ese piso (el !important del CSS gana al estilo en línea, que no lo lleva) y se deja
  que el navegador reparta el ancho por contenido con table-layout: auto. Solo afecta a esta vista:
  el formato de Courier conserva sus anchos calculados.
*/
.table-container :deep(.excel-container) {
  width: 100% !important;
}

.table-container :deep(.excel-table) {
  width: 100% !important;
  table-layout: auto !important;
}

.table-container :deep(.excel-table th),
.table-container :deep(.excel-table td) {
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
}

/* La columna oculta no debe reservar ancho */
.table-container :deep(.excel-table th.hidden-column),
.table-container :deep(.excel-table td[data-col-index="0"]) {
  width: 0 !important;
}

/*
  El encabezado se parte en dos líneas en vez de ensanchar la columna. ExcelGrid pone nowrap en
  th/td y overflow:hidden con text-overflow:ellipsis en .header-text, que recortaría la segunda
  línea; hay que levantar las tres cosas.
*/
.table-container :deep(.excel-table th) {
  white-space: normal !important;
  height: auto !important;
  vertical-align: middle !important;
}

.table-container :deep(.header-text) {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  line-height: 1.15;
  text-align: center;
}

.table-container :deep(.header-content) {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  gap: 2px;
}

/* El embudo de filtro, más chico: con 28 columnas su ancho se multiplica */
.table-container :deep(.filter-icon) {
  font-size: 0.6rem !important;
  flex: 0 0 auto;
}

/* --- OVERRIDES DEL DISEÑO DE EXCELGRID MEDIANTE DEEP SELECTORS --- */

/* Ocultar la primera columna (ID DB de la base de datos) */
.table-container :deep(.hidden-column) {
  display: none !important;
}
.table-container :deep(.excel-table td[data-col-index="0"]) {
  display: none !important;
}

/* Cabeceras individuales: fondo verde pastel y bordes negros, como en el formato.
   Un punto menos de letra que en el formato de Courier, porque son 28 columnas y no 15. */
.table-container :deep(.excel-table th) {
  background-color: #e2f0d9 !important;
  color: #000000 !important;
  font-weight: bold !important;
  border: 1px solid #000000 !important;
  text-align: center !important;
  font-size: 0.68rem !important;
  padding: 2px 2px !important;
}

/* Grupos de cabecera ('PESO PARCIAL (gr)', 'DATOS PSI...' y 'LABORATORIO') en gris */
.table-container :deep(.excel-table th.group-header-cell) {
  background-color: #d9d9d9 !important;
  font-size: 0.7rem !important;
}

/* El primer grupo es vacío y solo alinea las columnas de la izquierda */
.table-container :deep(.excel-table th.group-header-cell:first-of-type) {
  background-color: transparent !important;
  border: none !important;
  border-bottom: 1px solid #000000 !important;
}

/* Celdas del grid con bordes negros sólidos */
.table-container :deep(.excel-table td) {
  border: 1px solid #000000 !important;
  font-size: 0.75rem !important;
  height: 28px !important;
  padding: 2px 3px !important;
  text-align: center !important;
}

/* Los desplegables de MUESTRA y SECCIÓN no deben imponer ancho a su columna */
.table-container :deep(.cell-select) {
  width: 100% !important;
  min-width: 0 !important;
  font-size: 0.72rem !important;
}

/* Azul para MUESTRA, SECCIÓN y HORA, igual que CÓDIGO / ID / HORA en el formato de Courier */
.table-container :deep(.excel-table td[data-col-index="1"]),
.table-container :deep(.excel-table td[data-col-index="2"]),
.table-container :deep(.excel-table td[data-col-index="3"]) {
  color: #0056b3 !important;
  font-weight: bold;
}

/* Mensajes de estado (cargando / error / aviso) */
.state-message {
  text-align: center;
  padding: 10px;
  font-weight: 500;
}

.state-message.error {
  color: #dc2626;
}

.state-message.warning {
  color: #92400e;
}

/* --- REGLAS DE IMPRESIÓN OFICIAL (@media print) --- */
@media print {
  @page {
    size: landscape;
    margin: 6mm 8mm;
  }

  .no-print,
  .report-toolbar,
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
    margin-bottom: 4px !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .report-table td {
    border: 1px solid #000000 !important;
    padding: 2px 4px !important;
  }

  .corporate-logo {
    max-height: 40px !important;
    max-width: 130px !important;
  }

  .title-text {
    font-size: 9.5pt !important;
    line-height: 1.2 !important;
  }

  .selected-equipment-title {
    font-size: 9pt !important;
    margin-top: 2px !important;
  }

  .code-cell {
    width: 150px !important;
    min-width: 150px !important;
    padding: 3px 6px !important;
  }

  .code-box {
    font-size: 8pt !important;
    line-height: 1.3 !important;
  }

  .label-header,
  .value-header,
  .label-cell,
  .value-cell {
    font-size: 8pt !important;
  }

  .table-container {
    margin-top: 4px !important;
    width: 100% !important;
    overflow: visible !important;
  }

  .table-container :deep(.table-wrapper) {
    overflow: visible !important;
    border: none !important;
  }

  .table-container :deep(.excel-container) {
    width: 100% !important;
    box-shadow: none !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
    height: auto !important;
  }

  .table-container :deep(.excel-table) {
    width: 100% !important;
    font-size: 7pt !important;
    border-collapse: collapse !important;
    table-layout: auto !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.filter-icon),
  .table-container :deep(.filter-menu),
  .table-container :deep(.resizer) {
    display: none !important;
  }

  .table-container :deep(.header-content) {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
  }

  .table-container :deep(.header-text) {
    font-size: 6pt !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-align: center !important;
  }

  .table-container :deep(.excel-table th) {
    background-color: #e2f0d9 !important;
    border: 1px solid #000000 !important;
    color: #000000 !important;
    padding: 1px 1px !important;
    font-size: 6pt !important;
    font-weight: bold !important;
    line-height: 1.1 !important;
    min-width: unset !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.excel-table th.group-header-cell) {
    background-color: #d9d9d9 !important;
    font-size: 6.2pt !important;
    padding: 1px 1px !important;
    min-width: unset !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .table-container :deep(.excel-table td) {
    font-size: 7pt !important;
    height: 18px !important;
    padding: 1px 2px !important;
    border: 1px solid #000000 !important;
    min-width: unset !important;
    white-space: nowrap !important;
  }
}
</style>

<!-- Estilos globales no-scoped para ocultar el Header y el Sidebar en impresión -->
<style>
@media print {
  header,
  .header,
  aside,
  .sidebar,
  .brand-title,
  .search-box,
  .sidebar-menu,
  .sidebar-footer {
    display: none !important;
  }

  .container {
    margin-top: 0 !important;
    display: block !important;
  }

  .content {
    margin-left: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    min-height: auto !important;
    background-color: #ffffff !important;
  }

  /* Ocultar la barra superior de ExcelGrid (título, estado, botones, filtros, paginación) */
  .excel-container > .toolbar,
  .excel-container .actions,
  .excel-container .title-section,
  .excel-container .status-badge,
  .excel-container .filter-icon,
  .excel-container .filter-menu,
  .excel-container .pagination-controls,
  .filter-icon {
    display: none !important;
  }

  .report-toolbar,
  .no-print {
    display: none !important;
  }
}
</style>
