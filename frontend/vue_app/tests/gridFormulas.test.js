// Pruebas de las fórmulas de columnas calculadas (Peso Prod. y % Sol).
import { describe, expect, it } from 'vitest'
import { applyFormulas, assayWeightFormulas, normalizeNumberText, pesoProducto, porcentajeSolidos, toNumber } from '../src/utils/gridFormulas'
import { sanitizeValue } from '../src/utils/gridHelpers'

describe('fórmulas de pesos', () => {
  it('toNumber descarta la coma de miles y los vacíos o texto', () => {
    expect(toNumber('1,113.5')).toBe(1113.5)
    expect(toNumber(' 60 ')).toBe(60)
    expect(toNumber('')).toBeNull()
    expect(toNumber('abc')).toBeNull()
    expect(toNumber(null)).toBeNull()
  })

  it('Peso Prod. = Peso Total − Tara, sin ruido binario', () => {
    expect(pesoProducto(174.5, 114.5)).toBe(60)
    expect(pesoProducto(200.3, 114.5)).toBe(85.8)
    expect(pesoProducto(null, 114.5)).toBeNull()
  })

  it('% Sol = Peso Seco / (Peso Total − Tara) × 100 con 2 decimales', () => {
    expect(porcentajeSolidos(30, 110, 10)).toBe(30)
    expect(porcentajeSolidos(1, 3, 0)).toBe(33.33)
    expect(porcentajeSolidos(5, 10, 10)).toBeNull() // peso neto 0
  })
})

describe('applyFormulas con el diseño de Ensayos', () => {
  const colKeys = ['id', 'pSol', 'tara', 'tweight', 'dweight', 'pweight']
  const config = assayWeightFormulas((k) => colKeys.indexOf(k))
  const row = (vals) => colKeys.map((k) => vals[k] ?? '')

  it('al cambiar Peso Total recalcula Peso Prod. y % Sol', () => {
    const r = row({ tara: '114.5', tweight: '174.5', dweight: '30' })
    expect(applyFormulas(r, colKeys.indexOf('tweight'), config).sort()).toEqual([1, 5])
    expect(r[5]).toBe(60)
    expect(r[1]).toBe(50)
  })

  it('cambiar una columna que no es entrada no toca las fórmulas', () => {
    const r = row({ tara: '10', tweight: '20', pSol: '99' })
    expect(applyFormulas(r, 0, config)).toEqual([])
    expect(r[1]).toBe('99')
  })

  it('si falta un peso: Peso Prod. (solo lectura) se vacía y % Sol (editable) conserva el valor manual', () => {
    const r = row({ tara: '10', tweight: '', pweight: '7', pSol: '45' })
    applyFormulas(r, colKeys.indexOf('tweight'), config)
    expect(r[5]).toBe('')
    expect(r[1]).toBe('45')
  })

  it('las columnas que no existen en la grilla no generan fórmula', () => {
    const sinPeso = assayWeightFormulas((k) => ['tara', 'tweight', 'dweight', 'pSol'].indexOf(k))
    expect(Object.keys(sinPeso)).toEqual(['3'])
  })

  it('cascada: una fórmula que depende de otra calculada', () => {
    const cfg = {
      1: { formula: { dependsOn: [0], compute: (num) => num(0) * 2 } },
      2: { formula: { dependsOn: [1], compute: (num) => num(1) + 1 } },
    }
    const r = ['5', '', '']
    applyFormulas(r, 0, cfg)
    expect(r).toEqual(['5', 10, 11])
  })
})

describe('normalizeNumberText: punto decimal, coma de miles (se descarta)', () => {
  it.each([
    ['1035.5', '1035.5'], ['1,035.5', '1035.5'], ['1,035', '1035'], ['1,234,567.89', '1234567.89'],
    ['1 035.5', '1035.5'], ['1\u00a0035.5', '1035.5'], ['-0.25', '-0.25'], ['0.035', '0.035'], ['12', '12'],
  ])('%s -> %s', (input, expected) => {
    expect(normalizeNumberText(input)).toBe(expected)
  })

  it.each([['1.035,5'], ['114,5'], ['0,84'], ['1,03'], ['10,0000'], ['1.2.3'], ['N/D'], ['abc'], ['-'], ['']])('%s no es un formato aceptado', (input) => {
    expect(normalizeNumberText(input)).toBeNull()
  })

  it('sanitizeValue (payload a la API) usa la misma normalización', () => {
    expect(sanitizeValue('1,035.5', true)).toBe('1035.5')
    expect(sanitizeValue('Línea 1, norte', false)).toBe('Línea 1, norte')
  })
})
