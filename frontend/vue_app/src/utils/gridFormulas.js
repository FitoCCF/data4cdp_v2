// Columnas calculadas (fórmulas) para ExcelGrid.
//
// Una vista declara en `columnsConfig[col].formula`:
//   {
//     dependsOn: [índices de columna],   // al cambiar cualquiera de ellas se recalcula esta columna
//     compute: (num, row) => valor,      // num(col) devuelve el número de la celda o null si no hay
//     editable: false,                   // true = el usuario puede sobrescribir el valor a mano
//     description: 'Peso Total − Tara',  // se muestra como ayuda en la celda
//   }
// ExcelGrid recalcula en cascada (una fórmula puede depender de otra) al escribir, pegar, elegir en un
// desplegable o autoincrementar. Las fórmulas de pesos de ensayo están aquí para reutilizarlas en
// cualquier vista (Ensayos, Muestreo, ...) a partir del índice de cada campo.

/**
 * Normaliza un número copiado de Excel al formato de la API.
 * Formato aceptado (indicado por el usuario): el PUNTO es el decimal y la COMA es separador de miles,
 * que se descarta: '1,035.5' -> '1035.5', '1035.5' -> '1035.5', '1,234,567' -> '1234567'.
 * También se quitan los espacios (incluido el espacio duro que a veces copia Excel).
 * Cualquier otro uso de la coma no es válido y devuelve null (la grilla lo marca en rojo) en vez de
 * convertirse en un número equivocado: '114,5' o '0,84' (coma decimal) y '1.035,5' (formato europeo).
 */
const ACCEPTED_NUMBER = /^-?(\d{1,3}(,\d{3})+|\d+)?(\.\d+)?$/;

export const normalizeNumberText = (value) => {
  if (value === null || value === undefined) return null;
  const text = String(value).replace(/[\s\u00a0\u202f]/g, '');
  if (text === '' || text === '-' || !/\d/.test(text) || !ACCEPTED_NUMBER.test(text)) return null;
  return text.replace(/,/g, '');
};

/** Convierte el texto de una celda en número (acepta los formatos de Excel). Vacío o no numérico -> null. */
export const toNumber = (value) => {
  if (value === null || value === undefined) return null;
  const raw = typeof value === 'object' && value.value !== undefined ? value.value : value;
  if (typeof raw === 'number') return Number.isFinite(raw) ? raw : null;
  const text = normalizeNumberText(raw);
  return text === null ? null : Number(text);
};

/** true si la celda tiene texto pero no es un número válido. */
export const isInvalidNumber = (value) => {
  if (value === null || value === undefined) return false;
  const raw = typeof value === 'object' && value.value !== undefined ? value.value : value;
  return String(raw).trim() !== '' && toNumber(raw) === null;
};

/** Índices de columna que son entrada de alguna fórmula de columnsConfig. */
export const formulaInputColumns = (columnsConfig = {}) => {
  const inputs = new Set();
  Object.values(columnsConfig).forEach((cfg) => (cfg?.formula?.dependsOn || []).forEach((c) => inputs.add(Number(c))));
  return inputs;
};

/** Redondeo que evita el ruido binario de los decimales (p. ej. 0.3 - 0.1 = 0.19999999999999998). */
export const roundTo = (value, decimals) => {
  const factor = 10 ** decimals;
  return Math.round((value + Number.EPSILON) * factor) / factor;
};

/** Peso Prod. = Peso Total − Tara. */
export const pesoProducto = (tweight, tara) => {
  if (tweight === null || tara === null) return null;
  return roundTo(tweight - tara, 4);
};

/** % Sólidos = Peso Seco / (Peso Total − Tara) × 100, con 2 decimales. Sin peso neto positivo -> null. */
export const porcentajeSolidos = (dweight, tweight, tara) => {
  const neto = pesoProducto(tweight, tara);
  if (dweight === null || neto === null || neto <= 0) return null;
  return roundTo((dweight / neto) * 100, 2);
};

/**
 * Fórmulas de pesos de un ensayo para columnsConfig, según el índice de cada campo en la grilla.
 * Solo incluye las columnas que existen (índice >= 0), así sirve para grillas con distinto diseño.
 *
 * @param {(key: string) => number} indexOf  Índice de columna de un campo (p. ej. colKeys.indexOf).
 * @param {object} [options]
 * @param {boolean} [options.pSolEditable=true]  Permite sobrescribir % Sólidos a mano.
 */
export const assayWeightFormulas = (indexOf, { pSolEditable = true } = {}) => {
  const tara = indexOf('tara');
  const tweight = indexOf('tweight');
  const dweight = indexOf('dweight');
  const pweight = indexOf('pweight');
  const pSol = indexOf('pSol');
  const formulas = {};

  if (pweight >= 0 && tara >= 0 && tweight >= 0) {
    formulas[pweight] = {
      formula: {
        dependsOn: [tweight, tara],
        compute: (num) => pesoProducto(num(tweight), num(tara)),
        editable: false,
        description: 'Calculado: Peso Total − Tara',
      },
    };
  }

  if (pSol >= 0 && tara >= 0 && tweight >= 0 && dweight >= 0) {
    formulas[pSol] = {
      formula: {
        dependsOn: [dweight, tweight, tara],
        compute: (num) => porcentajeSolidos(num(dweight), num(tweight), num(tara)),
        editable: pSolEditable,
        description: 'Calculado: Peso Seco / (Peso Total − Tara) × 100',
      },
    };
  }

  return formulas;
};

/**
 * Recalcula en una fila las fórmulas afectadas por el cambio de una columna, en cascada.
 * Devuelve las columnas recalculadas. Función pura (sin Vue), usada por ExcelGrid.
 *
 * @param {Array} row
 * @param {number} changedCol
 * @param {object} columnsConfig
 */
export const applyFormulas = (row, changedCol, columnsConfig = {}) => {
  const formulaCols = Object.keys(columnsConfig)
    .map(Number)
    .filter((col) => columnsConfig[col]?.formula);
  if (formulaCols.length === 0) return [];

  const num = (col) => toNumber(row[col]);
  const changed = new Set([Number(changedCol)]);
  const recalculated = [];

  // Como mucho una pasada por fórmula: suficiente para cadenas de dependencias sin ciclos.
  for (let pass = 0; pass < formulaCols.length; pass++) {
    let progressed = false;
    for (const col of formulaCols) {
      const { dependsOn = [], compute, editable = false } = columnsConfig[col].formula;
      if (recalculated.includes(col) || !dependsOn.some((dep) => changed.has(Number(dep)))) continue;
      const value = compute(num, row);
      if (value === null || value === undefined) {
        // Faltan datos para calcular. En una columna editable se conserva lo que haya (p. ej. un % Sol
        // ingresado a mano); en una de solo lectura se vacía, porque su valor ya no es válido.
        if (editable) continue;
        row[col] = '';
      } else {
        row[col] = value;
      }
      recalculated.push(col);
      changed.add(col);
      progressed = true;
    }
    if (!progressed) break;
  }
  return recalculated;
};
