<template>
    <div class="header">
        
         <h3>Control de Proceoso Toquepala</h3>
    </div>
</template>
<script setup>

</script>
<style scoped>
.header {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 60px; /* Altura fija para el header */
    padding: 0 20px; /* Padding horizontal, vertical manejado por height/flex */
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    background-color: #333;
    color: white;
    z-index: 1000; /* Asegura que esté por encima de otros elementos */
    box-sizing: border-box; /* Incluye padding en el cálculo de altura */
}
h3 {
    margin: 0;
}
</style>