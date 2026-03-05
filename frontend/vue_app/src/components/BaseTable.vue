<template>
  <div class="table-container">
    <div class="table-header">
      <h2>{{ title }}</h2>
    </div>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col">{{ formatHeader(col) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in items" :key="item.id || index">
            <td v-for="col in columns" :key="col">
              {{ item[col] }}
            </td>
          </tr>
          <tr v-if="items.length === 0">
            <td :colspan="columns.length" class="no-data">No hay datos disponibles</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  title: {
    type: String,
    default: 'Tabla'
  },
  columns: {
    type: Array,
    required: true
  },
  items: {
    type: Array,
    default: () => []
  }
});

const formatHeader = (header) => {
  return header.charAt(0).toUpperCase() + header.slice(1);
};
</script>

<style scoped>
/* Estilos eliminados: ahora se usan los globales en src/style.css */
/* Mantenemos .base-table-container y .header mapeados a las clases globales si es necesario, 
   o simplemente dejamos que el HTML use las clases que ya tiene y el CSS global las estilice.
   En este caso, como los nombres de clase en el template coinciden con los globales de style.css (.table-container vs .base-table-container),
   necesitamos ajustar el template O renombrar las clases globales.
   He llamado a la clase global .table-container, pero el componente usa .base-table-container.
   Voy a actualizar el template del componente para usar .table-container y .table-header
*/

</style>
