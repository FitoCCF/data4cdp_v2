<!--
  SamplingView.vue
  // Vista principal para visualizar y generar el reporte de Muestreo de Calibración de Courier.
  // Esta vista está diseñada para replicar el formato físico oficial utilizado en la mina.
  Vista para visualizar el reporte de Muestreo.
  Replica formato "FORMATO DE MUESTREO DE CALIBRACIÓN DE COURIER".
-->
<template>
  <!-- Sección principal que contiene toda la vista de ensayos/muestreo -->
  <section class="assays-view">

    <!-- Tabla que estructura el encabezado del reporte, imitando el formato físico -->
    <table class="report-table">
      <!-- Fila 1: Contiene los Logos, el Título del reporte y el Código del documento -->
      <tr>
        <!-- Celda izquierda: Logo de la empresa -->
        <td class="logo-cell">
          <div class="logo-container">
            <!-- Contenedor placeholder para simular el logo si no hay imagen -->
            <div class="logo-placeholder">
                <!-- Nombre principal de la empresa -->
                <span class="logo-main">GrupoMéxico</span><br>
                <!-- División de la empresa -->
                <span class="logo-sub">MINERÍA</span><br>
                <!-- Ubicación específica -->
                <span class="logo-bottom">SouthernPerú</span>
            </div>
          </div>
        </td>
        <!-- Celda central: Título del reporte y selección de equipo -->
        <td class="title-cell">
          <!-- Texto del título principal del reporte -->
          <div class="title-text">FORMATO DE MUESTREO DE CALIBRACIÓN DE COURIER</div>
          <!-- Contenedor para el selector de equipo -->
          <div class="equipment-select-container">
             <!-- Selector dropdown para filtrar los datos por equipo específico -->
            <select v-model="selectedEquipment" class="header-select red-box-style">
                <!-- Opción por defecto cuando no se ha seleccionado nada -->
                <option value="">-- Seleccionar Equipo --</option>
                <!-- Itera sobre las opciones de equipos disponibles -->
                <option v-for="eq in equipmentOptions" :key="eq.id" :value="eq.id">
                    <!-- Muestra el nombre/etiqueta del equipo -->
                    {{ eq.label }}
                </option>
            </select>
          </div>
        </td>
        <!-- Celda derecha: Información de control del documento (Código, Versión, Página) -->
        <td class="code-cell">
          <!-- Código del documento -->
          <div>Código: CON-PSG-CPR-FM.005</div>
          <!-- Versión del documento -->
          <div>Versión: 02</div>
          <!-- Número de página -->
          <div>Página: 1 de 1</div>
        </td>
      </tr>

      <!-- Fila 2: Información de la Unidad Minera -->
      <tr>
        <!-- Celda que ocupa todo el ancho de la tabla (3 columnas) -->
        <td colspan="3" class="full-width-cell">
            <!-- Contenedor flexible para alinear etiqueta y valor a los extremos -->
            <div class="flex-row-space">
                <!-- Etiqueta del campo -->
                <span class="label">UNIDAD MINERA:</span>
                <!-- Valor fijo de la unidad minera -->
                <span class="value">Toquepala</span>
            </div>
        </td>
      </tr>

      <!-- Fila 3: Información de Gerencia y Departamento -->
      <tr>
        <!-- Celda que ocupa todo el ancho, sin padding interno para anidar otra tabla -->
        <td colspan="3" class="no-padding-cell">
            <!-- Tabla interna para estructurar los campos en una sola línea -->
            <table class="inner-table">
                <tr>
                    <!-- Etiqueta para Gerencia -->
                    <td class="label-cell">GERENCIA:</td>
                    <!-- Valor fijo para Gerencia -->
                    <td class="value-cell">Concentradora</td>
                    <!-- Etiqueta para Departamento/Área -->
                    <td class="label-cell">DEPARTAMENTO / ÁREA:</td>
                    <!-- Valor fijo para Departamento/Área -->
                    <td class="value-cell">Control de Procesos</td>
                </tr>
            </table>
        </td>
      </tr>

      <!-- Fila 4: Datos Variables (Fecha, Usuario, Operador) y Logo Derecho -->
      <tr>
        <!-- Celda contenedora principal -->
        <td colspan="3" class="no-padding-cell">
            <!-- Tabla interna para organizar los campos de entrada y el logo derecho -->
            <table class="inner-table">
                <!-- Sub-Fila 1: Fecha de Muestreo -->
                <tr>
                    <!-- Etiqueta para la fecha -->
                    <td class="label-cell-wide">FECHA DE MUESTREO:</td>
                    <!-- Celda con el input de fecha -->
                    <td class="input-cell">
                        <!-- Input tipo fecha vinculado a la variable selectedDate -->
                        <input type="date" v-model="selectedDate" class="date-input red-box-style full-width" />
                    </td>
                    <!-- Celda derecha que ocupa 3 filas verticalmente para el logo secundario -->
                    <td rowspan="3" class="right-logo-cell">
                         <div class="logo-container">
                             <!-- Placeholder SVG para el logo derecho -->
                             <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#1976d2" stroke-width="2">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="16" x2="12" y2="12"></line>
                                <line x1="12" y1="8" x2="12.01" y2="8"></line>
                             </svg>
                             <!-- Texto debajo del logo derecho -->
                             <div class="logo-text-right">Control de Procesos<br>2025</div>
                         </div>
                    </td>
                </tr>
                <!-- Sub-Fila 2: Enviado Por (Usuario) -->
                <tr>
                    <!-- Etiqueta para el usuario que envía -->
                    <td class="label-cell-wide">ENVIADO POR:</td>
                    <!-- Celda con el selector de usuario -->
                    <td class="input-cell">
                        <!-- Selector de usuario vinculado a selectedUser -->
                        <select v-model="selectedUser" class="header-select red-box-style full-width">
                            <option value="">-- Seleccionar --</option>
                            <!-- Itera sobre los usuarios disponibles -->
                            <option v-for="u in userOptions" :key="u.id" :value="u.id">
                                {{ u.nombre }} {{ u.apellido }}
                            </option>
                        </select>
                    </td>
                </tr>
                <!-- Sub-Fila 3: Operador de Metalurgia -->
                <tr>
                    <!-- Etiqueta para el operador -->
                    <td class="label-cell-wide">OPERADOR DE METALURGIA:</td>
                    <!-- Celda con el selector de operador -->
                    <td class="input-cell">
                         <!-- Selector de operador vinculado a selectedMetaUser -->
                         <select v-model="selectedMetaUser" class="header-select red-box-style full-width">
                             <option value="">-- Seleccionar --</option>
                             <!-- Itera sobre los operadores meta disponibles -->
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

    <!-- Muestra mensaje de carga si la variable loading es verdadera -->
    <div v-if="loading" class="state-message">Cargando datos...</div>
    <!-- Muestra mensaje de error si la variable error tiene contenido -->
    <div v-else-if="error" class="state-message error">{{ error }}</div>

    <!-- Contenedor para la tabla de ensayos con scroll horizontal si es necesario -->
    <div class="table-container">
      <!-- Tabla principal de datos de ensayos -->
      <table class="assays-table">
        <thead>
          <!-- Fila de encabezados agrupados -->
          <tr>
            <!-- Grupo: Identificación (ocupa 4 columnas) -->
            <th colspan="4" class="group-header">IDENTIFICACIÓN</th>
            <!-- Grupo: Datos Físicos (ocupa 5 columnas) -->
            <th colspan="5" class="group-header">DATOS FÍSICOS</th>
            <!-- Grupo: Elementos Analizados (ocupa 5 columnas) -->
            <th colspan="5" class="group-header">ELEMENTOS POR ANALIZAR</th>
          </tr>
          <!-- Fila de encabezados individuales -->
          <tr>
            <th>CÓDIGO</th> <!-- ID Químico -->
            <th>MUESTRA</th> <!-- Nombre de la muestra -->
            <th>SN</th> <!-- Tag o SN -->
            <th>ID</th> <!-- ID de instancia -->
            <th>HORA</th> <!-- Hora del ensayo -->
            <th>TARA</th> <!-- Peso Tara -->
            <th>PESO TOTAL</th> <!-- Peso Total -->
            <th>PESO SECO</th> <!-- Peso Seco -->
            <th>% SÓLIDOS</th> <!-- Porcentaje de Sólidos -->
            <th>%Fe</th> <!-- Porcentaje de Hierro -->
            <th>%Cu</th> <!-- Porcentaje de Cobre -->
            <th>%Zn</th> <!-- Porcentaje de Zinc -->
            <th>%Mo</th> <!-- Porcentaje de Molibdeno -->
            <th>%Ins</th> <!-- Porcentaje de Insolubles -->
          </tr>
        </thead>
        <tbody>
          <!-- Itera sobre los ensayos filtrados para generar las filas -->
          <tr v-for="assay in filteredAssays" :key="assay.id">
            <!-- Muestra el Código Químico si existe -->
            <td>{{ assay.chemical_id || '' }}</td>
            <!-- Muestra el Nombre de la Muestra (obtenido por helper) -->
            <td>{{ getSampleName(assay.sample) }}</td>
            <!-- Muestra el Tag/SN de la Muestra (obtenido por helper) -->
            <td>{{ getSampleTag(assay.sample) }}</td>
            <!-- Muestra el ID de Instancia -->
            <td>{{ assay.instance }}</td>
            <!-- Muestra la Hora formateada -->
            <td>{{ formatTime(assay.time) }}</td>
            <!-- Muestra la Tara formateada -->
            <td>{{ formatNumber(assay.tara) }}</td>
            <!-- Muestra el Peso Total formateado -->
            <td>{{ formatNumber(assay.tweight) }}</td>
            <!-- Muestra el Peso Seco formateado -->
            <td>{{ formatNumber(assay.dweight) }}</td>
            <!-- Muestra el % Sólidos formateado -->
            <td>{{ formatNumber(assay.pSol) }}</td>
            <!-- Muestra el % Fe formateado -->
            <td>{{ formatNumber(assay.pFe) }}</td>
            <!-- Muestra el % Cu formateado -->
            <td>{{ formatNumber(assay.pCu) }}</td>
            <!-- Muestra el % Zn formateado -->
            <td>{{ formatNumber(assay.pZn) }}</td>
            <!-- Muestra el % Mo formateado -->
            <td>{{ formatNumber(assay.pMo) }}</td>
            <!-- Muestra el % Ins formateado -->
            <td>{{ formatNumber(assay.pIns) }}</td>
          </tr>

          <!-- Muestra mensaje si no hay resultados tras filtrar y no está cargando -->
          <tr v-if="filteredAssays.length === 0 && !loading">
            <td colspan="14" class="no-results">
              No hay registros que coincidan con los filtros.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
