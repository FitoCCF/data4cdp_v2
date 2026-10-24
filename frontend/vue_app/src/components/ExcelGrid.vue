<template>
  <!-- Contenedor principal del componente ExcelGrid -->
  <div class="excel-container" ref="containerRef" @click="handleGlobalClick">

    <!-- BARRA DE HERRAMIENTAS SUPERIOR -->
    <div class="toolbar">
      <!-- Sección izquierda: Título y estado -->
      <div class="title-section">
        <div class="title-wrapper">
          <h2>{{ title }}</h2>
          <!-- Badge que indica si estamos en modo lectura o edición -->
          <span class="status-badge" :class="isEditMode ? 'status-edit' : 'status-read'">
            {{ isEditMode ? 'MODO EDICIÓN' : 'SOLO LECTURA' }}
          </span>
        </div>
      </div>

      <!-- Sección derecha: Botones de acción -->
      <div class="actions">
        <!-- Botón para alternar entre modo lectura y edición -->
        <button
          class="btn btn-sm"
          :class="isEditMode ? 'btn-gray' : 'btn-blue'"
          @click="toggleEditMode"
        >
          {{ isEditMode ? 'Bloquear Edición' : 'Habilitar Edición' }}
        </button>

        <!-- Botones visibles solo en modo edición -->
        <template v-if="isEditMode">
          <!-- Botón para agregar una nueva fila al final -->
          <button class="btn btn-blue btn-sm" @click="addRow">Fila</button>

          <!-- Botón para eliminar filas seleccionadas -->
          <!-- Se deshabilita si no hay filas seleccionadas -->
          <button
            class="btn btn-red btn-sm"
            @click="deleteSelectedRows"
            :disabled="selectedRowIndices.size === 0"
          >
            Eliminar ({{ selectedRowIndices.size }})
          </button>

          <!-- Botón estilo Excel para autoincrementar serie (+1) hacia abajo desde la celda activa -->
          <button
            v-if="canFillDown"
            type="button"
            class="btn btn-purple btn-sm"
            @click="fillDownSeriesFromActiveCell"
            title="Incrementar +1 hacia abajo a partir de la celda activa (Atajo: Ctrl+D o doble clic en la esquina de la celda)"
          >
            ⬇️ +1 Abajo
          </button>

          <!-- Botón para guardar todos los cambios -->
          <button class="btn btn-green btn-sm" @click="promptSave">Guardar Cambios</button>
        </template>

        <!-- Slot para botones o acciones adicionales al final de la barra de herramientas -->
        <slot name="actions-end" />
      </div>
    </div>

    <!-- CONTENEDOR DE LA TABLA (SCROLLABLE) -->
    <div
      class="table-wrapper"
      @mouseup="endSelection"
      @mouseleave="endSelection"
    >
      <table class="excel-table" ref="tableRef">
        <thead>
          <!-- FILA DE GRUPOS DE CABECERAS (COLSPAN) -->
          <template v-if="headerGroups && headerGroups.length > 0">
            <template v-if="Array.isArray(headerGroups[0])">
              <tr v-for="(row, rowIdx) in headerGroups" :key="'hgr-' + rowIdx">
                <th v-if="isEditMode" class="row-header"></th>
                <th
                  v-for="(group, idx) in row"
                  :key="'hg-' + rowIdx + '-' + idx"
                  :colspan="group.colspan"
                  class="col-header group-header-cell"
                >
                  {{ group.label }}
                </th>
              </tr>
            </template>
            <tr v-else>
              <th v-if="isEditMode" class="row-header"></th>
              <th
                v-for="(group, idx) in headerGroups"
                :key="'hg-' + idx"
                :colspan="group.colspan"
                class="col-header group-header-cell"
              >
                {{ group.label }}
              </th>
            </tr>
          </template>
          <tr>
            <!-- Encabezado de la columna de índices (SOLO VISIBLE EN MODO EDICIÓN) -->
            <th v-if="isEditMode" class="row-header">#</th>

            <!-- Encabezados de columnas dinámicos -->
            <th
              v-for="(col, index) in headers"
              :key="index"
              class="col-header"
              :class="columnsConfig[index]?.headerClass || ''"
              :style="[
                { width: colWidths[index] + 'px', minWidth: colWidths[index] + 'px' },
                columnsConfig[index]?.headerStyle || {}
              ]"
            >
              <div class="header-content">
                <!-- Texto del encabezado -->
                <span class="header-text">{{ col }}</span>
                <!-- Indicador de la columna ordenada -->
                <span v-if="sortState.colIndex === index" class="sort-indicator" :title="sortState.direction === 'asc' ? 'Orden ascendente' : 'Orden descendente'">
                  {{ sortState.direction === 'asc' ? '▲' : '▼' }}
                </span>
                <span v-else-if="defaultSortOf(index)" class="sort-indicator sort-default" title="Orden por defecto">
                  {{ defaultSortOf(index).direction === 'desc' ? '▼' : '▲' }}
                </span>
                <!-- Icono de filtro (embudo) -->
                <span
                  class="filter-icon"
                  :class="{ 'active': activeFilters[index] }"
                  @click.stop="toggleFilterMenu(index, $event)"
                >
                  {{ activeFilters[index] ? 'Filtro' : '▼' }}
                </span>
              </div>
              <!-- Redimensionador de columna (solo en modo edición) -->
              <div
                v-if="isEditMode"
                class="resizer col-resizer"
                @mousedown.stop="startResize($event, index, 'col')"
                title="Arrastrar para cambiar ancho"
              ></div>
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Filas de datos (filtradas) -->
          <tr
            v-for="(item, visualIndex) in filteredGrid"
            :key="item.originalIndex + '-' + renderVersion"
            :style="{ height: rowHeights[item.originalIndex] + 'px' }"
            :class="{ 'row-selected': selectedRowIndices.has(item.originalIndex) }"
            @click="emit('rowSelect', { index: item.originalIndex, row: item.row })"
            @dblclick="emit('rowDblClick', { index: item.originalIndex, row: item.row })"
            title="Haz clic para seleccionar o doble clic para abrir el modal de detalle/edición"
          >
            <!-- Celda de índice de fila (SOLO VISIBLE EN MODO EDICIÓN) -->
            <td
              v-if="isEditMode"
              class="row-header"
              @click="selectRow(item.originalIndex, $event)"
              :class="{ 'header-selected': selectedRowIndices.has(item.originalIndex) }"
            >
                {{ item.originalIndex + 1 }}
                <!-- Redimensionador de altura de fila -->
                <div
                  v-if="isEditMode"
                  class="resizer row-resizer"
                  @mousedown.stop="startResize($event, item.originalIndex, 'row')"
                  title="Arrastrar para cambiar alto"
                ></div>
            </td>

            <!-- Celdas de datos -->
            <!-- Celdas de datos (Iteradas usando template para soportar combinaciones en filas de resumen) -->
            <template v-for="(cell, cIndex) in item.row" :key="cIndex">
              <td
                v-if="!(item.row.isSummary && cell === null)"
                class="cell"
                :class="{
                  'active': activeCell.r === visualIndex && activeCell.c === cIndex,
                  'selected': isSelected(visualIndex, cIndex),
                  'read-only': !isEditMode || item.row.isSummary || cIndex === 0 || isFormulaLocked(cIndex),
                  'formula-cell': isFormulaColumn(cIndex) && !item.row.isSummary,
                  'invalid-number': formulaInputs.has(cIndex) && !item.row.isSummary && isInvalidNumber(cell),
                  'summary-cell': item.row.isSummary,
                  'fill-target': isFillTarget(visualIndex, cIndex)
                }"
                :title="typeof cell === 'object' && cell !== null ? (cell.tooltip || '') : (columnsConfig[cIndex]?.formula?.description || '')"
                :data-col-index="cIndex"
                :data-value="typeof cell === 'object' && cell !== null ? cell.value : cell"
                :colspan="item.row.isSummary && typeof cell === 'object' && cell !== null ? (cell.colspan || 1) : 1"
                :rowspan="item.row.isSummary && typeof cell === 'object' && cell !== null ? (cell.rowspan || 1) : 1"
                @mousedown="startSelection(visualIndex, cIndex)"
                @mouseover="updateSelection(visualIndex, cIndex)"
                @focus="setActive(visualIndex, cIndex)"
                @input="handleInput"
                @paste.prevent="handlePaste($event, visualIndex, cIndex)"
                @keydown="handleKeydown($event, visualIndex, cIndex)"
                @copy="handleCopy"

                :contenteditable="isEditMode && cIndex !== 0 && !isColumnSelect(cIndex) && !isFormulaLocked(cIndex) && !item.row.isSummary"
                @blur="handleBlur($event, item.originalIndex, cIndex)"
              >
                <!-- Renderizado Condicional: Select o Texto -->
                <template v-if="isColumnSelect(cIndex) && !item.row.isSummary">
                  <select
                    v-if="isEditMode"
                    :value="cell"
                    @change="updateCellSelect($event, item.originalIndex, cIndex)"
                    @paste.prevent="handlePaste($event, visualIndex, cIndex)"
                    class="cell-select"
                    @mousedown.stop
                  >
                    <option value="">-- Seleccionar --</option>
                    <option
                      v-for="opt in getColumnOptions(cIndex)"
                      :key="opt.value"
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </option>
                  </select>
                  <span v-else>{{ getOptionLabel(cIndex, cell) }}</span>
                </template>

                <template v-else>
                  <span v-if="typeof cell === 'object' && cell !== null && cell.hasOvertime" class="overtime-indicator"></span>
                  {{ typeof cell === 'object' && cell !== null ? cell.value : cell }}
                </template>

                <!-- Cuadrito de arrastre estilo Excel (Fill Handle) para sumar +1 sucesivamente hacia abajo -->
                <span
                  v-if="isEditMode && !isTyping && activeCell.r === visualIndex && activeCell.c === cIndex && !item.row.isSummary && cIndex !== 0 && canFillDownCell(visualIndex, cIndex)"
                  class="excel-fill-handle"
                  contenteditable="false"
                  tabindex="-1"
                  @mousedown.stop="startFillDrag($event, visualIndex, cIndex)"
                  @dblclick.stop="fillDownSeriesFromActiveCell"
                  title="Arrastra hacia abajo o haz doble clic para autoincrementar +1 en las filas inferiores"
                ></span>
              </td>
            </template>
          </tr>

          <!-- Mensaje cuando no hay resultados tras filtrar -->
          <tr v-if="filteredGrid.length === 0 && localGrid.length > 0">
              <td :colspan="headers.length + (isEditMode ? 1 : 0)" class="no-results">
                  No se encontraron resultados.
              </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- CONTROLES DE PAGINACIÓN (MOVIDO AL FINAL) -->
    <div class="pagination-controls" v-if="totalPages > 1 || totalItems > 0">
        <button
          class="btn btn-sm"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)">
          Anterior
        </button>

        <span class="page-info">
          Página {{ currentPage }} de {{ totalPages }} (Total: {{ totalItems }})
          <template v-if="pageFilterActive">
            · Filtro en esta página: {{ visibleDataRowCount }} de {{ loadedDataRows.length }}
          </template>
        </span>

        <!-- Selector de tamaño de página -->
        <select class="page-size-selector" :value="pageSize" @change="changePageSize($event)">
          <option :value="25">25 / página</option>
          <option :value="50">50 / página</option>
          <option :value="100">100 / página</option>
          <option :value="200">200 / página</option>
          <option :value="500">500 / página</option>
          <option :value="10000">Todos</option>
        </select>

        <button
          class="btn btn-sm"
          :disabled="currentPage === totalPages || totalPages === 0"
          @click="changePage(currentPage + 1)">
          Siguiente
        </button>
    </div>

    <!-- MENÚ DESPLEGABLE DE FILTRO -->
    <div
      v-if="openMenuIndex !== null"
      class="filter-menu"
      :style="{ top: menuPosition.top + 'px', left: menuPosition.left + 'px' }"
      @click.stop
    >
      <div class="menu-actions">
        <button class="menu-btn" @click="sortColumn(openMenuIndex, 'asc')">Ordenar A a Z</button>
        <button class="menu-btn" @click="sortColumn(openMenuIndex, 'desc')">Ordenar Z a A</button>
        <button v-if="sortState.colIndex !== null" class="menu-btn" @click="resetSort">Quitar orden (volver al orden por defecto)</button>
        <button v-if="activeFilters[openMenuIndex]" class="menu-btn" @click="clearColumnFilter(openMenuIndex)">Borrar filtro de esta columna</button>
      </div>
      <div class="menu-divider"></div>
      <div class="menu-search">
        <input type="text" v-model="menuSearchText" placeholder="Buscar..." class="menu-search-input">
      </div>
      <div class="menu-list">
        <div v-if="menuLoading" class="menu-status">Cargando valores...</div>
        <div v-else-if="menuError" class="menu-status menu-error">{{ menuError }}</div>
        <label v-if="!menuLoading" class="menu-item bold">
          <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll"> (Seleccionar todo)
        </label>
        <label v-for="val in (menuLoading ? [] : filteredUniqueValues)" :key="val" class="menu-item">
          <input type="checkbox" :checked="tempSelectedValues.has(String(val))" @change="toggleValue(String(val))">
          {{ getFilterLabel(openMenuIndex, val) }}
        </label>
        <div v-if="menuTruncated && !menuLoading" class="menu-status">
          Se muestran los primeros {{ currentUniqueValues.length }} valores. Use "Buscar" para encontrar otros.
        </div>
      </div>
      <div class="menu-footer">
        <button class="btn btn-sm btn-gray" @click="closeFilterMenu">Cancelar</button>
        <button class="btn btn-sm btn-blue" @click="applyFilter" :disabled="menuLoading || tempSelectedValues.size === 0">Aceptar</button>
      </div>
    </div>

    <!-- Input oculto para ayudar al copiado -->
    <textarea ref="clipboardInput" class="clipboard-helper"></textarea>

    <!-- MODAL CONFIRMACIÓN DE GUARDADO -->
    <div v-if="showSaveModal" class="modal-overlay">
      <div class="modal-content">
        <h3>¿Guardar cambios?</h3>
        <p>Se actualizarán los datos. Esta acción no se puede deshacer.</p>
        <div class="modal-actions">
          <button class="btn btn-sm btn-gray" @click="showSaveModal = false">Cancelar</button>
          <button class="btn btn-green" @click="executeSave">Sí, Guardar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, watch, computed } from 'vue';
