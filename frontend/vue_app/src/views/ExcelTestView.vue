<template>
  <div class="excel-container">
    <!--
      BARRA DE HERRAMIENTAS
      Contiene los controles principales para manipular la tabla.
    -->
    <div class="toolbar">
      <div class="title-section">
        <h2>Hoja de Cálculo (Prueba)</h2>
        <!-- Indicador visual del estado actual (Lectura o Edición) -->
        <span class="status-badge" :class="isEditMode ? 'status-edit' : 'status-read'">
          {{ isEditMode ? 'MODO EDICIÓN' : 'SOLO LECTURA' }}
        </span>
      </div>

      <div class="actions">
        <!-- Botón para alternar entre modo lectura y escritura -->
        <button
          class="btn btn-sm"
          :class="isEditMode ? 'btn-gray' : 'btn-blue'"
          @click="toggleEditMode"
        >
          {{ isEditMode ? '🔒 Bloquear Edición' : '✏️ Habilitar Edición' }}
        </button>

        <!-- Botones de acción (Solo visibles en modo edición) -->
        <template v-if="isEditMode">
          <button class="btn btn-blue btn-sm" @click="addRow">➕ Fila</button>
          <button class="btn btn-blue btn-sm" @click="addCol">➕ Columna</button>
          <button class="btn btn-green btn-sm" @click="promptSave">💾 Guardar Cambios</button>
        </template>

        <!-- Botón de exportación (Siempre visible para depuración) -->
        <button v-else class="btn btn-green btn-sm" @click="exportData">
          👁️ Ver JSON
        </button>
      </div>
    </div>

    <!-- Instrucciones de uso para el usuario -->
    <div class="instructions">
      <small v-if="isEditMode">💡 <b>Modo Edición:</b> Puedes escribir, pegar (Ctrl+V) y modificar estructura.</small>
      <small v-else>💡 <b>Modo Lectura:</b> Puedes seleccionar y copiar (Ctrl+C), pero no modificar datos.</small>
    </div>

    <!--
      CONTENEDOR DE LA TABLA
      Maneja eventos de ratón globales para la selección de celdas.
    -->
    <div
      class="table-wrapper"
      @mouseup="endSelection"
      @mouseleave="endSelection"
    >
      <table class="excel-table" ref="tableRef">
        <thead>
          <tr>
            <!-- Esquina superior izquierda (vacía o índice) -->
            <th class="row-header">#</th>

            <!--
              CABECERAS DE COLUMNA (A, B, C...)
              Incluye el redimensionador de ancho.
            -->
            <th
              v-for="(col, index) in headers"
              :key="index"
              class="col-header"
              :style="{ width: colWidths[index] + 'px', minWidth: colWidths[index] + 'px' }"
            >
              {{ col }}
              <!-- Elemento para redimensionar columna (solo activo en edición, pero visible para consistencia) -->
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
          <!--
            FILAS DE DATOS
          -->
          <tr
            v-for="(row, rIndex) in grid"
            :key="rIndex"
            :style="{ height: rowHeights[rIndex] + 'px' }"
          >
            <!-- Cabecera de Fila (1, 2, 3...) con redimensionador de alto -->
            <td class="row-header">
                {{ rIndex + 1 }}
                <div
                  v-if="isEditMode"
                  class="resizer row-resizer"
                  @mousedown.stop="startResize($event, rIndex, 'row')"
                  title="Arrastrar para cambiar alto"
                ></div>
            </td>

            <!--
              CELDAS DE DATOS
              contenteditable: Determina si el usuario puede escribir directamente.
            -->
            <td
              v-for="(cell, cIndex) in row"
              :key="cIndex"
              :contenteditable="isEditMode"
              class="cell"
              :class="{
                'active': activeCell.r === rIndex && activeCell.c === cIndex,
                'selected': isSelected(rIndex, cIndex),
                'read-only': !isEditMode
              }"
              @mousedown="startSelection(rIndex, cIndex)"
              @mouseover="updateSelection(rIndex, cIndex)"
              @focus="setActive(rIndex, cIndex)"
              @paste.prevent="handlePaste($event, rIndex, cIndex)"
              @keydown="handleKeydown($event, rIndex, cIndex)"
              @blur="updateCell($event, rIndex, cIndex)"
              @copy="handleCopy"
            >
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Input oculto auxiliar para facilitar el copiado al portapapeles del sistema -->
    <textarea ref="clipboardInput" class="clipboard-helper"></textarea>

    <!--
      MODAL DE CONFIRMACIÓN DE GUARDADO
      Aparece cuando el usuario intenta guardar cambios.
    -->
    <div v-if="showSaveModal" class="modal-overlay">
      <div class="modal-content">
        <h3>¿Guardar cambios?</h3>
        <p>Se actualizarán los datos de la tabla. Esta acción no se puede deshacer.</p>
        <div class="modal-actions">
          <button class="btn btn-gray" @click="showSaveModal = false">Cancelar</button>
          <button class="btn btn-green" @click="executeSave">Sí, Guardar</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';

