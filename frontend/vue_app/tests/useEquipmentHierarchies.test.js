// Pruebas del composable que traduce la jerarquía Planta > Área > Sistema > Equipo para la grilla.
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../src/api', () => ({ api: { get: vi.fn() } }))

import { api } from '../src/api'
import { useEquipmentHierarchies } from '../src/composables/useEquipmentHierarchies'

const catalogs = {
  'systems/': [{ id: 1, name: 'Analizadores' }, { id: 2, name: 'Bombas' }],
  'areas/': [{ id: 10, name: 'Flotación', plant: 100 }, { id: 11, name: 'Molienda', plant: 101 }],
  'plants/': [{ id: 100, name: 'Concentradora 1' }, { id: 101, name: 'Concentradora 2' }],
  'equipments/': [
    { id: 5, name: 'Courier', description: 'C5', area: 10, system: 1 },
    { id: 6, name: 'Bomba', area: 11, system: 2 },
  ],
}

let h

beforeEach(async () => {
  api.get.mockImplementation((url) => Promise.resolve({ data: { results: catalogs[url] } }))
  h = useEquipmentHierarchies()
  await h.loadDependencies()
})

describe('loadDependencies', () => {
  it('carga los cuatro catálogos con page_size alto', () => {
    expect(api.get).toHaveBeenCalledWith('plants/', { params: { page_size: 10000 } })
    expect(h.equipmentsList.value).toHaveLength(2)
    expect(h.plantsMap.value[100].name).toBe('Concentradora 1')
  })

  it('si la API falla no lanza error y deja las listas vacías', async () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    api.get.mockRejectedValue(new Error('caída'))
    const otro = useEquipmentHierarchies()
    await expect(otro.loadDependencies()).resolves.toBeUndefined()
    expect(otro.equipmentsList.value).toEqual([])
    spy.mockRestore()
  })
})

describe('getEquipmentHierarchyRow', () => {
  it('devuelve los nombres de la jerarquía de un equipo', () => {
    expect(h.getEquipmentHierarchyRow(5)).toEqual({
      plantName: 'Concentradora 1', areaName: 'Flotación', systemName: 'Analizadores',
      equipmentName: 'Courier', equipmentDesc: 'C5', equipmentId: 5,
    })
  })

  it('con un equipo desconocido devuelve textos vacíos', () => {
    expect(h.getEquipmentHierarchyRow(999).plantName).toBe('')
  })
})
