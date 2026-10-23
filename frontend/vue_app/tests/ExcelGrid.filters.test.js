// Pruebas de uso del menú de filtros de ExcelGrid montando el componente real.
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ExcelGrid from '../src/components/ExcelGrid.vue'

beforeAll(() => {
  // jsdom no implementa canvas; ExcelGrid lo usa solo para medir el ancho de las columnas.
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
})

const headers = ['ID', 'Tag', 'Nombre']
const data = [
  ['1', 'A', 'Bomba 10'],
  ['2', 'B', 'Bomba 2'],
  ['3', '', 'Celda'],
]

const mountGrid = (props = {}) => mount(ExcelGrid, { props: { headers, data, ...props }, attachTo: document.body })

const openMenu = async (wrapper, col) => {
  await wrapper.findAll('.filter-icon')[col].trigger('click')
  await flushPromises()
}
const menuLabels = (wrapper) => wrapper.findAll('.menu-list label.menu-item').slice(1).map((l) => l.text())
const uncheck = async (wrapper, label) => {
  const item = wrapper.findAll('.menu-list label.menu-item').find((l) => l.text() === label)
  await item.find('input').trigger('change')
}
const accept = (wrapper) => wrapper.findAll('.menu-footer button').find((b) => b.text() === 'Aceptar').trigger('click')
const visibleRows = (wrapper) => wrapper.findAll('tbody tr').filter((tr) => !tr.find('.no-results').exists())

describe('ExcelGrid: filtro local', () => {
  it('muestra (Vacías) primero y orden natural', async () => {
    const wrapper = mountGrid()
    await openMenu(wrapper, 2)
    expect(menuLabels(wrapper)).toEqual(['Bomba 2', 'Bomba 10', 'Celda'])
    await openMenu(wrapper, 2) // cerrar
    await openMenu(wrapper, 1)
    expect(menuLabels(wrapper)).toEqual(['(Vacías)', 'A', 'B'])
  })

  it('desmarcar un valor oculta sus filas y marca la columna como filtrada', async () => {
    const wrapper = mountGrid()
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'A')
    await accept(wrapper)
    expect(visibleRows(wrapper)).toHaveLength(2)
    expect(wrapper.findAll('.filter-icon')[1].classes()).toContain('active')
  })

  it('"Borrar filtro de esta columna" restaura todas las filas', async () => {
    const wrapper = mountGrid()
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'A')
    await accept(wrapper)
    await openMenu(wrapper, 1)
    await wrapper.findAll('.menu-btn').find((b) => b.text().startsWith('Borrar filtro')).trigger('click')
    expect(visibleRows(wrapper)).toHaveLength(3)
  })

  it('con texto en Buscar, Aceptar filtra a las coincidencias (como Excel)', async () => {
    const wrapper = mountGrid()
    await openMenu(wrapper, 2)
    await wrapper.find('.menu-search-input').setValue('bomba')
    await accept(wrapper)
    expect(visibleRows(wrapper)).toHaveLength(2)
  })

  it('el orden se indica en el encabezado', async () => {
    const wrapper = mountGrid()
    await openMenu(wrapper, 2)
    await wrapper.findAll('.menu-btn').find((b) => b.text() === 'Ordenar Z a A').trigger('click')
    expect(wrapper.find('.sort-indicator').text()).toBe('▼')
  })
})

