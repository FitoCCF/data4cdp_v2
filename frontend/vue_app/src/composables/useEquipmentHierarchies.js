import { ref } from 'vue';
import { api } from '../api';

/**
 * Composable para encapsular la lógica de jerarquía de equipos (Planta -> Área -> Sistema -> Equipo).
 * Permite cargar los catálogos en memoria y obtener los nombres relacionales para las filas.
 * (Los filtros por jerarquía ya no se traducen aquí: la API los resuelve con grid_filters,
 * ver utils/gridQuery.js y backend/works4cdp/grid_filters.py.)
 */
export function useEquipmentHierarchies() {
    const equipmentsList = ref([]);
    const systemsList = ref([]);
    const areasList = ref([]);
    const plantsList = ref([]);
    const systemsMap = ref({});
    const areasMap = ref({});
    const plantsMap = ref({});

    const extractData = (res) => res.data.results || res.data || [];

    // Descarga todos los catálogos vinculados a la jerarquía de un equipo
    const loadDependencies = async () => {
        try {
            const [sysRes, areaRes, plantRes, eqRes] = await Promise.all([
                api.get('systems/', { params: { page_size: 10000 } }),
                api.get('areas/', { params: { page_size: 10000 } }),
                api.get('plants/', { params: { page_size: 10000 } }),
                api.get('equipments/', { params: { page_size: 10000 } })
            ]);

            systemsList.value = extractData(sysRes);
            areasList.value = extractData(areaRes);
            plantsList.value = extractData(plantRes);
            equipmentsList.value = extractData(eqRes);

            systemsMap.value = systemsList.value.reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
            areasMap.value = areasList.value.reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
            plantsMap.value = plantsList.value.reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
        } catch (err) {
            console.error('Error al cargar jerarquías de equipos:', err);
        }
    };

    // Devuelve los nombres de Planta, Área y Sistema dado el ID de un equipo
    const getEquipmentHierarchyRow = (eqId) => {
        const eqObj = equipmentsList.value.find(e => e.id === eqId) || {};
        const areaObj = areasMap.value[eqObj.area] || {};
        const sysObj = systemsMap.value[eqObj.system] || {};
        const plantObj = plantsMap.value[areaObj.plant] || {};

        return {
            plantName: plantObj.name || '',
            areaName: areaObj.name || '',
            systemName: sysObj.name || '',
            equipmentName: eqObj.name || '',
            equipmentDesc: eqObj.description || '',
            equipmentId: eqId
        };
    };

    return {
        equipmentsList,
        plantsList,
        areasList,
        systemsList,
        plantsMap,
        areasMap,
        systemsMap,
        loadDependencies,
        getEquipmentHierarchyRow
    };
}