import { cellPassesSpec, compareCellText, resolveFilterSelection, sortFilterValues } from '../utils/gridFilterLogic';
import { applyFormulas, formulaInputColumns, isInvalidNumber, normalizeNumberText } from '../utils/gridFormulas';

// --- PROPS ---
const props = defineProps({
  title: { type: String, default: 'Tabla de Datos' },
  headers: { type: Array, required: true, default: () => [] },
  headerGroups: { type: Array, default: () => [] },
  data: { type: Array, required: true, default: () => [] },
  columnsConfig: { type: Object, default: () => ({}) },
  rowCalculator: { type: Function, default: null },
  // Nuevas props para Paginación y Filtrado backend
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  totalItems: { type: Number, default: 0 },
  pageSize: { type: Number, default: 25 },
  serverSideFiltering: { type: Boolean, default: false }, // Indica si el filtro lo hace el backend
  filterData: { type: Array, default: () => [] }, // Datos completos para el menú de filtros
  // Opcional (recomendado con serverSideFiltering): función que trae del servidor los valores de una columna.
  // Firma: (colIndex, specsActivos, textoBuscar) => Promise<{ values, truncated } | null>.
  // Si devuelve null, la grilla usa filterData o las filas cargadas. Ver utils/gridQuery.js.
  filterValuesLoader: { type: Function, default: null },
  // Alcance de los filtros de columna:
  //  'page' (por defecto): filtran solo las filas de la página cargada; el resultado nunca supera el
  //          tamaño de página y no se consulta al servidor. Al cambiar de página el filtro se aplica a
  //          las filas nuevas.
  //  'all':  filtran todos los registros en el servidor (requiere serverSideFiltering y emite filterChange).
  // El orden ("Ordenar A a Z") sigue el mismo alcance: en 'page' ordena la página, en 'all' el servidor.
  filterScope: { type: String, default: 'page', validator: (v) => ['page', 'all'].includes(v) },
  // Orden por defecto de varios niveles, aplicado a las filas cargadas: [{ colIndex, direction }, ...].
  // Ej. Ensayos: Fecha ascendente y, dentro de cada fecha, Muestra ascendente. Si el usuario ordena por
  // una columna, esa pasa a ser el primer criterio y el orden por defecto queda como desempate.
  defaultSort: { type: Array, default: () => [] }
});

