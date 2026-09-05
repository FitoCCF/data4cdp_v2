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

    <!-- Buscador rápido de módulos (visible solo si está expandido) -->
    <div class="search-box" v-if="!isCollapsed">
      <span class="search-icon">🔍</span>
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="Buscar vista o tabla..." 
        class="search-input"
      />
      <button v-if="searchQuery" @click="searchQuery = ''" class="clear-search-btn">✕</button>
    </div>

    <!-- Contenedor con scroll de secciones -->
    <nav class="sidebar-nav">
      <!-- Iteración por cada grupo temático definido en menuGroups -->
      <div 
        v-for="group in filteredGroups" 
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
          <span class="group-icon">{{ group.icon }}</span>
          <span class="group-title-text" v-if="!isCollapsed">{{ group.title }}</span>
          <span class="group-arrow" v-if="!isCollapsed">
            {{ openGroups[group.id] ? '▾' : '▸' }}
          </span>
        </button>

        <!-- Lista de enlaces del grupo (se muestra si está abierto o si hay búsqueda activa) -->
        <ul 
          v-show="isCollapsed ? false : (openGroups[group.id] || searchQuery.trim() !== '')" 
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
              <!-- Badge indicativo de la naturaleza de la vista -->
              <span 
                v-if="item.badge" 
                class="item-badge" 
                :class="'badge-' + item.badge.toLowerCase()"
              >
                {{ item.badge }}
              </span>
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
import { ref, computed } from 'vue';

// Control de colapso global del sidebar
const isCollapsed = ref(false);
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
  // Disparamos un evento personalizado en window para que MainView se entere del cambio de ancho
  window.dispatchEvent(new CustomEvent('sidebar-toggle', { detail: { isCollapsed: isCollapsed.value } }));
};

// Término de búsqueda en el sidebar
const searchQuery = ref('');

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
    icon: '📊',
    items: [
      { name: 'Tareas Semanales', path: '/weeklytasks', badge: 'Dashboard' },
      { name: 'Calendario Mensual', path: '/monthly-calendar', badge: 'Dashboard' },
      { name: 'Rotación de Cuadrillas', path: '/calendario-grupos', badge: 'Turnos' },
      { name: 'Muestreo Courier', path: '/sampling', badge: 'Reporte' }
    ]
  },
  {
    id: 'activos',
    title: 'Estructura de Activos',
    icon: '🏗️',
    items: [
      { name: 'Plantas', path: '/plants', badge: 'Excel' },
      { name: 'Áreas', path: '/areas', badge: 'Excel' },
      { name: 'Sistemas', path: '/sistems', badge: 'Excel' }, // Mantiene la ruta '/sistems' original
      { name: 'Equipos', path: '/equipments', badge: 'Excel' }
    ]
  },
  {
    id: 'mantenimiento',
    title: 'Gestión Mantenimiento',
    icon: '🛠️',
    items: [
      { name: 'Plantillas Preventivas', path: '/tasks', badge: 'Pautas' },
      { name: 'Tareas Programadas', path: '/stasks', badge: 'Excel' },
      { name: 'Tareas Correctivas', path: '/ctasks', badge: 'Fallas' }
    ]
  },
  {
    id: 'laboratorio',
    title: 'Metalurgia & Calidad',
    icon: '🧪',
    items: [
      { name: 'Muestras Físicas', path: '/samples', badge: 'Excel' },
      { name: 'Ensayos Químicos', path: '/assays', badge: 'Excel' }
    ]
  },
  {
    id: 'personal',
    title: 'Personal & Turnos',
    icon: '👥',
    items: [
      { name: 'Usuarios', path: '/users', badge: 'Excel' },
      { name: 'Grupos / Cuadrillas', path: '/userp', badge: 'Excel' }
    ]
  },
  {
    id: 'utilitarios',
    title: 'Entorno de Pruebas',
    icon: '⚙️',
    items: [
      { name: 'Prueba Cuadrícula', path: '/excel-test', badge: 'Lab' }
    ]
  }
];

/**
 * Filtra los grupos e ítems reactivamente según lo que escribe el usuario en la barra de búsqueda.
 */
const filteredGroups = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return menuGroups;

  return menuGroups
    .map(group => {
      const matchingItems = group.items.filter(item => 
        item.name.toLowerCase().includes(query) || 
        (item.badge && item.badge.toLowerCase().includes(query))
      );
      return {
        ...group,
        items: matchingItems
      };
    })
    .filter(group => group.items.length > 0);
});
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

/* Buscador de vistas */
.search-box {
  padding: 8px 12px;
  position: relative;
  background-color: #1e293b;
  border-bottom: 1px solid #334155;
}

.search-input {
  width: 100%;
  box-sizing: border-box;
  background-color: #0f172a;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 6px 26px 6px 28px;
  color: #f8fafc;
  font-size: 0.8rem;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #38bdf8;
}

.search-icon {
  position: absolute;
  left: 18px;
  top: 14px;
  font-size: 0.75rem;
  color: #64748b;
}

.clear-search-btn {
  position: absolute;
  right: 18px;
  top: 13px;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.75rem;
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
  gap: 10px;
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

.group-icon {
  font-size: 1rem;
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
  justify-content: space-between;
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

/* Badges indicativos */
.item-badge {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge-dashboard {
  background-color: #065f46;
  color: #6ee7b7;
}

.badge-excel {
  background-color: #1e3a8a;
  color: #93c5fd;
}

.badge-turnos,
.badge-pautas {
  background-color: #78350f;
  color: #fcd34d;
}

.badge-fallas {
  background-color: #7f1d1d;
  color: #fca5a5;
}

.badge-reporte,
.badge-lab {
  background-color: #475569;
  color: #e2e8f0;
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
