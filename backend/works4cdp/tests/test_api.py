"""Pruebas de la API REST: CRUD, filtros, paginación y endpoints personalizados."""
import datetime
from unittest import mock

from rest_framework import status
from rest_framework.test import APITestCase

from django.db.models import ProtectedError

from works4cdp.models import Area, Assay, AssaysPsi, Equipment, Plant, System, TaskP
from works4cdp.tests import factories as f

ROUTER_ENDPOINTS = [
    'estados', 'plants', 'areas', 'systems', 'equipments', 'taskcatalogs', 'tasks', 'taskp',
    'users', 'correctivetasks', 'samples', 'assays', 'assayspsi', 'userp', 'calendars',
]


class EndpointsBasicosTests(APITestCase):

    def test_todos_los_listados_responden_paginados(self):
        for endpoint in ROUTER_ENDPOINTS:
            response = self.client.get(f'/api/{endpoint}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK, endpoint)
            self.assertEqual(set(response.data), {'count', 'next', 'previous', 'results'}, endpoint)

    def test_todos_exponen_schema_con_los_campos_del_modelo(self):
        for endpoint in ROUTER_ENDPOINTS:
            response = self.client.get(f'/api/{endpoint}/schema/')
            self.assertEqual(response.status_code, status.HTTP_200_OK, endpoint)
            self.assertIn('id', response.data['fields'], endpoint)

    def test_schema_de_assays_incluye_campos_de_laboratorio(self):
        fields = self.client.get('/api/assays/schema/').data['fields']
        for campo in ('chemical_id', 'pSol', 'timestamp', 'sample'):
            self.assertIn(campo, fields)

    def test_recurso_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get('/api/plants/999999/').status_code, status.HTTP_404_NOT_FOUND)