// --- EMITS ---
const emit = defineEmits(['save', 'delete', 'pageChange', 'pageSizeChange', 'filterChange', 'sortChange', 'rowDblClick', 'rowSelect']);

// --- MÉTODOS PAGINACIÓN ---
const changePage = (newPage) => {
    if (newPage >= 1 && newPage <= props.totalPages) {
        emit('pageChange', newPage);
    }
};

const changePageSize = (event) => {
    const newSize = parseInt(event.target.value, 10);
    emit('pageSizeChange', newSize);
};

// --- CONSTANTES ---
const MIN_COL_WIDTH = 80;
const MAX_COL_WIDTH = 400;
const DEFAULT_ROW_HEIGHT = 25;

// --- ESTADO ---
const localGrid = ref([]);
const colWidths = ref([]);
const rowHeights = ref([]);
const isEditMode = ref(false);
const showSaveModal = ref(false);
const activeCell = ref({ r: null, c: null });
const isTyping = ref(false);
const selection = ref({ start: null, end: null });
const isSelecting = ref(false);
const tableRef = ref(null);
const containerRef = ref(null);
const clipboardInput = ref(null);

const selectedRowIndices = ref(new Set());

const activeFilters = ref({});
const sortState = ref({ colIndex: null, direction: null });
const openMenuIndex = ref(null);
const menuPosition = ref({ top: 0, left: 0 });
const menuSearchText = ref('');
const tempSelectedValues = ref(new Set());
// Especificación de cada filtro activo en formato de la API ({ in|not_in: [...], empty }), por columna.
const activeFilterSpecs = ref({});
// Valores del menú obtenidos del servidor (null = se usan los valores locales).
const remoteValues = ref(null);
const menuTruncated = ref(false);
const menuLoading = ref(false);
const menuError = ref('');
let menuRequestId = 0;      // descarta respuestas de peticiones anteriores (si el usuario abre otra columna)
let searchDebounce = null;

const resizing = reactive({ active: false, type: null, index: null, startPos: 0, startSize: 0 });

// Extrae el texto real de forma segura. Asegura que valores como 0 o false no se conviertan en vacíos
// Si el valor es un objeto (usado en celdas combinadas de resumen), se extrae su propiedad 'value'.
const getCellValueStr = (val) => {
    if (val === null || val === undefined) return '';
    if (typeof val === 'object' && val.value !== undefined) return String(val.value);
    return String(val);
};

// --- COLUMNAS CALCULADAS (columnsConfig[col].formula, ver utils/gridFormulas.js) ---

const isFormulaColumn = (colIndex) => Boolean(props.columnsConfig[colIndex]?.formula);
// Columnas que alimentan alguna fórmula: deben ser numéricas (se normalizan al pegar y se marcan si no lo son).
const formulaInputs = computed(() => formulaInputColumns(props.columnsConfig));
// Columna calculada que el usuario no puede editar (solo la fórmula escribe en ella).
const isFormulaLocked = (colIndex) => isFormulaColumn(colIndex) && !props.columnsConfig[colIndex].formula.editable;

// Punto único que se ejecuta tras cambiar una celda (escribir, pegar, desplegable, autoincremento):
// recalcula las fórmulas que dependen de esa columna y luego el rowCalculator propio de la vista.
// colIndex puede ser una lista (pegado de varias columnas de una misma fila).
const afterCellChange = (row, colIndex) => {
  applyFormulas(row, colIndex, props.columnsConfig);
  if (props.rowCalculator && typeof props.rowCalculator === 'function') {
    (Array.isArray(colIndex) ? colIndex : [colIndex]).forEach((col) => props.rowCalculator(row, col));
  }
};

// --- HELPERS PARA SELECT/DROPDOWN ---

const isColumnSelect = (colIndex) => {
    return props.columnsConfig[colIndex]?.type === 'select';
};

const getColumnOptions = (colIndex) => {
    return props.columnsConfig[colIndex]?.options || [];
};

const getOptionLabel = (colIndex, value) => {
    if (!isColumnSelect(colIndex)) return value;
    const options = getColumnOptions(colIndex);
    const option = options.find(opt => opt.value == value);
    return option ? option.label : value;
};

const getFilterLabel = (colIndex, value) => {
    if (value === '') return '(Vacías)';
    return getOptionLabel(colIndex, value);
};

// --- COMPUTED ---

// Los filtros se resuelven en el servidor solo con filterScope='all'; en 'page' se filtra lo cargado.
const filtersOnServer = computed(() => props.serverSideFiltering && props.filterScope === 'all');

// Criterios de orden vigentes: el elegido por el usuario (si hay) y luego el orden por defecto.
const activeSortKeys = computed(() => {
    const keys = [];
    if (sortState.value.colIndex !== null) keys.push({ ...sortState.value });
    for (const key of props.defaultSort) {
        if (!keys.some(k => Number(k.colIndex) === Number(key.colIndex))) {
            keys.push({ colIndex: Number(key.colIndex), direction: key.direction === 'desc' ? 'desc' : 'asc' });
        }
    }
    return keys;
});
// Columna de un criterio del orden por defecto (para el indicador gris del encabezado).
const defaultSortOf = (colIndex) => props.defaultSort.find(k => Number(k.colIndex) === Number(colIndex));

// Filas de datos de la página cargada (sin filas de resumen).
const loadedDataRows = computed(() => localGrid.value.filter(row => !row.isSummary));

// Calcula qué filas se ven y en qué orden (índices de localGrid), aplicando filtros locales y orden.
const computeViewOrder = () => {
    let result = localGrid.value.map((row, index) => ({ row, originalIndex: index }));

    // --- FILTRADO LOCAL (todo lo que no filtra el servidor) ---
    const activeCols = filtersOnServer.value ? [] : Object.keys(activeFilters.value);
    if (activeCols.length > 0) {
        result = result.filter(item => {
            if (item.row.isSummary) return true; // Mantener las filas de resumen siempre visibles
            return activeCols.every(colIndex =>
                cellPassesSpec(getCellValueStr(item.row[colIndex]), activeFilterSpecs.value[colIndex], activeFilters.value[colIndex])
            );
        });
    }

    // El orden se hace aquí salvo con filterScope='all' (ahí lo hace el servidor sobre todos los registros).
    // Con filtro de página el orden también es de página: si el servidor reordenara, traería otros
    // registros y el filtro local los ocultaría (los registros "desaparecían").
    const sortKeys = activeSortKeys.value;
    if (!filtersOnServer.value && sortKeys.length > 0) {
        const dataRows = result.filter(item => !item.row.isSummary);
        const summaryRows = result.filter(item => item.row.isSummary);

        // En columnas tipo select se ordena por la etiqueta visible (p. ej. el tag de la muestra, no su id).
        const textOf = (row, colIndex) =>
            getCellValueStr(isColumnSelect(colIndex) ? getOptionLabel(colIndex, row[colIndex]) : row[colIndex]);
        // Varios niveles: se pasa al siguiente criterio solo si el anterior empata.
        dataRows.sort((a, b) => {
            for (const { colIndex, direction } of sortKeys) {
                const diff = compareCellText(textOf(a.row, colIndex), textOf(b.row, colIndex), direction);
                if (diff !== 0) return diff;
            }
            return a.originalIndex - b.originalIndex; // orden estable
        });

        result = [...dataRows, ...summaryRows]; // Reensamblar dejando el resumen al final
    }

    return result.map(item => item.originalIndex);
};

// Orden visible "congelado": se recalcula al cargar datos o al cambiar filtros/orden, pero NO al editar
// una celda. Así, como en Excel, una fila no salta de lugar ni desaparece mientras se escribe o pega en
// ella (antes, con el orden por Fecha/Muestra, pegar en esas columnas reordenaba las filas al instante).
const viewOrder = ref([]);
const refreshView = () => { viewOrder.value = computeViewOrder(); };

