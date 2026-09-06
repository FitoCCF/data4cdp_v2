<template>
  <aside class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- Encabezado del Sidebar con botón para colapsar/expandir -->
    <div class="sidebar-header">
      <div class="brand-title" v-if="!isCollapsed">
        <span class="brand-badge">SISTEMA</span>
        <span class="brand-name">CDP Toquepala</span>
      </div>
      <button 
        type="button" 
        class="toggle-btn" 
        @click="toggleSidebar" 
        :title="isCollapsed ? 'Expandir barra lateral' : 'Colapsar barra lateral'"
      >
        {{ isCollapsed ? '▶' : '◀' }}
      </button>
    </div>

    <!-- Contenedor con scroll de secciones -->
    <nav class="sidebar-nav">
      <!-- Iteración por cada grupo temático definido en menuGroups -->
      <div 
        v-for="group in menuGroups" 
        :key="group.id" 
        class="nav-group"
      >
        <!-- Título de la sección con soporte de acordeón colapsable -->
        <button 
          type="button" 
          class="group-header" 
          @click="toggleGroup(group.id)"
          :title="group.title"
        >
          <span class="group-title-text" v-if="!isCollapsed">{{ group.title }}</span>
          <span class="group-arrow" v-if="!isCollapsed">
            {{ openGroups[group.id] ? '▾' : '▸' }}
          </span>
        </button>

        <!-- Lista de enlaces del grupo (se muestra si está abierto) -->
        <ul 
          v-show="!isCollapsed && openGroups[group.id]" 
          class="group-items"
        >
          <li v-for="item in group.items" :key="item.path" class="nav-item">
            <router-link 
              :to="item.path" 
              class="nav-link" 
              active-class="active-link"
              exact-active-class="exact-active-link"
            >
              <span class="item-name">{{ item.name }}</span>
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <!-- Pie del sidebar con información de versión -->
    <div class="sidebar-footer" v-if="!isCollapsed">
      <small class="version-text">v1.2.0 • Data4CDP</small>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue';

// Control de colapso global del sidebar
const isCollapsed = ref(false);
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
  // Disparamos un evento personalizado en window para que MainView se entere del cambio de ancho
  window.dispatchEvent(new CustomEvent('sidebar-toggle', { detail: { isCollapsed: isCollapsed.value } }));
};

// Estado de acordeón de cada grupo
const openGroups = ref({
  dashboards: true,
  activos: true,
  mantenimiento: true,
  laboratorio: false,
  personal: false,
  utilitarios: false
});

const toggleGroup = (groupId) => {
  openGroups.value[groupId] = !openGroups.value[groupId];
};

/**
 * Definición estructurada de todo el mapa de navegación del sistema.
 * Preserva al 100% las rutas existentes hacia las vistas tipo ExcelGrid y Dashboards.
 */
const menuGroups = [
  {
    id: 'dashboards',
    title: 'Paneles & Control',
    items: [
      { name: 'Tareas Semanales', path: '/weeklytasks' },
      { name: 'Calendario Mensual', path: '/monthly-calendar' },
      { name: 'Rotación de Cuadrillas', path: '/calendario-grupos' },
      { name: 'Muestreo Courier', path: '/sampling' }
    ]
  },
  {
    id: 'activos',
    title: 'Estructura de Activos',
    items: [
      { name: 'Plantas', path: '/plants' },
      { name: 'Áreas', path: '/areas' },
      { name: 'Sistemas', path: '/sistems' }, // Mantiene la ruta '/sistems' original
      { name: 'Equipos', path: '/equipments' }
    ]
  },
  {
    id: 'mantenimiento',
    title: 'Gestión Mantenimiento',
    items: [
      { name: 'Plantillas Preventivas', path: '/tasks' },
      { name: 'Tareas Programadas', path: '/stasks' },
      { name: 'Tareas Correctivas', path: '/ctasks' }
    ]
  },
  {
    id: 'laboratorio',
    title: 'Metalurgia & Calidad',
    items: [
      { name: 'Muestras Físicas', path: '/samples' },
      { name: 'Ensayos Químicos', path: '/assays' }
    ]
  },
  {
    id: 'personal',
    title: 'Personal & Turnos',
    items: [
      { name: 'Usuarios', path: '/users' },
      { name: 'Grupos / Cuadrillas', path: '/userp' }
    ]
  },
  {
    id: 'utilitarios',
    title: 'Entorno de Pruebas',
    items: [
      { name: 'Prueba Cuadrícula', path: '/excel-test' }
    ]
  }
];
</script>

<style scoped>
/* ==========================================================================
   ESTILOS PRINCIPALES DE LA BARRA LATERAL (SIDEBAR)
   ========================================================================== */
.sidebar {
  background-color: #1e293b; /* Azul pizarra oscuro */
  color: #e2e8f0;
  width: 240px;
  position: fixed;
  top: 60px; /* Debajo del Header */
  left: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  transition: width 0.25s ease-in-out;
  z-index: 950;
  user-select: none;
}

.sidebar-collapsed {
  width: 64px;
}

/* Encabezado */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #334155;
  background-color: #0f172a;
}

.brand-title {
  display: flex;
  flex-direction: column;
}

.brand-badge {
  font-size: 0.65rem;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: 0.08em;
}

.brand-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #ffffff;
}

.toggle-btn {
  background: transparent;
  border: 1px solid #475569;
  color: #94a3b8;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background-color: #334155;
  color: #ffffff;
}

/* Navegación y Grupos */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.nav-group {
  margin-bottom: 4px;
}

.group-header {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.15s, color 0.15s;
}

.group-header:hover {
  background-color: #334155;
  color: #f1f5f9;
}

.group-title-text {
  flex: 1;
}

.group-arrow {
  font-size: 0.7rem;
  color: #64748b;
}

/* Elementos del menú */
.group-items {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin: 1px 0;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 7px 16px 7px 38px;
  color: #cbd5e1;
  text-decoration: none;
  font-size: 0.85rem;
  transition: all 0.15s ease-in-out;
  border-left: 3px solid transparent;
}

.nav-link:hover {
  background-color: rgba(51, 65, 85, 0.6);
  color: #ffffff;
}

.active-link,
.exact-active-link {
  background-color: #0284c7; /* Azul corporativo destacado */
  color: #ffffff !important;
  font-weight: 600;
  border-left-color: #38bdf8;
}

/* Pie del Sidebar */
.sidebar-footer {
  padding: 10px 16px;
  border-top: 1px solid #334155;
  background-color: #0f172a;
  text-align: center;
}

.version-text {
  color: #64748b;
  font-size: 0.7rem;
}
</style>
