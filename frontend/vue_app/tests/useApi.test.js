// Pruebas del composable que centraliza los estados loading / error de las llamadas a la API.
import { describe, expect, it, vi } from 'vitest'
import { useApi } from '../src/composables/useApi'

describe('useApi', () => {
  it('activa loading durante la llamada y devuelve el resultado', async () => {
    const { loading, error, execute } = useApi()
    let loadingDuranteLaLlamada
    const result = await execute(async () => {
      loadingDuranteLaLlamada = loading.value
      return 42
    })
    expect(loadingDuranteLaLlamada).toBe(true)
    expect(result).toBe(42)
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('formatea el error del servidor y lo relanza', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { loading, error, execute } = useApi()
    const fallo = { response: { status: 400, data: { name: ['Requerido'] } } }
    await expect(execute(() => Promise.reject(fallo))).rejects.toBe(fallo)
    expect(error.value).toBe('Error del servidor (400): {"name":["Requerido"]}')
    expect(loading.value).toBe(false)
  })

  it('usa el mensaje personalizado si se indica', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { error, execute } = useApi()
    await expect(execute(() => Promise.reject(new Error('x')), 'No se pudo guardar')).rejects.toThrow()
    expect(error.value).toBe('No se pudo guardar')
  })

  it('errores sin respuesta del servidor (red caída)', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { error, execute } = useApi()
    await expect(execute(() => Promise.reject(new Error('Network Error')))).rejects.toThrow()
    expect(error.value).toBe('Error inesperado: Network Error')
  })

  it('limpia el error anterior al reintentar', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const { error, execute } = useApi()
    await execute(() => Promise.reject(new Error('x'))).catch(() => {})
    await execute(async () => 'ok')
    expect(error.value).toBeNull()
  })
})