const filteredGrid = computed(() =>
    viewOrder.value
        .filter(index => index < localGrid.value.length)
        .map(index => ({ row: localGrid.value[index], originalIndex: index }))
);

watch(
    [activeFilters, activeFilterSpecs, sortState, () => props.defaultSort, () => props.columnsConfig, filtersOnServer],
    refreshView,
    { deep: false }
);

// --- MENÚ FILTRO ---

const currentUniqueValues = computed(() => {
    if (openMenuIndex.value === null) return [];
    const colIndex = openMenuIndex.value;
    const labelOf = (v) => getFilterLabel(colIndex, v);

    // Valores traídos del servidor: ya vienen con el filtrado cruzado aplicado.
    if (remoteValues.value !== null) {
        return sortFilterValues(remoteValues.value, labelOf);
    }

    // Con alcance 'page' el menú ofrece solo los valores de la página cargada.
    let sourceData = (filtersOnServer.value && props.filterData && props.filterData.length > 0)
                        ? props.filterData
                        : loadedDataRows.value;

    // --- FILTRADO CRUZADO ---
    // Identificamos las columnas que ya tienen filtros aplicados, excluyendo la que el usuario acaba de abrir
    const activeCols = Object.keys(activeFilters.value).filter(col => String(col) !== String(colIndex));

    if (activeCols.length > 0) {
        // Reducimos el universo de datos disponibles verificando que la fila cumpla con los demás filtros activos
        sourceData = sourceData.filter(row => {
            return activeCols.every(col => {
                return cellPassesSpec(getCellValueStr(row[col]), activeFilterSpecs.value[col], activeFilters.value[col]);
            });
        });
    }

    const values = new Set(sourceData.map(row => getCellValueStr(row[colIndex])));
    // Orden natural ("2" antes que "10") y por etiqueta visible en columnas tipo select.
    return sortFilterValues(Array.from(values), labelOf);
});

const filteredUniqueValues = computed(() => {
    if (!menuSearchText.value) return currentUniqueValues.value;
    const colIndex = openMenuIndex.value;
    return currentUniqueValues.value.filter(v => {
        const label = String(getFilterLabel(colIndex, v)).toLowerCase();
        return label.includes(menuSearchText.value.toLowerCase());
    });
});

// Indicador de la paginación: hay filtros locales sobre una grilla paginada en el servidor.
const pageFilterActive = computed(() =>
    props.serverSideFiltering && !filtersOnServer.value && Object.keys(activeFilters.value).length > 0
);
const visibleDataRowCount = computed(() => filteredGrid.value.filter(item => !item.row.isSummary).length);

const isAllSelected = computed(() => {
    return filteredUniqueValues.value.every(val => tempSelectedValues.value.has(val));
});

// Pide al servidor los valores de la columna abierta (si la vista dio filterValuesLoader).
const loadRemoteValues = async (colIndex, search = '') => {
    if (!props.filterValuesLoader || !filtersOnServer.value) return false;
    const requestId = ++menuRequestId;
    menuLoading.value = true;
    menuError.value = '';
    try {
        const result = await props.filterValuesLoader(colIndex, { ...activeFilterSpecs.value }, search);
        if (requestId !== menuRequestId) return false; // llegó tarde: el usuario ya abrió otra columna
        if (result === null) { remoteValues.value = null; menuTruncated.value = false; return true; }
        remoteValues.value = result.values.map(v => String(v));
        menuTruncated.value = Boolean(result.truncated);
        return true;
    } catch (err) {
        if (requestId !== menuRequestId) return false;
        console.error('Error cargando valores del filtro:', err);
        menuError.value = 'No se pudieron cargar los valores del filtro.';
        remoteValues.value = null; // se usan los valores locales como respaldo
        return true;
    } finally {
        if (requestId === menuRequestId) menuLoading.value = false;
    }
};

const toggleFilterMenu = async (index, event) => {
    if (openMenuIndex.value === index) { closeFilterMenu(); return; }
    openMenuIndex.value = index;
    menuSearchText.value = '';
    remoteValues.value = null;
    menuTruncated.value = false;
    searchedOnServer = false;

    const th = event.target.closest('th');
    const rect = th.getBoundingClientRect();
    const containerRect = containerRef.value.getBoundingClientRect();
    const MENU_WIDTH = 240;
    menuPosition.value = {
        top: rect.bottom - containerRect.top,
        // Se ajusta para que el menú no se salga por la derecha en las últimas columnas.
        left: Math.max(0, Math.min(rect.left - containerRect.left, containerRect.width - MENU_WIDTH))
    };

    const usesLoader = Boolean(props.filterValuesLoader) && filtersOnServer.value;
    const loaded = await loadRemoteValues(index);
    if (loaded === false && usesLoader) return; // respuesta descartada
    if (openMenuIndex.value !== index) return;

    if (activeFilters.value[index]) {
        tempSelectedValues.value = new Set(activeFilters.value[index]);
        // Con filtro "excluir" los valores nuevos (no excluidos) deben aparecer marcados.
        const spec = activeFilterSpecs.value[index];
        if (spec && spec.not_in) {
            const excluded = new Set(spec.not_in);
            currentUniqueValues.value.forEach(v => {
                if (v === '' ? !spec.empty : !excluded.has(v)) tempSelectedValues.value.add(v);
            });
        }
    } else {
        // Inicializamos el menú seleccionando por defecto los valores que sobrevivieron al filtrado cruzado
        tempSelectedValues.value = new Set(currentUniqueValues.value);
    }
};

// Con lista truncada, "Buscar" consulta al servidor (con espera de 300 ms entre teclas).
// Si la lista estaba completa, la búsqueda es local y no hace falta ir al servidor.
let searchedOnServer = false; // la lista actual es resultado de una búsqueda en el servidor (parcial)
watch(menuSearchText, (text) => {
    if (!props.filterValuesLoader || !filtersOnServer.value || openMenuIndex.value === null) return;
    if (!menuTruncated.value && !searchedOnServer) return;
    clearTimeout(searchDebounce);
    const colIndex = openMenuIndex.value;
    searchDebounce = setTimeout(async () => {
        const search = text.trim();
        await loadRemoteValues(colIndex, search);
        searchedOnServer = Boolean(search);
        // Los valores encontrados por búsqueda se muestran marcados, como en Excel.
        currentUniqueValues.value.forEach(v => tempSelectedValues.value.add(v));
    }, 300);
});

// La lista del menú no es completa si el servidor la truncó o si es resultado de una búsqueda remota.
const isMenuListPartial = () => menuTruncated.value || searchedOnServer;

const closeFilterMenu = () => {
    openMenuIndex.value = null;
    remoteValues.value = null;
    searchedOnServer = false;
    menuError.value = '';
    clearTimeout(searchDebounce);
};
const handleGlobalClick = () => { if (openMenuIndex.value !== null) closeFilterMenu(); };

const toggleValue = (val) => {
    const strVal = String(val);
    if (tempSelectedValues.value.has(strVal)) tempSelectedValues.value.delete(strVal);
    else tempSelectedValues.value.add(strVal);
};

const toggleSelectAll = () => {
    if (isAllSelected.value) filteredUniqueValues.value.forEach(v => tempSelectedValues.value.delete(String(v)));
    else filteredUniqueValues.value.forEach(v => tempSelectedValues.value.add(String(v)));
};

// Envía los filtros a la vista: (valores por columna, especificación para la API por columna).
const emitFilterChange = () => {
    if (!filtersOnServer.value) return; // con alcance 'page' el filtro es local: no se recarga nada
    const filtersToSend = {};
    for (const key in activeFilters.value) {
        filtersToSend[key] = Array.from(activeFilters.value[key]);
    }
    emit('filterChange', filtersToSend, { ...activeFilterSpecs.value });
};

