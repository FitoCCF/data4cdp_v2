# Estructura del Proyecto Frontend (`vue_app`)

Este documento detalla la estructura actual del proyecto Vue 3, el propósito de cada directorio y la validez de los archivos encontrados, basado en los estándares modernos de Vue, Vite y buenas prácticas de arquitectura.

## Directorios Principales en `src/`

### 1. `assets/`
*   **Propósito:** Almacenar activos estáticos que serán procesados e incluidos en el bundle final por Vite (imágenes, fuentes locales, CSS global).
*   **Contenido Actual:**
    *   `vue.svg`: Logo por defecto de Vue.
*   **Validez:** ✅ Correcta.
*   **Recomendación:** Mover `src/style.css` aquí (como `main.css`).

### 2. `components/`
*   **Propósito:** Componentes de Vue reutilizables ("Dumb Components") que reciben props y emiten eventos, sin lógica de negocio compleja ni acceso directo a la API/Router.
*   **Contenido Actual:**
    *   `BaseTable.vue`: Tabla genérica simple.
    *   `Header.vue`, `Sidebar.vue`: Elementos de layout.
    *   `ScheduleTable.vue`, `TableComponent.vue`: Tablas con lógica más específica.
    *   `Weather.vue`: Widget del clima.
*   **Validez:** ✅ Correcta.

### 3. `views/`
*   **Propósito:** Componentes de página ("Smart Components") que se cargan a través del Router. Conectan los componentes con los datos (Stores/API).
*   **Contenido Actual:**
    *   `MainView.vue`: Vista principal.
    *   `genericViews/`: Subdirectorio con vistas CRUD (ej. `PlantsView.vue`, `AreasView.vue`).
*   **Validez:** ✅ Correcta. La subcarpeta `genericViews` es una buena práctica para agrupar vistas relacionadas.

### 4. `stores/`
*   **Propósito:** Definición de estados globales usando Pinia.
*   **Contenido Actual:**
    *   `weatherStore.js`: Store para manejar datos del clima.
*   **Validez:** ✅ Correcta.

### 5. `router/`
*   **Propósito:** Configuración de rutas de Vue Router.
*   **Contenido Actual:**
    *   `index.js`: Definición de todas las rutas de la aplicación.
*   **Validez:** ✅ Correcta.

### 6. `composable/` (Debería ser `composables/`)
*   **Propósito:** Lógica de estado/negocio reutilizable (Vue Composition API Hooks).
*   **Contenido Actual:**
    *   `useWeather.js`: Hook para lógica del clima.
*   **Validez:** ⚠️ **Nombre mejorable**. El estándar es plural: `composables`. La ubicación y contenido son correctos.

### 7. `helpers/`
*   **Propósito:** Funciones utilitarias puras (Javascript vanilla) que no dependen de Vue.
*   **Contenido Actual:**
    *   `getWeather.js`: Función para llamar a la API del clima.
*   **Validez:** ✅ Correcta. También llamado a veces `utils/`.

### 8. `modules/`
*   **Propósito:** Módulos funcionales encapsulados (a veces usado en arquitecturas basadas en dominio).
*   **Contenido Actual:** carpetas `contador`, `listadetareas`, `registro`.
*   **Validez:** ✅ Válida si se sigue una arquitectura modular (Domain Driven), aunque menos común en proyectos pequeños que suelen usar solo `views/components`.

---

## Archivos en Raíz de `src/`

*   `App.vue`: Componente raíz. ✅ Correcto.
*   `main.js`: Punto de entrada de la aplicación (montaje de Vue, Pinia, Router). ✅ Correcto.
*   `api.js`: Configuración de Axios. ✅ Válido (aunque comúnmente se mueve a `src/services/` o `src/api/`).
*   `style.css`: Estilos globales. ⚠️ Válido, pero se recomienda mover a `assets/`.