// ==========================================
// CONFIGURACIÓN INICIAL Y CONSTANTES
// ==========================================
const INITIAL_ROWS = 20;       // Número inicial de filas
const INITIAL_COLS = 10;       // Número inicial de columnas
const DEFAULT_COL_WIDTH = 100; // Ancho por defecto en píxeles
const DEFAULT_ROW_HEIGHT = 25; // Alto por defecto en píxeles

// ==========================================
// ESTADO REACTIVO (VARIABLES)
// ==========================================

// Datos principales de la tabla (Matriz bidimensional)
const grid = ref([]);

// Cabeceras de columna (A, B, C...)
const headers = ref([]);

// Dimensiones visuales
const colWidths = ref([]);
const rowHeights = ref([]);

// Estado de la interfaz
const isEditMode = ref(false);      // Controla si la tabla es editable
const showSaveModal = ref(false);   // Controla la visibilidad del modal de guardar

// Control de selección y foco
const activeCell = ref({ r: null, c: null }); // Celda que tiene el foco actual
const selection = ref({ start: null, end: null }); // Rango de selección
const isSelecting = ref(false); // Bandera para saber si se está arrastrando el mouse

// Referencias al DOM
const tableRef = ref(null);
const clipboardInput = ref(null);

// Estado para la lógica de redimensionamiento (Resizing)
const resizing = reactive({
    active: false, // Si se está redimensionando actualmente
    type: null,    // 'col' (columna) o 'row' (fila)
    index: null,   // Índice de la fila/columna siendo modificada
    startPos: 0,   // Posición inicial del mouse (X o Y)
    startSize: 0   // Tamaño inicial antes de mover
});

// ==========================================
// FUNCIONES DE UTILIDAD
// ==========================================

/**
 * Genera letras de columna tipo Excel (0 -> A, 25 -> Z, 26 -> AA)
 * @param {number} num - Índice numérico de la columna
 * @returns {string} Letra correspondiente
 */
const getLetter = (num) => {
  let letter = '';
  while (num >= 0) {
    letter = String.fromCharCode(num % 26 + 65) + letter;
    num = Math.floor(num / 26) - 1;
  }
  return letter;
};

/**
 * Inicializa la cuadrícula con filas y columnas vacías
 */
const initGrid = () => {
  // Crear columnas
  for (let i = 0; i < INITIAL_COLS; i++) {
    headers.value.push(getLetter(i));
    colWidths.value.push(DEFAULT_COL_WIDTH);
  }
  // Crear filas
  for (let i = 0; i < INITIAL_ROWS; i++) {
    const row = new Array(INITIAL_COLS).fill('');
    grid.value.push(row);
    rowHeights.value.push(DEFAULT_ROW_HEIGHT);
  }

  // Agregar listeners globales para el redimensionamiento (para que funcione aunque el mouse salga de la tabla)
  window.addEventListener('mousemove', handleResizeMove);
  window.addEventListener('mouseup', stopResize);
};

// ==========================================
// LÓGICA DE MODOS Y GUARDADO
// ==========================================

/**
 * Alterna entre modo edición y modo lectura
 */