const applyFilter = () => {
    const index = openMenuIndex.value;
    const result = resolveFilterSelection({
        selected: tempSelectedValues.value,
        allValues: currentUniqueValues.value,
        visibleValues: filteredUniqueValues.value,
        searchActive: Boolean(menuSearchText.value.trim()),
        truncated: isMenuListPartial()
    });

    const newActiveFilters = { ...activeFilters.value };
    const newSpecs = { ...activeFilterSpecs.value };
    if (result.clear) {
        delete newActiveFilters[index];
        delete newSpecs[index];
    } else {
        newActiveFilters[index] = result.selected;
        newSpecs[index] = result.spec;
    }
    activeFilters.value = newActiveFilters;
    activeFilterSpecs.value = newSpecs;

    emitFilterChange();
    closeFilterMenu();
};

const clearColumnFilter = (index) => {
    const newActiveFilters = { ...activeFilters.value };
    const newSpecs = { ...activeFilterSpecs.value };
    delete newActiveFilters[index];
    delete newSpecs[index];
    activeFilters.value = newActiveFilters;
    activeFilterSpecs.value = newSpecs;
    emitFilterChange();
    closeFilterMenu();
};

// Quita todos los filtros y el orden sin emitir eventos (para cuando la vista reinicia su estado,
// p. ej. al cambiar de equipo). Se expone con defineExpose.
// Vuelve al orden por defecto (defaultSort) o al de llegada si no hay.
const resetSort = () => {
    sortState.value = { colIndex: null, direction: null };
    if (filtersOnServer.value) emit('sortChange', { colIndex: null, direction: null });
    closeFilterMenu();
};

const clearFilters = () => {
    activeFilters.value = {};
    activeFilterSpecs.value = {};
    sortState.value = { colIndex: null, direction: null };
    closeFilterMenu();
};

const sortColumn = (colIndex, direction) => {
    sortState.value = { colIndex, direction };
    
    // Solo con filterScope='all' ordena el servidor; en los demás casos se ordena lo cargado (ver filteredGrid).
    if (filtersOnServer.value) {
        emit('sortChange', { colIndex, direction });
    }

    closeFilterMenu();
};

// --- INICIALIZACIÓN ---

const calculateAutoWidths = () => {
    if (!props.headers.length) return;
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = '14px Inter, sans-serif';

    const newWidths = props.headers.map((header, colIndex) => {
        let maxWidth = context.measureText(header).width + 50;
        const rowsToCheck = localGrid.value.slice(0, 50);
        rowsToCheck.forEach(row => {
                    let cellText = getCellValueStr(row[colIndex]);
            if (isColumnSelect(colIndex)) {
                        cellText = getCellValueStr(getOptionLabel(colIndex, row[colIndex]));
            }
            const width = context.measureText(cellText).width + 30;
            if (width > maxWidth) maxWidth = width;
        });
        return Math.min(MAX_COL_WIDTH, Math.max(MIN_COL_WIDTH, maxWidth));
    });
    colWidths.value = newWidths;
};

const initGrid = () => {
  if (props.data && props.data.length > 0) {
    localGrid.value = props.data.map(row => {
      const newRow = [...row];
      if (row._taskIds) Object.defineProperty(newRow, '_taskIds', { value: { ...row._taskIds }, enumerable: false, writable: true });
      if (row._taskId !== undefined) Object.defineProperty(newRow, '_taskId', { value: row._taskId, enumerable: false, writable: true });
      if (row.isSummary) Object.defineProperty(newRow, 'isSummary', { value: true, enumerable: false, writable: true });
      return newRow;
    });
  } else {
    localGrid.value = [];
  }
  refreshView();
  rowHeights.value = localGrid.value.map(() => DEFAULT_ROW_HEIGHT);
  calculateAutoWidths();
  window.addEventListener('mousemove', handleResizeMove);
  window.addEventListener('mouseup', stopResize);
};

watch(() => props.data, (newData) => {
  if (newData) {
    localGrid.value = newData.map(row => {
      const newRow = [...row];
      if (row._taskIds) Object.defineProperty(newRow, '_taskIds', { value: { ...row._taskIds }, enumerable: false, writable: true });
      if (row._taskId !== undefined) Object.defineProperty(newRow, '_taskId', { value: row._taskId, enumerable: false, writable: true });
      if (row.isSummary) Object.defineProperty(newRow, 'isSummary', { value: true, enumerable: false, writable: true });
      return newRow;
    });
    rowHeights.value = localGrid.value.map(() => DEFAULT_ROW_HEIGHT);
    refreshView();
    if (colWidths.value.length === 0 || colWidths.value.length !== props.headers.length) {
        calculateAutoWidths();
    }
  }
}, { deep: true });

// --- EDICIÓN Y EVENTOS ---

// Extrae el texto limpio de una celda ignorando elementos auxiliares como el fill handle o indicadores
const getCleanCellText = (element) => {
  if (!element) return '';
  const clone = element.cloneNode(true);
  const handle = clone.querySelector('.excel-fill-handle');
  if (handle) handle.remove();
  const indicator = clone.querySelector('.overtime-indicator');
  if (indicator) indicator.remove();
  return clone.innerText.replace(/[\r\n]+/g, '').trim();
};

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value;
  isTyping.value = false;
  selection.value = { start: null, end: null };
  activeCell.value = { r: null, c: null };
  selectedRowIndices.value.clear();
};

const promptSave = () => { showSaveModal.value = true; };
const executeSave = () => { emit('save', localGrid.value); showSaveModal.value = false; };

// Versión de render de las filas: al incrementarla Vue recrea las celdas desde localGrid. Se usa tras
// un pegado, porque una celda contenteditable editada a mano puede tener un DOM distinto del estado.
const renderVersion = ref(0);
// true mientras handlePaste desenfoca la celda: ese blur no debe copiar el texto viejo del DOM al estado.
let skipBlurSync = false;

const handleInput = () => {
  if (!isTyping.value) {
    isTyping.value = true;
  }
};

const handleBlur = (e, originalRowIndex, c) => {
  isTyping.value = false;
  if (skipBlurSync) {
    // Blur provocado por el pegado: el DOM aún muestra el valor anterior. Antes se copiaba ese valor
    // al estado y la celda donde se hizo clic perdía lo pegado (quedaba vacía o con el valor viejo).
    skipBlurSync = false;
    return;
  }
  if (!isColumnSelect(c)) {
    updateCell(e, originalRowIndex, c);
  }
};

const updateCell = (e, originalRowIndex, c) => {
  if (isFormulaLocked(c)) return; // solo la fórmula escribe en esta columna
  if (isEditMode.value) {
    localGrid.value[originalRowIndex][c] = getCleanCellText(e.target);
    afterCellChange(localGrid.value[originalRowIndex], c);
  } else {
    e.target.innerText = localGrid.value[originalRowIndex][c];
  }
};

const updateCellSelect = (e, originalRowIndex, c) => {
  localGrid.value[originalRowIndex][c] = e.target.value;
  afterCellChange(localGrid.value[originalRowIndex], c);
};

// --- SELECCIÓN DE FILAS COMPLETAS ---

const selectRow = (originalIndex, event) => {
    if (!isEditMode.value) return;
    if (!event.ctrlKey && !event.metaKey) {
        selectedRowIndices.value.clear();
    }
    if (selectedRowIndices.value.has(originalIndex)) {
        selectedRowIndices.value.delete(originalIndex);
    } else {
        selectedRowIndices.value.add(originalIndex);
    }
};

const deleteSelectedRows = () => {
    if (selectedRowIndices.value.size === 0) return;
    if (!confirm(`¿Estás seguro de eliminar ${selectedRowIndices.value.size} fila(s)?`)) return;

    const indicesToDelete = Array.from(selectedRowIndices.value).sort((a, b) => b - a);
    const idsToDelete = [];

    indicesToDelete.forEach(index => {
        const row = localGrid.value[index];
        if (row && row[0]) {
            idsToDelete.push(row[0]);
        }
        localGrid.value.splice(index, 1);
        rowHeights.value.splice(index, 1);
    });

    selectedRowIndices.value.clear();
    refreshView(); // los índices de localGrid cambiaron al borrar

    if (idsToDelete.length > 0) {
        emit('delete', idsToDelete);
    }
};

// --- SELECCIÓN Y NAVEGACIÓN ---