// Importa funciones reactivas y hooks del ciclo de vida de Vue
import { ref, computed, onMounted } from 'vue';
// Importa la instancia de API para realizar peticiones HTTP
import { api } from '../../api';

// --- Estado Reactivo ---
// Almacena la fecha seleccionada por defecto es la fecha actual (ISO string)
const selectedDate = ref(new Date().toISOString().split('T')[0]);
// Almacena el ID del equipo seleccionado en el filtro
const selectedEquipment = ref('');
// Almacena el ID del usuario seleccionado en el filtro
const selectedUser = ref('');
// Almacena el nombre del operador metalurgista seleccionado
const selectedMetaUser = ref('');

// Almacena la lista cruda de ensayos obtenidos de la API
const assays = ref([]);
// Diccionario para acceder rápidamente a las muestras por ID
const samplesById = ref({});
// Diccionario para acceder rápidamente a los usuarios por ID
const usersById = ref({});
// Diccionario para acceder a userP (perfiles de usuario) por ID
const userPsById = ref({});

// Lista de opciones para el selector de Equipos
const equipmentOptions = ref([]);
// Lista de opciones para el selector de Usuarios
const userOptions = ref([]);
// Lista de opciones para el selector de Operadores (Strings únicos)
const metaUserOptions = ref([]);

