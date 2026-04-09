from django.db import connection
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.contrib.postgres.aggregates import StringAgg

# ViewSet para cada modelo con un nuevo endpoint `/schema/`
class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in'],
        'estado_nombre': ['exact', 'in', 'icontains']
    }
    ordering_fields = ['id', 'estado_nombre']

    # Endpoint `/schema/`
    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Estado._meta.fields]  # Lista de campos del modelo
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
        'id': ['exact', 'in'],
        'tag': ['exact', 'in', 'icontains'],
        'name': ['exact', 'in', 'icontains'],
        'description': ['exact', 'in', 'icontains']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados (ej: ?ordering=name)
    ordering_fields = ['id', 'tag', 'name', 'description']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Plant._meta.fields]
        return Response({'fields': fields})

class AreaViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Area
    queryset = Area.objects.all()
    # Define el serializador encargado de convertir objetos Area a JSON (y viceversa)
    serializer_class = AreaSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in'],
        'tag': ['exact', 'in', 'icontains'],
        'name': ['exact', 'in', 'icontains'],
        'description': ['exact', 'in', 'icontains'],
        'plant': ['exact', 'in']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description', 'plant']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Area._meta.fields]
        return Response({'fields': fields})

class SystemViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo System
    queryset = System.objects.all()
    # Define el serializador encargado de convertir objetos System a JSON (y viceversa)
    serializer_class = SystemSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in'],
        'tag': ['exact', 'in', 'icontains'],
        'name': ['exact', 'in', 'icontains'],
        'description': ['exact', 'in', 'icontains']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in System._meta.fields]
        return Response({'fields': fields})

class EquipmentViewSet(viewsets.ModelViewSet):
    # Consulta base que obtiene todos los registros del modelo Equipment
    queryset = Equipment.objects.all()
    # Define el serializador encargado de convertir objetos Equipment a JSON (y viceversa)
    serializer_class = EquipmentSerializer
    # Configura los backends de filtrado: DjangoFilterBackend para igualdades/IN y OrderingFilter para ordenar
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # Especifica explícitamente qué campos pueden ser usados como filtros
    filterset_fields = {
        'id': ['exact', 'in'],
        'tag': ['exact', 'in', 'icontains'],
        'name': ['exact', 'in', 'icontains'],
        'description': ['exact', 'in', 'icontains'],
        'system': ['exact', 'in'],
        'area': ['exact', 'in']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'tag', 'name', 'description', 'system', 'area']


    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Equipment._meta.fields]
        return Response({'fields': fields})

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    # Habilitar filtros y ordenamiento
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    # Definir campos de filtrado
    filterset_fields = {
        'id': ['exact', 'in'],
        'name': ['exact', 'in', 'icontains'],
        'duration': ['exact', 'in'],
        'workers': ['exact', 'in'],
        'frequency': ['exact', 'in', 'icontains'],
        'start_date': ['exact', 'in', 'gte', 'lte'],
        'description': ['exact', 'in', 'icontains'],
        'procedure': ['exact', 'in', 'icontains'],
        'turn': ['exact', 'in', 'icontains'],
        'equipment': ['exact', 'in']
    }
    
    # Definir campos de ordenamiento
    ordering_fields = ['id', 'name', 'duration', 'workers', 'frequency', 'start_date', 'description', 'procedure', 'turn', 'equipment']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Task._meta.fields]
        return Response({'fields': fields})

class TaskPViewSet(viewsets.ModelViewSet):
    queryset = TaskP.objects.all()
    serializer_class = TaskPSerializer
    
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
        'id': ['exact', 'in'],
        'task': ['exact', 'in'],
        'year': ['exact', 'in', 'gte', 'lte'],
        'week': ['exact', 'in', 'gte', 'lte'],
        'date': ['exact', 'in', 'gte', 'lte'],
        'estado': ['exact', 'in'],
        'group': ['exact', 'in'], # Cambiado de 'usuario' a 'group' según tu models.py
        'rescheduled': ['exact']
    }
    
    # Definir campos de ordenamiento
    ordering_fields = ['id', 'task', 'year', 'week', 'day', 'date', 'usuario', 'estado', 'priority', 'rescheduled']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in TaskP._meta.fields]
        return Response({'fields': fields})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in'],
        'nombre': ['exact', 'in', 'icontains'],
        'apellido': ['exact', 'in', 'icontains'],
        'email': ['exact', 'in', 'icontains']
    }
    ordering_fields = ['id', 'nombre', 'apellido', 'email']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in User._meta.fields]
        return Response({'fields': fields})