const toggleEditMode = () => {
  isEditMode.value = !isEditMode.value;
  // Limpiar selección al cambiar de modo para evitar confusiones visuales
  selection.value = { start: null, end: null };
  activeCell.value = { r: null, c: null };
};

/**
 * Abre el modal de confirmación antes de guardar
 */
const promptSave = () => {
  showSaveModal.value = true;
};

/**
 * Ejecuta la lógica de guardado (Simulación)
 */
const executeSave = () => {
  // Aquí iría la llamada a la API (Backend)
  console.log('Guardando datos en el servidor...', grid.value);

  // Cerrar modal
  showSaveModal.value = false;

  // Opcional: Salir del modo edición tras guardar
  // isEditMode.value = false;

  alert('¡Cambios guardados correctamente! (Revisa la consola)');
};

/**
 * Exporta datos a consola (para depuración en modo lectura)
 */
const exportData = () => {
  console.log('Datos actuales:', grid.value);
  alert('Datos exportados a la consola (F12)');
};

// ==========================================
// LÓGICA DE SELECCIÓN DE CELDAS
// ==========================================

const startSelection = (r, c) => {
  isSelecting.value = true;
  selection.value.start = { r, c };
  selection.value.end = { r, c };
  activeCell.value = { r, c };
};

const updateSelection = (r, c) => {
  if (isSelecting.value) {
    selection.value.end = { r, c };
  }
};

const endSelection = () => {
  isSelecting.value = false;
};

/**
 * Determina si una celda específica está dentro del rango seleccionado
 */
const isSelected = (r, c) => {
  if (!selection.value.start || !selection.value.end) return false;

  // Calcular límites del rectángulo de selección
  const minR = Math.min(selection.value.start.r, selection.value.end.r);
  const maxR = Math.max(selection.value.start.r, selection.value.end.r);
  const minC = Math.min(selection.value.start.c, selection.value.end.c);
  const maxC = Math.max(selection.value.start.c, selection.value.end.c);

  return r >= minR && r <= maxR && c >= minC && c <= maxC;
};

// ==========================================
// LÓGICA DE COPIAR Y PEGAR (CLIPBOARD)
// ==========================================

/**
 * Maneja el evento de copiar (Ctrl+C)
 * Genera un string separado por tabulaciones (TSV) compatible con Excel
 */
const handleCopy = (e) => {
  if (!selection.value.start || !selection.value.end) return;

  // Prevenir comportamiento por defecto para manejarlo manualmente
  e.preventDefault();

  const minR = Math.min(selection.value.start.r, selection.value.end.r);
  const maxR = Math.max(selection.value.start.r, selection.value.end.r);
  const minC = Math.min(selection.value.start.c, selection.value.end.c);
  const maxC = Math.max(selection.value.start.c, selection.value.end.c);

  let textToCopy = "";

  // Construir el string TSV
  for (let i = minR; i <= maxR; i++) {
    const rowData = [];
    for (let j = minC; j <= maxC; j++) {
      rowData.push(grid.value[i][j]);
    }
    textToCopy += rowData.join("\t") + (i < maxR ? "\n" : "");
  }

  // Intentar usar API moderna del portapapeles
  if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
          console.log('Copiado al portapapeles');
      }).catch(err => {
          console.error('Error al copiar: ', err);
          fallbackCopy(textToCopy);
      });
  } else {
      fallbackCopy(textToCopy);
  }
};

/**
 * Método alternativo de copiado para navegadores antiguos o contextos inseguros
 */
const fallbackCopy = (text) => {
    if (clipboardInput.value) {
        clipboardInput.value.value = text;
        clipboardInput.value.select();
        document.execCommand('copy');
    }
};

/**
 * Maneja el evento de pegar (Ctrl+V)
 * Parsea el texto del portapapeles y rellena las celdas
 */
