<template>
  <div class="assays-view">
    <!-- Selector de Equipo en la Cabecera -->
    <div class="header-actions">
      <label for="equipment-select">Filtrar por Analizador:</label>
      <select
        id="equipment-select"
        v-model="selectedEquipmentId"
        @change="handleEquipmentChange"
        class="equipment-select"
        :disabled="loading"
      >
        <option :value="null" disabled>-- Seleccione un Analizador --</option>
        <option v-for="eq in equipmentsList" :key="eq.id" :value="eq.id">
          {{ eq.name }} {{ eq.description ? `- ${eq.description}` : '' }}
        </option>
      </select>
    </div>

    <!-- Solo mostrar el grid si hay un equipo seleccionado -->
    <div v-if="selectedEquipmentId" class="grid-container">
        <ExcelGrid
          title="Mantenimiento de Ensayos"
          :headers="headers"
          :data="assaysData"
          :columnsConfig="columnsConfig"
          :currentPage="currentPage"
          :totalPages="totalPages"
          :totalItems="totalItems"
          :pageSize="pageSize"
          :serverSideFiltering="true"
          :filterData="filterData"
          @save="handleSave"
          @delete="handleDelete"
          @pageChange="handlePageChange"
          @pageSizeChange="handlePageSizeChange"
          @filterChange="handleFilterChange"
          @sortChange="handleSortChange"
        />
    </div>

    <!-- Mensaje cuando no hay equipo seleccionado -->
    <div v-else class="no-selection-msg">
        Por favor, seleccione un analizador en el menú superior para ver sus ensayos.
    </div>

    <!-- Overlay de carga -->
    <div v-if="loading" class="loading-overlay">Cargando datos...</div>

    <!-- Mensaje de error detallado -->
    <div v-if="error" class="error-message">
        <p><strong>Error:</strong></p>
        <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import ExcelGrid from '../../components/ExcelGrid.vue';
import { api } from '../../api';
// Importación explícita del composable useApi
import { useApi } from './useApi';

// ============================================================================
// 1. CONFIGURACIÓN DE COLUMNAS
// ============================================================================
const headers = [
  'ID', 'Fecha', 'Hora', 'Instancia', 'N1 Fe', 'N2 Cu', 'N3 Zn', 'N4 Mo',
  'N5 Ech5', 'N6 Sc', 'N7 Ech7', '% Fe', '% Cu', '% Zn', '% Mo', '% Ins', '% Sol',
  'Tara', 'Peso Total', 'Peso Seco', 'Peso Prod.', 'Chemical ID',
  'Muestra', 'A1 Fe', 'A2 Cu', 'A3 Zn', 'A4 Mo', 'A5 A5', 'A6 Sol', 'A7 A7',
  'Usuario', 'Meta User'
];

const colKeys = [
  'id', 'date', 'time', 'instance', 'n1fe', 'n2cu', 'n3zn', 'n4mo',
  'n5ech5', 'n6sc', 'n7ech7', 'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pSol',
  'tara', 'tweight', 'dweight', 'pweight', 'chemical_id',
  'sample', 'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7',
  'user', 'meta_user'
];

// ============================================================================
// 2. ESTADO REACTIVO
// ============================================================================
const assaysData = ref([]);
const equipmentsList = ref([]);
const samplesList = ref([]); // Lista de muestras del equipo seleccionado
const usersList = ref([]);   // Lista de usuarios

const selectedEquipmentId = ref(null);

// Inyectamos el estado de red a través de useApi
const { loading, error, execute } = useApi();

// Estado Paginación y Filtrado
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]);

// ============================================================================
// 3. PROPIEDADES COMPUTADAS (Dropdowns en el Grid)
// ============================================================================
const columnsConfig = computed(() => {
    // La clave '22' corresponde al índice de 'sample' (Muestra) en colKeys
    // La clave '30' corresponde al índice de 'user' (Usuario) en colKeys
    return {
        22: {
            type: 'select',
            options: samplesList.value.map(s => ({
                value: s.id,
                label: s.tag ? `${s.tag} - ${s.name}` : s.name
            }))
        },
        30: {
            type: 'select',
            options: usersList.value.map(u => ({
                value: u.id,
                label: `${u.nombre || ''} ${u.apellido || ''}`.trim() || `Usuario ${u.id}`
            }))
        }
    };
});

