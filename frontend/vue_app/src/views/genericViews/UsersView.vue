<template>
  <!-- Contenedor principal de la vista de mantenimiento de Usuarios -->
  <div class="generic-view">
    <!-- Instanciamos el componente ExcelGrid pasándole las propiedades necesarias -->
    <ExcelGrid
      title="Mantenimiento de Usuarios"
      :headers="headers"
      :data="gridData"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :totalItems="totalItems"
      :pageSize="pageSize"
      :serverSideFiltering="true"
      :filterData="filterData"
      :columnsConfig="columnsConfig"
      @save="handleSave"
      @delete="handleDelete"
      @pageChange="handlePageChange"
      @pageSizeChange="handlePageSizeChange"
      @filterChange="handleFilterChange"
      @sortChange="handleSortChange"
    />
    
    <!-- Muestra una capa superpuesta de carga si la variable loading es verdadera -->
    <div v-if="loading" class="loading-overlay">Cargando usuarios...</div>
    <!-- Muestra un mensaje de error en color rojo si la petición falla -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup>
// Importamos las utilidades de reactividad y ciclo de vida de Vue
import { ref, onMounted, computed } from 'vue';
// Importamos el componente reutilizable de grilla
import ExcelGrid from '../../components/ExcelGrid.vue';
// Importamos la instancia de Axios para las peticiones a la API
import { api } from '../../api';
// Importamos el composable global que maneja automáticamente loading y error
import { useApi } from './useApi';

// Definimos los nombres visibles de las columnas para la tabla apuntando a tu modelo personalizado
const headers = ['ID', 'Nombres', 'Apellidos', 'Correo', 'Rol', 'Grupo'];
// Ajustamos a las claves exactas de tu modelo personalizado en models.py
const colKeys = ['id', 'nombre', 'apellido', 'email', 'rol', 'group'];

// Creamos la variable reactiva que almacenará la matriz de datos para la grilla
const gridData = ref([]);
// Creamos la variable para los datos del menú de filtros del ExcelGrid
const filterData = ref([]);
// Almacenamos la lista de Grupos para el menú desplegable
const userPsList = ref([]);

// Extraemos las propiedades reactivas y la función ejecutora de nuestro composable
const { loading, error, execute } = useApi();

// --- Estado de Paginación y Filtrado ---
// Página actual de la tabla (inicia en 1)
const currentPage = ref(1);
// Total de páginas calculadas según los registros
const totalPages = ref(1);
// Total de ítems en la base de datos
const totalItems = ref(0);
// Cantidad de registros mostrados por página
const pageSize = ref(25);
// Objeto que almacena los filtros activos aplicados por columna
const currentFilters = ref({});
// Objeto que almacena la configuración de ordenamiento (columna y dirección)
const currentSort = ref({ colIndex: null, direction: null });

// --- Configuración de Columnas (Dropdown para Grupos) ---
const columnsConfig = computed(() => {
    return {
        5: { // Índice 5 corresponde a la columna 'Grupo'
            type: 'select',
            options: userPsList.value.map(g => ({ value: g.id, label: g.name }))
        }
    };
});

// Función que carga todos los datos para poblar los checkboxes de filtros
const loadFilterData = async () => {
    try {
        // Hacemos un GET pidiendo hasta 10000 registros para abarcar las opciones de filtrado
        const res = await api.get('users/', { params: { page_size: 10000 } });
        // Extraemos los resultados paginados o la lista cruda
        const results = res.data.results || res.data;
        
        // Mapeamos los objetos JSON a una matriz plana bidimensional para el ExcelGrid
        filterData.value = results.map(u => [
            u.id,
            u.nombre || '',
            u.apellido || '',
            u.email || '',
            u.rol || '',
            (u.group && typeof u.group === 'object') ? u.group.id : (u.group || '')
        ]);
    } catch(e) {
        // Si falla en silencio, lo registramos en consola (no bloquea la UI principal)
        console.error("Error al cargar los filtros:", e);
    }
};

