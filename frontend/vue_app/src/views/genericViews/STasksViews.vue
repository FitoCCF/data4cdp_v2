

<template>
  <div>
    <BaseTable title="TAREAS PROGRAMADAS" :columns="[
    'planta',
    'sistema',
    'equipo',
    'descripcion',
    'tarea_descripcion',
    'semana',
    'fecha',
    'dia_semana',
    'estado',
    'turno'

          ]" :items="vtaskp" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { api } from '../../api';
import BaseTable from '../../components/BaseTable.vue';

const vtaskp = ref([]);

onMounted(async () => {
  try {
    const response = await api.get('vtaskp/');
    vtaskp.value = response.data;
  } catch (error) {
    console.error("Error al obtener plantas:", error);
  }
});
</script>
