// Escenario reportado: 50 registros por página, filtrar por fecha y luego ordenar la columna Muestra
// (ascendente o descendente) hacía desaparecer los registros.
import { beforeAll, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ExcelGrid from '../src/components/ExcelGrid.vue'

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
})

const headers = ['ID', 'Fecha', 'Hora', 'Muestra', 'Cu']
// Columna Muestra tipo select (como en Ensayos): el valor es el id y se muestra el tag.
const sampleOptions = [
  { value: '15', label: 'C_01_S10' }, { value: '12', label: 'C_01_S2' }, { value: '13', label: 'C_01_S3' },
]
const columnsConfig = { 3: { type: 'select', options: sampleOptions } }
const fechas = ['2026-10-20', '2026-10-21', '2026-10-22']
const page = Array.from({ length: 50 }, (_, i) => [
  // Fecha y muestra varían de forma independiente: cada fecha tiene las tres muestras.
  String(1000 + i), fechas[i % 3], `0${i % 10}:00:00`, sampleOptions[Math.floor(i / 3) % 3].value, String((i % 7) / 10),
])

// Simula la vista: si la grilla pide ordenar al servidor, la vista recarga otra página distinta.
const mountLikeView = () => {
  const otherPage = page.map((r) => [String(Number(r[0]) + 5000), '2026-09-01', r[2], r[3], r[4]])
  const wrapper = mount(ExcelGrid, {
    props: {
      headers, data: page, columnsConfig, serverSideFiltering: true, currentPage: 1, totalPages: 30,
      totalItems: 1452, pageSize: 50,
      onSortChange: () => wrapper.setProps({ data: otherPage }),
    },
    attachTo: document.body,
  })
  return wrapper
}

const open = async (w, col) => { await w.findAll('.filter-icon')[col].trigger('click'); await flushPromises() }
const items = (w) => w.findAll('.filter-menu .menu-list label.menu-item').slice(1)
const rows = (w) => w.findAll('.excel-table tbody tr').filter((tr) => !tr.find('.no-results').exists())
const col = (w, c) => rows(w).map((tr) => tr.findAll('td')[c].text())

const filterOnlyDate = async (w, fecha) => {
  await open(w, 1)
  for (const item of items(w)) {
    if (item.text() !== fecha) await item.find('input').trigger('change')
  }
  await w.findAll('.filter-menu .menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
  await flushPromises()
}
const sort = async (w, c, label) => {
  await open(w, c)
  await w.findAll('.menu-btn').find((b) => b.text() === label).trigger('click')
  await flushPromises()
}

describe('ExcelGrid: filtrar por fecha y luego ordenar por muestra (página de 50)', () => {
  it('ascendente: los registros filtrados siguen visibles y ordenados por muestra', async () => {
    const w = mountLikeView()
    await filterOnlyDate(w, '2026-10-21')
    expect(rows(w)).toHaveLength(17)
    await sort(w, 3, 'Ordenar A a Z')
    expect(rows(w)).toHaveLength(17)
    expect(new Set(col(w, 1))).toEqual(new Set(['2026-10-21']))
    expect(w.emitted('sortChange')).toBeUndefined() // no se recarga otra página
  })

  it('descendente: igual, en orden inverso', async () => {
    const w = mountLikeView()
    await filterOnlyDate(w, '2026-10-20')
    const antes = new Set(col(w, 0))
    await sort(w, 3, 'Ordenar Z a A')
    expect(new Set(col(w, 0))).toEqual(antes)
  })

  it('ordena por la etiqueta de la muestra en orden natural (S2 < S3 < S10)', async () => {
    const w = mountLikeView()
    await sort(w, 3, 'Ordenar A a Z')
    const valores = rows(w).map((tr) => tr.findAll('td')[3].attributes('data-value'))
    const etiquetas = valores.map((v) => sampleOptions.find((o) => o.value === v).label)
    const primeraAparicion = [...new Set(etiquetas)]
    expect(primeraAparicion).toEqual(['C_01_S2', 'C_01_S3', 'C_01_S10'])
  })

  it('ordena fechas y horas correctamente (antes "2026-10-20" y "2026-10-22" se comparaban como 2026)', async () => {
    const w = mountLikeView()
    await sort(w, 1, 'Ordenar Z a A')
    const fechasVistas = col(w, 1)
    expect(fechasVistas[0]).toBe('2026-10-22')
    expect(fechasVistas[fechasVistas.length - 1]).toBe('2026-10-20')
  })
})

describe('ExcelGrid: orden por defecto de varios niveles (defaultSort)', () => {
  const mountDefault = async () => {
    const w = mount(ExcelGrid, {
      props: {
        headers, data: page, columnsConfig, serverSideFiltering: true, pageSize: 50,
        defaultSort: [{ colIndex: 1, direction: 'asc' }, { colIndex: 3, direction: 'asc' }],
      },
      attachTo: document.body,
    })
    await flushPromises()
    return w
  }
  const label = (v) => sampleOptions.find((o) => o.value === v).label
  const pares = (w) => rows(w).map((tr) => [tr.findAll('td')[1].text(), label(tr.findAll('td')[3].attributes('data-value'))])

  it('ordena por Fecha y dentro de cada fecha por Muestra en orden natural', async () => {
    const w = await mountDefault()
    const p = pares(w)
    expect(p[0]).toEqual(['2026-10-20', 'C_01_S2'])
    const esperado = [...p].sort((a, b) => a[0].localeCompare(b[0]) ||
      ['C_01_S2', 'C_01_S3', 'C_01_S10'].indexOf(a[1]) - ['C_01_S2', 'C_01_S3', 'C_01_S10'].indexOf(b[1]))
    expect(p).toEqual(esperado)
  })

  it('ordenar por otra columna la usa primero y mantiene el orden por defecto como desempate', async () => {
    const w = await mountDefault()
    await sort(w, 4, 'Ordenar Z a A') // Cu descendente
    const cu = rows(w).map((tr) => Number(tr.findAll('td')[4].text()))
    expect(cu).toEqual([...cu].sort((a, b) => b - a))
    await open(w, 4)
    await w.findAll('.menu-btn').find((b) => b.text().startsWith('Quitar orden')).trigger('click')
    expect(pares(w)[0]).toEqual(['2026-10-20', 'C_01_S2'])
  })

  it('editar una celda de una columna ordenada no mueve la fila hasta volver a ordenar', async () => {
    if (!('innerText' in HTMLElement.prototype)) {
      Object.defineProperty(HTMLElement.prototype, 'innerText', {
        get() { return this.textContent }, set(v) { this.textContent = v }, configurable: true,
      })
    }
    const w = await mountDefault()
    await w.findAll('button').find((b) => b.text() === 'Habilitar Edición').trigger('click')
    const firstId = rows(w)[0].findAll('td')[1].text() // con modo edición la primera <td> es el nº de fila
    const td = rows(w)[0].findAll('td')[2] // Fecha
    td.element.focus()
    const event = new Event('paste', { bubbles: true, cancelable: true })
    event.clipboardData = { getData: () => '2030-01-01' }
    td.element.dispatchEvent(event)
    await flushPromises()
    expect(rows(w)[0].findAll('td')[1].text()).toBe(firstId) // la fila sigue arriba
    expect(rows(w)[0].findAll('td')[2].text()).toBe('2030-01-01')
  })
})
