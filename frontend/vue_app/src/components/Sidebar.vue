<template>
<div class="sidebar">
    <h2>Welcome</h2>
    <!-- Lista de enlaces de navegación para las diferentes vistas del sistema -->
    <ul>
        <!-- Enlace para la gestión de Plantas industriales -->
        <li><router-link to="/plants">Planta</router-link></li>
        <!-- Enlace para la gestión de Áreas operativas dentro de las plantas -->
        <li><router-link to="/areas">Area</router-link></li>
        <!-- Enlace para la gestión de Sistemas funcionales que agrupan equipos -->
        <li><router-link to="/sistems">Sistemas</router-link></li>
        <!-- Enlace para la gestión de Equipos físicos y maquinarias -->
        <li><router-link to="/equipments">Equipos</router-link></li>
        <!-- Enlace para el registro y gestión de Muestras de laboratorio -->
        <li><router-link to="/samples">Muestras</router-link></li>
        <!-- Enlace para la captura y gestión de Ensayos químicos/granulométricos -->
        <li><router-link to="/assays">Ensayos</router-link></li>
        <!-- Enlace para la gestión de Plantillas de Tareas de mantenimiento preventivo (Task) -->
        <li><router-link to="/tasks">Tareas</router-link></li>
        <!-- Enlace para el seguimiento de Tareas Programadas (TaskP) -->
        <li><router-link to="/stasks">Programadas</router-link></li>
        <!-- Enlace para el mantenimiento y registro de Tareas Correctivas imprevistas (CorrectiveTask) -->
        <li><router-link to="/ctasks">Correctivos</router-link></li>
        <!-- Enlace para la visualización del cronograma y planificación de Tareas Semanales -->
        <li><router-link to="/weeklytasks">Tareas Semanal</router-link></li>
        <!-- Enlace para el control y planificación del Muestreo -->
        <li><router-link to="/sampling">Muestreo</router-link></li>
        <!-- Enlace para probar el componente de cuadrícula Excel interactiva -->
        <li><router-link to="/excel-test">Prueba Excel</router-link></li>
        <!-- Enlace para la configuración del calendario y Rotación de Grupos de trabajo -->
        <li><router-link to="/calendario-grupos">Rotación de Grupos</router-link></li>
        <!-- Enlace para el mantenimiento de Usuarios del sistema (User) -->
        <li><router-link to="/users">Usuarios</router-link></li>
        <!-- Enlace para el mantenimiento de Grupos personalizados de usuarios (UserP) -->
        <li><router-link to="/userp">Grupos</router-link></li>
        <!-- Enlace para ver y gestionar la planificación en el Calendario Mensual -->
        <li><router-link to="/monthly-calendar">Calendario Mensual</router-link></li>
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
