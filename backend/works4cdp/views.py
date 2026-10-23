"""
Vistas (API REST) de la aplicación works4cdp.

Refactorización respecto a la versión anterior:
- Se eliminaron los imports con asterisco (`from .models import *`), que ocultaban de dónde venía
  cada nombre y provocaron un NameError latente (`time` se usaba sin importarse).
- El endpoint `/schema/` (copiado en 12 ViewSets) y `/delete-impact/` (copiado en 4) pasaron a mixins.
- La configuración de filtros/orden común pasó a `BaseViewSet`.
- La regla de chemical_id se reutiliza desde `AssaySyncService` en vez de duplicarse.
- `WeeklyTaskView` ahora valida sus parámetros en lugar de fallar con error 500.
"""
import logging
from datetime import datetime

from django.db import connection, transaction
from django.db.models import BooleanField, Case, F, Value, When
from django.db.models.functions import Coalesce
from django.contrib.postgres.aggregates import StringAgg
from django.utils import timezone
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Area, Assay, Calendar, CorrectiveTask, Equipment, Estado, Plant, Sample,
    System, Task, TaskCatalog, TaskP, User, UserP,
)
from .serializers import (
    AreaSerializer, AssaySerializer, CalendarSerializer, CorrectiveTaskSerializer,
    EquipmentSerializer, EstadoSerializer, PlantSerializer, SampleSerializer,
    SystemSerializer, TaskCatalogSerializer, TaskPSerializer, TaskSerializer,
    UserPSerializer, UserSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Piezas reutilizables
# ---------------------------------------------------------------------------

def parse_iso_date(value):
    """
    Convierte 'YYYY-MM-DD' en `date`.
    Devuelve (fecha, None) si es válida, (None, mensaje) si el formato es incorrecto
    y (None, None) si no se envió valor.
    """
    if not value:
        return None, None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"Formato de fecha inválido: {value}. Use YYYY-MM-DD."


def error_response(message, http_status):
    """Respuesta de error con el formato {"status": "error", "error": ...} que ya consume el frontend."""
    return Response({"status": "error", "error": message}, status=http_status)


class SchemaMixin:
    """Agrega GET /<recurso>/schema/ que lista los nombres de campo del modelo (antes copiado en cada ViewSet)."""

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in self.queryset.model._meta.fields]
        return Response({'fields': fields})


class DeleteImpactMixin:
    """
    Agrega /<recurso>/delete-impact/ (GET con ?ids=1,2 o POST con {"ids": [...]}) que informa
    cuántos registros dependientes se borrarían en cascada.

    Cada ViewSet declara `impact_counts`: un dict ordenado {nombre_campo: función(obj) -> int}.
    El resultado incluye esos conteos más `total_impact` (su suma), igual que antes.
    """
    impact_counts = {}

    def _requested_ids(self, request):
        """Lee los IDs pedidos y descarta los que no sean enteros (antes un valor inválido causaba error 500)."""
        raw = request.data.get('ids', []) if request.method == 'POST' else request.query_params.get('ids', '').split(',')
        ids = []
        for item in raw:
            try:
                ids.append(int(item))
            except (TypeError, ValueError):
                continue
        return ids

    @action(detail=False, methods=['post', 'get'], url_path='delete-impact')
    def delete_impact(self, request):
        impact = []
        for obj in self.queryset.model.objects.filter(id__in=self._requested_ids(request)):
            counts = {name: count(obj) for name, count in self.impact_counts.items()}
            impact.append({
                'id': obj.id,
                'tag': obj.tag,
                'name': obj.name,
                **counts,
                'total_impact': sum(counts.values()),
            })
        return Response({'impact': impact})


class BaseViewSet(SchemaMixin, viewsets.ModelViewSet):
    """CRUD estándar con filtros por campo (`filterset_fields`) y ordenamiento (`ordering_fields`)."""
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]


# ---------------------------------------------------------------------------
# Jerarquía de activos: Planta > Área > Equipo, y Sistema
# ---------------------------------------------------------------------------

class EstadoViewSet(BaseViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'estado_nombre': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'estado_nombre']


class TaskCatalogViewSet(BaseViewSet):
    queryset = TaskCatalog.objects.all()
    serializer_class = TaskCatalogSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'name', 'description']