// Estado de carga para mostrar spinner o mensaje
const loading = ref(false);
// Estado de error para mostrar mensajes de fallo
const error = ref('');

// --- Función de Carga de Datos ---
const loadData = async () => {
  // Inicia el estado de carga
  loading.value = true;
  // Limpia errores previos
  error.value = '';
  try {
    // Realiza múltiples peticiones en paralelo para cargar todos los datos necesarios
    const [assaysRes, samplesRes, usersRes, userPsRes, equipRes, plantsRes, areasRes] = await Promise.all([
      api.get('assays/'),    // Obtiene ensayos
      api.get('samples/'),   // Obtiene muestras
      api.get('users/').catch(() => ({ data: [] })), // Obtiene usuarios (con manejo de error individual)
      api.get('userp/').catch(() => ({ data: [] })), // Obtiene userp (perfiles)
      api.get('equipments/').catch(() => ({ data: [] })), // Obtiene equipos
      api.get('plants/').catch(() => ({ data: [] })), // Obtiene plantas (no usado directamente pero parte de carga masiva)
      api.get('areas/').catch(() => ({ data: [] })),  // Obtiene áreas (no usado directamente)
    ]);

    // Asigna los datos de ensayos
    assays.value = assaysRes.data || [];

    // Procesa y mapea las muestras
    const samples = samplesRes.data || [];
    samplesById.value = samples.reduce((acc, s) => {
      acc[s.id] = s; // Mapa ID -> Objeto Muestra
      return acc;
    }, {});

    // Procesa y mapea los usuarios
    const users = usersRes.data || [];
    userOptions.value = users;
    usersById.value = users.reduce((acc, u) => {
      acc[u.id] = u; // Mapa ID -> Objeto Usuario
      return acc;
    }, {});

    // Procesa y mapea UserPs
    const userPs = userPsRes.data || [];
    userPsById.value = userPs.reduce((acc, up) => {
      acc[up.id] = up; // Mapa ID -> Objeto UserP
      return acc;
    }, {});

    // Extrae lista única de "meta_user" (operadores que han registrado datos)
    const metas = new Set();
    assays.value.forEach(a => {
        if(a.meta_user) metas.add(a.meta_user);
    });
    // Añade también los nombres de los usuarios cargados como posibles operadores
    userOptions.value.forEach(u => metas.add(`${u.nombre} ${u.apellido}`));
    // Convierte el Set a Array y ordena alfabéticamente
    metaUserOptions.value = Array.from(metas).sort();

    // Procesa Opciones de Equipo
    // (plantsById y areasById se crean pero no se usan activamente en la lógica actual)
    const plantsById = {};
    (plantsRes.data || []).forEach(p => plantsById[p.id] = p.name);

    const areasById = {};
    (areasRes.data || []).forEach(a => areasById[a.id] = a);

    const equips = equipRes.data || [];
    // Define IDs de equipos permitidos para mostrar en este reporte específico
    const allowedEquipments = [1, 2, 5, 6];

    // Filtra y transforma los equipos para el selector
    equipmentOptions.value = equips
        .filter(e => allowedEquipments.includes(e.id))
        .map(e => {
            return {
                id: e.id,
                label: `${e.name} - ${e.description}` // Formato: Nombre - Descripción
            };
        }).sort((a,b) => a.label.localeCompare(b.label)); // Ordena alfabéticamente

  } catch (err) {
    // Registra error en consola
    console.error("Error cargando datos:", err);
    // Muestra mensaje de error al usuario
    error.value = "Error al cargar los datos del servidor.";
  } finally {
    // Finaliza el estado de carga
    loading.value = false;
  }
};

