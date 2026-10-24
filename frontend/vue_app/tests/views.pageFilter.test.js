// Prueba en TODAS las vistas paginadas en el servidor: con 25 registros por página, filtrar una columna
// solo afecta a esas 25 filas (el resultado es menor o igual a 25) y no se vuelve a pedir al servidor.
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

vi.mock('../src/api', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }))

import { api } from '../src/api'

const PAGE_SIZE = 25
const TOTAL = 1000 // muchos más registros que una página (como Ensayos de Courier Cobre)

// Muestras de un Courier (tags en distinto orden para probar el orden natural).
const SAMPLES = [
  { id: 15, tag: 'C_01_S10', name: 'Cola', equipment: 2 },
  { id: 12, tag: 'C_01_S2', name: 'Alim', equipment: 2 },
  { id: 13, tag: 'C_01_S3', name: 'Conc', equipment: 2 },
]

// Fila genérica con los campos que usan las vistas; el id es distinto en cada fila.
const makeRow = (id) => ({
  id, tag: id % 2 ? 'T1' : 'T2', name: `Nombre ${id % 3}`, description: '', nombre: 'Ana', apellido: 'P',
  email: `u${id}@x.com`, rol: '', group: null, plant: 1, system: 1, area: 1, equipment: 1,
  task_catalog: 1, duration: 1, workers: 1, frequency: 'Mensual', start_date: '2026-01-01', procedure: '',
  turn: 'A', task: null, corrective_task: null, estado: { id: 2, estado_nombre: 'P' }, year: 2026, week: 10,
  day: 'Lunes', date: ['2026-10-22', '2026-10-20', '2026-10-21', '2026-10-19'][Math.floor(id / 2) % 4], priority: 1, comments: '', rescheduled: false, root_cause: '',
  creation_date: '2026-03-02', created_by_user: 1, turno: 'A', time: '08:00:00', instance: id,
  sample: SAMPLES[id % 3], chemical_id: 26000 + id, user: null,
})

const listCalls = (endpoint) =>
  api.get.mock.calls.filter(([url, cfg]) => url.replace(/^\//, '') === `${endpoint}/` && cfg?.params?.page)

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
  window.alert = () => {}
  // jsdom no implementa innerText (el navegador sí); ExcelGrid lo usa para leer el texto de la celda.
  if (!('innerText' in HTMLElement.prototype)) {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() { return this.textContent },
      set(v) { this.textContent = v },
      configurable: true,
    })
  }
})

