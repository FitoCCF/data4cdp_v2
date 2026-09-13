<template>
  <div class="assays-view">
    <!-- Selector de Equipo y Panel de Extracción .clb en la Cabecera -->
    <div class="header-actions">
      <div class="analyzer-group">
        <label for="equipment-select">Filtrar por Analizador:</label>
        <select
          id="equipment-select"
          v-model="selectedEquipmentId"
          @change="handleEquipmentChange"
          class="equipment-select"
          :disabled="loading"
        >
          <option :value="null" disabled>-- Seleccione un Analizador --</option>
          <option v-for="eq in equipmentsList" :key="eq.id" :value="eq.id">
            {{ eq.name }} {{ eq.description ? `- ${eq.description}` : '' }}
          </option>
        </select>
      </div>

      <!-- Controles para la extracción de archivo .clb de calibración -->
      <div v-if="selectedEquipmentId" class="clb-export-panel">
        <div class="clb-field">
          <label for="clb-start-date">Fecha Inicio:</label>
          <input
            id="clb-start-date"
            type="date"
            v-model="startDate"
            class="clb-input"
          />
        </div>

        <div class="clb-field">
          <label for="clb-end-date">Fecha Fin:</label>
          <input
            id="clb-end-date"
            type="date"
            v-model="endDate"
            class="clb-input"
          />
        </div>

        <div class="clb-field">
          <label for="clb-sample-select">Muestra:</label>
          <select
            id="clb-sample-select"
            v-model="selectedSampleId"
            class="clb-select"
          >
            <option value="">-- Todas las Muestras --</option>
            <option v-for="s in samplesList" :key="s.id" :value="s.id">
              {{ s.tag ? `${s.tag} - ${s.name}` : s.name }}
            </option>
          </select>
        </div>

        <button
          class="btn-clb-export"
          @click="exportClbFile"
          :disabled="isExporting || loading"
          title="Descargar archivo .clb delimitado por tabuladores"
        >
          <span v-if="isExporting">⏳ Extrayendo...</span>
          <span v-else>📥 Extraer .clb</span>
        </button>
      </div>
    </div>

    <!-- Solo mostrar el grid si hay un equipo seleccionado -->
    <div v-if="selectedEquipmentId" class="grid-container">
        <ExcelGrid
          title="Mantenimiento de Ensayos"
          :headers="headers"
          :data="assaysData"
          :columnsConfig="columnsConfig"
          :currentPage="currentPage"
          :totalPages="totalPages"
          :totalItems="totalItems"
          :pageSize="pageSize"
          :serverSideFiltering="true"
          :filterData="filterData"
          @save="handleSave"
          @delete="handleDelete"
          @pageChange="handlePageChange"
          @pageSizeChange="handlePageSizeChange"
          @filterChange="handleFilterChange"
          @sortChange="handleSortChange"
        >
          <!-- Botón en la barra de herramientas para autollenar Chemical ID correlativo -->
          <template #actions-end>
            <button
              type="button"
              class="btn-autofill"
              @click="autoFillChemicalIds(true)"
              :disabled="loading || !selectedEquipmentId"
              title="Autollenar correlativos en las filas sin Chemical ID a partir del último valor registrado en la planta"
            >
              🔢 Autollenar Chemical ID
            </button>
          </template>
        </ExcelGrid>
    </div>

    <!-- Mensaje cuando no hay equipo seleccionado -->
    <div v-else class="no-selection-msg">
        Por favor, seleccione un analizador en el menú superior para ver sus ensayos.
    </div>

    <!-- Overlay de carga -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error detallado -->
    <div v-if="error" class="error-message">
        <p><strong>Error:</strong></p>
        <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';
// Importación explícita del composable useApi
import { useApi } from '../../composables/useApi';
// Importamos la función de utilidades compartida para construir el payload sanitizado
import { buildPayloadFromRow } from '../../utils/gridHelpers';

