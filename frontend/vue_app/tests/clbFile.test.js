// Pruebas de las reglas del archivo .clb (ver src/utils/clbFile.js).
import { describe, expect, it } from 'vitest'
import { formatClbNumber } from '../src/utils/clbFile'

describe('formatClbNumber: el .clb no lleva columnas vacías', () => {
  it('un valor ausente en la base se escribe 0', () => {
    expect(formatClbNumber(null)).toBe('0')
    expect(formatClbNumber(undefined)).toBe('0')
  })

  it('una celda vacía de la grilla también se escribe 0', () => {
    expect(formatClbNumber('')).toBe('0')
    expect(formatClbNumber('   ')).toBe('0')
  })

  it('un valor presente se escribe tal cual', () => {
    expect(formatClbNumber(32.36)).toBe('32.36')
    expect(formatClbNumber(0)).toBe('0')
    expect(formatClbNumber('1035.5')).toBe('1035.5')
    expect(formatClbNumber(-1.5)).toBe('-1.5')
  })

  it('no inventa decimales ni redondea', () => {
    expect(formatClbNumber(0.1)).toBe('0.1')
    expect(formatClbNumber(100)).toBe('100')
  })

  it('una fila con lecturas faltantes no deja ninguna columna en blanco', () => {
    // Caso real: un ensayo cargado sin % Ox ni % Sol. Antes el .clb salía con dos tabuladores
    // seguidos y el sistema que lo lee corría las columnas.
    const ensayo = { n1fe: 1200, n2cu: null, n3zn: '', n4mo: 340, n6sc: undefined, pSol: null }
    const fila = ['n1fe', 'n2cu', 'n3zn', 'n4mo', 'n6sc', 'pSol'].map((k) => formatClbNumber(ensayo[k]))

    expect(fila).toEqual(['1200', '0', '0', '340', '0', '0'])
    expect(fila.join('\t')).not.toMatch(/\t\t/)
    expect(fila.some((v) => v === '')).toBe(false)
  })
})
