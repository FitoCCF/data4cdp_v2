<template>
  <Header></Header>
  <div class="container">
    <Sidebar></Sidebar>
    <main class="content" :class="{ 'content-expanded': isSidebarCollapsed }">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import Header from '../components/Header.vue';

const isSidebarCollapsed = ref(false);

const handleSidebarToggle = (event) => {
  if (event.detail && typeof event.detail.isCollapsed === 'boolean') {
    isSidebarCollapsed.value = event.detail.isCollapsed;
  }
};

onMounted(() => {
  window.addEventListener('sidebar-toggle', handleSidebarToggle);
});

onUnmounted(() => {
  window.removeEventListener('sidebar-toggle', handleSidebarToggle);
});
</script>

<style scoped>
.container {
  display: flex;
  margin-top: 60px; /* Altura del Header fijo */
}

.content {
  flex: 1;
  padding: 20px;
  margin-left: 240px; /* Ancho sincronizado con el nuevo Sidebar */
  width: calc(100% - 240px);
  min-height: calc(100vh - 60px);
  box-sizing: border-box;
  background-color: #f8fafc; /* Fondo suave para resaltar las grillas */
  transition: margin-left 0.25s ease-in-out, width 0.25s ease-in-out;
}

.content-expanded {
  margin-left: 64px;
  width: calc(100% - 64px);
}
</style>