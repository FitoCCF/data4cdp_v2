import { normalizeNumberText } from './gridFormulas';

// Campos numéricos: al enviarlos a la API se quita la coma de miles (ver normalizeNumberText)
export const numericKeys = [
  'n1fe', 'n2cu', 'n3zn', 'n4mo', 'n5ech5', 'n6sc', 'n7ech7',
  'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pOx', 'pSol',
  'tara', 'tweight', 'dweight', 'pweight',
  'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7'
];

/**
 * Sanitizes a value: trims whitespace, replaces empty string/null with null,
 * and replaces commas with dots if the field is numeric.
 * @param {any} val - The raw cell value
 * @param {boolean} isNumeric - Whether the target field is numeric
 * @returns {any} Sanitized value
 */
export const sanitizeValue = (val, isNumeric = false) => {
  if (typeof val === 'string') {
    val = val.trim();
    // Números copiados de Excel: coma de miles y punto decimal ('1,035.5' -> '1035.5'). Antes solo se
    // cambiaba la primera coma por punto y '1,035.5' quedaba como '1.035.5' (inválido para la API).
    // Un formato no aceptado se deja tal cual para que la API lo rechace en vez de guardar otro número.
    if (isNumeric && val !== '') {
      const normalized = normalizeNumberText(val);
      if (normalized !== null) val = normalized;
    }
  }
  return (val === '' || val === null || val === undefined) ? null : val;
};

/**
 * Maps a frontend grid column key to the backend payload key
 * @param {string} key - The frontend column key
 * @param {string[]} colKeys - All column keys in the grid
 * @returns {string} The backend payload key
 */
// Los nombres deben coincidir con los campos de escritura de los serializers del backend
// (contrato verificado en backend/works4cdp/tests/test_api.py -> ContratoConElFrontendTests).
// Corrección: antes 'user' se enviaba como 'user_id' y 'group' como 'group_id'; AssaySerializer y
// UserSerializer esperan 'user' y 'group', así que DRF ignoraba esos valores y no se guardaban.
// Se quitaron también 'usuario' y 'userp', que ningún grid usa.
export const mapGridKeyToPayload = (key, colKeys = []) => {
  if (key === 'task') return 'task_id';       // TaskPSerializer
  if (key === 'estado') return 'estado_id';   // TaskPSerializer
  if (key === 'sample') return 'sample_id';   // AssaySerializer
  if (key === 'group') {
    // En la grilla de tareas programadas (TaskP) el campo de escritura es group_id;
    // en la de usuarios (User) es group.
    return colKeys.includes('task') ? 'group_id' : 'group';
  }
  return key;
};

/**
 * Builds a payload object from a grid row array and column keys array.
 * @param {any[]} row - The grid row data array
 * @param {string[]} colKeys - The grid column keys array
 * @returns {object} The constructed payload object
 */
export const buildPayloadFromRow = (row, colKeys) => {
  const payload = {};
  colKeys.forEach((key, idx) => {
    if (key.includes('__')) return; // Skip read-only hierarchy fields
    const rawVal = row[idx];
    const mappedKey = mapGridKeyToPayload(key, colKeys);
    const isNumeric = numericKeys.includes(key);
    payload[mappedKey] = sanitizeValue(rawVal, isNumeric);
  });
  return payload;
};
