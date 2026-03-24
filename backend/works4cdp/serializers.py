from rest_framework import serializers
from .models import *
import math

# Serializer para cada modelo
class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = '__all__'

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'

class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class UserPSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserP
        fields = '__all__'

class TaskPSerializer(serializers.ModelSerializer):
    # En vista STasksViews.vue, el frontend espera que 'task' sea un objeto para ver su nombre (task.name)
    # y en otras partes lo maneja como ID.
    # El modelo TaskP tiene FK 'task'.
    # Si serializamos solo el ID, el frontend no puede mostrar 'Tarea X' (nombre).
    # Necesitamos anidar Task en GET o enviar un campo extra 'task_name'.
    
    # Solucion: TaskReadSerializer para GET y TaskWriteSerializer para POST/PUT
    # O usar to_representation.
    
    task = TaskSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), source='task', write_only=True
    )
    
    # Lo mismo para UserP y Estado
    usuario = UserPSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=UserP.objects.all(), source='usuario', write_only=True, allow_null=True
    )
    
    estado = EstadoSerializer(read_only=True)
    estado_id = serializers.PrimaryKeyRelatedField(
        queryset=Estado.objects.all(), source='estado', write_only=True
    )

    class Meta:
        model = TaskP
        # 'fields' debe incluir los campos de escritura (_id) explícitamente si usamos '__all__'
        # pero como estamos redefiniendo 'task', 'usuario', 'estado' que coinciden con los nombres del modelo,
        # DRF los usa. Los campos '_id' son adicionales y write_only.
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CorrectiveTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectiveTask
        fields = '__all__'




class CalendarSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )
    group = UserPSerializer(read_only=True)
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=UserP.objects.all(), source='group', write_only=True
    )

    class Meta:
        model = Calendar
        fields = '__all__'


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = '__all__'

class AssaySerializer(serializers.ModelSerializer):
    # En AssayView el frontend espera que 'sample' sea un objeto a veces (para obtener sample.equipment),
    # o espera 'sample_id' si es solo ID.
    # AssaysView.vue linea 108: if (key === 'sample' && typeof assay[key] === 'object' && assay[key] !== null) ...
    # Esto indica que el frontend espera o maneja un objeto anidado en 'sample'.
    # Pero para escritura (POST/PUT) necesitamos enviar ID.
    
    # Solución híbrida estándar DRF:
    # Sobreescribir 'to_representation' para GET (devuelve objeto o ID enriquecido)
    # y dejar 'sample' como PrimaryKeyRelatedField por defecto para POST/PUT.

    # Opcion 2 (Mas simple): Dejar como está (ID) y que frontend cargue Samples aparte
    # y haga el match, PERO AssaysView.vue ya tiene lógica para filtrar por equipment usando sample__equipment
    # y renderizar sample.id si es objeto.
    
    # Vamos a exponer sample como objeto completo en GET para facilitar al frontend
    # ver el ID y otros datos, pero permitiendo escritura por ID.
    
    sample = SampleSerializer(read_only=True)
    sample_id = serializers.PrimaryKeyRelatedField(
        queryset=Sample.objects.all(), source='sample', write_only=True, allow_null=True
    )

    class Meta:
        model = Assay
        fields = '__all__'

    def to_representation(self, instance):
        # Convertir NaN a None para evitar errores de JSON
        data = super().to_representation(instance)
        for key, value in data.items():
            if isinstance(value, float) and math.isnan(value):
                data[key] = None
        return data
