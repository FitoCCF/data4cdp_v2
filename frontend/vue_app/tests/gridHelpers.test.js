// Pruebas de las utilidades que convierten filas de ExcelGrid en el JSON que recibe la API.
import { describe, expect, it } from 'vitest'
import { buildPayloadFromRow, mapGridKeyToPayload, sanitizeValue } from '../src/utils/gridHelpers'

describe('sanitizeValue', () => {
  it('convierte vacíos en null', () => {
    expect(sanitizeValue('')).toBeNull()
    expect(sanitizeValue('   ')).toBeNull()
    expect(sanitizeValue(null)).toBeNull()
    expect(sanitizeValue(undefined)).toBeNull()
  })

  it('recorta espacios y conserva el texto', () => {
    expect(sanitizeValue('  C1 ')).toBe('C1')
  })

  it('cambia la coma decimal por punto solo en campos numéricos', () => {
    expect(sanitizeValue('0,84', true)).toBe('0.84')
    expect(sanitizeValue('Línea 1, norte', false)).toBe('Línea 1, norte')
  })

  it('no altera números ni el cero', () => {
    expect(sanitizeValue(0)).toBe(0)
    expect(sanitizeValue(12.5, true)).toBe(12.5)
  })
})

describe('mapGridKeyToPayload', () => {
  it('usa los campos de escritura de los serializers', () => {
    expect(mapGridKeyToPayload('task')).toBe('task_id')
    expect(mapGridKeyToPayload('estado')).toBe('estado_id')
    expect(mapGridKeyToPayload('sample')).toBe('sample_id')
  })

  it('envía user y group con su nombre real (AssaySerializer y UserSerializer)', () => {
    expect(mapGridKeyToPayload('user')).toBe('user')
    expect(mapGridKeyToPayload('group', ['id', 'nombre', 'group'])).toBe('group')
  })

  it('en la grilla de tareas programadas group se envía como group_id', () => {
    expect(mapGridKeyToPayload('group', ['id', 'task', 'group'])).toBe('group_id')
  })

  it('deja igual el resto de claves', () => {
    expect(mapGridKeyToPayload('chemical_id')).toBe('chemical_id')
  })
})

describe('buildPayloadFromRow', () => {
  it('arma el payload de un ensayo', () => {
    const colKeys = ['id', 'pCu', 'sample', 'user', 'meta_user']
    const row = ['15', ' 0,84 ', '3', '2', '']
    expect(buildPayloadFromRow(row, colKeys)).toEqual({
      id: '15', pCu: '0.84', sample_id: '3', user: '2', meta_user: null,
    })
  })

  it('omite las columnas de solo lectura con "__"', () => {
    const payload = buildPayloadFromRow(['1', 'Concentradora 1'], ['id', 'equipment__area__plant__name'])
    expect(payload).toEqual({ id: '1' })
  })
})
