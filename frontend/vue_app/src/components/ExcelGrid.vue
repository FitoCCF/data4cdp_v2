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

          <!-- Botón para guardar todos los cambios -->
          <button class="btn btn-green btn-sm" @click="promptSave">Guardar Cambios</button>
        </template>
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
          <tr v-if="headerGroups && headerGroups.length > 0">
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
          <tr>
            <!-- Encabezado de la columna de índices (SOLO VISIBLE EN MODO EDICIÓN) -->
            <th v-if="isEditMode" class="row-header">#</th>

            <!-- Encabezados de columnas dinámicos -->
            <th
              v-for="(col, index) in headers"
              :key="index"
              class="col-header"
              :style="{ width: colWidths[index] + 'px', minWidth: colWidths[index] + 'px' }"
            >
              <div class="header-content">
                <!-- Texto del encabezado -->
                <span class="header-text">{{ col }}</span>
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
            :key="item.originalIndex"
            :style="{ height: rowHeights[item.originalIndex] + 'px' }"
            :class="{ 'row-selected': selectedRowIndices.has(item.originalIndex) }"
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
            <td
              v-for="(cell, cIndex) in item.row"
              :key="cIndex"
              class="cell"
              :class="{
                'active': activeCell.r === visualIndex && activeCell.c === cIndex,
                'selected': isSelected(visualIndex, cIndex),
                'read-only': !isEditMode || item.row.isSummary,
                'summary-cell': item.row.isSummary
              }"
              @mousedown="startSelection(visualIndex, cIndex)"
              @mouseover="updateSelection(visualIndex, cIndex)"
              @focus="setActive(visualIndex, cIndex)"
              @paste.prevent="handlePaste($event, item.originalIndex, cIndex)"
              @keydown="handleKeydown($event, visualIndex, cIndex)"
              @copy="handleCopy"

              :contenteditable="isEditMode && !isColumnSelect(cIndex) && !item.row.isSummary"
              @blur="!isColumnSelect(cIndex) && updateCell($event, item.originalIndex, cIndex)"
            >
              <!-- Renderizado Condicional: Select o Texto -->
              <template v-if="isColumnSelect(cIndex) && !item.row.isSummary">
                <select
                  v-if="isEditMode"
                  :value="cell"
                  @change="updateCellSelect($event, item.originalIndex, cIndex)"
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
                {{ cell }}
              </template>
            </td>
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
      </div>
      <div class="menu-divider"></div>
      <div class="menu-search">
        <input type="text" v-model="menuSearchText" placeholder="Buscar..." class="menu-search-input">
      </div>
      <div class="menu-list">
        <label class="menu-item bold">
          <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll"> (Seleccionar todo)
        </label>
        <label v-for="val in filteredUniqueValues" :key="val" class="menu-item">
          <input type="checkbox" :checked="tempSelectedValues.has(String(val))" @change="toggleValue(String(val))">
          {{ getFilterLabel(openMenuIndex, val) }}
        </label>
      </div>
      <div class="menu-footer">
        <button class="btn btn-sm btn-gray" @click="closeFilterMenu">Cancelar</button>
        <button class="btn btn-sm btn-blue" @click="applyFilter">Aceptar</button>
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
import { ref, onMounted, reactive, watch, computed } from 'vue';

// --- PROPS ---
const props = defineProps({
  title: { type: String, default: 'Tabla de Datos' },
  headers: { type: Array, required: true, default: () => [] },
  headerGroups: { type: Array, default: () => [] },
  data: { type: Array, required: true, default: () => [] },
  columnsConfig: { type: Object, default: () => ({}) },
  // Nuevas props para Paginación y Filtrado backend
  currentPage: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
  totalItems: { type: Number, default: 0 },
  pageSize: { type: Number, default: 25 },
  serverSideFiltering: { type: Boolean, default: false }, // Indica si el filtro lo hace el backend
  filterData: { type: Array, default: () => [] } // Datos completos para el menú de filtros
});

// --- EMITS ---
const emit = defineEmits(['save', 'delete', 'pageChange', 'pageSizeChange', 'filterChange', 'sortChange']);

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

const resizing = reactive({ active: false, type: null, index: null, startPos: 0, startSize: 0 });

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

