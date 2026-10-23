// Pruebas de montaje de componentes y de la configuración de rutas.
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseTable from '../src/components/BaseTable.vue'
import router from '../src/router'

describe('BaseTable', () => {
  it('muestra encabezados capitalizados y una fila por elemento', () => {
    const wrapper = mount(BaseTable, {
      props: { title: 'Plantas', columns: ['tag', 'name'], items: [{ id: 1, tag: 'C1', name: 'Concentradora 1' }] },
    })
    expect(wrapper.find('h2').text()).toBe('Plantas')
    expect(wrapper.findAll('th').map((th) => th.text())).toEqual(['Tag', 'Name'])
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.text()).toContain('Concentradora 1')
  })

  it('sin datos muestra el mensaje ocupando todas las columnas', () => {
    const wrapper = mount(BaseTable, { props: { columns: ['a', 'b', 'c'] } })
    const cell = wrapper.find('td.no-data')
    expect(cell.text()).toBe('No hay datos disponibles')
    expect(cell.attributes('colspan')).toBe('3')
  })
})

describe('router', () => {
  const expected = [
    '/plants', '/areas', '/sistems', '/equipments', '/samples', '/assays', '/tasks', '/stasks', '/ctasks',
    '/weeklytasks', '/sampling', '/excel-test', '/calendario-grupos', '/users', '/userp', '/monthly-calendar',
  ]

  it('registra todas las vistas', () => {
    const paths = router.getRoutes().map((r) => r.path)
    for (const path of expected) expect(paths).toContain(path)
  })

  it('cada ruta resuelve a un componente que se puede cargar', async () => {
    for (const route of router.getRoutes()) {
      const loader = route.components?.default
      expect(loader, route.path).toBeTruthy()
      const mod = typeof loader === 'function' ? await loader() : loader
      expect(mod.default ?? mod, route.path).toBeTruthy()
    }
  })
})
