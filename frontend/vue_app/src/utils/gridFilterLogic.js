// Lógica pura del menú de filtros de ExcelGrid (sin Vue), separada para poder probarla de forma aislada.
//
// Convención: el valor '' representa "(Vacías)" (NULL o texto vacío en la base de datos).

const collator = new Intl.Collator('es', { numeric: true, sensitivity: 'base' });

// Número "completo" (p. ej. '12', '-0.5'); '2026-10-20' o 'C_01_S2' NO son números aunque empiecen con dígitos.
const NUMERIC_RE = /^-?\d+(\.\d+)?$/;

/**
 * Compara dos textos de celda para ordenar como Excel:
 * - números completos por valor numérico;
 * - el resto (fechas ISO, horas, códigos de muestra) en orden natural: 'S2' < 'S10';
 * - las celdas vacías siempre al final, en ascendente y en descendente.
 * Antes se usaba parseFloat: '2026-10-20' y '2026-10-22' valían 2026 y quedaban "iguales".
 */
export const compareCellText = (a, b, direction = 'asc') => {
  const textA = String(a ?? '').trim();
  const textB = String(b ?? '').trim();
  if (textA === '' || textB === '') {
    if (textA === textB) return 0;
    return textA === '' ? 1 : -1; // vacías al final sin importar la dirección
  }
  const sign = direction === 'desc' ? -1 : 1;
  if (NUMERIC_RE.test(textA) && NUMERIC_RE.test(textB)) {
    return sign * (Number(textA) - Number(textB));
  }
  return sign * collator.compare(textA, textB);
};

/**
 * Ordena los valores del menú como lo haría Excel: "(Vacías)" primero y luego en orden natural
 * (2 antes que 10, sin distinguir mayúsculas). Si se pasa labelOf, se ordena por la etiqueta visible
 * (útil en columnas tipo select, donde el valor es un ID y la etiqueta es el nombre).
 */
export const sortFilterValues = (values, labelOf = (v) => v) => {
  return [...values].sort((a, b) => {
    if (a === '' && b !== '') return -1;
    if (b === '' && a !== '') return 1;
    return collator.compare(String(labelOf(a)), String(labelOf(b)));
  });
};

/**
 * Decide qué filtro aplicar cuando el usuario pulsa "Aceptar".
 *
 * @param {object} p
 * @param {Set<string>} p.selected       Valores marcados en el menú.
 * @param {string[]}    p.allValues      Todos los valores disponibles de la columna (tras filtrado cruzado).
 * @param {string[]}    p.visibleValues  Valores que coinciden con el texto de "Buscar" (o todos si no hay búsqueda).
 * @param {boolean}     p.searchActive   Si hay texto en "Buscar".
 * @param {boolean}     p.truncated      Si el servidor no devolvió todos los valores (lista incompleta).
 * @returns {{ clear: boolean, selected: Set<string>, spec: object|null }}
 *   clear=true  -> quitar el filtro de la columna (todo seleccionado).
 *   spec        -> { in: [...], empty } o { not_in: [...], empty }, formato que entiende la API (grid_filters).
 *                  `empty` indica que "(Vacías)" forma parte de la lista.
 */
export const resolveFilterSelection = ({ selected, allValues, visibleValues, searchActive = false, truncated = false }) => {
  // Como en Excel: con texto en "Buscar", solo cuentan los valores visibles que estén marcados.
  const available = new Set(allValues); // Set: búsquedas O(1) aunque la columna tenga miles de valores
  const effective = searchActive
    ? new Set(visibleValues.filter((v) => selected.has(v)))
    : new Set([...selected].filter((v) => truncated || available.has(v)));

  const everythingSelected = !truncated && allValues.length > 0 && allValues.every((v) => effective.has(v));
  if (everythingSelected) {
    return { clear: true, selected: effective, spec: null };
  }

  const included = [...effective].filter((v) => v !== '');
  const includesEmpty = effective.has('');

  // Si se desmarcaron pocos valores (o tantos como quedaron marcados), se guarda la lista de excluidos:
  // - en el servidor la URL queda corta (escalable);
  // - en el filtro de página, al cambiar de página siguen ocultos los valores desmarcados y se ven los
  //   valores nuevos (lo que el usuario espera al "quitar" un valor).
  // Solo es posible cuando se conoce la lista completa (no truncada) y no hay búsqueda: con texto en
  // "Buscar" el usuario pidió exactamente las coincidencias, como en Excel.
  if (!truncated && !searchActive) {
    const excluded = allValues.filter((v) => v !== '' && !effective.has(v));
    if (excluded.length <= included.length) {
      const emptyAvailable = allValues.includes('');
      return {
        clear: false,
        selected: effective,
        spec: { not_in: excluded, empty: emptyAvailable && !includesEmpty },
      };
    }
  }

  return { clear: false, selected: effective, spec: { in: included, empty: includesEmpty } };
};

/**
 * Filtro local: ¿la celda pasa el filtro de su columna?
 * Usa la especificación (spec) si existe, para que un filtro "excluir" (not_in) deje pasar valores
 * que aparecen al cambiar de página; si no, la lista de valores marcados.
 */
export const cellPassesSpec = (cellValue, spec, allowedValues) => {
  if (spec && spec.not_in) {
    if (cellValue === '') return !spec.empty;
    return !spec.not_in.includes(cellValue);
  }
  if (spec && spec.in) {
    if (cellValue === '') return Boolean(spec.empty);
    return spec.in.includes(cellValue);
  }
  if (!allowedValues) return true;
  return allowedValues.has(cellValue);
};
