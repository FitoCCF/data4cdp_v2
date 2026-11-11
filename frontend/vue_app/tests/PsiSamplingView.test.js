// Vista de Muestreo del PSI de Molienda C1 (formato CON-PSG-CPR-FM.003).
// Usa el mismo estilo y la misma cabecera que la vista de Courier (SamplingView.vue); lo propio del
// PSI son los textos del formato y las 28 columnas. Se comprueba eso, el aviso cuando el PSI no
// tiene muestras, y el mapeo de la grilla a /api/assayspsi/.
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

vi.mock('../src/api', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() } }))

import { api } from '../src/api'
import PsiSamplingView from '../src/views/genericViews/PsiSamplingView.vue'
import ExcelGrid from '../src/components/ExcelGrid.vue'

// Equipos como están hoy en la base: cuatro PSI que se distinguen solo por la descripción.
const EQUIPOS = [
  { id: 3, name: 'PSI', description: 'Molienda C1', area: 1, system: 1 },
  { id: 4, name: 'PSI', description: 'Remolienda C1', area: 2, system: 1 },
  { id: 7, name: 'PSI', description: 'Molienda C2', area: 3, system: 1 },
  { id: 2, name: 'Courier', description: 'Molibdeno C1', area: 4, system: 1 },
]
// Las secciones de molienda que se muestrean en este formato, desordenadas a propósito.
const MUESTRAS_C1 = [
  { id: 52, tag: 'S5', name: 'Sección 5', equipment: 3 },
  { id: 50, tag: 'S3', name: 'Sección 3', equipment: 3 },
  { id: 51, tag: 'S4', name: 'Sección 4', equipment: 3 },
]
const USUARIOS = [{ id: 9, nombre: 'Ana', apellido: 'Pérez' }]

let alertas = []
let muestras = MUESTRAS_C1
let equipos = EQUIPOS

beforeAll(() => {
  HTMLCanvasElement.prototype.getContext = () => ({ font: '', measureText: (t) => ({ width: String(t).length * 7 }) })
  if (!('innerText' in HTMLElement.prototype)) {
    Object.defineProperty(HTMLElement.prototype, 'innerText', {
      get() { return this.textContent }, set(v) { this.textContent = v }, configurable: true,
    })
  }
})