class PlantViewSet(DeleteImpactMixin, BaseViewSet):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'tag', 'name', 'description']
    impact_counts = {
        'areas_count': lambda plant: plant.area_set.count(),
        'equipments_count': lambda plant: Equipment.objects.filter(area__plant=plant).count(),
        'tasks_count': lambda plant: Task.objects.filter(equipment__area__plant=plant).count(),
        'correctives_count': lambda plant: CorrectiveTask.objects.filter(equipment__area__plant=plant).count(),
        'samples_count': lambda plant: Sample.objects.filter(equipment__area__plant=plant).count(),
    }


class AreaViewSet(DeleteImpactMixin, BaseViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull'],
        'plant': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'tag', 'name', 'description', 'plant']
    impact_counts = {
        'equipments_count': lambda area: area.equipment_set.count(),
        'tasks_count': lambda area: Task.objects.filter(equipment__area=area).count(),
        'correctives_count': lambda area: CorrectiveTask.objects.filter(equipment__area=area).count(),
        'samples_count': lambda area: Sample.objects.filter(equipment__area=area).count(),
    }


class SystemViewSet(DeleteImpactMixin, BaseViewSet):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'tag', 'name', 'description']
    impact_counts = {
        'equipments_count': lambda system: system.equipment_set.count(),
        'tasks_count': lambda system: Task.objects.filter(equipment__system=system).count(),
        'correctives_count': lambda system: CorrectiveTask.objects.filter(equipment__system=system).count(),
        'samples_count': lambda system: Sample.objects.filter(equipment__system=system).count(),
    }


class EquipmentViewSet(DeleteImpactMixin, BaseViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull'],
        'system': ['exact', 'in', 'isnull'],
        'area': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'tag', 'name', 'description', 'system', 'area']
    impact_counts = {
        'tasks_count': lambda eq: eq.task_set.count(),
        'correctives_count': lambda eq: eq.correctivetask_set.count(),
        'samples_count': lambda eq: eq.samples.count(),
    }


# ---------------------------------------------------------------------------
# Tareas
# ---------------------------------------------------------------------------

class TaskViewSet(BaseViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'task_catalog': ['exact', 'in', 'isnull'],
        'task_catalog__name': ['exact', 'in', 'icontains', 'isnull'],
        'duration': ['exact', 'in', 'isnull'],
        'workers': ['exact', 'in', 'isnull'],
        'frequency': ['exact', 'in', 'icontains', 'isnull'],
        'start_date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull'],
        'procedure': ['exact', 'in', 'icontains', 'isnull'],
        'turn': ['exact', 'in', 'icontains', 'isnull'],
        'equipment': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'task_catalog__name', 'duration', 'workers', 'frequency', 'start_date', 'description', 'procedure', 'turn', 'equipment']


class TaskPViewSet(BaseViewSet):
    queryset = TaskP.objects.all()
    serializer_class = TaskPSerializer
    # Para filtrar con varios valores se incluye el lookup 'in' en los campos clave.
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'task': ['exact', 'in', 'isnull'],
        'year': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'week': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'estado': ['exact', 'in', 'isnull'],
        'group': ['exact', 'in', 'isnull'],
        'rescheduled': ['exact', 'isnull']
    }
    ordering_fields = ['id', 'task', 'year', 'week', 'day', 'date', 'group', 'estado', 'priority', 'rescheduled']

    def get_queryset(self):
        # Excluir tareas huérfanas que no tienen ni plantilla programada ni correctiva
        return super().get_queryset().exclude(
            task__isnull=True,
            corrective_task__isnull=True
        )


class CorrectiveTaskFilter(django_filters.FilterSet):
    # Filtros que mapean los parámetros obsoletos 'year', 'week' y 'date' a 'creation_date'
    year = django_filters.NumberFilter(field_name='creation_date', lookup_expr='year')
    week = django_filters.NumberFilter(field_name='creation_date', lookup_expr='week')
    date = django_filters.DateFilter(field_name='creation_date')

    class Meta:
        model = CorrectiveTask
        fields = {
            'id': ['exact', 'in', 'isnull'],
            'name': ['exact', 'in', 'icontains', 'isnull'],
            'task_catalog': ['exact', 'in', 'isnull'],
            'task_catalog__name': ['exact', 'in', 'icontains', 'isnull'],
            'description': ['exact', 'in', 'icontains', 'isnull'],
            'root_cause': ['exact', 'in', 'icontains', 'isnull'],
            'equipment': ['exact', 'in', 'isnull'],
            'creation_date': ['exact', 'in', 'gte', 'lte', 'isnull'],
            'priority': ['exact', 'in', 'isnull'],
            'created_by_user': ['exact', 'in', 'isnull'],
            'turno': ['exact', 'in', 'icontains', 'isnull'],
        }


