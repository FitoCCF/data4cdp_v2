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

class TaskPSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskP
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CorrectiveTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectiveTask
        fields = '__all__'


class VTaskPSerializer(serializers.ModelSerializer):
    class Meta:
        model = VTaskP
        fields = '__all__'



class UserPSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserP
        fields = '__all__'


class SampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = '__all__'

class AssaySerializer(serializers.ModelSerializer):
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