class PlantCrudTests(APITestCase):

    def test_ciclo_completo_crear_leer_editar_borrar(self):
        created = self.client.post('/api/plants/', {'tag': 'C3', 'name': 'Concentradora 3'}, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        url = f"/api/plants/{created.data['id']}/"

        self.assertEqual(self.client.get(url).data['name'], 'Concentradora 3')

        patched = self.client.patch(url, {'description': 'Nueva'}, format='json')
        self.assertEqual(patched.data['description'], 'Nueva')

        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Plant.objects.exists())

    def test_validacion_campos_obligatorios_y_longitud(self):
        response = self.client.post('/api/plants/', {'tag': 'X' * 11}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertIn('tag', response.data)  # max_length=10

    def test_borrar_planta_con_equipos_se_rechaza(self):
        """Antes esto borraba en cascada la planta, sus áreas, sus equipos y el historial de tareas.

        Desde que Equipment.area es PROTECT (migración 0020), el borrado se rechaza con 409 y hay que
        reasignar o eliminar los equipos primero. La cascada Planta -> Área sigue existiendo: lo que
        corta es el equipo.
        """
        h = f.make_hierarchy()
        f.make_sample(h['equipment'])
        response = self.client.delete(f"/api/plants/{h['plant'].id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(type(h['equipment']).objects.exists())
        self.assertTrue(Plant.objects.filter(id=h['plant'].id).exists())


class FiltrosYPaginacionTests(APITestCase):

    def setUp(self):
        for i in range(30):
            f.make_plant(tag=f'P{i}', name=f'Planta {i:02d}')

    def test_paginacion_por_defecto_y_page_size(self):
        self.assertEqual(len(self.client.get('/api/plants/').data['results']), 25)
        self.assertEqual(len(self.client.get('/api/plants/?page_size=5').data['results']), 5)
        self.assertEqual(self.client.get('/api/plants/?page_size=5').data['count'], 30)

    def test_filtros_icontains_e_in(self):
        self.assertEqual(self.client.get('/api/plants/?name__icontains=planta 0').data['count'], 10)
        self.assertEqual(self.client.get('/api/plants/?tag__in=P1,P2,P3').data['count'], 3)

    def test_ordenamiento(self):
        names = [r['name'] for r in self.client.get('/api/plants/?ordering=name&page_size=3').data['results']]
        self.assertEqual(names, ['Planta 00', 'Planta 01', 'Planta 02'])

    def test_filtro_de_assays_por_equipo_de_la_muestra(self):
        h1 = f.make_hierarchy()
        otro = f.make_equipment(h1['system'], name='Otro')
        f.make_assay(f.make_sample(h1['equipment']))
        f.make_assay(f.make_sample(otro, tag='X'))
        response = self.client.get(f"/api/assays/?sample__equipment={h1['equipment'].id}")
        self.assertEqual(response.data['count'], 1)


class DeleteImpactTests(APITestCase):

    def setUp(self):
        self.h = f.make_hierarchy()
        f.make_sample(self.h['equipment'])
        f.make_task(f.make_catalog(), self.h['equipment'])
        f.make_corrective(self.h['equipment'], f.make_user())

    def test_impacto_de_planta_por_get(self):
        response = self.client.get(f"/api/plants/delete-impact/?ids={self.h['plant'].id}")
        impact = response.data['impact'][0]
        self.assertEqual(
            {k: impact[k] for k in ('areas_count', 'equipments_count', 'tasks_count', 'correctives_count', 'samples_count', 'total_impact')},
            {'areas_count': 1, 'equipments_count': 1, 'tasks_count': 1, 'correctives_count': 1, 'samples_count': 1, 'total_impact': 5},
        )

    def test_impacto_de_equipo_por_post(self):
        response = self.client.post('/api/equipments/delete-impact/', {'ids': [self.h['equipment'].id]}, format='json')
        self.assertEqual(response.data['impact'][0]['total_impact'], 3)

    def test_impacto_de_area_y_sistema(self):
        area = self.client.get(f"/api/areas/delete-impact/?ids={self.h['area'].id}").data['impact'][0]
        system = self.client.get(f"/api/systems/delete-impact/?ids={self.h['system'].id}").data['impact'][0]
        self.assertEqual(area['total_impact'], 4)
        self.assertEqual(system['total_impact'], 4)

    def test_ids_invalidos_se_ignoran(self):
        response = self.client.get(f"/api/plants/delete-impact/?ids=abc,{self.h['plant'].id},")
        self.assertEqual(len(response.data['impact']), 1)
        response = self.client.post('/api/plants/delete-impact/', {'ids': ['x', None]}, format='json')
        self.assertEqual(response.data['impact'], [])


class TaskPTests(APITestCase):

    def test_excluye_tareas_huerfanas(self):
        estado = f.make_estado()
        h = f.make_hierarchy()
        f.make_taskp(estado, task=f.make_task(f.make_catalog(), h['equipment']))
        f.make_taskp(estado)  # sin plantilla ni correctiva
        self.assertEqual(self.client.get('/api/taskp/').data['count'], 1)


class CorrectiveTaskFilterTests(APITestCase):

    def test_filtros_year_week_date_mapean_a_creation_date(self):
        h = f.make_hierarchy()
        user = f.make_user()
        f.make_corrective(h['equipment'], user, creation_date=datetime.date(2026, 3, 2))
        f.make_corrective(h['equipment'], user, creation_date=datetime.date(2025, 3, 2))
        self.assertEqual(self.client.get('/api/correctivetasks/?year=2026').data['count'], 1)
        self.assertEqual(self.client.get('/api/correctivetasks/?week=10&year=2026').data['count'], 1)
        self.assertEqual(self.client.get('/api/correctivetasks/?date=2025-03-02').data['count'], 1)


class WeeklyTaskViewTests(APITestCase):

    def setUp(self):
        h = f.make_hierarchy()
        self.estado = f.make_estado('Pendiente')
        self.realizada = f.make_estado('Realizada')
        self.group = f.make_group('Grupo A')
        f.make_user(group=self.group, nombre='Luis')
        task = f.make_task(f.make_catalog('Calibración'), h['equipment'], turn='B')
        self.taskp = f.make_taskp(self.estado, task=task)
        f.assign(self.taskp, f.make_calendar(self.group))
        corrective = f.make_corrective(h['equipment'], f.make_user(email='x@example.com'))
        self.correctiva = f.make_taskp(self.estado, corrective_task=corrective)

    def test_get_devuelve_tareas_y_calendario(self):
        data = self.client.get('/api/weekly-tasks/?week=10&year=2026').data
        self.assertEqual(len(data['tasks']), 2)
        programada = next(t for t in data['tasks'] if t['id'] == self.taskp.id)
        self.assertFalse(programada['is_corrective'])
        self.assertEqual(programada['tarea_descripcion'], 'Calibración')
        self.assertEqual(programada['turno'], 'B')
        self.assertEqual(programada['cuadrilla_grupo'], 'Grupo A')
        self.assertEqual(programada['usuarios_asignados'], 'Luis')
        correctiva = next(t for t in data['tasks'] if t['id'] == self.correctiva.id)
        self.assertTrue(correctiva['is_corrective'])
        self.assertEqual(correctiva['tarea_descripcion'], 'Falla bomba')
        self.assertEqual(data['calendar'][0]['nombre_grupo'], 'Grupo A')

    def test_get_valida_parametros(self):
        self.assertEqual(self.client.get('/api/weekly-tasks/').status_code, 400)
        self.assertEqual(self.client.get('/api/weekly-tasks/?week=x&year=2026').status_code, 400)

    def test_get_semana_sin_datos(self):
        self.assertEqual(self.client.get('/api/weekly-tasks/?week=11&year=2026').data, {'tasks': [], 'calendar': []})

    def test_post_actualiza_estados(self):
        payload = {'updates': [{'id': self.taskp.id, 'estado_id': self.realizada.id}]}
        self.assertEqual(self.client.post('/api/weekly-tasks/', payload, format='json').status_code, 200)
        self.taskp.refresh_from_db()
        self.assertEqual(self.taskp.estado, self.realizada)

    def test_post_invalido_no_guarda_nada(self):
        payload = {'updates': [{'id': self.taskp.id, 'estado_id': self.realizada.id}, {'id': self.correctiva.id}]}
        self.assertEqual(self.client.post('/api/weekly-tasks/', payload, format='json').status_code, 400)
        self.taskp.refresh_from_db()
        self.assertEqual(self.taskp.estado, self.estado)
        self.assertEqual(self.client.post('/api/weekly-tasks/', {'updates': 'x'}, format='json').status_code, 400)

    def test_post_marcar_realizada_registra_la_hora(self):
        """Antes la vista hacía .update() de queryset: no ejecutaba save() y dejaba
        completion_date y updated_at vacíos, así que el paso P -> R no dejaba rastro."""
        payload = {'updates': [{'id': self.taskp.id, 'estado_id': self.realizada.id}]}
        respuesta = self.client.post('/api/weekly-tasks/', payload, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['realizadas'], [self.taskp.id])
        self.taskp.refresh_from_db()
        self.assertIsNotNone(self.taskp.completion_date)
        self.assertIsNotNone(self.taskp.updated_at)

    def test_post_estado_inexistente_devuelve_400(self):
        # Antes terminaba en 500 por violación de clave foránea.
        payload = {'updates': [{'id': self.taskp.id, 'estado_id': 99999}]}
        self.assertEqual(self.client.post('/api/weekly-tasks/', payload, format='json').status_code, 400)
        self.taskp.refresh_from_db()
        self.assertEqual(self.taskp.estado, self.estado)


class ChemicalIdEndpointsTests(APITestCase):

    def setUp(self):
        self.h = f.make_hierarchy(plant_tag='C1', plant_name='Concentradora 1')
        self.s10 = f.make_sample(self.h['equipment'], tag='C_01_S10')
        self.s2 = f.make_sample(self.h['equipment'], tag='C_01_S2')

    def test_next_chemical_id_sin_datos_usa_la_base_de_la_planta(self):
        data = self.client.get(f"/api/assays/next-chemical-id/?equipment_id={self.h['equipment'].id}").data
        self.assertEqual((data['max_chemical_id'], data['next_chemical_id']), (None, 26001))
        c2 = f.make_plant(tag='C2', name='Concentradora 2')
        self.assertEqual(self.client.get(f'/api/assays/next-chemical-id/?plant_id={c2.id}').data['next_chemical_id'], 10001)

    def test_next_chemical_id_continua_la_serie(self):
        f.make_assay(self.s2, chemical_id=26010)
        data = self.client.get(f"/api/assays/next-chemical-id/?plant_id={self.h['plant'].id}").data
        self.assertEqual((data['max_chemical_id'], data['next_chemical_id']), (26010, 26011))

    def test_next_chemical_id_errores(self):
        self.assertEqual(self.client.get('/api/assays/next-chemical-id/').status_code, 400)
        self.assertEqual(self.client.get('/api/assays/next-chemical-id/?equipment_id=999999').status_code, 404)
        self.assertEqual(self.client.get('/api/assays/next-chemical-id/?plant_id=abc').status_code, 404)
        sin_area = f.make_equipment(self.h['system'], area=None, name='Sin área')
        self.assertEqual(self.client.get(f'/api/assays/next-chemical-id/?equipment_id={sin_area.id}').status_code, 400)

    def test_autofill_asigna_en_orden_natural_solo_a_los_vacios(self):
        a10 = f.make_assay(self.s10)
        a2 = f.make_assay(self.s2)
        ya_tenia = f.make_assay(self.s2, time=datetime.time(9, 0), chemical_id=26050)
        response = self.client.post('/api/assays/autofill-chemical-ids/', {'equipment_id': self.h['equipment'].id}, format='json')
        self.assertEqual(response.data['updated'], 2)
        for assay in (a10, a2, ya_tenia):
            assay.refresh_from_db()
        self.assertEqual((a2.chemical_id, a10.chemical_id, ya_tenia.chemical_id), (26051, 26052, 26050))

    def test_autofill_reassign_recalcula_todos_desde_el_maximo(self):
        a2 = f.make_assay(self.s2, chemical_id=26050)
        self.client.post('/api/assays/autofill-chemical-ids/', {'equipment_id': self.h['equipment'].id, 'reassign': True}, format='json')
        a2.refresh_from_db()
        self.assertEqual(a2.chemical_id, 26051)

    def test_autofill_filtra_por_fecha(self):
        f.make_assay(self.s2, date=datetime.date(2026, 1, 1))
        f.make_assay(self.s2, date=datetime.date(2026, 1, 2))
        response = self.client.post('/api/assays/autofill-chemical-ids/',
                                    {'equipment_id': self.h['equipment'].id, 'date': '2026-01-02'}, format='json')
        self.assertEqual(response.data['updated'], 1)
        self.assertEqual(Assay.objects.filter(chemical_id__isnull=True).count(), 1)

    def test_autofill_errores(self):
        url = '/api/assays/autofill-chemical-ids/'
        self.assertEqual(self.client.post(url, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'equipment_id': 'abc'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'equipment_id': 999999}, format='json').status_code, 404)
        self.assertEqual(self.client.post(url, {'equipment_id': self.h['equipment'].id, 'date': '2026-13-01'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'equipment_id': self.h['equipment'].id}, format='json').data['updated'], 0)

    def test_assay_con_chemical_id_repetido_por_api_devuelve_400(self):
        f.make_assay(self.s2, chemical_id=26001)
        response = self.client.post('/api/assays/', {'sample_id': self.s2.id, 'date': '2026-02-01', 'chemical_id': 26001}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SyncEquipmentEndpointTests(APITestCase):

    def test_requiere_equipment_id_y_fecha_valida(self):
        self.assertEqual(self.client.post('/api/assays/sync-equipment/', {}, format='json').status_code, 400)
        response = self.client.post('/api/assays/sync-equipment/', {'equipment_id': 1, 'date': '01-01-2026'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_delega_en_el_servicio(self):
        with mock.patch('works4cdp.services.clb_syncer.AssaySyncService.sync_equipment',
                        return_value={'status': 'ok', 'inserted': 3}) as sync:
            response = self.client.post('/api/assays/sync-equipment/', {'equipment_id': 5, 'date': '2026-01-02'}, format='json')
        self.assertEqual(response.data['inserted'], 3)
        sync.assert_called_once_with(equipment_id=5, target_date=datetime.date(2026, 1, 2))

    def test_error_inesperado_devuelve_500_controlado(self):
        with mock.patch('works4cdp.services.clb_syncer.AssaySyncService.sync_equipment', side_effect=RuntimeError('boom')):
            with self.assertLogs('works4cdp.views', level='ERROR'):
                response = self.client.post('/api/assays/sync-equipment/', {'equipment_id': 5}, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['status'], 'error')


class TaskPEstadoDefaultTests(APITestCase):

    def test_estado_por_defecto_es_pendiente(self):
        # id 2 = P (Pendiente). Antes era 1 = R (Realizado). Migración 0018.
        self.assertEqual(TaskP._meta.get_field('estado').default, 2)


class ContratoConElFrontendTests(APITestCase):
    """
    Nombres de campo que acepta la API para las claves foráneas que edita ExcelGrid
    (ver frontend/vue_app/src/utils/gridHelpers.js -> mapGridKeyToPayload).
    """

    def setUp(self):
        self.group = f.make_group()
        self.user = f.make_user()
        self.sample = f.make_sample(f.make_hierarchy()['equipment'])

    def test_users_acepta_group_y_no_group_id(self):
        url = f'/api/users/{self.user.id}/'
        self.client.patch(url, {'group_id': self.group.id}, format='json')
        self.user.refresh_from_db()
        self.assertIsNone(self.user.group)  # group_id se ignora en silencio
        self.client.patch(url, {'group': self.group.id}, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.group, self.group)

    def test_assays_acepta_user_y_sample_id(self):
        assay = f.make_assay(self.sample)
        url = f'/api/assays/{assay.id}/'
        self.client.patch(url, {'user_id': self.user.id}, format='json')
        assay.refresh_from_db()
        self.assertIsNone(assay.user)  # user_id se ignora en silencio
        self.client.patch(url, {'user': self.user.id}, format='json')
        assay.refresh_from_db()
        self.assertEqual(assay.user, self.user)

    def test_taskp_acepta_estado_id(self):
        estado = f.make_estado()
        otro = f.make_estado('Realizada')
        taskp = f.make_taskp(estado, task=f.make_task(f.make_catalog()))
        self.client.patch(f'/api/taskp/{taskp.id}/', {'estado_id': otro.id}, format='json')
        taskp.refresh_from_db()
        self.assertEqual(taskp.estado, otro)


class MuestreoPsiTests(APITestCase):
    """Contrato de /api/assayspsi/ con la vista PsiSamplingView.vue.

    El modelo AssaysPsi estaba en models.py desde el inicio pero sin serializer ni ruta, así que la
    tabla no se podía llenar desde la aplicación. Estas pruebas fijan lo que manda la grilla del
    formato CON-PSG-CPR-FM.003 (una fila = una sección de molienda en una de las rondas A/B/C).
    """

    def setUp(self):
        self.equipment = f.make_equipment(
            f.make_system(), f.make_area(f.make_plant()), name='PSI', tag='PSI-C1',
        )
        self.seccion3 = f.make_sample(self.equipment, tag='S3', name='Sección 3')
        self.seccion4 = f.make_sample(self.equipment, tag='S4', name='Sección 4')
        self.user = f.make_user()

    def _fila(self, **extra):
        """Una fila del formato, con los valores reales de la hoja C1_PSI_MOLIENDA."""
        payload = {
            'date': '2026-10-10',
            'time': '09:26',
            'turn': 'A',
            'sample_id': self.seccion3.id,
            'user_id': self.user.id,
            'meta_user': 'Anthony Taya',
            # Laboratorio: pesos y mallas
            'tara': 114.5, 'tweight': 1035.5, 'dweight': 300.0, 'psolid': 32.57,
            'pW48': 7.62, 'pW200': 48.71,
            # Datos que marcaba el PSI al tomar la muestra
            'instance': 1622,
            'aAvg': 322.75, 'aSD': 106.7, 'aDensity': 1.79, 'aSol': 35.91,
            'aP48': 7.62, 'P80': 197.76,
        }
        payload.update(extra)
        return payload

    def test_crea_una_fila_con_los_campos_del_formato(self):
        response = self.client.post('/api/assayspsi/', self._fila(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        fila = AssaysPsi.objects.get(id=response.data['id'])
        self.assertEqual(fila.sample, self.seccion3)
        # user_id SÍ se respeta acá, al contrario de /api/assays/ (ver ContratoConElFrontendTests).
        self.assertEqual(fila.user, self.user)
        self.assertEqual(fila.turn, 'A')
        self.assertEqual(fila.instance, 1622)
        self.assertEqual(fila.psolid, 32.57)
        self.assertEqual(fila.P80, 197.76)
        self.assertEqual(fila.meta_user, 'Anthony Taya')

    def test_la_muestra_viaja_anidada_en_get(self):
        """La grilla filtra por equipo a través de sample.equipment: necesita el objeto, no el id."""
        self.client.post('/api/assayspsi/', self._fila(), format='json')

        fila = self.client.get('/api/assayspsi/').data['results'][0]
        self.assertEqual(fila['sample']['id'], self.seccion3.id)
        self.assertEqual(fila['sample']['equipment'], self.equipment.id)

    def test_filtra_por_equipo_y_por_fecha_como_la_vista(self):
        self.client.post('/api/assayspsi/', self._fila(), format='json')
        self.client.post(
            '/api/assayspsi/',
            self._fila(sample_id=self.seccion4.id, turn='B', date='2026-10-11'),
            format='json',
        )

        response = self.client.get(
            f'/api/assayspsi/?sample__equipment={self.equipment.id}&date=2026-10-10'
        )
        self.assertEqual(response.data['count'], 1)

        otro = f.make_equipment(f.make_system(name='Otros', tag='OT'), name='Courier', tag='CR9')
        response = self.client.get(f'/api/assayspsi/?sample__equipment={otro.id}')
        self.assertEqual(response.data['count'], 0)

    def test_los_porcentajes_del_laboratorio_se_agregan_despues(self):
        """El laboratorio devuelve sus mallas horas más tarde: se edita la fila sin perder el PSI."""
        creada = self.client.post('/api/assayspsi/', self._fila(), format='json').data

        response = self.client.put(
            f"/api/assayspsi/{creada['id']}/",
            self._fila(pP48=7.1, pP65=19.0, pP100=29.5, pP150=39.0, pP200=48.0),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        fila = AssaysPsi.objects.get(id=creada['id'])
        self.assertEqual(fila.pP200, 48.0)
        self.assertEqual(fila.aP48, 7.62)  # lo que marcó el PSI sigue ahí


class ImpactoConTaskPTests(APITestCase):
    """El reporte de impacto tiene que contar las ocurrencias de TaskP: son el conteo más grande.

    Antes solo informaba equipos, tareas, correctivas y muestras, así que para un área real decía
    "30 tareas" y se callaba 979 ocurrencias programadas (191 ya reportadas como realizadas).
    """

    def setUp(self):
        self.h = f.make_hierarchy()
        self.pendiente = f.make_estado('P')
        self.realizado = f.make_estado('R')
        task = f.make_task(f.make_catalog(), self.h['equipment'])
        correctiva = f.make_corrective(self.h['equipment'], f.make_user())
        # Dos por la pauta preventiva (una de ellas ya realizada) y una por la correctiva.
        f.make_taskp(self.pendiente, task=task)
        f.make_taskp(self.realizado, task=task)
        f.make_taskp(self.pendiente, corrective_task=correctiva)

    def _impacto(self, recurso, obj):
        return self.client.get(f'/api/{recurso}/delete-impact/?ids={obj.id}').data['impact'][0]

    def test_cuenta_las_taskp_de_los_dos_caminos(self):
        """TaskP llega al equipo por task__equipment y por corrective_task__equipment."""
        for recurso, obj in (('equipments', self.h['equipment']), ('areas', self.h['area']),
                             ('systems', self.h['system']), ('plants', self.h['plant'])):
            with self.subTest(recurso=recurso):
                self.assertEqual(self._impacto(recurso, obj)['taskp_count'], 3)

    def test_informa_aparte_las_realizadas(self):
        impacto = self._impacto('areas', self.h['area'])
        self.assertEqual(impacto['taskp_realizadas_count'], 1)

    def test_las_realizadas_no_se_suman_al_total(self):
        """Son un subconjunto de taskp_count: sumarlas inflaría total_impact."""
        impacto = self._impacto('areas', self.h['area'])
        sumables = ('equipments_count', 'tasks_count', 'correctives_count', 'samples_count', 'taskp_count')
        self.assertEqual(impacto['total_impact'], sum(impacto[k] for k in sumables))
        self.assertNotIn(impacto['taskp_realizadas_count'], (impacto['total_impact'],))

    def test_sin_taskp_el_total_no_cambia(self):
        """Un área sin ocurrencias sigue dando el mismo total que antes de este cambio."""
        otra = f.make_area(self.h['plant'], name='Molienda', tag='ML')
        self.assertEqual(self._impacto('areas', otra)['total_impact'], 0)


class BorradoProtegidoTests(APITestCase):
    """Borrar algo de lo que cuelga el registro de trabajo devuelve 409, no 500 ni un borrado."""

    def setUp(self):
        self.h = f.make_hierarchy()
        self.task = f.make_task(f.make_catalog(), self.h['equipment'])
        self.taskp = f.make_taskp(f.make_estado('R'), task=self.task)

    def test_borrar_area_con_equipos_devuelve_409(self):
        response = self.client.delete(f"/api/areas/{self.h['area'].id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('bloqueado_por', response.data)
        self.assertTrue(Area.objects.filter(id=self.h['area'].id).exists())

    def test_borrar_sistema_con_equipos_devuelve_409(self):
        response = self.client.delete(f"/api/systems/{self.h['system'].id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(System.objects.filter(id=self.h['system'].id).exists())

    def test_borrar_equipo_con_tareas_devuelve_409(self):
        response = self.client.delete(f"/api/equipments/{self.h['equipment'].id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Equipment.objects.filter(id=self.h['equipment'].id).exists())

    def test_la_taskp_realizada_sobrevive(self):
        """Lo que motivó el cambio: la marcación de realizado no se puede perder por un borrado."""
        self.client.delete(f"/api/plants/{self.h['plant'].id}/")
        self.client.delete(f"/api/areas/{self.h['area'].id}/")
        self.client.delete(f"/api/equipments/{self.h['equipment'].id}/")
        self.assertTrue(TaskP.objects.filter(id=self.taskp.id).exists())

    def test_borrar_sin_dependencias_sigue_funcionando(self):
        """PROTECT no debe romper el borrado legítimo de un registro suelto."""
        suelta = f.make_area(self.h['plant'], name='Área vacía', tag='VA')
        response = self.client.delete(f'/api/areas/{suelta.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Area.objects.filter(id=suelta.id).exists())

    def test_a_nivel_modelo_levanta_protectederror(self):
        with self.assertRaises(ProtectedError):
            self.h['area'].delete()
