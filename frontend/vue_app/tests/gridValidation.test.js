// Pruebas del aviso de códigos correlativos fuera de la serie (chemical_id).
import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ExcelGrid from '../src/components/ExcelGrid.vue'
import { isOutOfSeries, seriesMedian } from '../src/utils/gridValidation'

describe('seriesMedian / isOutOfSeries', () => {
  it('caso real: 53098 y 53099 entre códigos ~5309 quedan fuera de la serie', () => {
    const median = seriesMedian(['5305', '5306', '5307', '5308', '53099', '53098', '5310', '5311'])
    expect(median).toBe(5309)
    expect(isOutOfSeries('53099', median)).toBe(true)
    expect(isOutOfSeries('531', median)).toBe(true) // dígito de menos
    expect(isOutOfSeries('5312', median)).toBe(false)
  })

  it('sin códigos suficientes o vacíos no avisa', () => {
    expect(seriesMedian(['10755', ''])).toBeNull()
    expect(isOutOfSeries('99999', null)).toBe(false)
    expect(isOutOfSeries('', 5309)).toBe(false)
  })
})

describe('ExcelGrid con seriesCheck', () => {
  const headers = ['ID', 'Código']
  const data = [['1', '10753'], ['2', '10754'], ['3', '53100'], ['4', '10756']]

  it('marca en naranja el código fuera de la serie y lo explica en la ayuda', async () => {
    HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
    const w = mount(ExcelGrid, { props: { headers, data, columnsConfig: { 1: { seriesCheck: true } } } })
    await flushPromises()
    const codes = w.findAll('.excel-table tbody td[data-col-index="1"]')
    expect(codes.map((td) => td.classes().includes('out-of-series'))).toEqual([false, false, true, false])
    expect(codes[2].attributes('title')).toContain('fuera de la serie')
    w.unmount()
  })

  it('sin seriesCheck no se marca nada', async () => {
    const w = mount(ExcelGrid, { props: { headers, data } })
    await flushPromises()
    expect(w.findAll('.excel-table tbody tr')).toHaveLength(4)
    expect(w.findAll('.out-of-series')).toHaveLength(0)
    w.unmount()
  })
})
