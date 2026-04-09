<template>
<div class="sidebar">
    <h2>Welcome</h2>
    <ul>
        <li><router-link to="/plants">Planta</router-link></li>
        <li><router-link to="/areas">Area</router-link></li>
        <li><router-link to="/sistems">Sistemas</router-link></li>
        <li><router-link to="/equipments">Equipos</router-link></li>
        <li><router-link to="/samples">Muestras</router-link></li>
        <li><router-link to="/assays">Ensayos</router-link></li>
        <li><router-link to="/tasks">Tareas</router-link></li>
        <li><router-link to="/stasks">Programadas</router-link></li>
        <li><router-link to="/ctasks">Correctivos</router-link></li>
        <li><router-link to="/weeklytasks">Tareas Semanal</router-link></li>
        <li><router-link to="/sampling">Muestreo</router-link></li>
        <li><router-link to="/excel-test">Prueba Excel</router-link></li>
        <li><router-link to="/calendario-grupos">Rotación de Grupos</router-link></li>

    </ul>
</div>
</template>
<script setup>
// import { useRegistrarStore } from '../modules/registro/stores/registrarStore';
// import { ref, watch } from 'vue';
// const registrarStore = useRegistrarStore();
</script>

<style scoped>
.sidebar {
    background-color: #cbd4e2ec; /* Color de fondo azul claro con transparencia */
    padding: 20px; /* Espaciado interno alrededor del contenido */
    width: 200px; /* Ancho fijo del sidebar */
    position: fixed; /* Fijo en la pantalla */
    top: 60px; /* Comienza justo debajo del header */
    left: 0; /* Pegado a la izquierda */
    bottom: 0; /* Se extiende hasta el final de la pantalla */
    overflow-y: auto; /* Permite scroll interno si el contenido es muy largo */
    z-index: 900; /* Debajo del header pero encima del contenido si fuera necesario */
}
</style>
