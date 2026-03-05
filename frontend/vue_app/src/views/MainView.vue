<template>
    <Header></Header>
<div class="container">
    <sidebar></sidebar>
    <div class="content">
        <router-view></router-view>
    </div>

</div>
</template>

<script setup>
import Sidebar from '../components/Sidebar.vue';
import Header from '../components/Header.vue';

</script>

<style scoped>
.container {
    display: flex;
    margin-top: 60px; /* Espacio para el header fijo */
}

.content {
    flex: 1;
    padding: 20px;
    margin-left: 200px; /* Espacio para el sidebar fijo */
    width: calc(100% - 200px); /* Ancho restante */
}
</style>