class CorrectiveTaskViewSet(viewsets.ModelViewSet):
    queryset = CorrectiveTask.objects.all()
    serializer_class = CorrectiveTaskSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in'],
        'description': ['exact', 'in', 'icontains'],
        'equipment': ['exact', 'in']
    }
    ordering_fields = ['id', 'equipment']

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
        'id': ['exact', 'in'],
        'tag': ['exact', 'in', 'icontains'],
        'name': ['exact', 'in', 'icontains'],
        'equipment': ['exact', 'in']
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
        'id': ['exact', 'in'],
        'date': ['exact', 'in', 'gte', 'lte'],
        'time': ['exact', 'in'],
        'sample': ['exact', 'in'],
        'sample__equipment': ['exact', 'in'],
        'user': ['exact', 'in']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'date', 'time', 'sample', 'user']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Assay._meta.fields]
        return Response({'fields': fields})

class CalendarViewSet(viewsets.ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in'],
        'date': ['exact', 'in', 'gte', 'lte'],
        'year': ['exact', 'in'],
        'week': ['exact', 'in'],
        'group': ['exact', 'in'],
        'turn': ['exact', 'in', 'icontains']
    }
    ordering_fields = ['id', 'date', 'year', 'week']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Calendar._meta.fields]
        return Response({'fields': fields})

class UserPViewSet(viewsets.ModelViewSet):  # Permite CRUD completo
    queryset = UserP.objects.all()


class UserPViewSet(viewsets.ModelViewSet):  # Permite CRUD completo
    queryset = UserP.objects.all()
    serializer_class = UserPSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'id': ['exact', 'in'],
        'name': ['exact', 'in', 'icontains'],
    }
    ordering_fields = ['id', 'name']


class WeeklyTaskView(APIView):
    def get(self, request):
        week = request.query_params.get('week')
        year = request.query_params.get('year', 2026)

        if not week or not year:
             return Response({"error": "Faltan parámetros week y year"}, status=400)

        # Construcción de la consulta avanzada utilizando el ORM de Django
        tareas = TaskP.objects.filter(
            week=week, 
            year=year
        ).values(
            'id', 
            'date',
            'estado_id',
            anio=F('year'),
            semana=F('week'),
            fecha=F('date'),
            dia_semana=F('day'),
            planta=F('task__equipment__area__plant__name'),
            area=F('task__equipment__area__name'),
            sistema=F('task__equipment__system__name'),
            tarea_descripcion=F('task__name'),
            tarea_detalle=F('task__description'),
            equipo=F('task__equipment__name'),
            equipo_desc=F('task__equipment__description'),
            turno=F('task__turn'),
            estado_nombre=F('estado__estado_nombre')
        ).annotate(
            cuadrilla_grupo=StringAgg(
                'taskgroupassignment__calendar__group__name', 
                delimiter=' / ', 
                distinct=True
            ),
            usuarios_asignados=StringAgg(
                'taskgroupassignment__calendar__group__user__nombre', 
                 
                
                #Concat(
                #    'taskgroupassignment__calendar__group__user__nombre', 
                #    Value(' '), 
                #    'taskgroupassignment__calendar__group__user__apellido'
                #), 
                delimiter=', ', 
                distinct=True
            )
        ).order_by('date', 'task__turn')

        return Response(list(tareas))

    def post(self, request):
        # Endpoint para guardar cambios masivos desde ExcelGrid
        updates = request.data.get('updates', [])
        for item in updates:
            TaskP.objects.filter(id=item['id']).update(estado_id=item['estado_id'])
        return Response({"status": "success"})
