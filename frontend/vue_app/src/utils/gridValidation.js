// Avisos de validación de celdas para ExcelGrid (no bloquean el guardado).
//
// Serie correlativa: una vista declara `columnsConfig[col].seriesCheck = true` en una columna de códigos
// correlativos (p. ej. chemical_id). ExcelGrid toma la mediana de los códigos cargados y marca en naranja
// los que se salen de la serie. Detecta el error típico de un dígito de más o de menos (53098 en vez de
// 5309), que ya rompió la serie de Courier moly C2 el 2026-10-24.

import { toNumber } from './gridFormulas';

// Un código está fuera de la serie si es más del doble o menos de la mitad de la mediana.
const SERIES_FACTOR = 2;
// Con menos códigos que esto la mediana no es representativa y no se avisa.
const MIN_SERIES_SIZE = 3;

/** Mediana de los números válidos (> 0) de una lista; null si hay menos de MIN_SERIES_SIZE. */
export const seriesMedian = (values) => {
  const nums = values.map(toNumber).filter((n) => n !== null && n > 0).sort((a, b) => a - b);
  if (nums.length < MIN_SERIES_SIZE) return null;
  const mid = Math.floor(nums.length / 2);
  return nums.length % 2 ? nums[mid] : (nums[mid - 1] + nums[mid]) / 2;
};

/** true si el valor es un número claramente fuera de la serie cuya mediana es `median`. */
export const isOutOfSeries = (value, median) => {
  if (median === null || median === undefined) return false;
  const n = toNumber(value);
  if (n === null || n <= 0) return false;
  return n > median * SERIES_FACTOR || n < median / SERIES_FACTOR;
};