// --- Propiedades Computadas ---
// Filtra los ensayos según los criterios seleccionados por el usuario
const filteredAssays = computed(() => {
  return assays.value.filter(a => {
    // 1. Filtro por Fecha
    if (selectedDate.value && a.date !== selectedDate.value) return false;

    // 2. Filtro por Equipo
    if (selectedEquipment.value) {
        // Obtiene la muestra asociada al ensayo
        const s = samplesById.value[a.sample];
        let eqId = null;
        // Resuelve el ID del equipo (puede venir como objeto o ID directo)
        if (s && s.equipment) {
            eqId = (typeof s.equipment === 'object') ? s.equipment.id : s.equipment;
        }
        // Descarta si no coincide
        if (eqId != selectedEquipment.value) return false;
    }

    // 3. Filtro por Usuario
    //if (selectedUser.value) {
        // Si el ensayo no tiene userp, descarta
    //    if (!a.userp) return false;
        // Busca el objeto userp
    //    const up = userPsById.value[a.userp];
        // Si no existe o no tiene usuario asociado, descarta
    //    if (!up || !up.user) return false;
        // Compara ID de usuario
    //    if (up.user != selectedUser.value) return false;
    //}

    // 4. Filtro por Operador Metalúrgico (Meta User)
    //if (selectedMetaUser.value) {
        // Compara string exacto
    //    if (a.meta_user !== selectedMetaUser.value) return false;
    //}

    // Si pasa todos los filtros, incluye el ensayo
    return true;
  });
});

