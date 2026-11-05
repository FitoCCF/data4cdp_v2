"""
Punto único de cambio de estado de las tareas programadas (TaskP).

Por qué existe: el cambio de estado entraba por dos caminos distintos.
  - `WeeklyTaskView.post` hacía `TaskP.objects.filter(id=...).update(estado_id=...)`. Un `.update()`
    de queryset no ejecuta `Model.save()`, así que no disparaba señales, no llenaba
    `completion_date` y no tocaba `updated_at`. Y es justamente el camino por el que el operador
    marca las tareas en la vista semanal.
  - El PATCH del grid (`TaskPViewSet`) sí pasa por el serializer y por `save()`.

Centralizar acá deja una sola definición de "la tarea pasó a realizada", que es lo que después lee
el sincronizador hacia la lista de SharePoint que se edita desde Power Apps.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

from django.db import transaction
from django.utils import timezone

from works4cdp.models import Estado, TaskP, estado_es_realizado

logger = logging.getLogger(__name__)

class EstadoInvalido(ValueError):
    """Se pidió un estado_id que no existe en works4cdp_estado."""


def es_realizado(estado: Estado) -> bool:
    """True si ese Estado es 'realizado'. La regla vive en models.estado_es_realizado."""
    return estado_es_realizado(estado.estado_nombre)


def _normalizar(updates: Iterable[Dict[str, Any]]) -> List[Dict[str, int]]:
    """Valida la forma de cada item y convierte los ids a entero (llegan como texto del frontend)."""
    normalizados = []
    for item in updates:
        if not isinstance(item, dict) or 'id' not in item or 'estado_id' not in item:
            raise ValueError("Cada elemento requiere 'id' y 'estado_id'")
        try:
            normalizados.append({'id': int(item['id']), 'estado_id': int(item['estado_id'])})
        except (TypeError, ValueError):
            raise ValueError("'id' y 'estado_id' deben ser enteros")
    return normalizados


@transaction.atomic
def aplicar_cambios_estado(updates: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Aplica cambios de estado en bloque. Todo o nada: se valida antes de escribir.

    Devuelve un resumen con las tareas que pasaron a R, que son las que el sincronizador tiene que
    publicar en la lista de SharePoint.
    """
    normalizados = _normalizar(updates)
    if not normalizados:
        return {'cambiadas': 0, 'sin_cambio': 0, 'no_encontradas': [], 'realizadas': []}

    # Un estado_id inexistente antes reventaba con 500 por violación de clave foránea.
    estados = Estado.objects.in_bulk()
    invalidos = sorted({i['estado_id'] for i in normalizados} - set(estados))
    if invalidos:
        raise EstadoInvalido(f"estado_id inexistente: {invalidos}")

    ids = [i['id'] for i in normalizados]
    # select_for_update evita que dos operadores marcando la misma semana se pisen entre sí.
    tareas = TaskP.objects.select_for_update().select_related('estado').in_bulk(ids)
    no_encontradas = sorted(set(ids) - set(tareas))

    cambiadas, sin_cambio, realizadas = 0, 0, []
    for item in normalizados:
        tarea = tareas.get(item['id'])
        if tarea is None:
            continue
        nuevo = estados[item['estado_id']]
        if tarea.estado_id == nuevo.id:
            sin_cambio += 1
            continue

        tarea.estado = nuevo
        campos = ['estado', 'updated_at']
        if es_realizado(nuevo):
            # En un P -> R real se registra el momento del cambio. Se sobrescribe a propósito:
            # si la tarea ya traía fecha de una marcación anterior que se deshizo, vale la nueva.
            tarea.completion_date = timezone.now()
            campos.append('completion_date')
            realizadas.append(tarea.id)
        # Al salir de R NO se borra completion_date: queda como señal de que esta tarea llegó a
        # reportarse realizada y de que ya existe (o debe existir) un item en la lista externa, que
        # hay que corregir al estado actual en vez de dejarlo desactualizado.
        tarea.save(update_fields=campos)
        cambiadas += 1

    resumen = {
        'cambiadas': cambiadas,
        'sin_cambio': sin_cambio,
        'no_encontradas': no_encontradas,
        'realizadas': realizadas,
    }
    if no_encontradas:
        logger.warning("Cambio de estado con ids inexistentes: %s", no_encontradas)
    logger.info("Cambios de estado aplicados: %s", resumen)
    return resumen
