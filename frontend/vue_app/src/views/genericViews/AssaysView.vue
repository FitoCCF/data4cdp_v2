<!--
  AssaysView.vue
  Vista de Mantenimiento de Ensayos usando ExcelGrid.
  Muestra ensayos filtrados dinámicamente por Equipo seleccionado.
  Solo muestra equipos del sistema "Analizadores".
  Selecciona por defecto el equipo con actividad más reciente.
-->
<template>
  <section class="assays-view">
    <header class="view-header">
      <h1>Mantenimiento de Ensayos</h1>

      <div class="header-actions">
        <!-- Selector de Equipo -->
        <select
          v-model="selectedEquipmentId"
          @change="handleEquipmentChange"
          class="equipment-select"
          :disabled="loading"
        >
          <option :value="null" disabled>-- Seleccione un Analizador --</option>
          <option
            v-for="eq in equipmentsList"
            :key="eq.id"
            :value="eq.id"
          >
            <!-- MODIFICADO: Formato "Nombre - Descripción" -->
            {{ eq.name }} {{ eq.description ? `- ${eq.description}` : '' }}
          </option>
        </select>

        <!-- Filtro rápido por fecha -->
        <input 
          type="date" 
          v-model="filterDate" 
          class="date-filter"
          title="Filtrar por fecha"
          @change="loadData(1)"
        />

        <button
          type="button"
          class="btn btn-blue"
          @click="loadData(1)"
          :disabled="loading || !selectedEquipmentId"
        >
          {{ loading ? 'Cargando...' : 'Recargar Datos' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="feedback error">{{ error }}</p>

    <p v-if="!selectedEquipmentId && !loading" class="feedback info">
      Por favor, seleccione un analizador para ver sus ensayos.
    </p>

    <!-- Componente ExcelGrid -->
    <div class="grid-wrapper" v-if="selectedEquipmentId">
      <ExcelGrid
        v-if="!loading"
        :title="gridTitle"
        :headers="gridHeaders"
        :data="gridData"
        :columnsConfig="gridConfig"
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
      <p v-else class="loading-text">Cargando datos...</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue';
import { api } from '../../api';
import ExcelGrid from '../../components/ExcelGrid.vue';

// --- Estado ---
const loading = ref(false);
const error = ref('');
const filterDate = ref('');
const rawAssays = ref([]);
const samplesList = ref([]);

// Estado para manejo de Equipos
const equipmentsList = ref([]);
const selectedEquipmentId = ref(null);

// --- Estado Paginación y Filtrado ---
const currentPage = ref(1);
const totalPages = ref(1);
const totalItems = ref(0);
const pageSize = ref(25);
const currentFilters = ref({});
const currentSort = ref({ colIndex: null, direction: null });
const filterData = ref([]);

// --- Configuración de la Grilla ---
const gridHeaders = [
  'ID', 'Chemical ID', 'Muestra', 'Fecha', 'Hora', 'Instancia',
  'A1 Fe', 'A2 Cu', 'A3 Zn', 'A4 Mo', 'A5 A5', 'A6 Sol', 'A7 A7',
  '% Fe', '% Cu', '% Zn', '% Mo', '% Ins', '% Sol',
  'N1 Fe', 'N2 Cu', 'N3 Zn', 'N4 Mo', 'N5 Ech5', 'N6 Sc', 'N7 Ech7',
  'Tara', 'Peso Total', 'Peso Seco', 'Peso Prod.',
  'User P', 'Meta User'
];

const colKeys = [
  'id', 'chemical_id', 'sample', 'date', 'time', 'instance',
  'a1fe', 'a2cu', 'a3zn', 'a4mo', 'a5a5', 'a6sol', 'a7a7',
  'pFe', 'pCu', 'pZn', 'pMo', 'pIns', 'pSol',
  'n1fe', 'n2cu', 'n3zn', 'n4mo', 'n5ech5', 'n6sc', 'n7ech7',
  'tara', 'tweight', 'dweight', 'pweight',
  'userp', 'meta_user'
];

const gridTitle = computed(() => {
    if (!selectedEquipmentId.value) return 'Ensayos';
    const eq = equipmentsList.value.find(e => e.id === selectedEquipmentId.value);
    return eq ? `Ensayos - ${eq.name}` : 'Ensayos';
});

const gridConfig = computed(() => {
  const sampleOptions = samplesList.value.map(s => ({
    value: s.id,
    label: s.name || s.tag || `ID ${s.id}`
  }));

  return {
    0: { readOnly: true },
    2: { type: 'select', options: sampleOptions },
  };
});

const gridData = computed(() => {
  return rawAssays.value.map(assay => {
    return colKeys.map(key => {
      if (key === 'sample' && typeof assay[key] === 'object' && assay[key] !== null) {
        return assay[key].id;
      }
      return assay[key] === null || assay[key] === undefined ? '' : assay[key];
    });
  });
});

// --- Carga de Equipos (Filtrado por Sistema "Analizadores") ---
const loadEquipments = async () => {
    try {
        // 1. Buscar el ID del sistema "Analizadores"
        // Usamos 'icontains' para ser más flexibles con mayúsculas/minúsculas o nombres parciales
        const systemRes = await api.get('systems/', { params: { name__icontains: 'Analizadores' } });
        const systems = systemRes.data.results || systemRes.data;

        if (!systems || systems.length === 0) {
            console.warn('No se encontró el sistema "Analizadores". Cargando todos los equipos.');
            // Fallback: Cargar todos si no existe el sistema
            const allEqRes = await api.get('equipments/', { params: { page_size: 1000 } });
            equipmentsList.value = allEqRes.data.results || allEqRes.data;
        } else {
            // Tomamos el primer sistema que coincida (idealmente solo debería haber uno)
            const analyzerSystemId = systems[0].id;

            // 2. Cargar equipos que pertenecen a ese sistema
            const eqRes = await api.get('equipments/', {
                params: {
                    system: analyzerSystemId,
                    page_size: 1000
                }
            });
            equipmentsList.value = eqRes.data.results || eqRes.data;
        }

        // 3. Seleccionar equipo por defecto (Lógica "Más Reciente" o Primero)
        if (equipmentsList.value.length > 0 && !selectedEquipmentId.value) {
             let targetEqId = null;

             try {
                 // Buscar ensayo más reciente
                 const recentRes = await api.get('assays/', { params: { ordering: '-date', page_size: 1 } });
                 const recentItems = recentRes.data.results || recentRes.data;

                 if (recentItems.length > 0 && recentItems[0].sample) {
                     const sId = (typeof recentItems[0].sample === 'object') ? recentItems[0].sample.id : recentItems[0].sample;
                     const sampleRes = await api.get(`samples/${sId}/`);
                     targetEqId = sampleRes.data.equipment;
                 }
             } catch (ignore) {
                 console.warn("No se pudo determinar el equipo más reciente.");
             }

             // Verificar si el equipo reciente está en nuestra lista FILTRADA
             if (targetEqId && equipmentsList.value.find(e => e.id === targetEqId)) {
                 selectedEquipmentId.value = targetEqId;
             } else {
                 // Fallback: Primer equipo de la lista filtrada
                 selectedEquipmentId.value = equipmentsList.value[0].id;
             }

             // 4. Cargar datos
             loadData(1);
             loadFilterData();
        } else if (equipmentsList.value.length === 0) {
            error.value = 'No se encontraron equipos en el sistema "Analizadores".';
        }

    } catch (err) {
        console.error("Error cargando equipos:", err);
        error.value = "Error al cargar la lista de analizadores.";
    }
};

const handleEquipmentChange = () => {
    currentPage.value = 1;
    currentFilters.value = {};
    currentSort.value = { colIndex: null, direction: null };
    loadData(1);
    loadFilterData();
};

// --- Carga de Datos ---
const loadFilterData = async () => {
    if (!selectedEquipmentId.value) return;
    try {
        const params = {
            sample__equipment: selectedEquipmentId.value,
            page_size: 5000
        };
        const response = await api.get('assays/', { params });
        const results = response.data.results || response.data;

        if (Array.isArray(results)) {
            filterData.value = results.map(assay => {
                return colKeys.map(key => {
                    if (key === 'sample' && typeof assay[key] === 'object' && assay[key] !== null) {
                        return assay[key].id;
                    }
                    return assay[key] === null || assay[key] === undefined ? '' : assay[key];
                });
            });
        }
    } catch (err) {
        console.error('Error cargando datos para filtros:', err);
    }
};

const loadData = async (page = 1) => {
  if (!selectedEquipmentId.value) return;

  loading.value = true;
  error.value = null;
  
  try {
    const params = {
      sample__equipment: selectedEquipmentId.value,
      page: page,
      page_size: pageSize.value
    };
    
    if (filterDate.value) {
      params.date = filterDate.value;
    }

    for (const [colIndex, values] of Object.entries(currentFilters.value)) {
        const fieldName = colKeys[colIndex];
        if (fieldName && values.length > 0) {
            params[`${fieldName}__in`] = values.join(','); 
        }
    }

    if (currentSort.value.colIndex !== null) {
        const fieldName = colKeys[currentSort.value.colIndex];
        if (fieldName) {
            params.ordering = currentSort.value.direction === 'desc' ? `-${fieldName}` : fieldName;
        }
    }

    const [assaysRes, samplesRes] = await Promise.all([
      api.get('assays/', { params }),
      api.get('samples/', { params: { equipment: selectedEquipmentId.value, page_size: 10000 } })
    ]);

    const responseData = assaysRes.data;
    
    if (responseData && responseData.results) {
        rawAssays.value = responseData.results;
        totalItems.value = responseData.count;
        totalPages.value = Math.ceil(responseData.count / pageSize.value);
        currentPage.value = page;
    } else {
        rawAssays.value = Array.isArray(responseData) ? responseData : [];
        totalItems.value = rawAssays.value.length;
        totalPages.value = 1;
        currentPage.value = 1;
    }

    samplesList.value = Array.isArray(samplesRes.data) ? samplesRes.data :
                        (samplesRes.data.results ? samplesRes.data.results : []);

  } catch (err) {
    console.error("Error cargando datos:", err);
    error.value = "Error al cargar datos del servidor.";
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (newPage) => { loadData(newPage); };
const handlePageSizeChange = (newSize) => { pageSize.value = newSize; loadData(1); };
const handleFilterChange = (filters) => { currentFilters.value = filters; loadData(1); };
const handleSortChange = (sortConfig) => { currentSort.value = sortConfig; loadData(1); };

// --- Guardado ---
const handleSave = async (gridRows) => {
  if (!selectedEquipmentId.value) {
      alert("Debe seleccionar un equipo antes de guardar.");
      return;
  }

  loading.value = true;
  error.value = '';

  try {
    const promises = [];

    for (const row of gridRows) {
      const payload = {};
      colKeys.forEach((key, index) => {
        let val = row[index];
        if (val === '') val = null;
        payload[key] = val;
      });

      const id = payload.id;

      if (id && String(id).toLowerCase() !== 'nuevo' && id !== '') {
        promises.push(api.put(`assays/${id}/`, payload));
      } else {
        delete payload.id;
        promises.push(api.post('assays/', payload));
      }
    }

    await Promise.all(promises);
    await loadData(currentPage.value);
    await loadFilterData();
    alert('Cambios guardados exitosamente.');

  } catch (err) {
    console.error("Error guardando:", err);
    error.value = "Error al guardar cambios. Verifique los datos.";
  } finally {
    loading.value = false;
  }
};

// --- Eliminación ---
const handleDelete = async (idsToDelete) => {
  loading.value = true;
  try {
    const promises = idsToDelete.map(id => api.delete(`assays/${id}/`));
    await Promise.all(promises);
    await loadData(currentPage.value);
    await loadFilterData();
    alert('Registros eliminados.');
  } catch (err) {
    console.error("Error eliminando:", err);
    error.value = "Error al eliminar registros.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadEquipments();
});
</script>

<style scoped>
.assays-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  height: 100%;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.equipment-select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    min-width: 300px; /* Aumentado para acomodar nombre + descripción */
    font-size: 1rem;
}

.date-filter {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.grid-wrapper {
  flex-grow: 1;
  overflow: hidden;
}

.loading-text {
  text-align: center;
  font-size: 1.2rem;
  color: #666;
  margin-top: 2rem;
}

.feedback.error {
  color: red;
  background: #fee2e2;
  padding: 10px;
  border-radius: 4px;
}

.feedback.info {
    color: #1e40af;
    background-color: #dbeafe;
    padding: 10px;
    border-radius: 4px;
    text-align: center;
}
</style>
