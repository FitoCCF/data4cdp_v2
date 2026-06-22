// List of database fields that represent numeric values where we need to replace decimal commas with dots
export const numericKeys = [
  'n1fe', 'n2cu', 'n3zn', 'n4mo', 'n5ech5', 'n6sc', 'n7ech7',
  'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pSol',
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
    if (isNumeric && val.includes(',')) {
      val = val.replace(',', '.');
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
export const mapGridKeyToPayload = (key, colKeys = []) => {
  if (key === 'task') return 'task_id';
  if (key === 'usuario') return 'usuario_id';
  if (key === 'estado') return 'estado_id';
  if (key === 'user') return 'user_id';
  if (key === 'userp') return 'user';
  if (key === 'sample') return 'sample_id';
  if (key === 'group') {
    return colKeys.includes('task') ? 'usuario_id' : 'group_id';
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