// ============================================================================
// 4. MÉTODOS DE CARGA DE DATOS
// ============================================================================

/**
 * Carga inicial: Obtiene solo los equipos del sistema "Analizadores" y todos los usuarios.
 */
const loadInitialData = async () => {
    // Utilizamos execute y definimos un custom error literal al final de la función
    await execute(async () => {
        // 1. Buscar el sistema llamado "Analizadores"
        const systemRes = await api.get('systems/', { params: { name__icontains: 'Analizadores' } });
        const systems = systemRes.data.results ? systemRes.data.results : systemRes.data;

        let analyzerSystemId = null;
        if (systems && systems.length > 0) {
            analyzerSystemId = systems[0].id;
        }

        // 2. Cargar equipos (solo los del sistema Analizadores si existe) y usuarios
        let eqParams = { page_size: 10000 };
        if (analyzerSystemId) {
            eqParams.system = analyzerSystemId;
        } else {
            console.warn('No se encontró el sistema "Analizadores". Se mostrará la lista vacía o se buscarán todos.');
        }

        const [eqRes, usersRes] = await Promise.all([
            api.get('equipments/', { params: eqParams }),
            api.get('users/', { params: { page_size: 10000 } })
        ]);

        equipmentsList.value = eqRes.data.results ? eqRes.data.results : eqRes.data;
        usersList.value = usersRes.data.results ? usersRes.data.results : usersRes.data;

        // 3. Autoseleccionar el primer equipo de la lista filtrada
        if (equipmentsList.value && equipmentsList.value.length > 0) {
            selectedEquipmentId.value = equipmentsList.value[0].id;
            await loadData(1);
            await loadFilterData();
        } else if (analyzerSystemId) {
            error.value = 'El sistema Analizadores existe, pero no tiene equipos asociados.';
        }
    // El segundo parámetro de execute sobreescribirá la variable error si la promesa falla
    }, 'Error al cargar la lista de equipos del sistema Analizadores.');
};

/**
 * Se ejecuta cuando el usuario cambia el equipo en el menú desplegable superior.
 */
const handleEquipmentChange = async () => {
    // Resetear paginación y filtros al cambiar de equipo
    currentPage.value = 1;
    currentFilters.value = {};
    currentSort.value = { colIndex: null, direction: null };

    await loadData(1);
    await loadFilterData();
};

/**
 * Carga los datos crudos para el menú de filtros desplegable de ExcelGrid.
 */