// Función principal que trae los usuarios aplicando la paginación y filtros
const loadData = async (page = 1) => {
    // Usamos el composable execute para mostrar el spinner y capturar errores
    await execute(async () => {
        // Preparamos los parámetros de la URL (querystring)
        const params = { page, page_size: pageSize.value };
        
        // Iteramos los filtros activos para añadirlos a los parámetros de Django
        for (const [colIndex, values] of Object.entries(currentFilters.value)) {
            // Obtenemos el nombre real del campo (ej: 'nombre')
            const fieldName = colKeys[colIndex];
            // Procesamos los valores y si existe un filtro por vacíos, usamos __isnull
            if (fieldName && values.length > 0) {
                const vals = Array.from(values);
                const validVals = vals.filter(v => v !== '');
                if (validVals.length > 0) {
                    params[`${fieldName}__in`] = validVals.join(',');
                }
                if (vals.includes('')) {
                    params[`${fieldName}__isnull`] = 'True';
                }
            }
        }
        
        // Si hay un ordenamiento activo, lo añadimos a los parámetros
        if (currentSort.value.colIndex !== null) {
            // Obtenemos el campo por el que se quiere ordenar
            const fieldName = colKeys[currentSort.value.colIndex];
            if (fieldName) {
                // Si es descendente, agregamos el guion '-' que Django espera (ej: '-nombre')
                params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
            }
        }

        // Ejecutamos la petición GET a usuarios y grupos simultáneamente
        const [resUsers, resGroups] = await Promise.all([
            api.get('users/', { params }),
            api.get('userp/', { params: { page_size: 10000 } })
        ]);
        
        userPsList.value = resGroups.data.results || resGroups.data;
        const responseData = resUsers.data;
        let dataArray = [];

        // Si la respuesta viene paginada, extraemos la info correspondiente
        if (responseData && responseData.results) {
            dataArray = responseData.results;
            totalItems.value = responseData.count;
            totalPages.value = Math.ceil(responseData.count / pageSize.value);
            currentPage.value = page;
        } else if (Array.isArray(responseData)) {
            // Si la respuesta no está paginada, la usamos directamente
            dataArray = responseData;
            totalItems.value = dataArray.length;
            totalPages.value = 1;
            currentPage.value = 1;
        }

        // Transformamos los diccionarios en arrays planos en el orden de colKeys
        gridData.value = dataArray.map(u => [
            u.id,
            u.nombre || '',
            u.apellido || '',
            u.email || '',
            u.rol || '',
            (u.group && typeof u.group === 'object') ? u.group.id : (u.group || '')
        ]);
    // Mensaje de fallback en caso de que la petición rechace
    }, 'Error al cargar la lista de usuarios.');
};

// Funciones proxy que escuchan eventos del ExcelGrid y recargan los datos
const handlePageChange = (p) => loadData(p);
const handlePageSizeChange = (s) => { pageSize.value = s; loadData(1); };
const handleFilterChange = (f) => { currentFilters.value = f; loadData(1); };
const handleSortChange = (s) => { currentSort.value = s; loadData(1); };

// Función que guarda las ediciones o creaciones
const handleSave = async (updatedGrid) => {
    // 1. Validación previa en el Frontend para datos obligatorios
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    for (let i = 0; i < updatedGrid.length; i++) {
        const nombreVal = updatedGrid[i][1]; // Índice 1: Nombres
        const emailVal = updatedGrid[i][3];  // Índice 3: Correo
        
        if (!nombreVal || String(nombreVal).trim() === '') {
            alert(`No se puede guardar: El campo "Nombres" está vacío en la fila ${i + 1}.`);
            return; // Aborta el guardado
        }
        if (!emailVal || !emailRegex.test(String(emailVal).trim())) {
            alert(`No se puede guardar: El correo "${emailVal || 'vacío'}" en la fila ${i + 1} no tiene un formato válido (Ej: usuario@correo.com).`);
            return; // Aborta el guardado
        }
    }

    try {
        await execute(async () => {
            // Por cada fila modificada, generamos una promesa de Axios
            const promises = updatedGrid.map(row => {
                const payload = {};
                // Reconstruimos el JSON basado en las columnas
                colKeys.forEach((key, idx) => {
                    let val = row[idx] === '' ? null : row[idx];
                    payload[key] = val;
                });
                if (!payload.group) delete payload.group; // Evitar enviar group nulo si la FK no lo permite
                
                // Extraemos el ID y validamos que sea estrictamente un número (evita el Error 404)
                const id = payload.id;
                const isExisting = id && String(id).trim() !== '' && String(id).toLowerCase() !== 'nuevo' && !isNaN(Number(id));
                
                if (isExisting) {
                    return api.put(`users/${id}/`, payload);
                } else {
                    // Si no tiene ID, lo removemos y hacemos un POST para crear
                    delete payload.id;
                    return api.post('users/', payload);
                }
            });
            // Esperamos que todas las inserciones terminen en paralelo
            await Promise.all(promises);
            alert('Usuarios guardados correctamente.');
            // Recargamos los datos para reflejar los IDs nuevos del backend
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        // Solo alertamos visualmente, la consola la gestiona useApi
        alert('Error al guardar usuarios. Revisa los datos.');
    }
};

// Función para eliminar filas seleccionadas
const handleDelete = async (idsToDelete) => {
    // Prevenimos ejecución si el array viene vacío
    if (!idsToDelete || idsToDelete.length === 0) return;
    try {
        await execute(async () => {
            // Mapeamos los IDs a promesas de DELETE
            const promises = idsToDelete.map(id => api.delete(`users/${id}/`));
            // Disparamos todos los deletes a la vez
            await Promise.all(promises);
            alert(`${idsToDelete.length} usuario(s) eliminado(s).`);
            // Refrescamos la tabla
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (e) {
        alert('Error al eliminar usuarios.');
    }
};

// Hook de ciclo de vida que se ejecuta al entrar a la vista
onMounted(() => {
    // Gatilla la carga principal de datos
    loadData();
    // Gatilla la carga en segundo plano de los filtros
    loadFilterData();
});
</script>

<style scoped>
/* El contenedor usa alto total y posición relativa para anclar el overlay */
.generic-view { position: relative; height: 100%; }
/* Capa translúcida que bloquea la tabla mientras carga */
.loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.8); display: flex; justify-content: center; align-items: center; font-weight: bold; z-index: 100; }
/* Estilo clásico para alertas de error */
.error-message { color: red; padding: 10px; text-align: center; }
</style>