const handlePaste = (e, startRow, startCol) => {
  // IMPORTANTE: Solo permitir pegar si estamos en modo edición
  if (!isEditMode.value) {
      alert('Debes habilitar el modo edición para pegar datos.');
      return;
  }

  const clipboardData = e.clipboardData || window.clipboardData;
  const pastedData = clipboardData.getData('Text');

  if (!pastedData) return;

  // Dividir por filas
  const rows = pastedData.split(/\r\n|\n|\r/).filter(row => row.length > 0 || row === "");
  if (rows.length > 0 && rows[rows.length - 1] === "") rows.pop(); // Limpiar última línea vacía si existe

  rows.forEach((rowStr, rOffset) => {
    const cells = rowStr.split('\t'); // Dividir por columnas (tabulaciones)
    const targetRow = startRow + rOffset;

    // Crear nueva fila si es necesario
    if (targetRow >= grid.value.length) {
      const newRow = new Array(headers.value.length).fill('');
      grid.value.push(newRow);
      rowHeights.value.push(DEFAULT_ROW_HEIGHT);
    }

    cells.forEach((cellData, cOffset) => {
      const targetCol = startCol + cOffset;

      // Crear nueva columna si es necesario
      if (targetCol >= headers.value.length) {
        addCol();
      }

      // Actualizar el modelo de datos
      grid.value[targetRow][targetCol] = cellData.trim();

      // Actualizar el DOM visualmente (necesario para contenteditable)
      setTimeout(() => {
         const table = document.querySelector('.excel-table tbody');
         if(table && table.children[targetRow] && table.children[targetRow].children[targetCol + 1]) {
             table.children[targetRow].children[targetCol + 1].innerText = cellData.trim();
         }
      }, 0);
    });
  });
};

// ==========================================
// LÓGICA DE REDIMENSIONAMIENTO (RESIZE)
// ==========================================

const startResize = (e, index, type) => {
    if (!isEditMode.value) return; // Solo permitir resize en modo edición

    resizing.active = true;
    resizing.type = type;
    resizing.index = index;

    if (type === 'col') {
        resizing.startPos = e.pageX;
        resizing.startSize = colWidths.value[index];
        document.body.style.cursor = 'col-resize';
    } else {
        resizing.startPos = e.pageY;
        resizing.startSize = rowHeights.value[index];
        document.body.style.cursor = 'row-resize';
    }
};

const handleResizeMove = (e) => {
    if (!resizing.active) return;

    if (resizing.type === 'col') {
        const diff = e.pageX - resizing.startPos;
        const newWidth = Math.max(30, resizing.startSize + diff); // Mínimo 30px
        colWidths.value[resizing.index] = newWidth;
    } else if (resizing.type === 'row') {
        const diff = e.pageY - resizing.startPos;
        const newHeight = Math.max(20, resizing.startSize + diff); // Mínimo 20px
        rowHeights.value[resizing.index] = newHeight;
    }
};

const stopResize = () => {
    if (resizing.active) {
        resizing.active = false;
        resizing.type = null;
        resizing.index = null;
        document.body.style.cursor = '';
    }
};

// ==========================================
// NAVEGACIÓN Y EDICIÓN DE CELDAS
// ==========================================

const handleKeydown = (e, r, c) => {
  // Permitir atajos nativos (Ctrl+C, Ctrl+V)
  if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'v')) return;

  const maxR = grid.value.length - 1;
  const maxC = headers.value.length - 1;

  // Navegación con flechas
  if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (r < maxR) focusCell(r + 1, c);
  }
  else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (r > 0) focusCell(r - 1, c);
  }
  else if (e.key === 'ArrowRight') {
      if(!e.shiftKey) { // Si shift está presionado, dejamos que el navegador seleccione texto
          if (c < maxC) focusCell(r, c + 1);
      }
  }
  else if (e.key === 'ArrowLeft') {
      if(!e.shiftKey) {
          if (c > 0) focusCell(r, c - 1);
      }
  }
};

const focusCell = (r, c) => {
  const table = document.querySelector('.excel-table tbody');
  // +1 porque la primera columna es el índice de fila
  const target = table.children[r].children[c + 1];
  if (target) {
      target.focus();
      setActive(r, c);
      // Al mover con teclado, la selección se resetea a la celda única
      selection.value.start = { r, c };
      selection.value.end = { r, c };
  }
};

const setActive = (r, c) => {
  activeCell.value = { r, c };
};