const startSelection = (r, c) => {
  isSelecting.value = true;
  selection.value.start = { r, c };
  selection.value.end = { r, c };
  activeCell.value = { r, c };
};
const updateSelection = (r, c) => { if (isSelecting.value) selection.value.end = { r, c }; };
const endSelection = () => { isSelecting.value = false; };
const isSelected = (r, c) => {
  if (!selection.value.start || !selection.value.end) return false;
  const minR = Math.min(selection.value.start.r, selection.value.end.r);
  const maxR = Math.max(selection.value.start.r, selection.value.end.r);
  const minC = Math.min(selection.value.start.c, selection.value.end.c);
  const maxC = Math.max(selection.value.start.c, selection.value.end.c);
  return r >= minR && r <= maxR && c >= minC && c <= maxC;
};

const handleKeydown = (e, visualR, c) => {
  if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'v')) return;

  // Atajo estilo Excel: Ctrl+D para autoincrementar serie (+1) hacia abajo
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') {
    e.preventDefault();
    if (isEditMode.value && canFillDownCell(visualR, c)) {
      fillDownSeriesFromActiveCell();
    }
    return;
  }

  const maxR = filteredGrid.value.length - 1;
  const maxC = props.headers.length - 1;
  if (e.key === 'Enter') {
    e.preventDefault();
    isTyping.value = false;
    if (document.activeElement && typeof document.activeElement.blur === 'function') {
      document.activeElement.blur();
    }
    if (visualR < maxR) focusCell(visualR + 1, c);
  }
  else if (e.key === 'Escape') {
    isTyping.value = false;
    if (document.activeElement && typeof document.activeElement.blur === 'function') {
      document.activeElement.blur();
    }
  }
  else if (e.key === 'ArrowDown') { e.preventDefault(); if (visualR < maxR) focusCell(visualR + 1, c); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (visualR > 0) focusCell(visualR - 1, c); }
  else if (e.key === 'ArrowRight') { if(!e.shiftKey && c < maxC) focusCell(visualR, c + 1); }
  else if (e.key === 'ArrowLeft') { if(!e.shiftKey && c > 0) focusCell(visualR, c - 1); }
};

// ============================================================================
// AUTOINCREMENTO / SERIE (+1) HACIA ABAJO ESTILO EXCEL
// ============================================================================

// Estado reactivo para el arrastre del manejador de autollenado
const isFilling = ref(false);
const fillStart = ref({ r: null, c: null });
const fillEnd = ref({ r: null, c: null });

/**
 * Parsea un valor para extraer prefijo alfanumérico, valor numérico y longitud de ceros a la izquierda.
 * Ejemplos:
 *   "26500"   -> { prefix: "", num: 26500, pad: 0 }
 *   "0042"    -> { prefix: "", num: 42, pad: 4 }
 *   "LAB-101" -> { prefix: "LAB-", num: 101, pad: 3 }
 */
const parseSeriesValue = (val) => {
  const str = getCellValueStr(val).trim();
  if (!str) return null;

  const match = str.match(/^(.*?)(\d+)$/);
  if (!match) return null;

  const prefix = match[1];
  const digitsStr = match[2];
  const num = parseInt(digitsStr, 10);
  if (isNaN(num)) return null;

  const pad = digitsStr.startsWith('0') && digitsStr.length > 1 ? digitsStr.length : 0;
  return { prefix, num, pad };
};

/**
 * Verifica si una celda específica permite la acción de autoincrementar hacia abajo (+1).
 */
const canFillDownCell = (visualR, colIndex) => {
  if (!isEditMode.value) return false;
  if (colIndex === null || colIndex === undefined || colIndex === 0) return false;
  if (visualR === null || visualR === undefined || visualR >= filteredGrid.value.length) return false;
  const item = filteredGrid.value[visualR];
  if (!item || item.row.isSummary) return false;
  if (isColumnSelect(colIndex)) return false;
  if (isFormulaLocked(colIndex)) return false;

  // Si la columna está explícitamente deshabilitada para autoincrementar
  if (props.columnsConfig[colIndex]?.autoIncrementDown === false) {
    return false;
  }

  // Para poder autoincrementar (+1 hacia abajo), la celda DEBE contener un valor con número parseable
  return parseSeriesValue(item.row[colIndex]) !== null;
};

/**
 * Propiedad computada que evalúa si la celda activa actual puede autoincrementar hacia abajo.
 */
const canFillDown = computed(() => {
  if (!isEditMode.value) return false;
  if (activeCell.value.r === null || activeCell.value.c === null) return false;
  return canFillDownCell(activeCell.value.r, activeCell.value.c);
});

/**
 * Función principal para autoincrementar +1 hacia abajo estilo Excel.
 * Toma el valor de la fila inicial, extrae la base numérica y añade +1 sucesivamente
 * a cada celda de las filas inferiores hasta la fila final especificada o el fin de la tabla.
 *
 * @param {number} startVisualR - Índice de la fila visual base
 * @param {number|null} endVisualR - Índice de la fila visual final (si es null, hasta el final de la tabla)
 * @param {number|null} colIndex - Índice de la columna a incrementar
 */
const fillDownSeries = (startVisualR, endVisualR = null, colIndex = null) => {
  if (startVisualR === null || startVisualR === undefined) return;
  if (colIndex === null || colIndex === undefined) {
    colIndex = activeCell.value.c;
  }
  if (colIndex === null || colIndex === undefined || colIndex === 0) return;

  // Si el usuario estaba escribiendo activamente en la celda antes de presionar el botón o arrastrar,
  // nos aseguramos de capturar el texto actualizado del elemento activo
  if (document.activeElement && document.activeElement.isContentEditable) {
    const curR = activeCell.value.r;
    const curC = activeCell.value.c;
    if (curR !== null && curC !== null && filteredGrid.value[curR]) {
      const origIdx = filteredGrid.value[curR].originalIndex;
      localGrid.value[origIdx][curC] = getCleanCellText(document.activeElement);
    }
  }

  const startItem = filteredGrid.value[startVisualR];
  if (!startItem || startItem.row.isSummary) return;

  const baseRawVal = startItem.row[colIndex];
  const parsed = parseSeriesValue(baseRawVal);

  if (!parsed) {
    alert('Para autoincrementar (+1 hacia abajo), la celda seleccionada debe contener un número (ej: 26500, 1024, etc.).');
    return;
  }

  // Determinar hasta qué fila visual rellenar
  const maxVisualRow = endVisualR !== null
    ? Math.min(endVisualR, filteredGrid.value.length - 1)
    : filteredGrid.value.length - 1;

  if (maxVisualRow <= startVisualR) {
    return;
  }

  let incrementStep = 1;
  for (let vr = startVisualR + 1; vr <= maxVisualRow; vr++) {
    const item = filteredGrid.value[vr];
    if (!item || item.row.isSummary) continue;

    const nextNum = parsed.num + incrementStep;
    const nextValStr = parsed.pad > 0 ? String(nextNum).padStart(parsed.pad, '0') : String(nextNum);
    const finalVal = parsed.prefix ? `${parsed.prefix}${nextValStr}` : (typeof baseRawVal === 'number' ? nextNum : nextValStr);

    const origIdx = item.originalIndex;
    localGrid.value[origIdx][colIndex] = finalVal;

    // Fórmulas dependientes y calculador de fila de la vista
    afterCellChange(localGrid.value[origIdx], colIndex);

    incrementStep++;
  }

  // Actualizar la selección para brindar retroalimentación visual al usuario
  selection.value.start = { r: startVisualR, c: colIndex };
  selection.value.end = { r: maxVisualRow, c: colIndex };
};

/**
 * Autoincrementa +1 desde la celda actualmente activa hasta la última fila de la tabla.
 */
const fillDownSeriesFromActiveCell = () => {
  if (activeCell.value.r === null || activeCell.value.c === null) return;
  fillDownSeries(activeCell.value.r, null, activeCell.value.c);
};

/**
 * Inicia el proceso de arrastre del cuadrito estilo Excel (Fill Handle).
 */
