from django.db import connection
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework.views import APIView
from .serializers import VTaskPSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# ViewSet para cada modelo con un nuevo endpoint `/schema/`
class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer

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

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Task._meta.fields]
        return Response({'fields': fields})

class TaskPViewSet(viewsets.ModelViewSet):
    queryset = TaskP.objects.all()
    serializer_class = TaskPSerializer

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in TaskP._meta.fields]
        return Response({'fields': fields})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in User._meta.fields]
        return Response({'fields': fields})

class CorrectiveTaskViewSet(viewsets.ModelViewSet):
    queryset = CorrectiveTask.objects.all()
    serializer_class = CorrectiveTaskSerializer

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
        'userp': ['exact', 'in']
    }
    # Especifica explícitamente qué campos pueden usarse para ordenar los resultados
    ordering_fields = ['id', 'date', 'time', 'sample', 'userp']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        fields = [field.name for field in Assay._meta.fields]
        return Response({'fields': fields})


class VTaskPViewSet(viewsets.ReadOnlyModelViewSet):  # Solo lectura
    queryset = VTaskP.objects.all()
    serializer_class = VTaskPSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['semana']

    @action(detail=False, methods=['put'], url_path='update-estado')
    def update_estado(self, request):
        """
        Endpoint para actualizar el estado de las tareas filtradas por semana.
        """
        try:
            # Obtener los datos del request
            id_taskp = request.data.get("id_taskp")  # Identificador de la tarea
            nuevo_estado_nombre = request.data.get("estado")  # Nuevo estado
            semana = request.data.get("semana")  # Semana para filtrar

            if not id_taskp or not nuevo_estado_nombre or not semana:
                return Response({"error": "Faltan parámetros: id_taskp, estado o semana"}, status=status.HTTP_400_BAD_REQUEST)

            # Verificar que la tarea esté en la semana filtrada
            tarea = get_object_or_404(VTaskP, id_taskp=id_taskp, semana=semana)

            # Obtener la tarea real en TaskP para actualizar su estado
            taskp = get_object_or_404(TaskP, id=id_taskp)

            # Buscar el objeto Estado en la base de datos
            nuevo_estado = get_object_or_404(Estado, estado_nombre=nuevo_estado_nombre)

            # Actualizar el estado en la tabla TaskP
            taskp.estado = nuevo_estado
            taskp.save()

            return Response({"message": f"Estado actualizado exitosamente para la tarea {id_taskp}"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserPViewSet(viewsets.ModelViewSet):  # Permite CRUD completo
    queryset = UserP.objects.all()
    serializer_class = UserPSerializer
