<template>
    <div>
      <BaseTable title="Tareas" :columns="[
        'id',
         'name',
         'duration',
         'workers',
         'frequency',
         'start_date',
         'description',
         'procedure',
         'turn',
         'equipment'
         ]" :items="tasks" />
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { api } from '../../api';
  import BaseTable from '../../components/BaseTable.vue';
  
  const tasks = ref([]);
  
  onMounted(async () => {
    try {
      const response = await api.get('tasks/');
      tasks.value = response.data;
    } catch (error) {
      console.error("Error al obtener plantas:", error);
    }
  });
  </script>
  