const startFillDrag = (e, visualR, colIndex) => {
  e.preventDefault();
  isFilling.value = true;
  fillStart.value = { r: visualR, c: colIndex };
  fillEnd.value = { r: visualR, c: colIndex };

  const onMouseMove = (moveEvent) => {
    if (!isFilling.value) return;
    const elem = document.elementFromPoint(moveEvent.clientX, moveEvent.clientY);
    const td = elem?.closest('td.cell');
    if (td && td.parentElement) {
      const rowIndex = Array.from(td.parentElement.parentElement.children).indexOf(td.parentElement);
      if (rowIndex >= fillStart.value.r) {
        fillEnd.value = { r: rowIndex, c: colIndex };
      }
    }
  };

  const onMouseUp = () => {
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
    if (isFilling.value && fillEnd.value.r > fillStart.value.r) {
      fillDownSeries(fillStart.value.r, fillEnd.value.r, fillStart.value.c);
    }
    isFilling.value = false;
    fillStart.value = { r: null, c: null };
    fillEnd.value = { r: null, c: null };
  };

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
};

/**
 * Evalúa si una celda visual dada es parte del rango actual que está siendo arrastrado para autollenar.
 */
const isFillTarget = (visualR, colIndex) => {
  if (!isFilling.value || fillStart.value.r === null || fillEnd.value.r === null) return false;
  if (colIndex !== fillStart.value.c) return false;
  return visualR > fillStart.value.r && visualR <= fillEnd.value.r;
};

const focusCell = (visualR, c) => {
  const table = document.querySelector('.excel-table tbody');
  const targetRow = table.children[visualR];
  if (targetRow) {
      const targetCell = targetRow.children[c + (isEditMode.value ? 1 : 0)]; // Ajuste de índice
      if (targetCell) {
          const select = targetCell.querySelector('select');
          if (select) select.focus();
          else targetCell.focus();
          setActive(visualR, c);
          selection.value.start = { r: visualR, c }; selection.value.end = { r: visualR, c };
      }
  }
};
const setActive = (r, c) => {
  if (activeCell.value.r !== r || activeCell.value.c !== c) {
    isTyping.value = false;
  }
  activeCell.value = { r, c };
};

// --- COPIAR / PEGAR ---
const handleCopy = (e) => {
  if (!selection.value.start || !selection.value.end) return;
  e.preventDefault();
  const minR = Math.min(selection.value.start.r, selection.value.end.r);
  const maxR = Math.max(selection.value.start.r, selection.value.end.r);
  const minC = Math.min(selection.value.start.c, selection.value.end.c);
  const maxC = Math.max(selection.value.start.c, selection.value.end.c);

  let textToCopy = "";
  for (let i = minR; i <= maxR; i++) {
    const item = filteredGrid.value[i];
    if (!item) continue;
    const rowData = [];
    for (let j = minC; j <= maxC; j++) {
      let val = item.row[j];
      if (isColumnSelect(j)) val = getOptionLabel(j, val);
      rowData.push(getCellValueStr(val));
    }
    textToCopy += rowData.join("\t") + (i < maxR ? "\n" : "");
  }
  if (navigator.clipboard) navigator.clipboard.writeText(textToCopy).catch(err => fallbackCopy(textToCopy));
  else fallbackCopy(textToCopy);
};
const fallbackCopy = (text) => {
    if (clipboardInput.value) { clipboardInput.value.value = text; clipboardInput.value.select(); document.execCommand('copy'); }
};
const handlePaste = (e, visualRowIndex, startCol) => {
  if (!isEditMode.value) { alert('Debes habilitar el modo edición para pegar datos.'); return; }
  const clipboardData = e.clipboardData || window.clipboardData;
  const pastedData = clipboardData ? clipboardData.getData('Text') : '';
  if (!pastedData) return;

  // Quitar saltos de línea residuales al final (común en Excel al copiar en Windows)
  const cleanData = pastedData.replace(/(\r\n|\n|\r)+$/, '');
  if (!cleanData) return;

  const rows = cleanData.split(/\r\n|\n|\r/);

  rows.forEach((rowStr, rOffset) => {
    const currentVisualRow = visualRowIndex + rOffset;
    let targetOriginalRow;

    if (currentVisualRow < filteredGrid.value.length) {
      // Si la fila visual existe, obtener su índice original real en localGrid
      targetOriginalRow = filteredGrid.value[currentVisualRow].originalIndex;
    } else {
      // Si el pegado excede las filas visibles actuales, crear una nueva fila al final
      const newRow = new Array(props.headers.length).fill('');
      localGrid.value.push(newRow);
      rowHeights.value.push(DEFAULT_ROW_HEIGHT);
      targetOriginalRow = localGrid.value.length - 1;
      viewOrder.value.push(targetOriginalRow); // la fila nueva se ve al final
    }

    // No sobreescribir filas de resumen si existen
    if (localGrid.value[targetOriginalRow]?.isSummary) return;

    const cells = rowStr.split('\t');
    const pastedCols = [];
    cells.forEach((cellData, cOffset) => {
      const targetCol = startCol + cOffset;
      // Las columnas calculadas no editables conservan su fórmula: el valor pegado se ignora.
      if (targetCol < props.headers.length && !isFormulaLocked(targetCol)) {
        let valToPaste = cellData.trim();
        if (isColumnSelect(targetCol)) {
          const options = getColumnOptions(targetCol);
          const match = options.find(opt =>
            String(opt.label).toLowerCase() === valToPaste.toLowerCase() ||
            String(opt.value).toLowerCase() === valToPaste.toLowerCase()
          );
          if (match) valToPaste = match.value;
        } else if (formulaInputs.value.has(targetCol)) {
          // Números de Excel con coma de miles y punto decimal: '1,035.5' -> '1035.5'.
          const normalized = normalizeNumberText(valToPaste);
          if (normalized !== null) valToPaste = normalized;
        }
        localGrid.value[targetOriginalRow][targetCol] = valToPaste;
        pastedCols.push(targetCol);
      }
    });

    // Se recalculan juntas las fórmulas afectadas por todas las columnas pegadas de la fila. Así un valor
    // pegado en una columna calculada editable (p. ej. Peso Prod.) se respeta y no lo pisa el cálculo
    // disparado por otra columna pegada (Tara, Peso Total).
    if (pastedCols.length) afterCellChange(localGrid.value[targetOriginalRow], pastedCols);
  });

  // Se desenfoca la celda para salir del modo escritura, sin que su blur copie el texto viejo del DOM.
  if (document.activeElement && typeof document.activeElement.blur === 'function') {
    skipBlurSync = true; // el evento blur se dispara de forma síncrona dentro de blur()
    document.activeElement.blur();
    skipBlurSync = false;
  }
  isTyping.value = false;
  // Las celdas se vuelven a dibujar desde el estado (lo pegado), aunque se hubiera escrito a mano antes.
  renderVersion.value++;
  // La selección muestra el bloque pegado, como en Excel.
  const lastRow = Math.min(visualRowIndex + rows.length - 1, filteredGrid.value.length - 1);
  const widest = Math.max(...rows.map(r => r.split('\t').length));
  selection.value = {
    start: { r: visualRowIndex, c: startCol },
    end: { r: lastRow, c: Math.min(startCol + widest - 1, props.headers.length - 1) }
  };
};

// --- REDIMENSIONAR ---
const startResize = (e, index, type) => {
    if (!isEditMode.value) return;
    resizing.active = true; resizing.type = type; resizing.index = index;
    if (type === 'col') { resizing.startPos = e.pageX; resizing.startSize = colWidths.value[index]; document.body.style.cursor = 'col-resize'; }
    else { resizing.startPos = e.pageY; resizing.startSize = rowHeights.value[index]; document.body.style.cursor = 'row-resize'; }
};
const handleResizeMove = (e) => {
    if (!resizing.active) return;
    if (resizing.type === 'col') colWidths.value[resizing.index] = Math.max(MIN_COL_WIDTH, resizing.startSize + (e.pageX - resizing.startPos));
    else rowHeights.value[resizing.index] = Math.max(20, resizing.startSize + (e.pageY - resizing.startPos));
};
const stopResize = () => {
    if (resizing.active) { resizing.active = false; resizing.type = null; resizing.index = null; document.body.style.cursor = ''; }
};