const filteredGrid = computed(() => {
    let result = localGrid.value.map((row, index) => ({ row, originalIndex: index }));

    // Si el filtrado u ordenamiento lo hace el backend, simplemente retornamos los datos tal cual
    if (props.serverSideFiltering) {
        return result;
    }

    // --- FILTRADO LOCAL (Solo aplica si no hay serverSideFiltering) ---
    const activeCols = Object.keys(activeFilters.value);
    if (activeCols.length > 0) {
        result = result.filter(item => {
            if (item.row.isSummary) return true; // Mantener las filas de resumen siempre visibles
            return activeCols.every(colIndex => {
                const allowedValues = activeFilters.value[colIndex];
                if (!allowedValues) return true;
                const cellValue = String(item.row[colIndex] || '');
                return allowedValues.has(cellValue);
            });
        });
    }

    if (sortState.value.colIndex !== null) {
        const { colIndex, direction } = sortState.value;
        const isSelect = isColumnSelect(colIndex);

        const dataRows = result.filter(item => !item.row.isSummary);
        const summaryRows = result.filter(item => item.row.isSummary);

        dataRows.sort((a, b) => {
            let valA = a.row[colIndex];
            let valB = b.row[colIndex];

            if (isSelect) {
                valA = getOptionLabel(colIndex, valA);
                valB = getOptionLabel(colIndex, valB);
            }

            valA = String(valA || '').toLowerCase();
            valB = String(valB || '').toLowerCase();

            const numA = parseFloat(valA);
            const numB = parseFloat(valB);

            if (!isNaN(numA) && !isNaN(numB)) {
                return direction === 'asc' ? numA - numB : numB - numA;
            }

            if (valA < valB) return direction === 'asc' ? -1 : 1;
            if (valA > valB) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        
        result = [...dataRows, ...summaryRows]; // Reensamblar dejando el resumen al final
    }

    return result;
});

// --- MENÚ FILTRO ---

const currentUniqueValues = computed(() => {
    if (openMenuIndex.value === null) return [];
    
    // Si tenemos filterData y el filtrado es de servidor, usamos filterData para extraer opciones
    const sourceData = (props.serverSideFiltering && props.filterData && props.filterData.length > 0) 
                        ? props.filterData 
                        : localGrid.value.filter(row => !row.isSummary); // Excluir resumen de los valores únicos
    
    const values = new Set(sourceData.map(row => String(row[openMenuIndex.value] || '')));
    return Array.from(values).sort();
});

const filteredUniqueValues = computed(() => {
    if (!menuSearchText.value) return currentUniqueValues.value;
    const colIndex = openMenuIndex.value;
    return currentUniqueValues.value.filter(v => {
        const label = String(getFilterLabel(colIndex, v)).toLowerCase();
        return label.includes(menuSearchText.value.toLowerCase());
    });
});

const isAllSelected = computed(() => {
    return filteredUniqueValues.value.every(val => tempSelectedValues.value.has(val));
});

const toggleFilterMenu = (index, event) => {
    if (openMenuIndex.value === index) { closeFilterMenu(); return; }
    openMenuIndex.value = index;
    menuSearchText.value = '';

    const th = event.target.closest('th');
    const rect = th.getBoundingClientRect();
    const containerRect = containerRef.value.getBoundingClientRect();

    menuPosition.value = {
        top: rect.bottom - containerRect.top,
        left: rect.left - containerRect.left
    };

    if (activeFilters.value[index]) {
        tempSelectedValues.value = new Set(activeFilters.value[index]);
    } else {
        const sourceData = (props.serverSideFiltering && props.filterData && props.filterData.length > 0) 
                            ? props.filterData 
                            : localGrid.value.filter(row => !row.isSummary);
        tempSelectedValues.value = new Set(sourceData.map(row => String(row[index] || '')));
    }
};

const closeFilterMenu = () => { openMenuIndex.value = null; };
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

const applyFilter = () => {
    const index = openMenuIndex.value;
    
    const sourceData = (props.serverSideFiltering && props.filterData && props.filterData.length > 0) 
                        ? props.filterData 
                        : localGrid.value.filter(row => !row.isSummary);
    const allValues = new Set(sourceData.map(row => String(row[index] || '')));
    
    // Preparar objeto de filtro que se enviará arriba

    let newActiveFilters = { ...activeFilters.value };

    if (tempSelectedValues.value.size === allValues.size) {
        delete newActiveFilters[index];
    } else {
        newActiveFilters[index] = new Set(tempSelectedValues.value);
    }

    activeFilters.value = newActiveFilters;

    // Si es filtrado tipo backend, emitimos el evento con los nuevos filtros (pasamos arrays nativos)
    if (props.serverSideFiltering) {
        const filtersToSend = {};
        for (const key in activeFilters.value) {
           filtersToSend[key] = Array.from(activeFilters.value[key]);
        }
        emit('filterChange', filtersToSend);
    }

    closeFilterMenu();
};

const sortColumn = (colIndex, direction) => {
    sortState.value = { colIndex, direction };
    
    // Si es paginación de backend, el backend o vista padre debe ordenarlo
    if (props.serverSideFiltering) {
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
            let cellText = String(row[colIndex] || '');
            if (isColumnSelect(colIndex)) {
                cellText = String(getOptionLabel(colIndex, row[colIndex]) || '');
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
      if (row.isSummary) Object.defineProperty(newRow, 'isSummary', { value: true, enumerable: false, writable: true });
      return newRow;
    });
  } else {
    localGrid.value = [];
  }
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
      if (row.isSummary) Object.defineProperty(newRow, 'isSummary', { value: true, enumerable: false, writable: true });
      return newRow;
    });
    rowHeights.value = localGrid.value.map(() => DEFAULT_ROW_HEIGHT);
    if (colWidths.value.length === 0 || colWidths.value.length !== props.headers.length) {
        calculateAutoWidths();
    }
  }
}, { deep: true });

