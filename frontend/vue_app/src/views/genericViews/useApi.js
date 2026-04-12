import { ref } from 'vue';

export function useApi() {
  const loading = ref(false);
  const error = ref(null);

  /**
   * Ejecuta una función asíncrona manejando automáticamente
   * los estados de `loading` y `error`.
   *
   * @param {Function} asyncFunction - La función asíncrona que contiene la llamada a la API (ej: peticiones con axios).
   * @param {String} customErrorMessage - Mensaje personalizado opcional en caso de que la petición falle.
   */
  const execute = async (asyncFunction, customErrorMessage = null) => {
    loading.value = true;
    error.value = null;
    
    try {
      return await asyncFunction();
    } catch (err) {
      console.error('useApi Error:', err);
      
      if (customErrorMessage) {
        error.value = customErrorMessage;
      } else if (err.response && err.response.data) {
        error.value = `Error del servidor (${err.response.status}): ${JSON.stringify(err.response.data)}`;
      } else {
        error.value = `Error inesperado: ${err.message}`;
      }
      
      throw err; // Relanzar por si el componente padre necesita ejecutar lógica adicional en el catch
    } finally {
      loading.value = false;
    }
  };

  return { loading, error, execute };
}