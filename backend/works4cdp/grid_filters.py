"""
Filtros y orden genéricos para las grillas del frontend (ExcelGrid).

Por qué existe:
Antes cada vista armaba `campo__in=a,b` y `campo__isnull=True`, y la API solo atendía los campos
listados a mano en `filterset_fields`. Las pruebas mostraron que eso fallaba en varios casos:
- Columnas fuera de `filterset_fields` (p. ej. pCu, chemical_id, day, estado_id): el filtro se ignoraba.
- "(Vacías)" sola enviaba `campo__in=` y django-filter lo descartaba: no filtraba nada.
- "(Vacías)" + valores enviaba `__in` y `__isnull` a la vez y se combinaban con AND: 0 resultados.
- Los textos vacíos se guardan a veces como '' y a veces como NULL: `__isnull` solo encontraba los NULL.
- Un valor con coma se partía en dos al usar `campo__in=a,b`.

Este módulo recibe un único parámetro JSON y lo traduce a consultas correctas para cualquier campo
del modelo (más rutas relacionadas declaradas por cada ViewSet):

    ?grid_filters={"tag": {"in": ["C1", "C2"], "empty": true},
                   "pCu": {"not_in": ["0.5"]}}

- "in": la fila pasa si el valor está en la lista (o es vacío, si "empty" es true).
- "not_in": la fila pasa si el valor NO está en la lista (y no es vacío, si "empty" es true).
  Se usa cuando el usuario desmarca pocos valores de muchos: la URL queda corta (escalabilidad).
"""
import json

from django.core.exceptions import FieldDoesNotExist, ValidationError as DjangoValidationError
from django.db import models
from django.db.models import Q
from rest_framework import filters
from rest_framework.exceptions import ValidationError

GRID_FILTERS_PARAM = 'grid_filters'
TEXT_FIELD_TYPES = (models.CharField, models.TextField)


def resolve_field(model, path):
    """
    Devuelve el campo de modelo final de una ruta tipo 'equipment__area__plant__name'.
    Acepta también el nombre de columna de una FK ('task_id') y lo trata como la FK ('task').
    Lanza FieldDoesNotExist si la ruta no existe.
    """
    current_model = model
    field = None
    parts = path.split('__')
    for index, part in enumerate(parts):
        try:
            field = current_model._meta.get_field(part)
        except FieldDoesNotExist:
            # 'task_id' -> campo 'task' (attname de la ForeignKey)
            field = next((f for f in current_model._meta.concrete_fields if f.attname == part), None)
            if field is None:
                raise
        is_last = index == len(parts) - 1
        if not is_last:
            if not field.is_relation:
                raise FieldDoesNotExist(f"'{part}' no es una relación en {current_model.__name__}")
            current_model = field.related_model
    return field


def query_path(path, field):
    """Ruta de consulta para el ORM: 'task_id' se consulta como 'task' (el ORM compara la FK por id)."""
    if path.endswith('_id') and field.is_relation and field.attname == path.split('__')[-1]:
        return path[:-3]
    return path


class GridFieldsMixin:
    """
    Reglas comunes de qué campos se pueden filtrar y ordenar desde la grilla.

    Se permiten todos los campos concretos del modelo y además las rutas relacionadas que el ViewSet
    declare en `grid_extra_fields` (p. ej. 'equipment__area__plant__name'). Así no hace falta mantener
    a mano una lista por vista cada vez que se agrega una columna.
    """

    @staticmethod
    def allowed_paths(view):
        model = view.queryset.model
        paths = {f.name for f in model._meta.concrete_fields}
        paths |= {f.attname for f in model._meta.concrete_fields}
        paths |= set(getattr(view, 'grid_extra_fields', ()))
        return paths

    def get_field(self, view, path):
        if path not in self.allowed_paths(view):
            raise ValidationError({GRID_FILTERS_PARAM: f"Campo no filtrable: '{path}'."})
        try:
            return resolve_field(view.queryset.model, path)
        except FieldDoesNotExist:
            raise ValidationError({GRID_FILTERS_PARAM: f"Campo inexistente: '{path}'."})


def coerce_values(field, raw_values, path):
    """Convierte los textos recibidos al tipo del campo. Un valor inválido da error 400 en vez de ignorarse."""
    target = field.target_field if field.is_relation else field
    coerced = []
    for raw in raw_values:
        # La grilla muestra los booleanos como 'true'/'false' (serialize_value); BooleanField.to_python
        # solo acepta 'True'/'False'/'t'/'f'/'1'/'0'.
        if isinstance(target, models.BooleanField) and isinstance(raw, str) and raw.lower() in ('true', 'false'):
            coerced.append(raw.lower() == 'true')
            continue
        try:
            coerced.append(target.to_python(raw))
        except (DjangoValidationError, TypeError, ValueError):
            raise ValidationError({GRID_FILTERS_PARAM: f"Valor inválido para '{path}': {raw!r}."})
    return coerced