const loadFilterData = async () => {
    if (!selectedEquipmentId.value) return;
    try {
        const response = await api.get('assays/', {
            params: {
                sample__equipment: selectedEquipmentId.value,
                page_size: 10000
            }
        });
        const results = response.data.results || response.data;

        filterData.value = results.map(assay => {
            return colKeys.map(key => {
                let value = assay[key];
                if (value !== null && typeof value === 'object') {
                    return value.id;
                }
                return value === null || value === undefined ? '' : value;
            });
        });
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

/**
 * Función principal que carga los ensayos aplicando los filtros del backend
 */
const loadData = async (page = 1) => {
    if (!selectedEquipmentId.value) return;

    // El catch interno de este método se elimina, porque execute ya formatea y vuelca los errores del servidor
    await execute(async () => {
        const params = {
            sample__equipment: selectedEquipmentId.value, // Filtro inicial por Equipo
            page,
            page_size: pageSize.value
        };

        // Aplicar filtros provenientes de ExcelGrid
        for (const [colIndex, values] of Object.entries(currentFilters.value)) {
            let fieldName = colKeys[colIndex];

            // Ajuste de nombres de campos si es necesario
            if (fieldName === 'userp') fieldName = 'user';

            if (fieldName && values.length > 0) {
                params[`${fieldName}__in`] = values.join(',');
            }
        }

        // Aplicar ordenamiento proveniente de ExcelGrid
        if (currentSort.value.colIndex !== null) {
            let fieldName = colKeys[currentSort.value.colIndex];
            if (fieldName === 'userp') fieldName = 'user';

            if (fieldName) {
                params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
            }
        }

        // Ejecutar peticiones en paralelo: Ensayos (paginados) y Muestras del equipo (para el dropdown interno)
        const [assaysRes, samplesRes] = await Promise.all([
            api.get('assays/', { params }),
            api.get('samples/', { params: { equipment: selectedEquipmentId.value, page_size: 10000 } })
        ]);

        // Procesar muestras
        samplesList.value = samplesRes.data.results ? samplesRes.data.results : samplesRes.data;

        // Procesar ensayos y variables de paginación
        const responseData = assaysRes.data;
        let dataArray = [];

        if (responseData && responseData.results) {
            dataArray = responseData.results;
            totalItems.value = responseData.count;
            totalPages.value = Math.ceil(responseData.count / pageSize.value);
            currentPage.value = page;
        } else if (Array.isArray(responseData)) {
            dataArray = responseData;
            totalItems.value = dataArray.length;
            totalPages.value = 1;
            currentPage.value = 1;
        }

        // Formatear los datos a la matriz bidimensional esperada por ExcelGrid
        assaysData.value = dataArray.map(assay => {
            return colKeys.map(key => {
                let value = assay[key];

                // Si la API nos devuelve un objeto anidado (ej. sample o user), extraer solo el ID
                if (value !== null && typeof value === 'object') {
                    return value.id;
                }

                if (value === null || value === undefined) {
                    return '';
                }
                return value;
            });
        });
    }); // Sin mensaje personalizado; useApi.js reportará el estado real del servidor HTTP
};

// --- Manejadores de Eventos del Componente ExcelGrid ---
const handlePageChange = (newPage) => { loadData(newPage); };
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

// ============================================================================
// 5. MÉTODOS DE GUARDADO Y ELIMINACIÓN
// ============================================================================

const handleSave = async (updatedGrid) => {
    try {
        // Envolvemos exclusivamente las peticiones que impactan la BD
        await execute(async () => {
            const promises = updatedGrid.map(row => {
                const payload = {};
                colKeys.forEach((key, index) => {
                    let val = row[index];
                    let payloadKey = key === 'userp' ? 'user' : key;
                    payload[payloadKey] = val === '' ? null : val;
                });

                const id = payload.id;
                if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
                    return api.put(`assays/${id}/`, payload);
                } else {
                    delete payload.id;
                    return api.post('assays/', payload);
                }
            });

            await Promise.all(promises);
            alert('Cambios guardados correctamente.');
            await loadData(currentPage.value);
            await loadFilterData();
        });
    } catch (err) {
        // Conservamos solo la alerta de UI y el catch genérico de Axios lo maneja useApi
        alert('Error al guardar. Revisa el mensaje de error en pantalla.');
    }
};

const handleDelete = async (idsToDelete) => {
    if (!idsToDelete || idsToDelete.length === 0) return;

    try {
        // Bloqueamos la vista mientras se eliminan registros iterativamente
        await execute(async () => {
            const deletePromises = idsToDelete.map(id => api.delete(`assays/${id}/`));
            await Promise.all(deletePromises);
            alert(`${idsToDelete.length} ensayo(s) eliminado(s) correctamente.`);

            let pageToLoad = currentPage.value;
            if (idsToDelete.length >= assaysData.value.length && pageToLoad > 1) {
                pageToLoad -= 1;
            }

            await loadData(pageToLoad);
            await loadFilterData();
        });
    } catch (err) {
        alert('Ocurrió un error al eliminar los registros.');
    }
};

// ============================================================================
// 6. CICLO DE VIDA
// ============================================================================
onMounted(() => {
    loadInitialData();
});
</script>

<style scoped>
.assays-view {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header-actions {
  padding: 15px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-actions label {
  font-weight: bold;
  color: #495057;
}

.equipment-select {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  min-width: 350px;
  background-color: white;
  cursor: pointer;
}

.grid-container {
  flex-grow: 1;
  overflow: hidden;
}

.no-selection-msg {
  padding: 40px;
  text-align: center;
  color: #6c757d;
  font-size: 1.2rem;
  font-style: italic;
  background-color: #f8f9fa;
  flex-grow: 1;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 1.2rem;
  z-index: 100;
}

.error-message {
  color: #721c24;
  padding: 15px;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  margin: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
}
</style>