const updateCell = (e, r, c) => {
  // Solo actualizar si estamos en modo edición
  if (isEditMode.value) {
      grid.value[r][c] = e.target.innerText;
  } else {
      // Si por alguna razón se editó en modo lectura (hack), revertir visualmente
      e.target.innerText = grid.value[r][c];
  }
};

const addRow = () => {
  const newRow = new Array(headers.value.length).fill('');
  grid.value.push(newRow);
  rowHeights.value.push(DEFAULT_ROW_HEIGHT);
};

const addCol = () => {
  const newIndex = headers.value.length;
  headers.value.push(getLetter(newIndex));
  colWidths.value.push(DEFAULT_COL_WIDTH);
  grid.value.forEach(row => row.push(''));
};

// Inicializar al montar el componente
onMounted(() => {
  initGrid();
});
</script>

<style scoped>
/* Contenedor Principal */
.excel-container {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: relative;
  display: flex;
  flex-direction: column;
  height: 85vh; /* Ocupar casi toda la altura disponible */
}

/* Barra de Herramientas */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-section h2 {
  margin: 0;
  font-size: 1.2rem;
}

/* Badge de Estado */
.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
}

.status-read {
  background-color: #e5e7eb;
  color: #374151;
  border: 1px solid #d1d5db;
}

.status-edit {
  background-color: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}

.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.instructions {
  margin-bottom: 10px;
  color: #666;
  font-size: 0.85rem;
}

/* Wrapper de la Tabla (Scroll) */
.table-wrapper {
  overflow: auto;
  border: 1px solid #ccc;
  flex-grow: 1; /* Ocupar espacio restante */
  position: relative;
  background-color: #f9f9f9; /* Fondo para áreas vacías */
}

/* Tabla */
.excel-table {
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
  width: max-content;
  background-color: white;
}

.excel-table th, .excel-table td {
  border-right: 1px solid #d1d5db;
  border-bottom: 1px solid #d1d5db;
  padding: 4px 8px;
  position: relative;
  box-sizing: border-box;
  overflow: hidden;
  white-space: nowrap;
  font-size: 14px;
}

/* Cabeceras */
.excel-table th {
  background-color: #f3f4f6;
  font-weight: 600;
  text-align: center;
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 20;
  border-top: 1px solid #d1d5db;
  height: 30px;
}

.row-header {
  background-color: #f3f4f6;
  width: 40px;
  min-width: 40px;
  text-align: center;
  font-weight: bold;
  color: #555;
  user-select: none;
  position: sticky;
  left: 0;
  z-index: 10;
  border-left: 1px solid #d1d5db;
}

/* Intersección superior izquierda */
.excel-table thead tr th:first-child {
    z-index: 30;
    left: 0;
    top: 0;
}

/* Celdas */
.cell {
  outline: none;
  cursor: cell;
  background: white;
}

/* Estilo cuando la celda es de solo lectura */
.cell.read-only {
  cursor: default;
  color: #333;
}

/* Foco en celda */
.cell:focus {
  border: 2px solid #3b82f6;
  z-index: 5;
}

/* Selección de rango */
.cell.selected {
  background-color: rgba(59, 130, 246, 0.15);
}

.cell.selected.active {
  background-color: white;
  border: 2px solid #3b82f6;
}

/* Redimensionadores (Resizers) */
.resizer {
    position: absolute;
    background: transparent;
    z-index: 25;
}

.resizer:hover, .resizer:active {
    background: #3b82f6;
}

.col-resizer {
    top: 0;
    right: 0;
    width: 5px;
    height: 100%;
    cursor: col-resize;
}

.row-resizer {
    bottom: 0;
    left: 0;
    width: 100%;
    height: 5px;
    cursor: row-resize;
}

/* Helper para portapapeles */
.clipboard-helper {
    position: absolute;
    left: -9999px;
    top: 0;
}

/* ==========================================
   ESTILOS DEL MODAL
   ========================================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  width: 400px;
  text-align: center;
}

.modal-content h3 {
  margin-top: 0;
  color: #333;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 15px;
}
</style>
