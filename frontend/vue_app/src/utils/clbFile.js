// Reglas del archivo .clb de calibración que se descarga desde la vista Ensayos: texto plano con las
// columnas separadas por tabuladores.

/**
 * Valor de una columna NUMÉRICA del .clb.
 *
 * El .clb no admite columnas vacías. El sistema que lo lee ubica cada valor por su posición entre
 * tabuladores, así que una celda en blanco se interpreta como lectura ausente o, peor, corre de
 * lugar las columnas siguientes. Por eso un ensayo que en `works4cdp_assay` no tiene la lectura
 * (NULL en la base, celda vacía en la grilla) se exporta como **0**.
 *
 * Solo vale para las lecturas (N1 Fe, N2 Cu, ...) y los porcentajes (% Fe, % Cu, ..., % Sol). La
 * fecha y la hora NO se rellenan con 0: un 0 ahí no significa nada y tienen su propio formato.
 *
 * Un 0 que ya está en la base sale igual que un vacío, y es a propósito: desde el punto de vista del
 * sistema que consume el archivo son lo mismo.
 */
export const formatClbNumber = (val) => {
  if (val === null || val === undefined) return '0';
  const text = String(val).trim();
  return text === '' ? '0' : text;
};