beforeEach(() => {
  api.get.mockReset()
  api.get.mockImplementation((url, cfg = {}) => {
    const params = cfg.params || {}
    if (url.includes('grid-values')) return Promise.resolve({ data: { values: [], truncated: false } })
    if (url.includes('weekly-tasks')) return Promise.resolve({ data: { tasks: [], calendar: [] } })
    if (url.replace(/^\//, '') === 'samples/' && params.equipment) {
      return Promise.resolve({ data: { count: SAMPLES.length, results: SAMPLES } })
    }
    const size = Math.min(Number(params.page_size) || PAGE_SIZE, PAGE_SIZE)
    const page = Number(params.page) || 1
    const results = Array.from({ length: size }, (_, i) => makeRow((page - 1) * size + i + 1))
    return Promise.resolve({ data: { count: TOTAL, next: null, previous: null, results } })
  })
})

const VIEWS = [
  ['Plantas', 'PlantsView.vue', 'plants'],
  ['Sistemas', 'SystemsView.vue', 'systems'],
  ['Áreas', 'AreasView.vue', 'areas'],
  ['Equipos', 'EquipmentsView.vue', 'equipments'],
  ['Muestras', 'SamplesView.vue', 'samples'],
  ['Usuarios', 'UsersView.vue', 'users'],
  ['Grupos', 'UserPsView.vue', 'userp'],
  ['Tareas', 'TasksView.vue', 'tasks'],
  ['Tareas programadas', 'STasksViews.vue', 'taskp'],
  ['Tareas correctivas', 'CTasksView.vue', 'correctivetasks'],
  ['Ensayos (Courier)', 'AssaysView.vue', 'assays'],
]

const visibleDataRows = (wrapper) =>
  wrapper.findAll('.excel-table tbody tr').filter((tr) => !tr.find('.no-results').exists())

const mountView = async (file, endpoint) => {
  const View = (await import(`../src/views/genericViews/${file}`)).default
  const wrapper = mount(View, { attachTo: document.body })
  await flushPromises()
  if (endpoint === 'assays') {
    // En Ensayos la grilla aparece al elegir el analizador (Courier).
    await wrapper.find('select').setValue('2')
    await flushPromises()
  }
  return wrapper
}

describe.each(VIEWS)('Vista %s', (_, file, endpoint) => {
  it('pegar varias celdas desde Excel empieza en la celda donde se hizo clic', async () => {
    const wrapper = await mountView(file, endpoint)
    await wrapper.findAll('.excel-container button').find((b) => b.text() === 'Habilitar Edición').trigger('click')
    await flushPromises()

    // Primera celda editable de texto (no ID ni desplegable) de la primera fila.
    const rows = () => wrapper.findAll('.excel-table tbody tr')
    const firstRowCells = rows()[0].findAll('td')
    const col = firstRowCells.findIndex((td) => td.attributes('contenteditable') === 'true')
    expect(col).toBeGreaterThan(0)

    const td = firstRowCells[col]
    await td.trigger('mousedown')
    td.element.focus()
    expect(document.activeElement).toBe(td.element)
    const event = new Event('paste', { bubbles: true, cancelable: true })
    event.clipboardData = { getData: () => 'P1\r\nP2\r\nP3\r\n' } // tres celdas copiadas de Excel
    td.element.dispatchEvent(event)
    await flushPromises()

    const pasted = rows().slice(0, 4).map((tr) => tr.findAll('td')[col].text())
    expect(pasted.slice(0, 3)).toEqual(['P1', 'P2', 'P3']) // la celda clicada no queda vacía
    expect(pasted[3]).not.toBe('P1') // el valor no se corre a la fila siguiente
    wrapper.unmount()
  })

  it('el filtro de columna actúa solo sobre las 25 filas de la página', async () => {
    const wrapper = await mountView(file, endpoint)

    expect(visibleDataRows(wrapper)).toHaveLength(PAGE_SIZE)
    const requestsBefore = listCalls(endpoint).length
    expect(requestsBefore).toBeGreaterThan(0)

    // Abrir el filtro de la columna ID: solo debe ofrecer los 25 IDs de la página.
    await wrapper.findAll('.filter-icon')[0].trigger('click')
    await flushPromises()
    const items = wrapper.findAll('.filter-menu .menu-list label.menu-item').slice(1)
    expect(items).toHaveLength(PAGE_SIZE)

    // Desmarcar dos IDs y aceptar.
    await items[0].find('input').trigger('change')
    await items[1].find('input').trigger('change')
    await wrapper.findAll('.filter-menu .menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
    await flushPromises()

    expect(visibleDataRows(wrapper)).toHaveLength(PAGE_SIZE - 2)
    expect(listCalls(endpoint).length).toBe(requestsBefore) // no se pidió otra página filtrada al servidor
    expect(api.get.mock.calls.some(([u]) => u.includes('grid-values'))).toBe(false)
    expect(wrapper.find('.page-info').text()).toContain(`Filtro en esta página: ${PAGE_SIZE - 2} de ${PAGE_SIZE}`)
    wrapper.unmount()
  })
})

const clickMenu = async (wrapper, col) => {
  await wrapper.findAll('.filter-icon')[col].trigger('click')
  await flushPromises()
}

describe.each(VIEWS)('Vista %s: filtrar y luego ordenar', (_, file, endpoint) => {
  it.each([['Ordenar A a Z'], ['Ordenar Z a A']])('%s en cada columna no hace desaparecer los registros filtrados', async (sortLabel) => {
    const wrapper = await mountView(file, endpoint)
    const headerCount = wrapper.findAll('.filter-icon').length

    // Filtro: quitar dos IDs de la página.
    await clickMenu(wrapper, 0)
    const items = wrapper.findAll('.filter-menu .menu-list label.menu-item').slice(1)
    await items[0].find('input').trigger('change')
    await items[1].find('input').trigger('change')
    await wrapper.findAll('.filter-menu .menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
    await flushPromises()
    const ids = new Set(visibleDataRows(wrapper).map((tr) => tr.findAll('td')[0].text()))
    expect(ids.size).toBe(PAGE_SIZE - 2)
    const requests = api.get.mock.calls.length

    // Ordenar por cada columna (incluida Muestra en Ensayos): siempre los mismos 23 registros.
    for (let col = 0; col < headerCount; col++) {
      await clickMenu(wrapper, col)
      await wrapper.findAll('.menu-btn').find((b) => b.text() === sortLabel).trigger('click')
      await flushPromises()
      const after = new Set(visibleDataRows(wrapper).map((tr) => tr.findAll('td')[0].text()))
      expect(after, `columna ${col}`).toEqual(ids)
    }
    expect(api.get.mock.calls.length).toBe(requests) // ordenar no pidió otra página al servidor
    wrapper.unmount()
  })
})

describe('Vista Ensayos: escenario reportado (filtrar por fecha y ordenar por Muestra)', () => {
  it.each([['Ordenar A a Z'], ['Ordenar Z a A']])('%s', async (sortLabel) => {
    const wrapper = await mountView('AssaysView.vue', 'assays')
    const headers = wrapper.findAll('.excel-table thead th .header-text').map((h) => h.text())
    const fechaCol = headers.findIndex((h) => /fecha/i.test(h))
    const muestraCol = headers.findIndex((h) => /muestra/i.test(h))
    expect(fechaCol).toBeGreaterThanOrEqual(0)
    expect(muestraCol).toBeGreaterThanOrEqual(0)

    await clickMenu(wrapper, fechaCol)
    for (const item of wrapper.findAll('.filter-menu .menu-list label.menu-item').slice(1)) {
      if (item.text() !== '2026-10-21') await item.find('input').trigger('change')
    }
    await wrapper.findAll('.filter-menu .menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
    await flushPromises()
    const filtradas = visibleDataRows(wrapper).length
    expect(filtradas).toBeGreaterThan(0)
    expect(filtradas).toBeLessThan(PAGE_SIZE)

    await clickMenu(wrapper, muestraCol)
    await wrapper.findAll('.menu-btn').find((b) => b.text() === sortLabel).trigger('click')
    await flushPromises()
    expect(visibleDataRows(wrapper)).toHaveLength(filtradas)
    wrapper.unmount()
  })
})

describe('Vista Ensayos: Peso Prod. y % Sol calculados', () => {
  it('al pegar Tara, Peso Total y Peso Seco se calculan y se envían al guardar', async () => {
    api.put.mockResolvedValue({ data: {} })
    const wrapper = await mountView('AssaysView.vue', 'assays')
    await wrapper.findAll('.excel-container button').find((b) => b.text() === 'Habilitar Edición').trigger('click')
    await flushPromises()

    const headers = wrapper.findAll('.excel-table thead th .header-text').map((h) => h.text())
    const col = (name) => headers.indexOf(name)
    const td = (r, c) => wrapper.findAll('.excel-table tbody tr')[r].findAll('td')[c + 1] // +1: columna de nº de fila
    expect(td(0, col('Peso Prod.')).attributes('contenteditable')).toBe('true') // calculado pero editable

    const tara = td(0, col('Tara'))
    tara.element.focus()
    const event = new Event('paste', { bubbles: true, cancelable: true })
    event.clipboardData = { getData: () => '114.5\t1,174.5\t30\r\n' } // Tara, Peso Total, Peso Seco
    tara.element.dispatchEvent(event)
    await flushPromises()

    expect(td(0, col('Peso Prod.')).text()).toBe('1060')
    expect(td(0, col('% Sol')).text()).toBe('2.83')

    await wrapper.findAll('button').find((b) => b.text() === 'Guardar Cambios').trigger('click')
    await wrapper.findAll('button').find((b) => b.text() === 'Sí, Guardar').trigger('click')
    await flushPromises()
    // Se busca el PUT de la fila editada (la primera visible), sin suponer el orden de envío.
    const editedId = td(0, 0).text()
    const [, payload] = api.put.mock.calls.find(([url]) => url === `assays/${editedId}/`)
    expect(payload).toMatchObject({ tara: '114.5', tweight: '1174.5', dweight: '30', pweight: 1060, pSol: 2.83 })
    wrapper.unmount()
  })
})

describe('Vista Ensayos: orden por defecto Fecha (más reciente primero) y, dentro de cada fecha, Muestra', () => {
  it('al filtrar 3 fechas, las filas quedan agrupadas por fecha y ordenadas por muestra (S2, S3, S10)', async () => {
    const wrapper = await mountView('AssaysView.vue', 'assays')
    const headers = wrapper.findAll('.excel-table thead th .header-text').map((h) => h.text())
    const fechaCol = headers.indexOf('Fecha')
    const muestraCol = headers.indexOf('Muestra')
    const horaCol = headers.indexOf('Hora')

    // Filtrar 3 de las 4 fechas de la página.
    await clickMenu(wrapper, fechaCol)
    const quitar = wrapper.findAll('.filter-menu .menu-list label.menu-item').slice(1).find((l) => l.text() === '2026-10-19')
    await quitar.find('input').trigger('change')
    await wrapper.findAll('.filter-menu .menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
    await flushPromises()

    const filas = visibleDataRows(wrapper).map((tr) => {
      const tds = tr.findAll('td')
      return { fecha: tds[fechaCol].text(), muestra: tds[muestraCol].text().split(' - ')[0], hora: tds[horaCol].text() }
    })
    expect(new Set(filas.map((f) => f.fecha))).toEqual(new Set(['2026-10-20', '2026-10-21', '2026-10-22']))
    const orden = { C_01_S2: 0, C_01_S3: 1, C_01_S10: 2 }
    for (let i = 1; i < filas.length; i++) {
      const a = filas[i - 1]
      const b = filas[i]
      expect(a.fecha >= b.fecha, `fila ${i}: fechas ${a.fecha} < ${b.fecha}`).toBe(true)
      if (a.fecha === b.fecha) {
        expect(orden[a.muestra] <= orden[b.muestra], `fila ${i}: ${a.muestra} después de ${b.muestra}`).toBe(true)
      }
    }
    // El encabezado indica el orden por defecto
    expect(wrapper.findAll('.excel-table thead th')[fechaCol].find('.sort-default').exists()).toBe(true)
    wrapper.unmount()
  })
})
