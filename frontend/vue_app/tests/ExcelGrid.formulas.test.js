// Pruebas de columnas calculadas en ExcelGrid: escribir, pegar y bloquear la edición manual.
import { beforeAll, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ExcelGrid from '../src/components/ExcelGrid.vue'
import { assayWeightFormulas } from '../src/utils/gridFormulas'

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
  if (!('innerText' in HTMLElement.prototype)) {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() { return this.textContent }, set(v) { this.textContent = v }, configurable: true,
    })
  }
})

const colKeys = ['id', 'pSol', 'tara', 'tweight', 'dweight', 'pweight']
const headers = ['ID', '% Sol', 'Tara', 'Peso Total', 'Peso Seco', 'Peso Prod.']
const columnsConfig = assayWeightFormulas((k) => colKeys.indexOf(k))
const COL = Object.fromEntries(colKeys.map((k, i) => [k, i]))

const mountInEdit = async (data) => {
  const wrapper = mount(ExcelGrid, { props: { headers, data, columnsConfig }, attachTo: document.body })
  await wrapper.findAll('button').find((b) => b.text() === 'Habilitar Edición').trigger('click')
  return wrapper
}
const cell = (w, r, c) => w.findAll('.excel-table tbody tr')[r].findAll('td')[c + 1]
// Escribir como en el navegador: se modifica el nodo de texto existente de la celda (no se reemplaza
// todo su contenido, que borraría los anclajes internos de Vue). Por eso las celdas editadas en estas
// pruebas parten con un valor.
const type = async (w, r, c, text) => {
  const td = cell(w, r, c)
  td.element.focus()
  const current = td.text()
  const walker = document.createTreeWalker(td.element, NodeFilter.SHOW_TEXT)
  let node
  while ((node = walker.nextNode()) && node.data.trim() !== current) { /* buscar el texto visible */ }
  if (!node) throw new Error(`no se encontró el texto "${current}" en la celda`)
  node.data = text
  await td.trigger('input')
  await td.trigger('blur')
  await nextTick()
}
const paste = async (w, r, c, text) => {
  const td = cell(w, r, c)
  td.element.focus()
  const event = new Event('paste', { bubbles: true, cancelable: true })
  event.clipboardData = { getData: () => text }
  td.element.dispatchEvent(event)
  await nextTick()
  await nextTick()
}

describe('ExcelGrid: columnas calculadas', () => {
  it('escribir Tara y Peso Total calcula Peso Prod. y % Sol', async () => {
    const w = await mountInEdit([['1', '', '0', '0', '30', '']])
    await type(w, 0, COL.tara, '114.5')
    await type(w, 0, COL.tweight, '174.5')
    expect(cell(w, 0, COL.pweight).text()).toBe('60')
    expect(cell(w, 0, COL.pSol).text()).toBe('50')
  })

  it('Peso Prod. no es editable y tiene la ayuda de la fórmula', async () => {
    const w = await mountInEdit([['1', '', '10', '20', '', '']])
    const td = cell(w, 0, COL.pweight)
    expect(td.attributes('contenteditable')).toBe('false')
    expect(td.classes()).toContain('formula-cell')
    expect(td.attributes('title')).toContain('Peso Total − Tara')
    // % Sol es calculada pero admite corrección manual
    expect(cell(w, 0, COL.pSol).attributes('contenteditable')).toBe('true')
  })

  it('pegar un bloque de pesos desde Excel calcula todas las filas', async () => {
    const w = await mountInEdit([['1', '', '', '', '', ''], ['2', '', '', '', '', '']])
    // Tara, Peso Total, Peso Seco, Peso Prod. (este último se ignora: lo calcula la fórmula)
    await paste(w, 0, COL.tara, '10\t110\t30\t999\n20\t70\t25\t999\n')
    expect([cell(w, 0, COL.pweight).text(), cell(w, 1, COL.pweight).text()]).toEqual(['100', '50'])
    expect([cell(w, 0, COL.pSol).text(), cell(w, 1, COL.pSol).text()]).toEqual(['30', '50'])
  })

  it('el valor calculado se guarda', async () => {
    const w = await mountInEdit([['1', '', '0', '0', '30', '']])
    await type(w, 0, COL.tara, '10')
    await type(w, 0, COL.tweight, '110')
    await w.findAll('button').find((b) => b.text() === 'Guardar Cambios').trigger('click')
    await w.findAll('button').find((b) => b.text() === 'Sí, Guardar').trigger('click')
    const [row] = w.emitted('save')[0][0]
    expect(row[COL.pweight]).toBe(100)
    expect(row[COL.pSol]).toBe(30)
  })

  it('% Sol manual se respeta mientras no cambien los pesos', async () => {
    const w = await mountInEdit([['1', '30', '10', '110', '30', '100']])
    await type(w, 0, COL.pSol, '31.5')
    expect(cell(w, 0, COL.pSol).text()).toBe('31.5')
    await type(w, 0, COL.dweight, '40')
    expect(cell(w, 0, COL.pSol).text()).toBe('40')
  })
})

describe('ExcelGrid: pegar pesos con coma de miles (formato 1,035.5)', () => {
  // Caso reportado: al pegar Tara / Peso Total / Peso Seco solo se calcularon algunas filas.
  // Las filas con Peso Total >= 1000 llegan desde Excel con separador de miles.
  it.each([
    ['1,035.5 (coma de miles, punto decimal)', '108.5\t1,035.5\t300\n111.5\t823\t250\n110.3\t1,117.5\t320\n'],
    ['con espacios de Excel', '108.5 \t 1,035.5\t300\n111.5\t823\u00a0\t250\n110.3\t1,117.5 \t320\n'],
  ])('%s: se calculan todas las filas y se guardan sin coma', async (_, clipboard) => {
    const w = await mountInEdit([['1', '', '', '', '', ''], ['2', '', '', '', '', ''], ['3', '', '', '', '', '']])
    await paste(w, 0, COL.tara, clipboard)
    expect([0, 1, 2].map((r) => cell(w, r, COL.tweight).text())).toEqual(['1035.5', '823', '1117.5'])
    expect([0, 1, 2].map((r) => cell(w, r, COL.pweight).text())).toEqual(['927', '711.5', '1007.2'])
    expect([0, 1, 2].map((r) => cell(w, r, COL.pSol).text())).toEqual(['32.36', '35.14', '31.77'])
  })

  it('formato no aceptado (1.035,5) se marca en rojo y no se calcula', async () => {
    const w = await mountInEdit([['1', '', '', '', '', '']])
    await paste(w, 0, COL.tara, '108.5\t1.035,5\t300\n')
    expect(cell(w, 0, COL.tweight).classes()).toContain('invalid-number')
    expect(cell(w, 0, COL.pweight).text()).toBe('')
  })

  it('un valor que no es número se marca en rojo', async () => {
    const w = await mountInEdit([['1', '', '', '', '', '']])
    await paste(w, 0, COL.tara, '10\tN/D\t5\n')
    expect(cell(w, 0, COL.tweight).classes()).toContain('invalid-number')
    expect(cell(w, 0, COL.tara).classes()).not.toContain('invalid-number')
    expect(cell(w, 0, COL.pweight).text()).toBe('')
  })
})