const addRow = () => {
  const newRow = new Array(props.headers.length).fill('');
  localGrid.value.push(newRow);
  rowHeights.value.push(DEFAULT_ROW_HEIGHT);
  viewOrder.value.push(localGrid.value.length - 1); // la fila nueva se ve al final
};

onMounted(() => { initGrid(); });

// Antes los listeners de window quedaban registrados al salir de la vista (fuga de memoria).
onBeforeUnmount(() => {
  window.removeEventListener('mousemove', handleResizeMove);
  window.removeEventListener('mouseup', stopResize);
  clearTimeout(searchDebounce);
});

defineExpose({ clearFilters });
</script>

<style scoped>
/* Estilos base */
.excel-container { padding: 20px; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); position: relative; display: flex; flex-direction: column; height: 85vh; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
.title-section { display: flex; align-items: center; gap: 15px; }
.title-wrapper { display: flex; flex-direction: column; align-items: flex-start; }
.title-section h2 { margin: 0; font-size: 1.2rem; }
.status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
.status-read { background-color: #e5e7eb; color: #374151; border: 1px solid #d1d5db; }
.status-edit { background-color: #dbeafe; color: #1e40af; border: 1px solid #93c5fd; }
.actions { display: flex; gap: 10px; align-items: center; }
.pagination-controls { display: flex; justify-content: center; align-items: center; gap: 15px; padding-top: 10px; border-top: 1px solid #eee; margin-top: 10px; flex-wrap: wrap;}
.page-info { font-size: 0.9rem; color: #555; font-weight: 500; }
.page-size-selector { padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.9rem; cursor: pointer; }
.table-wrapper { overflow: auto; border: 1px solid #ccc; flex-grow: 1; position: relative; background-color: #f9f9f9; }

.excel-table { border-collapse: separate; border-spacing: 0; table-layout: fixed; width: max-content; background-color: white; }
.excel-table th, .excel-table td { border-right: 1px solid #d1d5db; border-bottom: 1px solid #d1d5db; padding: 4px 8px; position: relative; box-sizing: border-box; overflow: hidden; white-space: nowrap; font-size: 14px; }
.excel-table th { background-color: #f3f4f6; font-weight: 600; text-align: center; user-select: none; position: sticky; top: 0; z-index: 20; border-top: 1px solid #d1d5db; height: auto; min-height: 30px; }
.header-content { display: flex; justify-content: space-between; align-items: center; width: 100%; height: 100%; }
.header-text { flex-grow: 1; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: pre-line; }
.filter-icon { cursor: pointer; font-size: 10px; padding: 2px 4px; margin-left: 4px; border-radius: 3px; color: #666; }
.filter-icon:hover { background-color: #e5e7eb; }
.filter-icon.active { color: #2563eb; font-weight: bold; }
.sort-indicator { font-size: 10px; color: #2563eb; margin-left: 2px; }
.sort-indicator.sort-default { color: #9ca3af; }
/* Celda de entrada de una fórmula con un valor que no es número (no se puede calcular) */
.cell.invalid-number { background-color: #fee2e2; color: #991b1b; }
/* Columnas calculadas por fórmula (p. ej. Peso Prod., % Sol) */
.cell.formula-cell { background-color: #f0f9ff; color: #0c4a6e; font-style: italic; }
.menu-status { padding: 6px 4px; color: #6b7280; font-size: 12px; }
.menu-error { color: #b91c1c; }
.row-header { background-color: #f3f4f6; width: 40px; min-width: 40px; text-align: center; font-weight: bold; color: #555; user-select: none; position: sticky; left: 0; z-index: 10; border-left: 1px solid #d1d5db; cursor: pointer; }
.row-header:hover { background-color: #e5e7eb; }
.header-selected { background-color: #cbd5e1 !important; color: #1e293b; border-right: 2px solid #3b82f6; }
.row-selected td { background-color: rgba(59, 130, 246, 0.05); }
.excel-table thead tr th:first-child { z-index: 30; left: 0; top: 0; }
.no-results { text-align: center; padding: 20px; color: #666; font-style: italic; }
.cell { outline: none; cursor: cell; background: white; }
.cell.read-only { cursor: default; color: #333; }
.cell:focus { border: 2px solid #3b82f6; z-index: 5; }
.cell.selected { background-color: rgba(59, 130, 246, 0.15); }
.cell.selected.active { background-color: white; border: 2px solid #3b82f6; }
.cell.active { overflow: visible !important; z-index: 20; }

/* Cuadro de arrastre estilo Excel (Fill Handle) */
.excel-fill-handle {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 8px;
  height: 8px;
  background-color: #2563eb;
  border: 1px solid #ffffff;
  cursor: crosshair;
  z-index: 30;
  box-sizing: border-box;
  display: block;
  user-select: none;
  -webkit-user-select: none;
  pointer-events: auto;
}

.excel-fill-handle:hover {
  background-color: #1d4ed8;
  transform: scale(1.25);
}

/* Resaltado visual mientras se arrastra el cuadro de autollenado */
.cell.fill-target {
  background-color: #eff6ff !important;
  border-left: 2px dashed #3b82f6 !important;
  border-right: 2px dashed #3b82f6 !important;
  border-bottom: 2px dashed #3b82f6 !important;
}

/* Botón púrpura para acciones de autoincremento estilo Excel */
.btn-purple {
  background-color: #7c3aed;
  color: #ffffff;
  border: 1px solid #6d28d9;
}

.btn-purple:not(:disabled):hover {
  background-color: #6d28d9;
}
.cell-select { width: 100%; height: 100%; border: none; background: transparent; outline: none; cursor: pointer; }
.resizer { position: absolute; background: transparent; z-index: 25; }
.resizer:hover, .resizer:active { background: #3b82f6; }
.col-resizer { top: 0; right: 0; width: 5px; height: 100%; cursor: col-resize; }
.row-resizer { bottom: 0; left: 0; width: 100%; height: 5px; cursor: row-resize; }
.clipboard-helper { position: absolute; left: -9999px; top: 0; }
.filter-menu { position: absolute; background: white; border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 4px; width: 240px; z-index: 1000; display: flex; flex-direction: column; font-size: 13px; color: #333; }
.menu-actions { padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.menu-btn { text-align: left; background: none; border: none; padding: 6px; cursor: pointer; border-radius: 3px; }
.menu-btn:hover { background-color: #f3f4f6; }
.menu-divider { height: 1px; background-color: #eee; margin: 0; }
.menu-search { padding: 8px; border-bottom: 1px solid #eee; }
.menu-search-input { width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }
.menu-list { max-height: 200px; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.menu-item { display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }
.menu-item.bold { font-weight: 600; border-bottom: 1px solid #f0f0f0; padding-bottom: 4px; margin-bottom: 4px; }
.menu-footer { padding: 8px; border-top: 1px solid #eee; display: flex; justify-content: flex-end; gap: 8px; background-color: #f9fafb; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); width: 400px; text-align: center; }
.modal-actions { margin-top: 20px; display: flex; justify-content: center; gap: 15px; }


.summary-cell {
  background-color: #f8f9fa !important;
  font-weight: 600;
  color: #1f2937;
}

.group-header-cell {
  background-color: #e5e7eb !important;
  color: #374151;
  font-size: 14px;
}

.overtime-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  border-top: 8px solid #dc2626; /* Triángulo rojo en la esquina superior izquierda */
  border-right: 8px solid transparent;
  z-index: 10;
}

/* Ocultar barra superior, botones y modales al imprimir */
@media print {
  .toolbar,
  .modal-overlay,
  .filter-menu,
  .filter-icon,
  .resizer,
  .pagination-controls {
    display: none !important;
  }
  .excel-container {
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    background: transparent !important;
    height: auto !important;
  }
  .table-wrapper {
    overflow: visible !important;
    border: none !important;
  }
  .excel-table {
    width: 100% !important;
    table-layout: auto !important;
  }
  .excel-table th,
  .excel-table td {
    min-width: unset !important;
    font-size: 7.5pt !important;
    padding: 2px 3px !important;
  }
  .excel-table th {
    font-size: 7pt !important;
    line-height: 1.15 !important;
    font-weight: bold !important;
  }
  .header-content {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
  }
  .header-text {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-align: center !important;
    font-size: inherit !important;
  }
}
</style>