def empty_q(lookup, field):
    """Condición de "celda vacía": NULL y, en campos de texto, también la cadena ''."""
    condition = Q(**{f'{lookup}__isnull': True})
    if isinstance(field, TEXT_FIELD_TYPES):
        condition |= Q(**{lookup: ''})
    return condition


def build_column_q(path, field, spec):
    """Traduce la especificación de una columna ({"in"|"not_in": [...], "empty": bool}) a un objeto Q."""
    if not isinstance(spec, dict):
        raise ValidationError({GRID_FILTERS_PARAM: f"Formato inválido para '{path}'."})
    lookup = query_path(path, field)
    include_empty = bool(spec.get('empty'))

    if 'in' in spec:
        values = coerce_values(field, spec['in'] or [], path)
        condition = Q(**{f'{lookup}__in': values}) if values else Q(pk__in=[])
        if include_empty:
            condition |= empty_q(lookup, field)
        return condition

    if 'not_in' in spec:
        values = coerce_values(field, spec['not_in'] or [], path)
        # Las filas vacías no están "en" la lista excluida, así que se conservan salvo que se pida lo contrario.
        condition = ~Q(**{f'{lookup}__in': values}) | empty_q(lookup, field) if values else Q()
        if include_empty:
            condition &= ~empty_q(lookup, field)
        return condition

    raise ValidationError({GRID_FILTERS_PARAM: f"'{path}' requiere 'in' o 'not_in'."})


def parse_grid_filters(request):
    raw = request.query_params.get(GRID_FILTERS_PARAM)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValidationError({GRID_FILTERS_PARAM: 'JSON inválido.'})
    if not isinstance(data, dict):
        raise ValidationError({GRID_FILTERS_PARAM: 'Se esperaba un objeto {campo: filtro}.'})
    return data


class GridFilterBackend(GridFieldsMixin, filters.BaseFilterBackend):
    """Aplica `?grid_filters=<json>` (ver docstring del módulo). Las columnas se combinan con AND."""

    def filter_queryset(self, request, queryset, view):
        grid_filters = parse_grid_filters(request)
        skip = getattr(view, 'grid_filters_skip', None)  # usado por grid-values para el filtrado cruzado
        condition = Q()
        for path, spec in grid_filters.items():
            if path == skip:
                continue
            condition &= build_column_q(path, self.get_field(view, path), spec)
        # distinct(): los filtros por rutas relacionadas (joins) pueden duplicar filas.
        if any('__' in path for path in grid_filters):
            return queryset.filter(condition).distinct()
        return queryset.filter(condition)


class GridOrderingFilter(GridFieldsMixin, filters.OrderingFilter):
    """
    `?ordering=campo` / `-campo` para cualquier campo permitido (no solo `ordering_fields`).
    Agrega 'pk' como desempate para que la paginación no repita ni salte filas cuando hay valores iguales.
    """

    def remove_invalid_fields(self, queryset, fields, view, request):
        allowed = self.allowed_paths(view) | set(getattr(view, 'ordering_fields', None) or [])
        valid = []
        for term in fields:
            path = term.lstrip('-')
            if path in allowed:
                try:
                    field = resolve_field(queryset.model, path)
                    valid.append(term.replace(path, query_path(path, field)))
                except FieldDoesNotExist:
                    if path in (getattr(view, 'ordering_fields', None) or []):
                        valid.append(term)  # alias/anotación declarada explícitamente por la vista
        return valid

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if ordering and not any(term.lstrip('-') in ('pk', 'id') for term in ordering):
            ordering = list(ordering) + ['pk']
        return ordering


GRID_VALUES_DEFAULT_LIMIT = 1000
GRID_VALUES_MAX_LIMIT = 5000


def serialize_value(value):
    """Valor tal como lo muestra la grilla y lo devuelve en el filtro: '' para vacío, ISO para fechas."""
    if value is None:
        return ''
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def distinct_values(view, request, path):
    """
    Valores distintos de una columna para el menú de filtros, respetando los demás filtros (filtrado
    cruzado) y los parámetros fijos de la vista (p. ej. sample__equipment). Consulta solo esa columna,
    con límite, en lugar de descargar todas las filas: escala con tablas grandes.
    """
    field = GridFieldsMixin().get_field(view, path)
    lookup = query_path(path, field)
    try:
        limit = min(int(request.query_params.get('limit', GRID_VALUES_DEFAULT_LIMIT)), GRID_VALUES_MAX_LIMIT)
    except ValueError:
        raise ValidationError({'limit': 'Debe ser un entero.'})

    view.grid_filters_skip = path  # el menú de una columna no se filtra por sí mismo
    queryset = view.filter_queryset(view.get_queryset())
    queryset = queryset.order_by().values_list(lookup, flat=True).distinct()

    search = request.query_params.get('search', '').strip()
    if search:
        queryset = queryset.filter(**{f'{lookup}__icontains': search})

    values = list(queryset.order_by(lookup)[:limit + 1])
    truncated = len(values) > limit
    serialized = sorted({serialize_value(v) for v in values[:limit]}, key=lambda v: (v != '', v))
    return {'field': path, 'values': serialized, 'truncated': truncated}