// --- Funciones Auxiliares (Helpers) ---

// Obtiene el nombre de la muestra dado su ID
const getSampleName = (sampleId) => {
  if (!sampleId) return '';
  const sample = samplesById.value[sampleId];
  // Retorna nombre si existe, sino un fallback con el ID
  return sample ? sample.name : `ID ${sampleId}`;
};

// Obtiene el Tag/SN de la muestra dado su ID
const getSampleTag = (sampleId) => {
  if (!sampleId) return '';
  const sample = samplesById.value[sampleId];
  // Retorna sn si existe, sino vacío
  return sample ? sample.sn : '';
};

// Formatea la hora cortando los segundos si es necesario (HH:MM)
const formatTime = (timeStr) => {
  if (!timeStr) return '';
  // Si es largo (HH:MM:SS), corta a 5 caracteres
  return timeStr.length > 5 ? timeStr.substring(0, 5) : timeStr;
};

// Formatea números (actualmente solo passthrough, listo para lógica futura)
const formatNumber = (val) => {
  if (val === null || val === undefined) return '';
  return val;
};

// --- Ciclo de Vida ---
// Al montar el componente, carga los datos iniciales
onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* Contenedor principal de la vista */
.assays-view {
  font-family: 'Arial', sans-serif; /* Tipografía base */
  color: #000; /* Color de texto negro */
  max-width: 1200px; /* Ancho máximo para centrar */
  margin: 0 auto; /* Centrado automático */
  background: white; /* Fondo blanco */
  padding: 20px; /* Espaciado interno */
}

/* --- Estilos de la Tabla de Reporte (Encabezado) --- */
.report-table {
  width: 100%; /* Ocupa todo el ancho disponible */
  border-collapse: collapse; /* Bordes colapsados (una sola línea) */
  margin-bottom: 20px; /* Margen inferior */
  border: 1px solid #000; /* Borde externo negro sólido */
}

.report-table td {
  border: 1px solid #000; /* Borde para cada celda */
  padding: 5px; /* Espaciado interno de celda */
  vertical-align: middle; /* Alineación vertical al medio */
}

/* --- Fila 1: Header --- */
.logo-cell {
  width: 20%; /* Ancho fijo para columna logo */
  text-align: center; /* Texto centrado */
}
.logo-main {
  font-weight: bold; /* Negrita */
  font-size: 1.1rem; /* Tamaño de fuente */
  color: #c62828; /* Rojo oscuro corporativo */
}
.logo-sub {
  font-size: 0.8rem; /* Tamaño pequeño */
  color: #555; /* Gris oscuro */
  letter-spacing: 2px; /* Espaciado entre letras */
}
.logo-bottom {
  font-weight: bold; /* Negrita */
  font-size: 0.9rem; /* Tamaño mediano */
  color: #555; /* Gris oscuro */
}

.title-cell {
  width: 60%; /* Columna central ancha */
  text-align: center; /* Texto centrado */
}
.title-text {
  font-weight: bold; /* Negrita */
  font-size: 1.1rem; /* Tamaño grande */
  margin-bottom: 10px; /* Espaciado inferior */
}
.equipment-select-container {
  display: inline-block; /* Comportamiento en línea bloque */
  padding: 2px; /* Padding mínimo */
  min-width: 250px; /* Ancho mínimo para el selector */
}

.code-cell {
  width: 20%; /* Ancho fijo columna derecha */
  font-size: 0.8rem; /* Fuente pequeña */
  text-align: right; /* Alineado a la derecha */
  vertical-align: top; /* Alineado arriba */
  line-height: 1.4; /* Altura de línea */
}

/* --- Fila 2: Unidad Minera --- */
.full-width-cell {
  font-weight: bold; /* Texto en negrita */
  /* El borde ya viene del td estándar */
}
.flex-row-space {
    display: flex; /* Flexbox */
    justify-content: space-between; /* Espacio entre extremos */
    width: 100%; /* Ancho total */
    align-items: center; /* Centrado vertical */
}