// ============================================================================
// 1. CONFIGURACIÓN DE COLUMNAS
// ============================================================================
const headers = [
  'ID', 'Fecha', 'Hora', 'Instancia', 'N1 Fe', 'N2 Cu', 'N3 Zn', 'N4 Mo',
  'N5 Ech5', 'N6 Sc', 'N7 Ech7', '% Fe', '% Cu', '% Zn', '% Mo', '% Ins', '% Ox', '% Sol',
  'Tara', 'Peso Total', 'Peso Seco', 'Peso Prod.', 'Chemical ID',
  'Muestra', 'A1 Fe', 'A2 Cu', 'A3 Zn', 'A4 Mo', 'A5 A5', 'A6 Sol', 'A7 A7',
  'Usuario', 'Meta User'
];

const colKeys = [
  'id', 'date', 'time', 'instance', 'n1fe', 'n2cu', 'n3zn', 'n4mo',
  'n5ech5', 'n6sc', 'n7ech7', 'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pOx', 'pSol',
  'tara', 'tweight', 'dweight', 'pweight', 'chemical_id',
  'sample', 'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7',
  'user', 'meta_user'
];

// ============================================================================
// 2. ESTADO REACTIVO
// ============================================================================
const assaysData = ref([]);
const equipmentsList = ref([]);
const samplesList = ref([]); // Lista de muestras del equipo seleccionado
const usersList = ref([]);   // Lista de usuarios

const selectedEquipmentId = ref(null);

// Inyectamos el estado de red a través de useApi
const { loading, error, execute } = useApi();

// Estado Paginación y Filtrado
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]);

// Estado para extracción de archivo .clb de calibración
const today = new Date();
const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
const startDate = ref(firstDayOfMonth.toISOString().split('T')[0]);
const endDate = ref(today.toISOString().split('T')[0]);
const selectedSampleId = ref('');
const isExporting = ref(false);

// ============================================================================
// 3. PROPIEDADES COMPUTADAS (Dropdowns en el Grid)
// ============================================================================
const columnsConfig = computed(() => {
    // La clave '23' corresponde al índice de 'sample' (Muestra) en colKeys
    // La clave '31' corresponde al índice de 'user' (Usuario) en colKeys
    return {
        23: {
            type: 'select',
            options: samplesList.value.map(s => ({
                value: s.id,
                label: s.tag ? `${s.tag} - ${s.name}` : s.name
            }))
        },
        31: {
            type: 'select',
            options: usersList.value.map(u => ({
                value: u.id,
                label: `${u.nombre || ''} ${u.apellido || ''}`.trim() || `Usuario ${u.id}`
            }))
        }
    };
});

// ============================================================================
// 4. MÉTODOS DE CARGA DE DATOS
// ============================================================================

/**
 * Carga inicial: Obtiene solo los equipos del sistema "Analizadores" y todos los usuarios.
 */
const loadInitialData = async () => {
    // Utilizamos execute y definimos un custom error literal al final de la función
    await execute(async () => {
        // 1. Buscar el sistema llamado "Analizadores"
        const systemRes = await api.get('systems/', { params: { name__icontains: 'Analizadores' } });
        const systems = systemRes.data.results ? systemRes.data.results : systemRes.data;

        let analyzerSystemId = null;
        if (systems && systems.length > 0) {
            analyzerSystemId = systems[0].id;
        }

        // 2. Cargar equipos (solo los del sistema Analizadores si existe) y usuarios
        let eqParams = { page_size: 10000 };
        if (analyzerSystemId) {
            eqParams.system = analyzerSystemId;
        } else {
            console.warn('No se encontró el sistema "Analizadores". Se mostrará la lista vacía o se buscarán todos.');
        }

        const [eqRes, usersRes] = await Promise.all([
            api.get('equipments/', { params: eqParams }),
            api.get('users/', { params: { page_size: 10000 } })
        ]);

        equipmentsList.value = eqRes.data.results ? eqRes.data.results : eqRes.data;
        usersList.value = usersRes.data.results ? usersRes.data.results : usersRes.data;

        // 3. Autoseleccionar el primer equipo de la lista filtrada
        if (equipmentsList.value && equipmentsList.value.length > 0) {
            selectedEquipmentId.value = equipmentsList.value[0].id;
            await loadData(1);
            await loadFilterData();
        } else if (analyzerSystemId) {
            error.value = 'El sistema Analizadores existe, pero no tiene equipos asociados.';
        }
    // El segundo parámetro de execute sobreescribirá la variable error si la promesa falla
    }, 'Error al cargar la lista de equipos del sistema Analizadores.');
};