class CorrectiveTaskViewSet(BaseViewSet):
    queryset = CorrectiveTask.objects.all()
    serializer_class = CorrectiveTaskSerializer
    filterset_class = CorrectiveTaskFilter
    ordering_fields = ['id', 'equipment', 'creation_date']


# ---------------------------------------------------------------------------
# Personal y calendario
# ---------------------------------------------------------------------------

class UserViewSet(BaseViewSet):
    """API endpoint para el modelo personalizado User (works4cdp_user)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'nombre': ['exact', 'in', 'icontains', 'isnull'],
        'apellido': ['exact', 'in', 'icontains', 'isnull'],
        'email': ['exact', 'in', 'icontains', 'isnull'],
        'rol': ['exact', 'in', 'icontains', 'isnull'],
        'group': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'nombre', 'apellido', 'group']


class UserPViewSet(BaseViewSet):
    """API endpoint para el modelo de Grupos (UserP)."""
    # UserP no define `ordering` en su Meta; sin orden explícito la paginación puede repetir u omitir
    # registros entre páginas (DRF emite UnorderedObjectListWarning).
    queryset = UserP.objects.order_by('id')
    serializer_class = UserPSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'name']


class CalendarViewSet(BaseViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'year': ['exact', 'in', 'isnull'],
        'week': ['exact', 'in', 'isnull'],
        'group': ['exact', 'in', 'isnull'],
        'turn': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'date', 'year', 'week']


# ---------------------------------------------------------------------------
# Muestras y ensayos
# ---------------------------------------------------------------------------

class SampleViewSet(BaseViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'equipment': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'tag', 'name', 'equipment']


class AssayViewSet(BaseViewSet):
    # select_related evita una consulta extra por ensayo al serializar `sample`.
    queryset = Assay.objects.select_related('sample', 'sample__equipment').all()
    serializer_class = AssaySerializer
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'time': ['exact', 'in', 'isnull'],
        'sample': ['exact', 'in', 'isnull'],
        'sample__equipment': ['exact', 'in', 'isnull'],
        'user': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'date', 'time', 'sample', 'user']

    @action(detail=False, methods=['post'], url_path='sync-equipment')
    def sync_equipment(self, request):
        """POST /api/assays/sync-equipment/ — sincroniza con el Courier a demanda desde la UI."""
        equipment_id = request.data.get('equipment_id')
        if not equipment_id:
            return error_response("El parámetro equipment_id es requerido.", status.HTTP_400_BAD_REQUEST)

        target_date, date_error = parse_iso_date(request.data.get('date'))
        if date_error:
            return error_response(date_error, status.HTTP_400_BAD_REQUEST)

        try:
            # Import local: evita cargar `requests` y el servicio al arrancar Django.
            from .services.clb_syncer import AssaySyncService
            result = AssaySyncService.sync_equipment(equipment_id=equipment_id, target_date=target_date)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            # Se registra el traceback completo; al cliente solo se le informa el mensaje.
            logger.exception("Error al sincronizar el equipo %s con el Courier", equipment_id)
            return error_response(
                f"Error al sincronizar con el analizador: {exc}",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'], url_path='next-chemical-id')
    def next_chemical_id(self, request):
        """
        GET /api/assays/next-chemical-id/?equipment_id=<id> | ?plant_id=<id>
        Retorna el siguiente chemical_id correlativo disponible para la planta del equipo.

        Regla de negocio (implementada en AssaySyncService):
        - Concentradora 1 (Courier 1 y 2) comparten una secuencia (serie ~26,000).
        - Concentradora 2 (Courier 5 y 6) comparten otra (serie ~10,000).
        """
        from .services.clb_syncer import AssaySyncService

        equipment_id = request.query_params.get('equipment_id')
        plant_id = request.query_params.get('plant_id')
        target_equipment = None

        # 1. Identificar la planta a partir del equipment_id o plant_id
        if equipment_id:
            try:
                target_equipment = Equipment.objects.select_related('area__plant').get(id=int(equipment_id))
            except (Equipment.DoesNotExist, ValueError):
                return error_response(f"Equipo con ID '{equipment_id}' no encontrado.", status.HTTP_404_NOT_FOUND)
            target_plant = target_equipment.area.plant if target_equipment.area else None
        elif plant_id:
            try:
                target_plant = Plant.objects.get(id=int(plant_id))
            except (Plant.DoesNotExist, ValueError):
                return error_response(f"Planta con ID '{plant_id}' no encontrada.", status.HTTP_404_NOT_FOUND)
        else:
            return error_response("Debe especificar el parámetro 'equipment_id' o 'plant_id'.", status.HTTP_400_BAD_REQUEST)

        if not target_plant:
            return error_response("No se pudo determinar la planta para el equipo especificado.", status.HTTP_400_BAD_REQUEST)

        # 2. Máximo registrado en la planta y 3. siguiente correlativo (con la base por planta si no hay datos)
        max_chemical_id = AssaySyncService.get_max_chemical_id(plant=target_plant)
        next_id = AssaySyncService.get_next_chemical_id_for_plant(plant=target_plant)

        return Response({
            "status": "ok",
            "plant_id": target_plant.id,
            "plant_name": target_plant.name,
            "equipment_id": target_equipment.id if target_equipment else None,
            "equipment_name": target_equipment.name if target_equipment else None,
            "max_chemical_id": max_chemical_id,
            "next_chemical_id": next_id
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='autofill-chemical-ids')
    def autofill_chemical_ids(self, request):
        """
        POST /api/assays/autofill-chemical-ids/
        Asigna o recalcula códigos chemical_id correlativos para un equipo (y fecha opcional).
        Con `reassign=true` también reasigna los ensayos que ya tenían código.
        """
        from .services.clb_syncer import AssaySyncService, assay_sort_key

        equipment_id = request.data.get('equipment_id')
        reassign = bool(request.data.get('reassign', False))

        if not equipment_id:
            return error_response("El parámetro equipment_id es requerido.", status.HTTP_400_BAD_REQUEST)
        try:
            equipment_id = int(equipment_id)  # antes un valor no numérico producía error 500
        except (TypeError, ValueError):
            return error_response(f"equipment_id inválido: {equipment_id}.", status.HTTP_400_BAD_REQUEST)

        target_date, date_error = parse_iso_date(request.data.get('date'))
        if date_error:
            return error_response(date_error, status.HTTP_400_BAD_REQUEST)

        equipment = Equipment.objects.select_related('area__plant').filter(id=equipment_id).first()
        if not equipment:
            return error_response("Equipo no encontrado.", status.HTTP_404_NOT_FOUND)
        plant = equipment.area.plant if equipment.area else None

        query = Assay.objects.filter(sample__equipment_id=equipment_id)
        if target_date:
            query = query.filter(date=target_date)
        if not reassign:
            query = query.filter(chemical_id__isnull=True)

        assays_to_update = sorted(query.select_related('sample'), key=assay_sort_key)
        if not assays_to_update:
            return Response({
                "status": "ok",
                "message": "No hay ensayos pendientes de código chemical_id para esta selección.",
                "updated": 0
            })

        # El cálculo del siguiente ID y la escritura van en la misma transacción para acortar la ventana
        # de carrera entre dos peticiones simultáneas.
        with transaction.atomic():
            next_id = AssaySyncService.get_next_chemical_id_for_plant(plant=plant, equipment_id=equipment_id)
            current_seq = next_id
            for assay in assays_to_update:
                assay.chemical_id = current_seq
                current_seq += 1
            Assay.objects.bulk_update(assays_to_update, ['chemical_id'])

        return Response({
            "status": "ok",
            "message": f"Se asignaron {len(assays_to_update)} códigos chemical_id iniciando en {next_id}.",
            "updated": len(assays_to_update),
            "start_id": next_id,
            "next_chemical_id": current_seq
        })


# ---------------------------------------------------------------------------
# Vista semanal
# ---------------------------------------------------------------------------

class WeeklyTaskView(APIView):
    """GET: tareas y calendario de una semana. POST: actualiza el estado de varias tareas (ExcelGrid)."""

    def get(self, request):
        week = request.query_params.get('week')
        # El año por defecto era 2026 fijo en el código; ahora es el año en curso.
        year = request.query_params.get('year', timezone.localdate().year)

        if not week or not year:
            return Response({"error": "Faltan parámetros week y year"}, status=400)
        try:
            # Antes un valor no numérico llegaba al ORM y terminaba en error 500.
            week, year = int(week), int(year)
        except (TypeError, ValueError):
            return Response({"error": "Los parámetros week y year deben ser enteros"}, status=400)

        # Excluye huérfanas (sin plantilla ni correctiva) para evitar celdas vacías en el frontend.
        tareas = TaskP.objects.filter(
            week=week,
            year=year
        ).exclude(
            task__isnull=True,
            corrective_task__isnull=True
        ).annotate(
            is_corrective=Case(
                When(corrective_task__isnull=False, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).values(
            'id',
            'date',
            'estado_id',
            'is_corrective',
            anio=F('year'),
            semana=F('week'),
            fecha=F('date'),
            dia_semana=F('day'),
            planta=Coalesce('task__equipment__area__plant__name', 'corrective_task__equipment__area__plant__name'),
            area=Coalesce('task__equipment__area__name', 'corrective_task__equipment__area__name'),
            sistema=Coalesce('task__equipment__system__name', 'corrective_task__equipment__system__name'),
            tarea_descripcion=Coalesce('task__task_catalog__name', 'corrective_task__task_catalog__name', 'corrective_task__name'),
            tarea_detalle=Coalesce('task__description', 'corrective_task__description'),
            equipo=Coalesce('task__equipment__name', 'corrective_task__equipment__name'),
            equipo_desc=Coalesce('task__equipment__description', 'corrective_task__equipment__description'),
            turno=Coalesce('task__turn', 'corrective_task__turno', Value('C')),
            estado_nombre=F('estado__estado_nombre')
        ).annotate(
            cuadrilla_grupo=StringAgg(
                'taskgroupassignment__calendar__group__name',
                delimiter=' / ',
                distinct=True
            ),
            usuarios_asignados=StringAgg(
                'taskgroupassignment__calendar__group__user__nombre',
                delimiter=', ',
                distinct=True
            )
        ).order_by('date', 'turno')

        # Consulta SQL nativa del calendario para las estadísticas de personal (parámetros enlazados con %s).
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.id AS calendar_id,
                    c.date AS fecha,
                    c.day AS dia_semana,
                    c.turn AS turno,
                    c.overtime AS horas_extra,
                    g.name AS nombre_grupo,
                    u.nombre AS usuario_nombre,
                    u.apellido AS usuario_apellido,
                    u.rol AS usuario_rol,
                    tga.taskp_id AS tarea_asignada_id
                FROM
                    public.works4cdp_calendar c
                LEFT JOIN
                    public.works4cdp_taskgroupassignment tga ON c.id = tga.calendar_id
                LEFT JOIN
                    public.works4cdp_userp g ON c.group_id = g.id
                LEFT JOIN
                    public.works4cdp_user u ON u.group_id = g.id OR u.id = c.id_user
                WHERE c.week = %s AND c.year = %s
                ORDER BY c.date ASC, g.name ASC;
            """, [week, year])
            columns = [col[0] for col in cursor.description]
            calendario = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return Response({"tasks": list(tareas), "calendar": calendario})

    def post(self, request):
        """Guarda cambios masivos de estado: {"updates": [{"id": 1, "estado_id": 2}, ...]}."""
        updates = request.data.get('updates', [])
        if not isinstance(updates, list):
            return Response({"error": "'updates' debe ser una lista"}, status=400)
        # Se valida todo antes de escribir para no dejar la actualización a medias (antes un item sin
        # 'id' o 'estado_id' lanzaba KeyError tras haber guardado los anteriores).
        if any(not isinstance(i, dict) or 'id' not in i or 'estado_id' not in i for i in updates):
            return Response({"error": "Cada elemento requiere 'id' y 'estado_id'"}, status=400)

        with transaction.atomic():
            for item in updates:
                TaskP.objects.filter(id=item['id']).update(estado_id=item['estado_id'])
        return Response({"status": "success"})
