// Conecta ExcelGrid con la API: arma los parámetros de filtro/orden y carga los valores de los menús.
//
// Las vistas solo declaran qué campo de la API corresponde a cada columna (colToField) y usan:
//   - buildGridParams(...)        -> parámetros para la petición paginada (grid_filters + ordering)
//   - createGridValuesLoader(...) -> función para la prop `filterValuesLoader` de ExcelGrid
import { api } from '../api';

export const GRID_VALUES_LIMIT = 1000;

/**
 * Convierte el mapa columna -> campo en un objeto. Acepta un arreglo (índice = columna) o un objeto.
 * Las columnas sin campo (null/undefined) no se filtran en el servidor.
 */
const fieldOf = (colToField, colIndex) => {
  const field = Array.isArray(colToField) ? colToField[Number(colIndex)] : colToField[colIndex];
  return field || null;
};

/**
 * @param {object} specs       { colIndex: { in|not_in: [...], empty } } emitido por ExcelGrid.
 * @param {Array|object} colToField
 * @param {object} [options]
 * @param {number|string} [options.skipCol]  Columna a omitir (filtrado cruzado del propio menú).
 * @returns {string|undefined} JSON para el parámetro grid_filters, o undefined si no hay filtros.
 */
export const buildGridFiltersParam = (specs, colToField, { skipCol } = {}) => {
  const byField = {};
  for (const [colIndex, spec] of Object.entries(specs || {})) {
    if (skipCol !== undefined && String(colIndex) === String(skipCol)) continue;
    const field = fieldOf(colToField, colIndex);
    if (field && spec) byField[field] = spec;
  }
  return Object.keys(byField).length ? JSON.stringify(byField) : undefined;
};

/** Parámetro ordering de DRF a partir del estado de orden de ExcelGrid ({ colIndex, direction }). */
export const buildOrderingParam = (sort, colToField) => {
  if (!sort || sort.colIndex === null || sort.colIndex === undefined) return undefined;
  const field = fieldOf(colToField, sort.colIndex);
  if (!field) return undefined;
  return sort.direction === 'desc' ? `-${field}` : field;
};

/**
 * Parámetros completos para la petición paginada de una grilla.
 * @param {object} p
 * @param {object} p.baseParams  page, page_size y filtros fijos de la vista (p. ej. sample__equipment).
 * @param {object} p.specs       Filtros de ExcelGrid.
 * @param {object} p.sort        Orden de ExcelGrid.
 * @param {Array|object} p.colToField
 */
export const buildGridParams = ({ baseParams = {}, specs = {}, sort = null, colToField }) => {
  const params = { ...baseParams };
  const gridFilters = buildGridFiltersParam(specs, colToField);
  if (gridFilters) params.grid_filters = gridFilters;
  const ordering = buildOrderingParam(sort, colToField);
  if (ordering) params.ordering = ordering;
  return params;
};

/**
 * Crea la función que ExcelGrid usa para llenar el menú de filtros desde el servidor
 * (GET /<endpoint>/grid-values/). Consulta solo la columna abierta, con límite y búsqueda,
 * en lugar de descargar todas las filas de la tabla.
 *
 * @param {string} endpoint          p. ej. 'plants' o 'assays'.
 * @param {Array|object} colToField
 * @param {Function} [getBaseParams] Devuelve los filtros fijos actuales de la vista.
 * @returns {Function} (colIndex, specs, search) => Promise<{ values, truncated } | null>
 *          null = columna sin campo en la API; la grilla usará sus valores locales.
 */
export const createGridValuesLoader = (endpoint, colToField, getBaseParams = () => ({})) => {
  return async (colIndex, specs, search = '') => {
    const field = fieldOf(colToField, colIndex);
    if (!field) return null;
    const params = { ...getBaseParams(), field, limit: GRID_VALUES_LIMIT };
    const gridFilters = buildGridFiltersParam(specs, colToField, { skipCol: colIndex });
    if (gridFilters) params.grid_filters = gridFilters;
    if (search) params.search = search;
    const response = await api.get(`${endpoint}/grid-values/`, { params });
    return { values: response.data.values, truncated: response.data.truncated };
  };
};