// --- EDICIÓN Y EVENTOS ---

const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value;
  selection.value = { start: null, end: null };
  activeCell.value = { r: null, c: null };
  selectedRowIndices.value.clear();
};

const promptSave = () => { showSaveModal.value = true; };
const executeSave = () => { emit('save', localGrid.value); showSaveModal.value = false; };

const updateCell = (e, originalRowIndex, c) => {
  if (isEditMode.value) localGrid.value[originalRowIndex][c] = e.target.innerText;
  else e.target.innerText = localGrid.value[originalRowIndex][c];
};

const updateCellSelect = (e, originalRowIndex, c) => {
    localGrid.value[originalRowIndex][c] = e.target.value;
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
  const maxR = filteredGrid.value.length - 1;
  const maxC = props.headers.length - 1;
  if (e.key === 'ArrowDown') { e.preventDefault(); if (visualR < maxR) focusCell(visualR + 1, c); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); if (visualR > 0) focusCell(visualR - 1, c); }
  else if (e.key === 'ArrowRight') { if(!e.shiftKey && c < maxC) focusCell(visualR, c + 1); }
  else if (e.key === 'ArrowLeft') { if(!e.shiftKey && c > 0) focusCell(visualR, c - 1); }
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
const setActive = (r, c) => { activeCell.value = { r, c }; };

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
      rowData.push(val);
    }
    textToCopy += rowData.join("\t") + (i < maxR ? "\n" : "");
  }
  if (navigator.clipboard) navigator.clipboard.writeText(textToCopy).catch(err => fallbackCopy(textToCopy));
  else fallbackCopy(textToCopy);
};
const fallbackCopy = (text) => {
    if (clipboardInput.value) { clipboardInput.value.value = text; clipboardInput.value.select(); document.execCommand('copy'); }
};
const handlePaste = (e, originalRowIndex, startCol) => {
  if (!isEditMode.value) { alert('Debes habilitar el modo edición para pegar datos.'); return; }
  const clipboardData = e.clipboardData || window.clipboardData;
  const pastedData = clipboardData.getData('Text');
  if (!pastedData) return;
  const rows = pastedData.split(/\r\n|\n|\r/).filter(row => row.length > 0 || row === "");
  if (rows.length > 0 && rows[rows.length - 1] === "") rows.pop();
  rows.forEach((rowStr, rOffset) => {
    const cells = rowStr.split('\t');
    const targetRow = originalRowIndex + rOffset;
    if (targetRow >= localGrid.value.length) {
      const newRow = new Array(props.headers.length).fill('');
      localGrid.value.push(newRow);
      rowHeights.value.push(DEFAULT_ROW_HEIGHT);
    }
    cells.forEach((cellData, cOffset) => {
      const targetCol = startCol + cOffset;
      if (targetCol < props.headers.length) {
          let valToPaste = cellData.trim();
          if (isColumnSelect(targetCol)) {
              const options = getColumnOptions(targetCol);
              const match = options.find(opt => opt.label.toLowerCase() === valToPaste.toLowerCase());
              if (match) valToPaste = match.value;
          }
          localGrid.value[targetRow][targetCol] = valToPaste;
      }
    });
  });
  setTimeout(() => { const table = document.querySelector('.excel-table tbody'); }, 0);
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
};

onMounted(() => { initGrid(); });
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
.excel-table th { background-color: #f3f4f6; font-weight: 600; text-align: center; user-select: none; position: sticky; top: 0; z-index: 20; border-top: 1px solid #d1d5db; height: 30px; }
.header-content { display: flex; justify-content: space-between; align-items: center; width: 100%; height: 100%; }
.header-text { flex-grow: 1; text-align: center; overflow: hidden; text-overflow: ellipsis; }
.filter-icon { cursor: pointer; font-size: 10px; padding: 2px 4px; margin-left: 4px; border-radius: 3px; color: #666; }
.filter-icon:hover { background-color: #e5e7eb; }
.filter-icon.active { color: #2563eb; font-weight: bold; }
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
.cell-select { width: 100%; height: 100%; border: none; background: transparent; outline: none; cursor: pointer; }
.resizer { position: absolute; background: transparent; z-index: 25; }
.resizer:hover, .resizer:active { background: #3b82f6; }
.col-resizer { top: 0; right: 0; width: 5px; height: 100%; cursor: col-resize; }
.row-resizer { bottom: 0; left: 0; width: 100%; height: 5px; cursor: row-resize; }
.clipboard-helper { position: absolute; left: -9999px; top: 0; }
.filter-menu { position: absolute; background: white; border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-radius: 4px; width: 220px; z-index: 1000; display: flex; flex-direction: column; font-size: 13px; color: #333; }
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
</style>
