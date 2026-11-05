/**
 * Mensaje de error de borrado, legible para el usuario.
 *
 * Desde que Equipment.system, Equipment.area y Task.equipment son PROTECT, el backend rechaza a
 * propósito el borrado de un sistema, un área o un equipo del que todavía cuelgan registros, y
 * responde HTTP 409 con `{ error, bloqueado_por, detalle }` (ver ProtectedDeleteMixin en views.py).
 * Antes eso llegaba como un error genérico y el usuario no tenía forma de saber qué lo frenó.
 */
export function mensajeErrorBorrado(err, fallback = 'Error al eliminar las filas.') {
  const respuesta = err?.response;
  if (!respuesta) return fallback;

  if (respuesta.status === 409) {
    const datos = respuesta.data || {};
    const bloqueantes = Array.isArray(datos.bloqueado_por) ? datos.bloqueado_por.join(', ') : '';
    return [
      datos.error || 'No se puede eliminar: hay registros que dependen de este elemento.',
      bloqueantes ? `\nLo bloquean: ${bloqueantes}.` : '',
      '\n\nReasigná o eliminá primero esos registros.',
    ].join('');
  }

  const detalle = respuesta.data?.error || respuesta.data?.detail;
  return detalle ? `${fallback}\n\n${detalle}` : fallback;
}