describe("ExcelGrid: filtro en servidor (filterScope='all')", () => {
  it('pide los valores al servidor y emite la especificación para la API', async () => {
    const loader = vi.fn().mockResolvedValue({ values: ['', 'A', 'B', 'C'], truncated: false })
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    expect(loader).toHaveBeenCalledWith(1, {}, '')
    expect(menuLabels(wrapper)).toEqual(['(Vacías)', 'A', 'B', 'C']) // C no está en la página, sí en la base
    await uncheck(wrapper, 'C')
    await accept(wrapper)
    const [filters, specs] = wrapper.emitted('filterChange')[0]
    expect(filters[1].sort()).toEqual(['', 'A', 'B'])
    expect(specs).toEqual({ 1: { not_in: ['C'], empty: false } })
  })

  it('envía los filtros de las otras columnas para el filtrado cruzado', async () => {
    const loader = vi.fn().mockResolvedValue({ values: ['A', 'B'], truncated: false })
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'B')
    await accept(wrapper)
    await openMenu(wrapper, 2)
    // Con dos valores y uno desmarcado se guarda como exclusión.
    expect(loader).toHaveBeenLastCalledWith(2, { 1: { not_in: ['B'], empty: false } }, '')
  })

  it('al reabrir una columna con filtro conserva lo marcado', async () => {
    const loader = vi.fn().mockResolvedValue({ values: ['A', 'B', 'C'], truncated: false })
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'B')
    await accept(wrapper)
    await openMenu(wrapper, 1)
    const checked = wrapper.findAll('.menu-list label.menu-item').slice(1).map((l) => l.find('input').element.checked)
    expect(checked).toEqual([true, false, true])
  })

  it('lista truncada: avisa y busca en el servidor', async () => {
    vi.useFakeTimers()
    const loader = vi.fn()
      .mockResolvedValueOnce({ values: ['A', 'B'], truncated: true })
      .mockResolvedValueOnce({ values: ['Z9'], truncated: false })
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    expect(wrapper.find('.menu-list').text()).toContain('Use "Buscar"')
    await wrapper.find('.menu-search-input').setValue('Z9')
    await vi.advanceTimersByTimeAsync(350)
    await flushPromises()
    expect(loader).toHaveBeenLastCalledWith(1, {}, 'Z9')
    expect(menuLabels(wrapper)).toEqual(['Z9'])
    await accept(wrapper)
    expect(wrapper.emitted('filterChange')[0][1]).toEqual({ 1: { in: ['Z9'], empty: false } })
    vi.useRealTimers()
  })

  it('si el servidor falla, avisa y usa los valores de la página', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const loader = vi.fn().mockRejectedValue(new Error('caída'))
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    expect(wrapper.find('.menu-error').exists()).toBe(true)
    expect(menuLabels(wrapper)).toEqual(['(Vacías)', 'A', 'B'])
  })

  it('clearFilters (expuesto) limpia filtros y orden sin emitir', async () => {
    const loader = vi.fn().mockResolvedValue({ values: ['A', 'B'], truncated: false })
    const wrapper = mountGrid({ serverSideFiltering: true, filterScope: 'all', filterValuesLoader: loader })
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'B')
    await accept(wrapper)
    wrapper.vm.clearFilters()
    await flushPromises()
    expect(wrapper.findAll('.filter-icon.active')).toHaveLength(0)
    expect(wrapper.emitted('filterChange')).toHaveLength(1)
  })
})

describe("ExcelGrid: grilla paginada en servidor con filtro de página (filterScope por defecto)", () => {
  // 25 filas de una página; el total en la base es mayor (simula Ensayos Courier Cobre).
  const page1 = Array.from({ length: 25 }, (_, i) => [String(i + 1), i % 2 ? 'S01' : 'S02', String(i)])
  const page2 = Array.from({ length: 25 }, (_, i) => [String(i + 26), i % 3 ? 'S01' : 'S03', String(i)])
  const props = (data) => ({
    data, serverSideFiltering: true, currentPage: 1, totalPages: 40, totalItems: 1000, pageSize: 25,
    filterValuesLoader: vi.fn(),
  })

  it('filtra solo dentro de las 25 filas cargadas, sin consultar al servidor', async () => {
    const wrapper = mountGrid(props(page1))
    await openMenu(wrapper, 1)
    expect(wrapper.props('filterValuesLoader')).not.toHaveBeenCalled()
    expect(menuLabels(wrapper)).toEqual(['S01', 'S02']) // solo valores de la página
    await uncheck(wrapper, 'S02')
    await accept(wrapper)
    expect(visibleRows(wrapper)).toHaveLength(12) // 12 de 25: nunca más que la página
    expect(wrapper.emitted('filterChange')).toBeUndefined() // no se recarga desde el servidor
    expect(wrapper.find('.page-info').text()).toContain('Filtro en esta página: 12 de 25')
  })

  it('al cambiar de página el filtro se aplica a las filas nuevas', async () => {
    const wrapper = mountGrid(props(page1))
    await openMenu(wrapper, 1)
    await uncheck(wrapper, 'S02') // excluir S02 -> en la página 2 aparece S03 y debe verse
    await accept(wrapper)
    await wrapper.setProps({ data: page2, currentPage: 2 })
    const tags = visibleRows(wrapper).map((tr) => tr.findAll('td')[1].text())
    expect(tags.length).toBeLessThanOrEqual(25)
    expect(tags).not.toContain('S02')
    expect(tags).toContain('S03')
  })

  it('el orden también es de la página: no recarga y reordena las 25 filas', async () => {
    const wrapper = mountGrid(props(page1))
    await openMenu(wrapper, 0)
    await wrapper.findAll('.menu-btn').find((b) => b.text() === 'Ordenar Z a A').trigger('click')
    expect(wrapper.emitted('sortChange')).toBeUndefined()
    const ids = visibleRows(wrapper).map((tr) => tr.findAll('td')[0].text())
    expect(ids).toHaveLength(25)
    expect(ids[0]).toBe('25') // orden numérico, no alfabético ('9' > '25' alfabéticamente)
  })
})
