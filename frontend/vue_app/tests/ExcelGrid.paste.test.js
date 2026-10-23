// Pruebas del pegado desde Excel externo (Ctrl+V) en modo edición.
import { beforeAll, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ExcelGrid from '../src/components/ExcelGrid.vue'

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
  // jsdom no implementa innerText (el navegador sí); ExcelGrid lo usa para leer el texto de la celda.
  if (!('innerText' in HTMLElement.prototype)) {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() { return this.textContent },
      set(v) { this.textContent = v },
      configurable: true,
    })
  }
})

const headers = ['ID', 'Muestra', 'Cu', 'Fe']
const blankRows = () => [['1', 'S1', '', ''], ['2', 'S2', '', ''], ['3', 'S3', '', ''], ['4', 'S4', '', '']]

const mountInEdit = async (data = blankRows()) => {
  const wrapper = mount(ExcelGrid, { props: { headers, data }, attachTo: document.body })
  await wrapper.findAll('button').find((b) => b.text() === 'Habilitar Edición').trigger('click')
  return wrapper
}

// Celda (fila visual, columna de datos) en modo edición: la primera <td> es el número de fila.
const cellEl = (wrapper, r, c) => wrapper.findAll('.excel-table tbody tr')[r].findAll('td')[c + 1]

// Simula lo que hace el usuario: clic en la celda (queda enfocada) y Ctrl+V con datos de Excel.
const clickAndPaste = async (wrapper, r, c, text) => {
  const td = cellEl(wrapper, r, c)
  await td.trigger('mousedown')
  td.element.focus()
  await td.trigger('focus')
  expect(document.activeElement).toBe(td.element) // la celda queda enfocada, como en el navegador
  const event = new Event('paste', { bubbles: true, cancelable: true })
  event.clipboardData = { getData: () => text }
  td.element.dispatchEvent(event)
  await nextTick()
  await nextTick()
}

const column = (wrapper, c) => wrapper.findAll('.excel-table tbody tr').map((tr) => tr.findAll('td')[c + 1].text())
const savedGrid = async (wrapper) => {
  await wrapper.findAll('button').find((b) => b.text() === 'Guardar Cambios').trigger('click')
  await wrapper.findAll('button').find((b) => b.text() === 'Sí, Guardar').trigger('click')
  return wrapper.emitted('save')[0][0]
}

describe('ExcelGrid: pegar varias celdas desde Excel', () => {
  it('la celda donde se hizo clic recibe el primer valor (columna)', async () => {
    const wrapper = await mountInEdit()
    await clickAndPaste(wrapper, 0, 2, '0.84\r\n0.91\r\n1.02\r\n')
    expect(column(wrapper, 2)).toEqual(['0.84', '0.91', '1.02', ''])
    const grid = await savedGrid(wrapper)
    expect(grid.map((r) => r[2])).toEqual(['0.84', '0.91', '1.02', ''])
  })

  it('bloque de varias filas y columnas', async () => {
    const wrapper = await mountInEdit()
    await clickAndPaste(wrapper, 1, 2, '1\t10\n2\t20\n')
    const grid = await savedGrid(wrapper)
    expect(grid.map((r) => [r[2], r[3]])).toEqual([['', ''], ['1', '10'], ['2', '20'], ['', '']])
  })

  it('pegar sobre una celda con valor la reemplaza', async () => {
    const data = blankRows()
    data[0][2] = 'viejo'
    const wrapper = await mountInEdit(data)
    await clickAndPaste(wrapper, 0, 2, 'nuevo\notro')
    const grid = await savedGrid(wrapper)
    expect(grid.map((r) => r[2])).toEqual(['nuevo', 'otro', '', ''])
  })

  it('si el pegado excede las filas, agrega filas nuevas', async () => {
    const wrapper = await mountInEdit()
    await clickAndPaste(wrapper, 3, 2, 'a\nb\nc')
    const grid = await savedGrid(wrapper)
    expect(grid).toHaveLength(6)
    expect(grid.slice(3).map((r) => r[2])).toEqual(['a', 'b', 'c'])
  })

  it('después de escribir en la celda, pegar también la reemplaza', async () => {
    const wrapper = await mountInEdit()
    const td = cellEl(wrapper, 0, 2)
    await td.trigger('mousedown')
    td.element.focus()
    td.element.textContent = 'tecleado'
    await td.trigger('input')
    await clickAndPaste(wrapper, 0, 2, 'X\nY')
    const grid = await savedGrid(wrapper)
    expect(grid.map((r) => r[2])).toEqual(['X', 'Y', '', ''])
    expect(column(wrapper, 2).slice(0, 2)).toEqual(['X', 'Y'])
  })
})
