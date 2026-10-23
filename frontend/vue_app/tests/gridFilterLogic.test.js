// Pruebas de la lógica del menú de filtros de ExcelGrid (qué filtro se envía al pulsar "Aceptar").
import { describe, expect, it } from 'vitest'
import { cellPassesSpec, compareCellText, resolveFilterSelection, sortFilterValues } from '../src/utils/gridFilterLogic'

describe('sortFilterValues', () => {
  it('pone (Vacías) primero y usa orden natural', () => {
    expect(sortFilterValues(['10', '', '2', 'b', 'A'])).toEqual(['', '2', '10', 'A', 'b'])
  })

  it('ordena por la etiqueta visible si se indica (columnas select)', () => {
    const labels = { 1: 'Zeta', 2: 'Alfa' }
    expect(sortFilterValues(['1', '2'], (v) => labels[v])).toEqual(['2', '1'])
  })
})

describe('resolveFilterSelection', () => {
  const all = ['', 'A', 'B', 'C', 'D']
  const resolve = (selected, extra = {}) =>
    resolveFilterSelection({ selected: new Set(selected), allValues: all, visibleValues: all, ...extra })

  it('todo marcado quita el filtro', () => {
    expect(resolve(all).clear).toBe(true)
  })

  it('pocos marcados -> lista "in"', () => {
    expect(resolve(['A']).spec).toEqual({ in: ['A'], empty: false })
  })

  it('(Vacías) sola -> in vacío con empty', () => {
    expect(resolve(['']).spec).toEqual({ in: [], empty: true })
  })

  it('pocos desmarcados -> lista "not_in" (URL corta)', () => {
    expect(resolve(['', 'A', 'B', 'C']).spec).toEqual({ not_in: ['D'], empty: false })
  })

  it('desmarcar (Vacías) y un valor -> not_in con empty', () => {
    expect(resolve(['A', 'B', 'C']).spec).toEqual({ not_in: ['D'], empty: true })
  })

  it('con búsqueda solo cuentan los visibles marcados (como Excel)', () => {
    const result = resolve(all, { searchActive: true, visibleValues: ['A', 'B'] })
    expect(result.clear).toBe(false)
    expect(result.spec).toEqual({ in: ['A', 'B'], empty: false })
  })

  it('lista truncada: nunca asume "todo" ni usa not_in', () => {
    const result = resolve(all, { truncated: true })
    expect(result.clear).toBe(false)
    expect(result.spec).toEqual({ in: ['A', 'B', 'C', 'D'], empty: true })
  })

  it('ignora valores marcados que ya no están disponibles', () => {
    expect(resolve(['A', 'Z']).spec).toEqual({ in: ['A'], empty: false })
  })
})

describe('cellPassesSpec', () => {
  it('in: solo los valores listados (y vacías si empty)', () => {
    expect(cellPassesSpec('A', { in: ['A'], empty: false })).toBe(true)
    expect(cellPassesSpec('B', { in: ['A'], empty: false })).toBe(false)
    expect(cellPassesSpec('', { in: [], empty: true })).toBe(true)
  })

  it('not_in: deja pasar valores nuevos que no estaban al filtrar', () => {
    expect(cellPassesSpec('NUEVO', { not_in: ['A'], empty: false })).toBe(true)
    expect(cellPassesSpec('A', { not_in: ['A'], empty: false })).toBe(false)
    expect(cellPassesSpec('', { not_in: ['A'], empty: true })).toBe(false)
  })

  it('sin spec usa la lista de valores marcados', () => {
    expect(cellPassesSpec('A', undefined, new Set(['A']))).toBe(true)
    expect(cellPassesSpec('A', undefined, undefined)).toBe(true)
  })
})

describe('compareCellText', () => {
  const sortBy = (vals, dir) => [...vals].sort((a, b) => compareCellText(a, b, dir))

  it('números por valor', () => {
    expect(sortBy(['10', '9', '-1', '2.5'], 'asc')).toEqual(['-1', '2.5', '9', '10'])
  })

  it('fechas y horas ISO en orden cronológico (no como el número 2026)', () => {
    expect(sortBy(['2026-10-22', '2026-10-20', '2025-12-31'], 'desc')).toEqual(['2026-10-22', '2026-10-20', '2025-12-31'])
    expect(sortBy(['10:05:00', '09:59:59'], 'asc')).toEqual(['09:59:59', '10:05:00'])
  })

  it('códigos de muestra en orden natural', () => {
    expect(sortBy(['C_01_S10', 'C_01_S2', 'c_01_s3'], 'asc')).toEqual(['C_01_S2', 'c_01_s3', 'C_01_S10'])
  })

  it('vacías al final en ambas direcciones', () => {
    expect(sortBy(['', 'B', 'A'], 'asc')).toEqual(['A', 'B', ''])
    expect(sortBy(['', 'B', 'A'], 'desc')).toEqual(['B', 'A', ''])
  })
})
