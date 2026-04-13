import { ref } from 'vue';
import { api } from '../../api';

/**
 * Composable para encapsular la lógica de jerarquía de equipos (Planta -> Área -> Sistema -> Equipo).
 * Permite cargar los catálogos en memoria, obtener nombres relacionales para las filas
 * y traducir los filtros de texto del frontend a IDs válidos para el backend.
 */
export function useEquipmentHierarchies() {
    const equipmentsList = ref([]);
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

            systemsMap.value = extractData(sysRes).reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
            areasMap.value = extractData(areaRes).reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
            plantsMap.value = extractData(plantRes).reduce((acc, item) => ({ ...acc, [item.id]: item }), {});
            equipmentsList.value = extractData(eqRes);
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

    // Intercepta los filtros marcados por el usuario y los traduce a un listado de IDs compatibles con 'equipment__in'
    const processEquipmentFilters = (currentFilters, colIndices) => {
        let eqFilterIds = null;
        // Se reciben los índices de columna para cada nivel de la jerarquía
        const { plant, area, system, equipment } = colIndices;

        for (const [colIndex, values] of Object.entries(currentFilters)) {
            if (values.length === 0) continue;

            if (colIndex === plant || colIndex === area || colIndex === system) {
                const validIds = equipmentsList.value.filter(eq => {
                    const areaObj = areasMap.value[eq.area] || {};
                    const plantObj = plantsMap.value[areaObj.plant] || {};
                    const sysObj = systemsMap.value[eq.system] || {};

                    if (colIndex === plant) return values.includes(plantObj.name || '');
                    if (colIndex === area) return values.includes(areaObj.name || '');
                    if (colIndex === system) return values.includes(sysObj.name || '');
                    return false;
                }).map(eq => String(eq.id));

                eqFilterIds = eqFilterIds === null ? validIds : eqFilterIds.filter(id => validIds.includes(id));
            } else if (colIndex === equipment) {
                const stringValues = values.map(v => String(v));
                eqFilterIds = eqFilterIds === null ? stringValues : eqFilterIds.filter(id => stringValues.includes(id));
            }
        }

        return eqFilterIds !== null ? (eqFilterIds.length > 0 ? eqFilterIds.join(',') : '-1') : null;
    };

    /**
     * Construye el objeto de parámetros de consulta final para una petición a la API,
     * manejando tanto filtros estándar como los filtros complejos basados en la jerarquía.
     * @param {object} baseParams - Parámetros iniciales como paginación.
     * @param {object} currentFilters - El objeto de filtros activos de la grilla.
     * @param {Array<string>} colKeys - El mapeo de índices de columna a nombres de campo.
     * @param {object} hierarchyColIndices - Un mapa de los índices de las columnas de jerarquía. Ej: { plant: '7', area: '8', ... }.
     * @returns {object} El objeto de parámetros final para la llamada a la API.
     */
    const buildFilterParams = (baseParams, currentFilters, colKeys, hierarchyColIndices) => {
        const params = { ...baseParams };
        const hierarchyIndexes = Object.values(hierarchyColIndices);

        // 1. Manejar filtros estándar (aquellos que no son parte de la jerarquía)
        for (const [colIndex, values] of Object.entries(currentFilters)) {
            if (hierarchyIndexes.includes(String(colIndex)) || values.length === 0) {
                continue;
            }
            
            
                            
            const fieldName = colKeys[colIndex];
            if (fieldName && !fieldName.includes('__')) {
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

        // 2. Manejar filtros de jerarquía, traduciéndolos a un único 'equipment__in'
        const equipmentFilterValue = processEquipmentFilters(currentFilters, hierarchyColIndices);
        if (equipmentFilterValue !== null) {
            params['equipment__in'] = equipmentFilterValue;
        }

        return params;
    };

    return { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams };
}