/**
 * Se ejecuta cuando el usuario cambia el equipo en el menú desplegable superior.
 */
const handleEquipmentChange = async () => {
    // Resetear paginación y filtros al cambiar de equipo
    currentPage.value = 1;
    currentFilters.value = {};
    currentSort.value = { colIndex: null, direction: null };

    await loadData(1);
    await loadFilterData();
};

/**
 * Carga los datos crudos para el menú de filtros desplegable de ExcelGrid.
 */
const loadFilterData = async () => {
    if (!selectedEquipmentId.value) return;
    try {
        const response = await api.get('assays/', {
            params: {
                sample__equipment: selectedEquipmentId.value,
                page_size: 10000
            }
        });
        const results = response.data.results || response.data;

        filterData.value = results.map(assay => {
            return colKeys.map(key => {
                let value = assay[key];
                if (value !== null && typeof value === 'object') {
                    return value.id;
                }
                return value === null || value === undefined ? '' : value;
            });
        });
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

/**
 * Función principal que carga los ensayos aplicando los filtros del backend
 */
const loadData = async (page = 1) => {
    if (!selectedEquipmentId.value) return;

    // El catch interno de este método se elimina, porque execute ya formatea y vuelca los errores del servidor
    await execute(async () => {
        const params = {
            sample__equipment: selectedEquipmentId.value, // Filtro inicial por Equipo
            page,
            page_size: pageSize.value
        };

        // Aplicar filtros provenientes de ExcelGrid
        for (const [colIndex, values] of Object.entries(currentFilters.value)) {
            let fieldName = colKeys[colIndex];

            // Ajuste de nombres de campos si es necesario
            if (fieldName === 'userp') fieldName = 'user';

            if (fieldName && values.length > 0) {
                const vals = Array.from(values);
                const validVals = vals.filter(v => v !== '');
                if (validVals.length > 0) {
                    params[`${fieldName}__in`] = validVals.join(',');
                }
                if (vals.includes('')) {
                    params[`${fieldName}__isnull`] = 'True';
                }
            }
        }

        // Aplicar ordenamiento proveniente de ExcelGrid
        if (currentSort.value.colIndex !== null) {
            let fieldName = colKeys[currentSort.value.colIndex];
            if (fieldName === 'userp') fieldName = 'user';

            if (fieldName) {
                params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
            }
        }

        // Ejecutar peticiones en paralelo: Ensayos (paginados) y Muestras del equipo (para el dropdown interno)
        const [assaysRes, samplesRes] = await Promise.all([
            api.get('assays/', { params }),
            api.get('samples/', { params: { equipment: selectedEquipmentId.value, page_size: 10000 } })
        ]);

        // Procesar muestras
        samplesList.value = samplesRes.data.results ? samplesRes.data.results : samplesRes.data;

        // Procesar ensayos y variables de paginación
        const responseData = assaysRes.data;
        let dataArray = [];

        if (responseData && responseData.results) {
            dataArray = responseData.results;
            totalItems.value = responseData.count;
            totalPages.value = Math.ceil(responseData.count / pageSize.value);
            currentPage.value = page;
        } else if (Array.isArray(responseData)) {
            dataArray = responseData;
            totalItems.value = dataArray.length;
            totalPages.value = 1;
            currentPage.value = 1;
        }

        // Formatear los datos a la matriz bidimensional esperada por ExcelGrid
        assaysData.value = dataArray.map(assay => {
            return colKeys.map(key => {
                let value = assay[key];

                // Si la API nos devuelve un objeto anidado (ej. sample o user), extraer solo el ID
                if (value !== null && typeof value === 'object') {
                    return value.id;
                }

                if (value === null || value === undefined) {
                    return '';
                }
                return value;
            });
        });

        // Autollenado automático hacia adelante de chemical_id si existen filas nuevas sin código
        await autoFillChemicalIds(false);
    }); // Sin mensaje personalizado; useApi.js reportará el estado real del servidor HTTP
};

/**
 * Autocompleta de manera correlativa y hacia adelante los valores faltantes de 'chemical_id'
 * (columna index 22) tomando como base el MAX(chemical_id) de la planta asociada al analizador seleccionado.
 * 
 * Regla de correlatividad por Planta:
 * - Concentradora 1 (Courier Flotacion C1 y Courier Molibdeno 1): serie ~26,000.
 * - Concentradora 2 (Courier Flotacion C2 y Courier Molibdeno C2): serie ~10,000.
 * 
 * Edición manual posterior:
 * - Las celdas de 'Chemical ID' (columna 22) en ExcelGrid son editables en modo edición.
 *   El usuario puede modificar cualquier código antes de presionar 'Guardar Cambios'.
 * 
 * @param {boolean} notifyUser - Si es true, notifica mediante alert al usuario o pide confirmación si ya están llenos.
 */
const autoFillChemicalIds = async (notifyUser = false) => {
    if (!selectedEquipmentId.value || !assaysData.value || assaysData.value.length === 0) {
        if (notifyUser) {
            alert('No hay ensayos cargados o no hay un analizador seleccionado.');
        }
        return;
    }

    const chemicalIdColIndex = 22; // Índice de 'chemical_id' en colKeys

    // Identificar las filas de la vista actual que no tienen Chemical ID asignado
    const emptyRowIndices = [];
    assaysData.value.forEach((row, idx) => {
        const val = row[chemicalIdColIndex];
        // Si notifyUser es false (llamada automática), sólo autollenamos filas nuevas sin ID en BD (row[0] === '')
        // Si notifyUser es true (clic en botón), llenamos cualquier fila con chemical_id vacío
        if (val === '' || val === null || val === undefined) {
            if (notifyUser || row[0] === '' || row[0] === 'nuevo') {
                emptyRowIndices.push(idx);
            }
        }
    });

    if (emptyRowIndices.length === 0 && !notifyUser) {
        return;
    }

    try {
        // Consultamos al backend el siguiente código correlativo disponible para la planta
        const res = await api.get('assays/next-chemical-id/', {
            params: { equipment_id: selectedEquipmentId.value }
        });

        if (!res.data || !res.data.next_chemical_id) {
            console.warn('Respuesta inesperada de next-chemical-id:', res.data);
            return;
        }

        const nextBaseId = res.data.next_chemical_id;

        if (emptyRowIndices.length > 0) {
            // Asignamos números correlativos secuenciales comenzando desde nextBaseId
            let currentSeq = nextBaseId;
            emptyRowIndices.forEach(idx => {
                assaysData.value[idx][chemicalIdColIndex] = currentSeq++;
            });

            // Disparamos reactividad para que ExcelGrid actualice sus celdas
            assaysData.value = [...assaysData.value];

            if (notifyUser) {
                alert(`✅ Se autollenaron ${emptyRowIndices.length} registro(s) con Chemical ID correlativo iniciando en ${nextBaseId}.\nPuedes editar cualquier valor en la columna 'Chemical ID' antes de presionar 'Guardar Cambios'.`);
            }
        } else if (notifyUser) {
            // Si el usuario presionó el botón pero todos ya tienen código, ofrecer opción de reasignar
            const confirmReassign = confirm(
                `Todos los ${assaysData.value.length} ensayos visibles ya cuentan con un Chemical ID.\n\n` +
                `¿Deseas recalcular y reasignar correlativos secuenciales a partir del próximo código de la planta (${nextBaseId})?`
            );

            if (confirmReassign) {
                let currentSeq = nextBaseId;
                assaysData.value.forEach(row => {
                    row[chemicalIdColIndex] = currentSeq++;
                });
                assaysData.value = [...assaysData.value];
                alert(`✅ Se reasignaron ${assaysData.value.length} registro(s) correlativos iniciando en ${nextBaseId}.`);
            }
        }
    } catch (err) {
        console.error('Error al autollenar chemical_id:', err);
        if (notifyUser) {
            alert('Error al consultar el siguiente Chemical ID disponible en el servidor.');
        }
    }
};

// --- Manejadores de Eventos del Componente ExcelGrid ---
const handlePageChange = (newPage) => { loadData(newPage); };
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

// ============================================================================
// 5. MÉTODOS DE GUARDADO Y ELIMINACIÓN
// ============================================================================

const handleSave = async (updatedGrid) => {
    try {
        // Envolvemos exclusivamente las peticiones que impactan la BD
        await execute(async () => {
            const promises = updatedGrid.map(row => {
                // Reconstruimos el JSON usando la utilidad de sanitización compartida
                const payload = buildPayloadFromRow(row, colKeys);

                const id = payload.id;
                if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
                    return api.put(`assays/${id}/`, payload);
                } else {
                    delete payload.id;
                    return api.post('assays/', payload);
                }
            });

            await Promise.all(promises);
            alert('Cambios guardados correctamente.');
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (err) {
        // Conservamos solo la alerta de UI y el catch genérico de Axios lo maneja useApi
        alert('Error al guardar. Revisa el mensaje de error en pantalla.');
    }
};

const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    try {
        // Bloqueamos la vista mientras se eliminan registros iterativamente
        await execute(async () => {
            const deletePromises = idsToDelete.map(id => api.delete(`assays/${id}/`));
            await Promise.all(deletePromises);
            alert(`${idsToDelete.length} ensayo(s) eliminado(s) correctamente.`);

            let pageToLoad = currentPage.value;
            if (idsToDelete.length >= assaysData.value.length && pageToLoad > 1) {
                pageToLoad -= 1;
            }

            await loadData(pageToLoad);
            await loadFilterData();
        });
    } catch (err) {
        alert('Ocurrió un error al eliminar los registros.');
    }
};

// ============================================================================
// 5.1 EXTRACCIÓN DE ARCHIVO .CLB
// ============================================================================
/**
 * Extrae y descarga un archivo de texto plano (.clb) con las lecturas y porcentajes
 * de calibración delimitadas por tabuladores, aplicando el rango de fechas, la muestra seleccionada
 * y conservando los filtros activos de la tabla.
 */
const exportClbFile = async () => {
  if (!selectedEquipmentId.value) {
    alert('Por favor selecciona un analizador primero.');
    return;
  }

  if (!startDate.value || !endDate.value) {
    alert('Por favor selecciona una fecha de inicio y una fecha de fin.');
    return;
  }

  if (startDate.value > endDate.value) {
    alert('La fecha de inicio no puede ser posterior a la fecha de fin.');
    return;
  }

  isExporting.value = true;

  try {
    const params = {
      sample__equipment: selectedEquipmentId.value,
      date__gte: startDate.value,
      date__lte: endDate.value,
      page_size: 10000,
      ordering: 'date,time'
    };

    // Si se seleccionó una muestra específica en el selector
    if (selectedSampleId.value) {
      params.sample = selectedSampleId.value;
    }

    // Conservar filtros activos adicionales aplicados en la grilla ExcelGrid
    for (const [colIndex, values] of Object.entries(currentFilters.value)) {
      let fieldName = colKeys[colIndex];
      if (fieldName === 'userp') fieldName = 'user';

      // Si ya filtramos por muestra arriba, evitar conflicto
      if (fieldName === 'sample' && selectedSampleId.value) continue;

      if (fieldName && values.length > 0) {
        const vals = Array.from(values);
        const validVals = vals.filter(v => v !== '');
        if (validVals.length > 0) {
          params[`${fieldName}__in`] = validVals.join(',');
        }
        if (vals.includes('')) {
          params[`${fieldName}__isnull`] = 'True';
        }
      }
    }

    const response = await api.get('assays/', { params });
    const assays = response.data.results || response.data || [];

    if (!assays || assays.length === 0) {
      alert('No se encontraron registros de ensayos para el rango de fechas, analizador y muestra seleccionados.');
      isExporting.value = false;
      return;
    }

    // Determinar si el analizador seleccionado es de Molibdeno (Equipos ID 2 y 6)
    const isMolyAnalyzer = [2, 6].includes(Number(selectedEquipmentId.value));

    // Cabecera solicitada con columnas separadas por tabulador (%Ox solo para analizadores de moly)
    const headersClb = isMolyAnalyzer
      ? ['Fecha', 'Hora', 'FE', 'CU', 'ZN', 'MO', 'SC', '% Fe', '% Cu', '% Zn', '% Mo', '%Ins', '%Ox', '%Sol']
      : ['Fecha', 'Hora', 'FE', 'CU', 'ZN', 'MO', 'SC', '% Fe', '% Cu', '% Zn', '% Mo', '%Ins', '%Sol'];

    const monthsClb = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const formatClbDate = (dateStr) => {
      if (!dateStr) return '';
      const cleanDate = String(dateStr).split('T')[0];
      const parts = cleanDate.split('-');
      if (parts.length === 3) {
        const year2Digits = String(parts[0]).slice(-2);
        const monthIndex = parseInt(parts[1], 10) - 1;
        const day = String(parts[2]).padStart(2, '0');
        const month = monthsClb[monthIndex] || parts[1];
        return `${day}/${month}/${year2Digits}`;
      }
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        const day = String(d.getDate()).padStart(2, '0');
        const month = monthsClb[d.getMonth()];
        const year2Digits = String(d.getFullYear()).slice(-2);
        return `${day}/${month}/${year2Digits}`;
      }
      return String(dateStr);
    };

    const formatValue = (val) => {
      if (val === null || val === undefined) return '';
      return String(val);
    };

    const formatTimeVal = (timeStr) => {
      if (!timeStr) return '';
      return timeStr.length > 5 ? timeStr.substring(0, 5) : timeStr;
    };

    const lines = [];
    lines.push(headersClb.join('\t'));

    assays.forEach(a => {
      const row = [
        formatClbDate(a.date),
        formatTimeVal(a.time),
        formatValue(a.n1fe),
        formatValue(a.n2cu),
        formatValue(a.n3zn),
        formatValue(a.n4mo),
        formatValue(a.n6sc),
        formatValue(a.pFe),
        formatValue(a.pCu),
        formatValue(a.pZn),
        formatValue(a.pMo),
        formatValue(a.pIns)
      ];

      // La columna %Ox (pOx) solo se incluye para los analizadores de molibdeno (ID 2 y 6)
      if (isMolyAnalyzer) {
        row.push(formatValue(a.pOx));
      }

      row.push(formatValue(a.pSol));
      lines.push(row.join('\t'));
    });

    const clbText = lines.join('\r\n');
    const blob = new Blob([clbText], { type: 'text/plain;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    // Helper para formatear fecha a ddmmYY (ej: 050826)
    const formatDateToDDMMYY = (dateStr) => {
      if (!dateStr) return '';
      const clean = String(dateStr).split('T')[0];
      const parts = clean.split('-');
      if (parts.length === 3) {
        const yy = String(parts[0]).slice(-2);
        const mm = String(parts[1]).padStart(2, '0');
        const dd = String(parts[2]).padStart(2, '0');
        return `${dd}${mm}${yy}`;
      }
      return dateStr.replace(/[^0-9]/g, '').slice(-6);
    };

    // Extraer el tag de la muestra (el código antes del guion ej: "C_01_S01 - Rebose..." -> "C_01_S01")
    let tagDeMuestra = 'MUESTRA';
    if (selectedSampleId.value) {
      const foundSample = samplesList.value.find(s => s.id == selectedSampleId.value);
      if (foundSample) {
        if (foundSample.tag && foundSample.tag.trim()) {
          // Extraer la parte antes del guion si viene concatenado en tag
          tagDeMuestra = foundSample.tag.includes(' - ')
            ? foundSample.tag.split(' - ')[0].trim()
            : foundSample.tag.trim();
        } else if (foundSample.name && foundSample.name.trim()) {
          // Extraer la parte antes del guion de "TAG - Nombre"
          tagDeMuestra = foundSample.name.includes(' - ')
            ? foundSample.name.split(' - ')[0].trim()
            : foundSample.name.trim();
        }
        // Reemplazar espacios residuales por guion bajo si los hubiera
        tagDeMuestra = tagDeMuestra.replace(/\s+/g, '_');
      }
    } else {
      tagDeMuestra = 'TODAS';
    }

    const startDDMMYY = formatDateToDDMMYY(startDate.value);
    const endDDMMYY = formatDateToDDMMYY(endDate.value);

    // Formato de nombre: tagdemuestra_ddmmYY_ddmmYY.clb
    link.href = url;
    link.setAttribute('download', `${tagDeMuestra}_${startDDMMYY}_${endDDMMYY}.clb`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    alert(`Archivo .clb generado y descargado exitosamente con ${assays.length} registro(s).`);
  } catch (err) {
    console.error('Error al exportar archivo .clb:', err);
    alert('Ocurrió un error al extraer los datos para el archivo .clb. Verifique la conexión.');
  } finally {
    isExporting.value = false;
  }
};

// ============================================================================
// 6. CICLO DE VIDA
// ============================================================================
onMounted(() => {
    loadInitialData();
});
</script>

<style scoped>
.assays-view {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header-actions {
  padding: 12px 16px;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.analyzer-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #334155;
}

.equipment-select {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.9rem;
  min-width: 260px;
  background-color: white;
  cursor: pointer;
  outline: none;
}

.equipment-select:focus {
  border-color: #2563eb;
}

/* Panel de controles de extracción .clb */
.clb-export-panel {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background-color: #ffffff;
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}

.clb-field {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.clb-field label {
  font-size: 0.85rem;
  color: #475569;
  font-weight: 500;
}

.clb-input {
  padding: 4px 8px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #1e293b;
  outline: none;
  background-color: #ffffff;
  cursor: pointer;
}

.clb-input:focus {
  border-color: #2563eb;
}

.clb-select {
  padding: 4px 8px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #1e293b;
  max-width: 200px;
  background-color: #ffffff;
  cursor: pointer;
  outline: none;
}

.clb-select:focus {
  border-color: #2563eb;
}

.btn-clb-export {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-clb-export:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-clb-export:disabled {
  background-color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.7;
}

/* Botón para autollenar Chemical ID correlativo */
.btn-autofill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #7c3aed;
  color: #ffffff;
  border: 1px solid #6d28d9;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.btn-autofill:hover:not(:disabled) {
  background-color: #6d28d9;
}

.btn-autofill:disabled {
  background-color: #e0e0e0;
  color: #9e9e9e;
  border-color: #bdbdbd;
  cursor: not-allowed;
  box-shadow: none;
}

.grid-container {
  flex-grow: 1;
  overflow: hidden;
}

.no-selection-msg {
  padding: 40px;
  text-align: center;
  color: #6c757d;
  font-size: 1.2rem;
  font-style: italic;
  background-color: #f8f9fa;
  flex-grow: 1;
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
  margin: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
}
</style>