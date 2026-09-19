from django.db import connection
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.views import APIView

# Importaciones adicionales para el filtrado avanzado y el modelo User de Django
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import F, Value, Case, When, BooleanField, Max
from django.db.models.functions import Concat, Coalesce
from django.contrib.postgres.aggregates import StringAgg
from django_filters import rest_framework as django_filters

# ViewSet para cada modelo con un nuevo endpoint `/schema/`
class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'estado_nombre': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'estado_nombre']

    # Endpoint `/schema/`
    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Estado._meta.fields]  # Lista de campos del modelo
        return Response({'fields': fields})

class TaskCatalogViewSet(viewsets.ModelViewSet):
    queryset = TaskCatalog.objects.all()
    serializer_class = TaskCatalogSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'name', 'description']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in TaskCatalog._meta.fields]
        return Response({'fields': fields})

class PlantViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Plant
    queryset = Plant.objects.all()
    # Define el serializador encargado de convertir objetos Plant a JSON (y viceversa)
    serializer_class = PlantSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados (ej: ?ordering=name)
    ordering_fields = ['id', 'tag', 'name', 'description']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Plant._meta.fields]
        return Response({'fields': fields})

    @action(detail=False, methods=['post', 'get'], url_path='delete-impact')
    def delete_impact(self, request):
        ids = request.data.get('ids', []) if request.method == 'POST' else [int(x) for x in request.query_params.get('ids', '').split(',') if x.strip().isdigit()]
        impact = []
        for plant in Plant.objects.filter(id__in=ids):
            areas_count = plant.area_set.count()
            equipments_count = Equipment.objects.filter(area__plant=plant).count()
            tasks_count = Task.objects.filter(equipment__area__plant=plant).count()
            correctives_count = CorrectiveTask.objects.filter(equipment__area__plant=plant).count()
            samples_count = Sample.objects.filter(equipment__area__plant=plant).count()
            impact.append({
                'id': plant.id,
                'tag': plant.tag,
                'name': plant.name,
                'areas_count': areas_count,
                'equipments_count': equipments_count,
                'tasks_count': tasks_count,
                'correctives_count': correctives_count,
                'samples_count': samples_count,
                'total_impact': areas_count + equipments_count + tasks_count + correctives_count + samples_count
            })
        return Response({'impact': impact})

class AreaViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Area
    queryset = Area.objects.all()
    # Define el serializador encargado de convertir objetos Area a JSON (y viceversa)
    serializer_class = AreaSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull'],
        'plant': ['exact', 'in', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description', 'plant']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Area._meta.fields]
        return Response({'fields': fields})

    @action(detail=False, methods=['post', 'get'], url_path='delete-impact')
    def delete_impact(self, request):
        ids = request.data.get('ids', []) if request.method == 'POST' else [int(x) for x in request.query_params.get('ids', '').split(',') if x.strip().isdigit()]
        impact = []
        for area in Area.objects.filter(id__in=ids):
            equipments_count = area.equipment_set.count()
            tasks_count = Task.objects.filter(equipment__area=area).count()
            correctives_count = CorrectiveTask.objects.filter(equipment__area=area).count()
            samples_count = Sample.objects.filter(equipment__area=area).count()
            impact.append({
                'id': area.id,
                'tag': area.tag,
                'name': area.name,
                'equipments_count': equipments_count,
                'tasks_count': tasks_count,
                'correctives_count': correctives_count,
                'samples_count': samples_count,
                'total_impact': equipments_count + tasks_count + correctives_count + samples_count
            })
        return Response({'impact': impact})

class SystemViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo System
    queryset = System.objects.all()
    # Define el serializador encargado de convertir objetos System a JSON (y viceversa)
    serializer_class = SystemSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in System._meta.fields]
        return Response({'fields': fields})

    @action(detail=False, methods=['post', 'get'], url_path='delete-impact')
    def delete_impact(self, request):
        ids = request.data.get('ids', []) if request.method == 'POST' else [int(x) for x in request.query_params.get('ids', '').split(',') if x.strip().isdigit()]
        impact = []
        for sys_obj in System.objects.filter(id__in=ids):
            equipments_count = sys_obj.equipment_set.count()
            tasks_count = Task.objects.filter(equipment__system=sys_obj).count()
            correctives_count = CorrectiveTask.objects.filter(equipment__system=sys_obj).count()
            samples_count = Sample.objects.filter(equipment__system=sys_obj).count()
            impact.append({
                'id': sys_obj.id,
                'tag': sys_obj.tag,
                'name': sys_obj.name,
                'equipments_count': equipments_count,
                'tasks_count': tasks_count,
                'correctives_count': correctives_count,
                'samples_count': samples_count,
                'total_impact': equipments_count + tasks_count + correctives_count + samples_count
            })
        return Response({'impact': impact})

class EquipmentViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Equipment
    queryset = Equipment.objects.all()
    # Define el serializador encargado de convertir objetos Equipment a JSON (y viceversa)
    serializer_class = EquipmentSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'description': ['exact', 'in', 'icontains', 'isnull'],
        'system': ['exact', 'in', 'isnull'],
        'area': ['exact', 'in', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description', 'system', 'area']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Equipment._meta.fields]
        return Response({'fields': fields})

    @action(detail=False, methods=['post', 'get'], url_path='delete-impact')
    def delete_impact(self, request):
        ids = request.data.get('ids', []) if request.method == 'POST' else [int(x) for x in request.query_params.get('ids', '').split(',') if x.strip().isdigit()]
        impact = []
        for eq in Equipment.objects.filter(id__in=ids):
            tasks_count = eq.task_set.count()
            correctives_count = eq.correctivetask_set.count()
            samples_count = eq.samples.count()
            impact.append({
                'id': eq.id,
                'tag': eq.tag,
                'name': eq.name,
                'tasks_count': tasks_count,
                'correctives_count': correctives_count,
                'samples_count': samples_count,
                'total_impact': tasks_count + correctives_count + samples_count
            })
        return Response({'impact': impact})

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    # Habilitar filtros y ordenamiento
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    # Definir campos de filtrado
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
    
    # Definir campos de ordenamiento
    ordering_fields = ['id', 'task_catalog__name', 'duration', 'workers', 'frequency', 'start_date', 'description', 'procedure', 'turn', 'equipment']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Task._meta.fields]
        return Response({'fields': fields})

class TaskPViewSet(viewsets.ModelViewSet):
    queryset = TaskP.objects.all()
    serializer_class = TaskPSerializer
    
    def get_queryset(self):
        # Excluir tareas huérfanas que no tienen ni plantilla programada ni correctiva
        return super().get_queryset().exclude(
            task__isnull=True,
            corrective_task__isnull=True
        )
    
    # Habilitar filtros y ordenamiento
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    # Definir campos de filtrado
    #filterset_fields = {
    #    'id': ['exact', 'in'],
    #    'task': ['exact', 'in'],
    #    'year': ['exact', 'in', 'gte', 'lte'],
    #    'week': ['exact', 'in', 'gte', 'lte'],
    #    'day': ['exact', 'in', 'icontains'],
    #    'date': ['exact', 'in', 'gte', 'lte'],
    #    'usuario': ['exact', 'in'],
    #    'estado': ['exact', 'in'],
    #    'priority': ['exact', 'in', 'icontains'],
    #    'rescheduled': ['exact', 'in']
    #}

    # IMPORTANTE: Cambia 'exact' por una lista que incluya 'in' para los campos clave
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
    
    # Definir campos de ordenamiento
    ordering_fields = ['id', 'task', 'year', 'week', 'day', 'date', 'group', 'estado', 'priority', 'rescheduled']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in TaskP._meta.fields]
        return Response({'fields': fields})

# --- VISTAS CORREGIDAS PARA USUARIOS Y GRUPOS ---

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint para el modelo personalizado User (works4cdp_user).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'nombre': ['exact', 'in', 'icontains', 'isnull'],
        'apellido': ['exact', 'in', 'icontains', 'isnull'],
        'email': ['exact', 'in', 'icontains', 'isnull'],
        'rol': ['exact', 'in', 'icontains', 'isnull'],
        'group': ['exact', 'in', 'isnull']
    }
    ordering_fields = ['id', 'nombre', 'apellido', 'group']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in User._meta.fields]
        return Response({'fields': fields})

class CorrectiveTaskFilter(django_filters.FilterSet):
    # Definimos filtros personalizados para mapear los parámetros obsoletos 'year', 'week' y 'date' a 'creation_date'
    year = django_filters.NumberFilter(field_name='creation_date', lookup_expr='year')
    week = django_filters.NumberFilter(field_name='creation_date', lookup_expr='week')
    date = django_filters.DateFilter(field_name='creation_date')

    class Meta:
        model = CorrectiveTask
        # Campos de base para el filtro
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

class CorrectiveTaskViewSet(viewsets.ModelViewSet):
    queryset = CorrectiveTask.objects.all()
    serializer_class = CorrectiveTaskSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Usamos la clase de filtro personalizada en lugar de filterset_fields
    filterset_class = CorrectiveTaskFilter
    # Se actualizó 'date' a 'creation_date' ya que el campo original se llama 'creation_date' en el modelo
    ordering_fields = ['id', 'equipment', 'creation_date']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in CorrectiveTask._meta.fields]
        return Response({'fields': fields})


class SampleViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Sample
    queryset = Sample.objects.all()
    # Define el serializador encargado de convertir objetos Sample a JSON (y viceversa)
    serializer_class = SampleSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'tag': ['exact', 'in', 'icontains', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull'],
        'equipment': ['exact', 'in', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'equipment']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Sample._meta.fields]
        return Response({'fields': fields})


class AssayViewSet(viewsets.ModelViewSet):
    # Optimización: Usamos select_related para traer datos de Sample y Equipment en una sola consulta
    queryset = Assay.objects.select_related('sample', 'sample__equipment').all()
    # Define el serializador encargado de convertir objetos Assay a JSON (y viceversa)
    serializer_class = AssaySerializer
    
    # Configuración de backends de filtros: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    # sample__equipment permite filtrar ensayos según el equipo de su muestra
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'time': ['exact', 'in', 'isnull'],
        'sample': ['exact', 'in', 'isnull'],
        'sample__equipment': ['exact', 'in', 'isnull'],
        'user': ['exact', 'in', 'isnull']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'date', 'time', 'sample', 'user']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Assay._meta.fields]
        return Response({'fields': fields})

    # Endpoint POST /api/assays/sync-equipment/ para sincronizar con el Courier a demanda desde la UI
    @action(detail=False, methods=['post'], url_path='sync-equipment')
    def sync_equipment(self, request):
        # Extraemos el ID del equipo analizador recibido en el payload JSON.
        equipment_id = request.data.get('equipment_id')
        # Extraemos la fecha opcional en formato YYYY-MM-DD.
        target_date_str = request.data.get('date')

        # Validamos que se haya enviado el parámetro obligatorio equipment_id.
        if not equipment_id:
            return Response(
                {"status": "error", "error": "El parámetro equipment_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parseamos la fecha si fue provista por el cliente.
        target_date = None
        if target_date_str:
            try:
                from datetime import datetime
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"status": "error", "error": f"Formato de fecha inválido: {target_date_str}. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            # Importamos el servicio de sincronización de Couriers.
            from .services.clb_syncer import AssaySyncService
            # Ejecutamos la sincronización con conciliación delta por clave natural.
            result = AssaySyncService.sync_equipment(equipment_id=equipment_id, target_date=target_date)
            # Retornamos respuesta con el estado y la cantidad de registros insertados.
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            # Capturamos cualquier excepción inesperada para responder con código 500.
            return Response(
                {"status": "error", "error": f"Error al sincronizar con el analizador: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Endpoint GET /api/assays/next-chemical-id/ para calcular el siguiente correlativo secuencial por planta
    @action(detail=False, methods=['get'], url_path='next-chemical-id')
    def next_chemical_id(self, request):
        """
        Calcula y retorna el siguiente chemical_id correlativo disponible para la planta
        asociada al equipo analizador especificado.
        
        Regla de negocio:
        - Concentradora 1 (Courier Flotacion C1 [id=1] y Courier Molibdeno C1 [id=2]):
          Comparten una misma secuencia correlativa continua (serie ~26,000).
        - Concentradora 2 (Courier Flotacion C2 [id=5] y Courier Molibdeno C2 [id=6]):
          Comparten una misma secuencia correlativa continua (serie ~10,000).
        """
        equipment_id = request.query_params.get('equipment_id')
        plant_id = request.query_params.get('plant_id')

        target_plant = None
        target_equipment = None

        # 1. Identificar la planta a partir del equipment_id o plant_id
        if equipment_id:
            try:
                target_equipment = Equipment.objects.select_related('area__plant').get(id=int(equipment_id))
                if target_equipment.area and target_equipment.area.plant:
                    target_plant = target_equipment.area.plant
            except (Equipment.DoesNotExist, ValueError):
                return Response(
                    {"status": "error", "error": f"Equipo con ID '{equipment_id}' no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif plant_id:
            try:
                target_plant = Plant.objects.get(id=int(plant_id))
            except (Plant.DoesNotExist, ValueError):
                return Response(
                    {"status": "error", "error": f"Planta con ID '{plant_id}' no encontrada."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"status": "error", "error": "Debe especificar el parámetro 'equipment_id' o 'plant_id'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not target_plant:
            return Response(
                {"status": "error", "error": "No se pudo determinar la planta para el equipo especificado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Consultar el valor máximo de chemical_id registrado en toda la planta
        # Se filtra chemical_id < 100000 para ignorar valores históricos de timestamps Unix (ej. 1741018740)
        max_record = Assay.objects.filter(
            sample__equipment__area__plant=target_plant,
            chemical_id__isnull=False,
            chemical_id__lt=100000
        ).aggregate(max_id=Max('chemical_id'))

        max_chemical_id = max_record.get('max_id')

        # 3. Si no existe ningún chemical_id previo en la planta, determinar base según la planta
        if max_chemical_id is None:
            # Concentradora 1 usa base 26000, Concentradora 2 usa base 10000
            if "1" in str(target_plant.name) or "1" in str(target_plant.tag):
                next_id = 26001
            else:
                next_id = 10001
        else:
            next_id = max_chemical_id + 1

        return Response({
            "status": "ok",
            "plant_id": target_plant.id,
            "plant_name": target_plant.name,
            "equipment_id": target_equipment.id if target_equipment else None,
            "equipment_name": target_equipment.name if target_equipment else None,
            "max_chemical_id": max_chemical_id,
            "next_chemical_id": next_id
        }, status=status.HTTP_200_OK)

    # Endpoint POST /api/assays/autofill-chemical-ids/ para autollenar o reasignar correlativos en BD
    @action(detail=False, methods=['post'], url_path='autofill-chemical-ids')
    def autofill_chemical_ids(self, request):
        """
        Asigna o recalcula códigos chemical_id correlativos para un equipo y fecha dados directamente en la base de datos.
        """
        equipment_id = request.data.get('equipment_id')
        date_str = request.data.get('date')
        reassign = bool(request.data.get('reassign', False))

        if not equipment_id:
            return Response(
                {"status": "error", "error": "El parámetro equipment_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_date = None
        if date_str:
            try:
                from datetime import datetime
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"status": "error", "error": f"Formato de fecha inválido: {date_str}. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        from .services.clb_syncer import AssaySyncService, natural_sort_key
        equipment = Equipment.objects.select_related('area__plant').filter(id=int(equipment_id)).first()
        if not equipment:
            return Response({"status": "error", "error": "Equipo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        plant = equipment.area.plant if equipment.area else None

        query = Assay.objects.filter(sample__equipment_id=equipment_id)
        if target_date:
            query = query.filter(date=target_date)

        if not reassign:
            query = query.filter(chemical_id__isnull=True)

        assays_to_update = list(query.select_related('sample'))
        if not assays_to_update:
            return Response({
                "status": "ok",
                "message": "No hay ensayos pendientes de código chemical_id para esta selección.",
                "updated": 0
            })

        assays_to_update.sort(
            key=lambda a: (
                natural_sort_key(a.sample.tag if a.sample else ""),
                a.instance or 0,
                a.time or time(0, 0, 0)
            )
        )

        next_id = AssaySyncService.get_next_chemical_id_for_plant(plant=plant, equipment_id=equipment_id)
        current_seq = next_id
        for a in assays_to_update:
            a.chemical_id = current_seq
            current_seq += 1

        from django.db import transaction
        with transaction.atomic():
            Assay.objects.bulk_update(assays_to_update, ['chemical_id'])

        return Response({
            "status": "ok",
            "message": f"Se asignaron {len(assays_to_update)} códigos chemical_id iniciando en {next_id}.",
            "updated": len(assays_to_update),
            "start_id": next_id,
            "next_chemical_id": current_seq
        })

class CalendarViewSet(viewsets.ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'date': ['exact', 'in', 'gte', 'lte', 'isnull'],
        'year': ['exact', 'in', 'isnull'],
        'week': ['exact', 'in', 'isnull'],
        'group': ['exact', 'in', 'isnull'],
        'turn': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'date', 'year', 'week']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Calendar._meta.fields]
        return Response({'fields': fields})

class UserPViewSet(viewsets.ModelViewSet):  # Permite CRUD completo
    """
    API endpoint para el modelo de Grupos (UserP).
    Se ha corregido para eliminar la duplicación y usar los nombres de campo correctos.
    """
    queryset = UserP.objects.all()
    serializer_class = UserPSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in', 'isnull'],
        'name': ['exact', 'in', 'icontains', 'isnull']
    }
    ordering_fields = ['id', 'name']

class WeeklyTaskView(APIView):
    def get(self, request):
        week = request.query_params.get('week')
        year = request.query_params.get('year', 2026)

        if not week or not year:
             return Response({"error": "Faltan parámetros week y year"}, status=400)

        # Construcción de la consulta avanzada utilizando el ORM de Django, excluyendo huérfanas (evita celdas vacías en frontend)
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
                #), 
                delimiter=', ', 
                distinct=True
            )
        ).order_by('date', 'turno')

        # 2. Ejecutamos la consulta SQL nativa del Calendario para las Estadísticas de Personal
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
        # Endpoint para guardar cambios masivos desde ExcelGrid
        updates = request.data.get('updates', [])
        for item in updates:
            TaskP.objects.filter(id=item['id']).update(estado_id=item['estado_id'])
        return Response({"status": "success"})
