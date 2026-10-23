// Pruebas de la conexión ExcelGrid <-> API (parámetros grid_filters / ordering y cargador de valores).
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/api', () => ({ api: { get: vi.fn() } }))

import { api } from '../src/api'
import {
  buildGridFiltersParam, buildGridParams, buildOrderingParam, createGridValuesLoader, GRID_VALUES_LIMIT,
} from '../src/utils/gridQuery'

const colToField = ['id', 'tag', null, 'equipment__area__plant__name']

describe('buildGridFiltersParam', () => {
  it('traduce columnas a campos y omite columnas sin campo', () => {
    const json = buildGridFiltersParam({ 1: { in: ['A'], empty: true }, 2: { in: ['x'] } }, colToField)
    expect(JSON.parse(json)).toEqual({ tag: { in: ['A'], empty: true } })
  })

  it('sin filtros devuelve undefined', () => {
    expect(buildGridFiltersParam({}, colToField)).toBeUndefined()
  })

  it('skipCol omite la columna indicada', () => {
    expect(buildGridFiltersParam({ 1: { in: ['A'] } }, colToField, { skipCol: '1' })).toBeUndefined()
  })

  it('acepta un objeto como mapa columna -> campo', () => {
    expect(JSON.parse(buildGridFiltersParam({ 5: { in: ['1'] } }, { 5: 'plant' }))).toEqual({ plant: { in: ['1'] } })
  })
})

describe('buildOrderingParam / buildGridParams', () => {
  it('orden ascendente y descendente', () => {
    expect(buildOrderingParam({ colIndex: 3, direction: 'asc' }, colToField)).toBe('equipment__area__plant__name')
    expect(buildOrderingParam({ colIndex: 1, direction: 'desc' }, colToField)).toBe('-tag')
    expect(buildOrderingParam({ colIndex: null }, colToField)).toBeUndefined()
    expect(buildOrderingParam({ colIndex: 2, direction: 'asc' }, colToField)).toBeUndefined()
  })

  it('combina parámetros base, filtros y orden', () => {
    const params = buildGridParams({
      baseParams: { page: 2, page_size: 25 },
      specs: { 1: { not_in: ['B'] } },
      sort: { colIndex: 0, direction: 'desc' },
      colToField,
    })
    expect(params).toEqual({ page: 2, page_size: 25, grid_filters: '{"tag":{"not_in":["B"]}}', ordering: '-id' })
  })
})

describe('createGridValuesLoader', () => {
  beforeEach(() => api.get.mockReset())

  it('pide grid-values con filtrado cruzado, búsqueda y parámetros fijos', async () => {
    api.get.mockResolvedValue({ data: { values: ['', 'A'], truncated: false } })
    const loader = createGridValuesLoader('equipments', colToField, () => ({ system: 3 }))
    const result = await loader(1, { 1: { in: ['A'] }, 0: { in: ['7'] } }, 'a')
    expect(result).toEqual({ values: ['', 'A'], truncated: false })
    expect(api.get).toHaveBeenCalledWith('equipments/grid-values/', {
      params: { system: 3, field: 'tag', limit: GRID_VALUES_LIMIT, grid_filters: '{"id":{"in":["7"]}}', search: 'a' },
    })
  })

  it('columna sin campo -> null (la grilla usa valores locales)', async () => {
    const loader = createGridValuesLoader('equipments', colToField)
    expect(await loader(2, {})).toBeNull()
    expect(api.get).not.toHaveBeenCalled()
  })
})