beforeEach(() => {
  alertas = []
  muestras = MUESTRAS_C1
  equipos = EQUIPOS
  window.alert = (msg) => alertas.push(String(msg))
  api.get.mockReset()
  api.post.mockReset()
  api.put.mockReset()
  api.get.mockImplementation((url) => {
    const ruta = url.replace(/^\//, '')
    if (ruta.includes('grid-values')) return Promise.resolve({ data: { values: [], truncated: false } })
    if (ruta === 'equipments/') return Promise.resolve({ data: { count: equipos.length, results: equipos } })
    if (ruta === 'samples/') return Promise.resolve({ data: { count: muestras.length, results: muestras } })
    if (ruta === 'users/') return Promise.resolve({ data: { count: USUARIOS.length, results: USUARIOS } })
    return Promise.resolve({ data: { count: 0, next: null, previous: null, results: [] } })
  })
  api.post.mockResolvedValue({ data: { id: 1 } })
  api.put.mockResolvedValue({ data: { id: 1 } })
})

const montar = async () => {
  const wrapper = mount(PsiSamplingView, { attachTo: document.body })
  await flushPromises()
  return wrapper
}

describe('Vista Muestreo PSI: cabecera del formato oficial', () => {
  it('reproduce los textos fijos del FM.003 de Molienda C1', async () => {
    const texto = (await montar()).text()
    expect(texto).toContain('CON-PSG-CPR-FM.003')
    expect(texto).toContain('FORMATO DE MUESTREO DE CALIBRACIÓN DE PSI')
    expect(texto).toContain('PSI MOLIENDA NORTE 300i C1')
    expect(texto).toContain('Toquepala')
    expect(texto).toContain('Concentradora')
    expect(texto).toContain('Control de Procesos')
    expect(texto).toContain('FECHA DE MUESTREO:')
    expect(texto).toContain('ENVIADO POR:')
    expect(texto).toContain('OPERADOR DE METALURGIA:')
  })

  it('arma la cabecera con las mismas clases que la vista de Courier', async () => {
    const w = await montar()
    // Si estas clases cambian, el estilo deja de ser el mismo que el del formato de Courier.
    for (const clase of [
      '.assays-view', '.report-toolbar', '.report-wrapper', '.report-table', '.row-header-top',
      '.logo-cell', '.title-cell', '.code-cell', '.inner-table', '.meta-table', '.right-logo-cell',
      '.label-cell-wide', '.input-cell', '.table-container',
    ]) {
      expect(w.find(clase).exists(), clase).toBe(true)
    }
    // Los dos logos corporativos del formato.
    expect(w.findAll('.report-table img')).toHaveLength(2)
  })

  it('no hay selector de equipo: el formato es solo del PSI de Molienda C1', async () => {
    const w = await montar()
    // Los únicos desplegables de la cabecera son "enviado por" y "operador de metalurgia".
    const opciones = w.findAll('.report-table select')
      .flatMap((s) => s.findAll('option').map((o) => o.text()))
    expect(opciones.some((o) => o.includes('PSI'))).toBe(false)
    expect(opciones.some((o) => o.includes('Courier'))).toBe(false)
  })

  it('avisa si el equipo del formato no existe en la base', async () => {
    equipos = [{ id: 2, name: 'Courier', description: 'Molibdeno C1' }]
    const w = await montar()
    expect(w.text()).toContain('No se encontró el equipo')
  })
})

describe('Vista Muestreo PSI: columnas del formato', () => {
  it('tiene las 28 columnas del Excel con sus textos, en los tres bloques', async () => {
    const grid = (await montar()).findComponent(ExcelGrid)

    // Las 28 columnas del formato (A..AB) más 'ID DB', que va oculta.
    expect(grid.props('headers')).toHaveLength(29)
    // Los pesos parciales van cortos porque 'PESO PARCIAL ... (gr)' pasó al grupo de cabecera:
    // ExcelGrid dimensiona cada columna por el largo de su encabezado.
    expect(grid.props('headers').slice(1, 13)).toEqual([
      'MUESTRA', 'SECCIÓN', 'HORA', 'TARA', 'PESO TOTAL', 'PESO SECO', '% SÓLIDOS',
      'M+48', 'M+65', 'M+100', 'M+150', 'M+200',
    ])
    expect(grid.props('headers').slice(13, 24)).toEqual([
      'ID', 'AVE', 'SD', 'Density', '%SOL', '%M+48', '%M+65', '%M+100', '%M+150', '%M+200', 'P80',
    ])
    expect(grid.props('headers').slice(24)).toEqual([
      '%M+48 LAB.', '%M+65 LAB.', '%M+100 LAB.', '%M+150 LAB.', '%M+200 LAB.',
    ])
  })

  it('los bloques de la fila de grupos cubren todas las columnas visibles', async () => {
    const grupos = (await montar()).findComponent(ExcelGrid).props('headerGroups')

    expect(grupos.map((g) => g.label)).toEqual([
      '', 'PESO PARCIAL (gr)', 'DATOS PSI AL TOMAR MUESTRA', 'LABORATORIO',
    ])
    // Suman 28 y no 29 porque 'ID DB' va oculta por CSS, igual que en el formato de Courier.
    expect(grupos.reduce((suma, g) => suma + g.colspan, 0)).toBe(28)
    // 'PESO PARCIAL (gr)' tiene que caer justo sobre M+48..M+200 (columnas 8 a 12).
    expect(grupos[0].colspan).toBe(7)
    expect(grupos[1].colspan).toBe(5)
  })

  it('% SÓLIDOS es una columna calculada y editable', async () => {
    const formula = (await montar()).findComponent(ExcelGrid).props('columnsConfig')[7].formula

    expect(formula.editable).toBe(true)
    const num = (col) => ({ 4: 114.5, 5: 1035.5, 6: 300 }[col] ?? null)
    expect(formula.compute(num)).toBe(32.57) // 300 / (1035.5 − 114.5) × 100
  })
})

describe('Vista Muestreo PSI: muestras del equipo', () => {
  it('la columna SECCIÓN ofrece las secciones de Molienda C1 ordenadas', async () => {
    const w = await montar()

    expect(w.text()).not.toContain('no tiene muestras registradas')
    expect(w.findComponent(ExcelGrid).props('columnsConfig')[2].options).toEqual([
      { value: 50, label: 'Sección 3' },
      { value: 51, label: 'Sección 4' },
      { value: 52, label: 'Sección 5' },
    ])
  })

  it('avisa cuando el PSI no tiene muestras cargadas', async () => {
    muestras = [{ id: 60, tag: 'L1', name: 'Línea 1', equipment: 7 }] // son de otro PSI
    const w = await montar()

    expect(w.text()).toContain('no tiene muestras registradas')
    expect(w.findComponent(ExcelGrid).props('columnsConfig')[2].options).toEqual([])
  })
})

describe('Vista Muestreo PSI: guardado', () => {
  // Una fila del formato con los valores reales de la hoja C1_PSI_MOLIENDA.
  const fila = (seccion = 50) => [
    '', 'A', seccion, '09:26', 114.5, 1035.5, 300, 32.57,
    7.62, 19.6, 29.81, 39.45, 48.71,
    1622, 322.75, 106.7, 1.79, 35.91,
    7.62, 19.6, 29.81, 39.45, 48.71, 197.76,
    '', '', '', '', '',
  ]

  it('una fila nueva se manda a assayspsi/ con sample_id, turn y la cabecera', async () => {
    const w = await montar()
    w.findComponent(ExcelGrid).vm.$emit('save', [fila()])
    await flushPromises()

    expect(api.post).toHaveBeenCalledTimes(1)
    const [url, payload] = api.post.mock.calls[0]
    expect(url).toBe('assayspsi/')
    expect(payload.sample_id).toBe(50)   // SECCIÓN -> works4cdp_sample
    expect(payload.turn).toBe('A')       // MUESTRA -> la ronda A/B/C
    expect(payload.instance).toBe(1622)  // ID propio del analizador
    expect(payload.psolid).toBe(32.57)
    expect(payload.P80).toBe(197.76)
    expect(payload.pP48).toBeNull()      // el laboratorio llega después
    expect(payload.date).toBeTruthy()
    expect(payload).not.toHaveProperty('id')
  })

  it('una fila con id se actualiza con PUT en vez de crear otra', async () => {
    const w = await montar()
    const existente = fila()
    existente[0] = 77
    w.findComponent(ExcelGrid).vm.$emit('save', [existente])
    await flushPromises()

    expect(api.post).not.toHaveBeenCalled()
    expect(api.put).toHaveBeenCalledWith('assayspsi/77/', expect.objectContaining({ id: 77 }))
  })

  it('se rechaza una fila sin SECCIÓN: sin muestra no pertenecería a ningún PSI', async () => {
    const w = await montar()
    w.findComponent(ExcelGrid).vm.$emit('save', [fila(''), fila(50)])
    await flushPromises()

    expect(api.post).not.toHaveBeenCalled()
    expect(alertas.join('\n')).toContain('Falta la SECCIÓN en las filas: 1')
  })

  it('solo pide los ensayos del PSI de Molienda C1', async () => {
    await montar()
    const consultas = api.get.mock.calls.filter(([url]) => url.replace(/^\//, '') === 'assayspsi/')
    expect(consultas).toHaveLength(1)
    expect(consultas[0][1].params.sample__equipment).toBe(3)
  })
})