/* --- Tablas Anidadas para alineación precisa --- */
.no-padding-cell {
  padding: 0 !important; /* Elimina padding para ajustar tabla interna */
  /* Mantener el borde del td contenedor */
}

.inner-table {
  width: 100%; /* Ancho total */
  border-collapse: collapse; /* Colapsar bordes */
  margin: 0; /* Sin margen */
  border: none; /* Sin borde externo propio */
}
.inner-table tr {
    border-bottom: 1px solid #000; /* Línea divisoria entre filas internas */
}
.inner-table tr:last-child {
    border-bottom: none; /* La última fila no necesita borde inferior (lo da la tabla padre) */
}
.inner-table td {
    border: none; /* Sin borde completo */
    border-right: 1px solid #000; /* Solo borde derecho */
    padding: 5px; /* Espaciado */
}
.inner-table td:last-child {
    border-right: none; /* La última celda no necesita borde derecho */
}

/* --- Celdas Personalizadas Fila 3 --- */
.label-cell {
    width: 20%; /* Ancho etiqueta */
    font-weight: bold; /* Negrita */
    background-color: #f5f5f5; /* Fondo gris claro */
}
.value-cell {
    width: 30%; /* Ancho valor */
}

/* --- Celdas Personalizadas Fila 4+ --- */
.label-cell-wide {
    width: 30%; /* Etiqueta más ancha */
    font-weight: bold; /* Negrita */
}
.input-cell {
    width: 40%; /* Celda para inputs */
}
.right-logo-cell {
    width: 30%; /* Columna derecha para logo */
    text-align: center; /* Centrado */
    vertical-align: middle; /* Centrado vertical */
}

/* --- Estilos de Controles (Inputs/Selects) --- */
.header-select {
  border: none; /* Sin borde nativo */
  background: transparent; /* Fondo transparente */
  font-family: inherit; /* Hereda fuente */
  font-size: 1rem; /* Tamaño fuente estándar */
  outline: none; /* Sin outline al foco */
  cursor: pointer; /* Cursor de mano */
  width: 100%; /* Ancho total */
}
.date-input {
    border: none; /* Sin borde nativo */
    font-family: inherit; /* Hereda fuente */
    font-size: 1rem; /* Tamaño fuente */
    outline: none; /* Sin outline */
}

.red-box-style {
    /* border removed based on design choice */
    padding: 2px 5px; /* Espaciado interno */
    font-weight: bold; /* Negrita */
    color: #000; /* Texto negro */
    text-align: center; /* Texto centrado */
    text-align-last: center; /* Centra el texto seleccionado en algunos navegadores */
}
.full-width {
    width: 100%; /* Ancho total */
    box-sizing: border-box; /* Incluye padding en el ancho */
}

/* --- Estilos Logo Derecho --- */
.logo-container {
    display: flex; /* Flexbox */
    flex-direction: column; /* Columna */
    align-items: center; /* Centrado horizontal */
}
.logo-text-right {
    font-size: 0.8rem; /* Tamaño pequeño */
    color: #1976d2; /* Azul */
    font-weight: bold; /* Negrita */
    margin-top: 5px; /* Margen superior */
}

/* --- Tabla de Resultados (Ensayos) --- */
.table-container {
  overflow-x: auto; /* Scroll horizontal si es necesario */
  margin-top: 20px; /* Margen superior */
}

.assays-table {
  width: 100%; /* Ancho total */
  border-collapse: collapse; /* Bordes colapsados */
  font-size: 0.8rem; /* Fuente pequeña para datos densos */
}

.assays-table th, .assays-table td {
  border: 1px solid #000; /* Borde negro fino */
  padding: 4px 6px; /* Espaciado compacto */
  text-align: center; /* Texto centrado */
}

.assays-table thead th {
  background-color: #e0e0e0; /* Fondo gris para encabezados */
  font-weight: bold; /* Negrita */
}

.group-header {
  background-color: #bdbdbd !important; /* Gris más oscuro para grupos */
  text-transform: uppercase; /* Mayúsculas */
}

.no-results {
  padding: 20px; /* Espaciado amplio */
  text-align: center; /* Centrado */
  color: #666; /* Texto gris */
}

.state-message {
  text-align: center; /* Mensaje centrado */
  padding: 10px; /* Espaciado */
}
.state-message.error { color: red; } /* Texto rojo para errores */
</style>
